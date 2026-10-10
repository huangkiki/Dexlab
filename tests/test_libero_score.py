"""Independent malformed-evidence and terminal-state regression checks."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from dexlab.libero_score import score
from dexlab.libero_workflow import TASK, file_hash


class LiberoScoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        params = dict(
            options=dict(timestep=0.002),
            model_timestep=0.002,
            control_timestep=0.002,
            object_body_id=0,
            gravity=[0, 0, -9.81],
            arrays=dict(
                body_mass=[0.1],
                body_ipos=[[0, 0, 0]],
                geom_solref=[[0.004, 1]],
                pair_solref=[],
            ),
        )
        for name in ("before", "effective", "after"):
            (self.root / f"parameters-{name}.json").write_text(json.dumps(params))
        self.physics = np.zeros((2, 32))
        self.physics[:, 0] = [0, 0.002]
        self.physics[:, 1] = [0.002, 0.004]
        self.physics[:, 11] = 0.981
        self.physics[:, 17] = 1
        self.physics[:, 18] = self.physics[:, 22] = 1
        self.arrays = dict(
            state=np.array([[0.002, 0, 0, 0.02], [0.004, 0, 0, 0.02]]),
            time=np.array([0.002, 0.004]),
            initial=np.array([0, 0, 0, 0.02]),
            actions=np.array([[0, 0.002, 0], [0.002, 0.004, 0]]),
            success=np.array([False, True]),
            physics=self.physics,
        )
        self.contacts = [
            dict(
                time_s=t,
                state_after_s=t + 0.002,
                contacts=[dict(world_force_on_object=[0, 0, 0.981])],
            )
            for t in [0, 0.002]
        ]
        self.receipt = dict(
            task=TASK,
            status="completed",
            candidate=dict(mode="actions", instrument=True, timestep_scale=1),
            native_success_any=True,
            native_success_final=True,
            object_qpos_adr=0,
            object_body_ids=[0],
            expected_actions=2,
            actions_executed=2,
            initial_time_s=0,
            final_time_s=0.004,
        )
        self.write()

    def write(self):
        np.savez_compressed(self.root / "trajectory.npz", **self.arrays)
        (self.root / "contacts.jsonl").write_text(
            "\n".join(json.dumps(c) for c in self.contacts) + "\n"
        )
        self.receipt["files"] = {
            p.name: file_hash(p) for p in self.root.iterdir() if p.name != "run.json"
        }
        (self.root / "run.json").write_text(json.dumps(self.receipt))

    def test_valid_native_success_and_physical_balance(self):
        result = score(self.root)
        self.assertTrue(result["observation_valid"])
        self.assertEqual(result["physical_acceptance"], "diagnostic-pass")

    def test_invalid_evidence_cannot_become_a_physical_pass(self):
        original = copy.deepcopy((self.arrays, self.contacts, self.receipt))
        for error in (
            "contact",
            "force",
            "epoch",
            "terminal",
            "clock",
            "initial",
            "success",
            "nan",
        ):
            self.arrays, self.contacts, self.receipt = copy.deepcopy(original)
            if error == "contact":
                self.contacts.pop()
            if error == "force":
                self.contacts[0]["contacts"][0]["world_force_on_object"][2] = 0
            if error == "epoch":
                self.contacts[0]["time_s"] += 0.002
            if error == "terminal":
                self.receipt["final_time_s"] += 0.002
            if error == "clock":
                self.arrays["state"][1, 0] = 0.002
            if error == "initial":
                self.receipt["initial_time_s"] = 1
            if error == "success":
                self.receipt["native_success_final"] = False
            if error == "nan":
                self.arrays["state"][1, 1] = float("nan")
            self.write()
            with self.subTest(error=error):
                result = score(self.root)
                self.assertFalse(result["observation_valid"])
                self.assertEqual(result["physical_acceptance"], "invalid-record")

    def test_parameter_override_is_detected_from_readback(self):
        self.receipt["effective_parameters_unchanged"] = True
        path = self.root / "parameters-effective.json"
        params = json.loads(path.read_text())
        params["arrays"]["body_mass"] = [2]
        path.write_text(json.dumps(params))
        self.write()
        self.assertFalse(score(self.root)["checks"]["requested_parameters_match"])

    def test_native_task_failure_is_retained_even_with_good_physics(self):
        self.arrays["success"][:] = False
        self.receipt.update(native_success_any=False, native_success_final=False)
        self.write()
        result = score(self.root)
        self.assertTrue(result["observation_valid"])
        self.assertFalse(result["native_success_final"])
        self.assertEqual(result["physical_acceptance"], "diagnostic-pass")

    def test_changed_artifact_hash_is_detected(self):
        with (self.root / "contacts.jsonl").open("a") as stream:
            stream.write("\n")
        # A changed hash is rejected before scientific interpretation.
        with self.assertRaises(json.JSONDecodeError):
            score(self.root)


if __name__ == "__main__":
    unittest.main()
