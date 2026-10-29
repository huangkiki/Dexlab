"""A negative control must not hide an initial-state or mass change."""

import json
from pathlib import Path
import runpy
import tempfile
import unittest

import numpy as np

from dexlab.libero_substeps import write_chunk


PAIR = runpy.run_path(str(Path(__file__).resolve().parents[1] / "demos/amp-box-lift/pair.py"))["compare_pair"]


class AmpPairTests(unittest.TestCase):
    def test_only_hand_masks_may_change_and_mass_mismatch_is_rejected(self):
        cases = [{"id": name, "actions": 1} for name in ("policy-seed-137", "no-hand-seed-137")]
        protocol = {"cases": cases, "checks": {"state_parity_atol": 1e-5, "state_parity_rtol": 0.}}
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / case["id"] for case in cases]
            for index, (path, case) in enumerate(zip(paths, cases)):
                (path / "native").mkdir(parents=True)
                manifest = {"status": "completed", "case": case, "completed_actions": 1,
                    **{key: "fixture" for key in ("source", "runtime", "native_payload", "runner_sha256",
                                                   "recorder_sha256", "protocol_sha256")}}
                (path / "invocation.json").write_text(json.dumps(manifest))
                metadata = {"geom_names": [f"robot/{side}_{part}_collision"
                    for side in ("left", "right") for part in ("hand", "wrist")],
                    **{key: [] for key in ("body_names", "joint_names", "site_names", "actuator_names")},
                    "options": {}, "time_dtype": "float32", "force_decoder_sha256": "fixture"}
                (path / "native/recording.json").write_text(json.dumps(metadata))
                write_chunk(path / "initial-state.npz", [{"qpos": np.array([.2]), "qvel": np.array([0.])}])
                model = {"body_mass": np.array([[1.3]]), "geom_contype": np.full(4, 1 - index),
                         "geom_conaffinity": np.full(4, 1 - index),
                         "pair_geom1": np.array([], dtype=int), "pair_geom2": np.array([], dtype=int),
                         "nxn_geom_pair": np.zeros((index, 2), dtype=int),
                         "nxn_pairid": np.zeros((index, 2), dtype=int)}
                np.savez(path / "native/effective-model.npz", **model)
            self.assertTrue(PAIR(*paths, protocol)["passed"])
            model["body_mass"][0, 0] = 1.5
            np.savez(paths[1] / "native/effective-model.npz", **model)
            with self.assertRaisesRegex(ValueError, "paired model.body_mass"):
                PAIR(*paths, protocol)


if __name__ == "__main__":
    unittest.main()
