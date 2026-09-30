"""Analytic dynamics and negative controls for the transient diagnostic."""

import unittest

import numpy as np

from dexlab.contact_load import LoadCase
from dexlab.contact_transient import reference, score


class TransientTests(unittest.TestCase):
    def data(self, **parameters):
        case = LoadCase()
        time = np.arange(case.steps + 1) * case.timestep
        pose = np.zeros((case.steps + 1, 7))
        pose[:, 3] = 1
        pose[:, 2] = case.half_size - reference(time, case.mass, **parameters)
        return case, {"time": time, "pose": pose}

    def test_reference_solves_independent_equation_and_static_limit(self):
        # Finite differences check the differential equation, not its formula.
        time = np.arange(0, 0.19, 1e-6)
        x = reference(time, 0.2)
        velocity = np.gradient(x, time)
        acceleration = np.gradient(velocity, time)
        residual = 0.2 * acceleration + 40 * velocity + 20000 * x - 2
        self.assertLess(np.abs(residual[10:-10]).max(), 2e-5)
        self.assertEqual(x[0], 0)
        self.assertAlmostEqual(x[-1], 2 / 20000, delta=1e-11)
        self.assertAlmostEqual(reference(0.59, 0.2), 6 / 20000, delta=1e-11)

    def test_exact_target_passes_without_temporal_alignment(self):
        case, data = self.data()
        self.assertTrue(score(case, data)["passed"])
        data["pose"][10:] = data["pose"][:-10].copy()
        self.assertFalse(score(case, data)["passed"])

    def test_same_static_stiffness_wrong_damping_fails(self):
        case, data = self.data(damping=5)
        self.assertFalse(score(case, data)["passed"])

    def test_wrong_stiffness_and_nonfinite_or_missing_data_fail(self):
        case, data = self.data(stiffness=40000)
        self.assertFalse(score(case, data)["passed"])
        case, data = self.data()
        data["pose"][3, 2] = np.nan
        self.assertFalse(score(case, data)["passed"])
        del data["pose"]
        self.assertFalse(score(case, data)["passed"])

    def test_invalid_reference_is_rejected(self):
        for mass in (0, -1, np.nan, 0.001):
            with self.assertRaises(ValueError):
                reference([0, 0.01], mass)


if __name__ == "__main__":
    unittest.main()
