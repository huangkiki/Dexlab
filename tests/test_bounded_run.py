"""Fail-closed checks before an archival workload may start."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from bounded_run import (verify_limits, verify_headroom, verify_service, main,
                         select_profile, freeze_resources, pressure, PROFILES)
from archive_run import record_stage
sys.path.pop(0)


class AdaptiveResourceTests(unittest.TestCase):
    def test_smallest_tier_reserves_fifty_percent_above_peak(self):
        self.assertEqual(select_profile(), 'adaptive-16g-4c')
        self.assertEqual(select_profile(complex_model=True), 'adaptive-24g-4c')
        for peak_gib, tier in ((4, 8), (8, 16), (12, 24), (17, 32), (24, 40)):
            self.assertEqual(select_profile(peak_gib * 1024, cores=8), f'adaptive-{tier}g-8c')
        for peak in (0, -1, float('inf'), float('nan'), 28 * 1024):
            with self.assertRaises(ValueError):
                select_profile(peak)
        self.assertEqual(PROFILES['experiment']['cpu'], 200)
        self.assertEqual(PROFILES['experiment-24g']['memory'], 24576)

    def test_batch_restart_reuses_plan_but_cannot_change_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / 'prior.json'
            receipt.write_text(json.dumps({'telemetry': {'final': {'memory.peak': str(12 * 1024**3)}}}))
            path = root / 'batch.json'
            plan = freeze_resources(path, receipt)
            self.assertEqual(plan['profile'], 'adaptive-24g-4c')
            original = path.read_bytes()
            self.assertEqual(freeze_resources(path, receipt), plan)
            with self.assertRaisesRegex(ValueError, 'frozen'):
                freeze_resources(path, receipt, cores=8)
            self.assertEqual(path.read_bytes(), original)
            receipt.write_text('{}')
            with self.assertRaises(KeyError):
                freeze_resources(root / 'missing.json', receipt)
            self.assertFalse((root / 'missing.json').exists())

    def test_missing_pressure_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(all(value is None for value in pressure(Path(directory)).values()))


class EffectiveLimitTests(unittest.TestCase):
    def test_requested_but_missing_cpu_or_device_limits_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {'memory.max': '1024', 'memory.high': '768',
                      'memory.swap.max': '0', 'cpu.max': '100000 100000',
                      'pids.max': '32', 'io.max': '8:0 rbps=16777216 wbps=8388608'}
            for name, value in values.items():
                (root / name).write_text(value)
            self.assertEqual(verify_limits(root, '8:0', 1024, 768), values)
            for name, bad in [('cpu.max', 'max 100000'), ('memory.swap.max', 'max'),
                              ('memory.high', 'max'), ('pids.max', 'max'),
                              ('io.max', '8:1 rbps=16777216 wbps=8388608'),
                              ('io.max', '8:0 rbps=max wbps=8388608')]:
                with self.subTest(name=name, bad=bad):
                    (root / name).write_text(bad)
                    with self.assertRaises(RuntimeError):
                        verify_limits(root, '8:0', 1024, 768)
                    (root / name).write_text(values[name])


class ArchiveStageTests(unittest.TestCase):
    def test_failed_stage_retains_receipt_and_propagates_error(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'stage.json'
            with self.assertRaisesRegex(RuntimeError, 'reader failed'):
                with record_stage(receipt, 'offline_reader'):
                    self.assertEqual(json.loads(receipt.read_text())['state'], 'running')
                    raise RuntimeError('reader failed')
            result = json.loads(receipt.read_text())
            self.assertEqual(result['state'], 'failed')
            self.assertEqual(result['stage'], 'offline_reader')
            self.assertGreaterEqual(result['wall_s'], 0)

    def test_completed_stage_is_distinct_from_started(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'stage.json'
            with record_stage(receipt, 'transfer'):
                pass
            self.assertEqual(json.loads(receipt.read_text())['state'], 'completed')


class ExperimentAdmissionTests(unittest.TestCase):
    def test_larger_profile_is_explicit_and_preserves_desktop_reserve(self):
        args = ["bounded_run", "--profile", "experiment", "--memory-mib", "24576",
                "--high-mib", "23552", "--io-device", "/dev/example",
                "--receipt", "/tmp/example-receipt", "--data-dir", "/tmp", "--", "true"]
        with patch.object(sys, "argv", args), patch("bounded_run.launch") as launch:
            with self.assertRaises(SystemExit) as failure:
                main()
            self.assertEqual(failure.exception.code, 2)
            launch.assert_not_called()
        args[2] = "experiment-24g"
        with patch.object(sys, "argv", args), patch("bounded_run.launch", return_value=0) as launch:
            self.assertEqual(main(), 0)
            self.assertEqual(launch.call_args.args[0].memory_mib, 24576)
        gib = 1024**3
        with self.assertRaises(RuntimeError):
            verify_headroom(32 * gib - 1, 20 * gib, 24 * gib)
        verify_headroom(32 * gib, 20 * gib, 24 * gib)

    def test_headroom_rejects_memory_or_disk_shortfall(self):
        gib = 1024**3
        verify_headroom(24 * gib, 20 * gib, 16 * gib)
        for available, free in [(24 * gib - 1, 20 * gib), (24 * gib, 20 * gib - 1)]:
            with self.subTest(available=available, free=free):
                with self.assertRaises(RuntimeError):
                    verify_headroom(available, free, 16 * gib)

    def test_experiment_requires_its_effective_cpu_tasks_and_io(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {'memory.max': '16384', 'memory.high': '15360',
                      'memory.swap.max': '0', 'cpu.max': '200000 100000',
                      'pids.max': '128', 'io.max': '8:0 rbps=33554432 wbps=16777216'}
            for name, value in values.items():
                (root / name).write_text(value)
            self.assertEqual(verify_limits(root, '8:0', 16384, 15360, 'experiment'), values)
            for name, bad in [('cpu.max', 'max 100000'), ('pids.max', 'max'),
                              ('memory.swap.max', '1'), ('io.max', '8:0 rbps=max wbps=max')]:
                with self.subTest(name=name):
                    (root / name).write_text(bad)
                    with self.assertRaises(RuntimeError):
                        verify_limits(root, '8:0', 16384, 15360, 'experiment')
                    (root / name).write_text(values[name])
            with self.assertRaises(RuntimeError):
                verify_limits(root, '8:0', 16384, 15360)  # archival contract unchanged


class ServiceRuntimeTests(unittest.TestCase):
    def test_live_runtime_and_process_cleanup_are_required(self):
        valid = 'LoadState=loaded\nRuntimeMaxUSec=1h\nTasksMax=128\nKillMode=control-group\n'
        with patch('bounded_run.subprocess.run', return_value=SimpleNamespace(stdout=valid)):
            self.assertEqual(verify_service('example.service', 3600, 128)['RuntimeMaxUSec'], '1h')
        for old, new in [('1h', 'infinity'), ('1h', '2h'), ('loaded', 'not-found'),
                         ('128', 'max'), ('control-group', 'process')]:
            with self.subTest(new=new), patch('bounded_run.subprocess.run',
                    return_value=SimpleNamespace(stdout=valid.replace(old, new))):
                with self.assertRaises(RuntimeError):
                    verify_service('example.service', 3600, 128)
