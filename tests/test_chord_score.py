"""Offline scoring must retain pre-reset failures and reject changed trajectories."""

import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1] / "demos/chord"
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("chord_score", HERE / "score.py")
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)
sys.path.pop(0)


class ChordScoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.baseline, self.recorded = root / "off", root / "on"
        invocation = {"status": "completed", "task": "tissue-box", "seed": 24,
                      "checkpoint_sha256": "fixed", "source": {}, "manifest_sha256": "fixed",
                      "adapter_sha256": {}, "packages": {}, "assistance": {"voc": 0},
                      "motion": {}, "runtime": {}, "native_identity": {}, "native_physics_scenes": {},
                      "steps_requested": 1, "steps_completed": 1,
                      "timing": {"physics_dt_s": .01, "control_dt_s": .01, "resampled_frames": 2}}
        for directory, enabled in ((self.baseline, False), (self.recorded, True)):
            directory.mkdir()
            (directory / "invocation.json").write_text(json.dumps({**invocation, "recorder": enabled}))
            # This is the state returned after a failed episode was reset.
            (directory / "trajectory.jsonl").write_text(json.dumps({"step": 0, "object": [0, 0, 0]}) + "\n")
        self.events = [
            {"epoch": "pre_step", "control_step": 0, "reference_index": [0],
             "reference_object_position_e": [[[0, 0, 0]]], "reference_object_wxyz_e": [[[1, 0, 0, 0]]]},
            {"epoch": "applied_virtual_control_after_physics", "control_step": 0,
             "virtual_control_body_frame_N_Nm": {"object": [[0] * 6]}},
            {"epoch": "post_step_before_reset", "control_step": 0, "reference_index": [0],
             "object_position_e": [[[0, 0, -.1]]], "object_wxyz_e": [[[-1, 0, 0, 0]]],
             "terminated": [True], "time_out": [False], "voc_scale": [[0]], "reward": [1e9]},
        ]
        self.write_events()

    def write_events(self):
        (self.recorded / "native.jsonl").write_text("".join(json.dumps(r) + "\n" for r in self.events))

    def test_failure_is_scored_before_reset_and_without_reward(self):
        result = score.tracking(self.recorded, self.baseline)
        self.assertAlmostEqual(result["position_rmse_m"], .1)
        self.assertAlmostEqual(result["orientation_rmse_rad"], 0)
        self.assertAlmostEqual(result["vertical_error_min_m"], -.1)
        self.assertEqual(result["native_terminations"], 1)
        self.assertFalse(result["reward_used_for_score"])

    def test_changed_returned_trajectory_fails_frozen_parity_tolerance(self):
        (self.recorded / "trajectory.jsonl").write_text(json.dumps({"step": 0, "object": [0, 0, 2e-6]}) + "\n")
        self.assertFalse(score.parity(self.baseline, self.recorded)["passed"])
        with self.assertRaisesRegex(ValueError, "matching successful parity"):
            score.tracking(self.recorded, self.baseline)

    def test_missing_substeps_and_nonzero_assistance_fail_closed(self):
        self.events[1]["virtual_control_body_frame_N_Nm"]["object"][0][2] = .001
        self.write_events()
        with self.assertRaisesRegex(ValueError, "VOC applied-command"):
            score.tracking(self.recorded, self.baseline)
        del self.events[1]
        self.write_events()
        with self.assertRaisesRegex(ValueError, "substep record is incomplete"):
            score.tracking(self.recorded, self.baseline)

    def test_changed_motion_cannot_borrow_an_identical_trajectory(self):
        path = self.recorded / "invocation.json"
        invocation = json.loads(path.read_text())
        invocation["motion"] = {"sha256": "different-reference"}
        path.write_text(json.dumps(invocation))
        with self.assertRaisesRegex(ValueError, "invocation differs: motion"):
            score.parity(self.baseline, self.recorded)

    def test_cli_failure_status_matches_failed_parity(self):
        (self.recorded / "trajectory.jsonl").write_text(json.dumps({"step": 0, "object": [1, 0, 0]}) + "\n")
        result = subprocess.run([sys.executable, str(HERE / "score.py"), "parity",
                                 str(self.baseline), str(self.recorded)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(json.loads(result.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
