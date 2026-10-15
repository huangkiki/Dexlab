"""Analytical transformations check the quantities shown in cutting videos."""

import unittest

import numpy as np

from dexlab.cutting_geometry import material_points
from dexlab.cutting_metrics import face_opening, face_pairs, reference_tetrahedra, signed_volumes


class ReplayMetricTests(unittest.TestCase):
    def test_second_cross_cut_measures_y_opening_and_preserves_first_digit(self):
        reference = material_points((.03, .03, .015), .0075)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        first = np.where(reference[:, 0] < 0, 1, 2)
        second = np.where(reference[:, 1] < 0, 1, 2)
        pairs, locations = face_pairs(reference, 0., .00375, axis=1)
        position = reference.copy()
        position[second == 2, 1] += .0015
        gap, count = face_opening(reference, position, deformation, first + 3*second,
                                  pairs, locations, 1, axis=1)
        self.assertAlmostEqual(gap, 1.5, places=12)
        self.assertEqual(count, len(pairs))

    def setUp(self):
        self.reference = material_points((.03, .015, .015), .0075)
        self.deformation = np.tile(np.eye(3), (len(self.reference), 1, 1))

    def test_signed_volume_preserves_rigid_motion_and_measures_affine_compression(self):
        tets = reference_tetrahedra(self.reference, .00375, np.ones(len(self.reference), dtype=bool))
        initial = signed_volumes(self.reference, tets)
        self.assertTrue((initial > 0).all())
        stretch = np.diag([.8, .9, 1.1])
        changed = signed_volumes(self.reference @ stretch.T + [.2, -.3, .1], tets)
        np.testing.assert_allclose(changed / initial, np.linalg.det(stretch), atol=1e-12)
        reflected = signed_volumes(self.reference * [-1, 1, 1], tets)
        np.testing.assert_allclose(reflected, -initial, atol=1e-15)

    def test_gap_is_unavailable_before_cut_and_equals_native_relative_motion(self):
        pairs, locations = face_pairs(self.reference, 0., .00375)
        codes = np.zeros(len(self.reference), dtype=int)
        self.assertEqual(face_opening(self.reference, self.reference, self.deformation,
                                      codes, pairs, locations, 0), (None, 0))
        codes = np.where(self.reference[:, 0] < 0, 1, 2)
        positions = self.reference + [.1, -.2, .3]
        positions[codes == 2, 0] += .004
        gap, count = face_opening(self.reference, positions, self.deformation, codes, pairs, locations, 0)
        self.assertAlmostEqual(gap, 4., places=10)
        self.assertEqual(count, len(pairs))
        # A prior cut's digit must not create samples for a later cut.
        self.assertEqual(face_opening(self.reference, positions, self.deformation,
                                      codes, pairs, locations, 1), (None, 0))

    def test_affine_continuity_does_not_create_a_visual_crack(self):
        pairs, locations = face_pairs(self.reference, 0., .00375)
        gradient = np.array([[.9, .1, 0.], [0., 1.1, .1], [0., 0., 1.]])
        deformation = np.tile(gradient, (len(self.reference), 1, 1))
        positions = self.reference @ gradient.T
        codes = np.where(self.reference[:, 0] < 0, 1, 2)
        gap, _ = face_opening(self.reference, positions, deformation, codes, pairs, locations, 0)
        self.assertAlmostEqual(gap, 0., places=12)


if __name__ == '__main__':
    unittest.main()
