"""Connected-fold geometry and independent saved-state audit, not triangle CCD."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.genesis_cloth_geometry import audit


def fold(rest, angle):
    rest = np.asarray(rest, float)
    if (
        rest.ndim != 2
        or rest.shape[1] != 3
        or not np.isfinite(rest).all()
        or angle not in (0, 150, 170)
    ):
        raise ValueError("Invalid frozen fold geometry")
    result = rest.copy()
    side = rest[:, 0] > 0
    radians = np.deg2rad(angle)
    result[side, 0] = rest[side, 0] * np.cos(radians)
    result[side, 2] += rest[side, 0] * np.sin(radians)
    return result


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("completed") is not True
            or "error" in record
        ):
            raise ValueError("Incomplete fold record")
        if (
            record["version"] != "1.4.3"
            or record["dt_s"] != 0.002
            or record["steps"] != 20
            or [c["angle_deg"] for c in record["cases"]] != [0, 150, 170]
        ):
            raise ValueError("Frozen fold protocol mismatch")
        results = []
        for case in record["cases"]:
            rest = np.asarray(case["rest"], float)
            mass = np.asarray(case["mass"], float)
            faces = np.asarray(case["faces"])
            if (
                rest.ndim != 2
                or rest.shape[1] != 3
                or mass.shape != (len(rest),)
                or not np.isfinite(mass).all()
                or (mass <= 0).any()
                or abs(mass.sum() - 0.00032) > 1e-8
            ):
                raise ValueError("Invalid rest geometry/mass")
            # A single topological component is required, unlike the pair probe.
            neighbors = {i: set() for i in range(len(rest))}
            for face in faces:
                for a in face:
                    neighbors[int(a)].update(map(int, face))
            reached = set()
            pending = [0]
            while pending:
                i = pending.pop()
                if i not in reached:
                    reached.add(i)
                    pending.extend(neighbors[i] - reached)
            if len(reached) != len(rest):
                raise ValueError("Disconnected cloth")
            first, second = np.triu_indices(len(rest), 1)
            eligible = np.linalg.norm(rest[first] - rest[second], axis=1) > 0.008
            first, second = first[eligible], second[eligible]
            if [e["repeat"] for e in case["episodes"]] != [0, 1]:
                raise ValueError("Missing reset repeat")
            traces = []
            states = []
            for episode in case["episodes"]:
                rows = episode["rows"]
                if [r["step"] for r in rows] != list(range(21)):
                    raise ValueError("Missing every-step states")
                p = np.asarray([r["pos"] for r in rows], float)
                v = np.asarray([r["vel"] for r in rows], float)
                if (
                    p.shape != (21, len(rest), 3)
                    or v.shape != p.shape
                    or not np.isfinite(p).all()
                    or not np.isfinite(v).all()
                ):
                    raise ValueError("Invalid state arrays")
                if (
                    np.max(abs(p[0] - fold(rest, case["angle_deg"]))) > 1e-8
                    or np.max(abs(v[0])) > 1e-8
                ):
                    raise ValueError("Initial fold mismatch")
                geometry = audit(p, faces, np.arange(21) * 0.002)
                gaps = np.linalg.norm(p[:, first] - p[:, second], axis=2) - 0.008
                center = np.einsum("tnk,n->tk", p, mass) / mass.sum()
                drift = float(np.linalg.norm(center - center[0], axis=1).max())
                flat_unchanged = bool(
                    np.max(abs(p - p[0])) <= 1e-9 and np.max(abs(v)) <= 1e-8
                )
                traces.append(
                    {
                        "repeat": episode["repeat"],
                        "geometry": geometry,
                        "minimum_eligible_pair_gap_m_each_step": gaps.min(
                            axis=1
                        ).tolist(),
                        "max_center_shift_m": drift,
                        "flat_unchanged": flat_unchanged,
                    }
                )
                states.append((p, v))
            diff = [float(np.max(abs(a - b))) for a, b in zip(*states)]
            passed = (
                diff[0] <= 1e-9
                and diff[1] <= 1e-8
                and all(
                    e["max_center_shift_m"] <= 1e-8
                    and e["geometry"]["maximum_crossing_pairs"] == 0
                    and e["geometry"]["maximum_degenerate_triangles"] == 0
                    and (case["angle_deg"] != 0 or e["flat_unchanged"])
                    for e in traces
                )
            )
            results.append(
                {
                    "angle_deg": case["angle_deg"],
                    "passed": passed,
                    "repeat_max_differences": diff,
                    "episodes": traces,
                }
            )
        return {
            "valid": True,
            "passed": all(c["passed"] for c in results),
            "cases": results,
            "limits": "Connected synthetic initial folds; flat is a geometric negative, not self-collision off. Saved-frame nonadjacent surfaces only; excludes shared vertices and continuous crossings. Pair gaps are diagnostics, not continuum thickness or material accuracy.",
        }
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
