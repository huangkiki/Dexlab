"""Regression tests for false-positive physical acceptance, using synthetic logs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh

SOURCE = Path(__file__).resolve().parents[1] / "demos/apple-stem-grasp/src"
sys.path.insert(0, str(SOURCE))
from verify_sdf_grasp import APPLE, verify_grasp


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        dt = 0.01
        times = np.arange(1400) * dt
        count = len(times)
        pose = np.tile([0, 0, 0.5, 0, 0, 0, 1.0], (count, 1))
        force = np.tile([0, 0, 1.962], (count, 1))
        zero = np.zeros((count, 3))
        self.log = {
            "time": times,
            "apple_pose": pose.copy(),
            "wrist_pose": pose.copy(),
            "base_pose": pose.copy(),
            "clearance": np.full(count, 0.12),
            "velocity_before": zero.copy(),
            "velocity": zero.copy(),
            "total": force,
            "hand": force.copy(),
            "table": zero.copy(),
            "other": zero.copy(),
            "penetration": np.full(count, 0.0001),
            "warnings": np.zeros(count),
        }
        stem = trimesh.load_mesh(APPLE / "stem-collision.obj", process=False)
        point = stem.vertices[np.argmax(stem.vertices[:, 2])]
        self.contacts = np.array(
            [
                [t, i, *point, -0.0001, 5, x, 0, 0.981]
                for t in times
                if 11 <= t < 14
                for i, x in ((0, 5), (1, -5))
            ]
        )
        engine = {
            "backend": "superdex",
            "fp64": True,
            "dt": dt,
            "mass_kg": 0.2,
            "apple_dynamic": True,
            "completed": True,
            "body_names": ["r_thumb_pad", "r_index_finger_pad"],
            "grasp_collider_types": {
                n: "SDF" for n in ("apple", "r_thumb_pad", "r_index_finger_pad")
            },
        }
        (self.directory / "engine.json").write_text(json.dumps(engine))

    def verify(self):
        np.savez(self.directory / "sdf-dynamics.npz", **self.log)
        np.savez(self.directory / "sdf-contacts.npz", contacts=self.contacts)
        return verify_grasp(self.directory)

    def test_consistent_fixture(self):
        self.assertTrue(self.verify()["passed"])

    def test_one_missing_finger_contact_fails(self):
        self.contacts = self.contacts[1:]
        result = self.verify()
        self.assertFalse(result["checks"]["two_sdf_pads_throughout_hold"])
        self.assertFalse(result["checks"]["contact_ledger_matches_hand_force"])

    def test_missing_step_fails(self):
        self.log = {k: np.delete(v, 1200, axis=0) for k, v in self.log.items()}
        result = self.verify()
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["full_hold"])

    def test_fruit_support_fails(self):
        fruit = trimesh.load_mesh(APPLE / "apple-collision.obj", process=False)
        self.contacts[:, 2:5] = fruit.vertices[np.argmin(fruit.vertices[:, 2])]
        self.assertFalse(self.verify()["checks"]["no_fruit_support_during_hold"])

    def test_sliding_hold_fails(self):
        self.log["apple_pose"][1200:, 0] += 0.005
        self.assertFalse(self.verify()["checks"]["retained"])

    def test_contact_between_steps_fails(self):
        self.contacts[10, 0] += 0.001
        self.assertFalse(self.verify()["checks"]["contact_step_times_valid"])

    def test_incidental_approach_contact_allowed(self):
        fruit = trimesh.load_mesh(APPLE / "apple-collision.obj", process=False)
        row = [5, 0, *fruit.vertices[0], -0.0001, 1, 1, 0, 0]
        self.contacts = np.vstack([row, self.contacts])
        self.assertTrue(self.verify()["passed"])


if __name__ == "__main__":
    unittest.main()
