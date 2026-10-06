"""Synthetic scoring fixtures never stand in for actual gripper experiments."""

import unittest
from dexlab.genesis_cloth_gripper_score import episode_metrics


def rows():
    result = []
    for step in range(2001):
        height = 0.084 if 1100 <= step <= 1550 else 0.004
        q = [0.08 if step else 0, 0.026, 0.026] if step else [0, 0.0255, 0.0255]
        result.append(
            {
                "step": step,
                "pos": [[0, -0.01, height], [0, 0, height], [0, 0.01, height]],
                "vel": [[0, 0, 0]] * 3,
                "q": q,
                "qvel": [0, 0, 0],
                "actuator_force": [0, 0, 0],
                "pad_pos": [[-0.04, 0, 0.025], [0.04, 0, 0.025]],
                "pad_quat": [[1, 0, 0, 0]] * 2,
            }
        )
    return result


class GripperScoreTests(unittest.TestCase):
    def test_hold_and_release(self):
        result, _ = episode_metrics(rows(), [0.00032 / 3] * 3)
        self.assertTrue(result["held"])
        self.assertTrue(result["released"])

    def test_command_cannot_replace_actual_lift(self):
        data = rows()
        for r in data[1:]:
            r["q"][0] = 0
        result, _ = episode_metrics(data, [0.00032 / 3] * 3)
        self.assertFalse(result["held"])

    def test_cloth_on_floor_not_grasp(self):
        data = rows()
        for r in data:
            for p in r["pos"]:
                p[2] = 0.004
        self.assertFalse(episode_metrics(data, [0.00032 / 3] * 3)[0]["held"])

    def test_release_requires_cloth_drop(self):
        data = rows()
        for p in data[-1]["pos"]:
            p[2] = 0.1
        self.assertFalse(episode_metrics(data, [0.00032 / 3] * 3)[0]["released"])

    def test_missing_frame_rejected(self):
        with self.assertRaises(ValueError):
            episode_metrics(rows()[:-1], [0.00032 / 3] * 3)
