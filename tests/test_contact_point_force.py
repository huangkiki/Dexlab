from copy import deepcopy
import unittest

import numpy as np

from dexlab.contact_damping import point_force_windows
from dexlab.contact_load import LoadCase


class PointForceTests(unittest.TestCase):
    def fixture(self):
        case = LoadCase()
        data = {'time': np.arange(case.steps+1)*case.timestep,
                'contact_force': np.zeros((case.steps, 3)), 'downward_load': case.loads()}
        return case, data, [[] for _ in range(case.steps)]

    def point(self, force):
        return {'force_on_box': [0., 0., force], 'normal_native': [0., 0., 1.],
                'point_b': [0., 0., 0.]}

    def test_balanced_point_forces_hidden_by_positive_total(self):
        case, data, rows = self.fixture()
        i = round(.6/case.timestep)
        rows[i] = [self.point(-.2), self.point(.3)]
        data['contact_force'][i, 2] = .1
        result = point_force_windows(case, data, rows)
        r = result['unloading']
        self.assertEqual(r['negative_point_samples'], 1)
        self.assertEqual(r['hidden_by_aggregate_steps'], [i])
        self.assertEqual(r['minimum_point_force_n'], -.2)
        np.testing.assert_allclose(r['negative_step_intervals_s'], [[.6, .6005]])
        self.assertIsNone(result['loading']['minimum_point_force_n'])

    def test_no_observation_is_not_a_fabricated_zero_force(self):
        case, data, rows = self.fixture()
        result = point_force_windows(case, data, rows)
        for r in result.values():
            self.assertEqual(r['point_samples'], 0)
            self.assertIsNone(r['minimum_point_force_n'])
            self.assertEqual(r['negative_point_samples'], 0)

    def test_positive_minimum_and_tolerance_boundary(self):
        case, data, rows = self.fixture()
        rows[0] = [self.point(.2)]
        data['contact_force'][0, 2] = .2
        self.assertEqual(point_force_windows(case, data, rows)['loading']['minimum_point_force_n'], .2)
        rows[0] = [self.point(-.5e-6)]
        data['contact_force'][0, 2] = -.5e-6
        self.assertEqual(point_force_windows(case, data, rows)['loading']['negative_point_samples'], 0)

    def test_missing_changed_frame_nonfinite_and_ledger_rejected(self):
        case, data, rows = self.fixture()
        rows[0] = [self.point(0)]
        for kind in ('missing', 'normal', 'plane', 'nan', 'field', 'ledger', 'clock'):
            r, d = deepcopy(rows), deepcopy(data)
            if kind == 'missing': r.pop()
            if kind == 'normal': r[0][0]['normal_native'] = [0, 1, 0]
            if kind == 'plane': r[0][0]['point_b'][2] = .001
            if kind == 'nan': r[0][0]['force_on_box'][2] = float('nan')
            if kind == 'field': del r[0][0]['normal_native']
            if kind == 'ledger': r[0][0]['force_on_box'][2] = 1
            if kind == 'clock': d['time'][1] += .1
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                point_force_windows(case, d, r)
