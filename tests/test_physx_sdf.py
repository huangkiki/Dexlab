"""Physical counterexamples for the concavity scorer."""

import copy
import unittest

import numpy as np

from dexlab.physx_sdf import DT, DURATION, GRAVITY, INITIAL_Z, MASS, score


def falling():
    t = np.arange(1, round(DURATION / DT) + 1) * DT
    p, v = np.zeros((len(t), 2, 3)), np.zeros((len(t), 2, 3))
    p[:, 1, 2] = 0.05
    p[:, 0, 2] = INITIAL_Z - 0.5 * GRAVITY * t**2
    v[:, 0, 2] = -GRAVITY * t
    return {"time": t, "position": p, "velocity": v, "force": np.zeros((len(t), 3))}


def supported(x):
    a = falling()
    hit = a["position"][:, 0, 2] <= 0.066
    a["position"][:, 0, 0] = x
    a["position"][hit, 0, 2] = 0.066
    a["velocity"][hit, 0] = 0
    a["force"][hit, 2] = MASS * GRAVITY
    return a


class SdfContactTests(unittest.TestCase):
    def test_ballistic_hole_and_supported_surface(self):
        self.assertTrue(score("sdf-hole", falling())["passed"])
        self.assertTrue(score("sdf-surface", supported(0.03))["passed"])
        self.assertTrue(score("convex-hole", supported(0))["passed"])

    def test_convex_hull_behavior_cannot_pass_sdf_hole(self):
        result = score("sdf-hole", supported(0))
        self.assertFalse(result["checks"]["falls_through_hole"])
        self.assertFalse(result["checks"]["no_false_contact"])

    def test_absent_collider_cannot_pass_positive_contact_control(self):
        a = falling()
        a["position"][:, 0, 0] = 0.03
        self.assertFalse(score("sdf-surface", a)["passed"])

    def test_false_suspension_wrong_support_and_penetration_fail(self):
        for failure in ("force", "penetration", "speed", "fixture"):
            a = supported(0.03)
            if failure == "force":
                a["force"][:] = 0
            elif failure == "penetration":
                a["position"][-50:, 0, 2] -= 0.003
            elif failure == "speed":
                a["velocity"][-50:, 0, 0] = 0.1
            else:
                a["position"][:, 1, 2] += 0.001
            self.assertFalse(score("sdf-surface", a)["passed"], failure)

    def test_missing_nonfinite_and_repeated_time_fail(self):
        for failure in ("missing", "nonfinite", "time"):
            a = copy.deepcopy(falling())
            if failure == "missing":
                a["force"] = a["force"][:-1]
            elif failure == "nonfinite":
                a["velocity"][0] = np.nan
            else:
                a["time"][1] = a["time"][0]
            self.assertFalse(score("sdf-hole", a)["passed"], failure)


if __name__ == "__main__":
    unittest.main()
