"""Reject a stale or relabelled controller record independently of its hashes."""

from copy import deepcopy
import unittest

import numpy as np

from dexlab.libero_initialization import INITIALIZATION_CONTRACT
from dexlab.libero_score_v2 import _controller_initialization


class LiberoControllerRecordTests(unittest.TestCase):
    def setUp(self):
        self.model = {'dimensions': {'nq': 7, 'nv': 7, 'nsite': 1},
                      'names': {'joint': [f'robot0_joint{i}' for i in range(1, 8)],
                                'site': ['gripper0_grip_site']},
                      'arrays': {'jnt_type': [3] * 7, 'jnt_qposadr': list(range(7)),
                                 'jnt_dofadr': list(range(7))}}
        state = np.r_[.25, np.arange(7) / 10, np.arange(7) / 100].tolist()
        after = {'joint_pos': state[1:8], 'joint_vel': state[8:], 'initial_joint': [0.] * 7,
                 'ee_pos': [1., 2., 3.], 'ee_ori_mat': np.eye(3).tolist(),
                 'goal_pos': [1., 2., 3.], 'goal_ori': np.eye(3).tolist(),
                 'gripper_current_action': [0.], 'new_update': False}
        before = dict(deepcopy(after), joint_pos=[0.] * 7, joint_vel=[0.] * 7,
                      ee_pos=[0.] * 3, goal_pos=[0.] * 3)
        self.init = {'contract': INITIALIZATION_CONTRACT, 'after_forward': state,
                     'after_controller_goals': state,
                     'controller': {'name': 'OSC_POSE', 'joint_ids': list(range(7)),
                         'qpos_indices': list(range(7)), 'qvel_indices': list(range(7)), 'eef_site_id': 0,
                         'before': before, 'after': after,
                         'native_after': {key: deepcopy(after[key]) for key in
                                          ('joint_pos', 'joint_vel', 'ee_pos', 'ee_ori_mat')}}}
        self.run = {'initialization_contract': INITIALIZATION_CONTRACT}
        self.expected = dict(self.run)

    def check(self):
        _controller_initialization(self.init, self.run, self.expected, self.model)

    def test_synchronized_cache_and_explicit_retained_history_are_accepted(self):
        self.check()

    def test_coherently_changed_cache_and_native_readback_still_fail_against_initial_state(self):
        for key in ('joint_pos', 'joint_vel'):
            with self.subTest(channel=key):
                original = deepcopy(self.init)
                self.init['controller']['after'][key][0] += .1
                self.init['controller']['native_after'][key][0] += .1
                with self.assertRaisesRegex(ValueError, 'restored.*cache'):
                    self.check()
                self.init = original

    def test_stale_goal_or_changed_nullspace_or_gripper_history_is_rejected(self):
        for key in ('goal_pos', 'goal_ori', 'initial_joint', 'gripper_current_action'):
            with self.subTest(channel=key):
                original = deepcopy(self.init)
                value = np.asarray(self.init['controller']['after'][key]); value.flat[0] += .1
                self.init['controller']['after'][key] = value.tolist()
                with self.assertRaises(ValueError):
                    self.check()
                self.init = original

    def test_wrong_arm_or_site_and_nonfinite_memory_are_rejected(self):
        changes = [lambda c: c.update(qpos_indices=list(reversed(range(7)))),
                   lambda c: c.update(joint_ids=[True] * 7),
                   lambda c: c.update(eef_site_id=3),
                   lambda c: c['after'].update(new_update=True),
                   lambda c: c['before']['ee_pos'].__setitem__(0, float('nan'))]
        for change in changes:
            original = deepcopy(self.init); change(self.init['controller'])
            with self.assertRaises(ValueError):
                self.check()
            self.init = original

    def test_legacy_records_cannot_claim_the_new_contract(self):
        _controller_initialization({}, {}, {}, self.model)
        for init, run in ((self.init, {}), ({}, self.run)):
            with self.assertRaisesRegex(ValueError, 'Historical'):
                _controller_initialization(init, run, {}, self.model)
        for contract in (None, 'unknown'):
            with self.assertRaises(ValueError):
                _controller_initialization(self.init, self.run, {'initialization_contract': contract}, self.model)


if __name__ == '__main__':
    unittest.main()
