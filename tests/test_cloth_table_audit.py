"""Analytic controls for triangle-interior geometry, independent of contacts."""

import unittest

import numpy as np

from dexlab.cloth_table_audit import tiled_box_bounds, triangle_box_depth


class ClothTableAuditTest(unittest.TestCase):
    def setUp(self):
        self.lo = np.array([-1., -1., -.003])
        self.hi = np.array([1., 1., .003])
        self.face = np.array([[-2., 0., -.01], [2., 0., .01], [0., 2., .01]])

    def test_outside_vertices_can_hide_deep_face_intrusion(self):
        vertex_depth = np.maximum(np.minimum(self.face - self.lo, self.hi - self.face).min(axis=1), 0)
        self.assertEqual(float(vertex_depth.max()), 0)
        # The midpoint of the first edge is the box center. No point can be
        # deeper than half the slab thickness, so the analytic optimum is 3 mm.
        self.assertAlmostEqual(triangle_box_depth(self.face, self.lo, self.hi), .003, places=10)

    def test_translated_negative_control_has_no_intrusion(self):
        self.assertEqual(triangle_box_depth(self.face + [0, 0, 1], self.lo, self.hi), 0)

    def test_surface_touch_is_not_interior_intrusion(self):
        face = np.array([[0, 0, .003], [.5, 0, .003], [0, .5, .003]])
        self.assertAlmostEqual(triangle_box_depth(face, self.lo, self.hi), 0, places=10)

    def test_known_parallel_plane_depth(self):
        face = np.array([[0, 0, .002], [.5, 0, .002], [0, .5, .002]])
        self.assertAlmostEqual(triangle_box_depth(face, self.lo, self.hi), .001, places=10)

    def test_tiled_union_requires_no_gap_or_overlap(self):
        centers = np.array([[-.5, 0, 0], [.5, 0, 0]])
        half = np.array([[.5, 1, .003], [.5, 1, .003]])
        lo, hi = tiled_box_bounds(centers, half)
        np.testing.assert_allclose(lo, self.lo)
        np.testing.assert_allclose(hi, self.hi)
        for second_x in (.4, .6):
            with self.subTest(second_x=second_x), self.assertRaises(ValueError):
                tiled_box_bounds([[-.5, 0, 0], [second_x, 0, 0]], half)

    def test_invalid_geometry_is_not_zero(self):
        self.face[0, 0] = np.nan
        with self.assertRaises(ValueError):
            triangle_box_depth(self.face, self.lo, self.hi)


if __name__ == "__main__":
    unittest.main()
