"""Reproduce all three outcomes from their packaged raw records."""

import gzip
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from dexlab.tactile_score import evaluate
from dexlab.tactile_observation_audit import audit_observations

ROOT = Path(__file__).resolve().parents[1] / "docs/evidence/synthetic-tactile"


class TactileEvidenceTests(unittest.TestCase):
    def test_manifest(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for name, expected in manifest["files"].items():
            with self.subTest(name=name):
                data = (ROOT / name).read_bytes()
                self.assertEqual(len(data), expected["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected["sha256"])

    def test_all_native_and_observer_outcomes(self):
        audit = json.loads((ROOT / "audit.json").read_text())
        for batch, expected in ((1, False), (2, False), (3, True)):
            path = ROOT / f"batch{batch}"
            record = json.loads(gzip.decompress((path / "record.json.gz").read_bytes()))
            arrays = {}
            for row in record["runs"]:
                with np.load(
                    path / (row["name"] + ".npz"), allow_pickle=False
                ) as archive:
                    arrays[row["name"]] = dict(archive)
                self.assertEqual(
                    audit_observations(arrays[row["name"]], row["resolution"]),
                    audit[str(batch)]["observation_audit"][row["name"]],
                )
            score = evaluate(record, arrays)
            self.assertTrue(score["valid"])
            self.assertEqual(score["passed"], expected)
            self.assertEqual(score, json.loads((path / "score.json").read_text()))
