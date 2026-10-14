"""Run frozen LIBERO cases under the existing resource and recovery ledger."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import time

from dexlab.contact_trials import command, execution_cgroup, recover
from dexlab.libero_workflow import TASK, UPSTREAM, file_hash
from dexlab.migration_budget import MigrationBudget, allowance, digest, json_bytes, publish


def source_hashes():
    root = Path(__file__).parent
    return {name: file_hash(root / name) for name in
            ('libero_workflow.py', 'libero_record.py', 'libero_score.py', 'libero_trials.py')}


def validate(manifest):
    if (manifest.get('schema_version') != 1 or manifest.get('task') != TASK
            or manifest.get('upstream_commit') != UPSTREAM):
        raise ValueError('This entrypoint accepts only the frozen cream-cheese task')
    candidates = manifest['candidates']
    if not 1 <= len(candidates) <= 8 or len({c['id'] for c in candidates}) != len(candidates):
        raise ValueError('Freeze one to eight unique candidates')
    for candidate in candidates:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', candidate['id']):
            raise ValueError('Invalid candidate identifier')
        if set(candidate) - {'solref_floor_s'} != {'id', 'mode', 'instrument', 'timestep_scale', 'hypothesis'}:
            raise ValueError('Incomplete or unknown candidate fields')
        if candidate['mode'] not in ('actions', 'observation-audit'):
            raise ValueError('State playback and policy claims are not executable evidence here')
        if candidate['timestep_scale'] not in (1., .5, .25) or not candidate['hypothesis'].strip():
            raise ValueError('Unsupported timestep or missing hypothesis')
        if candidate.get('solref_floor_s', 0.) not in (0., .004):
            raise ValueError('Only the declared 4 ms contact-reference control is supported')
        if type(candidate['instrument']) is not bool:
            raise ValueError('Explicit instrumentation switch required')
    development, heldout = manifest['development'], manifest['heldout']
    if (not development or not heldout or set(development) & set(heldout)
            or len(set(development + heldout)) != len(development + heldout)):
        raise ValueError('Development and heldout demonstrations must be distinct')
    for reference in manifest['inputs']:
        if file_hash(reference['path']) != reference['sha256']:
            raise ValueError('Input source or data changed')
    source = Path(manifest['libero_root'])
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != UPSTREAM:
        raise ValueError('Unexpected LIBERO source revision')
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Official baseline source must remain unchanged; patches are separate artifacts')


def create(root, manifest):
    validate(manifest)
    if not manifest.get('prior_budget'):
        allowance(manifest, None)
    matrix = [{'id': f"{c['id']}-{demo}"} for c in manifest['candidates']
              for demo in manifest['development'] + manifest['heldout']]
    frozen = dict(manifest, matrix=matrix, source_sha256=source_hashes())
    return MigrationBudget.create(root, frozen)


def run(root, candidate_id, demo, timeout=900, retry_reason=None):
    root = Path(root).resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    validate(manifest)
    if manifest['source_sha256'] != source_hashes():
        raise ValueError('Source changed: inherit the ledger in a new frozen revision')
    candidate = next((c for c in manifest['candidates'] if c['id'] == candidate_id), None)
    if candidate is None or demo not in manifest['development'] + manifest['heldout']:
        raise ValueError('Case outside the frozen matrix')
    selection_hash = None
    if demo in manifest['heldout']:
        selection = json.loads((root / 'selection.json').read_text())
        if candidate_id not in ('baseline', selection['candidate']):
            raise ValueError('Heldout is restricted to baseline and frozen selection')
        if selection['manifest_sha256'] != file_hash(root / 'manifest.json'):
            raise ValueError('Selection belongs to another frozen protocol')
        for name, expected in selection['sources'].items():
            source = (root / name).resolve()
            if not source.is_relative_to(root) or file_hash(source) != expected:
                raise ValueError('Development evidence changed after selection')
        selection_hash = file_hash(root / 'selection.json')
        for previous in MigrationBudget(root).status()['attempts']:
            frozen = previous['handle'].get('selection_sha256')
            if frozen is not None and frozen != selection_hash:
                raise ValueError('Heldout selection changed during evaluation')
    budget = MigrationBudget(root)
    attempt = budget.reserve(f'{candidate_id}-{demo}',
                             dict(parent_pid=os.getpid(), selection_sha256=selection_hash, **execution_cgroup()),
                             timeout_s=timeout, retry_reason=retry_reason)
    directory = root / 'attempts' / f'{attempt:04d}'
    directory.mkdir()
    started = time.monotonic()
    result = {'candidate': candidate, 'demo': demo,
              'split': 'development' if demo in manifest['development'] else 'heldout',
              'passed': False, 'outcome': 'failed', 'selection_sha256': selection_hash}
    try:
        payload = dict(manifest, candidate=candidate, demo=demo)
        publish(directory / 'input.json', json_bytes(payload))
        environment = dict(os.environ, MUJOCO_GL='egl',
                           PYTHONPATH=os.pathsep.join((str(Path(__file__).parents[1]), manifest['libero_root'])),
                           LIBERO_CONFIG_PATH=str(Path(manifest['config_dir']).resolve()),
                           NUMBA_CACHE_DIR=str(Path(manifest['cache_dir']).resolve()))
        args = [manifest['python'], '-m', 'dexlab.libero_record', str(directory / 'input.json'), str(directory / 'raw')]
        result['run_exit'] = command(args, directory / 'run.log', started + timeout,
                                     directory / 'process.json', environment=environment)
        if (directory / 'raw' / 'run.json').exists():
            args = [manifest['python'], '-m', 'dexlab.libero_score', str(directory / 'raw')]
            result['verify_exit'] = command(args, directory / 'score.json', started + timeout,
                                            directory / 'process.json', environment=environment)
            result['score'] = json.loads((directory / 'score.json').read_text())
            result['passed'] = result['run_exit'] == result['verify_exit'] == 0
            if result['run_exit'] == 0:
                result['outcome'] = 'recorded'
    except (KeyboardInterrupt, subprocess.TimeoutExpired) as error:
        result.update(outcome='interrupted', error=type(error).__name__)
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    finally:
        result['wall_s'] = time.monotonic() - started
        result['artifact_sha256'] = {str(p.relative_to(directory)): file_hash(p)
                                     for p in sorted(directory.rglob('*')) if p.is_file()}
        raw = json_bytes(result)
        publish(directory / 'result.json', raw)
        budget.finish(attempt, wall_s=result['wall_s'], evidence_sha256=digest(raw), outcome=result['outcome'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('manifest', type=Path)
    init.add_argument('root', type=Path)
    execute = sub.add_parser('run')
    execute.add_argument('root', type=Path)
    execute.add_argument('candidate')
    execute.add_argument('demo')
    execute.add_argument('--timeout', type=int, default=900)
    execute.add_argument('--retry-reason')
    sub.add_parser('status').add_argument('root', type=Path)
    sub.add_parser('recover').add_argument('root', type=Path)
    args = parser.parse_args()
    if args.action == 'init':
        result = create(args.root, json.loads(args.manifest.read_text())).status()
    elif args.action == 'run':
        result = run(args.root, args.candidate, args.demo, args.timeout, args.retry_reason)
    elif args.action == 'recover':
        result = recover(args.root)
    else:
        result = MigrationBudget(args.root).status()
    print(json.dumps(result, indent=2, allow_nan=False))
    if args.action == 'run' and result['outcome'] != 'recorded':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
