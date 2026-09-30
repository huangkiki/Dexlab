"""Analytical and adversarial tests of the independent plane scorer."""

import unittest

import numpy as np

from dexlab.contact_plane import PlaneCase, reference, score


def exact_record(case):
    t = np.arange(case.steps + 1) * case.timestep
    x, v = reference(case, t)
    pose = np.zeros((len(t), 7))
    pose[:, 0] = x
    pose[:, 2] = case.half_size
    pose[:, 3] = 1
    velocity = np.zeros((len(t), 6))
    velocity[:, 0] = v
    force = case.mass * np.diff(velocity[:, :3], axis=0) / case.timestep
    force[:, 2] += case.mass * case.gravity
    return {
        "time": t,
        "pose": pose,
        "velocity": velocity,
        "contact_force": force,
        "contact_known": np.ones(case.steps, dtype=bool),
        "step_completed": np.ones(case.steps, dtype=bool),
    }


class PlaneScoreTests(unittest.TestCase):
    def test_analytical_positive_negative_and_rest(self):
        for friction, speed in [(0.3, 0.25), (0.3, -0.25), (0.0, 0.25), (0.3, 0)]:
            case = PlaneCase(friction=friction, initial_speed=speed)
            self.assertTrue(score(case, exact_record(case))["passed"])

    def test_adhesive_braking_cannot_pass_frictionless_control(self):
        case = PlaneCase(friction=0)
        data = exact_record(case)
        x, v = reference(PlaneCase(friction=0.3), data["time"])
        data["pose"][:, 0] = x
        data["velocity"][:, 0] = v
        data["contact_force"][:, 0] = case.mass * np.diff(v) / case.timestep
        result = score(case, data)
        self.assertTrue(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["coulomb_position"])
        self.assertFalse(result["passed"])

    def test_missing_contact_is_unknown_not_zero(self):
        case = PlaneCase()
        data = exact_record(case)
        data["contact_known"][2] = False
        self.assertFalse(score(case, data)["checks"]["complete_contact_coverage"])

    def test_corrupt_force_and_time_are_rejected(self):
        case = PlaneCase()
        data = exact_record(case)
        data["contact_force"][12, 0] += 1
        self.assertFalse(score(case, data)["checks"]["momentum_balance"])
        data = exact_record(case)
        data["time"][12] = data["time"][11]
        self.assertFalse(score(case, data)["checks"]["uniform_time_grid"])

    def test_invalid_orientation_and_tipping_are_rejected(self):
        case = PlaneCase()
        data = exact_record(case)
        data["pose"][12, 3] = 2
        self.assertFalse(score(case, data)["checks"]["unit_quaternions"])
        data = exact_record(case)
        data["pose"][12, 3:] = [np.cos(0.1), np.sin(0.1), 0, 0]
        self.assertFalse(score(case, data)["checks"]["no_tipping_reference_applicable"])

    def test_no_data_is_failure(self):
        self.assertFalse(score(PlaneCase(), {})["passed"])

    def test_balanced_forces_do_not_justify_levitation(self):
        case = PlaneCase()
        data = exact_record(case)
        data["pose"][:, 2] += 0.1
        result = score(case, data)
        self.assertTrue(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["surface_contact_geometry"])

    def test_transverse_drift_and_initial_tilt_are_rejected(self):
        case = PlaneCase()
        data = exact_record(case)
        data["pose"][:, 1] = data["time"] * 0.1
        self.assertFalse(score(case, data)["checks"]["no_transverse_drift"])
        data = exact_record(case)
        data["pose"][:, 3:] = [np.cos(0.1), np.sin(0.1), 0, 0]
        self.assertFalse(
            score(case, data)["checks"]["initially_level_reference_applicable"]
        )

    def test_bad_protocol_parameters_rejected(self):
        for kw in [
            {"mass": 0},
            {"friction": -1},
            {"timestep": 0.0007},
            {"initial_speed": np.nan},
        ]:
            with self.assertRaises(ValueError):
                PlaneCase(**kw)
