"""Read-only historical rescoring; complete cohorts, explicit metric semantics.

No environment is created and no dynamics are stepped. Locations are private
inputs; exports contain only cohort IDs, relative filenames and content hashes.
"""

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "historical-evidence-v1"
OUTCOMES = ("protocol_pass", "protocol_fail", "geometry_review_required",
            "unsupported", "timeout", "runtime_failure")
# Failed scientific checks remain outcomes. Failed evidence checks are errors.
INTEGRITY_CHECKS = {
    "complete_shapes", "complete_time_grid", "uniform_time_grid",
    "uniform_step_coverage", "finite_records", "finite_states",
    "finite_states_and_forces", "finite_samples", "finite_record", "complete_contact_coverage",
    "artifact_hashes_match", "archived_source_hashes_match", "source_unchanged",
    "contact_ledger_matches", "exact_record_hash", "declared_mesh",
    "prescribed_loads", "frozen_source", "source_snapshot_matches",
    "native_artifacts_intact", "full_native_log", "complete_surface_audit_record",
    "finite_complete_measurements", "complete_hand_plans", "complete_contact_scan",
    "summary_bounds_recorded_maxima", "contact_step_times_valid",
    "contact_ledger_matches_hand_force",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def inside(root, name):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Evidence paths must be relative and contained")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or escaping evidence file: {name}")
    return path


def verify_hashes(root, expected):
    if not expected:
        raise ValueError("Empty input manifest")
    actual = {name: digest(inside(root, name)) for name in expected}
    if actual != expected:
        raise ValueError("Evidence hash mismatch")
    return actual


def verdict(result, key="passed"):
    checks = result.get("checks")
    if not checks or any(type(v) is not bool for v in checks.values()):
        raise ValueError("Missing or nonboolean checks")
    if type(result.get(key)) is not bool or result[key] != all(checks.values()):
        raise ValueError("Contradictory summary and checks")
    return "protocol_pass" if result[key] else "protocol_fail"


def historical_records(spec, report):
    """Extract the entire frozen cohort, never just successful examples."""
    kind = spec["kind"]
    if "batch" in spec:
        report = report["batches"][spec["batch"]]
    records = []
    if kind == "apple":
        for job in report["jobs"]:
            outcome = verdict(job["outcome"])
            records.append(dict(id=job["id"], profile=job["backend"],
                                historical=outcome, expected=job["artifacts"],
                                mass=job["parameters"]["apple_mass"]))
    elif kind == "cloth":
        for row in report["records"]:
            job, metadata = row["job"], row["metadata"]
            if job["status"] == "timeout":
                outcome = "timeout"
            elif metadata["status"] == "unsupported":
                outcome = "unsupported"
            elif metadata["status"] != "completed":
                outcome = "runtime_failure"
            else:
                outcome = verdict(row["summary"], "protocol_checks_passed")
            if outcome in ("unsupported", "timeout", "runtime_failure") and row.get("summary"):
                if verdict(row["summary"], "protocol_checks_passed") == "protocol_pass":
                    raise ValueError("A terminal outcome cannot have a passing summary")
            if job["protocol_checks_passed"] != (outcome == "protocol_pass"):
                raise ValueError("Contradictory job and summary")
            records.append(dict(id=row["run"], profile=job["solver"],
                                historical=outcome, expected={
                                    "run.json": row["run_sha256"],
                                    "summary.json": job["summary_sha256"],
                                } if metadata else {}))
    elif kind in ("contact", "normal", "transient"):
        for row in report["results"]:
            result = row["current_review"] if kind == "contact" else row["result"]
            outcome = verdict(result)
            if kind == "transient":
                transient_outcome = verdict(row["transient"])
                if transient_outcome != "protocol_pass":
                    outcome = "protocol_fail"
            records.append(dict(id=row.get("run", row.get("id")), profile=row["engine"],
                                historical=outcome, contact_kind=row.get("kind"),
                                original_passed=row.get("original_passed"),
                                expected={"run.json": row.get("run_sha256", row.get("receipt_sha256"))}))
    elif kind == "robot_cloth":
        # This cohort starts at the legacy verdict; D02's diagnostic is retained.
        legacy = report["protocol_controls"]["original"]["old_protocol_passed"]
        if type(legacy) is not bool:
            raise ValueError("Invalid legacy verdict")
        records.append(dict(id="integration-grasp-v1", profile="mujoco",
                            historical="protocol_pass" if legacy else "protocol_fail",
                            expected=report["input_sha256"]))
    else:
        raise ValueError(f"Unknown cohort kind: {kind}")
    ids = [row["id"] for row in records]
    if len(ids) != spec["count"] or len(set(ids)) != len(ids):
        raise ValueError("Incomplete or duplicate cohort")
    if dict(Counter(row["historical"] for row in records)) != spec["historical_counts"]:
        raise ValueError("Historical cohort counts differ")
    for row in records:
        if Path(row["id"]).is_absolute() or ".." in Path(row["id"]).parts:
            raise ValueError("Invalid record ID")
    return records


def input_manifest(kind, directory, record):
    expected = dict(record["expected"])
    if not expected and record["historical"] in ("unsupported", "timeout", "runtime_failure"):
        return {}
    if kind in ("apple", "robot_cloth"):
        return expected
    verify_hashes(directory, expected)
    extra = {}
    if kind in ("contact", "normal", "transient"):
        meta = read_json(directory / "run.json")
        extra.update(meta["artifact_sha256"])
    elif kind == "cloth":
        meta = read_json(directory / "run.json")
        if meta.get("trajectory_sha256"):
            extra["trajectory.npz"] = meta["trajectory_sha256"]
        extra.update({"source/" + name: value for name, value in meta["source_before"].items()})
        extra.update({"native/" + name: value for name, value in meta.get("native_artifact_sha256", {}).items()})
        if meta.get("native_log_sha256"):
            extra["native-worker.log"] = meta["native_log_sha256"]
    if any(name in expected and expected[name] != value for name, value in extra.items()):
        raise ValueError("Nested input hashes conflict with the published receipt")
    expected.update(extra)
    return expected


def time_coverage(kind, directory):
    """Reject damaged time grids even when an old scorer tolerates them."""
    if kind == "apple":
        meta = read_json(directory / "engine.json")
        filename, key = "sdf-dynamics.npz", "time"
        dt, duration, initial = meta["dt"], 14.0, False
    elif kind == "cloth":
        meta = read_json(directory / "run.json")
        filename, key = "trajectory.npz", "time"
        dt, duration, initial = meta["dt_s"], meta["case"]["duration"], True
    elif kind == "robot_cloth":
        filename, key = "states.npz", "time_s"
        dt, duration, initial = 0.04, read_json(directory / "summary.json")["schedule_s"]["duration"], False
    else:
        case = read_json(directory / "run.json")["case"]
        filename, key = "states.npz", "time"
        dt, initial = case["timestep"], True
        if kind == "contact" and "duration" not in case:
            from dexlab.contact_pinch import CylinderCase
            duration = CylinderCase(**case).steps * dt
        else:
            duration = case["duration"]
    with np.load(directory / filename, allow_pickle=False) as data:
        times = data[key]
    if not np.isfinite([dt, duration]).all() or dt <= 0 or duration <= 0:
        raise ValueError("Invalid sampling period")
    expected = np.arange(round(duration / dt) + int(initial)) * dt
    if times.shape != expected.shape or not np.isfinite(times).all() or not np.allclose(times, expected, atol=1e-10, rtol=0):
        raise ValueError("Incomplete, duplicate or shifted time grid")
    return dict(samples=len(times), dt_s=dt, first_s=float(times[0]),
                last_s=float(times[-1]), episode_duration_s=duration,
                includes_end_time=initial,
                contains_unstepped_initial_state=kind != "apple",
                state_epoch=("pre_step_saved_state" if kind == "robot_cloth" else
                             "post_step_state_labelled_with_step_start" if kind == "apple" else
                             "initial_then_post_step_states"))


def robot_cloth_scorer():
    spec = importlib.util.spec_from_file_location("dexlab_verify_cloth", ROOT / "demos/cloth-folding/src/verify_cloth.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_saved


def rescore(kind, directory, record):
    if kind == "apple":
        from verify_sdf_grasp import verify_grasp
        return verify_grasp(directory, expected_mass=record["mass"])
    if kind == "cloth":
        from dexlab.cloth_benchmark import verify
        return verify(directory, write_summary=False)
    if kind == "robot_cloth":
        return robot_cloth_scorer()(directory)
    if kind == "contact" and record["contact_kind"] in ("plane", "material-readback"):
        from dexlab.contact_plane_native import verify
    elif kind == "contact" and record["contact_kind"] in (
        "cylinder", "timestep-refinement", "iteration-refinement", "surface-refinement", "refined-surface-controls"
    ):
        from dexlab.contact_pinch_run import verify
    elif kind in ("normal", "transient") or record["contact_kind"] == "indent":
        from dexlab.contact_indent_run import verify
    else:
        raise ValueError("Unknown contact protocol")
    result = verify(directory)
    if kind == "transient":
        from dexlab.contact_load import LoadCase
        from dexlab.contact_transient import score
        with np.load(directory / "states.npz", allow_pickle=False) as data:
            transient = score(LoadCase(**read_json(directory / "run.json")["case"]), data)
        result["checks"].update({"transient/" + k: v for k, v in transient["checks"].items()})
        result["passed"] = all(result["checks"].values())
        result["transient_metrics"] = transient["metrics"]
    return result


def quantities(kind, record, result):
    """Export only explicitly defined quantities, in SI units."""
    metrics = result["metrics"]
    values = {}
    unavailable = {}
    if kind == "apple":
        for target, source, scale in (
            ("apple.native_depth", "maximum_penetration_mm", .001),
            ("apple.wrist_translation", "maximum_wrist_relative_displacement_mm", .001),
            ("apple.wrist_rotation", "maximum_wrist_relative_rotation_deg", np.pi / 180),
            ("apple.clearance", "minimum_clearance_mm", .001),
            ("apple.support", "mean_hand_support_weight_ratio", 1),
            ("apple.momentum", "maximum_momentum_residual_weight_ratio", 1),
        ):
            values[target] = metrics[source] * scale
    elif kind == "cloth":
        for target, source in (
            ("cloth.ground_depth", "ground_penetration_m"),
            ("cloth.sphere_depth", "sphere_penetration_m"),
            ("cloth.edge_strain", "maximum_absolute_edge_strain"),
            ("cloth.pin_error", "maximum_pin_error_m"),
        ):
            values[target] = metrics["maximum"][source]
        values["cloth.final_tip_sag"] = metrics["final"]["tip_sag_m"]
        values["cloth.crossing_pairs"] = result["self_intersection_audit"]["maximum_crossing_pairs"]
    elif kind == "robot_cloth":
        diagnostic = result["table_surface_diagnostic"]
        for key, source in (("robot_cloth.table_depth", "maximum_interior_depth_m"),
                            ("robot_cloth.intrusion_frames", "frames_with_intrusion")):
            if source in diagnostic:
                values[key] = diagnostic[source]
            else:
                unavailable[key] = dict(value=None, status="unavailable", reason=diagnostic["status"])
        values["robot_cloth.anchor_error"] = metrics["r"]["maximum_anchor_error_m"]
        values["robot_cloth.lift"] = metrics["r"]["lift_m"]
    else:
        if kind in ("normal", "transient") or record.get("contact_kind") in ("plane", "material-readback", "indent"):
            depth_metric = "plane.box_depth"
        else:
            depth_metric = "cylinder.sat_depth"
        values[depth_metric] = metrics["maximum_penetration_m"]
        values["contact.momentum"] = metrics.get("maximum_momentum_residual_weight_ratio", metrics.get("peak_momentum_residual_weight_ratio"))
        if kind in ("normal", "transient"):
            values["normal.static_error"] = max(metrics["response_relative_errors"])
            values["normal.plateau_std"] = max(r["indentation_std_m"] for r in metrics["plateaus"][:3])
        if kind == "transient":
            values["normal.transient_rms"] = max(r["rms_error_m"] for r in result["transient_metrics"]["windows"])
            values["normal.transient_peak"] = max(r["peak_error_m"] for r in result["transient_metrics"]["windows"])
    if any(value is None or not np.isfinite(value) for value in values.values()):
        raise ValueError("Missing or nonfinite required metric")
    exported = {key: {"value": float(value), "status": "observed"} for key, value in values.items()}
    exported.update(unavailable)
    if kind == "cloth":
        experiment = record["experiment"]
        applicable = {
            "cloth.ground_depth": experiment in ("drape", "folded-drop"),
            "cloth.sphere_depth": experiment == "drape",
            "cloth.pin_error": experiment in ("extension", "sag"),
        }
        for key, present in applicable.items():
            if not present:
                exported[key] = dict(value=None, status="not_applicable", reason="No such obstacle or boundary in this declared case")
    exported["material_slip"] = dict(value=None, status="unavailable", reason="No persistent material-pair tangential displacement record")
    return exported


def source_identity():
    files = list((ROOT / "src/dexlab").rglob("*.py"))
    files += list((ROOT / "demos/apple-stem-grasp/src").glob("*.py"))
    files += [ROOT / "demos/cloth-folding/src/verify_cloth.py"]
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(files)}


def build_report(plan_path, locations, *, progress=None):
    plan = read_json(plan_path)
    definitions_path = ROOT / "docs/evidence/metrics.json"
    definitions = read_json(definitions_path)
    sources = source_identity()
    frozen_files = {plan_path: digest(plan_path), definitions_path: digest(definitions_path)}
    reference_assets = {}
    if any(spec["kind"] == "apple" for spec in plan["cohorts"]):
        for name in ("apple-collision.obj", "stem-collision.obj"):
            path = inside(ROOT, "demos/apple-stem-grasp/assets/apple/" + name)
            reference_assets[str(path.relative_to(ROOT))] = digest(path)
            frozen_files[path] = digest(path)
    output = dict(schema=SCHEMA, selection_sha256=digest(plan_path),
                  metric_definitions_sha256=digest(definitions_path),
                  scorer_sha256=sources,
                  reference_asset_sha256=reference_assets,
                  environment={name: importlib.metadata.version(name) for name in ("numpy", "scipy", "mujoco")},
                  tracks={"measured_physical_accuracy": "unavailable: no measured reference dataset",
                          "equal_budget_task_performance": "unavailable: historical tuning budgets unmatched"},
                  cohorts=[], records=[])
    if set(locations) != {spec["id"] for spec in plan["cohorts"]}:
        raise ValueError("Private locations must cover exactly the selected cohorts")
    for spec in plan["cohorts"]:
        historical_path = inside(ROOT, spec["report"])
        if digest(historical_path) != spec["report_sha256"]:
            raise ValueError("Frozen report changed")
        frozen_files[historical_path] = spec["report_sha256"]
        records = historical_records(spec, read_json(historical_path))
        cohort_rows = []
        for record in records:
            location = locations[spec["id"]]
            directory = Path(location[record["id"]]) if isinstance(location, dict) else Path(location) / record["id"]
            kind = spec["kind"]
            expected = input_manifest(kind, directory, record)
            before = verify_hashes(directory, expected) if expected else {}
            outcome = record["historical"]
            row = dict(cohort=spec["id"], id=record["id"], profile=record["profile"],
                       historical_outcome=outcome, input_sha256=before,
                       historical_report=spec["report"], metrics={}, checks={}, coverage=None)
            row["input_scope"] = "listed raw files" if before else "terminal outcome in frozen cohort receipt only; no raw record"
            if record.get("original_passed") is not None:
                row["original_outcome"] = "protocol_pass" if record["original_passed"] else "protocol_fail"
            if outcome in ("unsupported", "timeout", "runtime_failure"):
                row["metrics"] = {"material_slip": dict(value=None, status="unavailable", reason=outcome)}
            else:
                row["coverage"] = time_coverage(kind, directory)
                if kind == "cloth":
                    record["experiment"] = read_json(directory / "run.json")["case"]["experiment"]
                result = rescore(kind, directory, record)
                bad = [name for name, passed in result["checks"].items() if name.removeprefix("transient/") in INTEGRITY_CHECKS and not passed]
                if bad:
                    raise ValueError(f"Invalid evidence in {record['id']}: {bad}")
                key = {"cloth": "protocol_checks_passed", "robot_cloth": "protocol_passed"}.get(kind, "passed")
                outcome = verdict(result, key)
                if kind == "robot_cloth" and result["assessment"] == "geometry_review_required":
                    outcome = "geometry_review_required"
                row["checks"] = result["checks"]
                row["metrics"] = quantities(kind, record, result)
                if kind == "cloth":
                    row["surface_coverage"] = result["self_intersection_audit"]
                if kind == "robot_cloth":
                    row["surface_coverage"] = result["self_surface_audit"]
            if not set(row["metrics"]) <= definitions.keys():
                raise ValueError("Exported metric lacks a definition")
            if before:
                verify_hashes(directory, before)
            row["outcome"] = outcome
            row["inputs_unchanged"] = True if before else None
            cohort_rows.append(row)
            if progress:
                progress(spec["id"], record["id"], outcome)
        output["cohorts"].append(dict(id=spec["id"], kind=spec["kind"], count=len(cohort_rows),
                                      historical_counts=dict(Counter(r["historical_outcome"] for r in cohort_rows)),
                                      counts=dict(Counter(r["outcome"] for r in cohort_rows)),
                                      raw_source=spec["raw_source"], report_sha256=spec["report_sha256"]))
        output["records"].extend(cohort_rows)
    if sources != source_identity():
        raise ValueError("Scorer changed during rescoring")
    if any(digest(path) != value for path, value in frozen_files.items()):
        raise ValueError("Selection, definitions or historical reports changed during rescoring")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=ROOT / "docs/evidence/cohorts.json")
    parser.add_argument("--locations", type=Path, required=True, help="Private JSON mapping cohort IDs to roots or per-record directories")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    locations = read_json(args.locations)
    roots = [Path(path).resolve() for value in locations.values() for path in (value.values() if isinstance(value, dict) else [value])]
    if args.output.exists() or any(args.output.resolve().is_relative_to(root) for root in roots):
        parser.error("Use a fresh report path outside every raw input directory")
    report = build_report(args.selection, locations, progress=lambda cohort, record, outcome: print(f"{cohort}/{record}: {outcome}", flush=True))
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
