"""Native solver controls must be explicit, bounded and engine specific."""
import unittest
from dexlab.contact_parameters import solver_parameters, solver_readback_matches


class SolverParametersTests(unittest.TestCase):
    def test_no_override_preserves_native_defaults(self):
        for engine in ('mujoco', 'superdex', 'physx'):
            self.assertEqual(solver_parameters(engine), {})

    def test_tolerance_names_are_not_cross_engine_equivalents(self):
        with self.assertRaises(ValueError):
            solver_parameters('mujoco', {'absolute_tolerance': 1e-8})
        with self.assertRaises(ValueError):
            solver_parameters('superdex', {'tolerance': 1e-8})
        with self.assertRaises(ValueError):
            solver_parameters('physx', {'iterations': 100})

    def test_invalid_values_cannot_silently_change_execution(self):
        for value in (True, 0, -1, float('nan'), float('inf'), '1e-8', [1e-8]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                solver_parameters('mujoco', {'tolerance': value})
        for value in (1.5, 10001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                solver_parameters('superdex', {'iterations': value})

    def test_values_are_preserved_without_mutating_input(self):
        controls = {'iterations': 100, 'absolute_tolerance': 1e-7, 'relative_tolerance': 1e-10}
        result = solver_parameters('superdex', controls)
        self.assertEqual(result, controls)
        self.assertIsNot(result, controls)

    def test_unapplied_or_missing_native_control_is_rejected(self):
        requested = {"iterations": 100, "absolute_tolerance": 1e-7}
        self.assertTrue(solver_readback_matches("superdex", requested, dict(requested)))
        for actual in ({"iterations": 100}, requested | {"absolute_tolerance": .001}, None):
            self.assertFalse(solver_readback_matches("superdex", requested, actual))
        self.assertFalse(solver_readback_matches("superdex", {"iterations": -1}, {}))
