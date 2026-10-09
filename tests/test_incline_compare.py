"""Reject mismatched observations; synthetic traces are not engine evidence."""
import itertools
import copy
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest

import numpy as np

from dexlab.incline_compare_score import score_superdex, validate_admission, geometric_penetration, compare, validate_contact_ledger
from dexlab.incline_compare_run import run_case
from dexlab.incline_score import score, file_hash
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
    def test_full_solver_override_or_frame_change_fails_admission(self):
        case = PROTOCOL['cases'][0]
        expected = {'non_linear_solver': {'solver_type': {'name': 'NEWTON', 'value': 0}}}
        protocol = PROTOCOL | dict(solver_profile={}, effective_solver_expected=expected)
        record = admission(case) | dict(effective_solver=copy.deepcopy(expected),
            box_com_local=[0, 0, 0], box_dofs=6, plane_dofs=0, contact_pair_disabled_command=False)
        validate_admission(protocol, case, record)
        for mutate in [lambda r: r['effective_solver']['non_linear_solver']['solver_type'].update(name='BFGS'),
                       lambda r: r.update(box_com_local=[.001, 0, 0]),
                       lambda r: r.update(contact_pair_disabled_command=True),
                       lambda r: r.update(plane_dofs=6)]:
            changed = copy.deepcopy(record); mutate(changed)
            with self.assertRaises(ValueError):
                validate_admission(protocol, case, changed)

    def test_contact_ownership_and_missing_force_are_rejected(self):
        trace = dict(forces=np.array([[0, 0, 2.]]), contact_count=np.array([1]),
            contact_distance=np.array([0.]), contact_torques=np.array([[0, -.2, 0]]),
            states=np.array([[0.]*14, [0.]*14]))
        point = dict(force_on_box=[0, 0, 2.], box_is_actor_a=True, normal_native=[0, 0, 1],
                     point_a=[.1, 0, 0], point_b=[0, 0, 0], velocity_a=[0]*3, velocity_b=[0]*3, distance=0.)
        stats = [dict(max_non_linear_iters=2, max_line_search_iters=1, residual_norm=1e-10)]
        validate_contact_ledger(trace, [[point]], stats)
        for ledger in [[], [[]], [[point | dict(box_is_actor_a=False)]], [[point | dict(force_on_box=[0, 0, 0])]]]:
            with self.assertRaises(ValueError):
                validate_contact_ledger(trace, ledger, stats)

    def test_interrupted_acquisition_keeps_only_completed_steps(self):
        class Interrupted:
            step_timing = dict(native_call_seconds=0., observation_seconds=0.)
            def __init__(self, *args, **kwargs): self.calls = 0
            def step(self):
                self.calls += 1
                if self.calls == 2: raise SystemExit('test interruption')
                return np.array([0, 0, .02, 1, 0, 0, 0]), np.zeros(6), np.zeros(3), [], True, 'CONVERGED'
            def clock(self): return .002
            def close(self): pass
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)/'case'
            initial = dict(pose=[0, 0, .02, 1, 0, 0, 0], velocity=[0]*6)
            with patch('dexlab.incline_compare_run.SuperDexPlane', Interrupted), patch('dexlab.incline_compare_run.admit', return_value=initial):
                with self.assertRaises(SystemExit):
                    run_case(PROTOCOL, PROTOCOL['cases'][0], folder)
            done = json.loads((folder/'completion.json').read_text())
            self.assertEqual(done['completed_steps'], 1)
            self.assertEqual(done['error']['type'], 'SystemExit')
            with np.load(folder/'trace.npz') as trace:
                self.assertEqual(trace['states'].shape, (2, 14))
                self.assertEqual(trace['forces'].shape, (1, 3))

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

    def test_geometric_penetration_uses_rotated_cube(self):
        case = PROTOCOL['cases'][0]
        trace = superdex_trace(case)
        self.assertAlmostEqual(geometric_penetration(PROTOCOL, case, trace['states']), 0)
        normal = np.array([np.sin(np.deg2rad(15)), 0, np.cos(np.deg2rad(15))])
        trace['states'][:, 1:4] -= .002*normal
        self.assertAlmostEqual(geometric_penetration(PROTOCOL, case, trace['states']), .002)

    def test_physical_failure_remains_a_result(self):
        case = PROTOCOL['cases'][0]
        trace = superdex_trace(case)
        trace['contact_count'][300] = 0
        result = score_superdex(PROTOCOL, case, trace)
        self.assertFalse(result['passed'])
        self.assertGreater(result['contact_loss_fraction'], 0)


class ArtifactBindingTests(unittest.TestCase):
    def test_altered_artifact_and_rehashed_wrong_readback_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            sd, mj = base/'sd', base/'mj'
            sd.mkdir(); mj.mkdir()
            (sd/'manifest.json').write_text(json.dumps(PROTOCOL))
            (sd/'campaign.json').write_text(json.dumps(dict(admission_only=False,
                completed_cases=9, manifest_sha256=file_hash(sd/'manifest.json'))))
            old = dict(protocol=PROTOCOL, results=[])
            for case in PROTOCOL['cases']:
                folder = sd/case['id']; folder.mkdir()
                previous = mj/case['id']; previous.mkdir()
                np.savez(folder/'trace.npz', **superdex_trace(case))
                np.savez(previous/'trace.npz', **ideal_trace(case))
                (folder/'admission.json').write_text(json.dumps(admission(case), default=lambda x: np.asarray(x).tolist()))
                (folder/'geometry.npz').write_bytes(b'fixture')
                meta = dict(case=case, state_writes_after_initialization=0,
                    trace_sha256=file_hash(folder/'trace.npz'), admission_sha256=file_hash(folder/'admission.json'),
                    geometry_sha256=file_hash(folder/'geometry.npz'))
                (folder/'metadata.json').write_text(json.dumps(meta))
                old['results'].append(dict(id=case['id'], **score(PROTOCOL, case, ideal_trace(case))))
            with patch('dexlab.incline_compare_score.score_campaign', return_value=old):
                self.assertEqual(len(compare(sd, mj)['results']), 9)
                first = sd/PROTOCOL['cases'][0]['id']
                saved = (first/'admission.json').read_text()
                (first/'admission.json').write_text(saved+' ')
                with self.assertRaisesRegex(ValueError, 'Artifact hash'):
                    compare(sd, mj)
                record = json.loads(saved); record['gravity'] = [0, 0, 0]
                (first/'admission.json').write_text(json.dumps(record))
                meta = json.loads((first/'metadata.json').read_text())
                meta['admission_sha256'] = file_hash(first/'admission.json')
                (first/'metadata.json').write_text(json.dumps(meta))
                with self.assertRaisesRegex(ValueError, 'gravity'):
                    compare(sd, mj)
