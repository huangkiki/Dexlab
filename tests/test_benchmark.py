"""Evidence integrity, paired sampling and failure accounting for benchmarks."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from dexlab.benchmark import (
    DEFAULT_SUITE,
    aggregate,
    load_receipt,
    read_suite,
    select_cases,
    sha256,
    wilson_interval,
    write_json,
)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = read_suite(DEFAULT_SUITE)

    def test_disjoint_frozen_cases(self):
        self.assertEqual(len(select_cases(self.spec, "development", None)), 20)
        self.assertEqual(len(select_cases(self.spec, "regression", None)), 10)
        self.assertEqual(len(select_cases(self.spec, "test", None)), 100)
        cases = self.spec["cases"]
        self.assertEqual(len({c["seed"] for c in cases}), 130)
        self.assertNotEqual(cases[0]["parameters"], cases[20]["parameters"])

    def test_cross_split_and_path_case_ids_rejected(self):
        with self.assertRaises(ValueError):
            select_cases(self.spec, "test", "development-000")
        for field, value in (
            ("id", "../escape"),
            ("seed", self.spec["cases"][1]["seed"]),
        ):
            spec = copy.deepcopy(self.spec)
            spec["cases"][0][field] = value
            path = self.root / "suite.json"
            write_json(path, spec)
            with self.assertRaises(ValueError):
                read_suite(path)

    def test_nonfinite_or_out_of_range_physical_cases_rejected(self):
        for value in (float("nan"), -0.2, 100):
            spec = copy.deepcopy(self.spec)
            spec["cases"][0]["parameters"]["apple_mass"] = value
            path = self.root / "suite.json"
            path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):
                read_suite(path)

    def test_missing_or_failed_runs_never_disappear_from_denominator(self):
        base = {"backend": "mujoco", "parameters": {"timestep": 0.0005}}
        rows = [
            base | {"status": "scored", "outcome": {"passed": True}},
            base | {"status": "scored", "outcome": {"passed": False}},
            base | {"status": "runtime_error", "outcome": {"passed": True}},
            base,
        ]
        report = aggregate(rows)["groups"]["mujoco/dt=0.0005"]
        self.assertEqual(report["success_rate"], 0.25)
        self.assertEqual(report["scheduled"], 4)
        self.assertEqual(report["terminal"], 3)

    def test_ten_successes_do_not_imply_certainty(self):
        low, high = wilson_interval(10, 10)
        self.assertLess(low, 0.73)
        self.assertAlmostEqual(high, 1.0)
        self.assertIsNone(wilson_interval(0, 0))

    def test_resume_rejects_changed_case_and_artifacts(self):
        artifact = self.root / "evidence.npz"
        artifact.write_bytes(b"original evidence")
        expected = {"id": "regression-000", "parameters": {"apple_mass": 0.2}}
        result = expected | {
            "artifacts": {artifact.name: sha256(artifact)},
            "status": "scored",
        }
        write_json(self.root / "result.json", result)
        self.assertEqual(load_receipt(self.root, expected), result)
        with self.assertRaises(ValueError):
            load_receipt(self.root, expected | {"id": "test-000"})
        artifact.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            load_receipt(self.root, expected)

    def test_baseline_is_explicit_and_not_part_of_held_out_denominator(self):
        case = select_cases(self.spec, "test", "baseline")[0]
        self.assertEqual(case["split"], "baseline")
        self.assertEqual(case["parameters"]["apple_mass"], 0.2)
        self.assertNotIn(case, self.spec["cases"])


if __name__ == "__main__":
    unittest.main()
