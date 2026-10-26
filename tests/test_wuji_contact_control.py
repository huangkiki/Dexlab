"""Check endpoint PD against independent constant-force integration."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wuji_control", ROOT / "demos/wuji-contact/control.py")
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)


class WujiSampledControlTests(unittest.TestCase):
    def test_endpoint_force_matches_independent_microsteps(self):
        mass = np.diag([7e-7, 2e-4])
        position = np.array([.02, -.03])
        velocity = np.array([.1, -.2])
        target = np.array([.01, .04])
        for steps in (1, 4):
            with self.subTest(control_steps=steps):
                torque = CONTROL.sampled_pd(
                    position, velocity, target, mass, np.zeros(2), 12., .08, .0005, steps)
                q, v = position.copy(), velocity.copy()
                for _ in range(steps):
                    v += .0005 * np.linalg.solve(mass, torque)
                    q += .0005 * v
                np.testing.assert_allclose(torque, 12.*(target-q)-.08*v, atol=1e-14, rtol=1e-12)

    def test_small_inertia_sampled_system_settles(self):
        mass = np.array([[7e-7]])
        for steps in (1, 4):
            with self.subTest(control_steps=steps):
                q, v = np.array([.1]), np.array([0.])
                for _ in range(400 // steps):
                    torque = CONTROL.sampled_pd(
                        q, v, np.zeros(1), mass, np.zeros(1), 12., .08, .0005, steps)
                    for _ in range(steps):
                        v += .0005 * np.linalg.solve(mass, torque)
                        q += .0005 * v
                self.assertLess(abs(q[0]), 1e-8)
                self.assertLess(abs(v[0]), 1e-6)


if __name__ == "__main__":
    unittest.main()
