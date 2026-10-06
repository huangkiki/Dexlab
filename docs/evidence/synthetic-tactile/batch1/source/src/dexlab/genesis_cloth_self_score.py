"""Independent particle-pair eligibility audit, not a triangle CCD certificate."""

import argparse
import json
from pathlib import Path

import numpy as np


def pair_distances(points, pairs):
    points = np.asarray(points, dtype=float)
    return np.linalg.norm(
        points[..., pairs[:, 0], :] - points[..., pairs[:, 1], :], axis=-1
    )


def canonical_mesh(rest, groups, faces, mass):
    """Compare imported layers independent of particle/face enumeration."""
    order = np.lexsort((rest[:, 1], rest[:, 0], groups))
    inverse = np.empty_like(order)
    inverse[order] = np.arange(len(order))
    triangles = np.sort(inverse[faces], axis=1)
    triangles = triangles[np.lexsort(triangles.T[::-1])]
    return np.c_[groups[order], rest[order, :2]], triangles, mass[order]


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("completed") is not True
            or "error" in record
        ):
            raise ValueError("Incomplete self-contact record")
        if (
            record["version"] != "1.4.3"
            or record["dt_s"] != 0.002
            or record["steps"] != 10
            or record["diameter_m"] != 0.008
            or [s["rest_separation_m"] for s in record["scenes"]] != [0.03, 0.006]
        ):
            raise ValueError("Frozen protocol mismatch")
        results, signatures = [], []
        for scene in record["scenes"]:
            native = scene["native"]
            rest = np.asarray(native["rest"], float)
            native_rest = np.asarray(native["rest_field"], float)
            mass = np.asarray(native["mass"], float)
            if any(type(g) is not bool for g in native["groups"]):
                raise ValueError("Invalid layer labels")
            groups = np.asarray(native["groups"])
            faces = np.asarray(native["faces"])
            n = len(rest)
            if (
                rest.shape != (n, 3)
                or native_rest.shape != rest.shape
                or groups.shape != (n,)
                or not groups.any()
                or groups.all()
                or mass.shape != (n,)
                or any(not np.isfinite(a).all() for a in (rest, native_rest, mass))
                or (mass <= 0).any()
                or abs(mass.sum() - 0.00064) > 1e-8
                or faces.ndim != 2
                or faces.shape[1] != 3
                or not len(faces)
                or not np.issubdtype(faces.dtype, np.integer)
                or (faces < 0).any()
                or (faces >= n).any()
            ):
                raise ValueError("Invalid imported geometry/mass")
            if not np.all(groups[faces] == groups[faces[:, :1]]):
                raise ValueError("Unexpected connection between patches")
            for layer in (False, True):
                triangles = rest[faces[groups[faces[:, 0]] == layer]]
                area = (
                    np.linalg.norm(
                        np.cross(
                            triangles[:, 1] - triangles[:, 0],
                            triangles[:, 2] - triangles[:, 0],
                        ),
                        axis=1,
                    ).sum()
                    / 2
                )
                if abs(area - 0.0016) > 1e-8:
                    raise ValueError("Imported patch area mismatch")
            signatures.append(canonical_mesh(rest, groups, faces, mass))
            pairs = np.array(
                [
                    (a, b)
                    for a in np.flatnonzero(~groups)
                    for b in np.flatnonzero(groups)
                ]
            )
            rest_distance = pair_distances(native_rest, pairs)
            if np.max(abs(rest_distance - pair_distances(rest, pairs))) > 1e-8:
                raise ValueError("Native rest-field distance mismatch")
            if [e["repeat"] for e in scene["episodes"]] != [0, 1]:
                raise ValueError("Missing reset repeat")
            episodes, states = [], []
            for episode in scene["episodes"]:
                rows = episode["rows"]
                if [r["step"] for r in rows] != list(range(11)):
                    raise ValueError("Incomplete time grid")
                p = np.asarray([r["pos"] for r in rows], float)
                v = np.asarray([r["vel"] for r in rows], float)
                if (
                    p.shape != (11, n, 3)
                    or v.shape != p.shape
                    or not np.isfinite(p).all()
                    or not np.isfinite(v).all()
                ):
                    raise ValueError("Invalid state arrays")
                target = rest.copy()
                target[:, 2] = 0.2 + np.where(groups, 0.003, -0.003)
                if np.max(abs(p[0] - target)) > 1e-8 or np.max(abs(v[0])) > 1e-8:
                    raise ValueError("Initial state mismatch")
                distances = pair_distances(p, pairs)
                selected = distances[0] < 0.008
                eligible = selected & (rest_distance > 0.008)
                excluded = selected & ~eligible
                if not selected.any():
                    raise ValueError("No overlapping cross-layer pair")
                shift = float(np.linalg.norm((p[1] - p[0]).T @ mass / mass.sum()))
                minimum = float(distances[1, selected].min())
                excluded_change = (
                    float(np.max(abs(distances[1, excluded] - distances[0, excluded])))
                    if excluded.any()
                    else None
                )
                if scene["rest_separation_m"] == 0.03:
                    passed = bool(
                        eligible.sum() == selected.sum()
                        and minimum >= 0.0075
                        and shift <= 1e-9
                    )
                else:
                    passed = bool(excluded.any() and excluded_change <= 1e-8)
                episodes.append(
                    {
                        "selected_pairs": int(selected.sum()),
                        "eligible_pairs": int(eligible.sum()),
                        "excluded_pairs": int(excluded.sum()),
                        "minimum_step1_distance_m": minimum,
                        "excluded_step1_max_distance_change_m": excluded_change,
                        "center_shift_m": shift,
                        "passed": passed,
                    }
                )
                states.append((p, v))
            differences = [float(np.max(abs(a - b))) for a, b in zip(*states)]
            repeat = differences[0] <= 1e-9 and differences[1] <= 1e-8
            results.append(
                {
                    "rest_separation_m": scene["rest_separation_m"],
                    "episodes": episodes,
                    "repeat_max_differences": differences,
                    "passed": repeat and all(e["passed"] for e in episodes),
                }
            )
        matched = all(
            a.shape == b.shape and np.allclose(a, b, rtol=0, atol=1e-8)
            for a, b in zip(*signatures)
        )
        return {
            "valid": True,
            "passed": matched and all(r["passed"] for r in results),
            "matched_imported_xy_topology_mass": matched,
            "cases": results,
            "limits": "Rest-distance eligibility control, not public collision-off. Disconnected patches; no connected-fold or continuous triangle-collision qualification.",
        }
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
