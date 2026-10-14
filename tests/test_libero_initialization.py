"""Native initialization must preserve source coordinates and failure evidence."""

import json
from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.libero_initialization import initialize_demo

try:
    import mujoco
except ImportError:
    mujoco = None


XML = '''<mujoco><worldbody><body name="free" pos="0 0 1"><freejoint/>
<geom type="sphere" size=".1"/><body name="ball" pos="0 0 .2">
<joint type="ball"/><geom type="sphere" size=".1"/></body></body>
</worldbody></mujoco>'''


class NativeFixture:
    """Tiny native scene with the pinned wrapper's time/qpos/qvel contract."""

    def __init__(self):
        self.calls = []
        self.restore_count = 0
        self.corrupt_phase = None
        self.sim = SimpleNamespace(reset=lambda: mujoco.mj_resetData(self.model, self.data),
                                   forward=self.forward, set_state_from_flattened=self.restore,
                                   get_state=lambda: SimpleNamespace(flatten=self.state))
        self.load(XML)

    def load(self, xml):
        self.model = mujoco.MjModel.from_xml_string(xml)
        self.data = mujoco.MjData(self.model)
        self.sim.model = SimpleNamespace(_model=self.model)

    def state(self):
        return np.r_[self.data.time, self.data.qpos, self.data.qvel]

    def reset(self):
        self.calls.append('reset')

    def reset_from_xml_string(self, xml):
        self.calls.append('reset-xml')
        self.load(xml)

    def restore(self, value):
        self.restore_count += 1
        self.data.time = value[0]
        self.data.qpos[:] = value[1:1 + self.model.nq]
        self.data.qvel[:] = value[1 + self.model.nq:]
        if self.corrupt_phase == 'restore':
            self.data.qvel[0] += .125

    def forward(self):
        mujoco.mj_forward(self.model, self.data)
        if self.corrupt_phase == 'forward':
            self.data.time += .002

    def _post_process(self):
        self.calls.append('post-process')
        if self.corrupt_phase == 'post-processing':
            self.data.qpos[0] += .125

    def _update_observables(self, force):
        self.calls.append(('observables', force))


@unittest.skipIf(mujoco is None, 'Native MuJoCo initialization tests require the engine')
class LiberoInitializationTests(unittest.TestCase):
    @unittest.skipUnless(mujoco is not None and mujoco.__version__ == '2.3.7',
                         'Requires pinned LIBERO MuJoCo 2.3.7 forward normalization')
    def test_restores_once_and_permits_only_native_quaternion_normalization(self):
        env = NativeFixture()
        initial = env.state()
        initial[0] = .25
        initial[4:8] = [2., .5, 0., 0.]
        initial[8:12] = [0., 3., 0., 1.]
        original = initial.copy()
        record = {}
        initialize_demo(env, XML, initial, record)
        self.assertEqual(record['status'], 'completed')
        np.testing.assert_array_equal(record['after_set'], original)
        np.testing.assert_array_equal(record['after_forward'], record['expected_after_forward'])
        np.testing.assert_array_equal(record['after_post'], record['after_forward'])
        np.testing.assert_array_equal(initial, original)
        self.assertEqual(env.restore_count, 1)
        self.assertEqual(env.calls, ['reset', 'reset-xml', 'post-process', ('observables', True)])
        self.assertTrue(set(record['normalized_indices']) <= set(range(4, 12)))
        self.assertTrue(record['normalized_indices'])
        json.dumps(record, allow_nan=False)

    @unittest.skipUnless(mujoco is not None and mujoco.__version__ == '3.15.0',
                         'Checks the separate MuJoCo 3.15.0 native forward contract')
    def test_newer_forward_contract_is_rejected_without_changing_source_state(self):
        env = NativeFixture()
        initial = env.state()
        initial[4:8] = [2., .5, 0., 0.]
        initial[8:12] = [0., 3., 0., 1.]
        original, record = initial.copy(), {}
        with self.assertRaisesRegex(ValueError, 'Unexpected native state change at after_forward'):
            initialize_demo(env, XML, initial, record)
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['phase'], 'forward')
        self.assertEqual(env.restore_count, 1)
        self.assertEqual(env.calls, ['reset', 'reset-xml'])
        np.testing.assert_array_equal(record['after_set'], original)
        np.testing.assert_array_equal(record['after_forward'], original)
        np.testing.assert_array_equal(initial, original)
        self.assertTrue(set(record['after_forward_mismatched_indices']) <= set(range(4, 12)))
        self.assertTrue(record['after_forward_mismatched_indices'])
        self.assertNotIn('after_post', record)
        json.dumps(record, allow_nan=False)

    def test_wrong_width_and_activation_state_are_rejected_before_restore(self):
        activated = '<mujoco><worldbody><body><joint name="j"/><geom size=".1"/></body></worldbody><actuator><general joint="j" dyntype="filter"/></actuator></mujoco>'
        for xml, initial, message in ((XML, np.zeros(3), 'width'),
                                      (activated, np.zeros(3), 'activation')):
            env = NativeFixture(); record = {}
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                initialize_demo(env, xml, initial, record)
            self.assertEqual(env.restore_count, 0)
            self.assertEqual(record['status'], 'failed')

    def test_zero_free_or_ball_quaternion_is_not_silently_replaced(self):
        for start in (4, 8):
            env = NativeFixture(); initial = env.state(); record = {}
            initial[start:start + 4] = 0
            with self.subTest(start=start), self.assertRaisesRegex(ValueError, 'degenerate'):
                initialize_demo(env, XML, initial, record)
            self.assertEqual(env.restore_count, 0)

    def test_unexpected_changes_fail_at_the_exact_phase_with_evidence(self):
        for phase, channel in (('restore', 'after_set'), ('forward', 'after_forward'),
                               ('post-processing', 'after_post')):
            env = NativeFixture(); env.corrupt_phase = phase; record = {}
            with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, channel):
                initialize_demo(env, XML, env.state(), record)
            self.assertEqual(record['phase'], phase)
            self.assertEqual(record['status'], 'failed')
            self.assertTrue(record[channel + '_mismatched_indices'])
            json.dumps(record, allow_nan=False)

    def test_invalid_input_does_not_reset_or_create_nonfinite_diagnostics(self):
        for initial in (np.array([float('nan')]), np.zeros((2, 2)), np.array([0, 1])):
            env = NativeFixture(); record = {}
            with self.subTest(initial=initial), self.assertRaisesRegex(ValueError, 'finite floating'):
                initialize_demo(env, XML, initial, record)
            self.assertFalse(env.calls)
            json.dumps(record, allow_nan=False)

    def test_diagnostics_cannot_overwrite_an_earlier_initialization(self):
        env = NativeFixture(); record = {'status': 'completed'}
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            initialize_demo(env, XML, env.state(), record)
        self.assertEqual(record, {'status': 'completed'})
        self.assertFalse(env.calls)

    def test_negative_time_is_rejected_without_restore(self):
        env = NativeFixture(); initial = env.state(); initial[0] = -1
        with self.assertRaisesRegex(ValueError, 'nonnegative'):
            initialize_demo(env, XML, initial, {})
        self.assertEqual(env.restore_count, 0)


if __name__ == '__main__':
    unittest.main()
