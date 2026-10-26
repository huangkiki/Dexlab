"""Independently decode recorded Warp constraint forces without running physics."""

import numpy as np


def check_step_clock(before, after, *, dt, dtype):
    """Check the actual native floating-point addition, including quantization."""
    if dtype not in ("float32", "float64") or not np.isfinite([before, after, dt]).all() or dt <= 0:
        raise ValueError("Invalid native clock declaration")
    scalar = np.dtype(dtype).type
    expected = float(scalar(scalar(before) + scalar(dt)))
    if float(after) != expected:
        raise ValueError("Native clock differs from its declared timestep and precision")


def carrying_windows(times, height, required_height, loaded_pairs, *, dt, hold_s, clock_dtype="float64"):
    """Return every uninterrupted carrying interval, never just a final frame.

    Samples describe the solved step's native kinematics. An interval includes
    one ``dt`` per sample; this is a discretely observed carrying diagnostic,
    not an assertion about unresolved motion within each step.
    """
    times, height = np.asarray(times), np.asarray(height)
    loaded = np.asarray(loaded_pairs)
    count = len(times)
    if times.shape != (count,) or height.shape != (count,) or loaded.shape != (count, 4) or \
            loaded.dtype.kind not in "iu" or (loaded < 0).any() or count == 0:
        raise ValueError("Invalid carrying trace")
    if clock_dtype not in ("float32", "float64"):
        raise ValueError("Invalid carrying clock precision")
    quantization = 2 * np.finfo(clock_dtype).eps * max(float(np.abs(times).max()), dt)
    if not all(np.isfinite(a).all() for a in (times, height, required_height, dt, hold_s)) or \
            dt <= 0 or hold_s <= 0 or not np.allclose(np.diff(times), dt, atol=quantization, rtol=0):
        raise ValueError("Invalid carrying clock or threshold")
    eligible = (height >= required_height) & (loaded[:, 0] > 0) & (loaded[:, 1] > 0) & \
               (loaded[:, 2] == 0) & (loaded[:, 3] == 0)
    edges = np.flatnonzero(np.diff(np.r_[False, eligible, False]))
    scalar = np.dtype(clock_dtype).type
    windows = [{"first_substep": int(start), "end_substep_exclusive": int(end),
                "start_s": float(times[start]),
                "end_s": float(scalar(scalar(times[end - 1]) + scalar(dt))),
                "native_clock_elapsed_s": float(scalar(scalar(times[end - 1]) + scalar(dt))) - float(times[start]),
                "duration_s": float((end - start) * dt)}
               for start, end in edges.reshape(-1, 2)]
    longest = max((window["duration_s"] for window in windows), default=0.)
    return {"windows": windows, "longest_s": longest, "reaches_diagnostic_window": longest >= hold_s,
            "duration_basis": "Native step count times the protocol timestep; quantized clock elapsed is reported separately",
            "task_success": None}


def hand_relative_positions(object_pos, hand_pos, hand_rotation):
    """Express an object's point in each hand frame to separate slip from travel."""
    point, position, rotation = map(np.asarray, (object_pos, hand_pos, hand_rotation))
    if point.shape != (3,) or position.shape != (2, 3) or rotation.shape != (2, 3, 3) or \
            not all(np.isfinite(a).all() for a in (point, position, rotation)) or \
            not np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=2e-5, rtol=0) or \
            not np.allclose(np.linalg.det(rotation), 1., atol=2e-5, rtol=0):
        raise ValueError("Invalid hand-relative kinematics")
    return np.einsum("nji,nj->ni", rotation, point - position)


def momentum_residual(first, second, force, torque_about_com, gravity, *, dt):
    """Residual of one solved-step impulse between adjacent native epochs.

    Use world-origin angular momentum so COM translation is included. The
    caller must expose unaccounted external forces, armature and epoch gaps;
    this diagnostic alone cannot qualify a physical model or identify a solver.
    """
    if not np.isfinite(dt) or dt <= 0 or first["mass_kg"] != second["mass_kg"]:
        raise ValueError("Momentum comparison needs fixed mass and a positive timestep")
    p0, p1 = (np.asarray(item["linear_momentum_kg_m_s"]) for item in (first, second))
    c0, c1 = (np.asarray(item["com_world_m"]) for item in (first, second))
    h0, h1 = (np.asarray(item["angular_momentum_about_com_kg_m2_s"]) for item in (first, second))
    force, torque, gravity = map(np.asarray, (force, torque_about_com, gravity))
    vectors = (p0, p1, c0, c1, h0, h1, force, torque, gravity)
    if any(a.shape != (3,) or not np.isfinite(a).all() for a in vectors) or \
            not np.isfinite(first["mass_kg"]) or first["mass_kg"] <= 0:
        raise ValueError("Invalid momentum/wrench observation")
    total_force = force + first["mass_kg"] * gravity
    return {"linear_ns": p1 - p0 - dt * total_force,
            "angular_nms": h1 + np.cross(c1, p1) - h0 - np.cross(c0, p0)
                           - dt * (torque + np.cross(c0, total_force))}


def compare_probe_values(reference, recorded, *, atol, rtol, path="record"):
    """Compare complete control records, including observations and reset flags."""
    if not np.isfinite([atol, rtol]).all() or min(atol, rtol) < 0:
        raise ValueError("Invalid parity tolerances")
    if isinstance(reference, dict):
        if not isinstance(recorded, dict) or set(reference) != set(recorded):
            raise ValueError(f"Probe record keys differ at {path}")
        return max((compare_probe_values(value, recorded[name], atol=atol, rtol=rtol,
                                        path=f"{path}.{name}")
                    for name, value in reference.items()), default=0.)
    if isinstance(reference, np.ndarray):
        if not isinstance(recorded, np.ndarray) or reference.shape != recorded.shape or \
                reference.dtype != recorded.dtype or not np.isfinite(reference).all() or \
                not np.isfinite(recorded).all():
            raise ValueError(f"Probe array shape, dtype or finiteness differs at {path}")
        if reference.dtype.kind in "biu":
            if not np.array_equal(reference, recorded):
                raise ValueError(f"Probe discrete values differ at {path}")
            return 0.
        if not np.allclose(reference, recorded, atol=atol, rtol=rtol):
            raise ValueError(f"Probe numerical values differ at {path}")
        return float(np.abs(reference - recorded).max(initial=0.))
    if type(reference) is float and type(recorded) is float:
        if not np.isfinite([reference, recorded]).all() or \
                abs(reference - recorded) > atol + rtol * abs(reference):
            raise ValueError(f"Probe numerical value differs at {path}")
        return abs(reference - recorded)
    if type(reference) is not type(recorded) or reference != recorded:
        raise ValueError(f"Probe value differs at {path}")
    return 0.


def decode_contact_forces(contacts, efc_force, *, cone):
    """Decode solved constraints; inactive contacts remain zero, missing data fails.

    ``cone`` is the actual MuJoCo enum readback: 0 pyramidal, 1 elliptic.
    The force is on geom[1], expressed in the contact frame. This reproduces
    the representation conversion, not a new contact solve or task score.
    """
    if cone not in (0, 1):
        raise ValueError("Unknown native friction cone")
    force = np.asarray(efc_force)
    dims = np.asarray(contacts["dim"])
    addresses = np.asarray(contacts["efc_address"])
    friction = np.asarray(contacts["friction"])
    ncon = len(dims)
    if force.ndim != 1 or not np.isfinite(force).all():
        raise ValueError("Invalid native constraint force")
    if dims.shape != (ncon,) or dims.dtype.kind not in "iu" or not np.isin(dims, [1, 3, 4, 6]).all():
        raise ValueError("Invalid contact dimension")
    if addresses.ndim != 2 or addresses.shape[0] != ncon or addresses.dtype.kind not in "iu":
        raise ValueError("Invalid native constraint addresses")
    if friction.shape != (ncon, 5) or not np.isfinite(friction).all() or (friction < 0).any():
        raise ValueError("Invalid contact friction")
    result = np.zeros((ncon, 6), dtype=float)
    claimed = set()
    for index, dim in enumerate(dims):
        width = int(max(1, 2 * (dim - 1))) if cone == 0 else int(dim)
        if addresses.shape[1] < width:
            raise ValueError("Truncated contact constraint addresses")
        slots = addresses[index, :width]
        if (slots == -1).all():
            continue
        if (slots < 0).any() or (slots >= force.size).any() or np.unique(slots).size != width:
            raise ValueError("Invalid or overflowed contact constraint addresses")
        if claimed.intersection(map(int, slots)):
            raise ValueError("Constraint addresses reused by different contacts")
        claimed.update(map(int, slots))
        if cone == 0 and not np.array_equal(slots, np.arange(slots[0], slots[0] + width)):
            raise ValueError("Pyramidal addresses differ from the pinned native decoder contract")
        values = force[slots]
        if cone == 1 or dim == 1:
            result[index, :dim] = values
        else:
            edges = values.reshape(-1, 2)
            result[index, 0] = edges.sum()
            result[index, 1:dim] = (edges[:, 0] - edges[:, 1]) * friction[index, :dim - 1]
    return result


def compare_contact_decoding(contacts, efc_force, *, cone, atol, rtol):
    """Report the independent decoding error separately from physical success."""
    if not np.isfinite([atol, rtol]).all() or min(atol, rtol) < 0:
        raise ValueError("Force comparison tolerances must be finite and nonnegative")
    expected = decode_contact_forces(contacts, efc_force, cone=cone)
    observed = np.asarray(contacts["local_force"])
    if observed.shape != expected.shape or not np.isfinite(observed).all():
        raise ValueError("Missing or invalid native decoded contact force")
    errors = np.abs(expected - observed)
    return {
        "passed": bool(np.all(errors <= atol + rtol * np.abs(expected))),
        "contacts": int(len(expected)),
        "maximum_component_error": float(errors.max(initial=0)),
        "comparison": "native GPU decoded force versus recorded constraint representation",
        "task_success": None,
    }


def object_contact_loads(contacts, *, object_geoms, left_geoms, right_geoms,
                         ground_geoms, object_com, ngeom, loaded_threshold_n):
    """Separate external support on the object from internal contacts.

    Groups are explicit compiled-model geom IDs, not guesses from a sensor's
    `found` flag. Counts are per loaded pair, so opposing forces do not erase
    contacts. Wrenches are about the supplied COM at the native force epoch.
    """
    groups = [set(group) for group in (object_geoms, left_geoms, right_geoms, ground_geoms)]
    if not all(groups) or any(not isinstance(g, (int, np.integer)) or isinstance(g, (bool, np.bool_))
                             or not 0 <= g < ngeom for group in groups for g in group):
        raise ValueError("Require nonempty compiled geometry groups with valid IDs")
    if any(a & b for i, a in enumerate(groups) for b in groups[i + 1:]):
        raise ValueError("Geometry ownership groups must be disjoint")
    if not np.isfinite(loaded_threshold_n) or loaded_threshold_n < 0:
        raise ValueError("Invalid loaded contact threshold")
    center = np.asarray(object_com)
    pairs = np.asarray(contacts["geom"])
    frames = np.asarray(contacts["frame"])
    points = np.asarray(contacts["pos"])
    local = np.asarray(contacts["local_force"])
    if pairs.ndim != 2 or pairs.shape[1] != 2 or pairs.dtype.kind not in "iu" or \
            (pairs < 0).any() or (pairs >= ngeom).any():
        raise ValueError("Invalid native contact pair identities")
    count = len(pairs)
    if center.shape != (3,) or frames.shape != (count, 3, 3) or \
            points.shape != (count, 3) or local.shape != (count, 6):
        raise ValueError("Invalid native contact wrench shapes")
    if not all(np.isfinite(a).all() for a in (center, frames, points, local)):
        raise ValueError("Nonfinite native contact wrench")
    if not np.allclose(frames @ frames.transpose(0, 2, 1), np.eye(3), atol=2e-5, rtol=0) or \
            not np.allclose(np.linalg.det(frames), 1., atol=2e-5, rtol=0):
        raise ValueError("Invalid native contact frame")
    result = {name: {"force_n": np.zeros(3), "torque_nm": np.zeros(3), "loaded_pairs": 0}
              for name in ("left", "right", "ground", "other")}
    obj, left, right, ground = groups
    for pair, frame, point, wrench in zip(pairs, frames, points, local):
        first, second = map(int, pair)
        if (first in obj) == (second in obj):
            continue  # internal object pair, or a pair entirely outside it
        sign, other = (1, first) if second in obj else (-1, second)
        force = sign * (frame.T @ wrench[:3])
        torque = sign * (frame.T @ wrench[3:]) + np.cross(point - center, force)
        name = "left" if other in left else "right" if other in right else "ground" if other in ground else "other"
        result[name]["force_n"] += force
        result[name]["torque_nm"] += torque
        result[name]["loaded_pairs"] += int(np.linalg.norm(force) > loaded_threshold_n)
    return result


def articulated_momentum(*, mass, inertia, body_ids, body_rootid, xipos, ximat,
                          cvel, subtree_com):
    """Compute whole-object momentum from native pre-integration kinematics.

    MuJoCo cvel is rotation:translation about the root subtree COM. Shift each
    body's linear velocity to its inertial COM before summing; a free-root
    velocity alone omits articulated descendants and rotational offsets.
    """
    mass, inertia = np.asarray(mass), np.asarray(inertia)
    roots, ids = np.asarray(body_rootid), np.asarray(body_ids)
    pos, rotations = np.asarray(xipos), np.asarray(ximat)
    velocity, centers = np.asarray(cvel), np.asarray(subtree_com)
    count = mass.size
    if mass.shape != (count,) or inertia.shape != (count, 3) or \
            roots.shape != (count,) or roots.dtype.kind not in "iu" or \
            pos.shape != (count, 3) or rotations.shape != (count, 3, 3) or \
            velocity.shape != (count, 6) or centers.shape != (count, 3):
        raise ValueError("Invalid native body kinematics shapes")
    if ids.ndim != 1 or ids.size == 0 or ids.dtype.kind not in "iu" or \
            (ids <= 0).any() or (ids >= count).any() or np.unique(ids).size != ids.size or \
            (roots < 0).any() or (roots >= count).any():
        raise ValueError("Invalid object body identities")
    if not all(np.isfinite(a).all() for a in (mass, inertia, pos, rotations, velocity, centers)) or \
            (mass < 0).any() or (inertia < 0).any() or mass[ids].sum() <= 0:
        raise ValueError("Invalid effective mass/inertia or body kinematics")
    rotation = rotations[ids]
    if not np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=2e-5, rtol=0) or \
            not np.allclose(np.linalg.det(rotation), 1., atol=2e-5, rtol=0):
        raise ValueError("Invalid native inertial orientation")
    omega = velocity[ids, :3]
    linear = velocity[ids, 3:] + np.cross(omega, pos[ids] - centers[roots[ids]])
    body_momentum = mass[ids, None] * linear
    center = np.sum(mass[ids, None] * pos[ids], axis=0) / mass[ids].sum()
    # Transform angular velocity to each principal-inertia frame and back.
    local_omega = np.einsum("nji,nj->ni", rotation, omega)
    spin = np.einsum("nij,nj->ni", rotation, inertia[ids] * local_omega)
    angular = spin + np.cross(pos[ids] - center, body_momentum)
    return {"mass_kg": float(mass[ids].sum()), "com_world_m": center,
            "linear_momentum_kg_m_s": body_momentum.sum(axis=0),
            "angular_momentum_about_com_kg_m2_s": angular.sum(axis=0)}
