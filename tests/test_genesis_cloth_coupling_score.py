"""Analytic conservation fixtures, not native experiment evidence."""

import copy
import unittest
from dexlab.genesis_cloth_coupling_score import score


def fixture():
    record = {
        "completed": True,
        "versions": {"genesis-world": "1.4.3"},
        "protocol": {
            "dt_s": 0.002,
            "steps": 150,
            "repeats": 2,
            "diameter_m": 0.008,
            "area_density_kg_m2": 0.2,
            "initial_height_m": 0.02,
            "initial_vz_m_s": -0.1,
            "gravity_m_s2": [0, 0, 0],
            "plate_size_m": [0.08, 0.08, 0.01],
            "plate_mass_kg": 0.001,
        },
        "scenes": [],
    }
    for name, coupled in [("coupled", True), ("disabled", False)]:
        rows = []
        for step in range(151):
            transfer = 1.6e-5 if coupled and step > 50 else 0
            rows.append(
                {
                    "step": step,
                    "pos": [[0, 0, 0.02]] * 4,
                    "vel": [[0, 0, -0.1 + transfer / 0.00032]] * 4,
                    "plate_pos": [0, 0, 0],
                    "plate_vel": [0, 0, -transfer / 0.001],
                }
            )
        record["scenes"].append(
            {
                "name": name,
                "coupled": coupled,
                "native": {
                    "particle_count": 4,
                    "particle_mass_kg": [0.00008] * 4,
                    "plate_mass_kg": 0.001,
                    "plate_dofs": 6,
                },
                "episodes": [
                    {"repeat": i, "rows": copy.deepcopy(rows)} for i in range(2)
                ],
            }
        )
    return record


class CouplingScoreTests(unittest.TestCase):
    def test_conservation_fixture(self):
        self.assertTrue(score(fixture())["passed"])

    def test_one_way_transfer_fails(self):
        r = fixture()
        for e in r["scenes"][0]["episodes"]:
            for row in e["rows"]:
                row["plate_vel"] = [0, 0, 0]
        self.assertFalse(score(r)["passed"])

    def test_no_exchange_is_not_positive(self):
        r = fixture()
        r["scenes"][0]["episodes"] = copy.deepcopy(r["scenes"][1]["episodes"])
        self.assertFalse(score(r)["passed"])

    def test_missing_nonfinite_and_fixed_fail(self):
        for defect in ["missing", "nan", "fixed"]:
            r = fixture()
            if defect == "missing":
                r["scenes"][0]["episodes"][0]["rows"].pop()
            if defect == "nan":
                r["scenes"][0]["native"]["plate_mass_kg"] = float("nan")
            if defect == "fixed":
                r["scenes"][0]["native"]["plate_dofs"] = 0
            with self.subTest(defect=defect):
                self.assertFalse(score(r)["valid"])
