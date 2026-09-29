"""Batch failure accounting and frozen-input guards, without native simulations."""

import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dexlab.cloth_benchmark import batch


class ClothBatchTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.suite = self.root / "cases.json"
        self.suite.write_text(json.dumps({"cases": [
            {"split": "test", "case": {"name": "held-out-a"}},
            {"split": "test", "case": {"name": "held-out-b"}},
            {"split": "development", "case": {"name": "dev"}},
        ]}))
        self.args = argparse.Namespace(
            suite=[self.suite], split="test", solver=["mujoco"],
            output=self.root / "batch", dt=0.0005, iterations=10,
            device="cpu", timeout=1,
        )

    def test_timeout_and_runtime_failure_remain_in_denominator(self):
        with patch("dexlab.cloth_benchmark.subprocess.run", side_effect=[
            subprocess.TimeoutExpired("episode", 1),
            subprocess.CompletedProcess("episode", 2),
        ]) as launch:
            self.assertFalse(batch(self.args))
        report = json.loads((self.args.output / "batch.json").read_text())
        self.assertEqual(report["total_count"], 2)
        self.assertEqual(report["passed_count"], 0)
        self.assertEqual(report["jobs"][0]["status"], "timeout")
        self.assertEqual(report["jobs"][1]["exit_code"], 2)
        self.assertEqual(launch.call_count, 2)
        self.assertEqual(len(list(self.args.output.glob("*.log"))), 2)

    def test_changed_suite_stops_remaining_cases(self):
        def mutate_suite(*args, **kwargs):
            self.suite.write_text("{}")
            return subprocess.CompletedProcess("episode", 1)

        with patch("dexlab.cloth_benchmark.subprocess.run", side_effect=mutate_suite):
            with self.assertRaisesRegex(RuntimeError, "Frozen batch"):
                batch(self.args)
        report = json.loads((self.args.output / "batch.json").read_text())
        self.assertEqual(report["status"], "source_or_suite_changed")
        self.assertEqual(report["jobs"][1]["status"], "queued")

    def test_saved_pass_with_failed_process_is_not_success(self):
        def write_untrustworthy_summary(command, **kwargs):
            output = Path(command[command.index("--output") + 1])
            output.mkdir()
            (output / "summary.json").write_text(json.dumps({
                "protocol_checks_passed": True, "checks": {"finite": True},
            }))
            return subprocess.CompletedProcess(command, 1)

        with patch("dexlab.cloth_benchmark.subprocess.run", side_effect=write_untrustworthy_summary):
            self.assertFalse(batch(self.args))

    def test_existing_output_is_preserved(self):
        self.args.output.mkdir()
        evidence = self.args.output / "keep.json"
        evidence.write_text("original")
        with self.assertRaises(FileExistsError):
            batch(self.args)
        self.assertEqual(evidence.read_text(), "original")


if __name__ == "__main__":
    unittest.main()
