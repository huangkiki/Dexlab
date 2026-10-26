"""Offline, engine-free evidence checks with small synthetic saved trajectories."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np


ENTRY = Path(__file__).resolve().parents[1] / "demos/rss-wiping/rescore_bundle.py"
SPEC = importlib.util.spec_from_file_location("rss_bundle", ENTRY)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class TestBundleIntegrity(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "bundle"
        self.root.mkdir()
        self.cases = [{"id": "controlled-original-01", "mode": "original"},
                      {"id": "controlled-no-latch-01", "mode": "no-latch"}]
        for case in self.cases:
            self.write_record(case)
        scorer = self.root / "source/scoring/score.py"
        scorer.parent.mkdir(parents=True)
        shutil.copyfile(ENTRY.with_name("score.py"), scorer)
        self.manifest = {"version": 1, "files": [], "archives": [{"files": {}}], "provenance": {},
                         "evidence": {"bundle_id": "test-fixture", "rss_commit": "a" * 40, "cases": self.cases,
                                      "compiled_model_sha256": self.model_digest}}
        self.refresh_manifest()
        self.manifest_path = self.base / "trusted-manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest))

    def refresh_manifest(self):
        files, provenance = {}, {}
        for path in self.root.rglob("*"):
            if path.is_file():
                name = path.relative_to(self.root).as_posix()
                files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                provenance[name] = {"bytes": path.stat().st_size, "license": "test fixture",
                                    "source": "synthetic", "purpose": "regression", "attempt": None}
        self.manifest["archives"][0]["files"] = files
        self.manifest["provenance"] = provenance

    def write_record(self, case):
        root = self.root / "runs" / case["id"]
        (root / "states").mkdir(parents=True)
        shift = 0.020 if case["mode"] == "no-latch" else 0.0
        points = np.array([[0.0, 0, 0], [0.0, 0.01, 0]])
        particles = np.stack([points, points + [shift, 0, 0]])
        ink = np.array([[1.0, 1.0], [0.0, 1.0 if shift else 0.0]])
        rows = []
        for step in range(2):
            rows.append({"step": step, "sim_time_s": step / 60, "active_pins": int(not shift),
                         "sponge_centroid_m": particles[step].mean(axis=0).tolist(),
                         "phase": "done" if step else "steady", "cleaned_fraction": float(np.mean(ink[step] <= 0.1)),
                         "bar_force_n": 4, "bar_peak_pressure_pa": 20000,
                         "arm_positions_m": {"right": [0, 0, 0], "left": [0, 0, 0]},
                         "hand_position_m": [0, 0, 0], "hand_quaternion_xyzw": [0, 0, 0, 1],
                         "grip_command": 1, "patch_centroid_slip_m": step * shift,
                         "patch_max_node_displacement_m": step * shift})
        (root / "observations.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        summary = {"recorded_steps": 2, "mode": case["mode"], "video_frames": 2, "ready_step": 0,
                   "phase": "done", "error": None, "finite": True,
                   "final_cleaned_fraction": rows[-1]["cleaned_fraction"], "peak_bar_force_n": 4,
                   "peak_pressure_pa": 20000, "sponge_return_xy_error_m": shift,
                   "sponge_return_min_z_error_m": 0, "home_errors_m": {"right": 0, "left": 0},
                   "max_hold_patch_centroid_slip_m": shift, "max_hold_patch_node_displacement_m": shift}
        (root / "summary.json").write_text(json.dumps(summary))
        # Different ZIP compression must not become a different physical model.
        save_model = np.savez_compressed if shift else np.savez
        save_model(root / "compiled-model.npz", geometry=np.zeros((3, 3)))
        self.model_digest = bundle.compiled_model_digest(root / "compiled-model.npz")
        (root / "manifest.json").write_text(json.dumps({
            "schema_version": 2, "mode": case["mode"], "rss_commit": "a" * 40,
            "compiled_model": {"sha256": self.model_digest},
            "control_hz": 60, "video_fps": 60, "stripe_cleared_below": 0.1,
            "arm_home_positions_m": {"right": [0, 0, 0], "left": [0, 0, 0]}}))
        np.save(root / "video-times.npy", np.array([0, 1 / 60]))
        np.save(root / "settled-particles.npy", points)
        np.save(root / "initial-particles.npy", points)
        np.save(root / "tracked-patch.npy", np.array([0, 1]))
        np.savez(root / "states/0000.npz", step=[0, 1], particles=particles,
                 body_q=np.zeros((2, 1, 7)), joint_q=np.zeros((2, 1)), stripe_ink=ink)

    def test_valid_raw_pair_reconstructs_curves_and_retains_task_failure(self):
        model_files = [self.root / "runs" / case["id"] / "compiled-model.npz" for case in self.cases]
        self.assertNotEqual(bundle.sha256(model_files[0]), bundle.sha256(model_files[1]))
        self.assertEqual(bundle.compiled_model_digest(model_files[0]), bundle.compiled_model_digest(model_files[1]))
        before = copy.deepcopy(self.manifest["archives"][0]["files"])
        output = self.base / "result"
        with patch.object(bundle, "plot_curves"):
            result = bundle.rescore(self.root, self.manifest_path, output)
        self.assertTrue(result["records"][self.cases[0]["id"]]["task_pass"])
        self.assertFalse(result["records"][self.cases[1]["id"]]["task_pass"])
        self.assertAlmostEqual(result["records"][self.cases[1]["id"]]["max_hold_patch_centroid_slip_m"], 0.02)
        self.assertIn("0.5,0.02", (output / f"{self.cases[1]['id']}.csv").read_text())
        self.refresh_manifest()
        self.assertEqual(before, self.manifest["archives"][0]["files"])

    def test_missing_wrong_hash_and_cross_attempt_records_are_rejected(self):
        victim = self.root / "runs" / self.cases[1]["id"] / "states/0000.npz"
        source = self.root / "runs" / self.cases[0]["id"] / "states/0000.npz"
        original = victim.read_bytes()
        for replacement in (None, b"wrong bytes", source.read_bytes()):
            with self.subTest(replacement=None if replacement is None else len(replacement)):
                if replacement is None:
                    victim.unlink()
                else:
                    victim.write_bytes(replacement)
                with self.assertRaises(ValueError):
                    bundle.verify_bundle(self.root, self.manifest)
                victim.write_bytes(original)

    def test_summary_only_manifest_and_record_identity_mixing_are_rejected(self):
        victim = self.root / "runs" / self.cases[1]["id"] / "manifest.json"
        recorded = json.loads(victim.read_text())
        recorded["rss_commit"] = "b" * 40
        victim.write_text(json.dumps(recorded))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "upstream identity"):
            bundle.verify_bundle(self.root, self.manifest)
        for path in self.root.rglob("*.npz"):
            path.unlink()
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "Missing raw input"):
            bundle.verify_bundle(self.root, self.manifest)

    def test_extra_file_and_symlink_are_rejected(self):
        extra = self.root / "extra"
        extra.write_text("unlisted")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            bundle.verify_bundle(self.root, self.manifest)
        extra.unlink()
        extra.symlink_to(self.manifest_path)
        with self.assertRaisesRegex(ValueError, "Non-regular"):
            bundle.verify_bundle(self.root, self.manifest)

    def test_output_never_overwrites_inputs_or_prior_results(self):
        for output in (self.root / "derived", self.base):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "new output"):
                bundle.rescore(self.root, self.manifest_path, output)
        dangling = self.base / "dangling"
        dangling.symlink_to(self.base / "elsewhere")
        with self.assertRaisesRegex(ValueError, "symlink"):
            bundle.rescore(self.root, self.manifest_path, dangling)

    def test_correct_hash_does_not_turn_inconsistent_raw_data_into_success(self):
        victim = self.root / "runs" / self.cases[0]["id"] / "states/0000.npz"
        with np.load(victim) as chunk:
            arrays = {name: chunk[name].copy() for name in chunk.files}
        arrays["stripe_ink"][-1] = 1
        np.savez(victim, **arrays)
        self.refresh_manifest()
        self.manifest_path.write_text(json.dumps(self.manifest))
        output = self.base / "invalid-result"
        with self.assertRaisesRegex(ValueError, "Invalid saved record"):
            bundle.rescore(self.root, self.manifest_path, output)
        self.assertFalse(output.exists())

    def test_changed_compiled_physics_cannot_join_the_same_cohort(self):
        victim = self.root / "runs" / self.cases[1]["id"] / "compiled-model.npz"
        np.savez(victim, geometry=np.ones((3, 3)))
        self.refresh_manifest()
        with self.assertRaisesRegex(ValueError, "model arrays differ"):
            bundle.verify_bundle(self.root, self.manifest)


if __name__ == "__main__":
    unittest.main()
