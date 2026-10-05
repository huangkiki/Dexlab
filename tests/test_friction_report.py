"""Corrupt campaign manifests must fail before any native or curve processing."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "demos/contact-benchmark/report_friction.py"
spec = importlib.util.spec_from_file_location("friction_report", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrictionReportIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.batch = {
            "status": "completed", "source_unchanged": True,
            "source_sha256": {},
            "suite": {"defaults": {"mass": 0.2}, "cases": [{"name": "dev-test"}],
                      "engines": ["mujoco", "superdex"], "max_runs": 2},
            "runs": [{"id": "mujoco-dev-test"}, {"id": "superdex-dev-test"}],
        }

    def reject(self, pattern):
        (self.root / "batch.json").write_text(json.dumps(self.batch))
        with self.assertRaisesRegex(ValueError, pattern):
            module.report(self.root)

    def test_interrupted_campaign_cannot_be_reported_complete(self):
        self.batch["status"] = "running"
        self.reject("Incomplete")

    def test_missing_duplicate_or_reordered_partner_is_rejected(self):
        rows = self.batch["runs"]
        for bad in (rows[:1], [rows[0], rows[0]], list(reversed(rows))):
            self.batch["runs"] = bad
            self.reject("Missing, duplicated or reordered")

    def test_changed_source_and_escaping_snapshot_are_rejected(self):
        self.batch["source_sha256"] = {"../outside.py": "ignored"}
        self.reject("Invalid source")
        path = self.root / "source" / "fixture.py"
        path.parent.mkdir()
        path.write_text("changed source")
        self.batch["source_sha256"] = {"fixture.py": "0" * 64}
        self.reject("Changed source")

    def test_runtime_cannot_silently_change_frozen_mass(self):
        path = self.root / "mujoco-dev-test"
        path.mkdir()
        (path / "run.json").write_text(json.dumps({"case": {"name": "dev-test", "mass": 0.4}, "engine": "mujoco"}))
        self.batch["runs"][0].update(case={"name": "dev-test", "mass": 0.2}, engine="mujoco")
        self.reject("Runtime case differs")
