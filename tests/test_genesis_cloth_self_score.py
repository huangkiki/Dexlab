import unittest
import numpy as np
from dexlab.genesis_cloth_self_score import canonical_mesh, pair_distances, score
from dexlab.genesis_cloth_self_probe import write_layers
from pathlib import Path
from tempfile import TemporaryDirectory


class PairGeometryTests(unittest.TestCase):
    def test_analytic_separation(self):
        p = np.array([[0, 0, 0], [0, 0, 0.006], [0.003, 0.004, 0]])
        np.testing.assert_allclose(
            pair_distances(p, np.array([[0, 1], [0, 2]])), [0.006, 0.005]
        )

    def test_permutation_independent_signature(self):
        p = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        g = np.array([False] * 3)
        f = np.array([[0, 1, 2]])
        m = np.ones(3)
        a = canonical_mesh(p, g, f, m)
        b = canonical_mesh(p[[2, 0, 1]], g, np.array([[1, 2, 0]]), m)
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x, y)

    def test_two_authored_components(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "layers.obj"
            write_layers(path, 0.03)
            lines = path.read_text().splitlines()
        vertices = [line for line in lines if line.startswith("v ")]
        faces = [
            list(map(int, line.split()[1:])) for line in lines if line.startswith("f ")
        ]
        self.assertEqual(len(vertices), 50)
        self.assertEqual(len(faces), 64)
        self.assertTrue(all(max(f) <= 25 or min(f) > 25 for f in faces))

    def test_incomplete_record_rejected(self):
        self.assertFalse(score({"completed": False})["valid"])
