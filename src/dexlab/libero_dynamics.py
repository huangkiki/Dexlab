"""Offline generalized-force diagnostics, independent of native scoring calls.

Outputs are per-coordinate numerical residuals, not physical truth or task
success. No MuJoCo import or forward/inverse call is used by this module.
"""

import numpy as np


def _array(value, shape, name, *, integer=False):
    result = np.asarray(value)
    if result.size == 0 and np.prod(shape) == 0:
        # JSON has no dtype/width for an empty array; dimensions come from the model.
        result = np.empty(shape, dtype=int if integer else float)
    if (result.shape != shape or result.dtype.kind not in ("iu" if integer else "fiu")
            or not np.isfinite(result).all()):
        raise ValueError("Missing, non-finite or malformed " + name)
    return result


def mass_matrix(model, packed):
    """Expand the recorded symmetric tree-packed mass matrix without the engine."""
    nv, nm = model["dimensions"]["nv"], model["dimensions"]["nM"]
    parents = _array(model["arrays"]["dof_parentid"], (nv,), "DOF parents", integer=True)
    addresses = _array(model["arrays"]["dof_Madr"], (nv,), "mass addresses", integer=True)
    values = _array(packed, (nm,), "packed mass")
    if np.any(parents < -1) or np.any(parents >= np.arange(nv)):
        raise ValueError("Invalid DOF parent topology")
    matrix, offset = np.zeros((nv, nv)), 0
    for row in range(nv):
        if addresses[row] != offset:
            raise ValueError("Mass addresses contradict DOF topology")
        column = row
        while column >= 0:
            if offset >= nm:
                raise ValueError("Truncated packed mass")
            matrix[row, column] = matrix[column, row] = values[offset]
            offset += 1
            column = parents[column]
    if offset != nm or np.any(np.diag(matrix) <= 0):
        raise ValueError("Invalid packed mass extent or diagonal")
    return matrix


def constraint_matrix(record, nefc, nv):
    if record["shape"] != [nefc, nv] or record["native_storage"] not in ("dense", "sparse"):
        raise ValueError("Constraint Jacobian shape/storage mismatch")
    values = np.asarray(record["values"])
    if values.ndim != 1:
        raise ValueError("Malformed Jacobian values")
    values = _array(values, values.shape, "Jacobian values")
    indices = _array(record["indices"], values.shape, "Jacobian indices", integer=True)
    ptr = _array(record["indptr"], (nefc + 1,), "Jacobian offsets", integer=True)
    if (ptr[0] != 0 or ptr[-1] != len(values) or np.any(np.diff(ptr) < 0)
            or np.any(indices < 0) or np.any(indices >= nv)):
        raise ValueError("Invalid Jacobian offsets or indices")
    matrix = np.zeros((nefc, nv))
    for row in range(nefc):
        columns = indices[ptr[row]:ptr[row + 1]]
        if np.any(np.diff(columns) <= 0):
            raise ValueError("Aliased or unordered Jacobian coordinates")
        matrix[row, columns] = values[ptr[row]:ptr[row + 1]]
    return matrix


def euler_position(model, before, velocity):
    """Reconstruct scalar/free/ball coordinates with the recorded updated velocity."""
    dims, arrays = model["dimensions"], model["arrays"]
    result = np.asarray(before, dtype=float).copy()
    dt = model["options"]["timestep"]
    used_q, used_v = [], []
    for key in ("jnt_type", "jnt_qposadr", "jnt_dofadr"):
        _array(arrays[key], (dims["njnt"],), key, integer=True)
    for kind, qa, va in zip(arrays["jnt_type"], arrays["jnt_qposadr"], arrays["jnt_dofadr"]):
        if kind not in (0, 1, 2, 3):
            raise ValueError("Invalid joint coordinate type")
        nq, nv = {0: (7, 6), 1: (4, 3), 2: (1, 1), 3: (1, 1)}[kind]
        if qa < 0 or va < 0 or qa + nq > dims["nq"] or va + nv > dims["nv"]:
            raise ValueError("Invalid joint coordinate address")
        used_q.extend(range(qa, qa + nq)); used_v.extend(range(va, va + nv))
        if kind in (2, 3):
            result[qa] += dt * velocity[va]
            continue
        if kind == 0:
            result[qa:qa + 3] += dt * velocity[va:va + 3]
            qa += 3; va += 3
        omega = velocity[va:va + 3]
        speed = np.linalg.norm(omega)
        delta = np.r_[np.cos(dt * speed / 2), omega * (np.sin(dt * speed / 2) / speed if speed else 0)]
        a, b = result[qa:qa + 4].copy(), delta
        quat = np.r_[a[0] * b[0] - a[1:] @ b[1:], a[0] * b[1:] + b[0] * a[1:] + np.cross(a[1:], b[1:])]
        norm = np.linalg.norm(quat)
        if norm == 0:
            raise ValueError("Degenerate source quaternion")
        result[qa:qa + 4] = quat / norm
    if sorted(used_q) != list(range(dims["nq"])) or sorted(used_v) != list(range(dims["nv"])):
        raise ValueError("Missing or aliased joint coordinates")
    return result


def diagnostics(model, row):
    """Validate a recorded substep and return independently reconstructed residuals.

    A protocol must separately declare tolerances, model references and windows.
    Generalized coordinates may mix N and N m, so no pooled 'physics pass' is
    returned. Unsupported versions/integrators and warning/reset rows fail shut.
    """
    if (model["schema_version"] not in (1, 2) or model["mujoco"] != "2.3.7"
            or model["options"]["integrator"] != 0 or row["status"] != "recorded"):
        raise ValueError("Unsupported or incomplete substep")
    dims, options = model["dimensions"], model["options"]
    nv, nu, nb = dims["nv"], dims["nu"], dims["nbody"]
    before, after, force = row["state_before"], row["state_after"], row["force"]
    times = _array([before["time"], after["time"], row["force_time"], options["timestep"]], (4,), "epochs")
    t0, t1, force_time, dt = times
    if t0 < 0 or dt <= 0 or force_time != t0 or t1 != t0 + dt:
        raise ValueError("Stale or inconsistent force/state epochs")
    for state in (before, after):
        for key, size in (("qpos", dims["nq"]), ("qvel", nv), ("act", dims["na"])):
            _array(state[key], (size,), key)
        warnings = np.asarray(state["warning_number"])
        _array(warnings, (8,), "warning counters", integer=True)
        if np.any(warnings):
            raise ValueError("Native warning/reset prevents substep qualification")
    vectors = {key: _array(force[key], (nv,), key) for key in
               ("qfrc_actuator", "qfrc_passive", "qfrc_bias", "qfrc_applied", "qfrc_smooth",
                "qfrc_constraint", "qacc", "qacc_smooth")}
    _array(force["ctrl"], (nu,), "ctrl")
    actuator = _array(force["actuator_force"], (nu,), "actuator force")
    moment = _array(force["actuator_moment"], (nu, nv), "actuator moment")
    mass = mass_matrix(model, force["qM"])
    damping = _array(model["arrays"]["dof_damping"], (nv,), "damping")
    if np.any(damping < 0):
        raise ValueError("Negative damping")
    external = _array(force["xfrc_applied"], (nb, 6), "body external forces")
    for key, width in (("xpos", 3), ("xquat", 4), ("xipos", 3), ("xmat", 9), ("cvel", 6), ("subtree_com", 3)):
        _array(force[key], (nb, width), key)
    expected = list(np.flatnonzero(np.any(external[1:] != 0, axis=1)) + 1)
    if [item["body"] for item in force["external_jacobians"]] != expected:
        raise ValueError("Missing or aliased external-force body mapping")
    applied = np.zeros(nv)
    for item in force["external_jacobians"]:
        body = item["body"]
        jp = _array(item["jacp"], (3, nv), "COM translation Jacobian")
        jr = _array(item["jacr"], (3, nv), "COM rotation Jacobian")
        applied += jp.T @ external[body, :3] + jr.T @ external[body, 3:]
    ef = np.asarray(force["efc_force"])
    if ef.ndim != 1:
        raise ValueError("Malformed constraint forces")
    ef = _array(ef, ef.shape, "constraint force")
    kinds = _array(force["efc_type"], ef.shape, "constraint types", integer=True)
    ids = _array(force["efc_id"], ef.shape, "constraint ids", integer=True)
    if np.any(kinds < 0) or np.any(kinds > 7) or np.any(ids < 0):
        raise ValueError("Invalid constraint identities")
    for kind, size in ((0, dims["neq"]), (1, nv), (2, dims["ntendon"]),
                       (3, dims["njnt"]), (4, dims["ntendon"])):
        if np.any(ids[kinds == kind] >= size):
            raise ValueError("Invalid joint/tendon/equality constraint mapping")
    for key in ("efc_pos", "efc_margin", "efc_vel"):
        _array(force[key], ef.shape, key)
    jacobian = constraint_matrix(force["jacobian"], len(ef), nv)
    contacts = force["contacts"]
    contact_errors = []
    for index, contact in enumerate(contacts):
        dim, address = contact["dim"], contact["efc_address"]
        if dim not in (1, 3, 4, 6) or address < -1:
            raise ValueError("Invalid contact dimension/address")
        if any(type(contact[k]) is not int or not 0 <= contact[k] < dims["ngeom"] for k in ("geom1", "geom2")):
            raise ValueError("Invalid contact geometry mapping")
        friction = _array(contact["friction"], (5,), "contact friction")
        _array(contact["pos"], (3,), "contact position")
        _array(contact["frame"], (9,), "contact frame")
        _array(contact["dist"], (), "contact distance")
        _array(contact["solref"], (2,), "contact solref")
        _array(contact["solimp"], (5,), "contact solimp")
        actual = _array(contact["local_wrench"], (6,), "contact wrench")
        predicted = np.zeros(6)
        if address >= 0:
            width = 2 * (dim - 1) if options["cone"] == 0 and dim > 1 else dim
            if address + width > len(ef) or not np.all(ids[address:address + width] == index):
                raise ValueError("Contact constraint mapping mismatch")
            expected_kind = 5 if dim == 1 else (6 if options["cone"] == 0 else 7)
            if not np.all(kinds[address:address + width] == expected_kind):
                raise ValueError("Contact constraint type mismatch")
            components = ef[address:address + width]
            if options["cone"] == 0 and dim > 1:
                pairs = components.reshape(dim - 1, 2)
                predicted[0] = np.sum(pairs)
                predicted[1:dim] = (pairs[:, 0] - pairs[:, 1]) * friction[:dim - 1]
            else:
                predicted[:dim] = components
        contact_errors.append(actual - predicted)
    if np.any(ids[kinds >= 5] >= len(contacts)):
        raise ValueError("Constraint refers to missing contact")
    smooth = vectors["qfrc_passive"] - vectors["qfrc_bias"] + vectors["qfrc_applied"] + vectors["qfrc_actuator"] + applied
    total = vectors["qfrc_smooth"] + vectors["qfrc_constraint"]
    integrated_acc = (np.asarray(after["qvel"]) - before["qvel"]) / dt
    actuator_generalized = moment.T @ actuator
    limited = model["arrays"]["jnt_actfrclimited"]
    for joint, is_limited in enumerate(limited):
        if is_limited:
            address = model["arrays"]["jnt_dofadr"][joint]
            actuator_generalized[address] = np.clip(actuator_generalized[address], *model["arrays"]["jnt_actfrcrange"][joint])
    return {"smooth_force": vectors["qfrc_smooth"] - smooth,
            "actuator_transmission": vectors["qfrc_actuator"] - actuator_generalized,
            "smooth_acceleration": mass @ vectors["qacc_smooth"] - vectors["qfrc_smooth"],
            "constrained_acceleration": mass @ vectors["qacc"] - total,
            "constraint_transmission": jacobian.T @ ef - vectors["qfrc_constraint"],
            "euler_velocity": mass @ integrated_acc + dt * damping * integrated_acc - total,
            "euler_position": np.asarray(after["qpos"]) - euler_position(model, before["qpos"], np.asarray(after["qvel"])),
            "contact_wrench": np.asarray(contact_errors).reshape(-1, 6)}
