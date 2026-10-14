"""Protect native task semantics, measurement epochs and immutable trial budgets."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np

from dexlab.libero_workflow import (
    file_hash,
    observation_difference,
    relocate_assets,
    settle_observation,
    TASK,
    UPSTREAM,
)
from dexlab.libero_score import momentum_residual, score
from dexlab.libero_trials import validate


class LiberoWorkflowTests(unittest.TestCase):
    def test_settle_returns_last_observation_without_changing_actions(self):
        class Environment:
            action_dim = 7

            def __init__(self):
                self.actions = []

            def step(self, action):
                self.actions.append(action)
                return {"position": np.array([len(self.actions)])}, 0, False, {}

        env = Environment()
        stale = {"position": np.array([0])}
        fresh = settle_observation(env, stale)
        self.assertEqual(fresh["position"].item(), 5)
        self.assertEqual(stale["position"].item(), 0)
        np.testing.assert_array_equal(env.actions, np.zeros((5, 7)))
        self.assertEqual(observation_difference(stale, fresh), {"position": 5.0})

    def test_observation_missing_channel_shape_or_nonfinite_is_rejected(self):
        for fresh in ({}, {"x": [1, 2]}, {"x": [float("nan")]}):
            with self.assertRaises(ValueError):
                observation_difference({"x": [0]}, fresh)

    def test_asset_relocation_changes_only_paths_and_preserves_physics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            asset = root / "libero/libero/assets/object/mesh.stl"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"fixture")
            xml = '<mujoco><asset><mesh name="a" file="/old/LIBERO/libero/libero/assets/object/mesh.stl"/></asset><worldbody><geom friction=".5 .1 .01" solref=".001 1"/></worldbody></mujoco>'
            relocated, sources = relocate_assets(xml, root, root / "robosuite")
            result = ET.fromstring(relocated)
            self.assertEqual(
                result.find("./worldbody/geom").attrib,
                ET.fromstring(xml).find("./worldbody/geom").attrib,
            )
            self.assertEqual(result.find("./asset/mesh").get("file"), str(asset))
            self.assertEqual(sources[0]["sha256"], file_hash(asset))
            with self.assertRaises(ValueError):
                relocate_assets(
                    xml.replace("/old/LIBERO/libero/libero/assets/object", "/unknown"),
                    root,
                    root,
                )

    def test_contact_impulse_clock_and_sign_are_physically_detectable(self):
        rows = np.zeros((3, 32))
        rows[:, 0] = [0, 0.002, 0.004]
        rows[:, 1] = rows[:, 0] + 0.002
        rows[:, 18] = rows[:, 22] = 1.0
        rows[:, 11] = 0.1 * 9.81
        residual = momentum_residual(rows, 0.1, np.array([0, 0, -9.81]), np.zeros(3))
        np.testing.assert_allclose(residual, 0.0, atol=1e-12)
        rows[:, 11] *= -1
        np.testing.assert_allclose(
            momentum_residual(rows, 0.1, np.array([0, 0, -9.81]), np.zeros(3)), 2.0
        )

    def test_free_fall_has_zero_momentum_residual(self):
        rows = np.zeros((2, 32))
        rows[:, 1] = 0.002
        rows[:, 18] = rows[:, 22] = 1.0
        rows[:, 8] = -0.002 * 9.81
        np.testing.assert_allclose(
            momentum_residual(rows, 0.1, np.array([0, 0, -9.81]), np.zeros(3)),
            0.0,
            atol=1e-12,
        )

    def manifest(self, root):
        source = root / "evidence.json"
        source.write_text("{}")
        return {
            "schema_version": 1,
            "upstream_commit": UPSTREAM,
            "task": TASK,
            "libero_root": str(root),
            "development": ["demo_0"],
            "heldout": ["demo_1"],
            "inputs": [{"path": str(source), "sha256": file_hash(source)}],
            "candidates": [
                {
                    "id": "baseline",
                    "mode": "actions",
                    "instrument": True,
                    "timestep_scale": 1.0,
                    "hypothesis": "Original native baseline",
                }
            ],
        }

    def test_changed_sources_holdout_leakage_and_candidate_limit_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            good = self.manifest(root)
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                validate(good)
            for kind in (
                "hash",
                "split",
                "candidates",
                "mode",
                "parameter",
                "revision",
            ):
                bad = copy.deepcopy(good)
                if kind == "revision":
                    bad["upstream_commit"] = "0" * 40
                if kind == "hash":
                    bad["inputs"][0]["sha256"] = "0" * 64
                if kind == "split":
                    bad["heldout"] = ["demo_0"]
                if kind == "candidates":
                    bad["candidates"] *= 9
                if kind == "mode":
                    bad["candidates"][0]["mode"] = "state-playback"
                if kind == "parameter":
                    bad["candidates"][0]["friction"] = 100
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    validate(bad)

    def test_foreign_or_modified_official_source_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            good = self.manifest(Path(temporary))
            for values in (["wrong"], [UPSTREAM, " M source.py"]):
                with (
                    patch(
                        "dexlab.libero_trials.subprocess.check_output",
                        side_effect=values,
                    ),
                    self.assertRaises(ValueError),
                ):
                    validate(good)


class LiberoBudgetTests(unittest.TestCase):
    def test_reservation_blocks_relaunch_and_counts_failure(self):
        from dexlab.libero_trials import create
        from dexlab.migration_budget import MigrationBudget

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = LiberoWorkflowTests().manifest(root)
            manifest["work_package"] = dict(
                id="test",
                hypothesis="fixture",
                max_starts=1,
                wall_s=100,
                evidence_sha256=["a" * 64],
            )
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                budget = create(root / "campaign", manifest)
            attempt = budget.reserve("baseline-demo_0", {"parent_pid": 0}, timeout_s=10)
            with self.assertRaises((RuntimeError, ValueError)):
                budget.reserve("baseline-demo_0", {"parent_pid": 0}, timeout_s=10)
            budget.finish(
                attempt, wall_s=1, evidence_sha256="b" * 64, outcome="interrupted"
            )
            with self.assertRaises((RuntimeError, ValueError)):
                budget.reserve(
                    "baseline-demo_0",
                    {"parent_pid": 0},
                    timeout_s=10,
                    retry_reason="Recovered",
                )
            self.assertEqual(
                MigrationBudget(root / "campaign").status()["starts_used"], 1
            )

    def test_interruption_recovery_preserves_reservation_and_allows_next_case(self):
        from dexlab.libero_trials import create, recover
        from dexlab.migration_budget import MigrationBudget

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = LiberoWorkflowTests().manifest(root)
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                budget = create(root / "campaign", manifest)
            budget.reserve(
                "baseline-demo_0",
                {
                    "parent_pid": 99999999,
                    "cgroup": "/dexlab-bounded-00000000000000000000000000000000.service",
                    "boot_id": Path("/proc/sys/kernel/random/boot_id")
                    .read_text()
                    .strip(),
                },
                timeout_s=5,
            )
            recover(root / "campaign")
            state = MigrationBudget(root / "campaign").status()
            self.assertEqual(state["starts_used"], 1)
            self.assertEqual(state["wall_charged_or_reserved_s"], 5)
            self.assertIsNotNone(state["attempts"][0]["terminal"])

    def test_heldout_rejects_changed_selection_evidence_before_launch(self):
        from dexlab.libero_trials import create, run
        from dexlab.migration_budget import MigrationBudget

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = LiberoWorkflowTests().manifest(root)
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                budget = create(root / "campaign", manifest)
            campaign = root / "campaign"
            evidence = campaign / "development.json"
            evidence.write_text("original")
            selection = dict(
                candidate="baseline",
                manifest_sha256=file_hash(campaign / "manifest.json"),
                sources={"development.json": file_hash(evidence)},
            )
            (campaign / "selection.json").write_text(json.dumps(selection))
            evidence.write_text("changed")
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                with self.assertRaisesRegex(ValueError, "Development evidence changed"):
                    run(campaign, "baseline", "demo_1")
            self.assertEqual(budget.status()["starts_used"], 0)
            evidence.write_text("original")
            attempt = budget.reserve(
                "baseline-demo_0",
                {"parent_pid": 0, "selection_sha256": "old"},
                timeout_s=5,
            )
            budget.finish(
                attempt, wall_s=1, evidence_sha256="a" * 64, outcome="recorded"
            )
            with patch(
                "dexlab.libero_trials.subprocess.check_output",
                side_effect=[UPSTREAM, ""],
            ):
                with self.assertRaisesRegex(ValueError, "selection changed"):
                    run(campaign, "baseline", "demo_1")
            self.assertEqual(MigrationBudget(campaign).status()["starts_used"], 1)


if __name__ == "__main__":
    unittest.main()
