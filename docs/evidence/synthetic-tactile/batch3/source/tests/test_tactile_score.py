import unittest
import numpy as np
from dexlab.tactile_score import evaluate, PATHS


def fixture():
    record = {'completed': True, 'case': dict(mass=.2, half_size=.02, friction=.3, gravity=9.81, timestep=.0005, initial_speed=0., duration=3., settle=0.), 'runs': []}
    arrays = {}
    for resolution in (32, 64):
        for path in PATHS:
            name = f'{resolution}-{path}'
            record['runs'].append(dict(name=name, path=path, resolution=resolution, contact_distances_m=[[0.]] * 6000))
            arrays[name] = dict(pose=np.tile([0, 0, .02, 1, 0, 0, 0], (6001, 1)), velocity=np.zeros((6001, 6)), force=np.tile([0, 0, 1.962], (6000, 1)), command=np.zeros((6000, 6)), warnings=np.zeros((6000, 8)), maps=np.zeros((150, resolution, resolution)), map_stats=np.zeros((6000, 3)))
            if path == 'slide-return':
                arrays[name]['pose'][2000, 0] = .02
            if path == 'detach-recontact':
                arrays[name]['pose'][2000, 2] = .035
    return record, arrays


class ScoreTests(unittest.TestCase):
    def test_synthetic_shapes_and_invariance(self):
        # Synthetic samples exercise scorer branches, not native dynamics.
        self.assertTrue(evaluate(*fixture())['passed'])

    def test_unexecuted_detachment_fails(self):
        record, arrays = fixture()
        for r in (32, 64):
            arrays[f'{r}-detach-recontact']['pose'][:, 2] = .02
        self.assertFalse(evaluate(record, arrays)['passed'])

    def test_observation_changes_physics_rejected(self):
        record, arrays = fixture()
        arrays['64-direct']['velocity'][2, 0] = .001
        self.assertFalse(evaluate(record, arrays)['passed'])

    def test_reset_contamination_rejected(self):
        record, arrays = fixture()
        arrays['32-reset-direct']['pose'][-1, 0] = .002
        self.assertFalse(evaluate(record, arrays)['passed'])

    def test_sensor_cannot_replace_force(self):
        record, arrays = fixture()
        arrays['32-direct']['force'][:] = 0
        self.assertFalse(evaluate(record, arrays)['passed'])

    def test_missing_or_nonunit_invalid(self):
        record, arrays = fixture()
        arrays['32-direct']['pose'] = arrays['32-direct']['pose'][:-1]
        self.assertFalse(evaluate(record, arrays)['valid'])
        record, arrays = fixture()
        arrays['32-direct']['pose'][0, 3] = 2
        self.assertFalse(evaluate(record, arrays)['valid'])
