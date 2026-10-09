"""Durable accounting for the single-writer contact migration comparison.

This is an experiment ledger, not a scheduler. The existing bounded runner
owns process termination and resource limits. An unfinished reservation blocks
all further launches until its process and evidence have been recovered.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

MAX_STARTS = 48
TOTAL_WALL_S = 5400
PROCESS_WALL_S = 900
PACKAGE_MAX_STARTS = 64
PACKAGE_WALL_S = 6 * 3600


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def allowance(manifest, previous):
    """Keep lifetime accounting; only a new evidenced package adds allowance."""
    package = manifest.get('work_package')
    previous = previous or {}
    prior_package = previous.get('work_package')
    seen = previous.get('package_ids', [])
    if package is None:
        if prior_package is not None:
            raise ValueError('A revision cannot discard its work package')
        return dict(work_package=None, package_ids=[], package_baseline_starts=0,
                    package_baseline_wall_s=0., starts_limit=MAX_STARTS,
                    wall_limit_s=TOTAL_WALL_S)
    if (not isinstance(package, dict)
            or not isinstance(package.get('id'), str) or not package['id'].strip()
            or not isinstance(package.get('hypothesis'), str) or not package['hypothesis'].strip()
            or type(package.get('max_starts')) is not int
            or not 1 <= package['max_starts'] <= PACKAGE_MAX_STARTS
            or type(package.get('wall_s')) is not int
            or not 1 <= package['wall_s'] <= PACKAGE_WALL_S
            or not isinstance(package.get('evidence_sha256'), list)
            or not package['evidence_sha256']
            or any(not isinstance(h, str) or len(h) != 64
                   or any(c not in '0123456789abcdef' for c in h)
                   for h in package['evidence_sha256'])):
        raise ValueError('Work package requires a hypothesis, evidence hashes and bounded allowance')
    if prior_package is not None and package['id'] == prior_package['id']:
        if package != prior_package:
            raise ValueError('A source revision cannot change its frozen work package')
        starts = previous['package_baseline_starts']
        wall = previous['package_baseline_wall_s']
    else:
        if package['id'] in seen:
            raise ValueError('A retired work package cannot be restarted')
        if prior_package is not None and (package['hypothesis'] == prior_package['hypothesis']
                or not set(package['evidence_sha256']) - set(prior_package['evidence_sha256'])):
            raise ValueError('A new work package requires new evidence and a concrete new hypothesis')
        starts = previous.get('starts_used', 0)
        wall = previous.get('wall_charged_or_reserved_s', 0.)
        seen = [*seen, package['id']]
    return dict(work_package=package, package_ids=seen, package_baseline_starts=starts,
                package_baseline_wall_s=wall, starts_limit=starts + package['max_starts'],
                wall_limit_s=wall + package['wall_s'])


def publish(path, raw, *, replace=False):
    """Durably publish whole evidence; only the ledger head may be replaced."""
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


class MigrationBudget:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)

    @classmethod
    def create(cls, root, manifest):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=False)
        (root / 'events').mkdir()
        (root / 'attempts').mkdir()
        raw = json_bytes(manifest)
        publish(root / 'manifest.json', raw)
        result = cls(root)
        result._append([], {'kind': 'created', 'manifest_sha256': digest(raw)})
        prior = manifest.get('prior_budget')
        allowance(manifest, result._prior(manifest, require_retired=False))
        if prior is not None:
            previous = cls(prior['directory'])
            with previous._lock():
                if digest((previous.root/'head.json').read_bytes()) != prior['head_sha256']:
                    raise ValueError('Prior comparison changed while admitting its successor')
                publish(previous.root/'superseded.json', json_bytes({'successor': str(result.root)}))
        return result

    def _prior(self, manifest, *, require_retired=True):
        """A reviewed source revision inherits, rather than restarts, the allowance."""
        prior = manifest.get('prior_budget')
        if prior is None:
            return None
        previous = MigrationBudget(prior['directory'])
        if previous.root == self.root:
            raise ValueError('A comparison cannot inherit itself')
        state = previous.status()
        if (digest((previous.root/'head.json').read_bytes()) != prior['head_sha256']
                or state['manifest_sha256'] != prior['manifest_sha256']
                or state['starts_used'] != prior['starts_used']
                or state['wall_charged_or_reserved_s'] != prior['wall_s']
                or any(a['terminal'] is None for a in state['attempts'])):
            raise ValueError('Prior comparison changed or still has an unfinished process')
        retired = previous.root/'superseded.json'
        if require_retired and (not retired.exists() or
                json.loads(retired.read_bytes()) != {'successor': str(self.root)}):
            raise ValueError('Prior comparison is not retired to this revision')
        return state

    @contextmanager
    def _lock(self):
        with (self.root / 'lock').open('ab') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def _append(self, events, event):
        index = len(events)
        previous = digest((self.root / 'events' / f'{index-1:04d}.json').read_bytes()) if index else None
        raw = json_bytes(dict(event, sequence=index, previous_sha256=previous))
        publish(self.root / 'events' / f'{index:04d}.json', raw)
        publish(self.root / 'head.json', json_bytes({'sequence': index, 'sha256': digest(raw)}), replace=True)

    def _read(self):
        events, previous = [], None
        for index, path in enumerate(sorted((self.root / 'events').glob('*.json'))):
            raw = path.read_bytes()
            event = json.loads(raw)
            if (path.name != f'{index:04d}.json' or event['sequence'] != index
                    or event['previous_sha256'] != previous):
                raise ValueError('Broken migration event chain')
            previous = digest(raw)
            events.append(event)
        head = json.loads((self.root / 'head.json').read_bytes())
        index = head['sequence']
        if type(index) is not int or not 0 <= index < len(events):
            raise ValueError('Lost migration events; budget cannot be recreated')
        if digest((self.root / 'events' / f'{index:04d}.json').read_bytes()) != head['sha256']:
            raise ValueError('Migration head hash mismatch')
        if index != len(events)-1:
            # Crash between event publication and head publication: charge the event.
            publish(self.root / 'head.json', json_bytes({'sequence': len(events)-1,
                                                        'sha256': previous}), replace=True)
        manifest = json.loads((self.root / 'manifest.json').read_bytes())
        if (events[0]['kind'] != 'created' or events[0]['manifest_sha256'] !=
                digest((self.root / 'manifest.json').read_bytes())):
            raise ValueError('Frozen migration manifest changed')
        attempts = []
        for event in events[1:]:
            if event['kind'] == 'reserved':
                if event['attempt'] != len(attempts) or (attempts and attempts[-1]['terminal'] is None):
                    raise ValueError('Overlapping or duplicate migration attempts')
                attempts.append(dict(event, terminal=None))
            elif event['kind'] == 'terminal':
                if (not attempts or event['attempt'] != len(attempts)-1
                        or attempts[-1]['terminal'] is not None):
                    raise ValueError('Terminal event has no active reservation')
                attempts[-1]['terminal'] = event
            else:
                raise ValueError('Unknown migration event')
        return events, manifest, attempts

    def status(self):
        with self._lock():
            _, manifest, attempts = self._read()
            previous = self._prior(manifest) or {}
            limits = allowance(manifest, previous)
            prior_starts = previous.get('starts_used', 0)
            prior_wall = previous.get('wall_charged_or_reserved_s', 0.)
            charged = prior_wall + sum(a['terminal']['wall_s'] if a['terminal'] else a['timeout_s']
                                       for a in attempts)
            starts = prior_starts + len(attempts)
            return {**limits, 'manifest_sha256': digest(json_bytes(manifest)), 'attempts': attempts,
                    'starts_used': starts, 'inherited_starts': prior_starts,
                    'inherited_wall_s': prior_wall, 'wall_charged_or_reserved_s': charged,
                    'package_starts_used': starts-limits['package_baseline_starts'],
                    'package_wall_s': charged-limits['package_baseline_wall_s'],
                    'remaining_starts': max(0, limits['starts_limit']-starts),
                    'remaining_wall_s': max(0., limits['wall_limit_s']-charged)}

    def reserve(self, case_id, handle, *, timeout_s=PROCESS_WALL_S, retry_reason=None):
        if (type(timeout_s) is not int or not 1 <= timeout_s <= PROCESS_WALL_S
                or not isinstance(handle, dict) or not handle):
            raise ValueError('A bounded timeout and recoverable process handle are required')
        with self._lock():
            events, manifest, attempts = self._read()
            if (self.root/'superseded.json').exists():
                raise ValueError('Comparison is retired; continue its recorded successor')
            previous = self._prior(manifest) or {}
            limits = allowance(manifest, previous)
            prior_starts = previous.get('starts_used', 0)
            prior_wall = previous.get('wall_charged_or_reserved_s', 0.)
            if case_id not in {case['id'] for case in manifest['matrix']}:
                raise ValueError('Unknown frozen migration case')
            if any(a['terminal'] is None for a in attempts):
                raise RuntimeError('Recover the unfinished process before another launch')
            prior = [a for a in attempts if a['case_id'] == case_id]
            if prior and (len(prior) > 1 or prior[-1]['terminal']['outcome'] == 'recorded'
                          or not isinstance(retry_reason, str) or not retry_reason.strip()):
                raise ValueError('Case needs reviewed infrastructure recovery; recorded results never retry')
            if not prior and retry_reason is not None:
                raise ValueError('A first attempt has no retry reason')
            spent = prior_wall + sum(a['terminal']['wall_s'] for a in attempts)
            if (prior_starts + len(attempts) >= limits['starts_limit']
                    or spent + timeout_s > limits['wall_limit_s']):
                raise ValueError('Migration launch or cumulative wall allowance exhausted')
            index = len(attempts)
            self._append(events, {'kind': 'reserved', 'attempt': index, 'case_id': case_id,
                                  'timeout_s': timeout_s, 'handle': handle,
                                  'retry_reason': retry_reason})
            return index

    def finish(self, index, *, wall_s, evidence_sha256, outcome):
        """Caller must establish process termination first; unknown cost charges cap."""
        if outcome not in ('recorded', 'failed', 'interrupted'):
            raise ValueError('Unknown terminal outcome')
        if (not isinstance(evidence_sha256, str) or len(evidence_sha256) != 64
                or any(c not in '0123456789abcdef' for c in evidence_sha256)):
            raise ValueError('Evidence must have a SHA256 identity')
        if wall_s is not None and (type(wall_s) not in (int, float)
                                  or not math.isfinite(wall_s) or wall_s < 0):
            raise ValueError('Invalid process wall time')
        with self._lock():
            events, _, attempts = self._read()
            if not attempts or index != len(attempts)-1 or attempts[-1]['terminal'] is not None:
                raise ValueError('No matching unfinished attempt')
            self._append(events, {'kind': 'terminal', 'attempt': index, 'outcome': outcome,
                                  'wall_s': attempts[-1]['timeout_s'] if wall_s is None else wall_s,
                                  'wall_source': 'reservation' if wall_s is None else 'whole_process',
                                  'evidence_sha256': evidence_sha256})
