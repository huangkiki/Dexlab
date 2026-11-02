#!/usr/bin/env python3
"""Offline CHORD recorder parity and reference-tracking diagnostics.

Native rewards never enter these metrics. A short training run and its tracking
errors are not a manipulation qualification or a physical slip measurement.
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np

from prepare import sha256


def rows(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def compare_values(left, right, path="root"):
    if isinstance(left, dict):
        if not isinstance(right, dict) or left.keys() != right.keys():
            raise ValueError(f"Parity fields differ at {path}")
        return max((compare_values(left[k], right[k], path + "." + k) for k in left), default=0.0)
    a, b = np.asarray(left), np.asarray(right)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError(f"Parity has invalid or misaligned arrays at {path}")
    return float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.size else 0.0


def parity(baseline, recorded):
    invocations = [json.loads((p / "invocation.json").read_text()) for p in (baseline, recorded)]
    if any(i["status"] != "completed" for i in invocations):
        raise ValueError("Parity requires two completed native processes")
    if [i["recorder"] for i in invocations] != [False, True]:
        raise ValueError("Parity requires recorder-off then recorder-on")
    for name in ("checkpoint_sha256", "source", "manifest_sha256", "adapter_sha256", "task", "seed",
                 "steps_requested", "steps_completed", "packages", "timing", "assistance",
                 "motion", "runtime", "native_identity", "native_physics_scenes"):
        if invocations[0][name] != invocations[1][name]:
            raise ValueError(f"Parity invocation differs: {name}")
    traces = [rows(p / "trajectory.jsonl") for p in (baseline, recorded)]
    count = invocations[0]["steps_completed"]
    if any(len(trace) != count for trace in traces) or count == 0:
        raise ValueError("Parity trajectory is incomplete")
    error = max(compare_values(a, b) for a, b in zip(*traces))
    return {"passed": error <= 1e-6, "absolute_tolerance": 1e-6,
            "max_absolute_error": error, "control_steps": count,
            "recorded_invocation_sha256": sha256(recorded / "invocation.json"),
            "native_sha256": sha256(recorded / "native.jsonl"),
            "baseline_trajectory_sha256": sha256(baseline / "trajectory.jsonl"),
            "recorded_trajectory_sha256": sha256(recorded / "trajectory.jsonl")}


def tracking(directory, baseline):
    qualification = parity(baseline, directory)
    invocation = json.loads((directory / "invocation.json").read_text())
    if (invocation["status"] != "completed" or qualification["passed"] is not True
            or qualification["recorded_invocation_sha256"] != sha256(directory / "invocation.json")
            or qualification["native_sha256"] != sha256(directory / "native.jsonl")):
        raise ValueError("Tracking requires completed records with matching successful parity")
    events = rows(directory / "native.jsonl")
    before = [r for r in events if r["epoch"] == "pre_step"]
    after = [r for r in events if r["epoch"] == "post_step_before_reset"]
    applied = [r for r in events if r["epoch"] == "applied_virtual_control_after_physics"]
    count = invocation["steps_completed"]
    if len(before) != count or len(after) != count:
        raise ValueError("Control-boundary record is incomplete")
    decimation = round(invocation["timing"]["control_dt_s"] / invocation["timing"]["physics_dt_s"])
    if len(applied) != count * decimation:
        raise ValueError("Virtual-control substep record is incomplete")
    positions, angles, indices, vertical = [], [], [], []
    terminated = timeouts = 0
    for step, (reference, measured) in enumerate(zip(before, after)):
        if reference["control_step"] != step or measured["control_step"] != step:
            raise ValueError("Control records are reordered or missing")
        if reference["reference_index"] != measured["reference_index"]:
            raise ValueError("Reference advanced across the measured boundary")
        delta = np.asarray(measured["object_position_e"]) - np.asarray(reference["reference_object_position_e"])
        positions.extend(np.linalg.norm(delta, axis=-1).ravel().tolist())
        vertical.extend(delta[..., 2].ravel().tolist())
        q = np.asarray(measured["object_wxyz_e"])
        target = np.asarray(reference["reference_object_wxyz_e"])
        cosine = np.sum(q * target, axis=-1) / (np.linalg.norm(q, axis=-1) * np.linalg.norm(target, axis=-1))
        angles.extend((2 * np.arccos(np.clip(np.abs(cosine), 0, 1))).ravel().tolist())
        indices.extend(reference["reference_index"])
        terminated += sum(measured["terminated"])
        timeouts += sum(measured["time_out"])
        if np.any(np.asarray(measured["voc_scale"]) != 0):
            raise ValueError("VOC assistance was nonzero during evaluation")
    wrench = max((float(np.max(np.abs(value)))
                  for row in applied for value in row["virtual_control_body_frame_N_Nm"].values()), default=None)
    if wrench is None or wrench != 0:
        raise ValueError("VOC applied-command evidence is missing or nonzero")
    if not np.isfinite([*positions, *angles, *vertical]).all():
        raise ValueError("Nonfinite tracking measurement")
    return {"task": invocation["task"], "control_steps": count,
            "position_rmse_m": float(np.sqrt(np.mean(np.square(positions)))),
            "position_max_m": max(positions),
            "orientation_rmse_rad": float(np.sqrt(np.mean(np.square(angles)))),
            "vertical_error_min_m": min(vertical),
            "distinct_reference_frames_observed": len(set(indices)),
            "reference_frames_total": invocation["timing"]["resampled_frames"],
            "native_terminations": terminated, "native_timeouts": timeouts,
            "max_applied_voc_component": wrench,
            "reward_used_for_score": False,
            "task_qualification": "not_established_by_bounded_training",
            "physical_slip": "not_inferred_from_reference_tracking", "parity": qualification}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    pair = sub.add_parser("parity")
    pair.add_argument("baseline", type=Path)
    pair.add_argument("recorded", type=Path)
    score = sub.add_parser("tracking")
    score.add_argument("recorded", type=Path)
    score.add_argument("baseline", type=Path)
    args = parser.parse_args()
    result = (parity(args.baseline, args.recorded) if args.operation == "parity" else
              tracking(args.recorded, args.baseline))
    print(json.dumps(result, indent=2, allow_nan=False))
    if args.operation == "parity" and not result["passed"]:
        sys.exit(2)
