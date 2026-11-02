"""Reference admission regressions; no native-physics claims."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

SPEC = importlib.util.spec_from_file_location(
    "chord_motion", Path(__file__).resolve().parents[1] / "demos/chord/motion.py")
motion = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motion)


def reference():
    data = SimpleNamespace(fps=30, object_body_names=["box"],
                           object_body_position=[[[0, 0, 0]], [[0, 0, 0.1]]],
                           object_body_wxyz=[[[1, 0, 0, 0]], [[1, 0, 0, 0]]])
    for side in ("left", "right"):
        setattr(data, f"{side}_robot_finger_joint_names", ["finger_a", "finger_b"])
        setattr(data, f"robot_{side}_finger_joints", [[0, 0], [0.1, 0.2]])
        setattr(data, f"robot_{side}_wrist_position", [[0, 0, 0], [0, 0, 0.1]])
        setattr(data, f"robot_{side}_wrist_wxyz", [[1, 0, 0, 0], [1, 0, 0, 0]])
    return data


class ChordMotionTests(unittest.TestCase):
    def test_span_uses_frame_intervals_not_frame_count(self):
        result = motion.validate(reference())
        self.assertEqual(result["frames"], 2)
        self.assertAlmostEqual(result["reference_span_s"], 1 / 30)

    def test_loaded_but_not_retargeted_partition_is_rejected(self):
        data = reference()
        data.robot_right_wrist_position = []
        with self.assertRaisesRegex(ValueError, "robot frames"):
            motion.validate(data)

    def test_bad_rotations_nonfinite_state_and_misaligned_joints_are_rejected(self):
        for field, value in (("object_body_wxyz", [[[2, 0, 0, 0]], [[1, 0, 0, 0]]]),
                             ("robot_left_wrist_position", [[0, 0, 0], [0, 0, float("nan")]]),
                             ("robot_right_finger_joints", [[0, 0]])):
            with self.subTest(field=field):
                data = reference()
                setattr(data, field, value)
                with self.assertRaises(ValueError):
                    motion.validate(data)

    def test_duplicate_joint_names_and_invalid_timing_are_rejected(self):
        for field, value in (("left_robot_finger_joint_names", ["same", "same"]),
                             ("fps", 0), ("fps", float("inf"))):
            with self.subTest(field=field, value=value):
                data = reference()
                setattr(data, field, value)
                with self.assertRaises(ValueError):
                    motion.validate(data)


if __name__ == "__main__":
    unittest.main()
