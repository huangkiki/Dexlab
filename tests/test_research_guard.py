import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/research_guard.py'


def wait_for(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError('Timed out waiting for process state')
        time.sleep(0.02)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lock = self.root / 'window.lock'
        self.processes = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)

    def launch(self, name, kind, code):
        process = subprocess.Popen([
            sys.executable, str(SCRIPT), 'run', '--lock', str(self.lock),
            '--kind', kind, '--receipt', str(self.root / (name + '.json')),
            '--', sys.executable, '-c', code,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(process)
        return process

    def blocking_job(self, started, release):
        return (f'from pathlib import Path; import time; Path({str(started)!r}).touch(); '
                f'\nwhile not Path({str(release)!r}).exists(): time.sleep(.02)')

    def test_both_acquisition_orders_serialize_actual_processes(self):
        for first, second in [('archive', 'timing'), ('timing', 'archive')]:
            with self.subTest(first=first):
                started = self.root / (first + '-started')
                release = self.root / (first + '-release')
                after = self.root / (second + '-after')
                a = self.launch(first, first, self.blocking_job(started, release))
                wait_for(started.exists)
                b = self.launch(second + '-second', second, f'from pathlib import Path; Path({str(after)!r}).touch()')
                time.sleep(.15)
                self.assertFalse(after.exists())
                release.touch()
                self.assertEqual(a.wait(timeout=10), 0)
                self.assertEqual(b.wait(timeout=10), 0)
                left = json.loads((self.root / (first + '.json')).read_text())
                right = json.loads((self.root / (second + '-second.json')).read_text())
                self.assertGreaterEqual(right['started_at_unix_s'], left['finished_at_unix_s'])

    def test_killed_guard_keeps_live_child_group_blocked_then_recovers(self):
        started, release = self.root / 'started', self.root / 'release'
        owner = self.launch('old', 'archive', self.blocking_job(started, release))
        wait_for(started.exists)
        active = self.lock.with_name(self.lock.name + '.active.json')
        old = json.loads(active.read_text())
        os.kill(old['process_group'], signal.SIGKILL)
        owner.wait(timeout=10)
        blocked = self.launch('blocked', 'timing', 'raise SystemExit(99)')
        self.assertEqual(blocked.wait(timeout=10), 75)
        self.assertFalse((self.root / 'blocked.json').exists())
        release.touch()
        # Retry only after the orphaned foreground child exits, excluding zombies.
        import importlib.util
        spec = importlib.util.spec_from_file_location('guard', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        wait_for(lambda: not module.group_members(old['process_group']))
        recovered = self.launch('recovered', 'timing', 'pass')
        self.assertEqual(recovered.wait(timeout=10), 0)
        result = json.loads((self.root / 'recovered.json').read_text())
        self.assertEqual(result['recovered_window'], old['id'])
        self.assertFalse(active.exists())

    def test_failed_command_releases_window_but_preserves_failure_receipt(self):
        failed = self.launch('failed', 'qualification', 'raise SystemExit(3)')
        self.assertEqual(failed.wait(timeout=10), 3)
        result = json.loads((self.root / 'failed.json').read_text())
        self.assertEqual(result['returncode'], 3)
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(self.launch('next', 'archive', 'pass').wait(timeout=10), 0)

    def test_receipt_is_not_overwritten(self):
        path = self.root / 'old.json'
        path.write_text('original')
        self.assertNotEqual(self.launch('old', 'archive', 'pass').wait(timeout=10), 0)
        self.assertEqual(path.read_text(), 'original')
