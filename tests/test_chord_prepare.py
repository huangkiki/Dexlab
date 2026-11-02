"""Preparation contracts only; these checks do not execute a CHORD policy."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("chord_prepare", ROOT / "demos/chord/prepare.py")
chord = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chord)
MANIFEST = json.loads((ROOT / "demos/chord/tasks.json").read_text())
TASKS = {task["id"]: task for task in MANIFEST["tasks"]}


class ChordPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def plan(self, task="tissue-box", **kwargs):
        values = dict(task=TASKS[task], source=self.root / "source", data_root=self.root / "data",
                      python=self.root / "env/bin/python", attempt=self.root / "attempt",
                      operation="train", seed=24, num_envs=2, iterations=3)
        values.update(kwargs)
        return chord.command(**values)

    def test_tissue_recipe_disables_contact_terms_before_and_after_curriculum(self):
        plan = self.plan()
        args = plan["argv"]
        self.assertIn("env.rewards.force_closure.weight=5.0", args)
        for term in ("contact_wrench_support_reward", "unintended_contact_penalty", "missed_contact_penalty"):
            self.assertIn(f"env.rewards.{term}.weight=0.0", args)
            self.assertIn(f"env.curriculum.fixed_timestep_curriculum.params.rewards_{term}=0.0", args)
        self.assertEqual(plan["sample_budget"], 144)
        self.assertNotIn("--use_primitive_urdfs", args)
        self.assertIn(f"hydra.run.dir={self.root / 'attempt/hydra'}", args)
        self.assertFalse(plan["execution_admitted"])

    def test_synthetic_smoke_cannot_be_used_as_a_training_campaign(self):
        with self.assertRaises(ValueError):
            self.plan("synthbox-smoke")
        plan = self.plan("synthbox-smoke", num_envs=1, iterations=1)
        self.assertIn("--use_primitive_urdfs", plan["argv"])
        self.assertEqual(plan["sample_budget"], 8)
        self.assertEqual(sum(t["kind"] == "demonstration-task" for t in TASKS.values()), 3)

    def test_missing_or_conflicting_budgets_are_rejected(self):
        for change in ({"iterations": None}, {"iterations": 0}, {"num_envs": 0}, {"seed": -1},
                       {"checkpoint": self.root / "model.pt"}, {"steps": 100},
                       {"operation": "eval", "iterations": None, "steps": 100},
                       {"operation": "eval", "checkpoint": self.root / "model.pt", "steps": 100}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.plan(**change)

    def test_eval_exports_into_fresh_attempt_preserving_original_checkpoint(self):
        checkpoint = self.root / "original.pt"
        checkpoint.write_bytes(b"test bytes; never deserialized")
        plan = self.plan(operation="eval", iterations=None, steps=200, checkpoint=checkpoint)
        report = {"files": [{"role": "checkpoint", **chord.inspect_file(checkpoint)}]}
        attempt = self.root / "attempt"
        chord.write_attempt(attempt, plan, report, checkpoint)
        self.assertEqual((attempt / "checkpoint.pt").read_bytes(), checkpoint.read_bytes())
        self.assertEqual(plan["argv"][plan["argv"].index("--checkpoint") + 1], str(attempt / "checkpoint.pt"))
        self.assertEqual(plan["evaluation_contract"]["voc_scale"], 0.0)
        (attempt / "checkpoint.pt").write_bytes(b"export changed")
        with self.assertRaises(FileExistsError):
            chord.write_attempt(attempt, plan, report, checkpoint)
        self.assertEqual(checkpoint.read_bytes(), b"test bytes; never deserialized")

    def test_missing_pointer_error_page_and_truncated_parquet_are_distinct(self):
        path = self.root / "motion.parquet"
        self.assertEqual(chord.inspect_file(path)["status"], "missing")
        for data, status in ((chord.LFS + b"\noid sha256:abc", "lfs-pointer"),
                             (b"<html>login</html>", "html-response"),
                             (b"PAR", "invalid-parquet-envelope"), (b"", "empty"),
                             (b"PAR1dummyPAR1", "present")):
            path.write_bytes(data)
            with self.subTest(status=status):
                row = chord.inspect_file(path)
                self.assertEqual(row["status"], status)
                self.assertEqual(row["sha256"], chord.sha256(path))

    def test_urdf_follows_collision_and_visual_meshes(self):
        urdf = self.root / "box.urdf"
        urdf.write_text('<robot><link><visual><mesh filename="visual.stl"/></visual>'
                        '<collision><mesh filename="collision.stl"/></collision></link></robot>')
        (self.root / "visual.stl").write_bytes(b"mesh")
        rows = {Path(row["path"]).name: row["status"] for row in chord.inspect_urdf(urdf)}
        self.assertEqual(rows, {"box.urdf": "present", "visual.stl": "present", "collision.stl": "missing"})

    def test_wrong_revision_and_dirty_checkout_fail_source_check(self):
        for output in (("bad-head", "", ""), (MANIFEST["upstream"]["commit"], "robotic_grounding/train.py", ""),
                       (MANIFEST["upstream"]["commit"], "", "robotic_grounding/extra.py")):
            with patch.object(chord, "capture", side_effect=output):
                self.assertEqual(chord.source_check(self.root, MANIFEST["upstream"]["commit"])["status"], "mismatch")

    def test_runtime_wrapper_stdout_does_not_corrupt_metadata_probe(self):
        metadata = {"python": "3.11.13", "packages": {"isaaclab": "0.54.2", "isaacsim": None,
                        "rsl-rl-lib": "3.1.2", "torch": "2.7.0", "pyarrow": "17.0.0"},
                    "releases": {"isaaclab": {"version": "2.3.2"},
                                 "isaacsim": {"version": "5.1.0-rc.19+release.26219"}},
                    "robotic_grounding": str(self.root / "robotic_grounding/__init__.py")}
        output = '[INFO] Using python wrapper\nDEXLAB_CHORD_PROBE=' + json.dumps(metadata)
        with patch.object(chord, "capture", return_value=output):
            self.assertEqual(chord.runtime_check(self.root / "python")["status"], "metadata-present")

    def test_internal_extension_version_is_not_a_lab_release(self):
        for lab, sim in (("0.54.2", "5.1.0"), ("2.3.2", "5.0.0"), (None, "5.1.0")):
            metadata = {"packages": {"isaaclab": "0.54.2", "torch": "2.7.0",
                                     "rsl-rl-lib": "3.1.2", "pyarrow": "17.0.0"},
                        "releases": {"isaaclab": {"version": lab}, "isaacsim": {"version": sim}},
                        "robotic_grounding": "/source/robotic_grounding/__init__.py"}
            with self.subTest(lab=lab, sim=sim), patch.object(
                    chord, "capture", return_value="DEXLAB_CHORD_PROBE=" + json.dumps(metadata)):
                self.assertEqual(chord.runtime_check(self.root / "python")["status"], "missing-or-incompatible")

    def test_missing_inputs_are_reported_without_native_claims(self):
        with patch.object(chord, "source_check", return_value={"status": "pinned-clean"}), \
             patch.object(chord, "runtime_check", return_value={"status": "unavailable"}), \
             patch.object(chord, "capture", return_value="GPU-example, card, 24000, 22000, 580"):
            report = chord.preflight(MANIFEST, TASKS["box-grab"], self.root, self.root,
                                     self.root / "missing-python")
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(row["check"] == "motion" for row in report["blockers"]))
        self.assertFalse(report["execution_admitted"])
        self.assertEqual(report["training"], "not-run")

    def test_bundled_hash_mismatch_is_a_blocker_even_with_valid_file_magic(self):
        task = TASKS["tissue-box"]
        partition = self.root / "data" / task["partition"]
        partition.mkdir(parents=True)
        path = partition / "tampered.parquet"
        path.write_bytes(b"PAR1modifiedPAR1")
        key = str(chord.ASSETS / "human_motion_data" / path.relative_to(self.root / "data"))
        manifest = {**MANIFEST, "upstream_file_sha256": {key: "0" * 64}}
        with patch.object(chord, "source_check", return_value={"status": "pinned-clean"}), \
             patch.object(chord, "runtime_check", return_value={"status": "unavailable"}), \
             patch.object(chord, "capture", return_value="GPU-example, card, 24000, 22000, 580"):
            report = chord.preflight(manifest, task, self.root / "source", self.root / "data", self.root / "python")
        self.assertTrue(any(row.get("status") == "hash-mismatch" for row in report["blockers"]))

    def test_cli_never_uses_upstream_unbounded_defaults(self):
        result = subprocess.run([sys.executable, str(ROOT / "demos/chord/prepare.py"), "train",
                                 "--task", "tissue-box", "--source", str(self.root),
                                 "--python", sys.executable, "--attempt", str(self.root / "out")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--seed", result.stderr)
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
