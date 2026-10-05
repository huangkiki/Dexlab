from copy import deepcopy
import json
from pathlib import Path
import unittest

import numpy as np

from dexlab.contact_damping import DAMPING, force_windows, pair_native_matches, validate_plan
from dexlab.contact_load import LoadCase


class DampingTests(unittest.TestCase):
    def test_frozen_pair_rejects_changes_and_missing_or_reordered_runs(self):
        plan = json.loads((Path(__file__).parents[1]/'benchmarks/contact-damping-ablation-v1.json').read_text())
        self.assertTrue(validate_plan(plan))
        for change in ('missing', 'duplicate', 'order', 'mass', 'penalty', 'threshold'):
            value = deepcopy(plan)
            if change == 'missing': value['jobs'].pop()
            if change == 'duplicate': value['jobs'][1]['id'] = value['jobs'][0]['id']
            if change == 'order': value['jobs'].reverse()
            if change == 'mass': value['jobs'][0]['case']['mass'] = .3
            if change == 'penalty': value['jobs'][0]['normal_parameters']['penalty_coefficient'] *= 2
            if change == 'threshold': value['target']['normal_tension_n'] = 1
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_plan(value)

    def test_native_comparison_retains_solver_and_other_actor_parameters(self):
        def native(damping):
            values = {DAMPING: damping, 'friction': 0}
            return {'normal_parameters_readback': deepcopy(values), 'contact': deepcopy(values),
                    'actor_contact_parameters': {'box': deepcopy(values), 'plane': deepcopy(values)},
                    'solver': {'iterations': 100}, 'identity': {'version': 'test'}}
        a, b = native(0), native(10)
        self.assertTrue(pair_native_matches(a, b))
        self.assertIn(DAMPING, a['contact'])
        b['solver']['iterations'] = 99
        self.assertFalse(pair_native_matches(a, b))
        b = native(10); b['actor_contact_parameters']['plane'][DAMPING] = 0
        with self.assertRaises(ValueError): pair_native_matches(a, b)

    def fixture(self):
        case = LoadCase()
        data = {'time': np.arange(case.steps+1)*case.timestep,
                'contact_force': np.zeros((case.steps, 3)), 'downward_load': case.loads()}
        return case, data

    def test_step_boundary_sign_tolerance_and_duration(self):
        case, data = self.fixture()
        boundary = round(.6/case.timestep)
        data['contact_force'][boundary-1, 2] = -.4
        data['contact_force'][boundary, 2] = -.2
        data['contact_force'][boundary+1, 2] = -.5e-6
        result = force_windows(case, data)
        self.assertEqual(result['loading']['negative_steps'], 1)
        self.assertEqual(result['unloading']['negative_steps'], 1)
        self.assertEqual(result['unloading']['minimum_force_n'], -.2)
        self.assertEqual(result['unloading']['negative_duration_s'], case.timestep)
        np.testing.assert_allclose(result['unloading']['negative_step_intervals_s'], [[.6, .6005]])

    def test_missing_clock_step_force_nan_and_changed_load_fail(self):
        case, original = self.fixture()
        for change in ('clock', 'force', 'nan', 'load'):
            data = deepcopy(original)
            if change == 'clock': data['time'][100] += .0001
            if change == 'force': data['contact_force'] = data['contact_force'][:-1]
            if change == 'nan': data['contact_force'][0, 0] = np.nan
            if change == 'load': data['downward_load'][0] = -1
            with self.subTest(change=change), self.assertRaises(ValueError): force_windows(case, data)

    def test_separated_force_is_not_fabricated_as_tension(self):
        case, data = self.fixture()
        result = force_windows(case, data)
        for row in result.values():
            self.assertEqual(row['minimum_force_n'], 0)
            self.assertEqual(row['negative_steps'], 0)
            self.assertEqual(row['negative_step_intervals_s'], [])
