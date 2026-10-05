#!/usr/bin/env python3
"""Low-priority, uncompressed, verified archival using private deployment config."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

from dexlab.archive_integrity import finalize, snapshot, write_receipt

ROOT = Path(__file__).resolve().parents[1]


def relative(value):
    path = PurePosixPath(value)
    if (path.is_absolute() or '..' in path.parts or value in ('', '.')
            or '\\' in value or path.as_posix() != value):
        raise ValueError('Use a normalized path relative to the private remote root')
    return path


def read_apple(directory):
    """Read archived model/poses without editing paths or evidence on disk."""
    import mujoco
    import numpy as np
    from verify_sdf_grasp import verify_grasp
    engine = json.loads((directory / 'engine.json').read_text())
    if engine.get('completed') is not True:
        raise ValueError('Archive only sealed complete episodes, including scored failures')
    if engine['backend'] == 'mujoco':
        from dexlab.mujoco_artifacts import load_model
        model = load_model(directory)
        model_kind = 'native_mujoco_model'
        with np.load(directory / 'sdf-dynamics.npz', allow_pickle=False) as dynamics:
            positions = dynamics['qpos']
            if (positions.ndim != 2 or positions.shape[1] != model.nq
                    or not len(positions) or not np.isfinite(positions).all()):
                raise ValueError('Invalid recorded native joint states')
            final_qpos = positions[-1].copy()
    elif engine['backend'] == 'superdex':
        # A SuperDex display scene is a rendering proxy, not a native checkpoint.
        assets = ROOT / 'demos/apple-stem-grasp/assets'
        manifest = json.loads((assets.parent / 'assets.json').read_text())
        hashes = {}
        for archive in manifest['archives']:
            hashes.update(archive['files'])
        hashes.update({item['path']: item['sha256'] for item in manifest['files']})
        hashes.update(manifest.get('repository_files', {}))
        xml = ET.fromstring((directory / 'display.xml').read_text())
        for element in xml.iter():
            reference = element.get('file')
            if reference is None:
                continue
            if '/assets/' not in reference:
                raise ValueError('Display asset is outside the published asset profile')
            name = str(relative(reference.rsplit('/assets/', 1)[1]))
            target = assets / name
            with target.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if hashes.get(name) != digest:
                raise ValueError('Display asset is missing or differs from its manifest')
            element.set('file', str(target.resolve()))
        model = mujoco.MjModel.from_xml_string(ET.tostring(xml, encoding='unicode'))
        model_kind = 'visual_mocap_proxy_not_superdex_checkpoint'
    else:
        raise ValueError('Unsupported archived apple backend')
    with np.load(directory / 'trajectory.npz', allow_pickle=False) as trajectory:
        frames = trajectory['frames']
        if (frames.ndim != 3 or frames.shape[-1] != 7 or not len(frames)
                or not frames.shape[1] or not np.isfinite(frames).all()):
            raise ValueError('Invalid recorded display poses')
    data = mujoco.MjData(model)
    if engine['backend'] == 'mujoco':
        data.qpos[:] = final_qpos
    else:
        if frames.shape[1] != model.nmocap:
            raise ValueError('Display poses do not match the archived model')
        data.mocap_pos[:] = frames[-1, :, :3]
        data.mocap_quat[:] = frames[-1][:, [6, 3, 4, 5]]
    mujoco.mj_fwdPosition(model, data)
    if not np.isfinite(data.xpos).all():
        raise ValueError('Nonfinite offline body positions')
    score = verify_grasp(directory)
    return {'readable': True, 'model_kind': model_kind, 'body_count': model.nbody,
            'saved_frames': len(frames), 'scientific_acceptance': score['passed'],
            'score': score}


@contextmanager
def record_stage(path, name):
    """Persist the last archival stage even if the worker is killed."""
    start = time.monotonic()
    record = {'stage': name, 'state': 'running', 'started_at_unix_s': time.time()}
    write_receipt(path, record)
    try:
        yield
    except BaseException:
        record.update(state='failed', wall_s=time.monotonic() - start)
        write_receipt(path, record)
        raise
    else:
        record.update(state='completed', wall_s=time.monotonic() - start)
        write_receipt(path, record)


def archive(args):
    config = json.loads(args.config.read_text())
    host, remote_root = config['ssh_alias'], PurePosixPath(config['remote_root'])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', host) or not remote_root.is_absolute():
        raise ValueError('Use a private SSH alias and an absolute remote root')
    checkout = remote_root / relative(args.checkout)
    source = remote_root / relative(args.source)
    policy = config['archive_policy']
    local_root = Path(policy['local_root'])
    if not local_root.is_dir():
        raise ValueError('Private archive volume must already be mounted/prepared')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.archive_id):
        raise ValueError('Use one new archive directory name')
    operation = uuid.uuid4().hex
    remote_state = remote_root / '.research'
    receipts = local_root / '.receipts'
    receipts.mkdir(exist_ok=True)
    def guarded_remote(command, label):
        arguments = ['nice', '-n', str(policy['nice']), 'ionice', '-c', '3', 'python3',
                     str(checkout / 'scripts/research_guard.py'), 'run',
                     '--lock', str(remote_state / 'window.lock'), '--kind', 'archive',
                     '--receipt', str(remote_state / 'receipts' / (operation + '-' + label + '.json')),
                     '--', *command]
        return shlex.join(arguments)
    def remote_json(command, label):
        return json.loads(subprocess.check_output([
            'ssh', '-o', 'BatchMode=yes', '-o', 'ForwardAgent=no', '-o', 'Compression=no',
            host, guarded_remote(command, label)], text=True))
    scan = [str(checkout / '.venv/bin/python'), str(checkout / 'scripts/archive_run.py'),
            'snapshot', '--source', str(source), '--boundary', str(remote_root)]
    # Remote lock/recovery is checked before any local scan or hashing begins.
    with record_stage(receipts / (operation + '-source-before.json'), 'remote_source_snapshot_before'):
        before = remote_json(scan, 'before')
    source_receipt = receipts / (args.archive_id + '-source.json')
    identity = {'checkout': str(checkout), 'source': str(source), 'manifest': before}
    if source_receipt.exists() and json.loads(source_receipt.read_text()) != identity:
        raise ValueError('Source identity changed; preserve the old staging directory')
    write_receipt(source_receipt, identity)
    stage = local_root / ('.incoming-' + args.archive_id)
    destination = local_root / args.archive_id
    if stage.is_symlink() or destination.is_symlink():
        raise ValueError('Archive directories must not be symlinks')
    if not destination.exists():
        stage.mkdir(exist_ok=True)
        with record_stage(receipts / (operation + '-transfer.json'), 'transfer'):
            subprocess.run([
                'rsync', '-a', '--partial', '--protect-args', '--no-compress',
                '--bwlimit=' + str(policy['bandwidth_KiB_per_second']),
                '-e', 'ssh -o BatchMode=yes -o ForwardAgent=no -o Compression=no',
                '--rsync-path=' + guarded_remote(['rsync'], 'transfer'),
                str(host) + ':' + str(source) + '/', str(stage) + '/',
            ], check=True)
    with record_stage(receipts / (operation + '-source-after.json'), 'remote_source_snapshot_after'):
        after = remote_json(scan, 'after')
    with record_stage(receipts / (operation + '-finalize.json'), 'local_verify_read_score_and_promote'):
        result = finalize(stage, destination, before, after, read_apple,
                          receipt_path=receipts / (args.archive_id + '-complete.json'))
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('archive', '_archive'):
        action = sub.add_parser(name)
        action.add_argument('--config', required=True, type=Path)
        action.add_argument('--checkout', required=True)
        action.add_argument('--source', required=True)
        action.add_argument('--archive-id', required=True)
    scan = sub.add_parser('snapshot')
    scan.add_argument('--source', required=True, type=Path)
    scan.add_argument('--boundary', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'snapshot':
        if not args.source.resolve().is_relative_to(args.boundary.resolve()):
            parser.error('Source escaped the private execution boundary')
        print(json.dumps(snapshot(args.source)))
    elif args.command == '_archive':
        from bounded_run import current_cgroup, verify_limits
        config = json.loads(args.config.read_text())
        device = Path(config['archive_policy']['io_device']).stat().st_rdev
        verify_limits(current_cgroup(), f'{os.major(device)}:{os.minor(device)}',
                      8 * 1024 ** 3, 6 * 1024 ** 3)
        archive(args)
    else:
        config = json.loads(args.config.read_text())
        root = Path(config['archive_policy']['local_root'])
        if not root.is_dir():
            parser.error('Archive volume must already exist')
        control = root / '.control'
        device = config['archive_policy'].get('io_device')
        if not device:
            parser.error('Private archive_policy.io_device is required for hard I/O bounds')
        command = ['nice', '-n', str(config['archive_policy']['nice']), 'ionice', '-c', '3',
                   sys.executable, str(ROOT / 'scripts/research_guard.py'), 'run',
                   '--lock', str(control / 'window.lock'), '--kind', 'archive',
                   '--receipt', str(control / (uuid.uuid4().hex + '.json')), '--',
                   sys.executable, str(Path(__file__).resolve()), '_archive', *sys.argv[2:]]
        bounded = [sys.executable, str(ROOT / 'scripts/bounded_run.py'),
                   '--io-device', device, '--receipt',
                   str(control / (uuid.uuid4().hex + '-resources.json')), '--', *command]
        raise SystemExit(subprocess.run(bounded, check=False).returncode)


if __name__ == '__main__':
    main()
