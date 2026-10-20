"""Adversarial checks for RSS saved-state interpretation; no simulator imports."""

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np


PATH = Path(__file__).resolve().parents[1] / "demos/rss-wiping/score.py"
SPEC = importlib.util.spec_from_file_location("rss_wiping_score", PATH)
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)
GEOMETRY_SPEC = importlib.util.spec_from_file_location("rss_wiping_geometry", PATH.with_name("geometry.py"))
geometry = importlib.util.module_from_spec(GEOMETRY_SPEC)
GEOMETRY_SPEC.loader.exec_module(geometry)


class TestMaterialPatchMotion(unittest.TestCase):
    def test_modified_collision_geometry_is_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "geometry.npz"
            np.savez(path, vertices_0=np.zeros((3, 3)), indices_0=np.array([0, 1, 2]))
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(geometry.load_parts(path, expected)[0][0].shape, (3, 3))
            np.savez(path, vertices_0=np.ones((3, 3)), indices_0=np.array([0, 1, 2]))
            with self.assertRaisesRegex(ValueError, "Frozen collision geometry changed"):
                geometry.load_parts(path, expected)

    def test_rigid_motion_with_the_hand_is_not_slip(self):
        patch = np.array([[0.01, 0.02, 0.03], [-0.01, 0.01, 0.02]])
        indices = np.array([0, 1])
        quaternion = np.array([0, 0, np.sin(0.3), np.cos(0.3)])
        rotation = score.rotation_xyzw(quaternion)
        hand = np.array([0.4, -0.3, 0.2])
        world = patch @ rotation.T + hand
        _, slip, maximum = score.patch_motion(world, hand, quaternion, indices, patch)
        self.assertLess(slip, 1e-12)
        self.assertLess(maximum, 1e-12)

    def test_native_quaternion_roundoff_does_not_scale_material_motion(self):
        quaternion = np.array([0, 0, np.sin(0.3), np.cos(0.3)])
        rotation = score.rotation_xyzw(quaternion * 1.000003)
        np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-14)
        np.testing.assert_allclose(rotation, score.rotation_xyzw(quaternion), atol=1e-14)

    def test_opposing_deformation_cannot_hide_in_centroid_motion(self):
        patch = np.array([[0.01, 0, 0], [-0.01, 0, 0]])
        _, slip, maximum = score.patch_motion(
            patch * 2, np.zeros(3), [0, 0, 0, 1], np.array([0, 1]), patch
        )
        self.assertEqual(slip, 0)
        self.assertAlmostEqual(maximum, 0.01)

    def test_rotation_of_object_with_fixed_hand_is_detected(self):
        patch = np.array([[0.02, 0, 0], [0.02, 0.01, 0]])
        rotation = score.rotation_xyzw([0, 0, np.sin(0.2), np.cos(0.2)])
        _, slip, maximum = score.patch_motion(
            patch @ rotation.T, np.zeros(3), [0, 0, 0, 1], np.array([0, 1]), patch
        )
        self.assertGreater(slip, 0.005)
        self.assertGreater(maximum, 0.005)

    def test_one_hidden_pin_invalidates_an_otherwise_successful_ablation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "states").mkdir()
            row = {
                "step": 0, "sim_time_s": 0, "active_pins": 1,
                "sponge_centroid_m": [0, 0, 0],
                "phase": "done", "cleaned_fraction": 1,
                "bar_force_n": 4, "bar_peak_pressure_pa": 20000,
                "arm_positions_m": {"right": [0, 0, 0], "left": [0, 0, 0]},
            }
            (root / "observations.jsonl").write_text(json.dumps(row) + "\n")
            summary = {
                "recorded_steps": 1, "mode": "no-latch", "video_frames": 0,
                "phase": "done", "error": None, "finite": True,
                "final_cleaned_fraction": 1, "peak_bar_force_n": 4,
                "peak_pressure_pa": 20000, "sponge_return_xy_error_m": 0,
                "sponge_return_min_z_error_m": 0, "home_errors_m": {"right": 0, "left": 0},
            }
            (root / "summary.json").write_text(json.dumps(summary))
            (root / "manifest.json").write_text(json.dumps({
                "schema_version": 2, "control_hz": 60, "video_fps": 10,
                "stripe_cleared_below": 0.1,
                "arm_home_positions_m": {"right": [0, 0, 0], "left": [0, 0, 0]},
            }))
            np.save(root / "video-times.npy", np.array([]))
            np.save(root / "settled-particles.npy", np.zeros((2, 3)))
            np.savez(
                root / "states/0000.npz", step=[0], particles=np.zeros((1, 2, 3)),
                body_q=np.zeros((1, 1, 7)), joint_q=np.zeros((1, 1)), stripe_ink=[[0]],
            )
            result = score.score(root)
            self.assertTrue(result["task_pass"])
            self.assertFalse(result["record_integrity_pass"])
            self.assertIn("unexpected_pin", result["record_failures"])
            # A successful summary cannot conceal a dirty raw stripe.
            np.savez(
                root / "states/0000.npz", step=[0], particles=np.zeros((1, 2, 3)),
                body_q=np.zeros((1, 1, 7)), joint_q=np.zeros((1, 1)), stripe_ink=[[1]],
            )
            result = score.score(root)
            self.assertFalse(result["task_pass"])
            self.assertIn("summary_final_cleaned_fraction", result["record_failures"])


if __name__ == "__main__":
    unittest.main()
