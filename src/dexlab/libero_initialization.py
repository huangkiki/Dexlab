"""Restore one admitted demonstration before task-aware native execution.

The pinned robosuite state contains time, qpos and qvel only. Native forward
normalizes quaternions; that exact transformation is permitted, not an epsilon
change to arbitrary coordinates. This does not qualify later physical behavior.
"""

import numpy as np


def initialize_demo(env, model_xml, initial, record):
    """Reset controllers/model, restore once, and retain each initialization stage.

    ``record`` is an empty caller-owned diagnostic dictionary. It remains usable
    when a phase fails, so the caller can archive failed initialization rather
    than losing the evidence. No success query or action is added here. The
    caller owns seed selection, source admission, output and environment cleanup.
    """
    import mujoco

    if record:
        raise ValueError("Initialization diagnostics must not overwrite an existing record")
    record.update(status="incomplete", phase="input")
    try:
        source = np.asarray(initial)
        if source.ndim != 1 or source.dtype.kind != "f" or not np.isfinite(source).all():
            raise ValueError("Expected a finite floating native source state")
        source = source.copy()
        record["source"] = source.tolist()
        record["phase"] = "native-reset"
        env.reset()
        env.reset_from_xml_string(model_xml)
        env.sim.reset()
        model = env.sim.model._model
        record["model_dimensions"] = {key: int(getattr(model, key)) for key in ("nq", "nv", "na")}
        if model.na != 0:
            raise ValueError("The pinned flat-state format does not include actuator activation")
        if source.shape != (1 + model.nq + model.nv,):
            raise ValueError("Source state width differs from the final native model")
        if source[0] < 0:
            raise ValueError("Native source time must be nonnegative")
        normalized = source.copy()
        qpos = normalized[1:1 + model.nq]
        for kind, address in zip(model.jnt_type, model.jnt_qposadr):
            if int(kind) in (0, 1):  # MuJoCo free and ball joints.
                begin = int(address) + (3 if int(kind) == 0 else 0)
                if not np.any(qpos[begin:begin + 4]):
                    raise ValueError("Source quaternion is degenerate")
        mujoco.mj_normalizeQuat(model, qpos)
        if not np.isfinite(normalized).all():
            raise ValueError("Native quaternion normalization produced non-finite state")
        record["expected_after_forward"] = normalized.tolist()

        def capture(name, expected):
            actual = np.asarray(env.sim.get_state().flatten()).copy()
            if actual.shape != expected.shape or not np.isfinite(actual).all():
                record[name + "_invalid"] = {"shape": list(actual.shape),
                                            "finite": bool(np.isfinite(actual).all())}
                raise ValueError("Invalid native state at " + name)
            record[name] = actual.tolist()
            if not np.array_equal(actual, expected):
                record[name + "_mismatched_indices"] = np.flatnonzero(actual != expected).tolist()
                raise ValueError("Unexpected native state change at " + name)

        record["phase"] = "restore"
        env.sim.set_state_from_flattened(source.copy())
        capture("after_set", source)
        record["phase"] = "forward"
        env.sim.forward()
        capture("after_forward", normalized)
        record["phase"] = "post-processing"
        env._post_process()
        env._update_observables(force=True)
        capture("after_post", normalized)
        record.update(status="completed", phase="ready-for-actions",
                      normalized_indices=np.flatnonzero(source != normalized).tolist())
    except BaseException as error:
        record.update(status="failed", error_type=type(error).__name__)
        raise
