"""Prevent visually plausible comparisons of different experiments or records."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "demos/cloth-benchmark/src/render.py"
SPEC = importlib.util.spec_from_file_location("cloth_comparison_render", SCRIPT)
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


class ClothComparisonTests(unittest.TestCase):
    def setUp(self):
        rest = np.array([[0., 0., .1], [.1, 0., .1], [0., .1, .1]])
        self.record = {
            "metadata": {"solver": "mujoco", "dt_s": .04,
                         "case": {"name": "sag", "duration": .08}},
            "time": np.array([0., .04, .08]),
            "rest_positions": rest,
            "positions": np.repeat(rest[None], 3, axis=0),
            "triangles": np.array([[0, 1, 2]]),
        }
        self.other = copy.deepcopy(self.record)
        self.other["metadata"]["solver"] = "newton-vbd"

    def test_rejects_different_loading_or_boundary_case(self):
        self.other["metadata"]["case"]["force"] = .01
        with self.assertRaisesRegex(ValueError, "case inputs"):
            render.check_comparison([self.record, self.other])

    def test_rejects_time_shift_and_changed_topology(self):
        self.other["time"] += .001
        with self.assertRaisesRegex(ValueError, "timestamps"):
            render.check_comparison([self.record, self.other])
        self.other["time"] = self.record["time"]
        self.other["triangles"] = np.array([[0, 2, 1]])
        with self.assertRaisesRegex(ValueError, "triangles"):
            render.check_comparison([self.record, self.other])

    def test_actual_solver_motion_may_differ(self):
        self.other["positions"][1:, :, 2] -= .05
        render.check_comparison([self.record, self.other])
        self.other["positions"][0, :, 2] -= .001
        with self.assertRaisesRegex(ValueError, "initial positions"):
            render.check_comparison([self.record, self.other])

    def test_record_digest_and_complete_episode_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            np.savez(root / "trajectory.npz", **{
                key: self.record[key] for key in
                ("time", "positions", "rest_positions", "triangles")
            })
            metadata = {**self.record["metadata"],
                        "trajectory_sha256": render.sha256(root / "trajectory.npz")}
            (root / "run.json").write_text(json.dumps(metadata))
            (root / "summary.json").write_text("{}")
            render.load_record(root)
            with self.assertRaisesRegex(ValueError, "outside"):
                render.render(root, output=root / "media")
            self.assertFalse((root / "media").exists())
            metadata["dt_s"] = .02
            (root / "run.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "time grid"):
                render.load_record(root)
            metadata["dt_s"] = .04
            metadata["case"]["duration"] = .12
            (root / "run.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "complete"):
                render.load_record(root)
            (root / "trajectory.npz").write_bytes(b"replaced")
            with self.assertRaisesRegex(ValueError, "digest"):
                render.load_record(root)


if __name__ == "__main__":
    unittest.main()
