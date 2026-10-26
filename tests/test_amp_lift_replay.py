"""Replay endpoints and read-only display checks, not AMP physics qualification."""

import unittest
from unittest.mock import patch

import mujoco
import numpy as np

from dexlab.amp_lift_replay import control_samples, set_display_pose


class AmpLiftReplayTests(unittest.TestCase):
    def fixture(self, count):
        protocol = {'conditions': {'decimation': 4, 'physics_dt_s': .005}}
        clock = np.empty(count * 4, dtype=np.float32)
        now = np.float32(0)
        actions = []
        for step in range(len(clock)):
            clock[step] = now
            now = np.float32(now + np.float32(.005))
            if step % 4 == 3:
                index = step // 4
                actions.append({'status': 'completed', 'action_index': index,
                    'feedback': {'native_time': float(now), 'qpos': np.array([index + 1.]),
                                 'automatic_reset': index + 1 == 3000},
                    'returned_observations': {'qpos': np.array([-999.])}})
        return {'time': 0., 'qpos': np.array([0.])}, actions, clock, protocol

    def test_all_boundaries_and_terminal_before_automatic_reset(self):
        poses, times, force_indices = control_samples(*self.fixture(3000), 'float32')
        self.assertEqual(poses.shape, (3001, 1))
        np.testing.assert_array_equal(poses[:, 0], np.arange(3001))
        self.assertEqual(force_indices[0], -1)
        self.assertEqual(force_indices[-1], 11999)
        self.assertGreater(times[-1], 59.)
        self.assertLess(times[-1], 61.)

    def test_truncated_clock_and_reset_observation_clock_are_rejected(self):
        initial, actions, clock, protocol = self.fixture(2)
        with self.assertRaisesRegex(ValueError, 'clock'):
            control_samples(initial, actions, clock[:-1], protocol, 'float32')
        actions[-1]['feedback']['native_time'] = 0.
        with self.assertRaisesRegex(ValueError, 'endpoint'):
            control_samples(initial, actions, clock, protocol, 'float32')

    def test_geometry_update_does_not_integrate_or_compute_contacts(self):
        model = mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
          <geom type="plane" size="1 1 .1"/>
          <body><freejoint/><geom type="box" size=".1 .1 .1" mass="1"/></body>
        </worldbody></mujoco>''')
        data = mujoco.MjData(model)
        data.qvel[:] = np.arange(model.nv)
        data.qacc[:] = 42.
        data.qfrc_constraint[:] = 17.
        data.time = 123.
        pose = np.array([.2, .3, .4, 1., 0., 0., 0.])
        state = {name: getattr(data, name).copy() for name in ('qvel', 'qacc', 'qfrc_constraint')}
        with patch.object(mujoco, 'mj_step', side_effect=AssertionError('integration')), \
             patch.object(mujoco, 'mj_forward', side_effect=AssertionError('solve')), \
             patch.object(mujoco, 'mj_collision', side_effect=AssertionError('collision')):
            set_display_pose(mujoco, model, data, pose)
        np.testing.assert_array_equal(data.qpos, pose)
        np.testing.assert_allclose(data.geom_xpos[1], pose[:3])
        for name, value in state.items():
            np.testing.assert_array_equal(getattr(data, name), value)
        self.assertEqual(data.time, 123.)


if __name__ == '__main__':
    unittest.main()
