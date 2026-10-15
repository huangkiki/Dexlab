"""Synthetic frame/domain checks and integration with the frozen box scorer."""
import unittest

import numpy as np

from dexlab.sdf_query_domain import classify_actor_domain

from dexlab.sdf_near_surface import HALF_SIZE, TRANSLATION, box_reference, query_cohort, score_queries


class ActorDomainTests(unittest.TestCase):
    def setUp(self):
        self.cohort = query_cohort()
        self.inputs = {
            "points_world_m": self.cohort["world_m"],
            "translation_m": TRANSLATION,
            "rotation_xyzw": [0, 0, np.sin(0.35), np.cos(0.35)],
            "bounds_local_m": np.array([-HALF_SIZE, HALF_SIZE]),
            "coordinate_guard_m": 1e-12,
        }

    def test_transformed_cohort_has_complete_partition(self):
        result = classify_actor_domain(**self.inputs)
        masks = [result[name] for name in ("interior_mask", "boundary_mask", "exterior_mask")]
        self.assertEqual([int(m.sum()) for m in masks], [2214, 702, 2214])
        self.assertEqual([int(m[:270].sum()) for m in masks], [108, 54, 108])
        np.testing.assert_array_equal(np.stack(masks).sum(axis=0), np.ones(5130))
        np.testing.assert_allclose(result["local_m"], self.cohort["local_m"], rtol=0, atol=1e-16)

    def test_known_quarter_turn_and_equivalent_quaternion_sign(self):
        # A positive x quarter-turn maps (x, y, z) to (x, -z, y).
        local = np.array([[0, 0, 0], [2, 1, -1], [2.1, 0, 0]])
        translation = np.array([0.5, 0.7, -0.8])
        world = np.array([[0, 0, 0], [2, 1, 1], [2.1, 0, 0]]) + translation
        quat = np.array([np.sqrt(0.5), 0, 0, np.sqrt(0.5)])
        for rotation in (quat, -quat):
            result = classify_actor_domain(world, translation_m=translation,
                rotation_xyzw=rotation, bounds_local_m=[[-2, -3, -4], [2, 3, 4]],
                coordinate_guard_m=1e-12)
            np.testing.assert_allclose(result["local_m"], local, rtol=0, atol=1e-14)
            np.testing.assert_array_equal(result["interior_mask"], [True, False, False])
            np.testing.assert_array_equal(result["boundary_mask"], [False, True, False])
            np.testing.assert_array_equal(result["exterior_mask"], [False, False, True])

    def test_guard_band_excludes_both_sides_of_a_face(self):
        guard = 1e-6
        points = np.array([[1 - 2*guard, 0, 0], [1 - guard/2, 0, 0],
                           [1, 0, 0], [1 + guard/2, 0, 0], [1 + 2*guard, 0, 0]])
        result = classify_actor_domain(points, translation_m=[0, 0, 0],
            rotation_xyzw=[0, 0, 0, 1], bounds_local_m=[[-1]*3, [1]*3],
            coordinate_guard_m=guard)
        np.testing.assert_array_equal(result["interior_mask"], [True, False, False, False, False])
        np.testing.assert_array_equal(result["boundary_mask"], [False, True, True, True, False])
        np.testing.assert_array_equal(result["exterior_mask"], [False, False, False, False, True])

    def test_scoring_keeps_missing_regions_and_stencil_denominators(self):
        domain = classify_actor_domain(**self.inputs)
        distances = box_reference(self.cohort["local_m"])[0]
        report = score_queries(self.cohort["local_m"], self.cohort["world_m"],
                               distances, domain["interior_mask"])
        self.assertEqual(report["expected_query_count"], 5130)
        self.assertEqual(report["declared_supported_query_count"], 2214)
        self.assertEqual(len(report["unsupported_query_indices"]), 2916)
        self.assertFalse(report["all_queries_declared_supported"])
        for name, expected, supported in (("inside", 108, 108), ("surface", 54, 0), ("outside", 108, 0)):
            region = report["distance_regions"][name]
            self.assertEqual((region["expected_count"], region["supported_count"]), (expected, supported))
            if supported == 0:
                self.assertIsNone(region["distance_error_m"]["max_absolute"])
                self.assertIsNone(region["sign_mismatches"])
        for row in report["distance_query_gradient"]:
            self.assertEqual(row["expected_count"], 270)
            self.assertEqual(row["complete_stencil_count"], 108)
            self.assertEqual(row["undefined_direction_count"], 162)

    def test_corner_band_is_coordinatewise_and_farther_exit_is_exterior(self):
        guard = 1e-4
        points = np.array([[1 + .75*guard, 1 + .75*guard, 0],
                           [1 + .75*guard, 1 + 2*guard, 0],
                           [1 - 2*guard, 1 - 2*guard, 0]])
        result = classify_actor_domain(points, translation_m=[0, 0, 0],
            rotation_xyzw=[0, 0, 0, 1], bounds_local_m=[[-1]*3, [1]*3],
            coordinate_guard_m=guard)
        np.testing.assert_array_equal(result["boundary_mask"], [True, False, False])
        np.testing.assert_array_equal(result["exterior_mask"], [False, True, False])
        np.testing.assert_array_equal(result["interior_mask"], [False, False, True])

    def test_bad_observations_are_retained_without_changing_domain(self):
        domain = classify_actor_domain(**self.inputs)
        supported = domain["interior_mask"]
        distances = -box_reference(self.cohort["local_m"])[0]
        report = score_queries(self.cohort["local_m"], self.cohort["world_m"], distances, supported)
        self.assertEqual(report["distance_regions"]["inside"]["sign_mismatches"], 108)
        for row in report["distance_query_gradient"]:
            self.assertAlmostEqual(row["angle_error_deg"]["mean_signed"], 180.0)
        distances[~supported] = np.inf
        poisoned = score_queries(self.cohort["local_m"], self.cohort["world_m"], distances, supported)
        self.assertEqual(report, poisoned)

    def test_malformed_pose_bounds_and_coordinates_are_rejected(self):
        invalid = [
            ("points_world_m", []), ("points_world_m", [[0, 0]]),
            ("points_world_m", [[np.nan, 0, 0]]),
            ("points_world_m", [[1j, 0, 0]]),
            ("points_world_m", [["1", "2", "3"]]),
            ("points_world_m", [[True, False, False]]),
            ("translation_m", [0, 0]), ("translation_m", [0, np.inf, 0]),
            ("rotation_xyzw", [0, 0, 0, 0]), ("rotation_xyzw", [0, 0, 0, 2]),
            ("rotation_xyzw", [0, 0, 1]), ("rotation_xyzw", [0, 0, np.nan, 1]),
            ("bounds_local_m", [[0, 0, 0], [0, 1, 1]]),
            ("bounds_local_m", [[1, 1, 1], [-1, -1, -1]]),
            ("bounds_local_m", [[-1, -1], [1, 1]]),
            ("bounds_local_m", [[-1, -1, -1], [1, 1, np.inf]]),
            ("coordinate_guard_m", 0), ("coordinate_guard_m", -1),
            ("coordinate_guard_m", np.nan), ("coordinate_guard_m", np.inf),
            ("coordinate_guard_m", True), ("coordinate_guard_m", [1e-12]),
            ("coordinate_guard_m", 1e-12 + 0j), ("coordinate_guard_m", "1e-12"),
        ]
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                classify_actor_domain(**dict(self.inputs, **{key: value}))

    def test_unrepresentable_coordinate_arithmetic_is_rejected(self):
        largest = np.finfo(float).max
        with self.assertRaisesRegex(ValueError, "not representable"):
            classify_actor_domain([[largest, 0, 0]], translation_m=[-largest, 0, 0],
                rotation_xyzw=[0, 0, 0, 1], bounds_local_m=[[-1]*3, [1]*3],
                coordinate_guard_m=1e-12)


if __name__ == "__main__":
    unittest.main()
