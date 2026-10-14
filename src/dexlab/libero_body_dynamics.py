"""Offline body accounting from force-stage caches, without engine calls.

World-oriented spatial vectors use angular/linear order and each tree's COM
as origin. Inferred subtree wrenches include motor/passive/constraint effort;
they are not uniquely identified bearing reactions or empirical force readings.
"""

import numpy as np

from dexlab.libero_dynamics import _array, constraint_matrix, mass_matrix
from dexlab.libero_score import rotation


def solver_observation(model, row):
    """Validate current native statistics without guessing an unexposed exit flag."""
    if model["schema_version"] != 2:
        raise ValueError("Solver telemetry requires recorded model schema 2")
    force, options = row["force"], model["options"]
    record = force["solver"]
    count, capacity = record["iterations"], model["solver_capacity"]
    nefc = len(force["efc_force"])
    if (type(count) is not int or count < 0 or capacity != 1000
            or count > options["iterations"] + options["noslip_iterations"]
            or record["constraints"] != nefc or not nefc and count):
        raise ValueError("Invalid solver iteration extent")
    if record["termination_reason"] != "not-exposed-by-native-api":
        raise ValueError("Native solver does not expose a termination reason")
    if nefc:
        if type(record["nnz"]) is not int or record["nnz"] < 0:
            raise ValueError("Invalid solver sparsity statistic")
    elif record["nnz"] is not None:
        raise ValueError("Unconstrained solver sparsity can be stale")
    if options["enableflags"] & 4:
        _array(record["fwdinv"], (2,), "forward/inverse statistic")
    elif record["fwdinv"] is not None:
        raise ValueError("Disabled forward/inverse statistic can be stale")
    fields = {"improvement", "gradient", "lineslope", "nactive", "nchange", "neval", "nupdate"}
    if set(record["statistics"]) != fields:
        raise ValueError("Missing solver statistic")
    for key, value in record["statistics"].items():
        _array(value, (min(count, capacity),), key, integer=key.startswith("n"))
    scale = float(model["meaninertia"]) * max(1, model["dimensions"]["nv"])
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid native solver normalization")
    residual = mass_matrix(model, force["qM"]) @ force["qacc"] - force["qfrc_smooth"] - force["qfrc_constraint"]
    # PGS has no primal-gradient statistic. NoSlip can change qacc after the
    # main solve, and the shared statistic array has no exposed stage boundary.
    comparable = bool(nefc and options["solver"] in (1, 2) and not options["noslip_iterations"])
    return {"iterations": count, "statistics_truncated": count > capacity,
            "scaled_equation_residual_norm": float(np.linalg.norm(residual) / scale),
            "primal_gradient_comparable": comparable,
            "termination_reason": record["termination_reason"]}


def _cross_matrix(vector):
    x, y, z = vector
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def body_accounting(model, row):
    """Reconstruct inertial and net subtree wrenches from the pre-step epoch.

    Projecting the inferred wrench into each DOF can be checked against native
    generalized effort. Contact/applied loads are localized; remaining loads
    (including equality links and tendons) stay explicitly unresolved in 6D.
    """
    if model["schema_version"] != 2 or row["force_time"] != row["state_before"]["time"]:
        raise ValueError("Body accounting requires schema 2 and force-stage epochs")
    dims, arrays, force = model["dimensions"], model["arrays"], row["force"]
    nb, nv = dims["nbody"], dims["nv"]
    parent = _array(arrays["body_parentid"], (nb,), "body parents", integer=True)
    root = _array(arrays["body_rootid"], (nb,), "body roots", integer=True)
    owner = _array(arrays["dof_bodyid"], (nv,), "DOF bodies", integer=True)
    address = _array(arrays["body_dofadr"], (nb,), "body DOF addresses", integer=True)
    number = _array(arrays["body_dofnum"], (nb,), "body DOF counts", integer=True)
    if (parent[0] != 0 or root[0] != 0 or number[0] != 0
            or np.any(parent[1:] < 0) or np.any(parent[1:] >= np.arange(1, nb))
            or np.any(owner <= 0) or np.any(owner >= nb) or np.any(number < 0)):
        raise ValueError("Invalid body/DOF topology")
    covered = []
    for body in range(1, nb):
        if root[body] != (root[parent[body]] if parent[body] else body):
            raise ValueError("Body root contradicts parent topology")
        start, size = address[body], number[body]
        if size and (start < 0 or start + size > nv or not np.all(owner[start:start + size] == body)):
            raise ValueError("Body DOF ownership mismatch")
        if size:
            covered.extend(range(start, start + size))
    if sorted(covered) != list(range(nv)):
        raise ValueError("Missing or aliased body DOFs")
    mass = _array(arrays["body_mass"], (nb,), "body mass")
    inertia = _array(arrays["body_inertia"], (nb, 3), "principal inertia")
    if np.any(mass < 0) or np.any(inertia < 0):
        raise ValueError("Negative mass/inertia")
    com = _array(force["xipos"], (nb, 3), "body COM")
    origin = _array(force["subtree_com"], (nb, 3), "tree COM")[root]
    orientation = _array(force["ximat"], (nb, 9), "inertia orientation").reshape(nb, 3, 3)
    velocity = _array(force["cvel"], (nb, 6), "spatial velocity")
    axes = _array(force["cdof"], (nv, 6), "spatial motion axes")
    axes_dot = _array(force["cdof_dot"], (nv, 6), "spatial axis derivatives")
    qvel = _array(row["state_before"]["qvel"], (nv,), "pre-integration velocity")
    qacc = _array(force["qacc"], (nv,), "force-stage acceleration")
    packed_inertia = _array(force["cinert"], (nb, 10), "native spatial inertia")
    gravity = _array(model["gravity"], (3,), "gravity")
    if model["options"]["disableflags"] & (1 << 6):
        gravity = np.zeros(3)
    acceleration, expected_velocity = np.zeros((nb, 6)), np.zeros((nb, 6))
    acceleration[0, 3:] = -gravity
    inertial, expected_inertia = np.zeros((nb, 6)), np.zeros((nb, 10))
    for body in range(1, nb):
        indices = np.flatnonzero(owner == body)
        acceleration[body] = acceleration[parent[body]] + axes_dot[indices].T @ qvel[indices] + axes[indices].T @ qacc[indices]
        expected_velocity[body] = expected_velocity[parent[body]] + axes[indices].T @ qvel[indices]
        offset = com[body] - origin[body]
        cross = _cross_matrix(offset)
        central = (orientation[body] * inertia[body]) @ orientation[body].T
        angular = central - mass[body] * cross @ cross
        spatial = np.block([[angular, mass[body] * cross], [-mass[body] * cross, mass[body] * np.eye(3)]])
        expected_inertia[body] = np.r_[angular[0, 0], angular[1, 1], angular[2, 2],
                                       angular[0, 1], angular[0, 2], angular[1, 2], mass[body] * offset, mass[body]]
        momentum = spatial @ velocity[body]
        omega, linear = velocity[body, :3], velocity[body, 3:]
        coriolis = np.r_[np.cross(omega, momentum[:3]) + np.cross(linear, momentum[3:]), np.cross(omega, momentum[3:])]
        inertial[body] = spatial @ acceleration[body] + coriolis
    external = _array(force["xfrc_applied"], (nb, 6), "applied body wrench")
    applied = np.c_[external[:, 3:] + np.cross(com - origin, external[:, :3]), external[:, :3]]
    applied[0] = 0  # Native body-zero applied force is ignored.
    contacts = np.zeros((nb, 6))
    geom_body = _array(arrays["geom_bodyid"], (dims["ngeom"],), "geometry bodies", integer=True)
    if np.any(geom_body < 0) or np.any(geom_body >= nb):
        raise ValueError("Invalid geometry body mapping")
    for contact in force["contacts"]:
        local = _array(contact["local_wrench"], (6,), "contact wrench")
        frame = _array(contact["frame"], (9,), "contact frame").reshape(3, 3)
        linear, torque = frame.T @ local[:3], frame.T @ local[3:]
        position = _array(contact["pos"], (3,), "contact position")
        for key, sign in (("geom1", -1), ("geom2", 1)):
            geom = contact[key]
            if type(geom) is not int or not 0 <= geom < len(geom_body):
                raise ValueError("Invalid contact geometry")
            body = geom_body[geom]
            if body:
                contacts[body] += sign * np.r_[torque + np.cross(position - origin[body], linear), linear]
    net = inertial - applied - contacts
    for body in range(nb - 1, 0, -1):
        if parent[body]:  # Different roots have different origins; never sum them as-is.
            net[parent[body]] += net[body]
    kinds = _array(force["efc_type"], (len(force["efc_force"]),), "constraint types", integer=True)
    efc = _array(force["efc_force"], kinds.shape, "constraint forces")
    jacobian = constraint_matrix(force["jacobian"], len(efc), nv)
    noncontact = jacobian[kinds < 5].T @ efc[kinds < 5]
    armature = _array(arrays["dof_armature"], (nv,), "armature")
    effort = sum((_array(force[key], (nv,), key) for key in
                  ("qfrc_actuator", "qfrc_passive", "qfrc_applied")), np.zeros(nv)) + noncontact - armature * qacc
    projected = np.einsum("ij,ij->i", axes, net[owner])
    supports = []
    for body in np.flatnonzero((parent == 0) & (np.arange(nb) != 0)):
        supports.append({"body": int(body), "world_origin_wrench": np.r_[net[body, :3] + np.cross(origin[body], net[body, 3:]), net[body, 3:]],
                         "root_has_dofs": bool(number[body])})
    return {"acceleration": acceleration, "inertial_wrench": inertial,
            "contact_wrench": contacts, "applied_wrench": applied,
            "inferred_net_subtree_wrench": net, "root_boundary_wrenches": supports,
            "noncontact_generalized_constraint": noncontact,
            "residuals": {"spatial_inertia": packed_inertia - expected_inertia,
                          "spatial_velocity": velocity - expected_velocity,
                          "projected_body_effort": projected - effort},
            "interpretation": "Inferred net subtree load, including unresolved motor/passive/noncontact loads; not a separately measured joint reaction."}


def free_com_balance(model, row, accounting):
    """Linear impulse for rigid free-joint trees, including recorded extra loads.

    Return raw N s errors and explicit exclusions, without imposing a universal
    physical tolerance. Rotating off-centre COMs retain time-discretization error.
    Articulated free trees need full post-step kinematics and are not passed here.
    """
    arrays, force = model["arrays"], row["force"]
    before, after = row["state_before"], row["state_after"]
    dt = model["options"]["timestep"]
    if after["time"] != before["time"] + dt or dt <= 0:
        raise ValueError("Invalid momentum interval")
    root, mass = np.asarray(arrays["body_rootid"]), np.asarray(arrays["body_mass"])
    gravity = np.asarray(model["gravity"]) if not model["options"]["disableflags"] & 64 else np.zeros(3)
    result = []
    for joint, kind in enumerate(arrays["jnt_type"]):
        if kind != 0:
            continue
        body, qa, va = (arrays[key][joint] for key in ("jnt_bodyid", "jnt_qposadr", "jnt_dofadr"))
        members = np.flatnonzero(root == body)
        entry = {"body": int(body), "joint": joint, "status": "unqualified"}
        if (not len(members) or sum(arrays["body_dofnum"][i] for i in members) != 6
                or np.any(np.asarray(arrays["dof_armature"])[va:va + 6]) or np.sum(mass[members]) <= 0):
            entry["reason"] = "Requires a positive-mass rigid free tree without armature; articulated/rotor momentum is unresolved."
            result.append(entry)
            continue
        total_mass = np.sum(mass[members])
        rotations = [rotation(np.asarray(s["qpos"])[qa + 3:qa + 7] / np.linalg.norm(np.asarray(s["qpos"])[qa + 3:qa + 7])) for s in (before, after)]
        offset = rotations[0].T @ (np.asarray(force["subtree_com"])[body] - np.asarray(force["xpos"])[body])
        velocities = [np.asarray(s["qvel"])[va:va + 3] + np.cross(r @ np.asarray(s["qvel"])[va + 3:va + 6], r @ offset)
                      for s, r in zip((before, after), rotations)]
        load = np.sum(accounting["contact_wrench"][members, 3:] + accounting["applied_wrench"][members, 3:], axis=0) + total_mass * gravity
        for key in ("qfrc_passive", "qfrc_actuator", "qfrc_applied"):
            load += np.asarray(force[key])[va:va + 3]
        load += accounting["noncontact_generalized_constraint"][va:va + 3]
        # Euler integrates damping implicitly. qfrc_passive above contains its
        # old-velocity value, so remove D*(v_after-v_before) once, not twice.
        load -= np.asarray(arrays["dof_damping"])[va:va + 3] * (np.asarray(after["qvel"])[va:va + 3] - np.asarray(before["qvel"])[va:va + 3])
        entry.update(status="diagnostic-only", mass_kg=float(total_mass),
                     measured_momentum_change=total_mass * (velocities[1] - velocities[0]), expected_impulse=dt * load,
                     residual_N_s=total_mass * (velocities[1] - velocities[0]) - dt * load)
        result.append(entry)
    return result
