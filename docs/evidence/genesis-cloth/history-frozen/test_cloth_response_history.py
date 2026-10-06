"""Synthetic histories extend the frozen first-step fixture, not native evidence."""

import copy
import gzip
import json
from pathlib import Path
import unittest

from dexlab.cloth_response_history import score


def fixture():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/evidence/genesis-cloth/response-record.json.gz"
    )
    data = json.loads(gzip.decompress(path.read_bytes()))
    data.update(duration_s=0.02, repeats=2)
    for case in data["cases"]:
        rows = [{"step": 0, **copy.deepcopy(case["initial"])}]
        rows += [
            {"step": step, **copy.deepcopy(case["final"])}
            for step in range(1, round(0.02 / case["dt"]) + 1)
        ]
        case["episodes"] = [
            {"repeat": i, "rows": copy.deepcopy(rows)} for i in range(2)
        ]
    return data


class HistoryTests(unittest.TestCase):
    def test_equal_duration_and_zero_negative_energy(self):
        result = score(fixture())
        self.assertTrue(result["passed"], result)
        for case in result["cases"]:
            self.assertAlmostEqual(case["episodes"][0]["curve"][-1]["time_s"], 0.02)
            if not case["enabled"]:
                self.assertEqual(
                    case["episodes"][0]["curve"][-1]["kinetic_energy_J"], 0
                )

    def test_missing_intermediate_state_rejected(self):
        data = fixture()
        del data["cases"][0]["episodes"][0]["rows"][2]
        self.assertFalse(score(data)["valid"])

    def test_late_drift_cannot_hide_behind_good_first_step(self):
        data = fixture()
        data["cases"][0]["episodes"][0]["rows"][-1]["pos"][0][0] += 0.01
        result = score(data)
        self.assertTrue(result["valid"])
        self.assertFalse(result["passed"])

    def test_nonfinite_late_velocity_rejected(self):
        data = fixture()
        data["cases"][0]["episodes"][1]["rows"][-1]["vel"][0][0] = float("nan")
        self.assertFalse(score(data)["valid"])

    def test_wrong_duration_rejected(self):
        data = fixture()
        data["duration_s"] = 0.01
        self.assertFalse(score(data)["valid"])
