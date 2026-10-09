"""Evidence corruption checks without importing a simulation engine."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

import numpy as np

from dexlab.newton_incline_score import (
    initial_state, validate_admission, validate_protocol, validate_rows,
)


FIXTURES = Path(__file__).parent / 'fixtures'


class NewtonEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((FIXTURES / 'newton-incline-protocol.json').read_text())
        self.admission = json.loads((FIXTURES / 'newton-incline-admission.json').read_text())
        self.case = next(c for c in self.protocol['cases'] if c['id'] == 'static-h0.001')

    def rows(self):
        state = initial_state(self.protocol, self.case)
        angle = np.deg2rad(self.case['angle_deg'])
        normal = [float(np.sin(angle)), 0., float(np.cos(angle))]
        weight = self.protocol['mass_kg'] * self.protocol['gravity_m_s2']
        result = []
        for i in range(2000):
            before, after = state.copy(), state.copy()
            before[0], after[0] = i * .001, (i + 1) * .001
            result.append(dict(interval_start_s=before[0], interval_end_s=after[0],
                               pre_state=before.tolist(), state=after.tolist(),
                               net_force=[0., 0., weight], contacts=dict(
                                   shape0=[0], shape1=[1], normal=[normal],
                                   point0=[[0, 0, 0]], point1=[[0, 0, -.02]],
                                   offset0=[[0, 0, 0]], offset1=[[0, 0, 0]],
                                   margin0=[0], margin1=[0]),
                               force_readback=dict(convention='wrench_on_shape0',
                                                   force=[[0, 0, -weight, 0, 0, 0]])))
        admission = deepcopy(self.admission)
        admission['initial_state'] = state.tolist()
        return admission, result

    def test_native_admission_accepts_float32_roundoff(self):
        validate_protocol(self.protocol)
        validate_admission(self.protocol, self.case, self.admission)

    def test_mass_inertia_geometry_and_drive_overrides_rejected(self):
        for key, changed in [
            ('body_mass', [.065]), ('body_inertia', [np.eye(3).tolist()]),
            ('shape_material_mu', [.5, .6]), ('shape_material_kd', [0, 0]),
            ('shape_scale', [[0, 0, 0], [.021] * 3]),
            ('joint_target_ke', [1] * 6), ('gravity', [[0, 0, -9.8]] * 2),
        ]:
            with self.subTest(key=key):
                value = deepcopy(self.admission)
                value['model'][key] = changed
                with self.assertRaises(ValueError):
                    validate_admission(self.protocol, self.case, value)

    def test_duplicate_free_joint_and_reset_pollution_rejected(self):
        for change in ('topology', 'velocity'):
            value = deepcopy(self.admission)
            if change == 'topology':
                value['counts']['joint_count'] = 2
            else:
                value['initial_state'][8] = .01
            with self.assertRaises(ValueError):
                validate_admission(self.protocol, self.case, value)

    def test_changed_threshold_and_duplicate_case_rejected(self):
        for change in ('limit', 'case'):
            value = deepcopy(self.protocol)
            if change == 'limit':
                value['limits']['penetration_m'] = .1
            else:
                value['cases'][1] = value['cases'][0]
            with self.assertRaises(ValueError):
                validate_protocol(value)

    def test_force_ledger_and_epochs(self):
        admission, rows = self.rows()
        trace = validate_rows(self.protocol, self.case, admission, rows)
        self.assertEqual(trace['states'].shape, (2001, 14))
        for change in ('time', 'force', 'pair', 'missing', 'convention'):
            with self.subTest(change=change):
                changed = deepcopy(rows)
                if change == 'time':
                    changed[4]['interval_end_s'] += .001
                elif change == 'force':
                    changed[4]['force_readback']['force'][0][2] *= -1
                elif change == 'pair':
                    changed[4]['contacts']['shape1'] = [0]
                elif change == 'convention':
                    changed[4]['force_readback']['convention'] = 'com_wrench'
                else:
                    changed.pop()
                with self.assertRaises(ValueError):
                    validate_rows(self.protocol, self.case, admission, changed)

    def test_position_injection_rejected(self):
        admission, rows = self.rows()
        rows[100]['state'][1] += .001
        with self.assertRaises(ValueError):
            validate_rows(self.protocol, self.case, admission, rows)


if __name__ == '__main__':
    unittest.main()
