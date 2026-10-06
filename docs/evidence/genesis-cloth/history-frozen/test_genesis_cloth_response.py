import unittest
import numpy as np
from dexlab.genesis_cloth_response import surface_error, score


class ResponseGeometryTests(unittest.TestCase):
    def setUp(self):
        self.rest = np.array([[0.0, -1, 0], [0, 1, 0], [-1, 0, 0], [1, 0, 0]])
        self.faces = np.array([[0, 1, 2], [1, 0, 3]])

    def test_flat_reference(self):
        self.assertEqual(
            surface_error(self.rest, self.rest, self.faces),
            {"strain_rms": 0.0, "bend_rms_rad": 0.0},
        )

    def test_uniform_stretch_reference(self):
        self.assertAlmostEqual(
            surface_error(self.rest * 1.1, self.rest, self.faces)["strain_rms"], 0.1
        )

    def test_fold_angle_reference(self):
        p = self.rest.copy()
        p[:, 2] = 0.2 * abs(p[:, 0])
        self.assertAlmostEqual(
            surface_error(p, self.rest, self.faces)["bend_rms_rad"], 2 * np.arctan(0.2)
        )

    def test_rigid_transform_preserves_errors(self):
        p = self.rest[:, [2, 0, 1]] + 5
        self.assertAlmostEqual(surface_error(p, self.rest, self.faces)["strain_rms"], 0)
        self.assertAlmostEqual(
            surface_error(p, self.rest, self.faces)["bend_rms_rad"], 0
        )

    def test_degenerate_rejected(self):
        with self.assertRaises(ValueError):
            surface_error(self.rest * 0, self.rest, self.faces)

    def test_incomplete_record_rejected(self):
        self.assertFalse(score({"completed": False})["valid"])
