"""A retained apple must not hide missing forces, fruit support or bad records."""

import copy
import unittest

import numpy as np
import trimesh

from dexlab.physx_apple import scale_closure
from dexlab.physx_apple_score import (
    BENCHMARK_INTERFACE_WARNING,
    PADS,
    physics_diagnostics,
    score,
)


def static_record():
    dt, count = 0.01, 1400
    names = [
        "apple/apple",
        "robot/r_wrist",
        "robot/robot_world",
        "table/table",
        *PADS,
        "robot/r_thumb_nail",
    ]
    states = {
        "time": np.arange(1, count + 1) * dt,
        "q": np.zeros((count, 54)),
        "dq": np.zeros((count, 54)),
        "position": np.zeros((count, len(names), 3)),
        "quaternion": np.zeros((count, len(names), 4)),
        "velocity": np.zeros((count, len(names), 3)),
        "angular_velocity": np.zeros((count, len(names), 3)),
    }
    states["quaternion"][:, :, 0] = 1
    states["position"][:, 0, 2] = 0.5
    states["position"][:, 1, 2] = 0.6
    steps = np.repeat(np.arange(count), 2)
    points = np.tile([[0.005, 0, 0.55], [-0.005, 0, 0.55]], (count, 1))
    contacts = {}
    for kind, forces in (
        ("normal", [[1, 0, 0], [-1, 0, 0]]),
        ("friction", [[0, 0, 0.981], [0, 0, 0.981]]),
    ):
        contacts[kind + "_step"] = steps.copy()
        contacts[kind + "_body_ids"] = np.tile([4, 5], count)
        contacts[kind + "_point"] = points.copy()
        contacts[kind + "_force"] = np.tile(forces, (count, 1)).astype(float)
    contacts["separation"] = np.full(2 * count, -0.0001)
    receipt = {
        "dt": dt,
        "body_names": names,
        "contact_polls": count,
        "initial_apple_com_velocity": [0, 0, 0],
        "contact_details": {"body_names": {str(i): n for i, n in enumerate(names)}},
    }
    native = {"apple": {"body_mass": [[0.2]], "body_com": [[[0, 0, 0]]]}}
    fruit = trimesh.creation.box([0.04, 0.04, 0.04])
    stem = trimesh.creation.box([0.01, 0.01, 0.02])
    stem.apply_translation([0, 0, 0.05])
    table = trimesh.creation.box([0.2, 0.2, 0.2])
    return receipt, states, contacts, native, fruit, stem, table


class PhysxAppleTests(unittest.TestCase):
    def test_startup_dependency_warning_does_not_hide_solver_diagnostics(self):
        log = (
            "timestamp "
            + BENCHMARK_INTERFACE_WARNING
            + "\n[Warning] [omni.physx.plugin] solver failure"
        )
        startup, physics = physics_diagnostics(log)
        self.assertEqual(len(startup), 1)
        self.assertEqual(physics, ["[Warning] [omni.physx.plugin] solver failure"])
        startup, physics = physics_diagnostics(
            BENCHMARK_INTERFACE_WARNING.replace("[Warning]", "[Error]")
        )
        self.assertFalse(startup)
        self.assertEqual(len(physics), 1)

    def test_balanced_stem_record_is_not_full_geometry_qualification(self):
        result = score(*static_record())
        self.assertTrue(result["native_hold_passed"])
        self.assertTrue(result["strict_stem_observations_passed"])
        self.assertFalse(result["qualified"])

    def test_fruit_assisted_hold_is_separate_from_stem_support(self):
        record = static_record()
        for kind in ("normal", "friction"):
            record[2][kind + "_point"][:, 2] = 0.52
        result = score(*record)
        self.assertTrue(result["native_hold_passed"])
        self.assertFalse(result["checks"]["stem_support_only"])
        self.assertFalse(result["strict_stem_observations_passed"])

    def test_nail_support_cannot_pass_as_two_pads(self):
        record = static_record()
        for kind in ("normal", "friction"):
            owners = record[2][kind + "_body_ids"]
            owners[owners == 4] = 6
        result = score(*record)
        self.assertTrue(result["native_hold_passed"])
        self.assertFalse(result["checks"]["only_two_pads_support"])
        self.assertFalse(result["strict_stem_observations_passed"])

    def test_missing_force_and_missing_polls_fail(self):
        record = static_record()
        record[2]["friction_force"][100] = 0
        self.assertFalse(score(*record)["checks"]["momentum_balance"])
        record = static_record()
        del record[0]["contact_polls"]
        self.assertFalse(score(*record)["native_hold_passed"])

    def test_missing_or_duplicate_steps_and_invalid_quaternions_fail(self):
        for mutation in ("missing", "duplicate", "rotation"):
            record = static_record()
            if mutation == "missing":
                record[1]["time"] = record[1]["time"][:-1]
            elif mutation == "duplicate":
                record[1]["time"][2] = record[1]["time"][1]
            else:
                record[1]["quaternion"][2, 0] = 0
            self.assertFalse(score(*record)["native_hold_passed"])

    def test_invalid_contact_index_or_value_fails(self):
        for field, value in (
            ("normal_step", 1400),
            ("normal_body_ids", 999),
            ("friction_force", float("nan")),
        ):
            record = static_record()
            record[2][field][0] = value
            self.assertFalse(score(*record)["checks"]["valid_contacts"])

    def test_drift_and_native_penetration_fail(self):
        record = static_record()
        record[1]["position"][-2, 0, 0] += 0.003
        self.assertFalse(score(*record)["checks"]["retained"])
        record = static_record()
        record[2]["separation"][0] = -0.0011
        self.assertFalse(score(*record)["checks"]["bounded_native_hand_penetration"])

    def test_closure_uses_path_prefix_and_does_not_mutate_prior(self):
        path = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 1.0]])
        original = copy.deepcopy(path)
        np.testing.assert_allclose(
            scale_closure(path, 0.5), [[0, 1], [0.5, 1.5], [1, 2]]
        )
        np.testing.assert_array_equal(path, original)
        np.testing.assert_array_equal(scale_closure(path, 1), path)
        for value in (0, -1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                scale_closure(path, value)


if __name__ == "__main__":
    unittest.main()
