"""Bounded normal-response development trials using the existing runner and scorer.

The research agent supplies hypotheses; this module does not call a model or
change physical thresholds. MigrationBudget remains the durable single-writer
ledger. Run under bounded_run/research_guard for enforced host resource limits.
"""
import argparse
from dataclasses import asdict
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time

from dexlab.contact_load import LIMITS, LoadCase
from dexlab.contact_parameters import normal_parameters, normal_readback_matches
from dexlab.migration_budget import MigrationBudget, digest, json_bytes, publish

SOURCE_ROOT = Path(__file__).parent


def execution_cgroup():
    """Recovery needs a managed cgroup, including the child-PID publication gap."""
    lines = Path('/proc/self/cgroup').read_text().splitlines()
    group = next((line[3:] for line in lines if line.startswith('0::')), '')
    if not re.search(r'/dexlab-bounded-[0-9a-f]+\.service$', group):
        raise RuntimeError('Run native trials inside the existing bounded_run adaptive envelope')
    return {'cgroup': group, 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def sources():
    return {p.name: digest(p.read_bytes()) for p in sorted(SOURCE_ROOT.glob('*.py'))}


def validate(manifest):
    if manifest.get('schema_version') != 1 or manifest.get('purpose') != 'development':
        raise ValueError('Normal trials are versioned development evidence, never holdouts')
    if manifest.get('limits') != LIMITS:
        raise ValueError('Physical limits must retain the existing normal-load protocol')
    case = LoadCase(**manifest['case'])
    if not case.name.startswith('dev-') or manifest['case'] != asdict(case):
        raise ValueError('Freeze the complete development case')
    engine = manifest['engine']
    if engine not in ('mujoco', 'superdex'):
        raise ValueError('This native normal-load trial path supports MuJoCo and SuperDex')
    profile = manifest.get('runtime_profile')
    if engine == 'mujoco':
        from dexlab.engine_versions import mujoco_profile_identity
        version = str(profile).split('-', 1)[-1]
        mujoco_profile_identity({'version': version}, version, profile=profile or '')
    elif profile != 'official-1.0.0-fp64':
        raise ValueError('Freeze the native SuperDex FP64 profile')
    baseline = normal_parameters(engine, manifest['baseline'])
    if set(manifest['baseline']) != set(baseline):
        raise ValueError('Freeze complete baseline parameters')
    identifiers = set()
    if not manifest['matrix']:
        raise ValueError('At least one candidate is required')
    for row in manifest['matrix']:
        identity = row['id']
        if (not isinstance(identity, str) or not identity or identity in identifiers
                or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in identity)):
            raise ValueError('Invalid or duplicate candidate id')
        identifiers.add(identity)
        for key in ('hypothesis', 'expected_effect', 'physical_reference'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError('Candidates require hypothesis, expected effect and physical reference')
        if set(row['parameters']) != set(normal_parameters(engine, row['parameters'])):
            raise ValueError('Freeze every effective candidate parameter explicitly')
        if not row.get('evidence'):
            raise ValueError('Hypotheses require hashed evidence')
        for reference in row['evidence']:
            path = Path(reference['path'])
            if not path.is_file() or digest(path.read_bytes()) != reference['sha256']:
                raise ValueError('Candidate evidence missing or changed')
    package = manifest.get('work_package', {})
    if not package or not set(package.get('evidence_sha256', [])) <= {
        ref['sha256'] for row in manifest['matrix'] for ref in row['evidence']
    }:
        raise ValueError('Work package must refer to candidate evidence')


def create(root, manifest):
    validate(manifest)
    frozen = {**manifest, 'source_sha256': sources()}
    # Validate allowance before creating a durable directory.
    from dexlab.migration_budget import allowance
    if not frozen.get('prior_budget'):
        allowance(frozen, None)
    return MigrationBudget.create(root, frozen)


def parameter_record(engine, baseline, requested, run):
    """Expose actual readback differences; missing observations are never defaults."""
    resolved = normal_parameters(engine, requested)
    effective = run.get('native', {}).get('normal_parameters_readback')
    return dict(
        baseline=baseline, requested=requested, resolved=resolved, effective=effective,
        changed_from_baseline={k: {'before': baseline[k], 'after': v}
                               for k, v in resolved.items() if v != baseline[k]},
        readback_matches=normal_readback_matches(engine, requested, run.get('native', {})),
        readback_differences={k: {'expected': v, 'observed': (effective or {}).get(k)}
                              for k, v in resolved.items() if (effective or {}).get(k) != v},
        declaration_matches=run.get('normal_parameters') == resolved,
    )


def command(argv, destination, deadline, process_record, *, environment=None):
    """Bound a native in-process engine child while retaining the guard process group."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired(argv, 0)
    with destination.open('xb') as log:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            publish(process_record, json_bytes({'pid': proc.pid, 'argv': argv}), replace=True)
            return proc.wait(timeout=remaining)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()


def run_trial(root, candidate_id, *, timeout_s=900, retry_reason=None):
    root = Path(root).resolve()
    budget = MigrationBudget(root)
    manifest = json.loads((root / 'manifest.json').read_bytes())
    validate(manifest)
    if manifest['source_sha256'] != sources():
        raise ValueError('Source changed; create an evidenced successor inheriting the old budget')
    candidate = next((r for r in manifest['matrix'] if r['id'] == candidate_id), None)
    if candidate is None:
        raise ValueError('Unknown frozen candidate')
    handle = {'parent_pid': os.getpid(), **execution_cgroup()}
    attempt = budget.reserve(candidate_id, handle,
                             timeout_s=timeout_s, retry_reason=retry_reason)
    directory = root / 'attempts' / f'{attempt:04d}'
    directory.mkdir()
    started = time.monotonic()
    outcome = 'failed'
    result = {'candidate_id': candidate_id, 'attempt': attempt, 'scope': 'development',
              'hypothesis': candidate['hypothesis'], 'expected_effect': candidate['expected_effect'],
              'evidence': candidate['evidence'], 'passed': False}
    try:
        for name, value in [('case.json', manifest['case']), ('parameters.json', candidate['parameters'])]:
            publish(directory / name, json_bytes(value))
        args = [sys.executable, '-m', 'dexlab.contact_indent_run']
        environment = dict(os.environ)
        if manifest['engine'] == 'mujoco':
            environment['DEXLAB_MUJOCO_PROFILE'] = manifest['runtime_profile']
        result['run_exit'] = command(
            [*args, '--protocol', 'normal-load', '--engine', manifest['engine'],
             '--case', str(directory / 'case.json'), '--normal-parameters', str(directory / 'parameters.json'),
             '--output', str(directory / 'raw'), '--measure-step-timing'],
            directory / 'run.log', started + timeout_s, directory / 'process.json', environment=environment)
        raw = directory / 'raw'
        if (raw / 'run.json').is_file():
            receipt = json.loads((raw / 'run.json').read_bytes())
            result['trial_binding_matches'] = (receipt.get('case') == manifest['case']
                                                and receipt.get('engine') == manifest['engine']
                                                and receipt.get('protocol') == 'normal-load')
            result['parameters'] = parameter_record(manifest['engine'], manifest['baseline'],
                                                    candidate['parameters'], receipt)
            result['cost'] = {k: receipt.get(k) for k in
                              ('total_seconds', 'step_and_observation_seconds', 'step_timing')}
            result['verify_exit'] = command([*args, '--verify', str(raw)], directory / 'verify.json',
                                             started + timeout_s, directory / 'process.json', environment=environment)
            score = json.loads((directory / 'verify.json').read_text())
            result['independent_score'] = score
            result['passed'] = (result['run_exit'] == 0 and result['verify_exit'] == 0
                                and score.get('passed') is True and result['trial_binding_matches']
                                and result['parameters']['readback_matches']
                                and result['parameters']['declaration_matches'])
            if receipt.get('status') == 'completed':
                outcome = 'recorded'  # A physical failure is evidence, never an infrastructure retry.
    except (KeyboardInterrupt, subprocess.TimeoutExpired) as exc:
        outcome = 'interrupted'
        result['error'] = type(exc).__name__
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        result['outcome'] = outcome
        result['artifact_sha256'] = {str(p.relative_to(directory)): digest(p.read_bytes())
                                     for p in sorted(directory.rglob('*')) if p.is_file()}
        result['wall_s'] = time.monotonic() - started
        result['within_reserved_wall'] = result['wall_s'] <= timeout_s
        result['passed'] = result['passed'] and result['within_reserved_wall']
        raw_result = json_bytes(result)
        publish(directory / 'result.json', raw_result)
        budget.finish(attempt, wall_s=result['wall_s'], evidence_sha256=digest(raw_result), outcome=outcome)
    return result


def recover(root):
    """Close a killed attempt after verifying its recorded process is gone."""
    root = Path(root).resolve()
    budget = MigrationBudget(root)
    active = [a for a in budget.status()['attempts'] if a['terminal'] is None]
    if len(active) != 1:
        raise ValueError('Expected one unfinished reservation')
    reservation = active[0]
    handle = reservation['handle']
    group = handle.get('cgroup', '')
    if not re.search(r'/dexlab-bounded-[0-9a-f]+\.service$', group):
        raise ValueError('Missing bounded cgroup identity; cannot establish child termination')
    if handle.get('boot_id') == Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        members = Path('/sys/fs/cgroup') / group.lstrip('/') / 'cgroup.procs'
        if members.exists() and members.read_text().strip():
            raise RuntimeError('Bounded cgroup still has processes; do not recover a live trial')
    directory = root / 'attempts' / f'{reservation["attempt"]:04d}'
    process = directory / 'process.json'
    # Parent PID covers the crash window before publishing the child PID.
    targets = [reservation['handle']['parent_pid']]
    if process.exists():
        targets.append(json.loads(process.read_bytes())['pid'])
    for pid in targets:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        raise RuntimeError('Recorded process is still present; recover it before closing the attempt')
    directory.mkdir(exist_ok=True)
    receipt = dict(outcome='interrupted', wall_source='full reserved allowance',
                   artifact_sha256={str(p.relative_to(directory)): digest(p.read_bytes())
                                     for p in sorted(directory.rglob('*')) if p.is_file()
                                     and p != directory / 'recovery.json'})
    raw = json_bytes(receipt)
    recovery = directory / 'recovery.json'
    if recovery.exists():
        if recovery.read_bytes() != raw:
            raise ValueError('Recovery evidence changed before ledger settlement')
    else:
        publish(recovery, raw)
    budget.finish(reservation['attempt'], wall_s=None, evidence_sha256=digest(raw), outcome='interrupted')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('manifest', type=Path)
    init.add_argument('root', type=Path)
    run = sub.add_parser('run')
    run.add_argument('root', type=Path)
    run.add_argument('candidate')
    run.add_argument('--timeout', type=int, default=900)
    run.add_argument('--retry-reason')
    sub.add_parser('recover').add_argument('root', type=Path)
    sub.add_parser('status').add_argument('root', type=Path)
    args = parser.parse_args()
    if args.action == 'init':
        value = create(args.root, json.loads(args.manifest.read_text())).status()
    elif args.action == 'run':
        value = run_trial(args.root, args.candidate, timeout_s=args.timeout, retry_reason=args.retry_reason)
    elif args.action == 'recover':
        value = recover(args.root)
    else:
        value = MigrationBudget(args.root).status()
    print(json.dumps(value, indent=2))
    if args.action == 'run' and not value['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
