#!/usr/bin/env python3
"""Run local archival in a verified Linux systemd resource envelope."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import uuid

from research_guard import atomic_json

FILES = ('memory.max', 'memory.high', 'memory.swap.max', 'cpu.max',
         'pids.max', 'io.max')
METRICS = ('memory.current', 'memory.peak', 'memory.events', 'cpu.stat',
           'pids.current', 'pids.events', 'io.stat')


def read_values(root, names):
    return {name: (root / name).read_text().strip() for name in names}


def verify_limits(root, device, memory, high):
    limits = read_values(root, FILES)
    expected = {'memory.max': str(memory), 'memory.high': str(high),
                'memory.swap.max': '0', 'cpu.max': '100000 100000', 'pids.max': '32'}
    if any(limits[key] != value for key, value in expected.items()):
        raise RuntimeError('Effective cgroup limits differ from the requested envelope')
    rows = {parts[0]: dict(field.split('=', 1) for field in parts[1:])
            for line in limits['io.max'].splitlines() if (parts := line.split())}
    if rows.get(device, {}).get('rbps') != '16777216' or rows.get(device, {}).get('wbps') != '8388608':
        raise RuntimeError('Effective archive-device I/O limits are missing or different')
    return limits


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


def inside(args):
    if os.getuid() == 0:
        raise RuntimeError('Workload must run as an unprivileged user')
    root = current_cgroup()
    limits = verify_limits(root, args.device_number, args.memory_bytes, args.high_bytes)
    state = {'state': 'running', 'effective_limits': limits,
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
    device = args.io_device.resolve(strict=True)
    info = device.stat()
    if not stat.S_ISBLK(info.st_mode):
        raise ValueError('I/O device must be a block device')
    if os.getuid() == 0:
        raise ValueError('Launch as the ordinary workload owner, not root')
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
                  'CPUQuota=100%', 'CPUQuotaPeriodSec=100ms', 'TasksMax=32',
                  f'RuntimeMaxSec={args.timeout}', 'TimeoutStopSec=5',
                  'KillMode=control-group', 'OOMPolicy=stop', 'Nice=15',
                  'CPUAccounting=yes', 'MemoryAccounting=yes', 'IOAccounting=yes',
                  'IOSchedulingClass=idle', f'WorkingDirectory={Path.cwd()}',
                  f'IOReadBandwidthMax={device} 16777216',
                  f'IOWriteBandwidthMax={device} 8388608']
    command = ['sudo', '-n', 'systemd-run', '--wait', '--pipe', '--unit=' + unit,
               '--uid=' + str(os.getuid()), '--gid=' + str(os.getgid())]
    for prop in properties:
        command += ['-p', prop]
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        command += ['--setenv=' + key + '=1']
    command += [sys.executable, str(Path(__file__).resolve()), '--inside',
                '--device-number', f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}',
                '--memory-bytes', str(memory), '--high-bytes', str(high),
                '--telemetry', str(telemetry), '--', *args.command]
    start = time.monotonic()
    result = subprocess.run(command, check=False)
    query = subprocess.run(['systemctl', 'show', unit, '--no-pager',
                            '-p', 'Result', '-p', 'ExecMainStatus', '-p', 'MemoryPeak',
                            '-p', 'CPUUsageNSec', '-p', 'IOReadBytes', '-p', 'IOWriteBytes'],
                           text=True, capture_output=True)
    data = {'state': 'completed' if result.returncode == 0 else 'failed',
            'returncode': result.returncode, 'wall_s': time.monotonic() - start,
            'service': unit, 'service_properties': query.stdout,
            'service_query_returncode': query.returncode,
            'telemetry': json.loads(telemetry.read_text()) if telemetry.exists() else None,
            'measurement_scope': 'Whole service, not physics throughput. memory.peak is a kernel high-water mark; CPU/I/O counters are cumulative; reported rate peaks are interval-sampled estimates, not instantaneous peaks. Missing final telemetry means interruption, not successful validation.'}
    atomic_json(args.receipt, data)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--io-device', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--memory-mib', type=int, default=8192)
    parser.add_argument('--high-mib', type=int, default=6144)
    parser.add_argument('--device-number', help=argparse.SUPPRESS)
    parser.add_argument('--memory-bytes', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--high-bytes', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--telemetry', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ['--']:
        args.command = args.command[1:]
    if not args.command:
        parser.error('Provide a foreground command after --')
    if not args.inside and (args.io_device is None or args.receipt is None
                            or not 0 < args.high_mib <= args.memory_mib <= 8192
                            or not 0 < args.timeout <= 3600):
        parser.error('Require device, fresh receipt, 0 < high <= memory <= 8192 MiB, and timeout <= 3600 s')
    return inside(args) if args.inside else launch(args)


if __name__ == '__main__':
    raise SystemExit(main())
