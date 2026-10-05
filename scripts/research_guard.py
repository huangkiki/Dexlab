#!/usr/bin/env python3
"""Serialize managed research windows and retain crash evidence on Linux.

All commands must remain in the guard's process group (no daemonization). A
remote controller first probes this guard remotely, then guards each remote
command, while holding its local guard across the entire window. This keeps
local postprocessing out of a timed window and detects surviving remote jobs.
"""

import argparse
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import uuid


class BusyWindow(RuntimeError):
    pass


def group_members(group):
    """Ignore zombies, which no longer execute or perform I/O."""
    members = []
    for item in Path('/proc').iterdir():
        if not item.name.isdecimal():
            continue
        try:
            fields = (item / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group and fields[0] not in ('Z', 'X'):
                members.append(int(item.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
    return members


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def run_window(lock_path, kind, receipt, command):
    """Called only inside a newly created, private process session."""
    if os.getpid() != os.getpgrp() or os.getpid() != os.getsid(0):
        raise RuntimeError('A private session is required before opening a window')
    lock_path, receipt = Path(lock_path).resolve(), Path(receipt).resolve()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    active = lock_path.with_name(lock_path.name + '.active.json')
    if receipt in (lock_path, active):
        raise ValueError('Receipt must be separate from lock and active marker')
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        recovered = None
        recovery_reason = None
        boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        if active.exists():
            previous = json.loads(active.read_text())
            # Process-group numbers can be reused after reboot. A recorded
            # previous boot cannot have live descendants in this boot. Legacy
            # markers without boot identity retain the conservative live check.
            prior_boot = previous.get('boot_id')
            rebooted = prior_boot is not None and prior_boot != boot_id
            members = [] if rebooted else group_members(previous['process_group'])
            if members:
                raise BusyWindow('Previous window has surviving processes; preserve it and retry later')
            recovered = previous['id']
            recovery_reason = 'previous_boot' if rebooted else 'no_surviving_processes'
        if receipt.exists():
            raise FileExistsError('Choose a new receipt; existing evidence is immutable')
        state = {
            'schema_version': 2, 'id': uuid.uuid4().hex, 'kind': kind,
            'boot_id': boot_id,
            'process_group': os.getpgrp(), 'started_at_unix_s': time.time(),
            'state': 'active', 'recovered_window': recovered,
            'recovery_reason': recovery_reason,
        }
        # Written before spawning: even a kill during launch leaves a known group.
        atomic_json(active, state)
        atomic_json(receipt, state)
        start = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        result = subprocess.run(command, check=False)
        survivors = [pid for pid in group_members(os.getpgrp()) if pid != os.getpid()]
        if survivors:
            raise BusyWindow('Command exited with live descendants; active marker retained')
        final_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        state.update({
            'state': 'completed', 'returncode': result.returncode,
            'finished_at_unix_s': time.time(),
            'whole_command_wall_s': time.monotonic() - start,
            'child_user_cpu_s': final_usage.ru_utime - usage.ru_utime,
            'child_system_cpu_s': final_usage.ru_stime - usage.ru_stime,
            'maximum_child_rss_kib': final_usage.ru_maxrss,
            'resource_scope': 'Whole command including setup and subprocesses; RSS is the largest child high-water mark, not summed process-tree peak or physics-step timing.',
        })
        atomic_json(receipt, state)
        active.unlink()
        return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('run', '_run'))
    parser.add_argument('--lock', required=True, type=Path)
    parser.add_argument('--kind', required=True, choices=('timing', 'archive', 'qualification'))
    parser.add_argument('--receipt', required=True, type=Path)
    try:
        separator = sys.argv.index('--')
    except ValueError:
        parser.error('Provide a foreground command after --')
    args = parser.parse_args(sys.argv[1:separator])
    command = sys.argv[separator + 1:]
    if not command:
        parser.error('Provide a foreground command after --')
    if args.mode == '_run':
        try:
            code = run_window(args.lock, args.kind, args.receipt, command)
        except BusyWindow as error:
            parser.exit(75, str(error) + '\n')
        raise SystemExit(code)
    child_args = [sys.executable, str(Path(__file__).resolve()), '_run',
                  '--lock', str(args.lock), '--kind', args.kind,
                  '--receipt', str(args.receipt), '--', *command]
    child = subprocess.Popen(child_args, start_new_session=True)
    def forward(signum, _frame):
        try:
            os.killpg(child.pid, signum)
        except ProcessLookupError:
            pass
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, forward)
    raise SystemExit(child.wait())


if __name__ == '__main__':
    main()
