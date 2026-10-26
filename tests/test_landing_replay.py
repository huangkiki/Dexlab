"""Protect complete replay coverage and the no-dynamics display boundary."""

import unittest
from unittest.mock import patch

import mujoco
import numpy as np

from dexlab.landing_replay import control_samples, set_display_pose


class LandingReplayTests(unittest.TestCase):
    def record(self):
        return {
            'pre_qpos': np.arange(28, dtype=float).reshape(4, 7),
            'qpos': np.arange(7, 35, dtype=float).reshape(4, 7),
            'native_time_before': np.array([0., .005, .01, .015]),
            'native_time_after': np.array([.005, .01, .015, .02]),
        }

    def test_every_control_boundary_includes_initial_and_final_endpoints(self):
        native = self.record()
        poses, times, forces = control_samples(native, {'control_steps': 2, 'substeps_per_control': 2})
        np.testing.assert_array_equal(poses, np.stack((native['pre_qpos'][0], native['qpos'][1], native['qpos'][3])))
        np.testing.assert_array_equal(times, [0., .01, .02])
        np.testing.assert_array_equal(forces, [-1, 1, 3])

    def test_missing_or_discontinuous_substeps_cannot_be_hidden_by_downsampling(self):
        protocol = {'control_steps': 2, 'substeps_per_control': 2}
        native = self.record()
        native['native_time_before'][1] += .001
        with self.assertRaisesRegex(ValueError, 'discontinuous'):
            control_samples(native, protocol)
        native = {key: value[:-1] for key, value in self.record().items()}
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            control_samples(native, protocol)

    def test_display_updates_geometry_without_touching_dynamics_or_the_record(self):
        model = mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
          <body><freejoint/><geom type="sphere" size=".1" mass="1"/></body>
          </worldbody></mujoco>''')
        data = mujoco.MjData(model)
        pose = model.qpos0.copy()
        pose[:3] = [.2, -.1, .6]
        original = pose.copy()
        data.qvel[:] = 7
        data.qacc[:] = 11
        data.qfrc_constraint[:] = 13
        data.time = 17
        with patch.object(mujoco, 'mj_forward', side_effect=AssertionError('No forward dynamics')), \
                patch.object(mujoco, 'mj_step', side_effect=AssertionError('No integration')), \
                patch.object(mujoco, 'mj_collision', side_effect=AssertionError('No replacement contacts')):
            set_display_pose(mujoco, model, data, pose)
        np.testing.assert_array_equal(pose, original)
        np.testing.assert_array_equal(data.qpos, original)
        np.testing.assert_allclose(data.geom_xpos[0], original[:3])
        np.testing.assert_array_equal(data.qvel, np.full(model.nv, 7))
        np.testing.assert_array_equal(data.qacc, np.full(model.nv, 11))
        np.testing.assert_array_equal(data.qfrc_constraint, np.full(model.nv, 13))
        self.assertEqual(data.time, 17)


if __name__ == '__main__':
    unittest.main()
