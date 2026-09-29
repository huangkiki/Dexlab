"""Do not publish selectively omitted, changed or unfinished batch evidence."""

import json
import tempfile
import unittest
from pathlib import Path

from dexlab.cloth_report import collect, digest


class ClothReportTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "test-mujoco"
        self.run.mkdir()
        (self.run / "trajectory.npz").write_bytes(b"archived trajectory")
        self.meta = {
            "case": {"name": "test", "experiment": "drape"}, "solver": "mujoco",
            "status": "completed", "split": "test", "suite_sha256": "suite",
            "source_before": {}, "source_after": {},
            "trajectory_sha256": digest(self.run / "trajectory.npz"),
        }
        self.write(self.run / "run.json", self.meta)
        self.write(self.run / "summary.json", {
            "checks": {"penetration": False}, "protocol_checks_passed": False,
        })
        self.batch = {
            "status": "completed", "total_count": 2, "passed_count": 0,
            "configuration": {}, "source_sha256": {},
            "suite_sha256": {"suite.json": "suite"}, "split": "test",
            "jobs": [
                {"case": "test", "solver": "mujoco", "suite": "suite.json",
                 "status": "completed", "exit_code": 1, "protocol_checks_passed": False,
                 "summary_sha256": digest(self.run / "summary.json")},
                {"case": "test", "solver": "newton-xpbd", "suite": "suite.json",
                 "status": "timeout", "exit_code": None, "protocol_checks_passed": False},
            ],
        }

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value))

    def report(self):
        self.write(self.root / "batch.json", self.batch)
        return collect(self.root)

    def test_physics_failure_and_timeout_remain_in_denominator(self):
        report = self.report()
        self.assertEqual((report["passed_count"], report["total_count"]), (0, 2))
        self.assertEqual(report["profiles"]["newton-xpbd"]["timeouts"], 1)
        self.assertFalse(report["records"][0]["summary"]["checks"]["penetration"])
        self.assertIsNone(report["records"][1]["summary"])

    def test_corrupted_trajectory_is_rejected(self):
        (self.run / "trajectory.npz").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "frozen batch"):
            self.report()

    def test_rewritten_summary_is_rejected(self):
        self.write(self.run / "summary.json", {"protocol_checks_passed": True})
        with self.assertRaisesRegex(ValueError, "Summary changed"):
            self.report()

    def test_incomplete_or_duplicate_jobs_cannot_publish(self):
        self.batch["status"] = "running"
        with self.assertRaisesRegex(ValueError, "completed batch"):
            self.report()
        self.batch["status"] = "completed"
        self.batch["jobs"][1] = self.batch["jobs"][0]
        with self.assertRaisesRegex(ValueError, "completed batch"):
            self.report()

    def test_falsified_total_is_rejected(self):
        self.batch["passed_count"] = 1
        with self.assertRaisesRegex(ValueError, "pass count"):
            self.report()


if __name__ == "__main__":
    unittest.main()
