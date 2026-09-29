"""Independent continuous spring dynamics and deliberately misleading drive records."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.physx_drive import BASE_POSITION, DT, DURATION, commands, run, score, verify


def reference():
    """RK4 reference for a mass with a saturated physical spring and damper."""
    rows, q, velocity = [], 0.0, 0.0
    h = DT / 20
    for step in range(round(DURATION / DT)):
        target, load = commands(step * DT)

        def acceleration(x, v):
            return (max(-2., min(2., 500.*(target-x) - 10.*v)) + load) / .1

        for _ in range(20):
            a1 = acceleration(q, velocity)
            v2 = velocity + h*a1/2
            a2 = acceleration(q + h*velocity/2, v2)
            v3 = velocity + h*a2/2
            a3 = acceleration(q + h*v2/2, v3)
            v4 = velocity + h*a3
            a4 = acceleration(q + h*v3, v4)
            q += h*(velocity + 2*v2 + 2*v3 + v4)/6
            velocity += h*(a1 + 2*a2 + 2*a3 + a4)/6
        rows.append((q, velocity, target, load))
    values = np.array(rows)
    count = len(rows)
    position = np.tile(BASE_POSITION, (count, 2, 1))
    position[:, 1, 0] += values[:, 0]
    velocity = np.zeros_like(position)
    velocity[:, 1, 0] = values[:, 1]
    return {"time": np.arange(1, count + 1)*DT, "q": values[:, 0], "dq": values[:, 1],
            "target": values[:, 2], "external_load": values[:, 3],
            "position": position, "velocity": velocity,
            "quaternion": np.tile([1., 0, 0, 0], (count, 2, 1))}


class PhysxDriveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = reference()

    def record(self):
        return {k: v.copy() for k, v in self.reference.items()}

    def test_continuous_physical_reference_passes(self):
        result = score(self.record())
        self.assertTrue(result["passed"], result)
        json.dumps(result, allow_nan=False)

    def test_static_position_with_reported_velocity_is_rejected(self):
        record = self.record()
        window = (record["time"] > .8) & (record["time"] <= 1.)
        record["dq"][window] = .0043
        record["velocity"][window, 1, 0] = .0043
        result = score(record)
        self.assertTrue(result["checks"]["body_joint_velocity_agree"])
        self.assertFalse(result["checks"]["loaded_stationary_velocity"])

    def test_targets_cannot_replace_loaded_actual_positions(self):
        record = self.record()
        record["q"] = record["target"].copy()
        record["position"][:, 1, 0] = BASE_POSITION[0] + record["q"]
        self.assertFalse(score(record)["checks"]["loaded_equilibrium"])

    def test_missing_steps_corrupt_clock_and_nonfinite_rejected(self):
        for kind in ("missing", "clock", "nan"):
            record = self.record()
            if kind == "missing":
                record["q"] = record["q"][:-1]
            elif kind == "clock":
                record["time"][10] = record["time"][9]
            else:
                record["dq"][10] = np.nan
            self.assertFalse(score(record)["passed"], kind)

    def test_wrong_force_history_and_limit_are_rejected(self):
        record = self.record()
        record["external_load"][600] = 0
        self.assertFalse(score(record)["checks"]["declared_commands_only"])
        pulse = (record["time"] > 1.01) & (record["time"] <= 1.035)
        record["dq"][pulse] = 0
        self.assertFalse(score(record)["checks"]["overload_matches_force_limit"])

    def test_moving_base_is_rejected(self):
        record = self.record()
        record["position"][:, 0, 2] += .001
        self.assertFalse(score(record)["checks"]["fixed_base_and_prismatic_pose"])

    def test_failed_worker_is_archived_and_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch.dict("os.environ", {"UNISIM_ISAACSIM_PYTHON": str(Path(directory)/"missing")}):
                self.assertFalse(run(output, True)["passed"])
            receipt = json.loads((output / "run.json").read_text())
            self.assertEqual(receipt["status"], "error")
            self.assertIn("IsaacSimDependencyError", receipt["error"])
            with (output / "states.npz").open("ab") as stream:
                stream.write(b"changed")
            self.assertFalse(verify(output)["checks"]["archive_hashes_match"])
            with self.assertRaises(FileExistsError):
                run(output, True)


if __name__ == "__main__":
    unittest.main()
