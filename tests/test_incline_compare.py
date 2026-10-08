"""Reject mismatched observations; synthetic traces are not engine evidence."""
import copy
import itertools
import json
from pathlib import Path
import unittest

import numpy as np

from dexlab.incline_compare_score import score_superdex, validate_admission
from dexlab.incline_score import score
from test_incline import ideal_trace

PROTOCOL = json.loads((Path(__file__).resolve().parents[1]/'docs/evidence/incline-comparison/manifest.json').read_text())


def admission(case):
    p, c = PROTOCOL, PROTOCOL['comparison']
    a = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(a), 0, np.cos(a)])
    contact = c['normal_parameters'] | dict(coulomb_friction_coefficient=case['friction'],
        friction_falloff_vel=c['friction_falloff_vel'], viscous_friction_coefficient=c['viscous_friction_coefficient'])
    inertia = p['mass_kg']*p['side_m']**2/6
    return dict(metadata=dict(identity=dict(version='1.0.0', record_verified=True),
        api_identity=dict(version='1.0.0', record_verified=True), mass_readback=p['mass_kg'],
        inertia_readback=[inertia, 0, 0, inertia, 0, inertia],
        solver=dict(integrator='BACKWARD_EULER', iterations=100, absolute_tolerance=1e-9, relative_tolerance=1e-9),
        actor_contact_parameters=dict(box=contact.copy(), plane=contact.copy())),
        double_precision=True, time_s=0, pose=np.r_[p['side_m']/2*normal, np.cos(a/2), 0, np.sin(a/2), 0],
        velocity=np.zeros(6), gravity=[0, 0, -9.81],
        geometry=dict(box_collider='BOX', plane_collider='PLANE', vertices=list(itertools.product([-.02, .02], repeat=3))),
        plane_query_points=np.array([-.03, 0, .03])[:, None]*normal, plane_distances=[-.03, 0, .03])


def superdex_trace(case):
    trace = ideal_trace(case)
    trace.pop('friction')
    trace.pop('warnings')
    trace['force_times'] = trace['states'][1:, 0].copy()
    n = len(trace['forces'])
    trace['statuses'] = np.full(n, 'CONVERGED', dtype='U20')
    trace['contact_force_errors'] = np.zeros(n)
    return trace


class ComparisonTests(unittest.TestCase):
    def test_same_motion_same_metrics_without_fake_friction(self):
        for case in PROTOCOL['cases']:
            validate_admission(PROTOCOL, case, admission(case))
            actual = score_superdex(PROTOCOL, case, superdex_trace(case))
            expected = score(PROTOCOL, case, ideal_trace(case))
            self.assertEqual(actual['metrics'], expected['metrics'])
            self.assertTrue(actual['passed'])
            self.assertIsNone(actual['combined_friction_readback'])

    def test_native_mismatch_is_rejected(self):
        case = PROTOCOL['cases'][0]
        changes = [lambda r: r.update(double_precision=False),
                   lambda r: r.update(gravity=[0, 0, 0]),
                   lambda r: r.update(plane_distances=[0, 0, 0]),
                   lambda r: r['metadata'].update(mass_readback=1),
                   lambda r: r['metadata']['identity'].update(record_verified=False),
                   lambda r: r['metadata']['solver'].update(iterations=1),
                   lambda r: r['metadata']['actor_contact_parameters']['box'].update(coulomb_friction_coefficient=.3),
                   lambda r: r['geometry'].update(vertices=[[0, 0, 0]]*8)]
        for change in changes:
            record = admission(case)
            change(record)
            with self.assertRaises(ValueError):
                validate_admission(PROTOCOL, case, record)

    def test_corrupt_native_records_rejected(self):
        case = PROTOCOL['cases'][0]
        for corrupt in ('force_epoch', 'state', 'force', 'status', 'sum', 'quaternion', 'count'):
            trace = superdex_trace(case)
            if corrupt == 'force_epoch': trace['force_times'] -= case['timestep']
            elif corrupt == 'state': trace['states'][10, 1] += .1
            elif corrupt == 'force': trace['forces'] *= -1
            elif corrupt == 'status': trace['statuses'][10] = 'DIVERGED'
            elif corrupt == 'sum': trace['contact_force_errors'][10] = 1
            elif corrupt == 'quaternion': trace['states'][10, 4:8] *= 2
            elif corrupt == 'count': trace['contact_count'][10] = -1
            with self.subTest(corrupt=corrupt), self.assertRaises(ValueError):
                score_superdex(PROTOCOL, case, trace)

    def test_physical_failure_remains_a_result(self):
        case = PROTOCOL['cases'][0]
        trace = superdex_trace(case)
        trace['contact_count'][300] = 0
        result = score_superdex(PROTOCOL, case, trace)
        self.assertFalse(result['passed'])
        self.assertGreater(result['contact_loss_fraction'], 0)
