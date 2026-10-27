"""Do not compare geometry errors over different contact-pair sets."""

import copy
import unittest

import numpy as np

from dexlab.landing_report import actuator_summary, distance_summary


class LandingReportTests(unittest.TestCase):
    def test_disabled_zero_ranges_do_not_become_saturation_and_joint_dof_is_used(self):
        native = {'qfrc_actuator': np.array([[0., 9., -5.], [0., 9., 5.], [0., 9., 6.]])}
        metadata = {'joint_actuatorfrclimited': [False, True], 'joint_type': [0, 3],
                    'joint_dofadr': [0, 2], 'joint_actuatorfrcrange': [[0, 0], [-5, 5]],
                    'joint_names': ['root', 'hinge'], 'actuator_forcelimited': [False],
                    'actuator_ctrllimited': [False]}
        result = actuator_summary(native, metadata)
        self.assertEqual(len(result['joints']), 1)
        self.assertEqual(result['joints'][0]['samples_exactly_at_bound'], 2)
        self.assertEqual(result['joints'][0]['samples_outside_declared_range'], 1)
        self.assertEqual(result['individual_actuator_force_limits_enabled'], 0)
        self.assertIn('unavailable', result['native_gpu_clamp_branch'])

    def row(self):
        return {'pre': {'common_pairs': 1, 'native_only_pairs': [],
                        'max_distance_error_m': 1e-7, 'nonfoot_penetration_m': 0},
                'post': {'common_pairs': 1, 'native_only_pairs': [],
                         'max_distance_error_m': .01, 'nonfoot_penetration_m': 0},
                'native_nonfoot_active': 0, 'native_nonfoot_loaded': 0}

    def test_different_common_pairs_are_excluded_without_dropping_contact_events(self):
        comparable = self.row()
        different = copy.deepcopy(comparable)
        different['post']['native_only_pairs'] = [[0, 2]]
        different['post']['common_pairs'] = 0
        different['post']['max_distance_error_m'] = None
        different['post']['nonfoot_penetration_m'] = .003
        different['native_nonfoot_loaded'] = 2
        result = distance_summary([comparable, different])
        self.assertEqual(result['complete_substeps'], 2)
        self.assertEqual(result['same_common_native_pair_set_substeps'], 1)
        self.assertEqual(result['pre_closer_substeps'], 1)
        self.assertEqual(result['post_nonfoot_penetration_samples'], 1)
        self.assertEqual(result['native_nonfoot_loaded_samples'], 1)

    def test_empty_contact_windows_do_not_become_zero_error_evidence(self):
        empty = self.row()
        for epoch in ('pre', 'post'):
            empty[epoch]['common_pairs'] = 0
            empty[epoch]['max_distance_error_m'] = None
        result = distance_summary([empty])
        self.assertEqual(result['same_common_native_pair_set_substeps'], 0)
        self.assertIsNone(result['max_pre_distance_error_m'])
        self.assertIsNone(result['max_post_distance_error_m'])


if __name__ == '__main__':
    unittest.main()
