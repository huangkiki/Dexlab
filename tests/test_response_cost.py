"""Validate serial cost accounting without running native physics."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dexlab.contact_load import LIMITS

SCRIPT = Path(__file__).resolve().parents[1] / 'demos/contact-benchmark/normal_response.py'
spec = importlib.util.spec_from_file_location('normal_response_cost_test', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ResponseCostTests(unittest.TestCase):
    def plan(self):
        return {
            'protocol': 'normal-load', 'target': LIMITS, 'scope': 'unit fixture',
            'measure_step_timing': True,
            'budget': {'episodes': 1, 'parallel_workers': 1, 'batch_seconds': 10},
            'jobs': [{'id': 'one', 'role': 'unit', 'engine': 'mujoco',
                      'case': {'name': 'dev-unit'}, 'normal_parameters': {}}],
        }

    def test_full_call_timing_and_native_flag(self):
        def native_run(case, engine, output, **kwargs):
            self.assertTrue(kwargs['measure_step_timing'])
            output.mkdir(parents=True)
            (output / 'run.json').write_text('{}')
            return {'passed': False, 'checks': {'native_run_completed': True}}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = root / 'suite.json'
            suite.write_text(json.dumps(self.plan()))
            with patch.object(runner, 'run', side_effect=native_run), patch.object(
                runner.time, 'perf_counter', side_effect=[0, 1, 2, 5, 6]
            ):
                report = runner.evaluate(root / 'out', suite)
            self.assertEqual(report['results'][0]['episode_wall_seconds'], 3)
            self.assertEqual(report['batch_elapsed_seconds'], 6)
            self.assertEqual(report['passed'], 0)  # Do not discard physical failures.

    def test_expired_budget_starts_no_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = root / 'suite.json'
            suite.write_text(json.dumps(self.plan()))
            with patch.object(runner, 'run') as run, patch.object(
                runner.time, 'perf_counter', side_effect=[0, 11]
            ):
                with self.assertRaises(TimeoutError):
                    runner.evaluate(root / 'out', suite)
            run.assert_not_called()

    def test_invalid_budget_rejected_before_output(self):
        for value in (True, -1, float('inf'), '10'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plan = self.plan()
                plan['budget']['batch_seconds'] = value
                (root / 'suite.json').write_text(json.dumps(plan))
                with self.assertRaises(ValueError):
                    runner.evaluate(root / 'out', root / 'suite.json')
                self.assertFalse((root / 'out').exists())

    def test_offline_rejects_missing_or_short_full_call_timing(self):
        from dexlab.contact_parameters import normal_parameters
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan()
            (root / 'suite.json').write_text(json.dumps(plan))
            folder = root / 'raw/one'
            folder.mkdir(parents=True)
            receipt = {'engine':'mujoco', 'case':plan['jobs'][0]['case'],
                       'normal_parameters':normal_parameters('mujoco', {}),
                       'measure_step_timing':True, 'total_seconds':2.0}
            (folder / 'run.json').write_text(json.dumps(receipt))
            result = {'passed':False}
            for wall in (None, True, -1, 1.9, float('nan')):
                report = {'suite_sha256':runner.digest(root/'suite.json'),
                          'results':[{'id':'one','receipt_sha256':runner.digest(folder/'run.json'),
                                      'result':result,'episode_wall_seconds':wall}],
                          'completed':1,'passed':0}
                (root/'report.json').write_text(json.dumps(report))
                with self.subTest(wall=wall), self.assertRaisesRegex(ValueError, 'timing'):
                    runner.rescore(root)
