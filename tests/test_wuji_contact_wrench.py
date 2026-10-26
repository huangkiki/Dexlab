"""Check physical wrench invariants, including the special stable two-point case."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class WujiPointWrenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('wuji_wrench', ROOT / 'demos/wuji-contact/wrench.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_point_forces_have_no_moment_about_the_contact_line(self):
        points = np.array([[-.01, .001, 0], [.01, .001, 0]])
        force = np.array([[.3, .02, .1], [-.27, -.03, .08]])
        wrench = self.module.point_force_map(points, np.zeros(3), .01) @ force.ravel()
        moment_about_first_point = .01*wrench[3:] - np.cross(points[0], wrench[:3])
        self.assertAlmostEqual(moment_about_first_point[0], 0., places=15)

    def test_rank_five_can_still_support_special_gravity_alignment(self):
        points = np.array([[-.01, 0, 0], [.01, 0, 0]])
        matrix = self.module.point_force_map(points, np.zeros(3), .01)
        self.assertEqual(np.linalg.matrix_rank(matrix), 5)
        # Opposing 0.3 N grip and equal upward friction support a 20 g sphere.
        force = np.array([.3, 0, .0981, -.3, 0, .0981])
        np.testing.assert_allclose(matrix @ force, [0, 0, .1962, 0, 0, 0], atol=1e-15)

    def test_offset_contact_line_cannot_balance_gravity_with_point_forces(self):
        points = np.array([[-.01, .001, 0], [.01, .001, 0]])
        matrix = self.module.point_force_map(points, np.zeros(3), .01)
        target = np.array([0, 0, .1962, 0, 0, 0])
        forces, *_ = np.linalg.lstsq(matrix, target, rcond=None)
        self.assertGreater(np.linalg.norm(matrix @ forces-target), .01)


if __name__ == '__main__':
    unittest.main()
