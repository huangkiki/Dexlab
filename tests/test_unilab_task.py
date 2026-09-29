"""Lifecycle and control-boundary tests; full native episodes are checked separately."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from unilab.base import registry

from dexlab.episode import GraspFrame
from dexlab.tasks.apple_stem import TASK, AppleStemCfg, AppleStemEnv


class UniLabTaskTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.received = []
        self.cleaned = 0

        def episode(args):
            Path(args.output).mkdir(parents=True, exist_ok=True)
            try:
                target = np.array([0.4, -0.3])
                action = yield GraspFrame(
                    0, ("a", "b"), np.zeros(2), np.array([0, 0, 0, 0, 0, 0, 1]), target
                )
                self.received.append(action.copy())
                yield GraspFrame(
                    0.002,
                    ("a", "b"),
                    action / 2,
                    np.array([0, 0, 0, 0, 0, 0, 1]),
                    target,
                    {"passed": True},
                )
            finally:
                self.cleaned += 1

        self.patch = patch("wuji_stem_grasp.episode", episode)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.env = AppleStemEnv(
            AppleStemCfg(output=self.tmp.name), backend_type="superdex"
        )
        self.addCleanup(self.env.close)

    def test_registry_and_actual_state_not_target(self):
        made = registry.make(TASK, sim_backend="mujoco")
        self.assertIsInstance(made, AppleStemEnv)
        self.assertEqual(made.cfg.sim_dt, 0.0005)
        state = self.env.init_state()
        np.testing.assert_array_equal(state.obs["obs"][0, :2], [0, 0])
        np.testing.assert_array_equal(state.info["scripted_target"], [[0.4, -0.3]])

    def test_action_reaches_engine_and_terminal_state_releases_scene(self):
        self.env.reset()
        state = self.env.step([[0.1, 0.2]])
        np.testing.assert_array_equal(self.received, [[0.1, 0.2]])
        np.testing.assert_array_equal(state.obs["obs"][0, :2], [0.05, 0.1])
        self.assertTrue(state.terminated[0])
        self.assertEqual(self.cleaned, 1)
        with self.assertRaises(RuntimeError):
            self.env.step([[0.1, 0.2]])

    def test_invalid_actions_do_not_advance(self):
        self.env.reset()
        for action in ([1, 2], [[np.nan, 0]], [[1, 2, 3]]):
            with self.assertRaises(ValueError):
                self.env.step(action)
        self.assertFalse(self.received)
        self.assertEqual(self.env.state.info["steps"][0], 0)

    def test_reset_and_early_close_release_live_scene(self):
        self.env.reset()
        self.env.reset()
        self.assertEqual(self.cleaned, 1)
        self.env.close()
        self.env.close()
        self.assertEqual(self.cleaned, 2)

    def test_reject_unsupported_configuration(self):
        with self.assertRaises(ValueError):
            AppleStemEnv(AppleStemCfg(), num_envs=2)
        with self.assertRaises(ValueError):
            AppleStemEnv(AppleStemCfg(max_episode_seconds=2))
        with self.assertRaises(ValueError):
            AppleStemEnv(AppleStemCfg(parameters={"fake": 1}))

    def test_timestep_override_cannot_be_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "timestep overrides"):
            AppleStemEnv(AppleStemCfg(sim_dt=0.001, ctrl_dt=0.001))

    def test_explicit_benchmark_step_is_recorded(self):
        env = AppleStemEnv(
            AppleStemCfg(output=self.tmp.name, parameters={"timestep": 0.001})
        )
        self.addCleanup(env.close)
        self.assertEqual(env.cfg.sim_dt, 0.001)
        env.reset()
        import json

        manifest = json.loads((Path(self.tmp.name) / "unilab.json").read_text())
        self.assertEqual(manifest["parameters"]["timestep"], 0.001)
        self.assertEqual(manifest["dt_s"], 0.001)

    def test_zero_benchmark_timestep_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported benchmark timestep"):
            AppleStemEnv(AppleStemCfg(parameters={"timestep": 0.0}))

    def test_native_failure_releases_scene(self):
        def failing(args):
            Path(args.output).mkdir(parents=True, exist_ok=True)
            yield GraspFrame(
                0, ("a",), np.zeros(1), np.array([0, 0, 0, 0, 0, 0, 1]), np.zeros(1)
            )
            raise RuntimeError("native failure")

        with patch("wuji_stem_grasp.episode", failing):
            self.env.reset()
            with self.assertRaisesRegex(RuntimeError, "native failure"):
                self.env.step([[0]])
        self.assertIsNone(self.env.state)
        self.env.reset()  # failure must not leave the process-global lock held

    def test_only_one_live_native_scene(self):
        self.env.reset()
        second = AppleStemEnv(AppleStemCfg(output=self.tmp.name))
        self.addCleanup(second.close)
        with self.assertRaises(RuntimeError):
            second.reset()
        self.assertEqual(self.cleaned, 0)
        self.env.close()
        second.reset()


if __name__ == "__main__":
    unittest.main()
