"""Independent sampled surface-crossing audit for nonadjacent cloth triangles.

Uses triangle AABBs, strict segment/plane crossings and a coplanar separating-axis
test. This checks zero-thickness surfaces, not thickness overlap or continuous
collision detection. Triangles sharing any vertex are excluded explicitly.
"""

import numpy as np

EPSILON_M = 1e-9


def nonadjacent_pairs(triangles):
    first, second = np.triu_indices(len(triangles), 1)
    shared = (triangles[first, :, None] == triangles[second, None, :]).any(axis=(1, 2))
    return first[~shared], second[~shared]


def _edges_cross_faces(edges_triangle, face_triangle, normals):
    result = np.zeros(len(normals), dtype=bool)
    face_edges = np.roll(face_triangle, -1, axis=1) - face_triangle
    tolerance = EPSILON_M * np.linalg.norm(face_edges, axis=2)
    for edge in range(3):
        begin = edges_triangle[:, edge]
        end = edges_triangle[:, (edge + 1) % 3]
        distance_begin = np.einsum("ij,ij->i", begin - face_triangle[:, 0], normals)
        distance_end = np.einsum("ij,ij->i", end - face_triangle[:, 0], normals)
        crossing = ((distance_begin > EPSILON_M) & (distance_end < -EPSILON_M)) | (
            (distance_begin < -EPSILON_M) & (distance_end > EPSILON_M)
        )
        fraction = np.divide(distance_begin, distance_begin - distance_end,
                             out=np.zeros(len(begin)), where=crossing)
        intersection = begin + fraction[:, None] * (end - begin)
        sides = np.einsum("ik,ijk->ij", normals,
                          np.cross(face_edges, intersection[:, None] - face_triangle))
        result |= crossing & (sides >= -tolerance).all(axis=1)
    return result


def crossing_count(vertices, triangles, pairs=None):
    """Return crossing-pair and degenerate-triangle counts for one frame."""
    faces = np.asarray(vertices, dtype=float)[triangles]
    normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    areas2 = np.linalg.norm(normals, axis=1)
    degenerate = areas2 <= EPSILON_M**2
    normals = np.divide(normals, areas2[:, None], out=np.zeros_like(normals), where=~degenerate[:, None])
    first, second = nonadjacent_pairs(triangles) if pairs is None else pairs
    low, high = faces.min(axis=1), faces.max(axis=1)
    candidate = ((low[first] <= high[second] + EPSILON_M).all(axis=1)
                 & (low[second] <= high[first] + EPSILON_M).all(axis=1)
                 & ~degenerate[first] & ~degenerate[second])
    first, second = first[candidate], second[candidate]
    if not len(first):
        return 0, int(degenerate.sum())
    a, b = faces[first], faces[second]
    na, nb = normals[first], normals[second]
    distance_a = np.einsum("ik,ijk->ij", nb, a - b[:, :1])
    distance_b = np.einsum("ik,ijk->ij", na, b - a[:, :1])
    coplanar = (np.abs(distance_a) <= EPSILON_M).all(axis=1) & (
        np.abs(distance_b) <= EPSILON_M
    ).all(axis=1)
    crossed = _edges_cross_faces(a, b, nb) | _edges_cross_faces(b, a, na)
    # Positive-area overlap only: coplanar boundary touching is not a crossing.
    for index in np.flatnonzero(coplanar):
        keep = np.arange(3) != np.argmax(np.abs(na[index]))
        pa, pb = a[index][:, keep], b[index][:, keep]
        edges = np.vstack((np.roll(pa, -1, axis=0) - pa, np.roll(pb, -1, axis=0) - pb))
        axes = np.c_[-edges[:, 1], edges[:, 0]]
        xa, xb = pa @ axes.T, pb @ axes.T
        overlap = np.minimum(xa.max(axis=0), xb.max(axis=0)) - np.maximum(xa.min(axis=0), xb.min(axis=0))
        crossed[index] = bool((overlap > EPSILON_M * np.linalg.norm(axes, axis=1)).all())
    return int(crossed.sum()), int(degenerate.sum())


def audit_record(time, positions, triangles):
    """Audit 100 Hz target times using the next saved frame, including endpoints."""
    targets = np.arange(time[0], time[-1] + 1e-9, 0.01)
    selected = np.unique(np.r_[np.searchsorted(time, targets), len(time) - 1])
    selected = selected[selected < len(time)]
    pairs = nonadjacent_pairs(triangles)
    counts = [crossing_count(positions[index], triangles, pairs) for index in selected]
    crossings, degenerate = np.asarray(counts).T
    offending = selected[crossings > 0]
    return {
        "scope": "nonadjacent zero-thickness surface crossings; shared-vertex pairs excluded; no continuous-time or thickness-overlap guarantee",
        "epsilon_m": EPSILON_M,
        "requested_sample_interval_s": 0.01,
        "maximum_observed_interval_s": float(np.diff(time[selected]).max(initial=0)),
        "audited_frame_count": len(selected),
        "candidate_topology_pairs": len(pairs[0]),
        "maximum_crossing_pairs": int(crossings.max(initial=0)),
        "frames_with_crossings": int((crossings > 0).sum()),
        "first_crossing_time_s": float(time[offending[0]]) if len(offending) else None,
        "maximum_degenerate_triangles": int(degenerate.max(initial=0)),
    }
