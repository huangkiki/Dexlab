"""Regression checks for admission failures that must stop physics stepping."""
import copy
import unittest
from dexlab.adapter_qualification import INITIAL_FIELDS, compare_initial, numeric_error


class AdmissionTests(unittest.TestCase):
    def test_leading_environment_axis(self):
        self.assertEqual(numeric_error([[1., 2., 3.]], [1., 2., 3.]), 0.)

    def test_missing_nonfinite_and_mismatched_parameters_fail(self):
        reference = {field: [1., 2.] for field in INITIAL_FIELDS}
        reference['options'] = {'noslip_iterations': 0}
        for field, value in [('kp', [1., 3.]), ('object_vel', [float('nan'), 2.]),
                             ('options', {'noslip_iterations': 1})]:
            candidate = copy.deepcopy(reference)
            candidate[field] = value
            self.assertFalse(compare_initial(candidate, reference)['passed'])
        del candidate['cube_mass']
        self.assertFalse(compare_initial(candidate, reference)['passed'])

    def test_shape_change_is_rejected(self):
        with self.assertRaises(ValueError):
            numeric_error([1., 2., 3.], [1., 2.])

    def test_exact_parameters_pass(self):
        reference = {field: [1., 2.] for field in INITIAL_FIELDS}
        reference['options'] = {'noslip_iterations': 0}
        self.assertTrue(compare_initial(reference, reference)['passed'])

    def test_storage_trial_does_not_admit_solver_changes(self):
        native = {field: [1., 2.] for field in INITIAL_FIELDS}
        native['options'] = {'batch_links_info': False, 'iterations': 25}
        adapter = copy.deepcopy(native)
        adapter['options']['batch_links_info'] = True
        self.assertFalse(compare_initial(adapter, native)['passed'])
        result = compare_initial(adapter, native, storage_trial=True)
        self.assertTrue(result['passed'])
        self.assertFalse(result['configuration_identical'])
        adapter['options']['iterations'] = 26
        self.assertFalse(compare_initial(adapter, native, storage_trial=True)['passed'])
