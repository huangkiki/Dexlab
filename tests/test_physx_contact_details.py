"""Contact accounting must detect dropped friction and incomplete evidence."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.physx_contact_details import CASE, run, score, verify


def sliding_record():
    time = np.arange(1, round(CASE.duration / CASE.timestep) + 1) * CASE.timestep
    initial = np.array([CASE.initial_speed, 0, 0])
    velocity = np.zeros((len(time), 3))
    velocity[:, 0] = np.maximum(
        CASE.initial_speed - CASE.friction * CASE.gravity * time, 0
    )
    delta = velocity - np.vstack((initial, velocity[:-1]))
    contacts = [
        dict(
            normal_body_ids=[2],
            normal_force=[[0, 0, CASE.mass * CASE.gravity]],
            friction_body_ids=[2],
            friction_force=[force.tolist()],
        )
        for force in CASE.mass * delta / CASE.timestep
    ]
    return dict(time=time, velocity=velocity, initial_velocity=initial), contacts


class ContactDetailsTests(unittest.TestCase):
    def test_actual_momentum_requires_tangential_force(self):
        states, contacts = sliding_record()
        self.assertTrue(score(states, contacts)["passed"])
        broken = copy.deepcopy(contacts)
        for row in broken:
            row["friction_force"] = [[0, 0, 0]]
        result = score(states, broken)
        self.assertFalse(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["friction_observed"])

    def test_dropped_or_duplicated_contact_impulse_fails(self):
        states, contacts = sliding_record()
        self.assertFalse(score(states, contacts[:-1])["passed"])
        contacts[1]["friction_force"] *= 2
        contacts[1]["friction_body_ids"] *= 2
        self.assertFalse(score(states, contacts)["checks"]["momentum_balance"])

    def test_invalid_time_and_forces_fail(self):
        states, contacts = sliding_record()
        states["time"][5] = states["time"][4]
        self.assertFalse(score(states, contacts)["passed"])
        states, contacts = sliding_record()
        contacts[1]["normal_force"] = [[0, 0, float("nan")]]
        self.assertFalse(score(states, contacts)["passed"])
        contacts[1]["normal_force"] = [0, 0, 1]
        self.assertFalse(score(states, contacts)["passed"])

    def test_runtime_failure_preserves_archive_and_rejects_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "failed"
            with patch.dict(
                "os.environ", {"UNISIM_ISAACSIM_PYTHON": str(Path(folder) / "absent")}
            ):
                result = run(output)
            self.assertFalse(result["passed"])
            self.assertEqual(
                json.loads((output / "run.json").read_text())["status"], "error"
            )
            self.assertTrue((output / "states.npz").is_file())
            self.assertFalse(verify(output)["passed"])
            with self.assertRaises(FileExistsError):
                run(output)


if __name__ == "__main__":
    unittest.main()
