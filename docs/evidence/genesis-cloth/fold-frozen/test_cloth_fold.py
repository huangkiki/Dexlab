import copy
import unittest
import numpy as np
from dexlab.cloth_fold import fold, score


def fixture():
    rest = np.array([[x, y, 0.2] for x in (-0.02, 0, 0.02) for y in (-0.02, 0.02)])
    faces = [[0, 2, 1], [1, 2, 3], [2, 4, 3], [3, 4, 5]]
    cases = []
    for angle in (0, 150, 170):
        rows = [
            {
                "step": i,
                "pos": fold(rest, angle).tolist(),
                "vel": np.zeros_like(rest).tolist(),
            }
            for i in range(21)
        ]
        cases.append(
            {
                "angle_deg": angle,
                "rest": rest.tolist(),
                "faces": faces,
                "mass": [0.00032 / 6] * 6,
                "episodes": [
                    {"repeat": i, "rows": copy.deepcopy(rows)} for i in range(2)
                ],
            }
        )
    return {
        "completed": True,
        "version": "1.4.3",
        "dt_s": 0.002,
        "steps": 20,
        "cases": cases,
    }


class FoldTests(unittest.TestCase):
    def test_fold_is_rigid_on_each_side(self):
        p = np.array([[0, 0, 0.2], [0.02, 0, 0.2], [0.02, 0.02, 0.2], [-0.02, 0, 0.2]])
        q = fold(p, 170)
        np.testing.assert_allclose(
            np.linalg.norm(q[:3, None] - q[None, :3], axis=2),
            np.linalg.norm(p[:3, None] - p[None, :3], axis=2),
        )
        np.testing.assert_allclose(q[3], p[3])
        self.assertLess(q[1, 0], 0)
        self.assertGreater(q[1, 2], 0.2)

    def test_synthetic_static_geometry_and_reset(self):
        self.assertTrue(score(fixture())["passed"])

    def test_late_center_drift_fails(self):
        r = fixture()
        for vertex in r["cases"][1]["episodes"][0]["rows"][-1]["pos"]:
            vertex[2] += 0.001
        self.assertFalse(score(r)["passed"])

    def test_disconnected_geometry_rejected(self):
        r = fixture()
        r["cases"][0]["faces"] = [[0, 1, 2], [3, 4, 5]]
        self.assertFalse(score(r)["valid"])

    def test_missing_or_nonfinite_sample_rejected(self):
        r = fixture()
        r["cases"][0]["episodes"][0]["rows"].pop()
        self.assertFalse(score(r)["valid"])
        r = fixture()
        r["cases"][1]["episodes"][1]["rows"][-1]["vel"][0][0] = float("nan")
        self.assertFalse(score(r)["valid"])
