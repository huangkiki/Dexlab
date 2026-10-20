#!/usr/bin/env python3
"""Build the public banana-force evidence from qualified local runs."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _read_json(path):
    return json.loads(Path(path).read_text())


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _qualified_summary(directory, suite, *, allow_refined_support_failure=False):
    path = Path(directory) / "summary.json"
    summary = _read_json(path)
    if summary.get("suite") != suite:
        raise ValueError(f"Expected {suite!r} suite in {path}")
    if not summary.get("complete"):
        raise ValueError(f"Incomplete or failed {suite} suite cannot be published")
    if summary.get("passed"):
        return path, summary
    if allow_refined_support_failure and suite == "refined":
        score = summary.get("case_scores", {}).get("refined-centres", {})
        checks = score.get("checks", {})
        failed_checks = sorted(name for name, passed in checks.items() if not passed)
        suite_checks = summary.get("checks", {})
        if (failed_checks == ["support_epoch_observed"]
                and score.get("passed") is False
                and score.get("first_support_time_s") is None
                and suite_checks.get("all_declared_cases_present") is True
                and suite_checks.get("exact_refined_particle_ratio") is True
                and suite_checks.get("all_declared_cases_pass") is False):
            return path, summary
    raise ValueError(f"Incomplete or failed {suite} suite cannot be published")


def _qualified_receipt(path):
    receipt = _read_json(path)
    telemetry = receipt.get("telemetry", {})
    if receipt.get("state") != "completed" or receipt.get("returncode") != 0:
        raise ValueError(f"Incomplete or failed bounded receipt: {path}")
    if telemetry.get("state") != "completed" or telemetry.get("returncode") != 0:
        raise ValueError(f"Missing final bounded telemetry: {path}")
    if "final" not in telemetry:
        raise ValueError(f"Missing final cgroup counters: {path}")
    limits = telemetry.get("effective_limits", {})
    required_limits = {"memory.max", "memory.high", "cpu.max", "pids.max", "io.max"}
    if (limits.get("memory.swap.max") != "0"
            or not required_limits.issubset(limits)):
        raise ValueError(f"Required cgroup limits are absent: {path}")
    properties = telemetry.get("effective_service_properties", {})
    if (not properties.get("RuntimeMaxUSec")
            or not properties.get("TasksMax")
            or properties.get("KillMode") != "control-group"):
        raise ValueError(f"Required task/runtime service limits are absent: {path}")
    return receipt


def _trace(case_directory):
    path = Path(case_directory) / "trace.npz"
    with np.load(path) as archive:
        required = ("time_s", "material_resistance_n", "rigid_support_resistance_n",
                    "total_resistance_n", "actuator_axial_force_n")
        missing = set(required).difference(archive.files)
        if missing:
            raise ValueError(f"Missing force channels in {path}: {sorted(missing)}")
        return {name: np.asarray(archive[name]) for name in required}


def _complete_manifest(case_directory):
    path = Path(case_directory) / "manifest.json"
    manifest = _read_json(path)
    if manifest.get("status") != "complete" or manifest.get("git_dirty"):
        raise ValueError(f"Case is incomplete or was run from a dirty tree: {path}")
    if not manifest.get("git_head") or not manifest.get("source_sha256"):
        raise ValueError(f"Case source identity is incomplete: {path}")
    return manifest


def _before_support(trace, support_time):
    mask = trace["time_s"] < support_time
    if mask.sum() < 2:
        raise ValueError("Force trace has no material-only epoch")
    return mask


def _normalized_rmse(reference_time, reference, candidate_time, candidate, mask):
    selected = mask.copy()
    selected &= reference_time >= candidate_time[0]
    selected &= reference_time <= candidate_time[-1]
    if not selected.any():
        raise ValueError("Force curves have no shared comparison epoch")
    aligned = np.interp(reference_time[selected], candidate_time, candidate)
    scale = max(float(np.ptp(reference[selected])),
                float(np.max(np.abs(reference[selected]))), 1e-12)
    return float(np.sqrt(np.mean((aligned-reference[selected])**2)) / scale)


def build_report(*, baseline_dir, sensitivity_dir, refined_dir, receipts,
                 protocol_path, evidence_path, figure_path):
    baseline_path, baseline = _qualified_summary(baseline_dir, "baseline")
    sensitivity_path, sensitivity = _qualified_summary(sensitivity_dir, "sensitivity")
    refined_path, refined = _qualified_summary(
        refined_dir, "refined", allow_refined_support_failure=True)
    receipt_records = [_qualified_receipt(path) for path in receipts]
    protocol = _read_json(protocol_path)
    if protocol.get("status") != "frozen-before-acceptance-runs":
        raise ValueError("Banana-force protocol was not frozen before the qualified runs")
    budget = protocol["execution_budget"]
    if len(receipt_records) < 3:
        raise ValueError("Baseline, sensitivity and refined execution need bounded receipts")
    bounded_wall_s = [float(record["wall_s"]) for record in receipt_records]
    if sum(bounded_wall_s) > budget["maximum_wall_s"]["all_cases_cumulative"]:
        raise ValueError("Qualified runs exceed the frozen cumulative wall-time budget")

    baseline_scores = baseline["case_scores"]
    expected = [f"base-seed-{seed}" for seed in range(20)]
    if sorted(baseline_scores) != sorted(expected):
        raise ValueError("Baseline evidence must contain exactly seeds 0 through 19")
    if baseline.get("baseline_sampling_hash_count") != 20:
        raise ValueError("Baseline particle samplings are not twenty distinct records")
    if refined.get("refined_particle_ratio") != 64:
        raise ValueError("Refined evidence does not contain exactly 64x particles")

    base_case_directories = [Path(baseline_dir) / "cases" / case for case in expected]
    manifests = [_complete_manifest(directory) for directory in base_case_directories]
    manifests.extend(_complete_manifest(Path(sensitivity_dir) / "cases" / case)
                     for case in sensitivity["case_scores"])
    refined_manifest = _complete_manifest(Path(refined_dir) / "cases" / "refined-centres")
    manifests.append(refined_manifest)
    refined_segments = refined_manifest.get("segments", ())
    if len(receipt_records) != 2 + len(refined_segments):
        raise ValueError("Receipts must contain baseline, sensitivity and every refined segment")
    if len(refined_segments) > budget["maximum_segments_per_case"]:
        raise ValueError("Refined run exceeds the frozen segment budget")
    if refined_manifest.get("wall_s_including_jit", np.inf) > budget["maximum_wall_s"]["refined"]:
        raise ValueError("Refined run exceeds the frozen wall-time budget")
    source_heads = {manifest["git_head"] for manifest in manifests}
    source_hashes = {json.dumps(manifest["source_sha256"], sort_keys=True)
                     for manifest in manifests}
    if len(source_heads) != 1 or len(source_hashes) != 1:
        raise ValueError("Published cases do not share one exact source identity")
    base_traces = [_trace(directory) for directory in base_case_directories]
    time = base_traces[0]["time_s"]
    if any(not np.array_equal(item["time_s"], time) for item in base_traces[1:]):
        raise ValueError("Pointwise cohort mean requires identical baseline sample times")
    support_time = min(float(baseline_scores[case]["first_support_time_s"])
                       for case in expected)
    mask = _before_support(base_traces[0], support_time)
    material = np.stack([item["material_resistance_n"] for item in base_traces])
    mean, standard_deviation = material.mean(axis=0), material.std(axis=0, ddof=1)
    convergence = baseline["convergence"]
    if not np.isclose(mean[mask].max(), convergence["cohort_pre_support_peak_mean_n"]):
        raise ValueError("Baseline summary does not match saved force traces")
    if not np.isclose(standard_deviation[mask].max(),
                      convergence["cohort_pre_support_peak_standard_deviation_n"]):
        raise ValueError("Baseline dispersion does not match saved force traces")

    refined_trace = _trace(Path(refined_dir) / "cases" / "refined-centres")
    refined_score = refined["case_scores"]["refined-centres"]
    refined_support_time = refined_score["first_support_time_s"]
    refined_mask = (np.ones_like(refined_trace["time_s"], dtype=bool)
                    if refined_support_time is None else
                    _before_support(refined_trace, float(refined_support_time)))
    refined_vs_cohort = _normalized_rmse(
        time, mean, refined_trace["time_s"], refined_trace["material_resistance_n"], mask)
    seed_zero = base_traces[0]
    sensitivity_rmse = sensitivity["convergence"][
        "sensitivity_vs_seed_0_pre_support_normalized_rmse"]
    if len(sensitivity_rmse) != 4:
        raise ValueError("Expected four one-factor-at-a-time sensitivity cases")

    figure_path = Path(figure_path)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 3, figsize=(13.2, 3.8), layout="constrained")

    axes[0].plot(time[mask], seed_zero["material_resistance_n"][mask],
                 color="#9e9e9e", linewidth=.8, label="single sampling")
    axes[0].fill_between(time[mask], (mean-standard_deviation)[mask],
                         (mean+standard_deviation)[mask], color="#1565c0", alpha=.18,
                         linewidth=0, label="20-sampling ±1 std")
    axes[0].plot(time[mask], mean[mask], color="#1565c0", linewidth=1.5,
                 label="20-sampling mean")
    axes[0].plot(refined_trace["time_s"][refined_mask],
                 refined_trace["material_resistance_n"][refined_mask],
                 color="#ef6c00", linewidth=1.0,
                 label=("64× particles" if refined.get("passed") else
                        "64× particles — no support contact"))
    axes[0].set(title="Material resistance before support contact",
                xlabel="Time (s)", ylabel="Axial resistance (N)")
    axes[0].legend(fontsize=7)

    axes[1].plot(time, seed_zero["material_resistance_n"], label="material", linewidth=1)
    axes[1].plot(time, seed_zero["rigid_support_resistance_n"], label="rigid support",
                 linewidth=1)
    axes[1].plot(time, seed_zero["total_resistance_n"], label="reported total",
                 linewidth=1)
    axes[1].plot(time, seed_zero["actuator_axial_force_n"], label="actuator (excluded)",
                 linewidth=.8, linestyle="--")
    axes[1].axvline(baseline_scores["base-seed-0"]["first_support_time_s"],
                    color="#424242", linewidth=.7, linestyle=":")
    axes[1].set(title="Force-channel accounting, seed 0",
                xlabel="Time (s)", ylabel="Axial force (N)")
    axes[1].set_yscale("symlog", linthresh=.1)
    axes[1].legend(fontsize=7)

    labels = ["dt / 2", "dt × 2", "normal / 2", "normal × 2"]
    keys = ["sensitivity-dt-6.25e-05", "sensitivity-dt-0.00025",
            "sensitivity-normal-0.05", "sensitivity-normal-0.2"]
    axes[2].bar(labels, [sensitivity_rmse[key] for key in keys], color="#6a1b9a")
    axes[2].set(title="Pre-support sensitivity vs seed 0",
                ylabel="Normalized RMSE")
    axes[2].tick_params(axis="x", rotation=20)
    axes[2].grid(axis="y", alpha=.2)

    figure.suptitle(
        "Independent DexLab banana-force protocol — no raw robot trace available",
        fontsize=12,
    )
    figure.savefig(figure_path)
    plt.close(figure)
    # Matplotlib emits path-data lines with trailing spaces. Keep the public
    # SVG deterministic and compatible with the repository whitespace gate.
    figure_path.write_text("\n".join(
        line.rstrip() for line in figure_path.read_text().splitlines()) + "\n")

    protocol_path = Path(protocol_path)
    refined_case = refined["case_scores"]["refined-centres"]
    evidence = {
        "schema_version": 1,
        "experiment": "independent BladeMaster-style single vertical banana cut",
        "qualified": bool(refined.get("passed")),
        "execution_complete": True,
        "baseline_and_sensitivity_passed": True,
        "refined_acceptance": {
            "passed": bool(refined.get("passed")),
            "failed_checks": sorted(
                name for name, passed in refined_score.get("checks", {}).items()
                if not passed),
            "interpretation": (
                "The frozen 64x case did not reach rigid-support contact within "
                "0.5 s. Its material response is retained as a negative result; "
                "it does not establish refinement convergence."
                if not refined.get("passed") else
                "The frozen 64x case passed every declared acceptance check."
            ),
        },
        "qualification_scope": (
            "Numerical integrity, 20-sampling dispersion, one-factor sensitivity and "
            "a completed 64x-particle refinement of the frozen DexLab model. The "
            "refined case is a retained negative acceptance result. No raw "
            "robot-force agreement or author-code equivalence claim."
        ),
        "paper_reference": "https://arxiv.org/html/2609.27342v2#S4.SS3",
        "protocol_sha256": _sha256(protocol_path),
        "source_git_head": source_heads.pop(),
        "source_sha256": json.loads(source_hashes.pop()),
        "sampling": {
            "runs": 20,
            "distinct_particle_sampling_hashes": baseline["baseline_sampling_hash_count"],
            "individual_material_peak_mean_n": baseline["convergence"]["individual_material_peak_mean_n"],
            "individual_material_peak_standard_deviation_n": baseline["convergence"]["individual_material_peak_standard_deviation_n"],
            "pointwise_mean_pre_support_peak_n": baseline["convergence"]["cohort_pre_support_peak_mean_n"],
            "maximum_pointwise_standard_deviation_pre_support_n": baseline["convergence"]["cohort_pre_support_peak_standard_deviation_n"],
            "material_impulse_mean_ns": baseline["convergence"]["material_impulse_mean_ns"],
            "material_impulse_standard_deviation_ns": baseline["convergence"]["material_impulse_standard_deviation_ns"],
        },
        "refinement": {
            "particle_ratio": refined["refined_particle_ratio"],
            "particle_count": refined_case["particle_count"],
            "timestep_s": refined_case["timestep_s"],
            "pre_support_material_peak_n": refined_case["peak_material_resistance_n_before_support"],
            "material_impulse_ns_before_support": refined_case["material_impulse_ns_before_support"],
            "first_support_time_s": refined_case["first_support_time_s"],
            "vs_twenty_sampling_mean_pre_support_normalized_rmse": refined_vs_cohort,
        },
        "sensitivity_vs_seed_0_pre_support_normalized_rmse": sensitivity_rmse,
        "force_channels": {
            "resistance_total": "material resistance + rigid-support resistance",
            "actuator": "recorded separately and excluded from resistance",
        },
        "source_frozen_unpublished_controls": {
            "paper_specified_cut_band_half_width": "6 * reference_grid_spacing",
            "particle_contact_radius_scale_s_r": 1.0,
            "cut_band_rear_extent": "2 * reference_grid_spacing",
            "cut_band_lead_extent": "2 * particle_radius",
            "minimum_cut_advance_speed_m_s": 0.0,
            "intact_reference_neighbor_exclusion_distance": (
                "2 * reference_grid_spacing"
            ),
            "qualification_boundary": (
                "The first field matches the paper. The other values were frozen in "
                "the exact hashed source before execution because the paper does not "
                "publish them; this experiment does not vary them independently."
            ),
        },
        "numerical_integrity": {
            "maximum_momentum_residual_ns": max(
                score["maximum_momentum_residual_ns"]
                for summary in (baseline, sensitivity, refined)
                for score in summary["case_scores"].values()),
            "minimum_jacobian": min(
                score["minimum_jacobian"]
                for summary in (baseline, sensitivity, refined)
                for score in summary["case_scores"].values()),
        },
        "inputs": {
            "baseline_summary_sha256": _sha256(baseline_path),
            "sensitivity_summary_sha256": _sha256(sensitivity_path),
            "refined_summary_sha256": _sha256(refined_path),
            "bounded_receipt_sha256": [_sha256(path) for path in receipts],
            "bounded_wall_s": bounded_wall_s,
            "bounded_wall_s_total": sum(bounded_wall_s),
            "frozen_cumulative_wall_s_limit": budget["maximum_wall_s"][
                "all_cases_cumulative"],
        },
        "figure": str(figure_path),
    }
    evidence_path = Path(evidence_path)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--sensitivity", required=True, type=Path)
    parser.add_argument("--refined", required=True, type=Path)
    parser.add_argument("--receipt", action="append", required=True, type=Path)
    parser.add_argument("--protocol", type=Path,
                        default=Path("demos/banana-force/force-protocol.json"))
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--figure", required=True, type=Path)
    args = parser.parse_args()
    build_report(baseline_dir=args.baseline, sensitivity_dir=args.sensitivity,
                 refined_dir=args.refined, receipts=args.receipt,
                 protocol_path=args.protocol, evidence_path=args.evidence,
                 figure_path=args.figure)
    print(args.evidence)
    print(args.figure)


if __name__ == "__main__":
    main()
