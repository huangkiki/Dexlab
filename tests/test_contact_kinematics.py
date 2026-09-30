"""Separate material velocity at a spatial contact from COM/wrist drift."""

import unittest

import numpy as np

from dexlab.contact_kinematics import cylinder_contact_motion


class ContactMotionTests(unittest.TestCase):
    def record(self):
        pose = np.zeros((2, 3, 7))
        pose[:, :, 3] = 1
        return {
            "time": np.array([0, 0.001]),
            "pose": pose,
            "velocity": np.zeros((2, 3, 6)),
        }

    def contact(self, *, point=(0.01, 0, 0), normal=(1, 0, 0), force=(4, 0, 0)):
        return [
            [
                {
                    "pad": 0,
                    "point": point,
                    "normal_direction": normal,
                    "normal_force": force,
                }
            ]
        ]

    def test_rotation_causes_tangent_motion_without_com_drift(self):
        data = self.record()
        data["velocity"][1, 2, 5] = 2
        result = cylinder_contact_motion(data, self.contact(), "mujoco")
        self.assertTrue(result["known"][0])
        self.assertAlmostEqual(result["peak_speed"][0], 0.02)

    def test_common_rigid_motion_and_normal_motion_are_not_slip(self):
        data = self.record()
        data["velocity"][1, :, :] = [0, 0, 2, 0, 0, 3]
        result = cylinder_contact_motion(data, self.contact(), "superdex")
        self.assertAlmostEqual(result["peak_speed"][0], 0)
        data["velocity"][1, 2, 0] += 10
        result = cylinder_contact_motion(data, self.contact(), "superdex")
        self.assertAlmostEqual(result["peak_speed"][0], 0)

    def test_missing_and_unloaded_are_distinct(self):
        data = self.record()
        missing = cylinder_contact_motion(data, [{}], "physx", [2, 4, 5])
        self.assertFalse(missing["known"][0])
        unloaded = cylinder_contact_motion(data, [[]], "mujoco")
        self.assertTrue(unloaded["known"][0])
        self.assertTrue(np.isnan(unloaded["peak_speed"][0]))
        np.testing.assert_array_equal(unloaded["normal_load"][0], [0, 0])

    def test_physx_normal_sign_and_separate_friction_anchors(self):
        data = self.record()
        data["velocity"][1, 2, 2] = -0.03
        row = {
            "normal_body_ids": [2],
            "normal_point": [[-0.01, 0, 0]],
            "normal_direction": [[-1, 0, 0]],
            "normal_force": [[4, 0, 0]],
            "friction_point": [[0, 0, 0], [1, 0, 0]],
        }
        result = cylinder_contact_motion(data, [row], "physx", [2, 4, 5])
        self.assertTrue(result["known"][0])
        self.assertAlmostEqual(result["peak_speed"][0], 0.03)

    def test_bad_normal_or_contact_pair_is_unknown(self):
        data = self.record()
        result = cylinder_contact_motion(data, self.contact(normal=(0, 0, 0)), "mujoco")
        self.assertFalse(result["known"][0])
        contacts = self.contact()
        contacts[0][0]["pad"] = 2
        self.assertFalse(cylinder_contact_motion(data, contacts, "mujoco")["known"][0])
