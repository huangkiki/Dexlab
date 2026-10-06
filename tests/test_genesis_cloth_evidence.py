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
from dexlab.cloth_pad_sweep import audit as sweep_audit
from dexlab.cloth_response_history import score as history_score
from dexlab.cloth_fold import score as fold_score

ROOT = Path(__file__).resolve().parents[1] / "docs/evidence/genesis-cloth"


class EvidenceTests(unittest.TestCase):
    def test_offset_metadata_requires_actual_geometry(self):
        record = json.loads(gzip.decompress((ROOT / "gripper-record.json.gz").read_bytes()))
        record["cloth_y_offset_m"] = 0.0
        self.assertTrue(gripper_score(record)["valid"])
        record["cloth_y_offset_m"] = 0.003
        self.assertFalse(gripper_score(record)["valid"])
        for scene in record["scenes"]:
            for episode in scene["episodes"]:
                for point in episode["rows"][0]["pos"]:
                    point[1] += 0.003
        self.assertTrue(gripper_score(record)["valid"])
        record["cloth_y_offset_m"] = float("nan")
        self.assertFalse(gripper_score(record)["valid"])

    def test_linear_sweep_rescores_existing_raw(self):
        report = json.loads((ROOT / "pad-linear-sweep.json").read_text())
        for name, expected in report["batches"].items():
            raw = gzip.decompress((ROOT / f"{name}-record.json.gz").read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["raw_sha256"])
            record = json.loads(raw)
            actual = [
                {
                    "coupled": scene["coupled"],
                    "repeat": episode["repeat"],
                    **sweep_audit(episode["rows"]),
                }
                for scene in record["scenes"]
                for episode in scene["episodes"]
            ]
            self.assertEqual(actual, expected["cases"])

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
            ("history", history_score, True),
            ("heldout-minus3mm", gripper_score, False),
            ("heldout-plus3mm", gripper_score, False),
            ("fold", fold_score, True),
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
