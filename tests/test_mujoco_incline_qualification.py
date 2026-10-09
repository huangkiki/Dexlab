"""Independent evidence rejection, not substitute physics experiments."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.incline_run import model_xml, run_case
from dexlab.incline_score import export_precision, validate_contacts

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / 'docs/evidence/mujoco-incline/newton-elliptic.json').read_text())


def supported_trace():
    case = copy.deepcopy(PROTOCOL['cases'][0])
    h = case['timestep']
    steps = round(PROTOCOL['duration_s'] / h)
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    tangent = np.array([np.cos(angle), 0., -np.sin(angle)])
    frame = np.array([normal, tangent, [0., 1., 0.]])
    force = np.array([0., 0., PROTOCOL['mass_kg'] * PROTOCOL['gravity_m_s2']])
    trace = dict(states=np.zeros((steps+1, 14)), forces=np.tile(force, (steps, 1)),
                 generalized_contact_forces=np.tile(np.r_[force, np.zeros(3)], (steps, 1)),
                 accelerations=np.zeros((steps, 6)), solver_iterations=np.ones(steps),
                 contact_distance=np.zeros(steps), contact_count=np.ones(steps))
    contacts = dict(offsets=np.arange(steps+1), geom=np.tile([0, 1], (steps, 1)),
                    frame=np.tile(frame.ravel(), (steps, 1)), pos=np.zeros((steps, 3)),
                    force_local=np.tile(np.r_[frame @ force, np.zeros(3)], (steps, 1)),
                    distance=np.zeros(steps), friction=np.tile([case['friction']]*2+[0.]*3, (steps, 1)),
                    solref=np.tile(PROTOCOL['solref'], (steps, 1)),
                    solimp=np.tile([.9, .9, .001, .5, 2], (steps, 1)))
    return case, trace, contacts


class NativeLedgerTests(unittest.TestCase):
    def test_independent_channels_agree(self):
        case, trace, contacts = supported_trace()
        validate_contacts(PROTOCOL, case, trace, contacts)

    def test_missing_contact_and_wrong_frames_forces_or_epochs_rejected(self):
        for kind in ('offset', 'pair', 'frame', 'normal', 'force', 'generalized', 'acceleration', 'solref'):
            case, trace, contacts = supported_trace()
            if kind == 'offset': contacts['offsets'][10] -= 1
            elif kind == 'pair': contacts['geom'][10] = [1, 1]
            elif kind == 'frame': contacts['frame'][10, 0] += .1
            elif kind == 'normal': contacts['frame'][10] *= -1
            elif kind == 'force': contacts['force_local'][10] *= -1
            elif kind == 'generalized': trace['generalized_contact_forces'][10, 0] += .1
            elif kind == 'acceleration': trace['accelerations'][10, 0] += .1
            elif kind == 'solref': contacts['solref'][10, 0] *= 2
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_contacts(PROTOCOL, case, trace, contacts)

    def test_negative_cannot_contain_support(self):
        case, trace, contacts = supported_trace()
        case['negative_no_floor'] = True
        with self.assertRaisesRegex(ValueError, 'Disabled support'):
            validate_contacts(PROTOCOL, case, trace, contacts)

    def test_lossy_export_detected_without_changing_original_physics(self):
        original = {'pose': [0.123456789123, .1], 'mass': .064}
        exported = copy.deepcopy(original)
        self.assertTrue(export_precision(original, exported)['within_tolerance'])
        exported['pose'][0] = .123457
        report = export_precision(original, exported)
        self.assertFalse(report['within_tolerance'])
        self.assertIn('pose', report['absolute_max_errors'])
        self.assertFalse(report['compiled_xml_used_for_physics'])

    def test_integrator_change_requires_new_epoch_protocol(self):
        with self.assertRaisesRegex(ValueError, 'Euler force epoch'):
            model_xml(dict(PROTOCOL, integrator='RK4'), PROTOCOL['cases'][0])

    def test_interruption_keeps_incomplete_record(self):
        for exception in (SystemExit('native abort'), KeyboardInterrupt()):
            data = SimpleNamespace(time=0., qpos=np.zeros(7), qvel=np.zeros(6), warning=[], maxuse_arena=0)
            model = SimpleNamespace()
            mj = SimpleNamespace(MjModel=SimpleNamespace(from_xml_string=lambda _: model,
                                 from_xml_path=lambda _: model), MjData=lambda _: data,
                                 mj_forward=lambda *args: None,
                                 mj_saveLastXML=lambda path, _: Path(path).write_text('<mujoco/>'))
            def interrupted(*args):
                raise exception
            mj.mj_step = interrupted
            with tempfile.TemporaryDirectory() as temp, patch('dexlab.incline_run.native_readback', return_value={}):
                destination = Path(temp) / 'case'
                with self.assertRaises(type(exception)):
                    run_case(mj, PROTOCOL, PROTOCOL['cases'][0], destination)
                meta = json.loads((destination / 'metadata.json').read_text())
                self.assertEqual(meta['completed_steps'], 0)
                self.assertIn(type(exception).__name__, meta['error'])
                with np.load(destination / 'trace.npz') as trace:
                    self.assertEqual(trace['states'].shape, (1, 14))
                    self.assertEqual(trace['forces'].shape, (0, 3))

class InvalidRecordTests(unittest.TestCase):
    def test_native_force_state_disagreement_keeps_residual(self):
        from dexlab.incline_score import ImpulseConsistencyError, measure_response
        case, trace, _ = supported_trace()
        steps = len(trace['forces'])
        trace['force_times'] = np.arange(steps) * case['timestep']
        trace['states'][:, 0] = np.arange(steps+1) * case['timestep']
        trace['states'][:, 4] = 1.
        trace['forces'][20, 0] += .1
        with self.assertRaises(ImpulseConsistencyError) as caught:
            measure_response(PROTOCOL, case, trace)
        self.assertGreater(caught.exception.residual, 1e-7)


class NativeAdmissionTests(unittest.TestCase):
    def test_frames_inertia_origin_geometry_and_control_overrides_rejected(self):
        from dexlab.incline_score import validate_admission
        protocol = json.loads((ROOT / 'docs/evidence/mujoco-incline/pgs-elliptic.json').read_text())
        admission = json.loads((ROOT / 'docs/evidence/mujoco-incline/admission-example.json').read_text())
        case = protocol['cases'][0]
        validate_admission(protocol, case, admission)
        for name in ('body_ipos', 'body_iquat', 'geom_size', 'geom_xmat', 'state',
                     'dof_damping', 'geom_contype', 'geom_solmix', 'ls_tolerance'):
            altered = copy.deepcopy(admission)
            value = np.asarray(altered[name], dtype=float)
            value.flat[0] += .001
            altered[name] = value.tolist()
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_admission(protocol, case, altered)


if __name__ == '__main__':
    unittest.main()
