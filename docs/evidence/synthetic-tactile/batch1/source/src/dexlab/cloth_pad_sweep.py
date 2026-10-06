"""Exact segment/slab audit under linear vertex and translating-box interpolation."""

import numpy as np


def audit(rows, halfsize=(0.01, 0.03, 0.02)):
    """Find vertex intrusion intervals; this does not cover triangle interiors.

    Relative vertex/pad motion is linear between observations. Pad orientations
    must stay identity. A 1e-12 m inset excludes numerical boundary touches.
    No claim is made about the engine's unobserved intra-step trajectory.
    """
    if len(rows) < 2:
        raise ValueError("Require at least two observations")
    points = np.asarray([r["pos"] for r in rows], dtype=float)
    pads = np.asarray([r["pad_pos"] for r in rows], dtype=float)
    quats = np.asarray([r["pad_quat"] for r in rows], dtype=float)
    size = np.asarray(halfsize, dtype=float)
    if (
        [r["step"] for r in rows] != list(range(len(rows)))
        or points.ndim != 3
        or points.shape[2] != 3
        or points.shape[1] == 0
        or pads.shape != (len(rows), 2, 3)
        or quats.shape != (len(rows), 2, 4)
        or size.shape != (3,)
        or (size <= 1e-12).any()
        or any(not np.isfinite(a).all() for a in (points, pads, quats, size))
        or np.max(abs(abs(quats[:, :, 0]) - 1)) > 1e-8
        or np.max(abs(quats[:, :, 1:])) > 1e-8
    ):
        raise ValueError("Invalid contiguous state or translating-pad assumption")
    relative = points[:, :, None, :] - pads[:, None, :, :]
    start, end = relative[:-1], relative[1:]
    delta = end - start
    bound = size - 1e-12
    moving = delta != 0
    a = np.divide(-bound - start, delta, out=np.zeros_like(delta), where=moving)
    b = np.divide(bound - start, delta, out=np.zeros_like(delta), where=moving)
    enter = np.where(moving, np.minimum(a, b), -np.inf).max(axis=-1)
    leave = np.where(moving, np.maximum(a, b), np.inf).min(axis=-1)
    parallel_outside = ((~moving) & (abs(start) >= bound)).any(axis=-1)
    enter, leave = np.maximum(enter, 0), np.minimum(leave, 1)
    hit = (~parallel_outside) & (enter < leave)
    endpoint_inside = (abs(start) < bound).all(axis=-1) | (abs(end) < bound).all(
        axis=-1
    )
    hidden = hit & ~endpoint_inside
    indices = np.argwhere(hidden)
    witness = None
    if len(indices):
        interval, vertex, pad = map(int, indices[0])
        witness = {
            "start_step": interval,
            "vertex": vertex,
            "pad": pad,
            "enter_fraction": float(enter[interval, vertex, pad]),
            "exit_fraction": float(leave[interval, vertex, pad]),
        }
    return {
        "intervals": len(rows) - 1,
        "vertex_pad_interval_tests": int(hit.size),
        "intruding_vertex_pad_intervals": int(hit.sum()),
        "endpoint_invisible_intrusion_intervals": int(hidden.sum()),
        "first_endpoint_invisible_witness": witness,
        "boundary_inset_m": 1e-12,
        "scope": "Linear interpolation only; vertices versus translating axis-aligned pads. Excludes triangle/edge interior crossings, physical cloth thickness and the actual unobserved engine path.",
    }
