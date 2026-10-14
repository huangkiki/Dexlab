"""Read MuJoCo 2.3.7 Euler substeps without advancing or recomputing dynamics.

Force caches belong to the pre-integration state; qpos/qvel after mj_step do
not. The caller owns persistence and action indices. A sink receives even a
failed native step, so it must retain partial records rather than discard them.
"""

from contextlib import contextmanager

import numpy as np


MODEL_ARRAYS = (
    "dof_parentid", "dof_Madr", "dof_damping", "dof_armature", "dof_jntid", "dof_bodyid",
    "jnt_type", "jnt_qposadr", "jnt_dofadr", "jnt_bodyid", "jnt_actfrclimited", "jnt_actfrcrange",
    "body_parentid", "body_rootid", "body_dofadr", "body_dofnum", "body_mass",
    "body_inertia", "body_ipos", "body_iquat", "body_gravcomp", "geom_bodyid", "site_bodyid",
)
FORCE_ARRAYS = (
    "ctrl", "actuator_force", "actuator_moment", "qfrc_actuator", "qfrc_passive",
    "qfrc_bias", "qfrc_applied", "qfrc_smooth", "qfrc_constraint", "qacc", "qacc_smooth",
    "qM", "xfrc_applied", "xpos", "xquat", "xipos", "xmat", "ximat", "cvel", "subtree_com",
    "cdof", "cdof_dot", "cinert",
)
CONSTRAINT_ARRAYS = ("efc_type", "efc_id", "efc_force", "efc_pos", "efc_margin", "efc_vel")
SOLVER_FIELDS = ("improvement", "gradient", "lineslope", "nactive", "nchange", "neval", "nupdate")
SOLVER_CAPACITY = 1000  # mjNSOLVER in the pinned 2.3.7 header.


def model_record(model):
    """Record native coordinate ownership and the supported integration contract."""
    import mujoco

    if mujoco.__version__ != "2.3.7" or int(model.opt.integrator) != 0:
        raise ValueError("Substep force epochs require MuJoCo 2.3.7 Euler qualification")
    if model.nplugin:
        raise ValueError("Plugin state/force epochs require separate qualification")
    dimensions = {key: int(getattr(model, key)) for key in
                  ("nq", "nv", "nu", "na", "nM", "nbody", "ngeom", "nsite", "njnt", "ntendon", "neq")}
    options = {key: float(getattr(model.opt, key)) for key in ("timestep", "tolerance", "noslip_tolerance")}
    options.update({key: int(getattr(model.opt, key)) for key in
                    ("integrator", "cone", "jacobian", "solver", "iterations", "noslip_iterations", "disableflags", "enableflags")})
    return {"schema_version": 2, "mujoco": mujoco.__version__, "dimensions": dimensions,
            "meaninertia": float(model.stat.meaninertia), "solver_capacity": SOLVER_CAPACITY,
            "options": options, "gravity": model.opt.gravity.tolist(),
            "arrays": {key: getattr(model, key).tolist() for key in MODEL_ARRAYS},
            "names": {kind: [mujoco.mj_id2name(model, getattr(mujoco.mjtObj, "mjOBJ_" + kind.upper()), i)
                             for i in range(dimensions[size])]
                      for kind, size in (("body", "nbody"), ("geom", "ngeom"), ("joint", "njnt"), ("site", "nsite"))},
            "epochs": {"force": "state_before", "integrated_state": "state_after",
                       "external_jacobians": "read-only mj_jacBodyCom from force-stage caches"},
            "reaction_observability": "Offline Newton-Euler inputs recorded; inferred net subtree wrench is not a separately measured joint reaction."}


def state_record(data):
    return {"time": float(data.time), "qpos": data.qpos.copy(), "qvel": data.qvel.copy(),
            "act": data.act.copy(), "warning_number": np.asarray(data.warning.number).copy()}


def constraint_jacobian(model, data):
    """Losslessly retain J as CSR; dense native storage has exact zeros elided."""
    import mujoco

    count = int(data.nefc)
    if mujoco.mj_isSparse(model):
        lengths = np.asarray(data.efc_J_rownnz[:count]).copy()
        starts = data.efc_J_rowadr[:count]
        indices = np.concatenate([data.efc_J_colind[a:a + n] for a, n in zip(starts, lengths)]) if count else np.empty(0, int)
        values = np.concatenate([data.efc_J[a:a + n] for a, n in zip(starts, lengths)]) if count else np.empty(0)
        native_storage = "sparse"
    else:
        dense = data.efc_J[:count * model.nv].reshape(count, model.nv)
        row, indices = np.nonzero(dense)
        lengths = np.bincount(row, minlength=count)
        values = dense[row, indices].copy()
        native_storage = "dense"
    return {"native_storage": native_storage, "shape": [count, int(model.nv)],
            "indptr": np.r_[0, np.cumsum(lengths)], "indices": indices.copy(), "values": values}


def force_record(model, data):
    """Read caches immediately after one Euler step, before any forward call."""
    import mujoco

    result = {key: np.asarray(getattr(data, key)).copy() for key in FORCE_ARRAYS}
    result.update({key: np.asarray(getattr(data, key)[:data.nefc]).copy() for key in CONSTRAINT_ARRAYS})
    result["jacobian"] = constraint_jacobian(model, data)
    contacts = []
    for index in range(data.ncon):
        contact = data.contact[index]
        wrench = np.zeros(6)
        mujoco.mj_contactForce(model, data, index, wrench)
        contacts.append({**{key: int(getattr(contact, key)) for key in
                            ("geom1", "geom2", "dim", "efc_address", "exclude")},
                         **{key: np.asarray(getattr(contact, key)).copy() for key in
                            ("pos", "frame", "dist", "friction", "solref", "solimp")},
                         "local_wrench": wrench})
    result["contacts"] = contacts
    external = []
    # Body zero is world; mj_xfrcAccumulate only visits actual bodies.
    for body in np.flatnonzero(np.any(data.xfrc_applied[1:] != 0, axis=1)) + 1:
        jacp, jacr = np.zeros((3, model.nv)), np.zeros((3, model.nv))
        mujoco.mj_jacBodyCom(model, data, jacp, jacr, int(body))
        external.append({"body": int(body), "jacp": jacp, "jacr": jacr})
    result["external_jacobians"] = external
    # Only the saved prefix belongs to this solve. nnz/fwdinv and unused slots
    # can retain earlier values; never turn those buffers into current telemetry.
    count = min(int(data.solver_iter), SOLVER_CAPACITY)
    result["solver"] = {
        "iterations": int(data.solver_iter), "constraints": int(data.nefc),
        "nnz": int(data.solver_nnz) if data.nefc else None,
        "fwdinv": data.solver_fwdinv.copy() if model.opt.enableflags & 4 else None,
        "statistics": {key: np.asarray(getattr(data.solver, key)[:count]).copy() for key in SOLVER_FIELDS},
        "termination_reason": "not-exposed-by-native-api",
    }
    return result


@contextmanager
def record_substeps(sim, sink):
    """Observe exactly the existing sim.step calls; restore the hook on failure.

    The supported wrapper must call mj_step once with no subsequent forward.
    Its identity is pinned by the executor's runtime/source manifest. This hook
    neither invokes a controller nor writes a native state or force buffer.
    """
    model, data = sim.model._model, sim.data._data
    descriptor = model_record(model)
    original = sim.step
    own_step = "step" in vars(sim)
    sequence = 0

    def step(*args, **kwargs):
        nonlocal sequence
        if (float(model.opt.timestep) != descriptor["options"]["timestep"]
                or int(model.opt.integrator) != descriptor["options"]["integrator"]):
            raise ValueError("Native timestep or integrator changed within recording")
        row = {"sequence": sequence, "status": "failed", "state_before": state_record(data)}
        sequence += 1
        try:
            result = original(*args, **kwargs)
            row["state_after"] = state_record(data)
            row["force_time"] = row["state_before"]["time"]
            row["force"] = force_record(model, data)
            row["status"] = "recorded"
        except BaseException as error:
            row["error_type"] = type(error).__name__
            try:
                sink(row)
            except BaseException as sink_error:
                raise error from sink_error
            raise
        sink(row)
        return result

    sim.step = step
    try:
        yield descriptor
    finally:
        if own_step:
            sim.step = original
        else:
            del sim.step
