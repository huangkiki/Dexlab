#!/usr/bin/env python3
"""Run local research in a verified Linux systemd resource envelope."""

import argparse
import json
import os
import re
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import time
import uuid

from research_guard import atomic_json

FILES = ('memory.max', 'memory.high', 'memory.swap.max', 'cpu.max',
         'pids.max', 'io.max')
PROFILES = {
    'archive': dict(memory=8192, high=6144, cpu=100, tasks=32, timeout=900, read=16777216, write=8388608),
    'experiment': dict(memory=16384, high=15360, cpu=200, tasks=128, timeout=3600, read=33554432, write=16777216),
}
# Explicit opt-in after measured pressure; the default experiment cap is unchanged.
PROFILES['experiment-24g'] = {**PROFILES['experiment'], 'memory': 24576, 'high': 23552}

METRICS = ('memory.current', 'memory.peak', 'memory.events', 'cpu.stat',
           'pids.current', 'pids.events', 'io.stat')


def read_values(root, names):
    return {name: (root / name).read_text().strip() for name in names}


def verify_limits(root, device, memory, high, profile='archive'):
    policy = PROFILES[profile]
    limits = read_values(root, FILES)
    expected = {'memory.max': str(memory), 'memory.high': str(high),
                'memory.swap.max': '0', 'cpu.max': f"{policy['cpu'] * 1000} 100000",
                'pids.max': str(policy['tasks'])}
    if any(limits[key] != value for key, value in expected.items()):
        raise RuntimeError('Effective cgroup limits differ from the requested envelope')
    rows = {parts[0]: dict(field.split('=', 1) for field in parts[1:])
            for line in limits['io.max'].splitlines() if (parts := line.split())}
    if rows.get(device, {}).get('rbps') != str(policy['read']) or rows.get(device, {}).get('wbps') != str(policy['write']):
        raise RuntimeError('Effective data-device I/O limits are missing or different')
    return limits


def experiment_admission(data_dir, device_number, memory):
    """Require measured headroom and a directly mapped data block device."""
    data_dir = data_dir.resolve(strict=True)
    if not data_dir.is_dir():
        raise ValueError('Data directory must exist')
    device = data_dir.stat().st_dev
    block = Path('/sys/dev/block') / f'{os.major(device)}:{os.minor(device)}'
    if not block.exists():
        raise ValueError('Data directory must reside on a block-backed filesystem')
    block = block.resolve()
    devices = [(block / 'dev').read_text().strip()]
    if (block / 'partition').exists():
        devices.append((block.parent / 'dev').read_text().strip())
    if device_number not in devices:
        raise ValueError('I/O device does not cover the data directory; stacked devices require separate qualification')
    fields = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(fields['MemAvailable'].split()[0]) * 1024
    free = shutil.disk_usage(data_dir).free
    verify_headroom(available, free, memory)
    return {'available_memory_bytes': available, 'data_free_bytes': free,
            'desktop_reserve_bytes': 8 * 1024**3, 'data_device': device_number}


def verify_headroom(available, free, memory):
    if available < memory + 8 * 1024**3:
        raise RuntimeError('Insufficient available RAM for the envelope plus 8 GiB desktop reserve')
    if free < 20 * 1024**3:
        raise RuntimeError('Data volume requires at least 20 GiB free before admission')


def counters(values, device):
    cpu = dict(line.split() for line in values['cpu.stat'].splitlines())
    rows = {parts[0]: dict(field.split('=', 1) for field in parts[1:])
            for line in values['io.stat'].splitlines() if (parts := line.split())}
    io = rows.get(device, {})
    return int(cpu['usage_usec']), int(io.get('rbytes', 0)), int(io.get('wbytes', 0))


def current_cgroup():
    group = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
                 if line.startswith('0::'))
    return Path('/sys/fs/cgroup') / group.lstrip('/')


def verify_service(unit, timeout, tasks):
    result = subprocess.run(['systemctl', '--system', 'show', unit, '--no-pager',
                             '-p', 'LoadState', '-p', 'RuntimeMaxUSec',
                             '-p', 'TasksMax', '-p', 'KillMode'],
                            text=True, capture_output=True, check=True)
    values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    duration = values.get('RuntimeMaxUSec', '')
    if not re.fullmatch(r'(?:\d+(?:min|h|s)\s*)+', duration):
        raise RuntimeError('Finite service runtime could not be verified')
    seconds = sum(int(value) * {'h': 3600, 'min': 60, 's': 1}[suffix]
                  for value, suffix in re.findall(r'(\d+)(min|h|s)', duration))
    if (values.get('LoadState') != 'loaded' or seconds != timeout
            or values.get('TasksMax') != str(tasks) or values.get('KillMode') != 'control-group'):
        raise RuntimeError('Effective service properties differ from the requested envelope')
    return values


def inside(args):
    if os.getuid() == 0:
        raise RuntimeError('Workload must run as an unprivileged user')
    root = current_cgroup()
    limits = verify_limits(root, args.device_number, args.memory_bytes, args.high_bytes, args.profile)
    admission = (experiment_admission(args.data_dir, args.device_number, args.memory_bytes)
                 if args.profile != 'archive' else None)
    service = verify_service(root.name, args.timeout, PROFILES[args.profile]['tasks'])
    state = {'state': 'running', 'profile': args.profile, 'admission': admission,
             'effective_service_properties': service,
             'effective_limits': limits,
             'started_at_unix_s': time.time(), 'initial': read_values(root, METRICS)}
    atomic_json(args.telemetry, state)
    start = time.monotonic()
    previous_time = start
    previous = counters(state['initial'], args.device_number)
    peaks = [0.0, 0.0, 0.0]
    child = subprocess.Popen(args.command)
    while child.poll() is None:
        now = time.monotonic()
        latest = read_values(root, METRICS)
        current = counters(latest, args.device_number)
        rates = [(new - old) / (now - previous_time) for new, old in zip(current, previous)]
        rates[0] /= 1e6
        peaks = [max(old, new) for old, new in zip(peaks, rates)]
        state.update(wall_s=now - start, latest=latest,
                     sampled_peak_cpu_cores=peaks[0], sampled_peak_read_bytes_s=peaks[1],
                     sampled_peak_write_bytes_s=peaks[2], sampling_interval_s=0.25)
        previous_time, previous = now, current
        atomic_json(args.telemetry, state)
        time.sleep(0.25)
    state.update(state='completed', returncode=child.returncode,
                 wall_s=time.monotonic() - start, final=read_values(root, METRICS))
    atomic_json(args.telemetry, state)
    return child.returncode


def launch(args):
    policy = PROFILES[args.profile]
    device = args.io_device.resolve(strict=True)
    info = device.stat()
    if not stat.S_ISBLK(info.st_mode):
        raise ValueError('I/O device must be a block device')
    if os.getuid() == 0:
        raise ValueError('Launch as the ordinary workload owner, not root')
    device_number = f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}'
    if args.profile != 'archive':
        experiment_admission(args.data_dir, device_number, args.memory_mib * 1024**2)
    args.receipt = args.receipt.resolve()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation preserves previous evidence even across failed launches.
    with args.receipt.open('x') as stream:
        json.dump({'state': 'starting', 'started_at_unix_s': time.time()}, stream)
    telemetry = args.receipt.with_name(args.receipt.name + '.cgroup.json')
    if telemetry.exists():
        raise FileExistsError('Existing cgroup evidence must not be overwritten')
    unit = 'dexlab-bounded-' + uuid.uuid4().hex
    memory, high = args.memory_mib * 1024 ** 2, args.high_mib * 1024 ** 2
    properties = [f'MemoryMax={memory}', f'MemoryHigh={high}', 'MemorySwapMax=0',
                  f"CPUQuota={policy['cpu']}%", 'CPUQuotaPeriodSec=100ms', f"TasksMax={policy['tasks']}",
                  f'RuntimeMaxSec={args.timeout}', 'TimeoutStopSec=5',
                  'KillMode=control-group', 'OOMPolicy=stop', 'Nice=15',
                  'CPUAccounting=yes', 'MemoryAccounting=yes', 'IOAccounting=yes',
                  'IOSchedulingClass=idle', f'WorkingDirectory={Path.cwd()}',
                  f"IOReadBandwidthMax={device} {policy['read']}",
                  f"IOWriteBandwidthMax={device} {policy['write']}"]
    command = ['sudo', '-n', 'systemd-run', '--wait', '--pipe', '--unit=' + unit,
               '--uid=' + str(os.getuid()), '--gid=' + str(os.getgid())]
    for prop in properties:
        command += ['-p', prop]
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        command += ['--setenv=' + key + '=' + str(policy['cpu'] // 100)]
    # Inherit only the caller's proxy routing, not authentication configuration.
    for key, value in os.environ.items():
        if key.lower() in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
            command += ['--setenv=' + key + '=' + value]
    command += [sys.executable, str(Path(__file__).resolve()), '--inside',
                '--profile', args.profile, '--timeout', str(args.timeout), '--device-number', device_number,
                '--memory-bytes', str(memory), '--high-bytes', str(high),
                '--telemetry', str(telemetry)]
    if args.data_dir is not None:
        command += ['--data-dir', str(args.data_dir.resolve())]
    command += ['--', *args.command]
    start = time.monotonic()
    result = subprocess.run(command, check=False)
    query = subprocess.run(['systemctl', '--system', 'show', unit, '--no-pager', '-p', 'LoadState',
                            '-p', 'Result', '-p', 'ExecMainStatus', '-p', 'MemoryPeak',
                            '-p', 'CPUUsageNSec', '-p', 'IOReadBytes', '-p', 'IOWriteBytes',
                            '-p', 'RuntimeMaxUSec', '-p', 'TasksMax', '-p', 'KillMode'],
                           text=True, capture_output=True)
    telemetry_data = json.loads(telemetry.read_text()) if telemetry.exists() else None
    properties = dict(line.split('=', 1) for line in query.stdout.splitlines() if '=' in line)
    complete = (telemetry_data is not None and telemetry_data.get('state') == 'completed'
                and telemetry_data.get('returncode') == 0)
    code = result.returncode or (0 if complete else 1)
    data = {'state': 'completed' if code == 0 else 'failed',
            'returncode': code, 'wall_s': time.monotonic() - start,
            'service': unit,
            'service_properties': query.stdout if properties.get('LoadState') == 'loaded' else None,
            'service_query_state': properties.get('LoadState', 'unavailable'),
            'service_query_returncode': query.returncode,
            'telemetry': telemetry_data,
            'measurement_scope': 'Whole service, not physics throughput. memory.peak is a kernel high-water mark; CPU/I/O counters are cumulative; reported rate peaks are interval-sampled estimates, not instantaneous peaks. Missing final telemetry means interruption, not successful validation.'}
    atomic_json(args.receipt, data)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--io-device', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--profile', choices=PROFILES, default='archive')
    parser.add_argument('--data-dir', type=Path, help='Required existing data volume directory for experiments')
    parser.add_argument('--timeout', type=int)
    parser.add_argument('--memory-mib', type=int)
    parser.add_argument('--high-mib', type=int)
    parser.add_argument('--device-number', help=argparse.SUPPRESS)
    parser.add_argument('--memory-bytes', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--high-bytes', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--telemetry', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    policy = PROFILES[args.profile]
    args.memory_mib = policy['memory'] if args.memory_mib is None else args.memory_mib
    args.high_mib = policy['high'] if args.high_mib is None else args.high_mib
    args.timeout = policy['timeout'] if args.timeout is None else args.timeout
    if args.command[:1] == ['--']:
        args.command = args.command[1:]
    if not args.command:
        parser.error('Provide a foreground command after --')
    if not args.inside and (args.io_device is None or args.receipt is None
                            or not 0 < args.high_mib <= args.memory_mib <= policy['memory']
                            or not 0 < args.timeout <= 3600):
        parser.error('Require device, fresh receipt, 0 < high <= memory <= profile cap, and timeout <= 3600 s')
    if args.profile != 'archive' and args.data_dir is None:
        parser.error('Experiment profile requires --data-dir')
    return inside(args) if args.inside else launch(args)


if __name__ == '__main__':
    raise SystemExit(main())
