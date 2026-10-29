"""Offline render integrity checks, without importing GPU or physics runtimes."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np


PATH = Path(__file__).resolve().parents[1] / "demos/rss-wiping/render.py"
SPEC = importlib.util.spec_from_file_location("rss_replay_render", PATH)
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


class TestReplayIntegrity(unittest.TestCase):
    def test_exact_interval_has_no_duplicated_endpoint(self):
        np.testing.assert_array_equal(render.frame_steps(60, 10, 10, 20), np.arange(600, 1200, 6))
        for values in ((60, 7, 0, 1), (60, 10, 0.001, 1), (60, 10, 0, 1.01),
                       (60, 0, 0, 1), (60, 10, 1, 1), (60, 10, 0, float("inf"))):
            with self.subTest(values=values), self.assertRaises(ValueError):
                render.frame_steps(*values)

    def write_chunk(self, root, steps, *, nan=False):
        count = len(steps)
        particles = np.zeros((count, 2, 3))
        if nan:
            particles[0, 0, 0] = np.nan
        np.savez(root / "states/0000.npz", step=np.array(steps), particles=particles,
                 body_q=np.zeros((count, 1, 7)), joint_q=np.zeros((count, 1)),
                 stripe_ink=np.zeros((count, 3)))

    def test_frames_preserve_state_and_hash_the_consumed_chunk(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "states").mkdir()
            self.write_chunk(root, [0, 1, 2, 3])
            inputs = {}
            frames = list(render.read_frames(root, np.array([0, 2]), inputs))
            self.assertEqual([step for step, _ in frames], [0, 2])
            self.assertEqual(inputs["states/0000.npz"], render.sha256(root / "states/0000.npz"))
            render.check_state_shapes(frames[0][1], bodies=1, joints=1, particles=2, ink=3)
            with self.assertRaisesRegex(ValueError, "rebuilt scene"):
                render.check_state_shapes(frames[0][1], bodies=1, joints=1, particles=3, ink=3)

    def test_duplicate_missing_truncated_and_nonfinite_records_fail(self):
        for steps, nan in (([0, 1, 1], False), ([0, 2, 3], False),
                           ([0, 1], False), ([0, 1, 2], True)):
            with self.subTest(steps=steps, nan=nan), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "states").mkdir()
                self.write_chunk(root, steps, nan=nan)
                with self.assertRaises(ValueError):
                    list(render.read_frames(root, np.array([0, 2]), {}))

    def test_renderer_mutation_is_detected(self):
        before = {"particles": np.zeros((2, 3)), "shape_color": np.ones((2, 3))}
        after = {name: value.copy() for name, value in before.items()}
        render.assert_unchanged(before, after)
        after["particles"][1, 2] = 0.001
        with self.assertRaisesRegex(ValueError, "changed loaded state: particles"):
            render.assert_unchanged(before, after)

    def test_only_display_flags_can_be_restored_from_record(self):
        current = np.array([7, 7, 6], dtype=np.int32)
        recorded = np.array([6, 7, 7], dtype=np.int32)
        np.testing.assert_array_equal(render.restore_visibility(current, recorded, 1), recorded)
        with self.assertRaisesRegex(ValueError, "collision flags"):
            render.restore_visibility(current, np.array([4, 7, 7], dtype=np.int32), 1)


if __name__ == "__main__":
    unittest.main()
