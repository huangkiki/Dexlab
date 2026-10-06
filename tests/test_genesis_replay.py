import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("replay", Path(__file__).resolve().parents[1] / "scripts/render_genesis_pinch.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class ReplayCoverageTest(unittest.TestCase):
    def test_full_episode_and_no_time_reversal(self):
        rows = [{"time": (i + 1) * .0005} for i in range(8000)]
        indices = replay.frame_indices(rows)
        self.assertEqual((indices[0], indices[-1]), (0, 7999))
        self.assertTrue((replay.np.diff(indices) > 0).all())
        self.assertEqual(len(indices), 121)

    def test_missing_or_nonfinite_steps_are_rejected(self):
        for times in ([.001, .003], [.001, float("nan")], [.002, .001]):
            with self.assertRaises(ValueError):
                replay.frame_indices([{"time": t} for t in times])
