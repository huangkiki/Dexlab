"""Independent actuator/cloth hold/release audit for a frozen prismatic fixture."""

import argparse
import json
from pathlib import Path

import numpy as np


def episode_metrics(rows, mass):
    if [r["step"] for r in rows] != list(range(2001)):
        raise ValueError("Missing every-step data")
    p, v, q, qv, force, pads, quat = [
        np.asarray([r[k] for r in rows], float)
        for k in ("pos", "vel", "q", "qvel", "actuator_force", "pad_pos", "pad_quat")
    ]
    mass = np.asarray(mass, float)
    if (
        mass.ndim != 1
        or len(mass) < 3
        or not np.isfinite(mass).all()
        or (mass <= 0).any()
        or abs(mass.sum() - 0.00032) > 1e-8
        or p.shape != (2001, len(mass), 3)
        or v.shape != p.shape
        or q.shape != (2001, 3)
        or qv.shape != q.shape
        or force.shape != q.shape
        or pads.shape != (2001, 2, 3)
        or quat.shape != (2001, 2, 4)
        or any(not np.isfinite(a).all() for a in (p, v, q, qv, force, pads, quat))
    ):
        raise ValueError("Invalid actual state or mass")
    if np.max(abs(abs(quat[:, :, 0]) - 1)) > 1e-8 or np.max(abs(quat[:, :, 1:])) > 1e-8:
        raise ValueError("Prismatic pad orientation assumption violated")
    if np.max(abs(q[0] - [0, 0.0255, 0.0255])) > 1e-8:
        raise ValueError("Initial actuator state mismatch")
    t = np.arange(2001) * 0.002
    hold = (t >= 2.2) & (t <= 3.1)
    center = np.einsum("tnk,n->tk", p, mass) / mass.sum()
    relative = center[hold] - np.column_stack(
        (np.zeros(hold.sum()), np.zeros(hold.sum()), q[hold, 0])
    )
    drift = float(np.max(np.linalg.norm(relative - relative[0], axis=1)))
    minimum_height = float(p[hold, :, 2].min())
    lift = float(q[hold, 0].min())
    local = abs(p[:, :, None, :] - pads[:, None, :, :]) - np.array([0.01, 0.03, 0.02])
    distance = np.linalg.norm(np.maximum(local, 0), axis=3) + np.minimum(
        local.max(axis=3), 0
    )
    intrusion = float(max(0.0, -distance.min()))
    gap = pads[:, 1, 0] - pads[:, 0, 0] - 0.02
    released = bool(p[-1, :, 2].min() <= 0.005 and gap[-1] >= 0.04)
    held = lift >= 0.07 and minimum_height >= 0.05 and drift <= 0.005
    return {
        "held": bool(held),
        "released": released,
        "actual_min_lift_m": lift,
        "hold_min_cloth_height_m": minimum_height,
        "hold_relative_center_drift_m": drift,
        "max_vertex_pad_intrusion_m": intrusion,
        "intrusion_passed": intrusion <= 0.0005,
        "final_gap_m": float(gap[-1]),
        "final_min_cloth_height_m": float(p[-1, :, 2].min()),
        "max_abs_actuator_force_N": abs(force).max(axis=0).tolist(),
    }, (p, v, q, qv)


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("completed") is not True
            or "error" in record
        ):
            raise ValueError("Incomplete gripper record")
        if (
            record["version"] != "1.4.3"
            or record["dt_s"] != 0.002
            or record["steps"] != 2000
            or record["repeats"] != 2
            or [s["coupled"] for s in record["scenes"]] != [True, False]
        ):
            raise ValueError("Frozen protocol mismatch")
        results = []
        for scene in record["scenes"]:
            if [e["repeat"] for e in scene["episodes"]] != [0, 1]:
                raise ValueError("Missing repeat")
            metrics = []
            trajectories = []
            for e in scene["episodes"]:
                result, states = episode_metrics(e["rows"], scene["native"]["mass"])
                metrics.append(result)
                trajectories.append(states)
            differences = [float(np.max(abs(a - b))) for a, b in zip(*trajectories)]
            repeat = all(
                d <= tol for d, tol in zip(differences, [1e-9, 1e-8, 1e-9, 1e-8])
            )
            passed = repeat and all(
                m["held"] and m["released"] and m["intrusion_passed"]
                if scene["coupled"]
                else not m["held"]
                for m in metrics
            )
            results.append(
                {
                    "coupled": scene["coupled"],
                    "passed": passed,
                    "repeat_passed": repeat,
                    "repeat_max_differences": differences,
                    "episodes": metrics,
                }
            )
        return {
            "valid": True,
            "passed": all(c["passed"] for c in results),
            "cases": results,
            "limits": "Vertex-to-box geometry only, not triangle/edge crossing certification. Actuator force is not independently measured cloth contact force. Synthetic fixture, not hardware.",
        }
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
