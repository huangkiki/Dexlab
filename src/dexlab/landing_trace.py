"""Align recorded control states with native substeps without changing evidence.

This audit detects representation and recording errors. It does not rerun a
controller, replace native forces, or decide whether a landing is successful.
"""

import numpy as np


def _finite(value, shape, name):
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in "iuf" or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite numeric array with shape {shape}")
    return array.astype(float, copy=False)


def _positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def joint_indices(reference_names, native_names):
    """Return the native one-DoF joint order for each reference joint.

    Native USD-derived names may have a slash or flattened underscore path
    prefix. Match a complete reference name at that boundary; reject ambiguous
    suffixes, missing joints and extra joints.
    The free root is not included in either list.
    """
    reference = list(reference_names)
    native = list(native_names)
    if not reference or any(not isinstance(name, str) or not name for name in reference + native):
        raise ValueError("Joint names must be nonempty strings")
    if len(set(reference)) != len(reference) or len(set(native)) != len(native):
        raise ValueError("Joint names are ambiguous")
    if len(reference) != len(native):
        raise ValueError("Reference and native joints differ")
    matches = [[i for i, name in enumerate(native)
                if name == ref or name.endswith(("/" + ref, "_" + ref))]
               for ref in reference]
    if any(len(indices) != 1 for indices in matches):
        raise ValueError("Missing or ambiguous native joint suffix")
    order = np.asarray([indices[0] for indices in matches], dtype=int)
    if len(set(order)) != len(native):
        raise ValueError("Native joint mapping is not one-to-one")
    return order


def align_states(rollout, substeps, reference_names, native_names, *, controls,
                 substeps_per_control, physics_dt, state_tolerance):
    """Compare free-root/hinge states at exact, complete control boundaries.

    ``rollout`` has qpos followed by qvel, including the initial state. Native
    qpos/qvel are copied after each physics substep, excluding the initial state.
    Both use a world position, wxyz root quaternion, world linear velocity and
    body angular velocity. The caller must qualify that coordinate contract.
    Quaternion signs are equivalent; joint permutations are reported separately.
    """
    controls = _positive_int(controls, "controls")
    ratio = _positive_int(substeps_per_control, "substeps_per_control")
    if not np.isfinite(physics_dt) or physics_dt <= 0:
        raise ValueError("physics_dt must be positive and finite")
    if not np.isfinite(state_tolerance) or state_tolerance < 0:
        raise ValueError("state_tolerance must be finite and nonnegative")
    order = joint_indices(reference_names, native_names)
    dofs = len(order)
    count = controls * ratio
    states = _finite(rollout, (controls + 1, 13 + 2 * dofs), "rollout states")
    qpos = _finite(substeps["qpos"], (count, 7 + dofs), "native qpos")
    qvel = _finite(substeps["qvel"], (count, 6 + dofs), "native qvel")
    times = _finite(substeps["time"], (count,), "native time")
    if not np.allclose(times, np.arange(1, count + 1) * physics_dt, rtol=0, atol=1e-8):
        raise ValueError("Missing, shifted, repeated or reset native timestamps")
    for name, quat in (("control", states[:, 3:7]), ("native", qpos[:, 3:7])):
        if not np.allclose(np.linalg.norm(quat, axis=1), 1, rtol=0, atol=1e-5):
            raise ValueError(f"Nonunit {name} root quaternion")

    ends = np.arange(ratio - 1, count, ratio)
    native_pos, native_vel = qpos[ends], qvel[ends]
    control_pos, control_vel = states[1:, :7 + dofs], states[1:, 7 + dofs:]
    quat_error = np.minimum(np.linalg.norm(control_pos[:, 3:7] - native_pos[:, 3:7], axis=1),
                            np.linalg.norm(control_pos[:, 3:7] + native_pos[:, 3:7], axis=1))
    errors = {
        "root_position_m": np.max(np.abs(control_pos[:, :3] - native_pos[:, :3]), axis=1),
        "root_quaternion_chord": quat_error,
        "joint_position_rad": np.max(np.abs(control_pos[:, 7:] - native_pos[:, 7 + order]), axis=1),
        "root_linear_velocity_m_s": np.max(np.abs(control_vel[:, :3] - native_vel[:, :3]), axis=1),
        "root_angular_velocity_rad_s": np.max(np.abs(control_vel[:, 3:6] - native_vel[:, 3:6]), axis=1),
        "joint_velocity_rad_s": np.max(np.abs(control_vel[:, 6:] - native_vel[:, 6 + order]), axis=1),
    }
    mismatched = np.logical_or.reduce([error > state_tolerance for error in errors.values()])
    return {
        "controls": controls,
        "native_substeps": count,
        "physics_dt_s": float(physics_dt),
        "control_dt_s": float(physics_dt * ratio),
        "native_order_for_reference": order.tolist(),
        "joint_order_identical": bool(np.array_equal(order, np.arange(dofs))),
        "unmapped_joint_position_max_rad": float(np.max(np.abs(control_pos[:, 7:] - native_pos[:, 7:]))),
        "mapped_max_errors": {name: float(error.max()) for name, error in errors.items()},
        "mismatched_control_frames": (np.flatnonzero(mismatched) + 1).tolist(),
        "aligned": bool(not mismatched.any()),
        "limitation": "Agreement of exposed states does not establish solver-cache equality or physical success.",
    }


def compare_contact_evidence(geometry, forces, *, penetration_tolerance_m, force_threshold_n):
    """Compare time-aligned geometric penetration with recorded nonfoot force.

    Geometry is an independently reconstructed minimum signed distance per
    sample. Native force is a recorded resultant, not reconstructed force. A
    resultant can cancel: its absence cannot prove absence of individual forces.
    Pairwise records are needed to resolve that ambiguity.
    """
    geometry = np.asarray(geometry)
    if geometry.ndim != 1 or not len(geometry):
        raise ValueError("Geometry must contain one signed distance per sample")
    geometry = _finite(geometry, geometry.shape, "geometry distance")
    forces = _finite(forces, (len(geometry), 3), "native nonfoot force")
    if (not np.isfinite(penetration_tolerance_m) or penetration_tolerance_m < 0
            or not np.isfinite(force_threshold_n) or force_threshold_n < 0):
        raise ValueError("Contact thresholds must be finite and nonnegative")
    penetrating = geometry < -penetration_tolerance_m
    loaded = np.linalg.norm(forces, axis=1) > force_threshold_n
    return {
        "samples": len(geometry),
        "penetration_samples": np.flatnonzero(penetrating).tolist(),
        "loaded_resultant_samples": np.flatnonzero(loaded).tolist(),
        "penetration_without_loaded_resultant": np.flatnonzero(penetrating & ~loaded).tolist(),
        "loaded_resultant_without_penetration": np.flatnonzero(loaded & ~penetrating).tolist(),
        "maximum_penetration_m": float(max(0, -geometry.min())),
        "maximum_resultant_n": float(np.linalg.norm(forces, axis=1).max()),
        "contact_epoch": "must be qualified separately; equal array indices are not proof",
        "task_success": None,
    }


def contact_pairs(offsets, pairs, distances, local_forces, *, steps, geom_count):
    """Validate a complete ragged native contact stream, including empty steps."""
    steps = _positive_int(steps, "steps")
    geom_count = _positive_int(geom_count, "geom_count")
    offsets = np.asarray(offsets)
    pairs = np.asarray(pairs)
    if (offsets.shape != (steps + 1,) or offsets.dtype.kind not in "iu"
            or offsets[0] != 0 or np.any(offsets[1:] < offsets[:-1])):
        raise ValueError("Invalid native contact offsets")
    count = int(offsets[-1])
    if pairs.shape != (count, 2) or pairs.dtype.kind not in "iu":
        raise ValueError("Invalid contact geometry pairs")
    if np.any(pairs < 0) or np.any(pairs >= geom_count) or np.any(pairs[:, 0] == pairs[:, 1]):
        raise ValueError("Invalid contact geometry IDs")
    _finite(distances, (count,), "native contact distances")
    _finite(local_forces, (count, 6), "native contact forces")
    return [slice(int(start), int(end)) for start, end in zip(offsets[:-1], offsets[1:])]
