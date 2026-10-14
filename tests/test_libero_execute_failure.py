"""A failed native clock must not destroy the executor's failure receipt."""

from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.libero_execute import NUMERICAL_ENVIRONMENT, RUNTIME_PACKAGES, run, source_hashes
from dexlab.libero_workflow import file_hash
import test_libero_execute as fixtures


class LiberoExecuteFailureTests(unittest.TestCase):
    def prepare(self, root, env):
        bddl = root / 'task.bddl'; bddl.write_bytes(b'fixture')
        task = {'task_id': 'fixture/task', 'bddl_path': 'task.bddl',
                'definition': fixtures.goal_fixtures.DEFINITION}
        inputs = {'task': task, 'demonstration': {'demo_id': 'demo_0', 'split': 'development', 'action_count': 3},
                  'bddl': b'fixture', 'model_xml': '<mujoco/>',
                  'metadata': {'problem_name': 'fixture', 'env_kwargs': {}},
                  'actions': np.ones((3, 7)), 'initial': np.r_[1.5, np.zeros(4)],
                  'admission': {'linkage': {'language': {'bddl': 'fixture'}}}}
        env.control_freq = 20
        env.control_timestep = .05
        env.model_timestep = .002
        env.sim.model.get_xml = lambda: '<mujoco/>'
        env.closed = False
        env.close = lambda: setattr(env, 'closed', True)
        payload = {'schema_version': 2, 'recording': True, 'seed': 0, 'purpose': 'development',
                   'runtime_versions': {name: 'fixture' for name in RUNTIME_PACKAGES},
                   'source_sha256': source_hashes(), 'input_dir': str(root),
                   'input_manifest_sha256': 'a' * 64, 'demo_id': 'demo_0',
                   'task_id': task['task_id'], 'libero_root': str(root)}
        payload['numerical_environment'] = dict.fromkeys(NUMERICAL_ENVIRONMENT)
        modules = {name: ModuleType(name) for name in ('libero', 'libero.libero', 'libero.libero.envs', 'robosuite')}
        modules['robosuite'].__file__ = str(root / 'robosuite/__init__.py')
        modules['libero.libero.envs'].TASK_MAPPING = {'fixture': lambda **kwargs: env}
        stack = ExitStack()
        stack.enter_context(patch.dict('os.environ', {}, clear=True))
        stack.enter_context(patch.dict(sys.modules, modules))
        stack.enter_context(patch('dexlab.libero_execute.importlib.metadata.version', return_value='fixture'))
        stack.enter_context(patch('dexlab.libero_execute.load_demo', return_value=inputs))
        stack.enter_context(patch('dexlab.libero_execute._source_identity'))
        stack.enter_context(patch('dexlab.libero_execute.initialize_demo',
                                  side_effect=lambda env, xml, initial, record: record.update(status='completed')))
        stack.enter_context(patch('dexlab.libero_execute.bind_task', return_value={'binding': 'fixture'}))
        return payload, stack

    def test_environment_mismatch_is_rejected_before_input_or_native_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); env = fixtures.NativeFixture()
            payload, stack = self.prepare(root, env)
            with stack, patch.dict('os.environ', {'OPENBLAS_NUM_THREADS': '2'}), \
                    patch('dexlab.libero_execute.load_demo') as loader:
                with self.assertRaisesRegex(ValueError, 'numerical environment differs'):
                    run(payload, root / 'output')
                loader.assert_not_called()
            self.assertFalse((root / 'output').exists())

    def test_nonfinite_clock_retains_original_error_partial_evidence_and_cleanup(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(clock=value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); env = fixtures.NativeFixture(); step = env.step
                def failed(action):
                    if env.count == 1:
                        env.sim.data.time = value
                        raise RuntimeError('native clock failure')
                    return step(action)
                env.step = failed
                payload, stack = self.prepare(root, env)
                with stack, self.assertRaisesRegex(RuntimeError, 'native clock failure'):
                    run(payload, root / 'output')
                receipt = json.loads((root / 'output/run.json').read_text())
                self.assertEqual(receipt['status'], 'failed')
                self.assertEqual(receipt['error_type'], 'RuntimeError')
                self.assertEqual(receipt['actions_executed'], 1)
                self.assertIsNone(receipt['final_time_s'])
                self.assertIsNone(receipt['native_success_final'])
                self.assertEqual(receipt['invalid_final_time'], repr(value))
                for name, expected in receipt['files'].items():
                    self.assertEqual(file_hash(root / 'output' / name), expected)
                self.assertTrue(env.closed)

    def test_completed_run_keeps_terminal_time_success_and_all_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); env = fixtures.NativeFixture()
            payload, stack = self.prepare(root, env)
            with stack:
                receipt = run(payload, root / 'output')
            self.assertEqual(receipt['status'], 'completed')
            self.assertEqual(receipt['actions_executed'], 3)
            self.assertEqual(receipt['final_time_s'], env.sim.data.time)
            self.assertTrue(receipt['native_success_final'])
            self.assertEqual(receipt['numerical_environment'], payload['numerical_environment'])
            self.assertNotIn('invalid_final_time', receipt)
            self.assertTrue(env.closed)


if __name__ == '__main__':
    unittest.main()
