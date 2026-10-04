"""Fail-closed checks before an archival workload may start."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from bounded_run import verify_limits
from archive_run import record_stage
sys.path.pop(0)


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
