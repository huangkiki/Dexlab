"""Offline reproducibility checks of packaged successful and failed diagnostics."""

import gzip
import hashlib
import json
from pathlib import Path
import unittest

from dexlab.genesis_cloth_score import score as plane_score
from dexlab.genesis_cloth_coupling_score import score as coupling_score
from dexlab.genesis_cloth_response import score as response_score
from dexlab.genesis_cloth_gripper_score import score as gripper_score
from dexlab.genesis_cloth_self_score import score as self_score

ROOT = Path(__file__).resolve().parents[1] / "docs/evidence/genesis-cloth"


class EvidenceTests(unittest.TestCase):
    def test_manifest_bytes_and_hashes(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for name, expected in manifest["files"].items():
            with self.subTest(name=name):
                data = (ROOT / name).read_bytes()
                self.assertEqual(len(data), expected["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected["sha256"])

    def test_raw_rescores_preserving_failure(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for label, scorer, expected in [
            ("plane", plane_score, True),
            ("coupling", coupling_score, False),
            ("response", response_score, True),
            ("gripper", gripper_score, False),
            ("gripper-compensated", gripper_score, False),
            ("self", self_score, True),
        ]:
            with self.subTest(label=label):
                raw = gzip.decompress((ROOT / f"{label}-record.json.gz").read_bytes())
                self.assertEqual(
                    hashlib.sha256(raw).hexdigest(), manifest[label]["raw_sha256"]
                )
                result = scorer(json.loads(raw))
                self.assertTrue(result["valid"])
                self.assertEqual(result["passed"], expected)
                self.assertEqual(
                    result, json.loads((ROOT / f"{label}-score.json").read_text())
                )
