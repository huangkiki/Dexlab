"""Analytical regressions for prediction epochs and full-prefix rejection."""

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

DEMO = Path(__file__).resolve().parents[1] / "demos/contact-response"
sys.path.insert(0, str(DEMO))
try:
    import baselines
    import data
    import prefix
finally:
    sys.path.pop(0)


def episode():
    n = 50
    raw = dict(time_s=np.arange(n) * .01,
               qpos_before=np.zeros((n, 27)), qpos_after=np.zeros((n, 27)),
               qvel_before=np.zeros((n, 26)), qvel_after=np.zeros((n, 26)),
               target=np.zeros((n, 20)), requested_torque=np.zeros((n, 20)),
               actuator_force=np.zeros((n, 20)), support_force=np.zeros((n, 3)),
               object_contact_force=np.zeros((n, 3)), qfrc_applied=np.zeros((n, 26)),
               external_wrenches=np.zeros((n, 4, 6)),
               contacts=np.empty((0, 22)), contact_offsets=np.zeros(n + 1, dtype=int),
               step_wall_s=np.zeros(n))
    raw["qpos_before"][:, 23] = raw["qpos_after"][:, 23] = 1
    return dict(directory=Path("fixture"), raw=raw, loads=np.zeros((n, 2)),
                manifest=dict(config=dict(support_end_s=.1, hold_start_s=.15, action_start_s=.2),
                              effective=dict(timestep=.01), source_sha256={"run.py": "source"},
                              asset_manifest_sha256="asset", runtime={"core": "fixture"},
                              force_epoch="pre-integration", case="fixture", observations_sha256="observations"),
                qualification={"scope": "analytic fixture"}, physical_sha256="physical", manifest_sha256="manifest")


class ContactResponseTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = episode(), episode(), episode()
        self.c["raw"]["target"][20:, 0] = .01
        self.protocol = dict(intervention_start_s=.2, horizon_s=.1,
                             prefix_tolerances=dict.fromkeys(prefix.UNITS, 1e-10),
                             tolerance_basis="Analytical identity fixtures; not a native experiment threshold")

    def test_local_angular_velocity_uses_right_quaternion_product(self):
        q = np.array([[np.sqrt(.5), np.sqrt(.5), 0., 0.]])
        _, predicted = baselines.predict(np.zeros((1, 3)), q, np.zeros((1, 3)),
                                         np.array([[0., np.pi, 0.]]), .5, "constant-velocity")
        np.testing.assert_allclose(predicted, [[.5, .5, .5, .5]], atol=1e-14)
        np.testing.assert_allclose(baselines.orientation_error(predicted, -predicted), 0, atol=1e-14)

    def test_constant_velocity_is_exact_for_analytical_linear_motion(self):
        p, q = baselines.predict(np.zeros((1, 3)), np.array([[1., 0., 0., 0.]]),
                                 np.array([[1., 2., 3.]]), np.zeros((1, 3)), .2, "constant-velocity")
        np.testing.assert_allclose(p, [[.2, .4, .6]])
        np.testing.assert_allclose(q, [[1, 0, 0, 0]])

    def test_copies_ignore_timing_encoding_and_quaternion_sign(self):
        a = data.physical_digest(self.a["raw"])
        self.b["raw"]["step_wall_s"] += 10
        self.b["raw"]["qpos_before"][:, 23:27] *= -1
        self.b["raw"]["qpos_after"][:, 23:27] *= -1
        self.assertEqual(a, data.physical_digest(self.b["raw"]))
        self.b["raw"]["target"][30, 0] = .1
        self.assertNotEqual(a, data.physical_digest(self.b["raw"]))

    def test_baseline_contact_uses_previous_completed_solve(self):
        # Exactly one origin (i=20): last solved load is true, i=20 and all future
        # loads are false. Using solve i would leak unavailable information.
        self.a["loads"][19] = 1.
        protocol = dict(origin_stride_s=.2, horizons_s=[.2], contact_normal_threshold_n=.02,
                        baselines=["hold", "constant-velocity"], partition="diagnostic-only")
        report = baselines.evaluate_episode(self.a, protocol)
        self.assertEqual(len(report["metrics"]), 4)
        for row in report["metrics"]:
            self.assertEqual(row["windows"], 1)
            self.assertEqual(row["contact_phase"], "loss")
            self.assertEqual(row["endpoint_contact"]["fp"], 1)
            self.assertEqual(row["event_forecast"], "no change")

    def test_intermediate_loss_is_not_hidden_by_recontact_at_endpoint(self):
        labels = np.ones(10, dtype=bool)
        labels[4] = False
        self.assertEqual(baselines.phase_labels(labels, np.array([2]), 5)[0], "switching")

    def test_early_divergence_rejected_even_when_onset_matches(self):
        self.c["raw"]["qpos_before"][2, 20] = .01
        report = prefix.compare(self.a, self.b, self.c, self.protocol)
        self.assertFalse(report["visible_prefix_compatible"])
        self.assertIn("object_position_m", report["comparisons"]["intervention"]["exceeded"])

    def test_onset_command_allowed_but_earlier_command_rejected(self):
        report = prefix.compare(self.a, self.b, self.c, self.protocol)
        self.assertTrue(report["visible_prefix_compatible"])
        self.assertEqual(report["response_identification"], "UNIDENTIFIED")
        self.c["raw"]["target"][19, 0] = .01
        self.assertFalse(prefix.compare(self.a, self.b, self.c, self.protocol)["visible_prefix_compatible"])

    def test_unit_contract_and_time_grid_are_required(self):
        del self.protocol["prefix_tolerances"]["joint_velocity_rad_s"]
        with self.assertRaisesRegex(ValueError, "every observable"):
            prefix.compare(self.a, self.b, self.c, self.protocol)
        self.protocol["prefix_tolerances"]["joint_velocity_rad_s"] = 1e-10
        self.b["raw"]["time_s"][2] += .001
        with self.assertRaisesRegex(ValueError, "time grids"):
            prefix.compare(self.a, self.b, self.c, self.protocol)

    def test_torque_and_force_groups_do_not_share_one_threshold(self):
        self.c["raw"]["qfrc_applied"][3, 20] = .001
        self.protocol["prefix_tolerances"]["applied_joint_torque_nm"] = 100.
        report = prefix.compare(self.a, self.b, self.c, self.protocol)
        self.assertIn("applied_object_force_n", report["comparisons"]["intervention"]["exceeded"])

    def test_contact_count_mismatch_is_not_silently_dropped(self):
        self.c["raw"]["contacts"] = np.zeros((1, 22))
        self.c["raw"]["contact_offsets"][3:] = 1
        report = prefix.compare(self.a, self.b, self.c, self.protocol)
        self.assertFalse(report["visible_prefix_compatible"])
        self.assertFalse(report["comparisons"]["intervention"]["native_contact_identity_matches"])

    def test_missing_hash_and_nonunit_orientation_reject_import(self):
        with tempfile.TemporaryDirectory() as path:
            (Path(path) / "manifest.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "Pinned bundle file"):
                data.load_episode(path, {"manifest.json": "wrong", "observations.npz": "wrong"})
        self.a["raw"]["qpos_after"][0, 23] = 2
        with self.assertRaisesRegex(ValueError, "Non-unit"):
            data.validate_shapes(self.a["raw"])

    def test_changed_physical_model_does_not_become_an_action_effect(self):
        self.c["manifest"]["effective"]["geom_friction"] = [0.]
        report = prefix.compare(self.a, self.b, self.c, self.protocol)
        self.assertFalse(report["visible_prefix_compatible"])
        self.assertIn("intervention: effective geom_friction differs", report["reasons"])

    def test_opposing_pair_loads_survive_zero_net_force(self):
        raw = self.a["raw"]
        raw["contacts"] = np.zeros((2, 22))
        raw["contacts"][:, 2] = [1, 2]
        raw["contacts"][:, 16] = 1.
        raw["contacts"][:, 15] = -.0001
        raw["contact_offsets"][1:] = 2
        effective = dict(body_names=["world", "r_index_finger_pad", "r_thumb_pad", "object"])
        loads, distances = data.pad_observations(raw, effective)
        np.testing.assert_equal(raw["object_contact_force"][0], 0)
        np.testing.assert_equal(loads[0], [1., 1.])
        np.testing.assert_equal(distances[0], [-.0001, -.0001])
        self.assertTrue(np.isnan(distances[1:]).all())

    def test_native_contact_with_tensile_normal_is_invalid(self):
        self.a["raw"]["contacts"] = np.zeros((1, 22))
        self.a["raw"]["contacts"][0, 16] = -1.
        with self.assertRaisesRegex(ValueError, "tensile"):
            data.validate_shapes(self.a["raw"])


if __name__ == "__main__":
    unittest.main()
