"""Native force response and adversarial independent scoring."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from dexlab.contact_indent_run import run, verify
from dexlab.contact_load import LoadCase, score
from dexlab.contact_parameters import normal_parameters


class NormalResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / "run"
        cls.case = LoadCase()
        cls.profile = {"solref": [-2500, -100], "solimp": [0.9, 0.9, 0.001, 0.5, 2]}
        cls.result = run(cls.case, "mujoco", cls.path, normal_parameters=cls.profile)
        with np.load(cls.path / "states.npz", allow_pickle=False) as saved:
            cls.data = dict(saved)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def copy_data(self):
        return {k: v.copy() for k, v in self.data.items()}

    def test_native_loading_matches_target_and_offline_score(self):
        self.assertTrue(self.result["passed"], self.result)
        self.assertEqual(self.result, verify(self.path))
        self.assertAlmostEqual(
            self.result["metrics"]["fit_secant_stiffness_n_m"], 20000, delta=50
        )

    def test_feedback_free_commands_and_fixed_duration(self):
        a = self.case.command(100, np.zeros(7), np.zeros(6), np.zeros(3))
        b = self.case.command(100, np.ones(7), np.ones(6), np.ones(3))
        np.testing.assert_array_equal(a, b)
        with self.assertRaises(ValueError):
            replace(self.case, duration=1.6)
        with self.assertRaises(ValueError):
            replace(self.case, timestep=0.003)

    def test_corrupt_command_or_missing_contact_is_not_a_success(self):
        data = self.copy_data()
        data["external_force"][10, 2] += 1
        result = score(self.case, data)
        self.assertFalse(result["checks"]["declared_force_commands"])
        self.assertFalse(result["checks"]["momentum_balance"])
        data = self.copy_data()
        data["contact_known"][10] = False
        self.assertFalse(score(self.case, data)["passed"])

    def test_stable_but_wrong_material_response_fails(self):
        data = self.copy_data()
        data["pose"][1:1201, 2] = self.case.half_size - 0.5 * (
            self.case.half_size - data["pose"][1:1201, 2]
        )
        result = score(self.case, data)
        self.assertTrue(result["checks"]["loaded_force_balance"])
        self.assertFalse(result["checks"]["fitting_load_response"])
        self.assertFalse(result["checks"]["intermediate_load_validation"])

    def test_force_release_and_jitter_are_scored(self):
        data = self.copy_data()
        data["contact_force"][-100:, 2] = 1
        self.assertFalse(score(self.case, data)["checks"]["fully_unloaded"])
        data = self.copy_data()
        data["pose"][302:401:2, 2] += 3e-5
        self.assertFalse(score(self.case, data)["checks"]["settled_plateaus"])

    def test_profile_readback_is_required_even_if_response_passes(self):
        path = self.path / "run.json"
        original = path.read_bytes()
        try:
            receipt = json.loads(original)
            receipt["native"]["normal_parameters_readback"]["solref"][0] *= 2
            path.write_text(json.dumps(receipt))
            result = verify(self.path)
            self.assertTrue(result["checks"]["fitting_load_response"])
            self.assertFalse(result["checks"]["normal_parameters_match"])
        finally:
            path.write_bytes(original)

    def test_unknown_or_invalid_native_profiles_fail_closed(self):
        bad = [
            ("physx", {"compliant_contact_stiffness": 5000}),
            (
                "physx",
                {"compliant_contact_stiffness": 0, "compliant_contact_damping": 1},
            ),
            ("mujoco", {"solref": [-1, 1]}),
            ("mujoco", {"solimp": [1, 1, 0.001, 0.5, 2]}),
            ("superdex", {"penalty_coefficient": float("nan")}),
            ("superdex", {"penalty_coefficient": True}),
            ("superdex", {"friction": 0.5}),
        ]
        for engine, profile in bad:
            with (
                self.subTest(engine=engine, profile=profile),
                self.assertRaises(ValueError),
            ):
                normal_parameters(engine, profile)


if __name__ == "__main__":
    unittest.main()
