"""Frame selection and camera convention checks without GPU dependencies."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location('studio', Path(__file__).resolve().parents[1] / 'scripts/render_studio_replay.py')
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


class StudioReplayTests(unittest.TestCase):
    def test_complete_uniform_trajectory_is_not_interpolated(self):
        times = np.arange(280) * .05
        np.testing.assert_array_equal(studio.sample_indices(times, 20), np.arange(280))
        selected = studio.sample_indices(times, 10)
        self.assertEqual(selected[0], 0)
        self.assertEqual(selected[-1], 279)
        self.assertTrue(np.all(np.diff(selected) > 0))

    def test_irregular_timestamps_select_existing_nearest_states(self):
        times = np.array([.01, .08, .23, .31])
        np.testing.assert_array_equal(studio.sample_indices(times, 10), [0, 1, 2, 3])

    def test_invalid_timeline_rejected(self):
        for times in ([0], [0, 0], [1, 0], [0, np.nan], [0, np.inf], [[0, 1]]):
            with self.subTest(times=times), self.assertRaises(ValueError):
                studio.sample_indices(times, 20)
        for fps in (0, -1, np.inf, np.nan):
            with self.subTest(fps=fps), self.assertRaises(ValueError):
                studio.sample_indices([0, 1], fps)

    def test_usd_camera_looks_down_negative_z(self):
        matrix = studio.camera_matrix([1, 2, 3], [0, 1, 0], [0, 0, 1])
        np.testing.assert_allclose(matrix[3], [1, 2, 3, 1])
        np.testing.assert_allclose(matrix[:3, :3] @ matrix[:3, :3].T, np.eye(3))
        np.testing.assert_allclose(np.array([0, 0, -1]) @ matrix[:3, :3], [0, 1, 0])
        self.assertAlmostEqual(np.linalg.det(matrix[:3, :3]), 1.)


if __name__ == '__main__':
    unittest.main()
