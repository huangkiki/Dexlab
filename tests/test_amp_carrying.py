"""Discriminating controls for offline carrying and momentum diagnostics."""

import unittest

import numpy as np

from dexlab.amp_lift_audit import (carrying_windows, check_step_clock, hand_relative_positions,
                                  momentum_residual)


class AmpCarryingTests(unittest.TestCase):
    def test_float32_clock_accepts_quantization_but_rejects_skipped_step(self):
        before = np.float32(59.)
        after = before + np.float32(.005)
        self.assertGreater(abs(float(after - before) - .005), 1e-6)
        check_step_clock(float(before), float(after), dt=.005, dtype="float32")
        with self.assertRaisesRegex(ValueError, "clock differs"):
            check_step_clock(float(before), float(after + np.float32(.005)), dt=.005, dtype="float32")

    def test_ground_support_and_accidental_endpoint_do_not_count_as_carrying(self):
        times = np.arange(500) * .005
        height = np.ones(500)
        contacts = np.tile([1, 1, 0, 0], (500, 1))
        options = dict(required_height=.8, dt=.005, hold_s=2.)
        result = carrying_windows(times, height, loaded_pairs=contacts, **options)
        self.assertTrue(result["reaches_diagnostic_window"])
        self.assertEqual(result["longest_s"], 2.5)
        self.assertIsNone(result["task_success"])
        contacts[:, 2] = 1
        self.assertEqual(carrying_windows(times, height, loaded_pairs=contacts, **options)["longest_s"], 0.)
        contacts[:, 2] = 0
        height[:-1] = .2
        result = carrying_windows(times, height, loaded_pairs=contacts, **options)
        self.assertFalse(result["reaches_diagnostic_window"])
        self.assertEqual(result["longest_s"], .005)
        height[:] = 1.
        contacts[250, 3] = 1
        self.assertEqual(len(carrying_windows(times, height, loaded_pairs=contacts, **options)["windows"]), 2)
        times[250] += .01
        with self.assertRaisesRegex(ValueError, "clock"):
            carrying_windows(times, height, loaded_pairs=contacts, **options)

    def test_common_rotation_and_translation_are_not_relative_slip(self):
        point = np.array([.1, .2, .3])
        hands = np.array([[.1, .1, .3], [.1, .3, .3]])
        rotations = np.tile(np.eye(3), (2, 1, 1))
        reference = hand_relative_positions(point, hands, rotations)
        turn = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        move = np.array([2., 3., 4.])
        actual = hand_relative_positions(turn @ point + move, hands @ turn.T + move,
                                         np.tile(turn, (2, 1, 1)))
        np.testing.assert_allclose(actual, reference, atol=1e-15)
        actual = hand_relative_positions(point + [.01, 0., 0.], hands, rotations)
        np.testing.assert_allclose(np.linalg.norm(actual - reference, axis=1), .01)

    def test_impulse_balance_detects_unexplained_velocity_jump(self):
        # A supported 2 kg body at x=3 has zero net force AND origin torque.
        first = {"mass_kg": 2., "com_world_m": np.array([3., 0., .2]),
                 "linear_momentum_kg_m_s": np.zeros(3),
                 "angular_momentum_about_com_kg_m2_s": np.zeros(3)}
        second = dict(first)
        options = dict(force=np.array([0., 0., 19.62]), torque_about_com=np.zeros(3),
                       gravity=np.array([0., 0., -9.81]), dt=.005)
        balanced = momentum_residual(first, second, **options)
        np.testing.assert_allclose(balanced["linear_ns"], 0.)
        np.testing.assert_allclose(balanced["angular_nms"], 0.)
        second["linear_momentum_kg_m_s"] = np.array([0., 0., 1.])
        injected = momentum_residual(first, second, **options)
        np.testing.assert_allclose(injected["linear_ns"], [0., 0., 1.])
        np.testing.assert_allclose(injected["angular_nms"], [0., -3., 0.])


if __name__ == "__main__":
    unittest.main()
