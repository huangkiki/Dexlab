"""Complete native action loops must retain every goal and restore hooks."""

from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.libero_execute import execute_actions
import test_libero_goals as goal_fixtures


class NativeFixture(goal_fixtures.NativeFixture):
    def __init__(self):
        super().__init__((True, True))
        self.visualization_sites_list = ['stove']
        self.count = 0
        self.state = np.zeros(4)
        self.sim.data.ctrl = np.zeros(2)
        self.sim.data.actuator_force = np.zeros(2)
        self.sim.data.qfrc_actuator = np.zeros(4)
        self.sim.data._data = SimpleNamespace(xpos=np.zeros((2, 3)), xquat=np.zeros((2, 4)),
                                             xipos=np.zeros((2, 3)))
        self.sim.model = SimpleNamespace(_model=SimpleNamespace(site_rgba=np.zeros((1, 4))))
        self.sim.get_state = lambda: SimpleNamespace(flatten=lambda: np.r_[self.sim.data.time, self.state])

    def get_object(self, name):
        return SimpleNamespace(object_properties={'vis_site_names': self.marker})

    def step(self, action):
        self.count += 1
        self.sim.data.time += .05
        self.state += action[:4]
        self.sim.data.ctrl[:] = action[:2]
        self.sim.data.actuator_force[:] = 2 * action[:2]
        self.sim.data.qfrc_actuator[:] = 2 * action[:4]
        reward = float(self._check_success())
        done = self._check_success()
        return {'position': self.state.copy()}, reward, done, {}


class LiberoExecuteTests(unittest.TestCase):
    def run_actions(self, env=None, recording=True, actions=None):
        env = env or NativeFixture()
        actions = np.ones((4, 7)) if actions is None else actions
        rows, events, markers = {}, [], []
        execute_actions(env, actions, goal_fixtures.DEFINITION, recording=recording,
                        rows=rows, events=events, markers=markers)
        return env, rows, events, markers

    def test_success_never_truncates_actions_and_every_existing_goal_is_captured(self):
        env, rows, events, markers = self.run_actions()
        self.assertEqual(env.count, 4)
        self.assertEqual(len(rows['state']), 4)
        self.assertTrue(all(rows['done']))
        self.assertEqual(len(events), 8)
        self.assertEqual(len(env.calls), 16)
        self.assertEqual(len(markers), 4)
        np.testing.assert_array_equal(rows['goal_event_range'], [[0, 2], [2, 4], [4, 6], [6, 8]])
        self.assertNotIn('_check_success', env.__dict__)

    def test_observer_switch_does_not_change_actions_state_or_native_queries(self):
        off, off_rows, off_events, off_markers = self.run_actions(recording=False)
        on, on_rows, on_events, on_markers = self.run_actions()
        self.assertEqual(off.calls, on.calls)
        self.assertEqual(off_events, [])
        self.assertEqual(len(on_events), 8)
        self.assertEqual(off_markers, on_markers)
        for key in off_rows.keys() - {'goal_event_range'}:
            np.testing.assert_array_equal(off_rows[key], on_rows[key])

    def test_native_action_mutation_does_not_change_the_admitted_actions(self):
        env = NativeFixture(); step = env.step
        def mutates(action):
            result = step(action)
            action[:] = 0
            return result
        env.step = mutates
        actions = np.ones((4, 7))
        _, rows, _, _ = self.run_actions(env, actions=actions)
        np.testing.assert_array_equal(actions, np.ones((4, 7)))
        np.testing.assert_array_equal(rows['actions'], actions)

    def test_failed_goal_keeps_trace_and_completed_prefix_and_restores_hooks(self):
        env = NativeFixture(); original = env._eval_predicate
        def raises(atom):
            if env.count == 2:
                raise RuntimeError('fixture failure')
            return original(atom)
        env._eval_predicate = raises
        rows, events, markers = {}, [], []
        with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
            execute_actions(env, np.ones((4, 7)), goal_fixtures.DEFINITION, recording=True,
                            rows=rows, events=events, markers=markers)
        self.assertEqual(len(rows['actions']), 1)
        self.assertEqual(events[-1]['status'], 'failed')
        self.assertEqual(len(events), 3)
        self.assertIs(env._eval_predicate, raises)
        self.assertNotIn('_check_success', env.__dict__)

    def test_missing_queries_inconsistent_done_or_channels_are_rejected(self):
        for mode in ('missing', 'done', 'channels'):
            env = NativeFixture(); step = env.step
            def changed(action):
                if mode == 'missing':
                    env.sim.data.time += .05
                    return {}, 0., False, {}
                obs, reward, done, info = step(action)
                if mode == 'done':
                    done = False
                elif env.count == 2:
                    obs = {}
                return obs, reward, done, info
            env.step = changed
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.run_actions(env)

    def test_empty_wrong_shape_nonfinite_and_integer_actions_are_rejected(self):
        for actions in (np.zeros((0, 7)), np.zeros((2, 6)), np.full((2, 7), np.nan),
                        np.ones((2, 7), dtype=int)):
            env = NativeFixture()
            with self.subTest(shape=actions.shape), self.assertRaises(ValueError):
                self.run_actions(env, actions=actions)
            self.assertEqual(env.count, 0)


if __name__ == '__main__':
    unittest.main()
