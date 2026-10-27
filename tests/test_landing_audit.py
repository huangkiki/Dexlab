"""Exercise independent collision reconstruction without solving new forces."""

import json
from pathlib import Path
import tempfile
import unittest

import mujoco
import numpy as np

from dexlab.landing_audit import audit, collision_distances, reconstruct


class LandingAuditTests(unittest.TestCase):
    def test_pre_and_post_pose_are_distinguished_without_replacing_native_force(self):
        model = mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
          <geom type="plane" size="1 1 .1"/>
          <body pos="0 0 .11"><freejoint/><geom type="sphere" size=".1" mass="1"/>
          </body></worldbody></mujoco>''')
        pre = model.qpos0.copy()
        post = pre.copy()
        post[2] = .09
        self.assertEqual(collision_distances(model, pre), {})
        self.assertAlmostEqual(collision_distances(model, post)[(0, 1)], -.01)
        native = {"pre_qpos": pre[None], "qpos": post[None], "time": np.array([.005])}
        pairs = {"pairs": np.array([[0, 1]]), "distances": np.array([-.01]),
                 "efc_address": np.array([-1]), "local_forces": np.zeros((1, 6))}
        metadata = {"mujoco_version": mujoco.__version__, "floor": [0], "feet": [[], []]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.mjb"
            mujoco.mj_saveModel(model, str(path))
            result = reconstruct(native, pairs, [slice(0, 1)], metadata, path,
                                 {"loaded_pair_force_threshold_n": .001})
            empty = {name: value[:0] for name, value in pairs.items()}
            filtered = reconstruct(native, empty, [slice(0, 0)], metadata, path,
                                   {"loaded_pair_force_threshold_n": .001}, candidates={
                                       "offsets": np.array([0, 1]), "geom": np.array([[0, 1]]),
                                       "dist": np.array([-.01]), "type": np.array([2])})
        row = result["substeps"][0]
        self.assertEqual(row["pre"]["native_only_pairs"], [[0, 1]])
        self.assertIsNone(row["pre"]["max_distance_error_m"])
        self.assertAlmostEqual(row["post"]["max_distance_error_m"], 0)
        self.assertEqual(row["native_nonfoot_active"], 0)
        self.assertEqual(row["native_nonfoot_loaded"], 0)
        np.testing.assert_array_equal(pairs["local_forces"], np.zeros((1, 6)))
        filtered_row = filtered["substeps"][0]
        self.assertEqual(filtered_row["post"]["reconstructed_only_pairs"], [[0, 1]])
        detail = filtered_row["nonfoot_pairs"][0]
        self.assertIsNone(detail["exported_distance_m"])
        self.assertEqual(detail["raw_candidate_distance_m"], -.01)
        self.assertEqual(detail["raw_candidate_types"], [2])

    def test_version_mismatch_stops_geometry_before_loading_binary(self):
        with self.assertRaisesRegex(ValueError, "recorded MuJoCo"):
            reconstruct({}, {}, [], {"mujoco_version": "0.0"}, Path("absent.mjb"), {})

    def test_legacy_records_remain_auditable_but_missing_pairs_are_explicit(self):
        protocol = {"joint_names": ["knee"], "control_steps": 2, "substeps_per_control": 1,
                    "physics_dt_s": .005, "state_alignment_tolerance": 1e-5,
                    "loaded_pair_force_threshold_n": .001}
        states = np.zeros((3, 15)); states[:, 3] = 1
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            np.savez(path / "rollout.npz", states=states, nonfoot_contact=[False, True, False])
            np.savez(path / "contact_forces_200hz.npz", qpos=states[1:, :8], qvel=states[1:, 8:],
                     joint_names=["free", "knee"], time=[.005, .01],
                     nonfoot_force=np.zeros((2, 3)), nonfoot_contacts=np.zeros(2, dtype=int))
            report = audit(path, protocol)
            self.assertTrue(report["state_alignment"]["aligned"])
            self.assertEqual(report["native_pairs"], "unavailable")
            self.assertEqual(report["upstream_geometric_nonfoot_frames"], [1])
            self.assertIsNone(report["task_success"])
            json.dumps(report, allow_nan=False)
            with self.assertRaisesRegex(ValueError, "native pair stream"):
                audit(path, protocol, geometry=True)


if __name__ == "__main__":
    unittest.main()
