"""Public banana-force reporting rejects incomplete experimental evidence."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_banana_force_report.py"
SPEC = importlib.util.spec_from_file_location("banana_force_report", SCRIPT)
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


class BananaForceReportTests(unittest.TestCase):
    def _write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def _score(self, particle_count=10, timestep=1e-3):
        return {
            "particle_count": particle_count,
            "timestep_s": timestep,
            "first_support_time_s": .3,
            "peak_material_resistance_n_before_support": 1.0,
            "material_impulse_ns_before_support": .1,
            "maximum_momentum_residual_ns": 1e-14,
            "minimum_jacobian": .9,
        }

    def _trace(self, path, scale=1):
        time = np.array([0., .1, .2, .3, .4])
        material = scale * np.array([0., .5, 1., 0., 0.])
        support = np.array([0., 0., 0., 2., 0.])
        np.savez_compressed(path, time_s=time, material_resistance_n=material,
                            rigid_support_resistance_n=support,
                            total_resistance_n=material+support,
                            actuator_axial_force_n=np.ones_like(time))

    def _manifest(self, folder, *, refined=False):
        self._write_json(folder / "manifest.json", {
            "status": "complete", "git_dirty": False, "git_head": "abc123",
            "source_sha256": {"src/dexlab/cutting.py": "deadbeef"},
            **({"segments": [{"index": 0}], "wall_s_including_jit": 1.}
               if refined else {}),
        })

    def _fixtures(self, root, baseline_complete=True, refined_support_failure=False):
        baseline, sensitivity, refined = (root / name for name in
                                          ("baseline", "sensitivity", "refined"))
        scores = {f"base-seed-{seed}": self._score() for seed in range(20)}
        cohort = np.stack([(1 + seed/100) * np.array([0., .5, 1., 0., 0.])
                           for seed in range(20)])
        convergence = {
            "individual_material_peak_mean_n": 1.,
            "individual_material_peak_standard_deviation_n": .1,
            "cohort_pre_support_peak_mean_n": float(cohort.mean(axis=0)[:3].max()),
            "cohort_pre_support_peak_standard_deviation_n": float(
                cohort.std(axis=0, ddof=1)[:3].max()),
            "material_impulse_mean_ns": .1,
            "material_impulse_standard_deviation_ns": .01,
        }
        self._write_json(baseline / "summary.json", {
            "suite": "baseline", "complete": baseline_complete, "passed": True,
            "case_scores": scores, "baseline_sampling_hash_count": 20,
            "convergence": convergence,
        })
        for seed in range(20):
            folder = baseline / "cases" / f"base-seed-{seed}"
            folder.mkdir(parents=True)
            self._trace(folder / "trace.npz", 1 + seed/100)
            self._manifest(folder)
        sensitivity_rmse = {
            "sensitivity-dt-6.25e-05": .6,
            "sensitivity-dt-0.00025": .2,
            "sensitivity-normal-0.05": .15,
            "sensitivity-normal-0.2": .4,
        }
        self._write_json(sensitivity / "summary.json", {
            "suite": "sensitivity", "complete": True, "passed": True,
            "case_scores": {name: self._score() for name in sensitivity_rmse},
            "convergence": {
                "sensitivity_vs_seed_0_pre_support_normalized_rmse": sensitivity_rmse},
        })
        for name in sensitivity_rmse:
            folder = sensitivity / "cases" / name
            folder.mkdir(parents=True)
            self._manifest(folder)
        refined_score = self._score(640, 2.5e-4)
        if refined_support_failure:
            refined_score.update(
                passed=False,
                first_support_time_s=None,
                checks={
                    "clean_exact_source": True,
                    "configuration_matches_protocol": True,
                    "bounded_execution": True,
                    "timeline_matches_manifest": True,
                    "finite_observations": True,
                    "force_channel_identity": True,
                    "momentum_balance": True,
                    "positive_jacobian": True,
                    "material_epoch_before_support": True,
                    "support_epoch_observed": False,
                    "cut_progress_observed": True,
                },
            )
        self._write_json(refined / "summary.json", {
            "suite": "refined", "complete": True,
            "passed": not refined_support_failure,
            "checks": {
                "all_declared_cases_present": True,
                "all_declared_cases_pass": not refined_support_failure,
                "exact_refined_particle_ratio": True,
            },
            "case_scores": {"refined-centres": refined_score},
            "refined_particle_ratio": 64, "convergence": {},
        })
        folder = refined / "cases" / "refined-centres"
        folder.mkdir(parents=True)
        self._trace(folder / "trace.npz", .8)
        self._manifest(folder, refined=True)
        receipts = []
        for index in range(3):
            receipt = root / f"receipt-{index}.json"
            self._write_json(receipt, {
                "state": "completed", "returncode": 0, "wall_s": 1.,
                "telemetry": {
                    "state": "completed", "returncode": 0, "final": {},
                    "effective_service_properties": {
                        "RuntimeMaxUSec": "1min", "TasksMax": "8",
                        "KillMode": "control-group"},
                    "effective_limits": {
                        "memory.swap.max": "0", "memory.max": "1",
                        "memory.high": "1", "cpu.max": "1 1", "pids.max": "8",
                        "io.max": "8:0 rbps=1"}},
            })
            receipts.append(receipt)
        protocol = root / "protocol.json"
        self._write_json(protocol, {"status": "frozen-before-acceptance-runs", "execution_budget": {
            "maximum_segments_per_case": 4,
            "maximum_wall_s": {"refined": 10., "all_cases_cumulative": 10.}}})
        return baseline, sensitivity, refined, receipts, protocol

    def test_complete_qualified_inputs_build_evidence_and_figure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, sensitivity, refined, receipts, protocol = self._fixtures(root)
            evidence_path, figure_path = root / "evidence.json", root / "force.svg"
            evidence = REPORT.build_report(
                baseline_dir=baseline, sensitivity_dir=sensitivity, refined_dir=refined,
                receipts=receipts, protocol_path=protocol,
                evidence_path=evidence_path, figure_path=figure_path)
            self.assertTrue(evidence["qualified"])
            self.assertEqual(evidence["sampling"]["runs"], 20)
            self.assertEqual(evidence["refinement"]["particle_ratio"], 64)
            self.assertEqual(
                evidence["source_frozen_unpublished_controls"]
                ["particle_contact_radius_scale_s_r"], 1.0)
            self.assertTrue(evidence_path.is_file())
            self.assertIn("<svg", figure_path.read_text()[:500])

    def test_completed_refined_support_failure_is_published_as_negative(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, sensitivity, refined, receipts, protocol = self._fixtures(
                root, refined_support_failure=True)
            evidence = REPORT.build_report(
                baseline_dir=baseline, sensitivity_dir=sensitivity, refined_dir=refined,
                receipts=receipts, protocol_path=protocol,
                evidence_path=root / "evidence.json", figure_path=root / "force.svg")
            self.assertFalse(evidence["qualified"])
            self.assertEqual(
                evidence["refined_acceptance"]["failed_checks"],
                ["support_epoch_observed"])

    def test_incomplete_baseline_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, sensitivity, refined, receipts, protocol = self._fixtures(
                root, baseline_complete=False)
            with self.assertRaisesRegex(ValueError, "Incomplete or failed baseline"):
                REPORT.build_report(
                    baseline_dir=baseline, sensitivity_dir=sensitivity,
                    refined_dir=refined, receipts=receipts, protocol_path=protocol,
                    evidence_path=root / "evidence.json", figure_path=root / "force.svg")

    def test_receipt_without_io_limit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, sensitivity, refined, receipts, protocol = self._fixtures(root)
            damaged = json.loads(receipts[0].read_text())
            del damaged["telemetry"]["effective_limits"]["io.max"]
            self._write_json(receipts[0], damaged)
            with self.assertRaisesRegex(ValueError, "Required cgroup limits"):
                REPORT.build_report(
                    baseline_dir=baseline, sensitivity_dir=sensitivity,
                    refined_dir=refined, receipts=receipts, protocol_path=protocol,
                    evidence_path=root / "evidence.json", figure_path=root / "force.svg")

    def test_unmatched_extra_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, sensitivity, refined, receipts, protocol = self._fixtures(root)
            extra = root / "unmatched-receipt.json"
            extra.write_bytes(receipts[0].read_bytes())
            with self.assertRaisesRegex(ValueError, "Receipts must contain"):
                REPORT.build_report(
                    baseline_dir=baseline, sensitivity_dir=sensitivity,
                    refined_dir=refined, receipts=[*receipts, extra],
                    protocol_path=protocol, evidence_path=root / "evidence.json",
                    figure_path=root / "force.svg")


if __name__ == "__main__":
    unittest.main()
