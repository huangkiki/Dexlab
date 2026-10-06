"""Scoring must reject missing coverage and signed-force corruption."""

import copy
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from dexlab.newton_contact_score import score


def fixture():
    record = {
        "completed": True,
        "dt_s": 0.001,
        "steps": 1000,
        "mass_kg": 0.1,
        "radius_m": 0.05,
        "initial_height_m": 0.1,
        "gravity_m_s2": -9.81,
        "device": "cpu",
        "precision": "float32",
        "versions": {"newton": "1.6.1", "warp-lang": "1.18.0"},
        "solver": {
            "name": "SolverXPBD",
            "iterations": 4,
            "rigid_contact_relaxation": 0.8,
            "rigid_contact_con_weighting": True,
            "enable_restitution": False,
        },
        "episodes": [],
    }
    for case in ("support", "support-repeat", "collision-disabled"):
        negative = case == "collision-disabled"
        rows = []
        for n in range(1, 1001):
            z = 0.1 - 9.81 * 0.001**2 * n * (n + 1) / 2 if negative else 0.05
            v = -9.81 * 0.001 * n if negative else 0.0
            rows.append(
                {
                    "step": n,
                    "q": [0.0, 0.0, z, 0.0, 0.0, 0.0, 1.0],
                    "qd": [0.0, 0.0, v, 0.0, 0.0, 0.0],
                    "shape0": [] if negative else [0],
                    "shape1": [] if negative else [1],
                    "force": [] if negative else [[0.0, 0.0, -0.981, 0.0, 0.0, 0.0]],
                }
            )
        record["episodes"].append(
            {
                "case": case,
                "rows": rows,
                "body_index": 0,
                "shape_body": [-1, 0],
                "shape_type": [1, 3],
                "shape_scale": [[0.0, 0.0, 0.0], [0.05, 0.0, 0.0]],
                "shape_transform": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]] * 2,
                "shape_mu": [0.0, 0.0],
                "shape_margin": [0.0, 0.0],
                "observed_mass_kg": 0.1,
                "initial_q": [0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 1.0],
                "initial_qd": [0.0] * 6,
            }
        )
    return record


class ScoreTests(unittest.TestCase):
    def test_support_and_freefall_negative_are_distinct(self):
        result = score(fixture())
        self.assertTrue(result["passed"])
        self.assertFalse(result["cases"]["collision-disabled"]["support_passed"])

    def test_non_object_record_fails_closed(self):
        self.assertFalse(score([])["passed"])
        self.assertFalse(score(None)["passed"])

    def test_signed_force_not_absolute(self):
        record = fixture()
        for episode in record["episodes"][:2]:
            for row in episode["rows"]:
                row["force"][0][2] *= -1
        self.assertFalse(score(record)["passed"])

    def test_bad_records_fail_closed(self):
        original = fixture()
        mutations = [
            lambda r: r["episodes"][0]["rows"].pop(),
            lambda r: r["episodes"][0]["rows"][0].update(q=[float("nan")] * 7),
            lambda r: r["episodes"][0]["rows"][900].update(force=[]),
            lambda r: r["episodes"][0]["rows"][0].update(shape0=[-1]),
            lambda r: r.update(completed=False),
            lambda r: r.update(steps=999),
            lambda r: r["episodes"][0].update(observed_mass_kg=float("nan")),
            lambda r: r["episodes"][0].update(observed_mass_kg=float("inf")),
            lambda r: r["episodes"][0].update(body_index=False),
            lambda r: r["episodes"][0].update(shape_type=[1, 7]),
            lambda r: r["episodes"][0].update(shape_margin=[0.01, 0.0]),
            lambda r: r["episodes"].pop(),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                record = copy.deepcopy(original)
                mutate(record)
                self.assertFalse(score(record)["passed"])

    def test_negative_control_cannot_be_a_second_support(self):
        record = fixture()
        record["episodes"][2]["rows"] = copy.deepcopy(record["episodes"][0]["rows"])
        self.assertFalse(score(record)["negative_control_verified"])

    def test_repeat_change_detected(self):
        record = fixture()
        record["episodes"][1]["rows"][50]["q"][0] = 0.0001
        self.assertFalse(score(record)["repeat_identical"])


class PackagedEvidenceTests(unittest.TestCase):
    def test_raw_hash_and_independent_score(self):
        root = Path(__file__).resolve().parents[1]
        evidence = root / "docs/evidence/newton-xpbd"
        packed = (evidence / "record.json.gz").read_bytes()
        raw = gzip.decompress(packed)
        manifest = json.loads((evidence / "manifest.json").read_text())
        self.assertEqual(
            hashlib.sha256(packed).hexdigest(), manifest["compressed_sha256"]
        )
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest["record_sha256"])
        record = json.loads(raw)
        self.assertEqual(
            score(record), json.loads((evidence / "score.json").read_text())
        )
        self.assertTrue(score(record)["passed"])
        runner = root / "src/dexlab/newton_contact_probe.py"
        self.assertEqual(
            hashlib.sha256(runner.read_bytes()).hexdigest(), record["source_sha256"]
        )

    def test_missing_optional_runtime_records_failure(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "missing-runtime"
            result = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-m",
                    "dexlab.newton_contact_probe",
                    str(output),
                ],
                env={**os.environ, "PYTHONPATH": str(root / "src")},
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertNotEqual(result.returncode, 0)
            record = json.loads((output / "record.json").read_text())
            self.assertFalse(record["completed"])
            self.assertIn("ModuleNotFoundError", record["error"])
            self.assertFalse(score(record)["passed"])
