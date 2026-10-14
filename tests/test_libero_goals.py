"""Goal logging must preserve native query side effects and reject lost goals."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.libero_goals import goal_atoms, record_goal_queries


DEFINITION = {
    "objects": {"pot": "moka_pot"}, "fixtures": {"stove": "flat_stove"},
    "regions": {"stove_top": {"target": "stove", "target_declared": True}},
    "goal": ["and", ["turnon", "stove"], ["on", "pot", "stove_top"]],
}


class NativeFixture:
    def __init__(self, values=(False, True)):
        self.parsed_problem = {"goal_state": deepcopy(DEFINITION["goal"][1:])}
        self.sim = SimpleNamespace(data=SimpleNamespace(time=1.5))
        self.values = values
        self.calls = []
        self.marker = None

    def _eval_predicate(self, state):
        self.calls.append(deepcopy(state))
        self.marker = state[0]
        return self.values[self.parsed_problem["goal_state"].index(state)]

    def _check_success(self):
        result = True
        for state in self.parsed_problem["goal_state"]:
            result = self._eval_predicate(state) and result
        return result


class LiberoGoalTests(unittest.TestCase):
    def test_recording_preserves_calls_results_time_and_side_effects(self):
        for values in ((False, True), (True, False), (True, True),
                       (np.bool_(True), np.bool_(False))):
            with self.subTest(values=values):
                plain, recorded = NativeFixture(values), NativeFixture(values)
                baseline = [plain._check_success(), plain._check_success()]
                with record_goal_queries(recorded, DEFINITION) as records:
                    actual = [recorded._check_success(), recorded._check_success()]
                self.assertEqual(actual, baseline)
                self.assertEqual(recorded.calls, plain.calls)
                self.assertEqual(recorded.marker, plain.marker)
                self.assertEqual(recorded.sim.data.time, plain.sim.data.time)
                self.assertEqual(len(records), 2)
                self.assertEqual([q["value"] for q in records[0]["queries"]], list(values))
                self.assertEqual(records[1]["check_index"], 1)
                self.assertTrue(all(r["status"] == "completed" for r in records))
                self.assertNotIn("_check_success", recorded.__dict__)
                self.assertNotIn("_eval_predicate", recorded.__dict__)

    def test_no_success_query_is_added_by_opening_or_closing_recorder(self):
        env = NativeFixture()
        with record_goal_queries(env, DEFINITION) as records:
            pass
        self.assertEqual(records, [])
        self.assertEqual(env.calls, [])

    def test_direct_predicate_calls_remain_unmodified_and_are_not_success(self):
        env = NativeFixture()
        with record_goal_queries(env, DEFINITION) as records:
            self.assertFalse(env._eval_predicate(DEFINITION["goal"][1]))
        self.assertEqual(len(env.calls), 1)
        self.assertEqual(records, [])

    def test_dropped_secondary_goal_fails_and_keeps_partial_trace(self):
        env = NativeFixture()
        env._check_success = lambda: env._eval_predicate(env.parsed_problem["goal_state"][0])
        original = env._check_success
        with record_goal_queries(env, DEFINITION) as records:
            with self.assertRaisesRegex(ValueError, "omitted"):
                env._check_success()
        self.assertEqual(records[0]["status"], "failed")
        self.assertEqual(len(records[0]["queries"]), 1)
        self.assertIs(env._check_success, original)

    def test_reordered_or_duplicated_queries_are_rejected(self):
        for indices in ((1, 0), (0, 0), (0, 1, 1)):
            env = NativeFixture((True, True))
            def changed():
                return all([env._eval_predicate(env.parsed_problem["goal_state"][i]) for i in indices])
            env._check_success = changed
            with record_goal_queries(env, DEFINITION) as records:
                with self.assertRaisesRegex(ValueError, "order or arguments"):
                    env._check_success()
            self.assertEqual(records[0]["status"], "failed")

    def test_declaration_mutation_during_query_is_rejected(self):
        env = NativeFixture((True, True))
        native = env._check_success
        def mutates():
            result = native()
            env.parsed_problem["goal_state"][-1][1] = "wrong_object"
            return result
        env._check_success = mutates
        with record_goal_queries(env, DEFINITION) as records:
            with self.assertRaisesRegex(ValueError, "changed during"):
                env._check_success()
        self.assertEqual(records[0]["status"], "failed")

    def test_external_hook_removal_is_rejected_and_class_methods_restored(self):
        env = NativeFixture()
        with self.assertRaisesRegex(ValueError, "hooks changed"):
            with record_goal_queries(env, DEFINITION):
                del env._eval_predicate
        self.assertNotIn("_check_success", env.__dict__)
        self.assertNotIn("_eval_predicate", env.__dict__)

    def test_changed_native_declaration_rejected_before_query(self):
        env = NativeFixture()
        with record_goal_queries(env, DEFINITION) as records:
            env.parsed_problem["goal_state"].pop()
            with self.assertRaisesRegex(ValueError, "changed after"):
                env._check_success()
        self.assertEqual(env.calls, [])
        self.assertEqual(records[0]["status"], "failed")
        with self.assertRaisesRegex(ValueError, "differ"):
            with record_goal_queries(env, DEFINITION):
                pass

    def test_native_exception_is_retained_and_original_hooks_restored(self):
        env = NativeFixture()
        def broken(state):
            raise RuntimeError("native failure")
        env._eval_predicate = broken
        with self.assertRaisesRegex(RuntimeError, "native failure"):
            with record_goal_queries(env, DEFINITION) as records:
                env._check_success()
        self.assertIs(env._eval_predicate, broken)
        self.assertNotIn("_check_success", env.__dict__)
        self.assertEqual(records[0]["error_type"], "RuntimeError")

    def test_boolean_result_is_not_inferred_from_numbers_or_missing_values(self):
        for value in (None, 0, 1, float("nan"), "true", np.array([True])):
            env = NativeFixture((value, True))
            with record_goal_queries(env, DEFINITION) as records:
                with self.assertRaisesRegex(ValueError, "booleans"):
                    env._check_success()
            self.assertEqual(records[0]["status"], "failed")

    def test_native_success_must_match_every_predicate(self):
        env = NativeFixture()
        native = env._check_success
        def inconsistent():
            native()
            return True
        env._check_success = inconsistent
        with record_goal_queries(env, DEFINITION) as records:
            with self.assertRaisesRegex(ValueError, "contradicts"):
                env._check_success()
        self.assertEqual(records[0]["status"], "failed")

    def test_query_epoch_cannot_advance_or_be_nonfinite(self):
        for time in (2., float("nan"), float("inf")):
            env = NativeFixture()
            native = env._check_success
            def advances():
                result = native()
                env.sim.data.time = time
                return result
            env._check_success = advances
            with record_goal_queries(env, DEFINITION) as records:
                with self.assertRaisesRegex(ValueError, "simulation time"):
                    env._check_success()
            self.assertEqual(records[0]["status"], "failed")
            json.dumps(records, allow_nan=False)

    def test_nonfinite_initial_epoch_rejects_before_query_and_is_serializable(self):
        env = NativeFixture()
        env.sim.data.time = float("nan")
        with record_goal_queries(env, DEFINITION) as records:
            with self.assertRaisesRegex(ValueError, "finite"):
                env._check_success()
        self.assertEqual(env.calls, [])
        json.dumps(records, allow_nan=False)

    def test_goal_parser_preserves_order_and_rejects_unsupported_semantics(self):
        atoms = goal_atoms(DEFINITION)
        atoms[0][1] = "mutated"
        self.assertEqual(DEFINITION["goal"][1][1], "stove")
        for goal in (["or", ["open", "stove"]], ["and"],
                     ["and", ["on", "pot"]], ["and", ["open", "absent"]],
                     ["and", ["not", ["open", "stove"]]]):
            with self.subTest(goal=goal), self.assertRaises(ValueError):
                goal_atoms(dict(DEFINITION, goal=goal))


if __name__ == "__main__":
    unittest.main()
