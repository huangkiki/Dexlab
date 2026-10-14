"""Observe native LIBERO goal queries without evaluating another predicate.

This records the queries made by the pinned native success method. It does not
replace task success, measure contact, or establish physical validity.
"""

from contextlib import contextmanager
from copy import deepcopy
import math

import numpy as np


PREDICATE_ARITY = {"in": 2, "on": 2, "open": 1, "close": 1, "turnon": 1, "turnoff": 1}


def goal_atoms(definition):
    """Require the ordered conjunction supported by the frozen native source."""
    goal = definition["goal"]
    if not isinstance(goal, list) or len(goal) < 2 or goal[0] != "and":
        raise ValueError("Expected a nonempty native goal conjunction")
    known = set(definition["objects"]) | set(definition["fixtures"])
    known.update(name for name, region in definition["regions"].items()
                 if region["target_declared"])
    for atom in goal[1:]:
        if (not isinstance(atom, list) or not atom
                or not isinstance(atom[0], str)
                or atom[0] not in PREDICATE_ARITY
                or len(atom) != PREDICATE_ARITY[atom[0]] + 1
                or any(not isinstance(name, str) or name not in known for name in atom[1:])):
            raise ValueError("Unsupported native predicate or unresolved goal argument")
    return deepcopy(goal[1:])


def _boolean(value):
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError("Native goal queries must return booleans")
    return bool(value)


@contextmanager
def record_goal_queries(env, definition):
    """Yield ordered records of existing success checks and restore both hooks.

    Install after native initialization. Call env.step normally; do not add a
    _check_success call for logging. Each native call returns its original result
    and each predicate runs exactly once at its original position. Failed or
    incomplete checks remain in the yielded list and propagate their exception.
    Instance hooks leave the engine source and class definitions unchanged.
    """
    expected = goal_atoms(definition)
    if env.parsed_problem["goal_state"] != expected:
        raise ValueError("Native goals differ from the pinned task declaration")
    original_check, original_predicate = env._check_success, env._eval_predicate
    previous = {name: env.__dict__[name] for name in ("_check_success", "_eval_predicate")
                if name in env.__dict__}
    records = []
    active = None

    def evaluate(state):
        if active is None:
            return original_predicate(state)
        index = len(active["queries"])
        if index >= len(expected) or state != expected[index]:
            raise ValueError("Native goal query order or arguments changed")
        value = original_predicate(state)
        active["queries"].append({"goal_index": index, "predicate": deepcopy(state),
                                  "value": _boolean(value)})
        return value

    def check():
        nonlocal active
        if active is not None:
            raise ValueError("Nested native success checks are unsupported")
        active = {"check_index": len(records), "status": "incomplete", "queries": []}
        records.append(active)
        try:
            before = float(env.sim.data.time)
            if not math.isfinite(before):
                raise ValueError("Native goal time must be finite")
            active["time_s"] = before
            if env.parsed_problem["goal_state"] != expected:
                raise ValueError("Native goals changed after recorder binding")
            value = original_check()
            if env.parsed_problem["goal_state"] != expected:
                raise ValueError("Native goals changed during a success check")
            after = float(env.sim.data.time)
            if not math.isfinite(after):
                raise ValueError("A native goal query left non-finite simulation time")
            active["time_after_s"] = after
            if after != before:
                raise ValueError("A native goal query advanced simulation time")
            if len(active["queries"]) != len(expected):
                raise ValueError("Native success check omitted declared goals")
            success = _boolean(value)
            if success != all(query["value"] for query in active["queries"]):
                raise ValueError("Native success contradicts its goal conjunction")
            active.update(status="completed", native_success=success)
            return value
        except BaseException as error:
            active.update(status="failed", error_type=type(error).__name__)
            raise
        finally:
            active = None

    env._eval_predicate, env._check_success = evaluate, check
    try:
        yield records
        if env._check_success is not check or env._eval_predicate is not evaluate:
            raise ValueError("Native goal hooks changed during recording")
    finally:
        for name in ("_check_success", "_eval_predicate"):
            if name in previous:
                setattr(env, name, previous[name])
            elif name in env.__dict__:
                delattr(env, name)
