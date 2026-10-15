"""Fixed analytic-box queries and offline metrics; no native qualification.

This prospective cohort preserves the historical box dimensions and pose while
adding both sides of each face. Distance-query finite differences are reported
as such: they are neither native gradients nor native contact normals.
"""
from itertools import product

import numpy as np


PROTOCOL = "analytic-box-near-surface-v1"
HALF_SIZE = np.array([0.02, 0.015, 0.01])
TRANSLATION = np.array([0.1, 0.2, 0.3])
ROTATION = np.array([
    [np.cos(0.7), -np.sin(0.7), 0.0],
    [np.sin(0.7), np.cos(0.7), 0.0],
    [0.0, 0.0, 1.0],
])
OFFSETS_M = (-0.0004, -0.0001, 0.0, 0.0001, 0.0004)
DIFFERENCE_STEPS_M = np.array([0.00002, 0.00001, 0.000005])
COORDINATE_ATOL_M = 1e-12  # Serialized-coordinate identity, not accuracy.


def _real_array(value):
    array = np.asarray(value)
    if array.dtype.kind not in "fiu":
        raise ValueError("Expected real numeric samples")
    try:
        with np.errstate(over="raise", invalid="raise"):
            return array.astype(np.float64, copy=False)
    except FloatingPointError as error:
        raise ValueError("Sample conversion is not representable") from error


def box_reference(points):
    """Return signed distance, outward unit gradient, and differentiability.

    Distances are negative inside the closed box. Normals at equidistant inside
    faces or sharp surface features are undefined and returned as NaN, with an
    explicit false mask. No arbitrary sharp-feature normal is selected.
    """
    points = _real_array(points)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite local points of shape (N, 3)")
    q = np.abs(points) - HALF_SIZE
    outside = np.maximum(q, 0.0)
    with np.errstate(over="ignore"):
        length = np.hypot.reduce(outside, axis=1)
    if not np.isfinite(length).all():
        raise ValueError("Reference distance is not representable")
    distance = length + np.minimum(q.max(axis=1), 0.0)
    normal = np.full(points.shape, np.nan)
    differentiable = length > 0.0
    normal[differentiable] = (
        np.sign(points[differentiable]) * outside[differentiable]
        / length[differentiable, None]
    )
    for i in np.flatnonzero(~differentiable):
        nearest = np.flatnonzero(q[i] == q[i].max())
        if len(nearest) == 1 and points[i, nearest[0]] != 0.0:
            normal[i] = 0.0
            normal[i, nearest[0]] = np.sign(points[i, nearest[0]])
            differentiable[i] = True
    return distance, normal, differentiable


def query_cohort():
    """Return 270 centers and all 4,860 central-difference stencil points.

    Every face uses a 3x3 tangential lattice at -1/2, 0, 1/2 half-extents,
    with five fixed normal offsets. Stencils use local axes and +/- h in that
    order. The same 5,130 world points must be used at every spatial level.
    """
    centers, offsets, normals = [], [], []
    for axis, sign in product(range(3), (-1, 1)):
        tangents = [i for i in range(3) if i != axis]
        for u, v, offset in product((-0.5, 0.0, 0.5), (-0.5, 0.0, 0.5), OFFSETS_M):
            point = np.zeros(3)
            point[axis] = sign * (HALF_SIZE[axis] + offset)
            point[tangents] = np.array([u, v]) * HALF_SIZE[tangents]
            normal = np.zeros(3)
            normal[axis] = sign
            centers.append(point)
            offsets.append(offset)
            normals.append(normal)
    centers = np.array(centers)
    stencil = (
        centers[:, None, None, None, :]
        + DIFFERENCE_STEPS_M[None, :, None, None, None]
        * np.eye(3)[None, None, :, None, :]
        * np.array([-1.0, 1.0])[None, None, None, :, None]
    )
    local = np.concatenate([centers, stencil.reshape(-1, 3)])
    return {
        "local_m": local,
        "world_m": local @ ROTATION.T + TRANSLATION,
        "center_offsets_m": np.array(offsets),
        "center_normals_local": np.array(normals),
        "stencil_shape": stencil.shape[:-1],
    }


def _errors(values):
    if values.size == 0:
        return {"count": 0, "max_absolute": None, "rms": None, "mean_signed": None}
    scale = float(np.max(np.abs(values)))
    scaled = values / scale if scale else values
    return {
        "count": int(values.size),
        "max_absolute": scale,
        "rms": float(scale * np.sqrt(np.mean(scaled**2))),
        "mean_signed": float(scale * np.mean(scaled)),
    }


def score_queries(local_m, world_m, distances_m, signed_distance_supported):
    """Measure declared distance queries without asserting physical accuracy.

    The caller must obtain the support mask from the actual query domain and
    documented API semantics. This arithmetic helper cannot establish that
    provenance. Unsupported/missing queries remain in the denominator and
    invalidate dependent stencils; they are never silently scored as distances.
    """
    cohort = query_cohort()
    local, world = _real_array(local_m), _real_array(world_m)
    distances = _real_array(distances_m)
    supported = np.asarray(signed_distance_supported)
    expected = cohort["local_m"]
    if (local.shape != expected.shape or world.shape != expected.shape
            or distances.shape != (len(expected),)
            or supported.shape != distances.shape or supported.dtype != np.dtype(bool)):
        raise ValueError("Incomplete cohort, distances, or explicit boolean support mask")
    for actual, reference in ((local, expected), (world, cohort["world_m"])):
        if (not np.isfinite(actual).all()
                or not np.allclose(actual, reference, rtol=0, atol=COORDINATE_ATOL_M)):
            raise ValueError("Changed query cohort or incorrect coordinate frame")
    if not np.isfinite(distances[supported]).all():
        raise ValueError("Nonfinite value declared to be a supported distance query")

    offsets = cohort["center_offsets_m"]
    count = len(offsets)
    center_supported = supported[:count]
    errors = distances[:count] - offsets
    regions = {}
    for label, region in (("inside", offsets < 0), ("surface", offsets == 0),
                          ("outside", offsets > 0)):
        measured = region & center_supported
        regions[label] = {
            "expected_count": int(region.sum()),
            "supported_count": int(measured.sum()),
            "distance_error_m": _errors(errors[measured]),
            # Zero-distance surface residuals are reported above, never judged
            # by a float sign or an invented near-surface accuracy tolerance.
            "sign_mismatches": None if label == "surface" or not measured.any()
            else int(np.count_nonzero(
                np.sign(distances[:count][measured]) != np.sign(offsets[measured]))),
        }

    stencil = distances[count:].reshape(cohort["stencil_shape"])
    stencil_support = supported[count:].reshape(cohort["stencil_shape"])
    gradient_rows = []
    for i, step in enumerate(DIFFERENCE_STEPS_M):
        complete = center_supported & stencil_support[:, i].all(axis=(1, 2))
        gradient = np.full((count, 3), np.nan)
        try:
            with np.errstate(over="raise", invalid="raise"):
                gradient[complete] = (
                    stencil[complete, i, :, 1] - stencil[complete, i, :, 0]
                ) / (2 * step)
                norm = np.hypot.reduce(gradient, axis=1)
        except FloatingPointError as error:
            raise ValueError("Distance-gradient arithmetic is not representable") from error
        directed = complete & (norm > 0)
        reference = cohort["center_normals_local"][directed]
        selected = gradient[directed] / norm[directed, None]
        angle = np.degrees(np.arctan2(
            np.linalg.norm(np.cross(selected, reference), axis=1),
            np.sum(selected * reference, axis=1),
        ))
        per_query_angles = [None] * count
        for row, value in zip(np.flatnonzero(directed), angle):
            per_query_angles[int(row)] = float(value)
        gradient_rows.append({
            "difference_step_m": float(step),
            "expected_count": count,
            "complete_stencil_count": int(complete.sum()),
            "zero_gradient_count": int(np.count_nonzero(complete & (norm == 0))),
            "undefined_direction_count": int(np.count_nonzero(~directed)),
            "gradient_norm_minus_one": _errors(norm[complete] - 1),
            "angle_error_deg": _errors(angle),
            "angle_error_by_center_deg": per_query_angles,
        })
    return {
        "protocol": PROTOCOL,
        "expected_query_count": len(expected),
        "declared_supported_query_count": int(supported.sum()),
        "unsupported_query_indices": np.flatnonzero(~supported).tolist(),
        "all_queries_declared_supported": bool(supported.all()),
        "distance_regions": regions,
        "distance_query_gradient": gradient_rows,
        "scope": "Offline analytic-box metrics under a caller-provided support mask; "
                 "native domain, geometry and provenance require separate verification. "
                 "Finite differences are not native gradients/contact normals. "
                 "No accuracy threshold, refinement pass, apple qualification or physics result.",
    }
