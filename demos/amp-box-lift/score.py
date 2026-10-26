#!/usr/bin/env python3
"""Recompute carrying diagnostics from a complete AMP record without physics."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.amp_lift_audit import (
    articulated_momentum, carrying_windows, check_step_clock, compare_contact_decoding,
    compare_probe_values, hand_relative_positions, momentum_residual,
    object_contact_loads, static_plane_geoms,
)
from dexlab.libero_substeps import read_chunk


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def score(directory, protocol):
    """Keep record integrity, source predicates and physical diagnostics separate."""
    invocation = json.loads((directory / "invocation.json").read_text())
    meta = json.loads((directory / "native/recording.json").read_text())
    case = invocation["case"]
    if invocation["status"] != "completed" or meta["status"] != "completed" or \
            not case["record_substeps"] or invocation["completed_actions"] != case["actions"]:
        raise ValueError("Scoring requires a complete recorded case; retain failed prefixes separately")
    decimation = protocol["conditions"]["decimation"]
    dt = protocol["conditions"]["physics_dt_s"]
    checks = protocol["checks"]
    total = case["actions"] * decimation
    if total < 2 or meta["substeps"] != total or len(meta["chunks"]) != case["actions"]:
        raise ValueError("Incomplete native trace")
    expected = {f"action-{index:06d}.npz" for index in range(case["actions"])}
    for folder in ("actions", "native/substeps"):
        if {path.name for path in (directory / folder).glob("*.npz")} != expected:
            raise ValueError("Unexpected recorded extent")
    with np.load(directory / "native/effective-model.npz", allow_pickle=False) as archive:
        model = dict(archive)
    nbody, ngeom = len(meta["body_names"]), len(meta["geom_names"])

    def field(name, shape):
        value = model[name]
        if value.shape == (1, *shape):
            value = value[0]
        if value.shape != shape or not np.isfinite(value).all():
            raise ValueError(f"Unexpected effective model field: {name}")
        return value

    root = meta["body_names"].index("toaster/toaster_root")
    njoint = len(meta["joint_names"])
    free_joints = np.flatnonzero((field("jnt_type", (njoint,)) == 0) &
                                (field("jnt_bodyid", (njoint,)) == root))
    addresses = field("jnt_qposadr", (njoint,))
    if len(free_joints) != 1 or addresses.dtype.kind not in "iu":
        raise ValueError("Require one identified object free joint")
    root_qpos = int(addresses[free_joints[0]])
    roots = field("body_rootid", (nbody,))
    bodies = np.flatnonzero(roots == root)
    mass, inertia = field("body_mass", (nbody,)), field("body_inertia", (nbody, 3))
    geom_bodies = field("geom_bodyid", (ngeom,))
    geom_types = field("geom_type", (ngeom,))
    groups = {
        "object_geoms": set(np.flatnonzero(np.isin(geom_bodies, bodies))),
        "left_geoms": {meta["geom_names"].index(f"robot/left_{part}_collision") for part in ("hand", "wrist")},
        "right_geoms": {meta["geom_names"].index(f"robot/right_{part}_collision") for part in ("hand", "wrist")},
        "ground_geoms": static_plane_geoms(geom_types, geom_bodies, field("body_weldid", (nbody,))),
    }
    palms = [meta["site_names"].index(f"robot/{side}_palm") for side in ("left", "right")]
    gravity = np.asarray(meta["options"]["gravity"], dtype=float).reshape(3)
    initial = read_chunk(directory / "initial-state.npz")
    if len(initial) != 1:
        raise ValueError("Missing initial state")
    initial = initial[0]
    if not 0 <= root_qpos <= len(initial["qpos"]) - 7:
        raise ValueError("Object free-joint state is truncated")
    required_height = float(np.asarray(initial["goal"]).reshape(3)[2]) - checks["source_height_tolerance_m"]
    values = {key: [] for key in ("time_s", "root_height_m", "tilt_rad", "hand_relative_m",
                                  "loaded_pairs", "support_force_n", "penetration_m",
                                  "linear_residual_ns", "angular_residual_nms")}
    evidence = {name: digest(directory / name) for name in (
        "invocation.json", "initial-state.npz", "native/recording.json", "native/effective-model.npz")}
    previous = initial
    previous_momentum = previous_loads = None
    source_success_actions = 0
    maximum_force_error = 0.
    applied_max = {"qfrc_applied": 0., "xfrc_applied": 0.}
    limited = field("actuator_forcelimited", (len(meta["actuator_names"]),)).astype(bool)
    ranges = field("actuator_forcerange", (len(limited), 2))
    if np.any(ranges[limited, 1] <= ranges[limited, 0]):
        raise ValueError("Invalid effective actuator force range")
    saturation_samples = 0
    for index, chunk in enumerate(meta["chunks"]):
        name = f"action-{index:06d}.npz"
        if chunk != {"name": name, "action_index": index, "substeps": decimation}:
            raise ValueError("Broken native chunk sequence")
        action_path = directory / "actions" / name
        native_path = directory / "native/substeps" / name
        actions, rows = read_chunk(action_path), read_chunk(native_path)
        if len(actions) != 1 or len(rows) != decimation or actions[0]["status"] != "completed":
            raise ValueError("Truncated action record")
        action = actions[0]
        if action["action_index"] != index or action["feedback"]["automatic_reset"] != (index + 1 == 3000):
            raise ValueError("Unexpected action/reset boundary")
        for field_name in ("qpos", "qvel"):
            compare_probe_values(rows[-1]["after"][field_name], action["feedback"][field_name],
                                 atol=0., rtol=0., path="terminal feedback")
        source_success_actions += int(np.any(action["feedback"]["source_success"]))
        evidence[f"actions/{name}"] = digest(action_path)
        evidence[f"native/substeps/{name}"] = digest(native_path)
        for offset, row in enumerate(rows):
            if row["sequence"] != index * decimation + offset or row["action_index"] != index:
                raise ValueError("Broken native substep sequence")
            before, after, contacts = row["before"], row["after"], row["contacts"]
            for key in ("qpos", "qvel", "time"):
                compare_probe_values(previous[key], before[key], atol=0., rtol=0., path="native continuity")
            check_step_clock(before["time"], after["time"], dt=dt, dtype=meta["time_dtype"])
            if any(not np.isfinite(value).all() for phase in (before, after) for value in phase.values()):
                raise ValueError("Invalid native clock/state")
            if row["nefc"] != len(row["efc_force"]) or np.any(contacts["worldid"] != 0):
                raise ValueError("Invalid native constraint extent")
            decoded = compare_contact_decoding(contacts, row["efc_force"], cone=meta["options"]["cone"],
                atol=checks["force_decode_atol"], rtol=checks["force_decode_rtol"])
            if not decoded["passed"]:
                raise ValueError("Independent contact-force decoding failed")
            maximum_force_error = max(maximum_force_error, decoded["maximum_component_error"])
            momentum = articulated_momentum(mass=mass, inertia=inertia, body_ids=bodies,
                body_rootid=roots, **{key: after[key] for key in ("xipos", "ximat", "cvel", "subtree_com")})
            loads = object_contact_loads(contacts, **groups, object_com=momentum["com_world_m"],
                ngeom=ngeom, loaded_threshold_n=checks["loaded_contact_threshold_n"])
            if previous_momentum is not None:
                residual = momentum_residual(previous_momentum, momentum,
                    sum(load["force_n"] for load in previous_loads.values()),
                    sum(load["torque_nm"] for load in previous_loads.values()), gravity, dt=dt)
                values["linear_residual_ns"].append(residual["linear_ns"])
                values["angular_residual_nms"].append(residual["angular_nms"])
            previous_momentum, previous_loads, previous = momentum, loads, after
            point = after["xpos"][root]
            quaternion = after["xquat"][root]
            if not np.isclose(np.linalg.norm(quaternion), 1., atol=2e-5, rtol=0):
                raise ValueError("Invalid native object orientation")
            values["time_s"].append(before["time"])
            values["root_height_m"].append(point[2])
            values["tilt_rad"].append(np.arccos(np.clip(1 - 2 * np.sum(quaternion[1:3] ** 2), -1, 1)))
            values["hand_relative_m"].append(hand_relative_positions(point, after["site_xpos"][palms],
                                                                         after["site_xmat"][palms]))
            values["loaded_pairs"].append([loads[name]["loaded_pairs"] for name in ("left", "right", "ground", "other")])
            values["support_force_n"].append([loads[name]["force_n"] for name in ("left", "right", "ground", "other")])
            object_contacts = np.isin(contacts["geom"], list(groups["object_geoms"])).any(axis=1)
            distances = np.asarray(contacts["dist"])
            if distances.shape != (len(contacts["geom"]),) or not np.isfinite(distances).all():
                raise ValueError("Invalid native contact distance")
            values["penetration_m"].append(float(np.maximum(-distances[object_contacts], 0).max(initial=0)))
            for key in applied_max:
                applied_max[key] = max(applied_max[key], float(np.abs(before[key]).max(initial=0)))
            force = after["actuator_force"][limited]
            center = ranges[limited].mean(axis=1)
            half_range = (ranges[limited, 1] - ranges[limited, 0]) / 2
            saturation_samples += int(np.count_nonzero(np.abs(force - center) >= .99 * half_range))
    series = {key: np.asarray(value) for key, value in values.items()}
    carrying = carrying_windows(series["time_s"], series["root_height_m"], required_height,
                                 series["loaded_pairs"], dt=dt, hold_s=checks["independent_hold_s"],
                                 clock_dtype=meta["time_dtype"])
    for window in carrying["windows"]:
        segment = series["hand_relative_m"][window["first_substep"]:window["end_substep_exclusive"]]
        window["maximum_hand_relative_drift_m"] = np.linalg.norm(segment - segment[0], axis=2).max(axis=0).tolist()
    report = {
        "schema_version": 1, "case": case, "record_integrity": "passed", "task_success": None,
        "source_success_actions": source_success_actions, "carrying": carrying,
        "native_substeps": total, "momentum_intervals": total - 1,
        "mass_kg": float(mass[bodies].sum()), "required_root_height_m": required_height,
        "net_root_lift_m": float(previous["qpos"][root_qpos + 2] - initial["qpos"][root_qpos + 2]),
        "net_root_lift_epoch": "Initial integrated state to final integrated state before automatic reset",
        "native_sampled_root_lift_m": float(series["root_height_m"][-1] - series["root_height_m"][0]),
        "maximum_tilt_rad": float(series["tilt_rad"].max()),
        "maximum_penetration_m": float(series["penetration_m"].max()),
        "maximum_force_decode_error": maximum_force_error, "maximum_applied_inputs": applied_max,
        "actuator_samples_at_99_percent_force_limit": saturation_samples,
        "actuator_sample_denominator": int(total * limited.sum()),
        "body_gravcomp": field("body_gravcomp", (nbody,))[bodies].tolist(),
        "dof_armature": model["dof_armature"].tolist(),
        "disableflags": meta["options"]["disableflags"],
        "limitations": [
            "Kinematic and momentum samples retain the source native compute epoch; the final integrated endpoint is preserved in the raw trace but has no subsequent momentum sample.",
            "Residuals include contact and gravity only. Generalized applied forces, armature, model disable flags, non-contact constraints and integrator effects require separate attribution before physical qualification.",
            "Hand-relative drift measures a point displacement in each palm frame, not contact-patch material slip.",
            "No source success flag or carrying window establishes task success, solver failure, hardware validation or cross-engine equivalence.",
        ],
        "evidence_sha256": evidence,
    }
    for key in ("linear_residual_ns", "angular_residual_nms"):
        report[f"maximum_{key}"] = float(np.linalg.norm(series[key], axis=1).max())
    return report, series


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = Path(__file__).with_name("protocol.json").read_bytes()
    invocation = json.loads((args.run / "invocation.json").read_text())
    if invocation["protocol_sha256"] != hashlib.sha256(raw).hexdigest():
        parser.error("Record belongs to a different protocol")
    args.output.mkdir(parents=True, exist_ok=False)
    report, series = score(args.run, json.loads(raw))
    with (args.output / "diagnostic-series.npz").open("xb") as stream:
        np.savez_compressed(stream, **series)
    report["series_sha256"] = digest(args.output / "diagnostic-series.npz")
    report["scorer_sha256"] = digest(Path(__file__))
    report["audit_sha256"] = digest(Path(__file__).resolve().parents[2] / "src/dexlab/amp_lift_audit.py")
    (args.output / "diagnostics.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(args.output / "diagnostics.json")


if __name__ == "__main__":
    main()
