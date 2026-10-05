"""Adversarial force-response diagnostics; synthetic traces are not experiments."""

import unittest

import numpy as np
from test_contact_plane import exact_record

from dexlab.contact_friction import diagnose
from dexlab.contact_plane import PlaneCase


class FrictionDiagnosticTests(unittest.TestCase):
    def test_both_directions_have_same_positive_resisting_ratio(self):
        for speed in (0.25, -0.25):
            case = PlaneCase(initial_speed=speed)
            result = diagnose(case, exact_record(case))
            self.assertEqual(result["status"], "available")
            self.assertTrue(result["physical_acceptance"]["passed"])
            # The first high-speed bin contains only full sliding steps.
            row = next(x for x in result["bins"] if x["speed_lower_m_s"] == 0.1)
            self.assertAlmostEqual(row["resisting_force_ratio_median"], case.friction)
            self.assertLess(result["translational_contact_work_proxy_j"], 0)
            counts = result["interval_counts"]
            self.assertEqual(counts["total"], sum(v for k, v in counts.items() if k != "total"))

    def test_zero_friction_and_rest_are_distinct(self):
        case = PlaneCase(friction=0)
        result = diagnose(case, exact_record(case))
        self.assertTrue(any(r["resisting_force_ratio_median"] == 0 for r in result["bins"]))
        case = PlaneCase(initial_speed=0)
        result = diagnose(case, exact_record(case))
        self.assertEqual(result["interval_counts"]["selected"], 0)
        self.assertTrue(all(r["resisting_force_ratio_median"] is None for r in result["bins"]))

    def test_missing_force_coverage_is_incomplete(self):
        case = PlaneCase()
        data = exact_record(case)
        data["contact_known"][3] = False
        self.assertEqual(diagnose(case, data)["status"], "incomplete")

    def test_assisting_force_is_negative_ratio_and_failed_physics(self):
        case = PlaneCase(friction=0)
        data = exact_record(case)
        data["contact_force"][:, 0] = 0.2 * case.mass * case.gravity
        result = diagnose(case, data)
        row = next(x for x in result["bins"] if x["count"])
        self.assertAlmostEqual(row["resisting_force_ratio_median"], -0.2)
        self.assertFalse(result["physical_acceptance"]["passed"])
        self.assertAlmostEqual(result["sampled_contact_assisting_translation_duration_s"], case.duration)

    def test_detachment_and_velocity_reversal_are_excluded(self):
        case = PlaneCase(friction=0)
        data = exact_record(case)
        data["contact_force"][0, 2] = 0
        data["velocity"][3, 0] = -0.1
        result = diagnose(case, data)
        self.assertEqual(result["interval_counts"]["not_loaded"], 1)
        self.assertEqual(result["interval_counts"]["direction_crossing"], 2)
        self.assertFalse(result["physical_acceptance"]["passed"])

    def test_tipping_is_not_a_valid_planar_reference(self):
        case = PlaneCase()
        data = exact_record(case)
        data["pose"][20, 3:] = [np.cos(0.1), np.sin(0.1), 0, 0]
        result = diagnose(case, data)
        self.assertEqual(result["status"], "available")
        self.assertFalse(result["reference_applicable"])
        self.assertFalse(result["physical_acceptance"]["passed"])
