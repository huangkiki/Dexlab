"""Restore one admitted demonstration before task-aware native execution.

The pinned robosuite state contains time, qpos and qvel only. Native forward
normalizes quaternions; that exact transformation is permitted, not an epsilon
change to arbitrary coordinates. This does not qualify later physical behavior.
"""

import numpy as np


INITIALIZATION_CONTRACT = "osc-restored-pose-v1"


def _controller_snapshot(controller, gripper):
    """Retain controller memory separately from the saved native flat state."""
    shapes = {"joint_pos": (7,), "joint_vel": (7,), "initial_joint": (7,),
              "ee_pos": (3,), "ee_ori_mat": (3, 3), "goal_pos": (3,), "goal_ori": (3, 3)}
    result = {}
    for name, shape in shapes.items():
        value = np.asarray(getattr(controller, name))
        if value.shape != shape or not np.isfinite(value).all():
            raise ValueError("Invalid OSC controller state: " + name)
        result[name] = value.tolist()
    action = np.asarray(gripper.current_action)
    if action.shape not in ((1,), (2,)) or not np.isfinite(action).all():
        raise ValueError("Invalid native gripper action memory")
    return dict(result, gripper_current_action=action.tolist(), new_update=bool(controller.new_update))


def initialize_demo(env, model_xml, initial, record):
    """Reset controllers/model, restore once, and retain each initialization stage.

    ``record`` is an empty caller-owned diagnostic dictionary. It remains usable
    when a phase fails, so the caller can archive failed initialization rather
    than losing the evidence. No success query or action is added here. The
    caller owns seed selection, source admission, output and environment cleanup.
    A single delta OSC pose controller supplies the native forward and refreshes
    its caches; its Cartesian goals are then reset to the restored pose. Native
    reset nullspace/gripper references remain explicit, not inferred history.
    Controller-free analytical fixtures retain the flat-state-only contract.
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
        if len(env.robots) > 1:
            raise ValueError("Only the qualified single-arm OSC restore is supported")
        robot = env.robots[0] if env.robots else None
        controller = robot.controller if robot is not None else None
        record["contract"] = INITIALIZATION_CONTRACT if robot is not None else "flat-state-only-v1"
        record["controller"] = None
        if controller is not None:
            if (controller.name != "OSC_POSE" or not controller.use_delta
                    or controller.interpolator_pos is not None or controller.interpolator_ori is not None):
                raise ValueError("Restore requires native delta OSC_POSE without interpolation")
            record["controller"] = {
                "name": controller.name,
                "joint_ids": [int(i) for i in controller.joint_index],
                "qpos_indices": [int(i) for i in controller.qpos_index],
                "qvel_indices": [int(i) for i in controller.qvel_index],
                "eef_site_id": int(env.sim.model.site_name2id(controller.eef_name)),
                "before": _controller_snapshot(controller, robot.gripper),
                "history_scope": "Native reset nullspace and gripper references; source controller history is unavailable.",
            }
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
        if controller is None:
            env.sim.forward()
        else:
            # The pinned native update performs exactly one sim.forward().
            # Do not add a separate forward or a dummy control action.
            controller.update(force=True)
        capture("after_forward", normalized)
        if controller is not None:
            record["phase"] = "controller-goals"
            controller.reset_goal()
            snapshot = _controller_snapshot(controller, robot.gripper)
            diagnostic = record["controller"]
            diagnostic["after"] = snapshot
            data, site = env.sim.data, diagnostic["eef_site_id"]
            native = {"joint_pos": np.asarray(data.qpos)[controller.qpos_index],
                      "joint_vel": np.asarray(data.qvel)[controller.qvel_index],
                      "ee_pos": np.asarray(data.site_xpos[site]),
                      "ee_ori_mat": np.asarray(data.site_xmat[site]).reshape(3, 3)}
            diagnostic["native_after"] = {key: value.tolist() for key, value in native.items()}
            for key, value in native.items():
                if not np.array_equal(snapshot[key], value):
                    raise ValueError("OSC cache differs from restored native state: " + key)
            for goal, pose in (("goal_pos", "ee_pos"), ("goal_ori", "ee_ori_mat")):
                if not np.array_equal(snapshot[goal], snapshot[pose]):
                    raise ValueError("OSC goal differs from restored pose: " + goal)
            for key in ("initial_joint", "gripper_current_action"):
                if snapshot[key] != diagnostic["before"][key]:
                    raise ValueError("Restore changed native reset history: " + key)
            capture("after_controller_goals", normalized)
        record["phase"] = "post-processing"
        env._post_process()
        env._update_observables(force=True)
        capture("after_post", normalized)
        record.update(status="completed", phase="ready-for-actions",
                      normalized_indices=np.flatnonzero(source != normalized).tolist())
    except BaseException as error:
        record.update(status="failed", error_type=type(error).__name__)
        raise
