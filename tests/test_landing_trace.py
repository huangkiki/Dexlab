"""Adversarial recording controls; these fixtures are not physical rollouts."""

import unittest

import numpy as np

from dexlab.landing_trace import align_states, compare_contact_evidence, contact_pairs, joint_indices


def recorded_states():
    states = np.zeros((4, 17))
    states[:, 3] = 1
    states[1:, 7:9] = [[.1, -.2], [.3, -.4], [.5, -.6]]
    states[1:, 15:17] = [[1, -2], [3, -4], [5, -6]]
    pos = np.repeat(states[1:, :9], 4, axis=0)
    vel = np.repeat(states[1:, 9:], 4, axis=0)
    # Native layout deliberately differs from the policy/CSV layout.
    pos[:, [7, 8]] = pos[:, [8, 7]]
    vel[:, [6, 7]] = vel[:, [7, 6]]
    return states, {"time": np.arange(1, 13) * .005, "qpos": pos, "qvel": vel}


def align(states, native):
    return align_states(states, native, ["left", "right"], ["/robot/right", "/robot/left"],
                        controls=3, substeps_per_control=4, physics_dt=.005, state_tolerance=1e-6)


class LandingTraceTests(unittest.TestCase):
    def test_named_joint_mapping_distinguishes_layout_from_state_divergence(self):
        states, native = recorded_states()
        report = align(states, native)
        self.assertTrue(report["aligned"])
        self.assertFalse(report["joint_order_identical"])
        self.assertGreater(report["unmapped_joint_position_max_rad"], 1)
        native["qpos"][7, 8] += .01
        report = align(states, native)
        self.assertFalse(report["aligned"])
        self.assertEqual(report["mismatched_control_frames"], [2])

    def test_quaternion_sign_does_not_manufacture_mismatch(self):
        states, native = recorded_states()
        native["qpos"][:, 3:7] *= -1
        self.assertTrue(align(states, native)["aligned"])
        native["qpos"][0, 3] = .9
        with self.assertRaisesRegex(ValueError, "Nonunit"):
            align(states, native)

    def test_clock_shift_reset_truncation_and_nonfinite_state_are_rejected(self):
        for defect in ("shift", "reset", "truncate", "nan"):
            states, native = recorded_states()
            if defect == "shift": native["time"] += .005
            if defect == "reset": native["time"][5:] -= .025
            if defect == "truncate": native["qpos"] = native["qpos"][:-1]
            if defect == "nan": states[2, 7] = np.nan
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                align(states, native)

    def test_missing_or_ambiguous_joint_mapping_is_not_guessed(self):
        for names in (["left", "left"], ["a/left", "b/left"], ["left", "elbow"]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                joint_indices(["left", "right"], names)

    def test_usd_flattened_paths_match_full_unique_suffixes(self):
        names = ["_World_Robot_right_hip_link_right_hip_joint",
                 "_World_Robot_left_hip_link_left_hip_joint"]
        np.testing.assert_array_equal(joint_indices(["left_hip_joint", "right_hip_joint"], names), [1, 0])
        with self.assertRaises(ValueError):
            joint_indices(["hip_joint", "left_hip_joint"], names)

    def test_geometry_and_force_remain_separate_and_do_not_decide_task_success(self):
        report = compare_contact_evidence([-.002, .001, -.001, 0],
                                          [[0, 0, 0], [0, 0, 5], [0, 0, 2], [0, 0, 0]],
                                          penetration_tolerance_m=0, force_threshold_n=.001)
        self.assertEqual(report["penetration_without_loaded_resultant"], [0])
        self.assertEqual(report["loaded_resultant_without_penetration"], [1])
        self.assertEqual(report["penetration_samples"], [0, 2])
        self.assertIsNone(report["task_success"])

    def test_missing_force_does_not_become_zero(self):
        for forces in (None, [[np.nan, 0, 0]], []):
            with self.subTest(forces=forces), self.assertRaises(ValueError):
                compare_contact_evidence([-.001], forces,
                                         penetration_tolerance_m=0, force_threshold_n=.001)

    def test_empty_steps_are_preserved_in_native_pair_stream(self):
        spans = contact_pairs(np.array([0, 1, 1, 2]), np.array([[0, 1], [0, 2]]),
                              [-.001, .002], np.zeros((2, 6)), steps=3, geom_count=3)
        self.assertEqual([(span.start, span.stop) for span in spans], [(0, 1), (1, 1), (1, 2)])
        for offsets in ([0, 1, 0, 2], [1, 1, 1, 2], [0, 1, 1, 3]):
            with self.subTest(offsets=offsets), self.assertRaises(ValueError):
                contact_pairs(np.array(offsets), np.array([[0, 1], [0, 2]]),
                              [-.001, .002], np.zeros((2, 6)), steps=3, geom_count=3)


if __name__ == "__main__":
    unittest.main()
