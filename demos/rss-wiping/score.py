#!/usr/bin/env python3
"""Rescore saved RSS material-point motion without importing the simulator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def rotation_xyzw(quaternion):
    quaternion = np.asarray(quaternion, dtype=np.float64)
    norm = np.linalg.norm(quaternion)
    if not np.isclose(norm, 1.0, atol=1e-5, rtol=0):
        raise ValueError("Invalid hand orientation")
    # Float32 native poses drift slightly off the unit sphere; a rotation
    # must remain orthogonal, including after the object has been released.
    x, y, z, w = quaternion / norm
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)],
    ])


def patch_motion(particles, hand_position, hand_quaternion, indices, reference=None):
    local = (particles[indices] - hand_position) @ rotation_xyzw(hand_quaternion)
    if reference is None:
        return local, 0.0, 0.0
    displacement = local - reference
    return local, float(np.linalg.norm(displacement.mean(axis=0))), float(np.linalg.norm(displacement, axis=1).max())


def score(folder: Path, *, include_curves=False):
    rows = [json.loads(line) for line in (folder / "observations.jsonl").read_text().splitlines()]
    summary = json.loads((folder / "summary.json").read_text())
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["schema_version"] != 2:
        raise ValueError("Expected a schema 2 record")
    failures = []
    if not rows:
        raise ValueError("No observations")
    if len(rows) != summary["recorded_steps"]:
        failures.append("observation_count")
    steps = [r["step"] for r in rows]
    if any(b != a + 1 for a, b in zip(steps, steps[1:])):
        failures.append("nonconsecutive_steps")
    times = np.array([r["sim_time_s"] for r in rows])
    if not np.allclose(np.diff(times), 1 / manifest["control_hz"], atol=1e-7, rtol=0):
        failures.append("control_time_spacing")
    if summary["mode"] == "no-latch" and any(r["active_pins"] for r in rows):
        failures.append("unexpected_pin")
    frames = np.load(folder / "video-times.npy")
    if len(frames) != summary["video_frames"]:
        failures.append("video_frame_count")
    if len(frames) > 1 and not np.allclose(np.diff(frames), 1 / manifest["video_fps"], atol=1e-7, rtol=0):
        failures.append("video_time_spacing")
    indices_path = folder / "tracked-patch.npy"
    indices = np.load(indices_path) if indices_path.exists() else None
    reference = None
    maximum_slip = maximum_node = None
    finite = True
    final_particles = None
    cursor = 0
    curves = []
    for chunk in sorted((folder / "states").glob("*.npz")):
        with np.load(chunk) as data:
            for i, step in enumerate(data["step"]):
                if cursor >= len(rows) or int(step) != rows[cursor]["step"]:
                    raise ValueError("Raw state and observation steps differ")
                row = rows[cursor]
                particles = data["particles"][i]
                finite_step = all(np.isfinite(data[key][i]).all()
                                  for key in ("particles", "body_q", "joint_q", "stripe_ink"))
                finite = finite and finite_step
                if not finite_step:
                    failures.append(f"nonfinite_state:{step}")
                cleaned = float(np.mean(data["stripe_ink"][i] <= manifest["stripe_cleared_below"]))
                if not np.isclose(cleaned, row["cleaned_fraction"], atol=1e-10, rtol=0):
                    failures.append(f"cleaned_readback:{step}")
                if not np.allclose(particles.mean(axis=0), row["sponge_centroid_m"], atol=1e-10, rtol=0):
                    failures.append(f"centroid_readback:{step}")
                slip = node = None
                if indices is not None and step >= summary["ready_step"]:
                    local, slip, node = patch_motion(
                        particles, np.asarray(row["hand_position_m"]), row["hand_quaternion_xyzw"],
                        indices, reference,
                    )
                    if reference is None:
                        reference = local
                    if not np.isclose(slip, row["patch_centroid_slip_m"], atol=1e-7, rtol=0):
                        failures.append(f"slip_readback:{step}")
                    if not np.isclose(node, row["patch_max_node_displacement_m"], atol=1e-7, rtol=0):
                        failures.append(f"node_readback:{step}")
                    if row["grip_command"] >= 0.5:
                        maximum_slip = max(maximum_slip or 0, slip)
                        maximum_node = max(maximum_node or 0, node)
                if include_curves:
                    curves.append({
                        "step": int(step), "sim_time_s": row["sim_time_s"],
                        "cleaned_fraction": cleaned,
                        "patch_centroid_slip_m": slip,
                        "patch_max_node_displacement_m": node,
                        "grip_command": row.get("grip_command"),
                        "active_pins": row["active_pins"],
                    })
                final_particles = particles
                cursor += 1
    if cursor != len(rows):
        failures.append("raw_state_count")
    if maximum_slip is not None and not np.isclose(
        maximum_slip, summary["max_hold_patch_centroid_slip_m"], atol=1e-7, rtol=0
    ):
        failures.append("summary_slip")
    if maximum_node is not None and not np.isclose(
        maximum_node, summary["max_hold_patch_node_displacement_m"], atol=1e-7, rtol=0
    ):
        failures.append("summary_node")
    settled = np.load(folder / "settled-particles.npy")
    measured = {
        "final_cleaned_fraction": cleaned,
        "peak_bar_force_n": max(row["bar_force_n"] for row in rows),
        "peak_pressure_pa": max(row["bar_peak_pressure_pa"] for row in rows),
        "sponge_return_xy_error_m": float(np.linalg.norm(
            final_particles.mean(axis=0)[:2] - settled.mean(axis=0)[:2])),
        "sponge_return_min_z_error_m": float(abs(
            final_particles[:, 2].min() - settled[:, 2].min())),
    }
    for name, value in measured.items():
        if not np.isclose(value, summary[name], atol=1e-7, rtol=0):
            failures.append(f"summary_{name}")
    home_errors = {
        arm: float(np.linalg.norm(np.asarray(rows[-1]["arm_positions_m"][arm]) - home))
        for arm, home in manifest["arm_home_positions_m"].items()
    }
    for arm, error in home_errors.items():
        if not np.isclose(error, summary["home_errors_m"][arm], atol=1e-7, rtol=0):
            failures.append(f"summary_home_{arm}")
    if rows[-1]["phase"] != summary["phase"]:
        failures.append("summary_phase")
    if bool(finite) != summary["finite"]:
        failures.append("summary_finite")
    outcomes = {
        "routine_finished": rows[-1]["phase"] == "done" and summary["error"] is None,
        "finite": bool(finite),
        "cleaned_at_least_90_percent": measured["final_cleaned_fraction"] >= 0.90,
        "bar_force_over_1_n": measured["peak_bar_force_n"] > 1.0,
        "bar_pressure_over_5_kpa": measured["peak_pressure_pa"] > 5000,
        "sponge_return_xy_under_20_mm": measured["sponge_return_xy_error_m"] < 0.020,
        "sponge_return_height_within_3_mm": measured["sponge_return_min_z_error_m"] <= 0.003,
        "arms_home_within_6_mm": all(x < 0.006 for x in home_errors.values()),
    }
    result = {
        "schema_version": 2, "mode": summary["mode"], "measured": measured,
        "record_integrity_pass": not failures, "record_failures": failures,
        "task_outcomes": outcomes, "task_pass": all(outcomes.values()),
        "max_hold_patch_centroid_slip_m": maximum_slip,
        "max_hold_patch_node_displacement_m": maximum_node,
        "holding_under_10_mm": maximum_slip is not None and maximum_slip < 0.010,
        "actual_max_pin_count": max(r["active_pins"] for r in rows),
        "video_recorded": len(frames) >= 2,
        "scope": "Saved-state consistency and upstream task thresholds. "
                 "Not material validation or a substitute for the unchanged upstream test.",
    }

    if include_curves:
        result["curves"] = curves
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    result = score(args.folder)
    (args.folder / "score.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["record_integrity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
