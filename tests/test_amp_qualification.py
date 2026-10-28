"""Offline admission must detect corrupted native records and control effects."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

import numpy as np

from dexlab.amp_lift_audit import compare_probe_values
from dexlab.libero_substeps import write_chunk
from dexlab.migration_budget import MigrationBudget


QUALIFY = runpy.run_path(str(Path(__file__).resolve().parents[1] / "demos/amp-box-lift/qualify.py"))["qualify"]


class AmpQualificationTests(unittest.TestCase):
    def test_parity_includes_discrete_feedback_and_rejects_nonfinite_states(self):
        reference = {"qpos": np.array([.1, .2]), "feedback": {"found": np.array([1], dtype=int)}}
        changed = deepcopy(reference)
        changed["qpos"][0] += 1e-6
        self.assertLess(compare_probe_values(reference, changed, atol=1e-5, rtol=0), 1e-5)
        changed["feedback"]["found"][0] = 0
        with self.assertRaisesRegex(ValueError, "discrete"):
            compare_probe_values(reference, changed, atol=1e-5, rtol=0)
        changed = deepcopy(reference)
        changed["qpos"][0] = np.nan
        with self.assertRaisesRegex(ValueError, "finiteness"):
            compare_probe_values(reference, changed, atol=1e-5, rtol=0)

    def test_complete_probe_acceptance_and_corrupted_force_rejection(self):
        cases = [{"id": name, "actions": 1} for name in ("probe-native", "probe-recorded")]
        protocol = {"cases": cases, "conditions": {"decimation": 1, "physics_dt_s": .005},
                    "gpu_budget": {"limit_mib": 20480, "minimum_device_reserve_mib": 2048, "sampling_interval_s": 2},
                    "checks": {"state_parity_atol": 1e-5, "state_parity_rtol": 0.,
                               "force_decode_atol": 1e-4, "force_decode_rtol": 1e-5,
                               "loaded_contact_threshold_n": .001}}
        digest = "a" * 64
        initial = {"qpos": np.array([0.]), "qvel": np.array([0.]), "time": 0.}
        after = {"qpos": np.array([.1]), "qvel": np.array([1.]), "time": .005}
        row = {"sequence": 0, "action_index": 0, "before": initial, "after": after,
               "nefc": 1, "efc_force": np.array([9.81]), "contacts": {
                   "dim": np.array([1]), "efc_address": np.array([[0]]),
                   "friction": np.ones((1, 5)), "local_force": np.array([[9.81, 0., 0., 0., 0., 0.]]),
                   "worldid": np.array([0])}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            budget = MigrationBudget.create(root / "budget", {"protocol_sha256": digest, "matrix": cases,
                "resource_plan": {"profile": "adaptive-16g-4c", "measurement": {"sha256": "b" * 64, "peak_mib": 4096.}}})
            for case in cases:
                output = root / case["id"]
                (output / "actions").mkdir(parents=True)
                (output / "native").mkdir()
                write_chunk(output / "initial-state.npz", [initial])
                write_chunk(output / "actions/action-000000.npz", [{"feedback": after}])
                np.savez(output / "native/effective-model.npz", mass=np.array([1.]))
                (output / "native/compiled-template.mjb").write_bytes(b"fixture only")
                metadata = {"options": {"cone": 0}, "time_dtype": "float64", "use_cuda_graph": True,
                            "force_decoder_sha256": "fixture", "body_names": ["object"],
                            "geom_names": ["surface"], "joint_names": [], "site_names": [], "actuator_names": [],
                            "epochs": {}, "force_order": "fixture", "status": "model-only"}
                if case["id"] == "probe-recorded":
                    (output / "native/substeps").mkdir()
                    write_chunk(output / "native/substeps/action-000000.npz", [row])
                    metadata.update(status="completed", substeps=1, chunks=[{
                        "name": "action-000000.npz", "action_index": 0, "substeps": 1}])
                (output / "native/recording.json").write_text(json.dumps(metadata))
                invocation = {"status": "completed", "completed_actions": 1, "case": case,
                              "protocol_sha256": digest, "source": {}, "runtime": {},
                              "native_payload": {}, "runner_sha256": "fixture", "recorder_sha256": "fixture",
                              "effective_conditions": {"seed": 137}}
                resource_path = output / "resources.json"
                invocation.update(resources_receipt=str(resource_path),
                                  cgroup="0::/test/dexlab-bounded-fixture.service")
                resource_path.write_text(json.dumps({
                    "state": "completed", "returncode": 0, "service": "dexlab-bounded-fixture", "wall_s": .1,
                    "resource_plan": {"profile": "adaptive-16g-4c", "measurement": {
                        "sha256": "b" * 64, "peak_mib": 4096.}},
                    "telemetry": {"state": "completed", "returncode": 0, "profile": "adaptive-16g-4c",
                                  "gpu_budget": {"uuid": "GPU-fixture", "limit_mib": 20480, "sampling_interval_s": 2},
                                  "initial_gpu_memory_mib": ["GPU-fixture, 1000, 23028"],
                                  "gpu_memory_samples_mib": [{"devices": ["GPU-fixture, 2000, 23028"]}],
                                  "final_gpu_memory_mib": ["GPU-fixture, 1000, 23028"],
                                  "final": {"memory.events": "oom 0\noom_kill 0\noom_group_kill 0"},
                                  "effective_limits": {"memory.max": "1024", "memory.swap.max": "0"}}}))
                raw = json.dumps(invocation).encode()
                (output / "invocation.json").write_bytes(raw)
                attempt = budget.reserve(case["id"], {"output": str(output)}, timeout_s=1)
                budget.finish(attempt, wall_s=.01, evidence_sha256=hashlib.sha256(raw).hexdigest(), outcome="recorded")
            result = QUALIFY(budget, protocol, digest)
            self.assertTrue(result["passed"])
            self.assertIsNone(result["task_success"])
            self.assertEqual(result["loaded_contacts"], 1)
            resource_path = root / "probe-recorded/resources.json"
            receipt = resource_path.read_text()
            changed = json.loads(receipt)
            del changed["telemetry"]["final"]
            resource_path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "final resource telemetry"):
                QUALIFY(budget, protocol, digest)
            resource_path.write_text(receipt)
            changed = json.loads(receipt)
            changed["resource_plan"] = None
            resource_path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "measured adaptive resource plan"):
                QUALIFY(budget, protocol, digest)
            resource_path.write_text(receipt)
            for sample in (None, ["GPU-fixture, 22000, 23028"]):
                changed = json.loads(receipt)
                changed["telemetry"]["gpu_memory_samples_mib"][0]["devices"] = sample
                resource_path.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, "GPU"):
                    QUALIFY(budget, protocol, digest)
            resource_path.write_text(receipt)
            # Corrupt a measured force without altering its solved constraints.
            path = root / "probe-recorded/native/substeps/action-000000.npz"
            path.unlink()
            row["contacts"]["local_force"][0, 0] = 0.
            write_chunk(path, [row])
            with self.assertRaisesRegex(ValueError, "decoding failed"):
                QUALIFY(budget, protocol, digest)
            row["contacts"]["local_force"][0, 0] = 9.81
            row["before"]["qpos"][0] = .2
            path.unlink()
            write_chunk(path, [row])
            with self.assertRaisesRegex(ValueError, "native continuity.qpos"):
                QUALIFY(budget, protocol, digest)


if __name__ == "__main__":
    unittest.main()
