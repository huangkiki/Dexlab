import runpy
from pathlib import Path
import unittest

import numpy as np


DEMO = Path(__file__).resolve().parents[1] / "demos/rope-opening-a"
SCORER = runpy.run_path(str(DEMO / "evaluate.py"))
is_single_loop = SCORER["is_single_loop"]
strand_sections = SCORER["strand_sections"]


class OpeningAScoreTest(unittest.TestCase):
    def test_loop_requires_connectivity_and_valid_edges(self):
        loop = np.array([[1, 0], [1, 2], [3, 2], [0, 3]])
        self.assertTrue(is_single_loop(loop[[2, 0, 3, 1]], 4))
        self.assertFalse(is_single_loop(loop[:-1], 4))
        self.assertFalse(is_single_loop(np.array([[0, 1], [1, 0], [3, 2], [2, 3]]), 4))
        separate_loops = np.array([[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3]])
        self.assertFalse(is_single_loop(separate_loops, 6))

    def test_sections_measure_both_strands_even_at_a_vertex(self):
        points = np.array([[-0.25, 0.04, 0], [0, 0.04, 0], [0.25, 0.04, 0],
                           [0.25, -0.04, 0], [-0.25, -0.04, 0]])
        edges = np.array([[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]])
        sections = strand_sections(points, edges)
        np.testing.assert_allclose(sections[:, :, 0], np.tile([-0.04, 0.04], (9, 1)))
        self.assertIsNone(strand_sections(points + [0.4, 0, 0], edges))


if __name__ == "__main__":
    unittest.main()
