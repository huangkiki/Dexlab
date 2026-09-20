"""Independently validate recorded native forces, velocities and contact geometry."""

import argparse
import json
from pathlib import Path

import numpy as np


def verify_sequence(records, dynamics, dt):
    """Check both suspended holds and the intervening unassisted table rest."""
    phases = {
        "stem_hold": (11.0, 14.0),
        "released": (22.0, 23.0),
        "body_hold": (37.0, 40.0),
    }
    result = {
        "physics": "native SuperDex FP64",
        "fixed_base": True,
        "sequence": "stem pinch → lift → table → release → body grasp → lift",
        "apple_mass_kg": 0.2,
        "stem_model": "original rigid SDF mesh; no bending/fracture",
        "joint_targets_only": True,
        "phases": {},
        "checks": {},
    }
    norm = lambda values: sum(float(np.linalg.norm(v)) for v in values)
    for name, (start, end) in phases.items():
        rows = [r for r in records if start <= r["time"] < end]
        steps = [r for r in dynamics if start <= r["time"] < end]
        if not rows or not steps:
            result["checks"][name + "_recorded"] = False
            continue
        hand_ratio = float(np.mean([r["hand_force"][2] for r in steps]) / (0.2 * 9.81))
        table_ratio = float(
            np.mean([r["table_force"][2] for r in steps]) / (0.2 * 9.81)
        )
        impulse = (
            np.sum(
                [np.asarray(r["total_force"]) - [0, 0, 0.2 * 9.81] for r in steps],
                axis=0,
            )
            * dt
        )
        momentum = 0.2 * (
            np.asarray(steps[-1]["velocity"]) - np.asarray(steps[0]["velocity_before"])
        )
        error = float(np.linalg.norm(impulse - momentum) / ((end - start) * 0.2 * 9.81))
        phase = {
            "minimum_clearance_m": min(r["clearance"] for r in rows),
            "maximum_clearance_m": max(r["clearance"] for r in rows),
            "hand_support_weight_ratio": hand_ratio,
            "table_support_weight_ratio": table_ratio,
            "momentum_balance_error_weight_fraction": error,
            "maximum_hand_contact_n": max(
                norm(r["robot_contact_forces"].values()) for r in rows
            ),
            "minimum_hand_contact_n": min(
                norm(r["robot_contact_forces"].values()) for r in rows
            ),
            "apple_solver_status_counts": {
                s: sum(r["apple_status"] == s for r in steps)
                for s in sorted({r["apple_status"] for r in steps})
            },
        }
        result["phases"][name] = phase
        result["checks"][name + "_momentum_balance"] = error < 0.02
        if name == "released":
            result["checks"]["released_on_table"] = (
                abs(table_ratio - 1) < 0.05 and phase["maximum_clearance_m"] < 0.001
            )
            result["checks"]["released_no_hand_contact"] = (
                phase["maximum_hand_contact_n"] < 0.01
            )
        else:
            result["checks"][name + "_lifted"] = phase["minimum_clearance_m"] > 0.07
            result["checks"][name + "_supported_by_hand"] = abs(hand_ratio - 1) < 0.05
            result["checks"][name + "_no_table_support"] = abs(table_ratio) < 0.01
            result["checks"][name + "_continuous_contact"] = (
                phase["minimum_hand_contact_n"] > 0.2
            )
    stem_rows = [r for r in records if r["time"] < 17.5]
    result["maximum_stem_phase_nonstem_force_n"] = max(
        r["off_stem_contact_force_n"] for r in stem_rows
    )
    result["checks"]["stem_grasp_only_stem"] = (
        result["maximum_stem_phase_nonstem_force_n"] < 0.05
    )
    stem_hold = [r for r in records if 11 <= r["time"] < 14]
    result["checks"]["stem_hold_two_fingers"] = bool(stem_hold) and all(
        norm(v for n, v in row["robot_contact_forces"].items() if n.startswith(prefix))
        > 0.1
        for row in stem_hold
        for prefix in ("r_thumb", "r_index_finger")
    )
    body_hold = [r for r in records if 37 <= r["time"] < 40]
    result["checks"]["body_hold_contacts_fruit"] = bool(body_hold) and all(
        r["off_stem_contact_force_n"] > 0.2 for r in body_hold
    )
    result["checks"]["no_other_robot_support"] = all(
        norm(
            v for n, v in row["robot_contact_forces"].items() if not n.startswith("r_")
        )
        < 0.05
        for row in records
    )
    result["maximum_penetration_m"] = max(
        r["maximum_robot_apple_penetration_m"] for r in records
    )
    result["checks"]["bounded_penetration"] = result["maximum_penetration_m"] < 0.001
    result["checks"]["no_solver_divergence"] = all(
        r["apple_status"] != "DIVERGED" and r["scene_status"] != "DIVERGED"
        for r in dynamics
    )
    result["checks"]["finite_state"] = all(
        np.isfinite(r["apple_position"]).all() for r in records
    )
    force = np.array([r["total_force"] for r in dynamics])
    velocity = np.array([r["velocity"] for r in dynamics])
    previous_velocity = np.array([r["velocity_before"] for r in dynamics])
    residual = force - [0, 0, 0.2 * 9.81] - 0.2 * (velocity - previous_velocity) / dt
    errors = np.linalg.norm(residual, axis=1) / (0.2 * 9.81)
    result["whole_sequence_force_balance"] = {
        "maximum_error_weight_fraction": float(errors.max()),
        "p99_error_weight_fraction": float(np.percentile(errors, 99)),
        "scene_status_counts": {
            status: sum(r["scene_status"] == status for r in dynamics)
            for status in sorted({r["scene_status"] for r in dynamics})
        },
    }
    result["checks"]["whole_sequence_force_balance"] = bool(
        errors.max() < 0.05 and np.percentile(errors, 99) < 0.01
    )
    result["passed"] = bool(all(result["checks"].values()))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    records = json.loads((args.input / "metrics.json").read_text())
    dynamics = json.loads((args.input / "dynamics.json").read_text())
    dt = dynamics[1]["time"] - dynamics[0]["time"]
    summary = verify_sequence(records, dynamics, dt)
    trace = np.load(args.input / "trajectory.npz")
    base_index = list(trace["names"]).index("openarm_body_link0")
    base = trace["frames"][:, base_index]
    summary["maximum_base_pose_change"] = float(np.abs(base - base[0]).max())
    summary["checks"]["base_stationary"] = summary["maximum_base_pose_change"] < 1e-12
    summary["checks"]["all_recorded_transforms_finite"] = bool(
        np.isfinite(trace["frames"]).all()
    )
    summary["passed"] = bool(all(summary["checks"].values()))
    (args.input / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit("Physical sequence verification failed")
