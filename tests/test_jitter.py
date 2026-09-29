"""Analytic signals and damaged ledgers must not manufacture quiet contact."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from dexlab.jitter import PADS, analyze, diagnose_run


class JitterTests(unittest.TestCase):
    def setUp(self):
        self.dt = 0.01
        self.times = np.arange(100) * self.dt
        pose = np.tile([0, 0, 0.5, 0, 0, 0, 1.0], (100, 1))
        self.log = {
            "time": self.times.copy(),
            "apple_pose": pose.copy(),
            "wrist_pose": pose.copy(),
            "velocity": np.zeros((100, 3)),
            "hand": np.tile([0, 0, 2.0], (100, 1)),
        }
        self.contacts = np.array(
            [
                [t, finger, 0, 0, 0, 0, 0, force, 0, 1]
                for t in self.times
                for finger, force in ((0, 4), (1, -4))
            ]
        )
        self.names = dict(enumerate(PADS))

    def report(self):
        result = analyze(self.log, self.contacts, self.dt, self.names, (0.0, 1.0))
        json.dumps(result, allow_nan=False)
        return result

    def set_thumb_load(self, indices, force):
        for index in indices:
            self.contacts[2 * index, 7:] = [0, 0, force]
            self.log["hand"][index] = self.contacts[2 * index : 2 * index + 2, 7:].sum(
                axis=0
            )

    def test_stationary_hold_separates_static_load_from_jitter(self):
        before = {k: v.copy() for k, v in self.log.items()}
        contacts = self.contacts.copy()
        result = self.report()
        signals = result["signals"]
        self.assertEqual(signals["hand_force_on_apple_world"]["rms_norm"], 2)
        self.assertEqual(signals["hand_force_on_apple_world"]["centered_rms_norm"], 0)
        self.assertEqual(
            signals["apple_origin_wrist_relative_position"]["peak_norm"], 0
        )
        self.assertEqual(result["sampling"]["nominal_rate_hz"], 100)
        self.assertNotIn("passed", result)
        self.assertFalse(result["energy"]["available"])
        for name in PADS:
            finger = result["contact_ledger"]["fingers"][name]
            self.assertEqual(finger["observed_low_force_intervals"], [])
            self.assertEqual(finger["unknown_intervals"], [])
        for key, value in before.items():
            np.testing.assert_array_equal(self.log[key], value)
        np.testing.assert_array_equal(self.contacts, contacts)

    def test_oscillation_matches_analytic_rms_velocity_and_force(self):
        phase = 2 * np.pi * 5 * self.times
        self.log["apple_pose"][:, 0] = 0.002 * np.sin(phase)
        self.log["velocity"][:, 0] = 0.002 * 2 * np.pi * 5 * np.cos(phase)
        self.contacts[:, 9] += np.repeat(0.2 * np.sin(phase), 2)
        self.log["hand"][:, 2] += 0.4 * np.sin(phase)
        result = self.report()["signals"]
        for name, amplitude in (
            ("apple_origin_wrist_relative_position", 0.002),
            ("apple_com_world_velocity", 0.002 * 2 * np.pi * 5),
            ("hand_force_on_apple_world", 0.4),
        ):
            self.assertAlmostEqual(
                result[name]["centered_rms_norm"], amplitude / np.sqrt(2)
            )
            self.assertAlmostEqual(result[name]["centered_peak_norm"], amplitude)

    def test_smooth_drift_remains_visible_not_called_band_limited_jitter(self):
        self.log["apple_pose"][:, 0] = self.times * 0.001
        result = self.report()["signals"]["apple_origin_wrist_relative_position"]
        self.assertAlmostEqual(result["centered_rms_norm"], np.std(self.times * 0.001))
        self.assertGreater(result["centered_rms_norm"], 0)

    def test_explicit_zero_rows_and_threshold_equality_form_low_force_runs(self):
        self.set_thumb_load(range(20, 30), 0)
        self.set_thumb_load(range(50, 55), 0.1)
        finger = self.report()["contact_ledger"]["fingers"][PADS[0]]
        self.assertEqual(finger["observed_zero_force_samples"], 10)
        self.assertEqual(finger["load"]["unknown_samples"], 0)
        self.assertAlmostEqual(finger["observed_low_force_duration_s"], 0.15)
        self.assertEqual(
            [x["samples"] for x in finger["observed_low_force_intervals"]], [10, 5]
        )
        self.assertFalse(finger["observed_low_force_intervals"][0]["left_censored"])
        self.assertFalse(finger["observed_low_force_intervals"][0]["right_censored"])

    def test_missing_step_splits_interruption_and_censors_boundaries(self):
        self.set_thumb_load(range(20, 30), 0)
        self.log = {k: np.delete(v, 25, axis=0) for k, v in self.log.items()}
        result = self.report()
        self.assertEqual(result["sampling"]["missing_samples"], 1)
        self.assertEqual(
            result["signals"]["apple_com_world_velocity"]["unknown_samples"], 1
        )
        finger = result["contact_ledger"]["fingers"][PADS[0]]
        self.assertEqual(
            [x["samples"] for x in finger["observed_low_force_intervals"]], [5, 4]
        )
        self.assertTrue(finger["observed_low_force_intervals"][0]["right_censored"])
        self.assertTrue(finger["observed_low_force_intervals"][1]["left_censored"])
        self.assertAlmostEqual(finger["observed_low_force_duration_s"], 0.09)

    def test_absent_rows_not_zero_even_when_resultant_force_matches(self):
        self.contacts = np.empty((0, 10))
        self.log["hand"][:] = 0
        result = self.report()
        self.assertEqual(result["contact_ledger"]["force_mismatch_samples"], 0)
        for finger in result["contact_ledger"]["fingers"].values():
            self.assertEqual(finger["load"]["valid_samples"], 0)
            self.assertIsNone(finger["load"]["rms_norm"])
            self.assertEqual(finger["observed_zero_force_samples"], 0)
            self.assertEqual(finger["unknown_intervals"][0]["duration_s"], 1)
            self.assertEqual(finger["low_force_duration_bounds_s"], [0, 1])

    def test_truncated_ledger_force_mismatch_is_unknown_for_both_pads(self):
        self.contacts = self.contacts[1:]
        result = self.report()["contact_ledger"]
        self.assertEqual(result["force_mismatch_samples"], 1)
        for finger in result["fingers"].values():
            self.assertEqual(finger["load"]["unknown_samples"], 1)
            self.assertEqual(finger["observed_low_force_intervals"], [])

    def test_duplicate_dynamics_timestamp_invalidates_entire_bin(self):
        self.log = {k: np.insert(v, 5, v[5], axis=0) for k, v in self.log.items()}
        result = self.report()
        self.assertEqual(result["sampling"]["duplicate_bins"], 1)
        self.assertEqual(result["sampling"]["unique_samples"], 99)
        self.assertEqual(
            result["signals"]["apple_com_world_velocity"]["unknown_samples"], 1
        )

    def test_invalid_payloads_are_not_finite_zeroes(self):
        self.log["velocity"][8, 0] = np.nan
        self.log["wrist_pose"][9, 3:] = 0
        self.contacts[20, 7] = np.inf
        self.contacts[22, 1] = 999
        result = self.report()
        self.assertEqual(
            result["signals"]["apple_com_world_velocity"]["unknown_samples"], 1
        )
        self.assertEqual(
            result["signals"]["apple_origin_wrist_relative_position"][
                "unknown_samples"
            ],
            1,
        )
        self.assertEqual(result["contact_ledger"]["invalid_rows_in_window"], 2)
        self.assertEqual(
            result["contact_ledger"]["fingers"][PADS[0]]["load"]["unknown_samples"], 2
        )

    def test_off_grid_contact_time_makes_ledger_coverage_untrusted(self):
        self.contacts[0, 0] += self.dt / 4
        result = self.report()["contact_ledger"]
        self.assertEqual(result["off_grid_rows_in_window"], 1)
        self.assertEqual(result["fingers"][PADS[0]]["load"]["valid_samples"], 0)

    def test_no_contact_file_and_malformed_field_remain_unavailable(self):
        self.contacts = None
        self.log["velocity"] = self.log["velocity"][:-1]
        result = self.report()
        self.assertFalse(result["contact_ledger"]["available"])
        self.assertIn("velocity", result["unavailable_or_malformed_fields"])
        self.assertIsNone(result["signals"]["apple_com_world_velocity"]["rms_norm"])

    def test_empty_trace_reports_unknown_entire_window(self):
        self.log = {k: v[:0] for k, v in self.log.items()}
        self.contacts = self.contacts[:0]
        result = self.report()
        self.assertEqual(result["sampling"]["missing_samples"], 100)
        self.assertIsNone(result["signals"]["hand_force_on_apple_world"]["peak_norm"])

    def test_multiple_contact_points_use_load_not_cancelled_resultant(self):
        extra = self.contacts[self.contacts[:, 1] == 0].copy()
        extra[:, 7:] *= -1
        self.contacts = np.concatenate((self.contacts, extra))
        self.log["hand"][:] = [-4, 0, 1]
        finger = self.report()["contact_ledger"]["fingers"][PADS[0]]
        self.assertAlmostEqual(finger["load"]["rms_norm"], 2 * np.sqrt(17))
        self.assertEqual(finger["load"]["unknown_samples"], 0)

    def test_wrist_relative_coordinates_respect_rotation(self):
        self.log["apple_pose"][:, :3] = [1, 0, 0.5]
        self.log["wrist_pose"][:, 3:] = [0, 0, np.sqrt(0.5), np.sqrt(0.5)]
        stats = self.report()["signals"]["apple_origin_wrist_relative_position"]
        np.testing.assert_allclose(stats["mean_components"], [0, -1, 0], atol=1e-12)

    def test_invalid_timestamps_and_off_grid_dynamics_are_reported(self):
        self.log["time"][4] = np.nan
        self.log["time"][8] += self.dt / 3
        result = self.report()
        self.assertEqual(result["sampling"]["missing_samples"], 2)
        self.assertEqual(result["sampling"]["off_grid_rows_in_window"], 1)
        self.assertEqual(result["sampling"]["nonfinite_timestamps_in_archive"], 1)
        self.contacts[0, 0] = np.nan
        self.assertEqual(
            self.report()["contact_ledger"]["fingers"][PADS[0]]["load"][
                "valid_samples"
            ],
            0,
        )

    def test_archive_reader_hashes_inputs_without_modifying_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engine.json").write_text(
                json.dumps(
                    {
                        "backend": "superdex",
                        "dt": self.dt,
                        "body_names": list(PADS),
                        "version": "fixture",
                    }
                )
            )
            self.log["time"] += 11
            self.contacts[:, 0] += 11
            np.savez(root / "sdf-dynamics.npz", **self.log)
            np.savez(root / "sdf-contacts.npz", contacts=self.contacts)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = diagnose_run(root)
            self.assertEqual(set(result["input_sha256"]), set(before))
            self.assertEqual(result["sampling"]["missing_samples"], 200)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dexlab.jitter",
                    str(root),
                    "--output",
                    str(root / "engine.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("must not overwrite", completed.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


if __name__ == "__main__":
    unittest.main()
