"""Analytic and malformed-input checks only; no engine import or native run."""
import unittest

import numpy as np

from dexlab.sdf_near_surface import (
    ROTATION, TRANSLATION, box_reference, query_cohort, score_queries,
)


class NearSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.cohort = query_cohort()
        self.local = self.cohort["local_m"]
        self.world = self.cohort["world_m"]
        self.distance = box_reference(self.local)[0]
        self.support = np.ones(len(self.local), dtype=bool)

    def score(self, distance=None, support=None):
        return score_queries(self.local, self.world,
                             self.distance if distance is None else distance,
                             self.support if support is None else support)

    def test_nonreal_samples_are_not_silently_coerced(self):
        for kind in (complex, str, bool):
            with self.subTest(reference=kind), self.assertRaisesRegex(ValueError, "real numeric"):
                box_reference(self.local.astype(kind))
            for index in range(3):
                inputs = [self.local, self.world, self.distance]
                inputs[index] = inputs[index].astype(kind)
                with self.subTest(kind=kind, input=index), self.assertRaisesRegex(ValueError, "real numeric"):
                    score_queries(*inputs, self.support)

    def test_reference_known_distances_and_normal_ambiguity(self):
        points = np.array([
            [0.019, 0, 0], [0.023, 0.019, 0], [0.02, 0.015, 0],
            [0, 0, 0], [-0.021, 0, 0], [0, 0, -0.01],
        ])
        distance, normal, defined = box_reference(points)
        np.testing.assert_allclose(distance, [-0.001, 0.005, 0, -0.01, 0.001, 0],
                                   rtol=0, atol=1e-17)
        np.testing.assert_array_equal(defined, [True, True, False, False, True, True])
        np.testing.assert_allclose(normal[defined], [[1, 0, 0], [0.6, 0.8, 0],
                                                    [-1, 0, 0], [0, 0, -1]], atol=1e-14)
        self.assertTrue(np.isnan(normal[~defined]).all())
        with self.assertRaisesRegex(ValueError, "not representable"):
            box_reference(np.full((1, 3), np.finfo(float).max))

    def test_complete_fixed_cohort_and_stencil_reference(self):
        self.assertEqual(self.local.shape, (5130, 3))
        self.assertEqual(self.cohort["stencil_shape"], (270, 3, 3, 2))
        offsets = self.cohort["center_offsets_m"]
        self.assertEqual([sum(offsets < 0), sum(offsets == 0), sum(offsets > 0)], [108, 54, 108])
        distance, normal, defined = box_reference(self.local[:270])
        self.assertTrue(defined.all())
        np.testing.assert_allclose(distance, offsets, rtol=0, atol=1e-17)
        np.testing.assert_array_equal(normal, self.cohort["center_normals_local"])
        # Independent planar expression: every stencil stays on its center's
        # unique closest-face branch, so its exact change is normal dot offset.
        displacement = self.local[270:].reshape(270, 3, 3, 2, 3) - self.local[:270, None, None, None, :]
        expected = offsets[:, None, None, None] + np.sum(
            displacement * normal[:, None, None, None, :], axis=-1)
        np.testing.assert_allclose(self.distance[270:].reshape(expected.shape), expected,
                                   rtol=0, atol=1e-17)
        np.testing.assert_allclose((self.world - TRANSLATION) @ ROTATION, self.local,
                                   rtol=0, atol=1e-16)

    def test_analytic_distance_has_complete_metrics_without_accuracy_claim(self):
        summary = self.score()
        self.assertEqual(summary["declared_supported_query_count"], 5130)
        for region in summary["distance_regions"].values():
            self.assertEqual(region["expected_count"], region["supported_count"])
            self.assertLess(region["distance_error_m"]["max_absolute"], 1e-17)
        for row in summary["distance_query_gradient"]:
            self.assertEqual(row["complete_stencil_count"], 270)
            self.assertEqual(row["undefined_direction_count"], 0)
            self.assertEqual(row["angle_error_deg"]["max_absolute"], 0)
            self.assertLess(row["gradient_norm_minus_one"]["max_absolute"], 1e-10)
        self.assertNotIn("physical_accuracy_established", summary)
        self.assertNotIn("native_normal", summary)

    def test_sign_reversal_retains_negative_outcomes_and_180_degree_angles(self):
        summary = self.score(-self.distance)
        self.assertEqual(summary["distance_regions"]["inside"]["sign_mismatches"], 108)
        self.assertEqual(summary["distance_regions"]["outside"]["sign_mismatches"], 108)
        for row in summary["distance_query_gradient"]:
            self.assertEqual(row["angle_error_deg"]["max_absolute"], 180)
            self.assertEqual(row["angle_error_deg"]["count"], 270)

    def test_bias_is_reported_even_when_gradient_direction_matches(self):
        summary = self.score(self.distance + 0.0005)
        self.assertEqual(summary["distance_regions"]["inside"]["sign_mismatches"], 108)
        self.assertAlmostEqual(summary["distance_regions"]["surface"]["distance_error_m"]["max_absolute"], 0.0005)
        for row in summary["distance_query_gradient"]:
            self.assertEqual(row["angle_error_deg"]["max_absolute"], 0)

    def test_constant_distance_never_receives_a_zero_angle_for_undefined_gradient(self):
        summary = self.score(np.zeros_like(self.distance))
        for row in summary["distance_query_gradient"]:
            self.assertEqual(row["zero_gradient_count"], 270)
            self.assertEqual(row["undefined_direction_count"], 270)
            self.assertIsNone(row["angle_error_deg"]["max_absolute"])
            self.assertEqual(row["angle_error_by_center_deg"], [None] * 270)

    def test_tilted_distance_field_reports_45_degree_gradient_error(self):
        summary = self.score(self.distance + self.local[:, 1])
        for row in summary["distance_query_gradient"]:
            # The first 90 centers lie on +/- x faces; adding y tilts their
            # analytic gradients to (+/-1, 1, 0), exactly 45 degrees away.
            np.testing.assert_allclose(row["angle_error_by_center_deg"][:90], 45,
                                       rtol=0, atol=1e-10)

    def test_large_finite_errors_are_not_overflowed_or_clipped(self):
        summary = self.score(np.full_like(self.distance, 1e200))
        for region in summary["distance_regions"].values():
            self.assertEqual(region["distance_error_m"]["max_absolute"], 1e200)
            self.assertEqual(region["distance_error_m"]["rms"], 1e200)
        unrepresentable = self.distance.copy()
        unrepresentable[270] = np.finfo(float).max
        with self.assertRaisesRegex(ValueError, "not representable"):
            self.score(unrepresentable)

    def test_missing_points_and_stencils_remain_in_denominators(self):
        supported = self.support.copy()
        supported[0] = False
        supported[270 + 18] = False  # Center 1, first h, first axis, negative side.
        distances = self.distance.copy()
        distances[~supported] = np.nan
        summary = self.score(distances, supported)
        self.assertEqual(summary["expected_query_count"], 5130)
        self.assertEqual(summary["declared_supported_query_count"], 5128)
        self.assertEqual(summary["unsupported_query_indices"], [0, 288])
        self.assertFalse(summary["all_queries_declared_supported"])
        self.assertEqual(summary["distance_regions"]["inside"]["expected_count"], 108)
        self.assertEqual(summary["distance_regions"]["inside"]["supported_count"], 107)
        self.assertEqual([row["complete_stencil_count"] for row in summary["distance_query_gradient"]], [268, 269, 269])

    def test_no_supported_data_produces_missing_metrics_not_zero_errors(self):
        summary = self.score(np.full_like(self.distance, np.nan), np.zeros_like(self.support))
        for region in summary["distance_regions"].values():
            self.assertEqual(region["supported_count"], 0)
            self.assertIsNone(region["distance_error_m"]["max_absolute"])
            self.assertIsNone(region["sign_mismatches"])
        for row in summary["distance_query_gradient"]:
            self.assertEqual(row["undefined_direction_count"], 270)
            self.assertIsNone(row["angle_error_deg"]["max_absolute"])

    def test_wrong_frame_changed_points_missing_mask_and_nonfinite_values_rejected(self):
        bad_local = self.local.copy(); bad_local[0, 0] += 1e-6
        nan_distances = self.distance.copy(); nan_distances[2] = np.nan
        invalid = [
            (self.local[:-1], self.world, self.distance, self.support),
            (bad_local, self.world, self.distance, self.support),
            (self.local, self.local, self.distance, self.support),
            (self.local, self.world, self.distance[:-1], self.support),
            (self.local, self.world, self.distance, None),
            (self.local, self.world, self.distance, self.support.astype(int)),
            (self.local, self.world, nan_distances, self.support),
        ]
        for args in invalid:
            with self.subTest(shapes=[np.shape(a) for a in args]), self.assertRaises(ValueError):
                score_queries(*args)


if __name__ == "__main__":
    unittest.main()
