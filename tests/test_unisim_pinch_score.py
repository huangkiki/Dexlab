import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('score_unisim', Path(__file__).resolve().parents[1] / 'scripts/score_unisim_pinch.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ScoreTests(unittest.TestCase):
    def test_truncated_trace_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            module.score_trial({'initial': {}, 'samples': []}, {'initial': {}, 'samples': []})

    def test_wrong_command_rejected_before_metric_aggregation(self):
        candidate = {'initial': {'cube_link': 1, 'pad_links': [2, 3], 'plane_link': 0},
                     'samples': [{'time': .0005, 'command': [0, 0, 0]}] * 8000}
        reference = {'initial': {}, 'samples': [{'time': .0005, 'command': [0, 1, 0]}] * 8000}
        with self.assertRaisesRegex(ValueError, 'command'):
            module.score_trial(candidate, reference)

    def test_full_trace_and_corruption_detection(self):
        import copy
        from dexlab.adapter_qualification import INITIAL_FIELDS

        initial = {name: [0.] for name in INITIAL_FIELDS}
        initial.update(options={}, cube_link=1, plane_link=0, pad_links=[2, 3],
                       adapter_reset_sensors={'left_force': [[0., 0., 0.]]})
        reference_row = dict(command=[0., 0., 0.], q=[0., 0., 0.],
                             object_pos=[0., 0., .02], object_vel=[0., 0., 0.],
                             object_quat=[1., 0., 0., 0.],
                             object_contact_force=[[0., 0., 1.]])
        candidate_row = dict(reference_row,
            adapter_state={'root_pose': [[0., 0., .02, 1., 0., 0., 0.]],
                           'root_velocity': [[0.] * 6]},
            adapter_forces={'left_force': [[0., 0., 1.]],
                            'right_force': [[0., 0., 0.]], 'ground_force': [[0., 0., 0.]]},
            contacts={'link_a': [[2]], 'link_b': [[1]], 'valid_mask': [[True]],
                      'force_a': [[[0., 0., -1.]]], 'force_b': [[[0., 0., 1.]]]})
        reference = {'initial': initial, 'samples': [dict(reference_row, time=(i+1)*.0005) for i in range(8000)]}
        candidate = {'initial': copy.deepcopy(initial), 'samples': [dict(candidate_row, time=(i+1)*.0005) for i in range(8000)]}
        self.assertTrue(module.score_trial(candidate, reference)['passed'])
        candidate['samples'][12] = copy.deepcopy(candidate['samples'][12])
        candidate['samples'][12]['adapter_forces']['left_force'][0][2] = 2.
        self.assertIn('public_force', module.score_trial(candidate, reference)['failures'])
        candidate['samples'][12] = dict(candidate_row, time=13*.0005)
        candidate['initial']['adapter_reset_sensors']['left_force'][0][0] = 1.
        self.assertIn('stale_reset_contact', module.score_trial(candidate, reference)['failures'])
