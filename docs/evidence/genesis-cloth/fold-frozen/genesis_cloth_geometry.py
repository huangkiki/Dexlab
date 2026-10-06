"""Every-saved-frame triangle audit plus an explicitly linear plane sweep."""

import numpy as np

from .cloth_self_contact import crossing_count, nonadjacent_pairs


def audit(positions, faces, times, *, plane_z=None):
    """Audit recorded geometry; never infer actual inter-step engine trajectories."""
    p = np.asarray(positions, dtype=float)
    f = np.asarray(faces)
    t = np.asarray(times, dtype=float)
    if (
        p.ndim != 3
        or p.shape[2] != 3
        or len(p) < 2
        or not np.isfinite(p).all()
        or t.shape != (len(p),)
        or not np.isfinite(t).all()
        or (np.diff(t) <= 0).any()
        or f.ndim != 2
        or f.shape[1] != 3
        or not len(f)
        or not np.issubdtype(f.dtype, np.integer)
        or (f < 0).any()
        or (f >= p.shape[1]).any()
    ):
        raise ValueError("Invalid saved geometry or time grid")
    pairs = nonadjacent_pairs(f)
    counts = [crossing_count(vertices, f, pairs) for vertices in p]
    result = {
        "frames": len(p),
        "max_interval_s": float(np.diff(t).max()),
        "maximum_crossing_pairs": max(c[0] for c in counts),
        "frames_with_self_crossing": sum(c[0] > 0 for c in counts),
        "maximum_degenerate_triangles": max(c[1] for c in counts),
        "scope": "Every saved frame; shared-vertex triangle pairs excluded. No general swept self-contact or thickness guarantee.",
    }
    if plane_z is not None:
        if not np.isfinite(plane_z):
            raise ValueError("Nonfinite plane")
        z = p[:, :, 2] - plane_z
        result["plane"] = {
            "minimum_signed_distance_m": float(z.min()),
            "maximum_midsurface_depth_m": float(max(0.0, -z.min())),
            "crossing_intervals": int(
                np.count_nonzero(
                    np.any(
                        ((z[:-1] > 0) & (z[1:] < 0)) | ((z[:-1] < 0) & (z[1:] > 0)),
                        axis=1,
                    )
                )
            ),
            "linear_sweep_minimum_m": float(z.min()),
            "scope": "For straight interpolation of vertices against a fixed horizontal plane, the space-time minimum occurs at an endpoint vertex. This does not certify the engine path between observations.",
        }
    return result


def audit_prismatic_pads(rows, faces, halfsize=(0.01, 0.03, 0.02)):
    """Audit triangle interiors against recorded nonrotating box pads.

    Uses the existing independent triangle/box linear program. This is a saved-
    frame test, not a continuous-time or contact-force measurement.
    """
    from .cloth_table_audit import triangle_box_depth

    f = np.asarray(faces)
    size = np.asarray(halfsize, float)
    if (
        f.ndim != 2
        or f.shape[1] != 3
        or not len(f)
        or not np.issubdtype(f.dtype, np.integer)
        or (f < 0).any()
        or size.shape != (3,)
        or not np.isfinite(size).all()
        or (size <= 0).any()
        or not rows
    ):
        raise ValueError("Invalid triangle/pad geometry")
    maximum = 0.0
    witness = None
    checked = 0
    previous_step = -1
    for row in rows:
        points = np.asarray(row["pos"], float)
        centers = np.asarray(row["pad_pos"], float)
        quat = np.asarray(row["pad_quat"], float)
        if (
            points.ndim != 2
            or points.shape[1] != 3
            or (f >= len(points)).any()
            or centers.shape != (2, 3)
            or quat.shape != (2, 4)
            or any(not np.isfinite(x).all() for x in (points, centers, quat))
            or np.max(abs(abs(quat[:, 0]) - 1)) > 1e-8
            or np.max(abs(quat[:, 1:])) > 1e-8
            or row["step"] != previous_step + 1
        ):
            raise ValueError("Invalid/missing pad observation or rotating pad")
        previous_step = row["step"]
        triangles = points[f]
        for pad, center in enumerate(centers):
            lower, upper = center - size, center + size
            candidates = np.flatnonzero(
                (triangles.max(axis=1) >= lower).all(axis=1)
                & (triangles.min(axis=1) <= upper).all(axis=1)
            )
            for face in candidates:
                checked += 1
                depth = triangle_box_depth(triangles[face], lower, upper)
                if depth > maximum:
                    maximum = depth
                    witness = {"step": row["step"], "pad": pad, "face": int(face)}
    return {
        "frames": len(rows),
        "candidate_triangle_checks": checked,
        "maximum_triangle_interior_depth_m": maximum,
        "witness": witness,
        "scope": "Every saved frame; independent triangle interior/box LP; nonrotating prismatic pads only; no inter-step certification.",
    }
