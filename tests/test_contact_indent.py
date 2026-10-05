"""Contact task invariants and adversarial rescoring of an actual native trace."""

import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
from unilab.base import registry

from dexlab.contact_indent import IndentCase, score
from dexlab.contact_indent_run import run, verify
from dexlab.contact_plane import PlaneCase
from dexlab.tasks.contact_plane import INDENT_TASK, TASK


class IndentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "native"
        cls.case = IndentCase()
        cls.result = run(cls.case, "mujoco", cls.output)
        with np.load(cls.output / "states.npz", allow_pickle=False) as saved:
            cls.data = dict(saved)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def copy_data(self):
        return {k: v.copy() for k, v in self.data.items()}

    def test_native_loading_and_unloading_are_measured(self):
        self.assertTrue(self.result["passed"], self.result)
        self.assertTrue(verify(self.output)["passed"])
        self.assertGreater(self.result["metrics"]["maximum_normal_force_n"], 0)
        self.assertGreater(
            self.result["metrics"]["minimum_released_clearance_m"], 0.0005
        )

    def test_requested_geometry_cannot_pass_without_supported_native_evidence(self):
        path = self.output / "run.json"
        original = path.read_text()
        try:
            receipt = json.loads(original)
            receipt["record_native_geometry"] = True
            path.write_text(json.dumps(receipt))
            result = verify(self.output)
            self.assertFalse(result["checks"]["native_geometry_matches"])
            self.assertFalse(result["passed"])
        finally:
            path.write_text(original)

    def test_injected_adhesion_cannot_pass_even_with_balanced_force(self):
        data = self.copy_data()
        released = data["time"][1:] > 1.35
        data["contact_force"][released, 2] += 0.5
        data["external_force"][released, 2] -= 0.5
        result = score(self.case, data)
        self.assertTrue(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["fully_unloaded"])
        self.assertFalse(result["checks"]["declared_feedback_and_control_period"])

    def test_missing_contact_and_corrupt_clock_are_rejected(self):
        data = self.copy_data()
        data["contact_known"][23] = False
        self.assertFalse(score(self.case, data)["passed"])
        data = self.copy_data()
        data["time"][23] = data["time"][22]
        self.assertFalse(score(self.case, data)["checks"]["uniform_time_grid"])

    def test_fake_target_and_unreported_force_are_rejected(self):
        data = self.copy_data()
        data["target_height"][30] += 0.001
        self.assertFalse(score(self.case, data)["checks"]["declared_targets"])
        data = self.copy_data()
        data["external_force"][30, 2] += 1
        result = score(self.case, data)
        self.assertFalse(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["declared_feedback_and_control_period"])

    def test_artifact_mutation_is_detected(self):
        path = self.output / "native-status.json"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n")
            self.assertFalse(verify(self.output)["checks"]["artifact_hashes_match"])
        finally:
            path.write_bytes(original)

    def test_plausible_trace_does_not_override_wrong_native_parameters(self):
        path = self.output / "run.json"
        original = path.read_bytes()
        for field, wrong, check in (
            ("mass_readback", 0.4, "native_mass_matches"),
            ("inertia_readback", [1, 1, 1], "native_inertia_matches"),
            ("friction_readback", [[0.5, 0, 0]] * 2, "native_friction_matches"),
        ):
            with self.subTest(field=field):
                try:
                    receipt = json.loads(original)
                    receipt["native"][field] = wrong
                    path.write_text(json.dumps(receipt))
                    result = verify(self.output)
                    self.assertTrue(result["checks"]["momentum_balance"])
                    self.assertFalse(result["checks"][check])
                    self.assertFalse(result["passed"])
                finally:
                    path.write_bytes(original)

    def test_native_model_cannot_be_removed_from_archive_manifest(self):
        path = self.output / "run.json"
        original = path.read_bytes()
        try:
            receipt = json.loads(original)
            del receipt["artifact_sha256"]["model.xml"]
            path.write_text(json.dumps(receipt))
            self.assertFalse(verify(self.output)["checks"]["artifact_hashes_match"])
        finally:
            path.write_bytes(original)

    def test_rehashed_snapshot_must_match_the_pre_run_source_hash(self):
        from dexlab.physx_baseline import digest

        path = self.output / "run.json"
        source = self.output / "runner.py"
        original, original_source = path.read_bytes(), source.read_bytes()
        try:
            source.write_bytes(original_source + b"\n# post-run change\n")
            receipt = json.loads(original)
            receipt["artifact_sha256"]["runner.py"] = digest(source)
            path.write_text(json.dumps(receipt))
            result = verify(self.output)
            self.assertTrue(result["checks"]["artifact_hashes_match"])
            self.assertFalse(result["checks"]["archived_source_hashes_match"])
        finally:
            path.write_bytes(original)
            source.write_bytes(original_source)

    def test_controller_period_does_not_change_with_substeps(self):
        case = replace(self.case, timestep=0.00025)
        pose = np.array([0, 0, 0.02, 1, 0, 0, 0])
        velocity = np.zeros(6)
        previous = case.command(0, pose, velocity, np.zeros(3))
        for step in (1, 2, 3):
            np.testing.assert_array_equal(
                case.command(step, pose + 0.001, velocity, previous), previous
            )
        self.assertFalse(
            np.array_equal(case.command(4, pose + 0.001, velocity, previous), previous)
        )
        with self.assertRaises(ValueError):
            replace(case, controller_period=0.0001)


class ContactTaskTests(unittest.TestCase):
    def make_env(self, name, case, directory):
        return registry.make(
            name,
            sim_backend="mujoco",
            env_cfg_override={
                "case": asdict(case),
                "sim_dt": case.timestep,
                "ctrl_dt": case.timestep,
                "max_episode_seconds": case.duration,
                "output_dir": str(directory),
            },
        )

    def test_passive_task_cannot_apply_hidden_force_or_overwrite_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = PlaneCase(duration=0.002, settle=0.002)
            env = self.make_env(TASK, case, Path(tmp))
            try:
                state = env.init_state()
                self.assertFalse(state.info["contact_known"])
                self.assertEqual(state.obs["obs"].shape, (1, 14))
                with self.assertRaises(ValueError):
                    env.step([[0, 0, 1]])
                self.assertEqual(env.steps, 0)
                for _ in range(case.steps):
                    state = env.step(np.empty((1, 0)))
                self.assertTrue(state.terminated[0])
                with self.assertRaises(RuntimeError):
                    env.step(np.empty((1, 0)))
                with self.assertRaises(RuntimeError):
                    env.reset()
            finally:
                env.close()

    def test_indentation_rejects_lateral_or_excessive_force_before_stepping(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = PlaneCase(duration=0.002, settle=0.002, initial_speed=0, friction=0)
            env = self.make_env(INDENT_TASK, case, Path(tmp))
            try:
                env.init_state()
                for action in ([[1, 0, 0]], [[0, 0, 41]], [[0, 0, np.nan]], [0, 0, 1]):
                    with self.assertRaises(ValueError):
                        env.step(action)
                self.assertEqual(env.steps, 0)
                env.step([[0, 0, 1]])
                self.assertEqual(env.steps, 1)
            finally:
                env.close()
