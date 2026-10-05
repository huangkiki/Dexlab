"""Native payload ownership and real-record qualification boundaries."""

import base64
import hashlib
import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dexlab.apple_admission import (apple_profile, record_native_file, rescore_record,
                                    loaded_mujoco_library, publication_status)


class AppleAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_new_release_classifies_original_batch_as_historical_without_mutation(self):
        frozen = {"runtime": {"installed": {"mujoco": "3.14.0"},
                              "native": {"mujoco": "3.14.0"}}}
        before = json.dumps(frozen, sort_keys=True)
        with patch("dexlab.apple_admission.refresh_inventory", return_value=[
                {"package": "mujoco", "version": "3.15.0"}]):
            status = publication_status(frozen)
        self.assertEqual(status["classification"], "historical_new_qualification_required")
        self.assertEqual(json.dumps(frozen, sort_keys=True), before)

    def test_process_mapping_not_install_location_selects_mujoco_library(self):
        library = self.root / "libmujoco.so.3.14.0"
        library.write_bytes(b"mapped")
        row = f"0000-1000 r-xp 0 00:00 1 {library}"
        with patch("pathlib.Path.read_text", return_value=row + "\n" + row):
            self.assertEqual(loaded_mujoco_library(), library)
        with patch("pathlib.Path.read_text", return_value=""):
            with self.assertRaisesRegex(ValueError, "actually mapped"):
                loaded_mujoco_library()

    def test_native_payload_must_be_owned_by_a_matching_wheel_record(self):
        native = self.root / "native.so"
        native.write_bytes(b"original")
        encoded = base64.urlsafe_b64encode(hashlib.sha256(b"original").digest()).rstrip(b"=").decode()
        entry = SimpleNamespace(hash=SimpleNamespace(mode="sha256", value=encoded))
        dist = SimpleNamespace(files=[entry], locate_file=lambda _: native)
        with patch("dexlab.apple_admission.distribution", return_value=dist):
            self.assertEqual(record_native_file("fixture", native), hashlib.sha256(b"original").hexdigest())
            native.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "differs"):
                record_native_file("fixture", native)
            outside = self.root / "outside.so"
            outside.write_bytes(b"original")
            with self.assertRaisesRegex(ValueError, "outside"):
                record_native_file("fixture", outside)

    def test_module_entry_profile_read_does_not_register_task_twice(self):
        result = subprocess.run([
            sys.executable, "-c",
            "import runpy; runpy.run_module('dexlab.tasks.apple_stem', run_name='entry_probe'); "
            "from dexlab.apple_admission import apple_profile; apple_profile('mujoco', {})",
        ], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_timestep_is_not_normalized_to_the_default(self):
        for timestep in (0, -0.001, float("nan"), float("inf")):
            with self.subTest(timestep=timestep), self.assertRaises(ValueError):
                apple_profile("mujoco", {"timestep": timestep})
        self.assertEqual(apple_profile("mujoco", {"timestep": None}),
                         apple_profile("mujoco", {"timestep": 0.0005}))

    def test_scene_variation_does_not_change_frozen_control_profile(self):
        baseline = apple_profile("mujoco", {})
        varied = apple_profile("mujoco", {"apple_mass": 0.22, "apple_yaw": 4.0})
        self.assertEqual(baseline, varied)
        self.assertNotEqual(baseline, apple_profile("mujoco", {"timestep": 0.001}))
        self.assertNotEqual(baseline, apple_profile("mujoco", {"mujoco_friction": 0.8}))
        with self.assertRaises(ValueError):
            apple_profile("mujoco", {"unrecognized": 1})

    def test_new_admission_requires_official_archives_before_native_work(self):
        from dexlab.apple_admission import admit_records
        with patch("dexlab.apple_admission.observe_runtime") as observe:
            with self.assertRaisesRegex(ValueError, "Official wheel directory"):
                admit_records({}, {}, {})
        observe.assert_not_called()

    def test_historical_demo_does_not_require_wheel_qualification(self):
        from dexlab.tasks.apple_stem import main
        from wuji_stem_grasp import parse_args
        args = parse_args(["--backend", "superdex", "--headless", "--output", str(self.root)])
        state = SimpleNamespace(terminated=[True], info={"summary": {"passed": True}})
        env = SimpleNamespace(init_state=lambda: state, close=lambda: None)
        with patch.dict("os.environ", {"DEXLAB_MUJOCO_PROFILE": "historical-3.11.0"}), \
             patch("wuji_stem_grasp.parse_args", return_value=args), \
             patch("dexlab.tasks.apple_stem.registry.make", return_value=env), \
             patch("dexlab.apple_admission.observe_runtime") as observe:
            main()
        observe.assert_not_called()
        self.assertFalse((self.root / "qualification-observation.json").exists())
        self.assertTrue((self.root / "runtime-timing.json").exists())

    def make_record(self):
        profile = apple_profile("superdex", {})
        observation = {"source_unchanged": True, "runtime_unchanged": True,
                       "source_sha256": {"task": "hash"}, "runtime": {"native": "identity"},
                       "backend": "superdex", "profile": profile}
        for name, value in {
            "qualification-observation.json": observation,
            "engine.json": {"backend": "superdex", "dt": 0.002},
            "unilab.json": {"backend": "superdex", "parameters": {}},
        }.items():
            (self.root / name).write_text(json.dumps(value))
        return profile, observation

    def test_saved_success_never_skips_independent_rescoring(self):
        profile, observation = self.make_record()
        with patch("dexlab.apple_admission.raw_record_hash", return_value="a" * 64), \
             patch("verify_sdf_grasp.verify_grasp", return_value={"passed": False}) as score:
            with self.assertRaisesRegex(ValueError, "qualification failed"):
                rescore_record(self.root, "superdex", expected_profile=profile,
                               expected_source=observation["source_sha256"], runtime=observation["runtime"])
        score.assert_called_once_with(self.root, expected_mass=0.2)

    def test_source_change_rejected_before_scoring_and_raw_mutation_after(self):
        profile, observation = self.make_record()
        with patch("dexlab.apple_admission.raw_record_hash", return_value="a" * 64), \
             patch("verify_sdf_grasp.verify_grasp") as score:
            with self.assertRaisesRegex(ValueError, "observation differs"):
                rescore_record(self.root, "superdex", expected_profile=profile,
                               expected_source={"task": "new"}, runtime=observation["runtime"])
            score.assert_not_called()
        with patch("dexlab.apple_admission.raw_record_hash", side_effect=["a" * 64, "b" * 64]), \
             patch("verify_sdf_grasp.verify_grasp", return_value={"passed": True, "checks": {"complete": True}}):
            with self.assertRaisesRegex(ValueError, "changed during"):
                rescore_record(self.root, "superdex", expected_profile=profile,
                               expected_source=observation["source_sha256"], runtime=observation["runtime"])
