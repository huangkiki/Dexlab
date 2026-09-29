"""Known geometric counterexamples for the independent self-crossing audit."""

from dataclasses import replace
import unittest

import numpy as np

from dexlab.cloth import ClothCase
from dexlab.cloth_self_contact import audit_record, crossing_count


class SelfContactAuditTest(unittest.TestCase):
    triangles = np.array([[0, 1, 2], [3, 4, 5]])
    first = np.array([[0, 0, 0], [2, 0, 0], [0, 2, 0]], dtype=float)

    def count(self, second):
        return crossing_count(np.vstack((self.first, second)), self.triangles)

    def test_edge_through_face_without_vertex_intersection(self):
        second = np.array([[0.5, 0.2, -1], [0.5, 0.2, 1], [0.5, 1, 0]])
        self.assertEqual(self.count(second), (1, 0))
        self.assertEqual(self.count(second[::-1]), (1, 0))

    def test_coplanar_overlap_separation_and_boundary_touch(self):
        self.assertEqual(self.count(self.first + [0.2, 0.2, 0]), (1, 0))
        self.assertEqual(self.count(self.first + [0, 0, 0.001]), (0, 0))
        self.assertEqual(self.count(self.first + [2, 0, 0]), (0, 0))

    def test_rotated_coplanar_overlap(self):
        vertices = np.vstack((self.first, self.first + [0.2, 0.2, 0]))
        angle = 0.71
        rotation = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0],
                             [-np.sin(angle), 0, np.cos(angle)]])
        vertices = vertices @ rotation.T + [1, 2, 3]
        self.assertEqual(crossing_count(vertices, self.triangles), (1, 0))

    def test_shared_vertex_exclusion_and_degenerate_report(self):
        vertices = np.vstack((self.first, [[0.5, 0.2, -1], [0.5, 0.2, 1]]))
        self.assertEqual(crossing_count(vertices, np.array([[0, 1, 2], [0, 3, 4]])), (0, 0))
        self.assertEqual(self.count(np.zeros((3, 3))), (0, 1))

    def test_fold_preserves_mass_and_has_no_initial_surface_crossings(self):
        flat = ClothCase(nx=9, ny=5)
        folded = replace(flat, experiment="folded-drop")
        vertices, triangles, masses = folded.mesh()
        self.assertAlmostEqual(masses.sum(), flat.mesh()[2].sum())
        self.assertEqual(crossing_count(vertices, triangles), (0, 0))
        self.assertEqual(len(folded.pins), 0)
        with self.assertRaises(ValueError):
            replace(folded, nx=8)

    def test_sampling_reports_coverage_and_first_failure(self):
        separated = np.vstack((self.first, self.first + [0, 0, 1]))
        crossing = np.vstack((self.first, self.first + [0.2, 0.2, 0]))
        record = np.array([separated, crossing, separated])
        report = audit_record(np.array([0, 0.01, 0.02]), record, self.triangles)
        self.assertEqual(report["audited_frame_count"], 3)
        self.assertEqual(report["frames_with_crossings"], 1)
        self.assertAlmostEqual(report["first_crossing_time_s"], 0.01)


if __name__ == "__main__":
    unittest.main()
