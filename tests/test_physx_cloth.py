"""Admission and observation boundaries that do not require an optional SDK."""

import unittest
from unittest.mock import Mock, patch

import numpy as np

from dexlab.cloth import ClothCase
from dexlab.physx_cloth import PhysXCloth


class PhysXClothBoundaryTest(unittest.TestCase):
    def test_force_driven_extension_rejected_before_worker_start(self):
        with patch("subprocess.Popen") as spawn:
            with self.assertRaisesRegex(NotImplementedError, "nodal-force"):
                PhysXCloth(ClothCase(), 0.0005, device="cuda:0", iterations=16)
            spawn.assert_not_called()

    def test_cpu_configuration_rejected_before_worker_start(self):
        with patch("subprocess.Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "cuda"):
                PhysXCloth(
                    ClothCase(experiment="sag"), 0.0005, device="cpu", iterations=16
                )
            spawn.assert_not_called()

    def test_nonzero_force_cannot_silently_advance(self):
        native = PhysXCloth.__new__(PhysXCloth)
        native._shape = (45, 3)
        native._request = Mock()
        for forces, error in [
            (np.ones((45, 3)), NotImplementedError),
            (np.full((45, 3), np.nan), ValueError),
            (np.zeros((44, 3)), ValueError),
        ]:
            with self.assertRaises(error):
                native.step(forces)
        native._request.assert_not_called()

    def test_observations_are_actual_worker_values_and_owned_copies(self):
        native = PhysXCloth.__new__(PhysXCloth)
        native._shape = (3, 3)
        positions = np.arange(9).reshape(3, 3).tolist()
        native._request = Mock(
            return_value={
                "positions": positions,
                "velocities": np.ones((3, 3)).tolist(),
            }
        )
        native.step(np.zeros((3, 3)))
        observed, velocity = native.observe()
        np.testing.assert_array_equal(observed, positions)
        np.testing.assert_array_equal(velocity, 1)
        observed[:] = -1
        np.testing.assert_array_equal(native.observe()[0], positions)
        native._request.return_value["positions"] = [[np.nan] * 3] * 3
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            native.step(np.zeros((3, 3)))


if __name__ == "__main__":
    unittest.main()
