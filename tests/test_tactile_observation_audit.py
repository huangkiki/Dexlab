import unittest
import numpy as np
from dexlab.tactile_depth import depth_map
from dexlab.tactile_observation_audit import audit_observations, rotation


class ObservationAuditTests(unittest.TestCase):
    def fixture(self):
        p = np.array([0.031, 0, 0.0205, 1, 0, 0, 0])
        return {
            "pose": np.tile(p, (6001, 1)),
            "maps": np.tile(depth_map(p[:3], np.eye(3))[None], (150, 1, 1)),
        }

    def test_clipped_analytic_volume_and_isolation(self):
        a = audit_observations(self.fixture(), 32)
        self.assertTrue(a["passed"])
        self.assertAlmostEqual(
            a["axis_aligned_volume_references"][0]["reference_m3"],
            0.029 * 0.04 * 0.0005,
            places=15,
        )

    def test_corrupted_map_rejected(self):
        a = self.fixture()
        a["maps"][12, 10, 12] += 0.0001
        self.assertFalse(audit_observations(a, 32)["passed"])
        a["maps"][12, 10, 12] = np.nan
        self.assertFalse(audit_observations(a, 32)["passed"])

    def test_quarter_turn(self):
        r = rotation([2**-0.5, 0, 0, 2**-0.5])
        np.testing.assert_allclose(r @ [1, 0, 0], [0, 1, 0], atol=1e-12)
