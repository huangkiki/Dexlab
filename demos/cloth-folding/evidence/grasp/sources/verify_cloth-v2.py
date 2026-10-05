"""Acceptance checks for the recorded episode, separate from its controller.

These thresholds validate a nominal simulation experiment. They do not certify
material fidelity or sim-to-real transfer.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SCORER_VERSION = "cloth-evidence-v2"
MAXIMUM_FIELDS = (
    "edge_strain", "hand_penetration_m", "table_penetration_m",
    "self_contact_penetration_m", "robot_rigid_penetration_m",
)


def input_hashes(directory):
    files = [directory / name for name in ("model.mjb", "states.npz", "trace.json", "summary.json")]
    files.extend(sorted(directory.glob("plan-*.npz")))
    hashes = {}
    for path in files:
        with path.open('rb') as stream:
            hashes[path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return hashes


def evidence_checks(records, maximums, plans, task, duration, sample_dt):
    """Require actual sampling coverage before computing success fractions."""
    expected_sides = {"r", "l"} if task == "fold" else {"r"}
    checks = {
        "valid_task": task in ("grasp", "fold"),
        "complete_time_grid": False,
        "finite_complete_measurements": False,
        "complete_hand_plans": False,
        "complete_contact_scan": False,
        "summary_bounds_recorded_maxima": False,
    }
    try:
        expected_time = np.arange(round(duration / sample_dt)) * sample_dt
        times = np.array([row["time_s"] for row in records])
        checks["complete_time_grid"] = len(times) == len(expected_time) and bool(
            np.allclose(times, expected_time, atol=1e-10, rtol=0)
        )
        checks["complete_hand_plans"] = (
            len(plans) == len(expected_sides)
            and {plan["side"] for plan in plans} == expected_sides
            and all(np.isfinite(plan["point"]).all() for plan in plans)
        )
        checks["complete_contact_scan"] = bool(records) and all(
            row.get("contact_measurement_complete") is True for row in records
        )
        quantities = list(maximums.values())
        required_maxima = set(MAXIMUM_FIELDS)
        for row in records:
            quantities.extend(row[key] for key in required_maxima)
            quantities.extend(row["cloth_height_range_m"])
            quantities.extend(row["forces"].values())
            if any(force < 0 for force in row["forces"].values()):
                return checks
            for side in expected_sides:
                for key in ("material", "anchors") + (
                    ("far_material",) if task == "fold" else ()
                ):
                    point = np.asarray(row[key][side])
                    if point.shape != (3,):
                        return checks
                    quantities.extend(point)
        checks["finite_complete_measurements"] = (
            required_maxima <= maximums.keys() and bool(np.isfinite(quantities).all())
        )
        # The summary scans every physics step, the trace only at 100 Hz.
        # Equality would incorrectly reject a peak between recorded samples.
        checks["summary_bounds_recorded_maxima"] = bool(records) and all(
            np.isfinite(maximums[key])
            and maximums[key] >= 0
            and all(0 <= row[key] <= maximums[key] for row in records)
            for key in MAXIMUM_FIELDS
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        pass
    return checks


def verify_episode(
    records, maximums, plans, *, task, hold_end, duration, failure, sample_dt=0.01
):
    coverage = evidence_checks(records, maximums, plans, task, duration, sample_dt)
    if not all(coverage.values()):
        return dict(
            passed=False,
            checks=coverage,
            metrics={},
            error="Incomplete or invalid measurement evidence",
        )
    checks = {
        **coverage,
        "completed_without_physics_warning": failure is None,
        "edge_strain_below_5_percent": maximums["edge_strain"] < 0.05,
        "robot_contact_penetration_below_1_5_mm": maximums["hand_penetration_m"]
        < 0.0015,
        "table_contact_penetration_below_1_5_mm": maximums["table_penetration_m"]
        < 0.0015,
        "cloth_self_contact_penetration_below_1_5_mm": maximums[
            "self_contact_penetration_m"
        ]
        < 0.0015,
        "robot_rigid_penetration_below_1_5_mm": maximums["robot_rigid_penetration_m"]
        < 0.0015,
    }
    metrics = {}
    held = [row for row in records if 2 <= row["time_s"] < hold_end]
    released = [row for row in records if row["time_s"] >= duration - 0.5]
    for plan in plans:
        side = plan["side"]
        pad_names = [
            f"collision_{side}_{finger}_pad" for finger in ("thumb", "index_finger")
        ]
        coverage = (
            np.mean(
                [
                    all(row["forces"].get(name, 0) > 0.02 for name in pad_names)
                    for row in held
                ]
            )
            if held
            else 0.0
        )
        slip = max(
            (
                np.linalg.norm(np.subtract(row["material"][side], row["anchors"][side]))
                for row in held
            ),
            default=None,
        )
        lift = max(
            (row["material"][side][2] - plan["point"][2] for row in held), default=0.0
        )
        metrics[side] = dict(
            two_pad_contact_fraction=float(coverage),
            maximum_anchor_error_m=None if slip is None else float(slip),
            lift_m=float(lift),
        )
        checks[f"{side}_both_pads_contact_at_least_95_percent"] = bool(coverage >= 0.95)
        checks[f"{side}_material_slip_below_1_cm"] = bool(
            slip is not None and slip < 0.01
        )
        checks[f"{side}_material_lift_above_8_cm"] = bool(lift > 0.08)
    release_force = max((sum(row["forces"].values()) for row in released), default=None)
    metrics["maximum_final_robot_cloth_normal_force_N"] = (
        None if release_force is None else float(release_force)
    )
    checks["released_from_all_robot_geometries"] = bool(
        release_force is not None and release_force < 0.001
    )
    if task == "fold":
        # A fold must preserve the far part of the panel while moving its hem
        # onto that part. Robot trajectory completion alone cannot pass this.
        final = records[-1] if records else None
        for plan in plans:
            side = plan["side"]
            target = np.asarray(plan["fold_target"])
            hem_error = (
                np.linalg.norm(np.asarray(final["material"][side])[:2] - target[:2])
                if final
                else None
            )
            far_displacement = (
                np.linalg.norm(np.asarray(final["far_material"][side]) - target)
                if final
                else None
            )
            metrics[side].update(
                hem_target_error_m=None if hem_error is None else float(hem_error),
                far_material_displacement_m=None
                if far_displacement is None
                else float(far_displacement),
            )
            checks[f"{side}_hem_within_5_cm_of_fold_target"] = bool(
                hem_error is not None and hem_error < 0.05
            )
            checks[f"{side}_far_panel_displacement_below_5_cm"] = bool(
                far_displacement is not None and far_displacement < 0.05
            )
        checks["fold_settled_on_table"] = bool(
            final
            and final["cloth_height_range_m"][0] > 0.497
            and final["cloth_height_range_m"][1] < 0.53
        )
    return dict(passed=all(checks.values()), checks=checks, metrics=metrics)


def verify_saved(directory):
    """Read and rescore evidence without writing into the source directory."""
    import mujoco

    directory = Path(directory)
    original_hashes = input_hashes(directory)
    metadata = json.loads((directory / "summary.json").read_text())
    records = json.loads((directory / "trace.json").read_text())
    plans = []
    for path in sorted(directory.glob("plan-*.npz")):
        with np.load(path, allow_pickle=False) as archive:
            plan = dict(archive)
            plan["side"] = str(plan["side"])
            plans.append(plan)
    schedule = metadata["schedule_s"]
    result = verify_episode(
        records,
        metadata["maximums"],
        plans,
        task=metadata["task"],
        hold_end=schedule["hold_end"],
        duration=schedule["duration"],
        failure=metadata["failure"],
        sample_dt=metadata["sample_dt_s"],
    )
    model = mujoco.MjModel.from_binary_path(str(directory / "model.mjb"))
    cloth_bodies = set(model.flex_vertbodyid)
    guards = {
        "no_mocap_or_external_welds": model.nmocap == 0
        and bool(np.all(model.eq_type == mujoco.mjtEq.mjEQ_FLEX)),
        "no_cloth_actuators": not any(
            model.jnt_bodyid[j] in cloth_bodies for j in model.actuator_trnid[:, 0]
        ),
        "three_dof_passive_cloth_vertices": all(
            model.body_dofnum[b] == 3 for b in cloth_bodies
        ),
    }
    result["checks"].update(guards)
    # The archive is sampled at 25 Hz; replay only forward kinematics, never
    # integration. This complements the per-step native penetration maxima.
    from dexlab.cloth_self_contact import audit_record

    with np.load(directory / "states.npz", allow_pickle=False) as archive:
        times = archive["time_s"]
        poses = archive["qpos"]
        triangles = archive["triangles"]
    expected = np.arange(round(schedule["duration"] * 25)) / 25
    valid_states = (
        model.nflex == 1
        and poses.shape == (len(expected), model.nq)
        and times.shape == expected.shape
        and np.isfinite(poses).all()
        and np.allclose(times, expected, rtol=0, atol=1e-10)
        and triangles.ndim == 2 and triangles.shape[1] == 3
        and triangles.dtype.kind in 'iu'
        and np.array_equal(triangles.ravel(), model.flex_elem)
    )
    result["checks"]["complete_surface_audit_record"] = bool(valid_states)
    result["checks"]["no_sampled_surface_crossings"] = False
    if valid_states:
        data = mujoco.MjData(model)
        vertices = []
        for pose in poses:
            data.qpos[:] = pose
            mujoco.mj_fwdPosition(model, data)
            vertices.append(data.flexvert_xpos.copy())
        audit = audit_record(times, np.asarray(vertices), triangles)
        result["self_surface_audit"] = audit
        result["checks"]["no_sampled_surface_crossings"] = (
            audit["maximum_crossing_pairs"] == 0
            and audit["maximum_degenerate_triangles"] == 0
        )
        from dexlab.cloth_table_audit import audit_table

        result["table_surface_diagnostic"] = audit_table(
            model, times, poses, triangles, np.asarray(vertices)
        )
    else:
        result["table_surface_diagnostic"] = {
            "status": "insufficient_evidence", "reason": "Invalid saved surface states"
        }
    result["scorer_version"] = SCORER_VERSION
    result["verifier_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    from dexlab import cloth_table_audit, cloth_self_contact

    result["table_auditor_sha256"] = hashlib.sha256(
        Path(cloth_table_audit.__file__).read_bytes()
    ).hexdigest()
    result['self_auditor_sha256'] = hashlib.sha256(
        Path(cloth_self_contact.__file__).read_bytes()
    ).hexdigest()
    if input_hashes(directory) != original_hashes:
        raise ValueError('Recording changed during offline verification')
    result["input_sha256"] = original_hashes
    # Do not expose an unqualified success boolean in v2 offline reports.
    result.pop("passed", None)
    result["protocol_passed"] = all(result["checks"].values())
    result["protocol_scope"] = "Existing nominal protocol with corrected evidence integrity; not complete geometric validity"
    result["assessment"] = (
        "protocol_failed" if not result["protocol_passed"] else
        "geometry_review_required" if result["table_surface_diagnostic"]["status"] != "no_sampled_intrusion" else
        "limited_protocol_pass"
    )
    result["coverage_limits"] = [
        "Independent cloth versus robot surface audit is not implemented",
        "25 Hz saved states cannot certify separation between frames",
        "Table audit uses zero-thickness triangles, not shell thickness or native contact distance",
        "Table diagnostic is exploratory; no new physical pass threshold is imposed",
    ]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, help="New report path; existing files are never overwritten")
    args = parser.parse_args()
    if args.output and args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error('Report output must be outside the original recording')
    report = verify_saved(args.directory)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["protocol_passed"]:
        raise SystemExit(1)
    if report["assessment"] == "geometry_review_required":
        raise SystemExit(2)
