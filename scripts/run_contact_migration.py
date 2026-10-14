#!/usr/bin/env python3
"""Freeze, execute and independently check the bounded Genesis migration trial.

Run using the isolated candidate environment. Native processes remain under
the repository's bounded_run/research_guard tools. Evidence stays private by
default; publishing a report requires the normal repository delivery gates.
"""
import argparse
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from dexlab.cloth_engines import package_identity
from dexlab.contact_migration import comparison_matrix, compare_recordings, read_recording
from dexlab.migration_budget import MigrationBudget, digest, json_bytes, publish

ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = ('mujoco', 'genesis-world', 'quadrants', 'torch', 'numpy', 'scipy')
RUNNERS = {'native': 'scripts/references/genesis_pinch_native.py',
           'unisim': 'src/dexlab/genesis_pinch_probe.py'}


def hashes(root):
    return {str(path.relative_to(root)): digest(path.read_bytes())
            for path in sorted(root.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}


def dependencies():
    return dict(sorted((dist.metadata['Name'], dist.version) for dist in metadata.distributions()))


def runtime_identity():
    return {name: {key: value for key, value in package_identity(name).items()
                   if key != 'installation_origin'} for name in RUNTIMES}


def runtime_stamps():
    """Detect environment changes between full byte checks at freeze and final check."""
    result = {}
    for name in RUNTIMES:
        dist = metadata.distribution(name)
        for entry in dist.files or ():
            if str(entry).endswith('.py') or '.so' in entry.name:
                stat = dist.locate_file(entry).stat()
                result[f'{name}/{entry}'] = [stat.st_size, stat.st_mtime_ns, stat.st_ino]
    return result


def source_paths(root, *, dexlab):
    paths = list((root/'src').rglob('*.py'))
    for name in ('pyproject.toml', 'uv.lock'):
        if (root/name).is_file():
            paths.append(root/name)
    if dexlab:
        paths += [root/name for name in (
            'demos/contact-benchmark/force-limit-v1.json',
            'scripts/bounded_run.py', 'scripts/research_guard.py',
            'scripts/run_contact_migration.py', RUNNERS['native'],
            'docs/unisim-contact-migration.md', 'docs/unisim-contact-migration.zh-CN.md')]
    return sorted(set(paths))


def freeze(args):
    from dexlab.genesis_pinch_probe import create_scene

    roots = dict(dexlab=ROOT, unisim=args.unisim_root.resolve(strict=True))
    for module, root in roots.items():
        spec = importlib.util.find_spec(module)
        if spec is None or spec.origin is None or Path(spec.origin).resolve() != root/'src'/module/'__init__.py':
            raise ValueError(f'{module} editable installation does not point to its candidate tree')
    official = json.loads(args.official_receipt.read_bytes())
    identity = runtime_identity()
    for name in ('mujoco', 'genesis-world', 'quadrants'):
        expected = official[name]['official_wheel']['package_code_sha256']
        if identity[name]['code_sha256'] != expected or identity[name]['version'] != official[name]['installed']['version']:
            raise ValueError(f'Installed {name} differs from admitted official artifact')
    sources = {name: {str(path.relative_to(root)): digest(path.read_bytes())
                      for path in source_paths(root, dexlab=name == 'dexlab')}
               for name, root in roots.items()}
    cases = json.loads((ROOT/'demos/contact-benchmark/force-limit-v1.json').read_bytes())['cases']
    matrix = comparison_matrix(cases)
    for case in matrix:
        case['matched_batched_info'] = args.native_storage == 'matched'
        if case['route'] == 'unisim':
            case['recording_route'] = 'unisim_public'
    if len(matrix) != 38:
        raise ValueError('Migration matrix changed; review protocol first')
    model_bytes = {}
    args.directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.directory.parent) as temporary:
        for case in matrix:
            if case['route'] != 'unisim':
                continue
            folder = Path(temporary)/case['pair']
            folder.mkdir()
            condition = case['case']
            create_scene(folder, condition['force_limit_N'] if condition else 10.,
                         condition['initial_x_m'] if condition else 0.)
            model_bytes.update({str(path.relative_to(temporary)): path.read_bytes()
                                for path in folder.glob('*.xml')})
    manifest = dict(schema=1, matrix=matrix, sources=sources,
                    models={key: digest(value) for key, value in model_bytes.items()},
                    roots={key: str(value) for key, value in roots.items()},
                    base_revisions={name: subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root,
                                                                  text=True).strip() for name, root in roots.items()},
                    python=dict(version=platform.python_version(), executable=sys.executable),
                    dependencies=dependencies(), runtimes=identity, runtime_stamps=runtime_stamps(),
                    official_artifacts=official, thresholds=dict(initial=1e-12, state=1e-9, force_N=1e-7,
                                                                  epoch_s=1e-12),
                    budget=dict(max_starts=48, cumulative_wall_s=5400, process_wall_s=900))
    manifest['resources'] = dict(profile='adaptive', cpu_cores=args.cpu_cores)
    peak_receipt = args.peak_receipt.read_bytes() if args.peak_receipt is not None else None
    if peak_receipt is not None:
        manifest['resources']['peak_receipt_sha256'] = digest(peak_receipt)
    if args.previous_comparison is not None:
        previous = MigrationBudget(args.previous_comparison)
        state = previous.status()
        manifest['prior_budget'] = dict(directory=str(previous.root),
                                       manifest_sha256=state['manifest_sha256'],
                                       head_sha256=digest((previous.root/'head.json').read_bytes()),
                                       starts_used=state['starts_used'],
                                       wall_s=state['wall_charged_or_reserved_s'])
        if state.get('work_package') is not None:
            manifest['work_package'] = state['work_package']
    if args.work_package is not None:
        manifest['work_package'] = json.loads(args.work_package.read_bytes())
    if 'work_package' in manifest:
        package = manifest['work_package']
        manifest['budget'] = dict(max_starts=package['max_starts'], cumulative_wall_s=package['wall_s'],
                                  process_wall_s=900, scope='work_package; lifetime ledger retained')
    ledger = MigrationBudget.create(args.directory, manifest)
    if peak_receipt is not None:
        publish(args.directory/'prior-resources.json', peak_receipt)
    for name, files in sources.items():
        for relative, expected in files.items():
            raw = (roots[name]/relative).read_bytes()
            if digest(raw) != expected:
                raise ValueError('Source changed during freeze')
            target = args.directory/'sources'/name/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            publish(target, raw)
    for relative, raw in model_bytes.items():
        target = args.directory/'models'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        publish(target, raw)
    return ledger.status()


def verify_sources(directory, manifest, *, live):
    expected_peak = manifest.get('resources', {}).get('peak_receipt_sha256')
    if expected_peak is not None and digest((directory/'prior-resources.json').read_bytes()) != expected_peak:
        raise ValueError('Frozen resource measurement changed')
    for name, files in manifest['sources'].items():
        root = Path(manifest['roots'][name]) if live else directory/'sources'/name
        for relative, expected in files.items():
            if digest((root/relative).read_bytes()) != expected:
                raise ValueError(f'Frozen source hash mismatch: {name}/{relative}')
        if live and {str(path.relative_to(root)) for path in source_paths(root, dexlab=name == 'dexlab')} != set(files):
            raise ValueError('Frozen source file set changed')
    if hashes(directory/'models') != manifest['models']:
        raise ValueError('Frozen model bytes changed')


def seal_attempt(directory, ledger, attempt):
    """Only a terminal bounded receipt can release a reservation automatically."""
    folder = directory/'attempts'/f'{attempt["attempt"]:04d}'
    receipt = json.loads((folder/'resources.json').read_bytes())
    if receipt['state'] not in ('completed', 'failed'):
        raise RuntimeError('Bounded process has no terminal receipt; recover its live handle')
    service = subprocess.run(['systemctl', '--system', 'is-active', receipt['service']],
                             text=True, capture_output=True, check=False)
    if service.stdout.strip() not in ('inactive', 'failed', 'unknown'):
        raise RuntimeError('Native service is still active or cannot be verified')
    manifest = json.loads((directory/'manifest.json').read_bytes())
    admission_error = None
    try:
        verify_sources(directory, manifest, live=True)
        if dependencies() != manifest['dependencies'] or runtime_stamps() != manifest['runtime_stamps']:
            raise ValueError('Runtime changed during the attempt')
    except (ValueError, OSError) as error:
        admission_error = str(error)
    evidence = dict(case_id=attempt['case_id'], files=hashes(folder),
                    manifest_sha256=ledger.status()['manifest_sha256'],
                    admission_error=admission_error)
    raw = json_bytes(evidence)
    evidence_path = folder/'evidence.json'
    if evidence_path.exists():
        # Recovery after sealing but before appending terminal must use the same bytes.
        saved = json.loads(evidence_path.read_bytes())
        observed = hashes(folder)
        observed.pop('evidence.json')
        if saved['files'] != observed or saved['case_id'] != attempt['case_id']:
            raise ValueError('Attempt changed after sealing')
        raw = evidence_path.read_bytes()
        admission_error = saved['admission_error']
    else:
        publish(evidence_path, raw)
    ledger.finish(attempt['attempt'], wall_s=receipt['wall_s'], evidence_sha256=digest(raw),
                  outcome='recorded' if receipt['state'] == 'completed' and admission_error is None else 'failed')


def run(args):
    ledger = MigrationBudget(args.directory)
    status = ledger.status()
    if status['attempts'] and status['attempts'][-1]['terminal'] is None:
        seal_attempt(args.directory, ledger, status['attempts'][-1])
        status = ledger.status()
    manifest = json.loads((args.directory/'manifest.json').read_bytes())
    verify_sources(args.directory, manifest, live=False)
    verify_sources(args.directory, manifest, live=True)
    if dependencies() != manifest['dependencies'] or runtime_stamps() != manifest['runtime_stamps']:
        raise ValueError('Frozen runtime changed; require new source/runtime admission')
    if platform.python_version() != manifest['python']['version'] or sys.executable != manifest['python']['executable']:
        raise ValueError('Different Python environment')
    case = next(case for case in manifest['matrix'] if case['id'] == args.case)
    index = ledger.reserve(args.case, {'pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                                     'resources': f'attempts/{len(status["attempts"]):04d}/resources.json'},
                           retry_reason=args.retry_reason)
    folder = args.directory/'attempts'/f'{index:04d}'
    folder.mkdir()
    runner = ROOT/RUNNERS[case['route']]
    command = [sys.executable, str(runner), str(folder/'records'), '--dt', str(case['dt_s'])]
    if case['case'] is not None:
        command += ['--case-id', case['case']['id']]
    if case['route'] == 'native' and case.get('matched_batched_info'):
        command.append('--batched-info')
    bounded = [sys.executable, str(ROOT/'scripts/bounded_run.py'), *resource_flags(args.directory, manifest),
               '--io-device', str(args.io_device), '--data-dir', str(args.data_dir), '--timeout', '900',
               '--receipt', str(folder/'resources.json'), '--', sys.executable,
               str(ROOT/'scripts/research_guard.py'), 'run', '--lock', str(args.lock),
               '--kind', 'timing', '--receipt', str(folder/'window.json'), '--', *command]
    with (folder/'process.log').open('xb') as log:
        subprocess.run(bounded, stdout=log, stderr=subprocess.STDOUT, check=False, cwd=ROOT)
    seal_attempt(args.directory, ledger, ledger.status()['attempts'][-1])
    return ledger.status()


def resource_flags(directory, manifest):
    """Historical batches keep their envelope; new batches freeze one measured plan."""
    resources = manifest.get('resources')
    if resources is None:
        return ['--profile', 'experiment']
    flags = ['--profile', 'adaptive', '--resource-plan', str(directory/'resource-plan.json'),
             '--cpu-cores', str(resources['cpu_cores'])]
    if 'peak_receipt_sha256' in resources:
        flags += ['--peak-receipt', str(directory/'prior-resources.json')]
    return flags


def check(args):
    ledger = MigrationBudget(args.directory)
    status = ledger.status()
    manifest = json.loads((args.directory/'manifest.json').read_bytes())
    verify_sources(args.directory, manifest, live=False)
    # Offline rescoring can use archived acquisition trees after production
    # changes, but its own scoring/identity implementation must remain bound.
    for relative in ('scripts/run_contact_migration.py', 'src/dexlab/contact_migration.py',
                     'src/dexlab/genesis_pinch_score.py', 'src/dexlab/adapter_qualification.py',
                     'src/dexlab/migration_budget.py', 'src/dexlab/cloth_engines.py'):
        if digest((ROOT/relative).read_bytes()) != manifest['sources']['dexlab'][relative]:
            raise ValueError('Offline checker differs from frozen source')
    recordings = {}
    for attempt in status['attempts']:
        terminal = attempt['terminal']
        if terminal is None:
            continue
        folder = args.directory/'attempts'/f'{attempt["attempt"]:04d}'
        raw = (folder/'evidence.json').read_bytes()
        evidence = json.loads(raw)
        actual = hashes(folder)
        actual.pop('evidence.json')
        if (digest(raw) != terminal['evidence_sha256'] or actual != evidence['files']
                or evidence['manifest_sha256'] != status['manifest_sha256']):
            raise ValueError('Attempt evidence hash mismatch')
        if terminal['outcome'] == 'recorded':
            case = next(row for row in manifest['matrix'] if row['id'] == attempt['case_id'])
            if case['id'] in recordings:
                raise ValueError('Duplicate completed case')
            if case['route'] == 'unisim':
                for model in (args.directory/'models'/case['pair']).glob('*.xml'):
                    if model.read_bytes() != (folder/'records'/model.name).read_bytes():
                        raise ValueError('Run model differs from frozen model')
            # Keep paths until this pair is scored. Holding the entire campaign's
            # decoded trajectories at once exceeds the bounded archive worker.
            recordings[case['id']] = (folder/'records', case,
                                      manifest['sources']['dexlab'][RUNNERS[case['route']]])
    results, missing = {}, []
    for case in manifest['matrix']:
        if case['route'] != 'native':
            continue
        keys = (case['pair']+'-native', case['pair']+'-unisim')
        if any(key not in recordings for key in keys):
            missing.extend(key for key in keys if key not in recordings)
        else:
            results[case['pair']] = compare_recordings(
                read_recording(*recordings[keys[0]]), read_recording(*recordings[keys[1]]), case)
    if args.verify_runtime and runtime_identity() != manifest['runtimes']:
        raise ValueError('Installed runtime bytes differ from frozen admission')
    physical_passed = bool(results) and all(row['passed'] for row in results.values())
    return dict(passed=not missing and physical_passed and args.verify_runtime,
                coverage_complete=not missing, physical_comparison_passed=physical_passed,
                missing=missing, comparison_results=results,
                runtime_reverified=args.verify_runtime, budget=status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run', 'status', 'check'))
    parser.add_argument('directory', type=Path)
    parser.add_argument('--unisim-root', type=Path)
    parser.add_argument('--official-receipt', type=Path)
    parser.add_argument('--previous-comparison', type=Path,
                        help='Retire a superseded candidate and inherit all its budget/evidence')
    parser.add_argument('--work-package', type=Path,
                        help='New evidenced development allowance; revisions inherit it by default')
    parser.add_argument('--peak-receipt', type=Path, help='Measured prior receipt to freeze new batch resources')
    parser.add_argument('--cpu-cores', type=int, choices=(4, 8), default=4)
    parser.add_argument('--native-storage', choices=('historical', 'matched'), default='matched',
                        help='New freezes align native parameter storage; historical retains the old comparison')
    parser.add_argument('--case')
    parser.add_argument('--retry-reason')
    parser.add_argument('--io-device', type=Path)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--lock', type=Path)
    parser.add_argument('--verify-runtime', action='store_true')
    args = parser.parse_args()
    args.directory = args.directory.resolve()
    required = {'freeze': ('unisim_root', 'official_receipt'), 'run': ('case', 'io_device', 'data_dir', 'lock')}
    if any(getattr(args, key) is None for key in required.get(args.action, ())):
        parser.error(f'Missing required options for {args.action}')
    result = MigrationBudget(args.directory).status() if args.action == 'status' else globals()[args.action](args)
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(args.action == 'check' and not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
