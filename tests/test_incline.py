"""Synthetic evidence tests do not substitute for native benchmark results."""
import json
from pathlib import Path
import unittest

import numpy as np
from dexlab.incline_score import score

PROTOCOL = json.loads((Path(__file__).resolve().parents[1] / 'docs/evidence/incline-friction/manifest.json').read_text())


def ideal_trace(case):
    p = PROTOCOL
    h = case['timestep']
    n = round(p['duration_s'] / h)
    a = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(a), 0, np.cos(a)])
    tangent = np.array([np.cos(a), 0, -np.sin(a)])
    acceleration = 0 if case['regime'] == 'static' else p['gravity_m_s2'] * (np.sin(a) - case['friction'] * np.cos(a))
    time = np.arange(n + 1) * h
    states = np.zeros((n + 1, 14))
    states[:, 0] = time
    states[:, 4:8] = [np.cos(a / 2), 0, np.sin(a / 2), 0]
    states[:, 8:11] = time[:, None] * acceleration * tangent
    states[:, 1:4] = p['side_m'] / 2 * normal
    states[1:, 1:4] += np.cumsum(states[1:, 8:11] * h, axis=0)
    force = p['mass_kg'] * (acceleration * tangent + [0, 0, p['gravity_m_s2']])
    return dict(states=states, forces=np.tile(force, (n, 1)), force_times=time[:-1].copy(),
                contact_distance=np.zeros(n), contact_count=np.full(n, 4),
                friction=np.full((n, 2), case['friction']), warnings=np.zeros((n, 8)))


class InclineTests(unittest.TestCase):
    def test_ideal_all_regimes(self):
        for case in PROTOCOL['cases']:
            result = score(PROTOCOL, case, ideal_trace(case))
            self.assertTrue(result['passed'], (case, result))
            json.dumps(result, allow_nan=False)
            self.assertLess(result['metrics']['acceleration_error_m_s2'], 1e-10)

    def test_corruption_rejected(self):
        case = PROTOCOL['cases'][0]
        for corruption in ['position', 'velocity', 'time', 'force_epoch', 'nan', 'truncate', 'force', 'friction', 'initial', 'warning']:
            trace = ideal_trace(case)
            if corruption == 'position': trace['states'][10:, 1] += .01
            elif corruption == 'velocity': trace['states'][10:, 8] += .1
            elif corruption == 'time': trace['states'][10, 0] += .01
            elif corruption == 'force_epoch': trace['force_times'] += case['timestep']
            elif corruption == 'nan': trace['forces'][10, 0] = np.nan
            elif corruption == 'truncate': trace['states'] = trace['states'][:-1]
            elif corruption == 'force': trace['forces'] *= -1
            elif corruption == 'friction': trace['friction'] *= 2
            elif corruption == 'initial': trace['states'][:, 1] += 1
            elif corruption == 'warning': trace['warnings'][1, 0] = 1
            with self.subTest(corruption=corruption), self.assertRaises(ValueError):
                score(PROTOCOL, case, trace)

    def test_wrong_physics_is_failed_not_hidden(self):
        case = PROTOCOL['cases'][0]
        trace = ideal_trace(case)
        h = case['timestep']
        trace['states'][:, 8] = trace['states'][:, 0] * .1
        trace['states'][1:, 1] += np.cumsum(trace['states'][1:, 8] * h)
        trace['forces'][:, 0] += PROTOCOL['mass_kg'] * .1
        result = score(PROTOCOL, case, trace)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['static_displacement_m'])

    def test_contact_loss_is_reported_as_physics_failure(self):
        case = PROTOCOL['cases'][0]
        trace = ideal_trace(case)
        trace['contact_count'][300] = 0
        trace['friction'][300] = np.nan
        result = score(PROTOCOL, case, trace)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['continuous_support'])
