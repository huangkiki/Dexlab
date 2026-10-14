"""Reject overwritten parameters, bad contact epochs and incomplete evidence."""

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.genesis_incline_score import (
    initial_state, validate_admission, validate_protocol, validate_runtime, validate_trace,
)


ROOT = Path(__file__).resolve().parents[1] / 'docs/evidence/genesis-incline'


class GenesisInclineTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((ROOT / 'profiles/newton-elliptic-signorini.json').read_text())
        self.case = self.protocol['cases'][0]
        self.admission = json.loads((ROOT / 'admission-example.json').read_text())

    def test_native_zero_time_readback_and_full_case_matrix(self):
        validate_protocol(self.protocol)
        validate_admission(self.protocol, self.case, self.admission)

    def test_wrong_mass_frame_friction_clock_or_solver_is_rejected(self):
        mutations = [lambda a: a['mass'].__setitem__(0, .065),
                     lambda a: a['com'][0].__setitem__(0, .001),
                     lambda a: a['inertia'][0][1].__setitem__(1, .001),
                     lambda a: a['options'].update(constraint_solver=0),
                     lambda a: a['options'].update(dt=.01),
                     lambda a: a['sim_options'].update(substeps=2),
                     lambda a: a['geom_parameters'][0]['quat'].__setitem__(2, -.13),
                     lambda a: a['geom_parameters'][1]['data'].__setitem__(0, .041),
                     lambda a: a['geom_parameters'][1].update(friction=.01),
                     lambda a: a['geom_parameters'][0]['sol_params'].__setitem__(0, .002),
                     lambda a: a['friction_ratio'].__setitem__(1, 2),
                     lambda a: a.update(n_envs=2),
                     lambda a: a.update(initial_contact_count=1),
                     lambda a: a['static_config'].update(enable_signorini_contact=False)]
        for mutate in mutations:
            admission = copy.deepcopy(self.admission)
            mutate(admission)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                validate_admission(self.protocol, self.case, admission)

    def test_missing_duplicate_negative_and_unsafe_cases_rejected(self):
        for kind in ('missing', 'duplicate', 'negative', 'path'):
            protocol = copy.deepcopy(self.protocol)
            if kind == 'missing':
                protocol['cases'].pop(0)
            elif kind == 'duplicate':
                protocol['cases'][1] = copy.deepcopy(protocol['cases'][0])
            elif kind == 'negative':
                protocol['cases'].pop()
            else:
                protocol['cases'][0]['id'] = '../escape'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_protocol(protocol)

    def test_unsupported_signorini_combinations_rejected(self):
        for key, value in [('constraint_solver', 'CG'), ('friction_cone', 'pyramidal')]:
            protocol = copy.deepcopy(self.protocol)
            protocol['genesis']['options'][key] = value
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                validate_protocol(protocol)

    def stationary_trace(self):
        h = self.case['timestep']
        protocol = dict(self.protocol, duration_s=3 * h)
        states = np.tile(initial_state(protocol, self.case), (4, 1))
        states[:, 0] = np.arange(4) * h
        force = [0, 0, protocol['mass_kg'] * protocol['gravity_m_s2']]
        angle = np.deg2rad(self.case['angle_deg'])
        normal = [np.sin(angle), 0, np.cos(angle)]
        contacts = dict(geom_a=[1], geom_b=[0], link_a=[1], link_b=[0],
                        penetration=[0], position=[states[0, 1:4].tolist()], normal=[normal],
                        force=[[-v for v in force]], friction=[.5], sol_params=[protocol['genesis']['sol_params']])
        rows = [dict(interval_start_s=i * h, interval_end_s=(i + 1) * h, contacts=copy.deepcopy(contacts))
                for i in range(3)]
        trace = dict(states=states, forces=np.tile(force, (3, 1)), contact_count=np.ones(3),
                     native_errors=np.zeros((3, 1)), force_times=states[:-1, 0].copy())
        return protocol, trace, rows

    def test_stationary_independent_force_ledger(self):
        protocol, trace, rows = self.stationary_trace()
        validate_trace(protocol, self.case, trace, rows)

    def test_contact_loss_wrong_sign_parameter_override_and_clock_shift(self):
        for kind in ('lost', 'sign', 'friction', 'normal', 'pair', 'sol', 'row-clock', 'force-clock', 'error'):
            protocol, trace, rows = self.stationary_trace()
            data = rows[1]['contacts']
            if kind == 'lost':
                data['force'] = []
            elif kind == 'sign':
                data['force'][0][2] *= -1
            elif kind == 'friction':
                data['friction'][0] = .4
            elif kind == 'normal':
                data['normal'][0][0] *= -1
            elif kind == 'pair':
                data['geom_a'][0] = 0
            elif kind == 'sol':
                data['sol_params'][0] = [.001, 1, .9, .9, .001, .5, 2]
            elif kind == 'row-clock':
                rows[1]['interval_start_s'] += .001
            elif kind == 'force-clock':
                trace['force_times'] += .001
            else:
                trace['native_errors'][1] = 4
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_trace(protocol, self.case, trace, rows)

    def test_zero_geom_friction_does_not_hide_effective_contact_floor(self):
        protocol, trace, rows = self.stationary_trace()
        case = dict(self.case, friction=0, regime='frictionless')
        for row in rows:
            row['contacts']['friction'] = [.01]
        validate_trace(protocol, case, trace, rows)
        rows[1]['contacts']['friction'] = [0]
        with self.assertRaisesRegex(ValueError, 'pair friction'):
            validate_trace(protocol, case, trace, rows)

    def test_truncation_reset_state_injection_and_nonfinite_data_rejected(self):
        for kind in ('truncate', 'reset', 'injection', 'nan'):
            protocol, trace, rows = self.stationary_trace()
            if kind == 'truncate':
                trace['states'] = trace['states'][:-1]
            elif kind == 'reset':
                trace['states'][0, 8] = .01
            elif kind == 'injection':
                trace['states'][2:, 1] += .001
            else:
                trace['forces'][1, 0] = np.nan
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_trace(protocol, self.case, trace, rows)

    def test_interrupts_preserve_partial_records_and_release_scene(self):
        from dexlab.genesis_incline import run_case

        for error in (SystemExit(1), KeyboardInterrupt(), RuntimeError('native failure')):
            with self.subTest(error=type(error).__name__), TemporaryDirectory() as directory:
                target = Path(directory) / 'case'
                with patch('dexlab.genesis_incline.GenesisIncline') as scene:
                    scene.return_value.admission = self.admission
                    scene.return_value.state.return_value = initial_state(self.protocol, self.case)
                    scene.return_value.step.side_effect = error
                    with self.assertRaises(type(error)):
                        run_case(self.protocol, self.case, target)
                    scene.return_value.close.assert_called_once()
                meta = json.loads((target / 'metadata.json').read_text())
                self.assertEqual(meta['completed_steps'], 0)
                self.assertEqual(meta['attempted_steps'], 1)
                self.assertIn(type(error).__name__, meta['error'])
                with np.load(target / 'trace.npz') as trace:
                    self.assertEqual(trace['states'].shape, (1, 14))
                    self.assertEqual(trace['forces'].shape, (0, 3))

    def test_runtime_requires_official_payload_and_actual_compiler_readback(self):
        proof = json.loads((ROOT / 'official-proof.json').read_text())
        runtime = json.loads((ROOT / 'runtime-example.json').read_text())
        validate_runtime(self.protocol, proof, runtime)
        for kind in ('hash', 'threads', 'precision', 'version'):
            bad = copy.deepcopy(runtime)
            if kind == 'hash':
                bad['mapped_native'] = {}
            elif kind == 'threads':
                bad['compiler']['cpu_max_num_threads'] = 4
            elif kind == 'precision':
                bad['precision'] = 'float32'
            else:
                bad['packages']['genesis-world']['version'] = '1.4.2'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_runtime(self.protocol, proof, bad)


if __name__ == '__main__':
    unittest.main()
