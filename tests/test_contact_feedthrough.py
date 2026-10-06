import gzip
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import test_contact_tangent as tangent_tests

from dexlab.contact_feedthrough import PROFILES, score, verify
from dexlab.contact_tangent import fit_response
from dexlab.physx_baseline import digest


class FeedthroughTests(unittest.TestCase):
    def test_separates_applied_load_from_material_coefficients(self):
        rng = np.random.default_rng(173)
        depth, speed, load = rng.normal(size=(3, 800))
        force = 0.7 + 20000 * depth + 40 * speed + 0.3 * load
        result = fit_response(depth, speed, force, applied_load=load)
        for name, expected in (
            ("stiffness_n_m", 20000),
            ("damping_ns_m", 40),
            ("load_gain", 0.3),
            ("intercept_n", 0.7),
        ):
            self.assertAlmostEqual(result[name], expected, places=8)

    def test_rank_and_nonfinite_load_fail_closed(self):
        x = np.linspace(0, 1, 100)
        for load in (x, np.full(100, np.nan), np.ones(100)):
            with self.assertRaises(ValueError):
                fit_response(x, np.sin(50 * x), x, applied_load=load)

    def test_good_regression_cannot_override_invalid_settling(self):
        data = tangent_tests.TangentIdentificationTests.synthetic_data()
        data["velocity"][650, 2] += 0.01
        result = score(4.0, 0.0005, data)
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["settled_speed"])
        self.assertTrue(result["models"]["post-basic"]["prediction_ok"])
        self.assertFalse(result["models"]["post-basic"]["data_valid"])

    def test_known_zero_feedthrough_and_epoch_are_distinguished(self):
        result = score(
            4.0, 0.0005, tangent_tests.TangentIdentificationTests.synthetic_data()
        )
        self.assertTrue(result["valid"])
        post = result["models"]["post-load"]["fit"]
        self.assertAlmostEqual(post["load_gain"], 0.0, places=7)
        self.assertAlmostEqual(post["damping_ns_m"], 40.0, places=7)
        self.assertTrue(result["models"]["post-load"]["prediction_ok"])
        self.assertNotAlmostEqual(
            result["models"]["pre-load"]["fit"]["damping_ns_m"], 40.0, places=2
        )

    def test_missing_data_and_coherent_adhesion_fail(self):
        self.assertFalse(score(4.0, 0.0005, {})["valid"])
        data = tangent_tests.TangentIdentificationTests.synthetic_data()
        data["force"][1000, 2] = data["ledger"][1000, 2] = -1.0
        result = score(4.0, 0.0005, data)
        self.assertFalse(result["checks"]["momentum"])
        self.assertFalse(result["valid"])

    def test_raw_archive_parameter_and_warning_tampering(self):
        data = tangent_tests.TangentIdentificationTests.synthetic_data()
        normal = PROFILES["low"]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            np.savez(root / "states.npz", **data)
            (root / "native.json").write_text(
                json.dumps(
                    {
                        "normal_parameters_readback": normal,
                        "mass_readback": 0.2,
                        "solver": {
                            "integrator": 0,
                            "algorithm": 2,
                            "cone": 1,
                            "iterations": 100,
                            "tolerance": 1e-10,
                            "impratio": 1.0,
                            "disableflags": 0,
                            "enableflags": 0,
                        },
                        "geometry_readback": {
                            "type": [0, 6],
                            "size": [[2.0, 2.0, 0.1], [0.02, 0.02, 0.02]],
                        },
                        "friction_readback": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                        "inertia_readback": [0.2 * 0.04**2 / 6] * 3,
                    }
                )
            )
            (root / "model.xml").write_text("<mujoco/>")
            rows = [
                {
                    "warnings": [0],
                    "contacts": [
                        {"force_on_box": (f / 4).tolist(), "parameters": normal}
                        for _ in range(4)
                    ],
                }
                for f in data["force"]
            ]

            def save():
                with gzip.open(root / "contacts.jsonl.gz", "wt") as stream:
                    for row in rows:
                        stream.write(json.dumps(row) + "\n")
                (root / "receipt.json").write_text(
                    json.dumps(
                        {
                            "load_n": 4.0,
                            "timestep_s": 0.0005,
                            "normal": normal,
                            "hashes": {
                                name: digest(root / name)
                                for name in (
                                    "states.npz",
                                    "contacts.jsonl.gz",
                                    "native.json",
                                    "model.xml",
                                )
                            },
                        }
                    )
                )

            save()
            self.assertTrue(verify(root)["valid"])
            (root / "score.json").write_text('{"valid":false}')
            self.assertTrue(verify(root)["valid"])  # Does not trust saved verdicts.
            rows[1000]["warnings"] = [1]
            save()
            with self.assertRaisesRegex(ValueError, "disagree"):
                verify(root)
            rows[1000]["warnings"] = [0]
            rows[1000]["contacts"][0]["parameters"] = PROFILES["high"]
            save()
            with self.assertRaisesRegex(ValueError, "pair parameters"):
                verify(root)
            (root / "model.xml").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "hashes"):
                verify(root)
