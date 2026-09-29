"""Analytical fixture trajectories and deliberately incorrect contact behavior."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.physx_pinch import (
    CASES, DT, DURATION, GRAVITY, commands, box_overlap, rotation_matrices, run, score, verify,
)


def reference(case):
    times = np.arange(1, round(DURATION / DT)+1)*DT
    count = len(times)
    position = np.tile([[-.015, 0, .2], [.015, 0, .2], [0, 0, .2]], (count, 1, 1))
    velocity = np.zeros((count, 3, 3))
    normal = np.tile([[4., 0, 0], [-4., 0, 0]], (count, 1, 1))
    if case.should_hold:
        falling = np.maximum(times - 2.5, 0)
        position[:, 2, 2] -= 0.5*GRAVITY*falling**2
        velocity[:, 2, 2] = -GRAVITY*falling
    else:
        # Known initial friction-limited acceleration, followed by contact-free fall.
        falling = np.maximum(times - .5, 0)
        initial = np.minimum(falling, .1)
        free = np.maximum(falling - .1, 0)
        acceleration = GRAVITY - case.friction*8/case.mass
        position[:, 2, 2] -= .5*acceleration*initial**2 + acceleration*initial*free + .5*GRAVITY*free**2
        velocity[:, 2, 2] = -acceleration*initial-GRAVITY*free
        normal[times > .6] = 0
    separated = times > 2.5
    position[separated, 0, 0] = -.0352
    position[separated, 1, 0] = .0352
    normal[separated] = 0
    return {
        "time": times, "position": position,
        "quaternion": np.tile([1., 0, 0, 0], (count, 3, 1)),
        "velocity": velocity, "angular_velocity": np.zeros((count, 3, 3)),
        "q": (position[:, :2, 0]-[-.0152, .0152])*[1, -1], "dq": np.zeros((count, 2)),
        "external_force": np.array([commands(case, step*DT) for step in range(count)]),
        "contact_normal_force": normal,
    }


class PinchQualificationTests(unittest.TestCase):
    def test_expected_holding_and_dropping_both_pass(self):
        for case in CASES.values():
            with self.subTest(case=case.name):
                result = score(case, reference(case))
                self.assertTrue(result["passed"], result)
                json.dumps(result, allow_nan=False)

    def test_adhesion_after_release_is_rejected(self):
        case = CASES["hold"]
        archive = reference(case)
        archive["position"][:, 2, 2] = .2
        archive["velocity"][:, 2] = 0
        result = score(case, archive)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["fully_released"])
        self.assertFalse(result["checks"]["freefall_acceleration"])

    def test_overload_that_incorrectly_holds_fails(self):
        case = CASES["overload"]
        archive = reference(case)
        before_release = archive["time"] <= 2.5
        archive["position"][before_release, 2, 2] = .2
        archive["velocity"][before_release, 2] = 0
        self.assertFalse(score(case, archive)["checks"]["negative_control_drops"])

    def test_hidden_support_and_false_normal_force_fail(self):
        case = CASES["hold"]
        archive = reference(case)
        archive["external_force"][1000, 2, 2] = case.mass*GRAVITY
        self.assertFalse(score(case, archive)["checks"]["declared_external_forces_only"])
        archive["contact_normal_force"] *= 2
        self.assertFalse(score(case, archive)["checks"]["normal_load_matches_command"])
        archive["contact_normal_force"][1000] = 0
        self.assertFalse(score(case, archive)["checks"]["continuous_normal_support"])

    def test_missing_contact_and_corrupt_time_fail(self):
        case = CASES["hold"]
        archive = reference(case)
        del archive["contact_normal_force"]
        self.assertFalse(score(case, archive)["passed"])
        archive = reference(case)
        archive["time"][20] = archive["time"][19]
        self.assertFalse(score(case, archive)["passed"])
        archive["position"][20, 2, 0] = np.nan
        self.assertFalse(score(case, archive)["passed"])

    def test_obb_separation_overlap_and_rotation(self):
        identity = np.eye(3)[None]
        zero = np.zeros((1, 3))
        self.assertAlmostEqual(box_overlap(zero, identity, np.ones(3), [[1.5, 0, 0]], identity, np.ones(3))[0], .5)
        self.assertEqual(box_overlap(zero, identity, np.ones(3), [[3, 0, 0]], identity, np.ones(3))[0], 0)
        rotated = rotation_matrices(np.array([[np.cos(np.pi/8), 0, 0, np.sin(np.pi/8)]]))
        depth = box_overlap(zero, identity, np.ones(3), [[2, 0, 0]], rotated, np.ones(3))[0]
        self.assertAlmostEqual(depth, np.sqrt(2)-1)

    def test_failed_worker_archived_and_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"failed"
            with patch.dict("os.environ", {"UNISIM_ISAACSIM_PYTHON": str(Path(directory)/"missing")}):
                result = run(CASES["hold"], output)
            self.assertFalse(result["passed"])
            receipt = json.loads((output/"run.json").read_text())
            self.assertEqual(receipt["status"], "error")
            self.assertIn("IsaacSimDependencyError", receipt["error"])
            with (output/"states.npz").open("ab") as stream:
                stream.write(b"changed")
            self.assertFalse(verify(output)["checks"]["archive_hashes_match"])
            with self.assertRaises(FileExistsError):
                run(CASES["hold"], output)


if __name__ == "__main__":
    unittest.main()
