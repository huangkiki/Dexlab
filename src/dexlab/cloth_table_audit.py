"""Exploratory triangle-interior audit of a tiled, axis-aligned solid table.

This reads recorded positions only. Native contact distances, collision radius
and physical acceptance thresholds are deliberately separate from this metric.
"""

from collections import Counter
from itertools import product

import numpy as np
from scipy.optimize import linprog

NUMERICAL_EPS_M = 1e-8


def tiled_box_bounds(centers, half_sizes):
    """Prove disjoint box interiors fill their bounding box before merging them."""
    centers, half_sizes = np.asarray(centers), np.asarray(half_sizes)
    if (centers.ndim != 2 or centers.shape[1:] != (3,)
            or centers.shape != half_sizes.shape or not len(centers)
            or not np.isfinite(centers).all() or not np.isfinite(half_sizes).all()
            or np.any(half_sizes <= 0)):
        raise ValueError("Expected finite nonempty positive boxes")
    lower, upper = centers - half_sizes, centers + half_sizes
    lo, hi = lower.min(axis=0), upper.max(axis=0)
    for i in range(len(centers)):
        overlaps = np.minimum(upper[i], upper[i + 1:]) - np.maximum(lower[i], lower[i + 1:])
        if np.any(np.all(overlaps > 1e-12, axis=1)):
            raise ValueError("Overlapping tile interiors cannot be merged")
    volume = np.prod(hi - lo)
    if not np.isclose(np.prod(2 * half_sizes, axis=1).sum(), volume, rtol=1e-10, atol=1e-15):
        raise ValueError("Table tiles do not fill a solid box")
    return lo, hi


def verified_table_bounds(model, data):
    import mujoco

    ids = [g for g in range(model.ngeom) if (model.geom(g).name or '').startswith('table_')]
    if not ids or any(model.body_weldid[model.geom_bodyid[g]] != 0 for g in ids):
        raise ValueError('Expected fixed named table solids')
    lower, upper, mesh_count, corner_error = [], [], 0, 0.0
    signs = np.array(list(product((0, 1), repeat=3)))
    for geom in ids:
        kind = model.geom_type[geom]
        rotation = data.geom_xmat[geom].reshape(3, 3)
        if kind == mujoco.mjtGeom.mjGEOM_BOX:
            if not np.allclose(rotation, np.eye(3), atol=1e-12, rtol=0):
                raise ValueError('Rotated table boxes are unsupported')
            lo, hi = data.geom_xpos[geom] - model.geom_size[geom], data.geom_xpos[geom] + model.geom_size[geom]
        elif kind == mujoco.mjtGeom.mjGEOM_MESH:
            mesh_count += 1
            mid = model.geom_dataid[geom]
            va, vn = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
            fa, fn = model.mesh_faceadr[mid], model.mesh_facenum[mid]
            if vn != 8 or fn != 12:
                raise ValueError('Only eight-corner, twelve-face cuboid meshes are supported')
            graph = int(model.mesh_graphadr[mid])
            if graph < 0:
                raise ValueError('Missing native table collision hull')
            count = int(model.mesh_graph[graph])
            hull_ids = model.mesh_graph[graph+2+count:graph+2+2*count]
            if count != 8 or not np.array_equal(np.sort(hull_ids), np.arange(8)):
                raise ValueError('Native table collision hull does not preserve all cuboid corners')
            points = model.mesh_vert[va:va+vn].astype(float) @ rotation.T + data.geom_xpos[geom]
            if not np.isfinite(points).all():
                raise ValueError('Nonfinite table mesh')
            lo, hi = points.min(axis=0), points.max(axis=0)
            corners = lo + signs * (hi-lo)
            distances = np.linalg.norm(points[:, None] - corners[None, :], axis=2)
            correspondence = distances.argmin(axis=1)
            error = float(distances.min(axis=1).max())
            if len(set(correspondence)) != 8 or error > NUMERICAL_EPS_M:
                raise ValueError('Table mesh vertices do not form an axis-aligned cuboid')
            faces = model.mesh_face[fa:fa+fn]
            if np.any(faces < 0) or np.any(faces >= 8):
                raise ValueError('Invalid table mesh face indices')
            edges = Counter(tuple(sorted((int(face[i]), int(face[(i+1)%3]))))
                            for face in faces for i in range(3))
            if any(count != 2 for count in edges.values()):
                raise ValueError('Table mesh is not a closed triangular surface')
            area = 0.0
            for triangle in points[faces]:
                if not any(np.all(np.abs(triangle[:, axis]-bound) <= NUMERICAL_EPS_M)
                           for axis in range(3) for bound in (lo[axis], hi[axis])):
                    raise ValueError('Table mesh triangle cuts through its bounding box')
                area += np.linalg.norm(np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]))/2
            size = hi-lo
            if not np.isclose(area, 2*(size[0]*size[1]+size[0]*size[2]+size[1]*size[2]), rtol=1e-10, atol=1e-12):
                raise ValueError('Table mesh does not cover its cuboid surface')
            corner_error = max(corner_error, error)
        else:
            raise ValueError('Unsupported table solid')
        lower.append(lo); upper.append(hi)
    lower, upper = np.array(lower), np.array(upper)
    snap_error = 0.0
    if mesh_count:
        # Compiler float mesh storage may separate originally coincident planes
        # by nanometres. Reconcile only within the existing 10 nm numerical zero;
        # do not change triangle intrusion or physical acceptance thresholds.
        original = np.vstack((lower, upper))
        snapped = original.copy()
        for axis in range(3):
            order = np.argsort(original[:, axis]); start = 0
            while start < len(order):
                stop = start+1
                while stop < len(order) and original[order[stop], axis]-original[order[start], axis] <= NUMERICAL_EPS_M:
                    stop += 1
                group = order[start:stop]
                snapped[group, axis] = original[group, axis].mean()
                start = stop
        snap_error = float(np.max(np.abs(snapped-original)))
        lower, upper = np.split(snapped, 2)
    lo, hi = tiled_box_bounds((lower+upper)/2, (upper-lower)/2)
    return lo, hi, {'box_count': len(ids)-mesh_count, 'verified_cuboid_mesh_count': mesh_count,
                    'maximum_corner_residual_m': corner_error, 'maximum_tile_plane_snap_m': snap_error,
                    'mesh_geometry_zero_tolerance_m': NUMERICAL_EPS_M}


def triangle_box_depth(triangle, lower, upper):
    """Maximum distance to the nearest box face over points in a triangle.

    p = p0 + s*(p1-p0) + t*(p2-p0), s,t>=0, s+t<=1.
    Maximize d>=0 subject to lower+d <= p <= upper-d (a linear program).
    Vertices can all be outside while the triangle interior intersects the box.
    """
    triangle, lower, upper = map(np.asarray, (triangle, lower, upper))
    if (triangle.shape != (3, 3) or lower.shape != (3,) or upper.shape != (3,)
            or not all(np.isfinite(x).all() for x in (triangle, lower, upper))
            or np.any(upper <= lower)):
        raise ValueError("Invalid triangle or box")
    if np.any(triangle.max(axis=0) < lower) or np.any(triangle.min(axis=0) > upper):
        return 0.0
    p, a, b = triangle[0], triangle[1] - triangle[0], triangle[2] - triangle[0]
    matrix, bound = [], []
    for axis in range(3):
        matrix.extend(([a[axis], b[axis], 1], [-a[axis], -b[axis], 1]))
        bound.extend((upper[axis] - p[axis], p[axis] - lower[axis]))
    matrix.append([1, 1, 0])
    bound.append(1)
    solution = linprog(
        [0, 0, -1], A_ub=matrix, b_ub=bound, bounds=[(0, None)] * 3,
        method="highs", options={"primal_feasibility_tolerance": 1e-9},
    )
    if solution.status == 2:  # Infeasible: no triangle point inside the box.
        return 0.0
    if not solution.success:
        raise RuntimeError(f"Triangle-box LP failed: {solution.message}")
    return max(0.0, float(solution.x[2]))


def audit_table(model, times, poses, triangles, vertices):
    """Audit this demo's table only; unsupported geometry is never a zero."""
    import mujoco

    ids = [g for g in range(model.ngeom) if (model.geom(g).name or "").startswith("table_")]
    if not ids:
        return {"status": "unsupported_geometry", "reason": "Expected fixed named table solids"}
    data = mujoco.MjData(model)
    rows = []
    first_bounds = None
    try:
        for time, pose, points in zip(times, poses, vertices, strict=True):
            data.qpos[:] = pose
            mujoco.mj_fwdPosition(model, data)
            lo, hi, geometry = verified_table_bounds(model, data)
            if first_bounds is None:
                first_bounds = [lo.tolist(), hi.tolist()]
            elif not np.allclose([lo, hi], first_bounds, atol=1e-12, rtol=0):
                raise ValueError("Moving table is outside this diagnostic")
            depths = [triangle_box_depth(face, lo, hi) for face in points[triangles]]
            vertex_depth = np.maximum(np.minimum(points - lo, hi - points).min(axis=1), 0)
            rows.append({
                "time_s": float(time), "triangle_max_interior_depth_m": max(depths),
                "vertex_max_interior_depth_m": float(vertex_depth.max()),
                "triangles_with_interior_points": sum(d > NUMERICAL_EPS_M for d in depths),
            })
    except (ValueError, RuntimeError) as error:
        return {"status": "insufficient_evidence", "reason": str(error)}
    if not rows:
        return {"status": "insufficient_evidence", "reason": "No saved states"}
    affected = [row for row in rows if row["triangle_max_interior_depth_m"] > NUMERICAL_EPS_M]
    return {
        "version": "table-triangle-interior-v1",
        "status": "sampled_intrusion_detected" if affected else "no_sampled_intrusion",
        "classification": "exploratory_diagnostic_not_a_new_physical_threshold",
        "method": "LP over zero-thickness triangle interiors in verified union of table boxes",
        "table_bounds_m": first_bounds, "table_geom_count": len(ids),
        "table_geometry_verification": geometry,
        "numerical_zero_tolerance_m": NUMERICAL_EPS_M,
        "maximum_interior_depth_m": max(row["triangle_max_interior_depth_m"] for row in rows),
        "frames_with_intrusion": len(affected), "saved_frames": len(rows),
        "first_intrusion_time_s": affected[0]["time_s"] if affected else None,
        "rows": rows,
    }
