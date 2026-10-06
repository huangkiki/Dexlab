import unittest
import numpy as np
from dexlab.genesis_cloth_geometry import audit


class GeometryTests(unittest.TestCase):
    def test_plane_crossing_between_clear_frames(self):
        p = np.array(
            [[[0, 0, 1], [1, 0, 1], [0, 1, 1]], [[0, 0, -1], [1, 0, -1], [0, 1, -1]]]
        )
        result = audit(p, [[0, 1, 2]], [0, 1], plane_z=0)
        self.assertEqual(result["plane"]["crossing_intervals"], 1)
        self.assertEqual(result["plane"]["maximum_midsurface_depth_m"], 1)

    def test_coplanar_overlapping_triangles_detected(self):
        p = np.array(
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0.1, 0.1, 0], [1, 0.1, 0], [0.1, 1, 0]]
        )
        result = audit([p, p], [[0, 1, 2], [3, 4, 5]], [0, 1])
        self.assertEqual(result["frames_with_self_crossing"], 2)

    def test_shared_vertex_exclusion_explicit(self):
        p = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        result = audit([p, p], [[0, 1, 2], [1, 3, 2]], [0, 1])
        self.assertEqual(result["maximum_crossing_pairs"], 0)

    def test_missing_time_fails(self):
        with self.assertRaises(ValueError):
            audit(np.zeros((2, 3, 3)), [[0, 1, 2]], [0, 0])


class PadGeometryTests(unittest.TestCase):
    def test_interior_crossing_with_all_vertices_outside(self):
        from dexlab.genesis_cloth_geometry import audit_prismatic_pads

        rows = [
            {
                "step": 0,
                "pos": [[-2, -2, 0], [2, -2, 0], [0, 2, 0]],
                "pad_pos": [[0, 0, 0], [10, 0, 0]],
                "pad_quat": [[1, 0, 0, 0]] * 2,
            }
        ]
        result = audit_prismatic_pads(rows, [[0, 1, 2]], halfsize=(0.1, 0.1, 0.1))
        self.assertAlmostEqual(result["maximum_triangle_interior_depth_m"], 0.1)

    def test_rotation_is_not_silently_ignored(self):
        from dexlab.genesis_cloth_geometry import audit_prismatic_pads

        rows = [
            {
                "step": 0,
                "pos": [[-2, -2, 0], [2, -2, 0], [0, 2, 0]],
                "pad_pos": [[0, 0, 0], [10, 0, 0]],
                "pad_quat": [[0, 1, 0, 0]] * 2,
            }
        ]
        with self.assertRaises(ValueError):
            audit_prismatic_pads(rows, [[0, 1, 2]])
