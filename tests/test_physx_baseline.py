"""Analytical references and evidence rejection; no Isaac Sim dependency."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.physx_baseline import CASES, box_plane_clearance, create_scene, run, score, verify


def analytical_archive(case):
    time = np.arange(1, round(case.duration / case.timestep) + 1) * case.timestep
    pose = np.tile([0, 0, case.half_size, 1, 0, 0, 0], (len(time), 1))
    velocity = np.zeros((len(time), 6))
    force = np.tile([0, 0, case.mass * case.gravity], (len(time), 1))
    if case.initial_speed:
        acceleration = case.friction * case.gravity
        moving_time = np.minimum(time, case.initial_speed / acceleration) if acceleration else time
        pose[:, 0] = case.initial_speed * moving_time - 0.5 * acceleration * moving_time**2
        velocity[:, 0] = np.maximum(case.initial_speed - acceleration * time, 0)
        force[:, 0] = np.where(velocity[:, 0] > 0, -case.mass * acceleration, 0)
    return {"time": time, "pose": pose, "velocity": velocity, "force": force,
            "initial_pose": np.array([0, 0, case.half_size, 1, 0, 0, 0])}


class ContactScoringTests(unittest.TestCase):
    def test_analytical_rest_and_slide(self):
        for case in CASES.values():
            with self.subTest(case=case.name):
                self.assertTrue(score(case, analytical_archive(case))["passed"])

    def test_support_reference_uses_case_mass(self):
        case = replace(CASES["rest"], mass=0.4)
        archive = analytical_archive(case)
        self.assertTrue(score(case, archive)["passed"])
        archive["force"] *= 0.5
        self.assertFalse(score(case, archive)["checks"]["support_matches_weight"])

    def test_missing_repeated_and_nonfinite_samples_fail(self):
        case = CASES["rest"]
        archive = analytical_archive(case)
        archive["pose"] = archive["pose"][:-1]
        self.assertFalse(score(case, archive)["passed"])
        archive = analytical_archive(case)
        archive["time"][10] = archive["time"][9]
        self.assertFalse(score(case, archive)["passed"])
        archive = analytical_archive(case)
        archive["force"][10, 0] = np.nan
        self.assertFalse(score(case, archive)["passed"])

    def test_frozen_object_fails_frictionless_control(self):
        case = CASES["slide-frictionless"]
        archive = analytical_archive(case)
        archive["velocity"][:] = 0
        self.assertFalse(score(case, archive)["passed"])

    def test_missing_worker_retains_failed_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "missing-worker"
            with patch.dict("os.environ", {"UNISIM_ISAACSIM_PYTHON": str(Path(directory) / "absent-python")}):
                result = run(CASES["rest"], output, worker_timeout=10)
            self.assertFalse(result["passed"])
            self.assertFalse(result["checks"]["native_run_completed"])
            receipt = json.loads((output / "run.json").read_text())
            self.assertEqual(receipt["status"], "error")
            self.assertIn("IsaacSimDependencyError", receipt["error"])
            self.assertTrue((output / "states.npz").is_file())
            self.assertTrue(result["checks"]["exact_archive_hash"])
            with (output / "states.npz").open("ab") as stream:
                stream.write(b"altered")
            self.assertFalse(verify(output)["checks"]["exact_archive_hash"])
            with self.assertRaises(FileExistsError):
                run(CASES["rest"], output, worker_timeout=10)

    def test_rotated_box_plane_geometry(self):
        angle = np.pi / 4
        pose = np.array([[0, 0, 0.02, np.cos(angle / 2), 0, np.sin(angle / 2), 0]])
        self.assertAlmostEqual(box_plane_clearance(pose, 0.02)[0], 0.02 * (1 - np.sqrt(2)))
        pose[0, 3:] *= 2
        with self.assertRaises(ValueError):
            box_plane_clearance(pose, 0.02)

    def test_scene_compiles_through_unisim_portable_compiler(self):
        import mujoco
        from unisim.scene_compiler import compile_portable_scene

        with tempfile.TemporaryDirectory() as directory:
            scene = create_scene(CASES["rest"], Path(directory) / "scene")
            compiled = compile_portable_scene(scene, num_envs=1, sim_dt=0.001)
            try:
                self.assertEqual({entity.name for entity in compiled.layout.entities}, {"box", "table"})
                model = mujoco.MjModel.from_xml_path(compiled.model_file)
                self.assertEqual(model.nsensor, 1)
                self.assertEqual(model.nsensordata, 3)
                self.assertAlmostEqual(model.body("box/body").mass[0], CASES["rest"].mass)
            finally:
                compiled.close()


if __name__ == "__main__":
    unittest.main()
