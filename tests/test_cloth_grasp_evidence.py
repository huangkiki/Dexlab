"""Failure cases for the imported cloth-grasp evidence verifier."""

import copy
import importlib.util
import unittest
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).resolve().parents[1] / "demos/cloth-folding/src/verify_cloth.py"
SPEC = importlib.util.spec_from_file_location("cloth_grasp_verifier", SOURCE)
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ClothGraspEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.maximums = dict(
            edge_strain=0.01,
            hand_penetration_m=0.0001,
            table_penetration_m=0.0001,
            self_contact_penetration_m=0,
            robot_rigid_penetration_m=0,
        )
        self.plans = [dict(side="r", point=np.array([0, 0, 0.5]))]
        self.records = []
        for tick in range(900):
            self.records.append(
                dict(
                    time_s=tick * 0.01,
                    contact_measurement_complete=True,
                    material={"r": [0, 0, 0.62]},
                    anchors={"r": [0, 0, 0.62]},
                    cloth_height_range_m=[0.5, 0.62],
                    forces={
                        "collision_r_thumb_pad": 0.04,
                        "collision_r_index_finger_pad": 0.04,
                    }
                    if tick < 800
                    else {},
                    **self.maximums,
                )
            )

    def verify(self):
        return VERIFIER.verify_episode(
            self.records,
            self.maximums,
            self.plans,
            task="grasp",
            hold_end=5,
            duration=9,
            failure=None,
        )

    def test_complete_record_can_pass(self):
        self.assertTrue(self.verify()["passed"])

    def test_missing_sample_is_not_counted_as_success(self):
        del self.records[350]
        self.assertFalse(self.verify()["passed"])

    def test_missing_plan_cannot_vacuously_pass(self):
        self.plans = []
        self.assertFalse(self.verify()["passed"])

    def test_unknown_contact_coverage_does_not_mean_zero_force(self):
        del self.records[-1]["contact_measurement_complete"]
        self.assertFalse(self.verify()["passed"])

    def test_single_pad_and_lingering_contact_fail(self):
        original = copy.deepcopy(self.records)
        for row in self.records:
            row["forces"].pop("collision_r_index_finger_pad", None)
        self.assertFalse(self.verify()["passed"])
        self.records = original
        self.records[-1]["forces"] = {"collision_l_wrist": 0.01}
        self.assertFalse(self.verify()["passed"])

    def test_nonfinite_measurement_fails(self):
        self.records[420]["material"]["r"][1] = float("nan")
        self.assertFalse(self.verify()["passed"])

    def test_each_trace_peak_must_be_bounded_by_summary(self):
        for key in VERIFIER.MAXIMUM_FIELDS:
            with self.subTest(key=key):
                previous = self.records[48][key]
                self.records[48][key] = 0.02
                result = self.verify()
                self.assertFalse(result["passed"])
                self.assertFalse(result["checks"]["summary_bounds_recorded_maxima"])
                self.records[48][key] = previous

    def test_between_sample_peak_in_summary_is_valid(self):
        self.maximums["table_penetration_m"] = 0.0002
        self.assertTrue(self.verify()["passed"])

    def test_consistent_large_penetration_still_fails_original_threshold(self):
        self.records[48]["table_penetration_m"] = 0.02
        self.maximums["table_penetration_m"] = 0.02
        result = self.verify()
        self.assertTrue(result["checks"]["summary_bounds_recorded_maxima"])
        self.assertFalse(result["checks"]["table_contact_penetration_below_1_5_mm"])

    def test_negative_penetration_is_invalid_evidence(self):
        self.records[48]["table_penetration_m"] = -0.02
        self.assertFalse(self.verify()["passed"])


if __name__ == "__main__":
    unittest.main()
