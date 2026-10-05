"""Verify the conditional optimization, including controls and domain rejection."""
import unittest

from dexlab.damping_reference import compare_reference


class DampingReferenceTests(unittest.TestCase):
    def test_existing_mapping_is_minimax_but_not_exact(self):
        result = compare_reference([2, 4, 6], 40)
        self.assertEqual(result['minimax_coefficient_s_m'], 10)
        self.assertEqual(result['effective_tangent_damping_ns_m'], [20, 40, 60])
        self.assertEqual(result['relative_tangent_errors'], [-.5, 0, .5])
        self.assertAlmostEqual(result['minimum_worst_relative_tangent_error'], .5)

    def test_equal_load_is_exact_positive_control(self):
        result = compare_reference([4, 4], 40)
        self.assertEqual(result['minimum_worst_relative_tangent_error'], 0)
        self.assertEqual(result['relative_tangent_errors'], [0, 0])

    def test_no_sampled_alternative_beats_endpoint_bound(self):
        loads = [1, 2.5, 7]
        result = compare_reference(loads, 12)
        bound = result['minimum_worst_relative_tangent_error']
        for index in range(401):
            coefficient = index / 10
            error = max(abs(coefficient * load / 12 - 1) for load in loads)
            self.assertGreaterEqual(error + 1e-14, bound)

    def test_units_scale_coefficient_not_relative_error(self):
        left = compare_reference([2, 6], 40)
        right = compare_reference([20, 60], 80)
        self.assertAlmostEqual(right['minimax_coefficient_s_m'],
                               left['minimax_coefficient_s_m'] / 5)
        self.assertEqual(left['relative_tangent_errors'], right['relative_tangent_errors'])

    def test_invalid_preload_and_damping_rejected(self):
        for loads in ([], [0], [-1], [float('nan')], [float('inf')]):
            with self.subTest(loads=loads), self.assertRaises(ValueError):
                compare_reference(loads, 40)
        for target in (0, -1, float('nan'), float('inf')):
            with self.subTest(target=target), self.assertRaises(ValueError):
                compare_reference([2, 6], target)

    def test_unrepresentable_mapping_rejected(self):
        with self.assertRaises(ValueError):
            compare_reference([1e-300], 1e300)
