"""Analytical shared grids and confounds must remain distinguishable."""
import copy
import unittest
from dataclasses import replace
import numpy as np
from dexlab.contact_plane import PlaneCase
from dexlab.contact_refinement import compare_grids, matching_profiles


def record(case, error=0):
    t = np.arange(case.steps + 1) * case.timestep
    p = np.zeros((len(t), 7))
    p[:, 3] = 1
    p[:, 2] = case.half_size
    p[:, 0] = case.initial_speed*t + error*t
    v = np.zeros((len(t), 6))
    v[:, 0] = case.initial_speed
    return {'time': t, 'pose': p, 'velocity': v}


class RefinementTests(unittest.TestCase):
    def setUp(self):
        self.a = PlaneCase(timestep=.001, settle=0, duration=.004)
        self.b = replace(self.a, timestep=.0005)

    def test_exact_motion_agrees_on_shared_times(self):
        r = compare_grids(self.a, record(self.a), self.b, record(self.b))
        self.assertTrue(r['comparable'])
        self.assertEqual(r['metrics']['shared_samples'], 5)
        self.assertEqual(r['metrics']['maximum_position_m'], 0)

    def test_known_difference_has_expected_max_and_rms(self):
        r = compare_grids(self.a, record(self.a, error=.01), self.b, record(self.b))
        self.assertAlmostEqual(r['metrics']['maximum_position_m'], .00004)
        self.assertAlmostEqual(r['metrics']['rms_position_m'], np.sqrt(6)*1e-5)

    def test_different_settled_height_is_not_integration_error(self):
        b = record(self.b)
        b['pose'][:, 2] += 1e-5
        self.assertEqual(compare_grids(self.a, record(self.a), self.b, b)['reason'],
                         'observed_initial_state_mismatch')

    def test_physical_parameter_change_is_rejected(self):
        b = replace(self.b, friction=.5)
        self.assertFalse(compare_grids(self.a, record(self.a), b, record(b))['comparable'])

    def test_missing_nonfinite_and_corrupt_time_are_rejected(self):
        for key in ('time', 'pose', 'velocity'):
            b=record(self.b)
            b[key]=b[key][:-1]
            self.assertFalse(compare_grids(self.a, record(self.a), self.b, b)['comparable'])
        b=record(self.b)
        b['time'][1]=b['time'][0]
        self.assertFalse(compare_grids(self.a, record(self.a), self.b, b)['comparable'])
        b=record(self.b)
        b['velocity'][2,0]=np.nan
        self.assertFalse(compare_grids(self.a, record(self.a), self.b, b)['comparable'])

    def test_quaternion_sign_does_not_change_orientation(self):
        b=record(self.b)
        b['pose'][:,3:]*=-1
        r=compare_grids(self.a,record(self.a),self.b,b)
        self.assertTrue(r['comparable'])
        self.assertEqual(r['metrics']['maximum_orientation_rad'],0)

    def test_equal_grid_is_not_a_refinement(self):
        self.assertFalse(compare_grids(self.a,record(self.a),self.a,record(self.a))['comparable'])


class NativeProfileTests(unittest.TestCase):
    def test_missing_changed_source_and_changed_solver_are_rejected(self):
        native = dict(identity={'version': 'test'}, mass_readback=.2,
                      inertia_readback=[1, 1, 1], friction_readback=[.3, .3],
                      normal_parameters_readback={'stiffness': 1},
                      solver={'iterations': 100}, geometry_readback={'type': [0, 6]})
        left = {'engine': 'mujoco', 'source_sha256': {'source.py': 'frozen'}, 'native': native}
        self.assertTrue(matching_profiles(left, copy.deepcopy(left)))
        for field in native:
            right = copy.deepcopy(left)
            del right['native'][field]
            self.assertFalse(matching_profiles(left, right), field)
        right = copy.deepcopy(left)
        right['native']['solver']['iterations'] = 50
        self.assertFalse(matching_profiles(left, right))
        right = copy.deepcopy(left)
        right['source_sha256']['source.py'] = 'changed'
        self.assertFalse(matching_profiles(left, right))


class ArchiveSeparationTests(unittest.TestCase):
    """Physical failure must survive a valid numerical comparison."""

    def test_comparable_physical_failure_is_not_upgraded(self):
        import json
        import tempfile
        from dataclasses import asdict
        from pathlib import Path
        from unittest.mock import patch
        from dexlab.contact_refinement import compare_archives

        checks = dict.fromkeys((
            'native_run_completed', 'source_unchanged',
            'archived_source_hashes_match', 'clean_shutdown', 'declared_limits',
            'artifact_hashes_match', 'contact_ledger_matches'), True)
        checks['momentum_balance'] = False
        score = {'passed': False, 'checks': checks}
        coarse = PlaneCase(timestep=.001, settle=0, duration=.004)
        fine = replace(coarse, timestep=.0005)
        with tempfile.TemporaryDirectory() as temporary:
            paths = [Path(temporary) / name for name in ('coarse', 'fine')]
            for path, case in zip(paths, (coarse, fine)):
                path.mkdir()
                (path / 'run.json').write_text(json.dumps({'case': asdict(case)}))
                np.savez(path / 'states.npz', **record(case))
            with patch('dexlab.contact_plane_native.verify', return_value=score), patch(
                'dexlab.contact_refinement.matching_profiles', return_value=True
            ):
                result = compare_archives(*paths)
                self.assertTrue(result['comparable'])
                self.assertEqual(result['physical_passed'], [False, False])
                checks['artifact_hashes_match'] = False
                rejected = compare_archives(*paths)
                self.assertFalse(rejected['comparable'])
                self.assertEqual(rejected['reason'], 'untrusted_archive')

    def test_null_native_profile_is_not_a_match(self):
        metadata = {'engine': 'mujoco', 'source_sha256': {'a.py': 'same'}, 'native': None}
        self.assertFalse(matching_profiles(metadata, metadata))


class SolverComparisonTests(unittest.TestCase):
    def test_solver_comparison_requires_fixed_time_grid(self):
        case = PlaneCase(timestep=.001, settle=0, duration=.004)
        fine = replace(case, timestep=.0005)
        self.assertTrue(compare_grids(case, record(case), case, record(case), same_grid=True)['comparable'])
        self.assertFalse(compare_grids(case, record(case), fine, record(fine), same_grid=True)['comparable'])

    def test_solver_change_cannot_hide_contact_or_integrator_change(self):
        native = {
            'identity': {'version': 'test'}, 'mass_readback': .2,
            'inertia_readback': [1, 1, 1], 'friction_readback': [.3, .3],
            'normal_parameters_readback': {'stiffness': 1},
            'solver': {'iterations': 100, 'tolerance': 1e-8, 'integrator': 0},
            'geometry_readback': {'type': [0, 6]},
        }
        left = {'engine': 'mujoco', 'source_sha256': {'source.py': 'same'}, 'native': native}
        right = copy.deepcopy(left)
        self.assertFalse(matching_profiles(left, right, varying_solver=True))
        right['native']['solver']['tolerance'] = 1e-10
        self.assertTrue(matching_profiles(left, right, varying_solver=True))
        for key, value in (('integrator', 1), ('new_unknown_field', 0)):
            invalid = copy.deepcopy(right)
            invalid['native']['solver'][key] = value
            self.assertFalse(matching_profiles(left, invalid, varying_solver=True))
        right['native']['friction_readback'] = [.5, .5]
        self.assertFalse(matching_profiles(left, right, varying_solver=True))
