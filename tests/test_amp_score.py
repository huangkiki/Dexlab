"""Full offline record fixture; this does not run or qualify the AMP policy."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import tempfile
import unittest

import numpy as np

from dexlab.libero_substeps import write_chunk


SCORE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "demos/amp-box-lift/score.py"))["score"]


class AmpScoreTests(unittest.TestCase):
    def test_complete_trace_and_discontinuous_state_rejection(self):
        protocol = {"conditions": {"decimation": 4, "physics_dt_s": .5}, "checks": {
            "source_height_tolerance_m": .115, "force_decode_atol": 1e-4,
            "force_decode_rtol": 1e-5, "loaded_contact_threshold_n": .001, "independent_hold_s": 2.}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "actions").mkdir()
            (root / "native/substeps").mkdir(parents=True)
            (root / "invocation.json").write_text(json.dumps({"status": "completed", "completed_actions": 1,
                "case": {"id": "analytical-fixture", "record_substeps": True, "actions": 1}}))
            metadata = {"status": "completed", "time_dtype": "float64", "substeps": 4, "chunks": [{
                "name": "action-000000.npz", "action_index": 0, "substeps": 4}],
                "body_names": ["world", "toaster/toaster_root", "left", "right"],
                "geom_names": ["floor", "toaster/box", "robot/left_hand_collision", "robot/left_wrist_collision",
                               "robot/right_hand_collision", "robot/right_wrist_collision"],
                "site_names": ["robot/left_palm", "robot/right_palm"], "actuator_names": [], "joint_names": ["object_freejoint"],
                "options": {"gravity": [[0., 0., -9.81]], "cone": 0, "disableflags": 0}}
            (root / "native/recording.json").write_text(json.dumps(metadata))
            np.savez(root / "native/effective-model.npz", body_mass=np.array([[0., 1., 1., 1.]]),
                body_inertia=np.ones((1, 4, 3)), body_rootid=np.arange(4),
                geom_bodyid=np.array([0, 1, 2, 2, 3, 3]), geom_type=np.array([0, 6, 6, 6, 6, 6]),
                body_gravcomp=np.zeros((1, 4)), dof_armature=np.zeros(1),
                jnt_type=np.array([0]), jnt_bodyid=np.array([1]), jnt_qposadr=np.array([0]),
                actuator_forcelimited=np.array([], dtype=bool), actuator_forcerange=np.zeros((0, 2)))
            qpos = np.array([0., 0., 1., 1., 0., 0., 0.])
            initial = {"qpos": qpos.copy(), "qvel": np.array([0.]), "time": 0., "goal": np.array([[0., 0., 1.1]])}
            write_chunk(root / "initial-state.npz", [initial])
            contacts = {"dim": np.array([1, 1]), "efc_address": np.array([[0], [1]]),
                "friction": np.ones((2, 5)), "local_force": np.array([[4.905, 0., 0., 0., 0., 0.]] * 2),
                "geom": np.array([[2, 1], [4, 1]]), "pos": np.array([[-.1, 0., 1.], [.1, 0., 1.]]),
                "frame": np.tile(np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]]), (2, 1, 1)),
                "dist": np.zeros(2), "worldid": np.zeros(2, dtype=int)}
            rows = []
            for i in range(4):
                before = {"qpos": qpos.copy(), "qvel": np.array([0.]), "time": i * .5,
                          "qfrc_applied": np.zeros(1), "xfrc_applied": np.zeros((4, 6))}
                after = {"qpos": qpos.copy(), "qvel": np.array([0.]), "time": (i + 1) * .5,
                    "xpos": np.array([[0., 0., 0.], [0., 0., 1.], [-.1, 0., 1.], [.1, 0., 1.]]),
                    "xquat": np.tile([1., 0., 0., 0.], (4, 1)), "xipos": np.tile([0., 0., 1.], (4, 1)),
                    "ximat": np.tile(np.eye(3), (4, 1, 1)), "subtree_com": np.tile([0., 0., 1.], (4, 1)),
                    "cvel": np.zeros((4, 6)), "site_xpos": np.array([[-.1, 0., 1.], [.1, 0., 1.]]),
                    "site_xmat": np.tile(np.eye(3), (2, 1, 1)), "actuator_force": np.zeros(0)}
                rows.append({"sequence": i, "action_index": 0, "before": before, "after": after,
                             "contacts": deepcopy(contacts), "nefc": 2, "efc_force": np.array([4.905, 4.905])})
            rows[-1]["after"]["qpos"][2] += .02
            path = root / "native/substeps/action-000000.npz"
            write_chunk(path, rows)
            write_chunk(root / "actions/action-000000.npz", [{"status": "completed", "action_index": 0,
                "feedback": {"qpos": rows[-1]["after"]["qpos"].copy(), "qvel": np.array([0.]), "automatic_reset": False,
                             "source_success": np.array([True])}}])
            result, series = SCORE(root, protocol)
            self.assertTrue(result["carrying"]["reaches_diagnostic_window"])
            self.assertEqual(result["source_success_actions"], 1)
            self.assertIsNone(result["task_success"])
            self.assertEqual(result["momentum_intervals"], 3)
            self.assertAlmostEqual(result["net_root_lift_m"], .02)
            self.assertEqual(result["native_sampled_root_lift_m"], 0.)
            np.testing.assert_allclose(series["linear_residual_ns"], 0., atol=1e-12)
            # A state write between substeps is not accepted as ordinary motion.
            rows[1]["before"]["qpos"][0] = 1.1
            path.unlink()
            write_chunk(path, rows)
            with self.assertRaisesRegex(ValueError, "continuity"):
                SCORE(root, protocol)


if __name__ == "__main__":
    unittest.main()
