"""Adversarial checks over independently verifiable native-record fields."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory

import numpy as np

from dexlab.drake_incline_score import initial_state, validate_admission, validate_runtime, validate_trace


ROOT = Path(__file__).resolve().parents[1] / 'docs/evidence/drake-incline'


class DrakeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((ROOT / 'protocol-v1.json').read_text())
        self.case = self.protocol['cases'][1]
        self.admission = json.loads((ROOT / 'admission-example.json').read_text())

    def test_native_zero_duration_readbacks(self):
        validate_admission(self.protocol, self.case, self.admission)

    def test_clearance_is_explicit_and_verified(self):
        protocol = dict(self.protocol, initial_clearance_m=1e-6)
        with self.assertRaisesRegex(ValueError, 'initial state'):
            validate_admission(protocol, self.case, self.admission)
        admission = copy.deepcopy(self.admission)
        admission['state'] = initial_state(protocol, self.case).tolist()
        validate_admission(protocol, self.case, admission)

    def test_interrupts_preserve_partial_trace_and_error(self):
        from dexlab.drake_incline import run_case

        for error in (SystemExit(1), KeyboardInterrupt(), RuntimeError('native failure')):
            with self.subTest(error=type(error).__name__), TemporaryDirectory() as directory:
                destination = Path(directory) / 'case'
                with patch('dexlab.drake_incline.DrakeIncline') as scene:
                    scene.return_value.admission = self.admission
                    scene.return_value.state.return_value = initial_state(self.protocol, self.case)
                    scene.return_value.step.side_effect = error
                    with self.assertRaises(type(error)):
                        run_case(self.protocol, self.case, destination)
                meta = json.loads((destination / 'metadata.json').read_text())
                self.assertEqual(meta['completed_steps'], 0)
                self.assertIn(type(error).__name__, meta['error'])
                with np.load(destination / 'trace.npz') as trace:
                    self.assertEqual(trace['states'].shape, (1, 14))
                    self.assertEqual(trace['forces'].shape, (0, 3))

    def test_overwritten_friction_mass_frame_clock_and_solver_are_rejected(self):
        mutations = [lambda a: a.update(mass=.065), lambda a: a.update(solver='kTamsi'),
                     lambda a: a.update(sampled_output=False), lambda a: a.update(timestep=.002),
                     lambda a: a['com'].__setitem__(0, .001),
                     lambda a: a['cube_dimensions'].__setitem__(0, .041),
                     lambda a: a['plane_pose_in_world'][0].__setitem__(2, -.258819),
                     lambda a: a['cube_properties']['material']['coulomb_friction'].update(dynamic=.4),
                     lambda a: a['plane_properties']['hydroelastic'].update(hydroelastic_modulus=1e6)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                admission = copy.deepcopy(self.admission)
                mutate(admission)
                with self.assertRaises(ValueError):
                    validate_admission(self.protocol, self.case, admission)

    def stationary_trace(self):
        protocol = dict(self.protocol, duration_s=.003)
        states = np.tile(initial_state(protocol, self.case), (4, 1))
        states[:, 0] = [0, .001, .002, .003]
        force = [0, 0, protocol['mass_kg'] * protocol['gravity_m_s2']]
        trace = dict(states=states, forces=np.tile(force, (3, 1)),
                     generalized_contact_forces=np.tile([0, 0, 0, *force], (3, 1)),
                     contact_count=np.ones(3), force_times=np.array([0, .001, .002]))
        rows = [dict(interval_start_s=i * .001, interval_end_s=(i + 1) * .001,
                     contacts=[dict(force_on_cube_world=force, torque_on_cube_at_centroid_world=[0, 0, 0],
                                    centroid_world=[0, 0, 0], area_m2=.0016)]) for i in range(3)]
        return protocol, trace, rows

    def test_stationary_ledger_is_consistent(self):
        protocol, trace, rows = self.stationary_trace()
        validate_trace(protocol, self.case, trace, rows)

    def test_force_epoch_shift_is_rejected(self):
        protocol, trace, rows = self.stationary_trace()
        trace['force_times'] += .001
        with self.assertRaisesRegex(ValueError, 'force epoch'):
            validate_trace(protocol, self.case, trace, rows)

    def test_lost_contact_and_wrong_force_sign_are_rejected(self):
        for lost in (True, False):
            protocol, trace, rows = self.stationary_trace()
            if lost:
                rows[1]['contacts'] = []
            else:
                rows[1]['contacts'][0]['force_on_cube_world'] = [0, 0, -.62784]
            with self.assertRaises(ValueError):
                validate_trace(protocol, self.case, trace, rows)

    def test_injected_state_reset_contamination_and_truncation_are_rejected(self):
        for kind in ('injected', 'reset', 'truncated', 'nan'):
            protocol, trace, rows = self.stationary_trace()
            if kind == 'injected':
                trace['states'][2:, 1] += .001
            elif kind == 'reset':
                trace['states'][0, 8] = .01
            elif kind == 'truncated':
                trace['states'] = trace['states'][:-1]
            else:
                trace['forces'][1, 0] = np.nan
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_trace(protocol, self.case, trace, rows)

    def test_core_and_binding_cannot_be_inferred_from_version_label(self):
        proof = json.loads((ROOT / 'official-proof.json').read_text())
        native = next(name for name in proof['native_files'] if Path(name).name == 'libdrake.so')
        runtime = dict(native_version_file=proof['native_version_file'],
                       package=dict(version=proof['version'], code_sha256=proof['package_code_sha256'], record_verified=True),
                       loaded_files={native: proof['native_files'][native]}, precision='float64', engine_patches=False)
        validate_runtime(self.protocol, proof, runtime)
        for key in ('native_version_file', 'loaded_files', 'package'):
            invalid = copy.deepcopy(runtime)
            if key == 'native_version_file':
                invalid[key] = '1.57.0 different-build'
            elif key == 'loaded_files':
                invalid[key] = {native: '0' * 64}
            else:
                invalid[key]['code_sha256'] = '0' * 64
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_runtime(self.protocol, proof, invalid)


if __name__ == '__main__':
    unittest.main()
