import unittest
from dexlab.genesis_joint_score import score_trial


class JointScoreTests(unittest.TestCase):
    def record(self):
        return {'armature_profile': 'zero', 'response': 'default', 'limits_enabled': True,
                'initial_readback': {'get_links_mass': [0., .1], 'get_dofs_armature': [0.],
                    'get_mass_mat': [[.1]], 'get_dofs_damping': [0.], 'get_dofs_kp': [100.],
                    'get_dofs_kv': [10.], 'get_dofs_limit': [[0.], [.05]],
                    'get_dofs_force_range': [[-5.], [5.]], 'get_dofs_position': [.025],
                    'joint_sol_params': [.01, 1., .9, .95, .001, .5, 2.]},
                'samples': [{'step': i+1, 'q_m': .025, 'v_m_s': 0., 'generalized_force_N': 0.} for i in range(500)]}

    def test_hidden_armature_fails_model_even_if_limit_passes(self):
        record = self.record()
        record['initial_readback']['get_dofs_armature'] = [.1]
        result = score_trial(record)
        self.assertFalse(result['import_passed'])
        self.assertTrue(result['limit_criterion_passed'])

    def test_transient_not_hidden_by_final_sample(self):
        record = self.record()
        record['samples'][10]['q_m'] = -.002
        self.assertFalse(score_trial(record)['limit_criterion_passed'])

    def test_missing_sample_rejected(self):
        record = self.record()
        record['samples'].pop()
        with self.assertRaises(ValueError): score_trial(record)

    def test_nonfinite_rejected(self):
        record = self.record()
        record['samples'][8]['v_m_s'] = float('nan')
        with self.assertRaises(ValueError): score_trial(record)
