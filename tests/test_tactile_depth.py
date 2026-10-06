import unittest
import numpy as np
from dexlab.tactile_depth import depth_map


class DepthTests(unittest.TestCase):
    def test_flat_contact_and_miss(self):
        image = depth_map([0, 0, 0.02], np.eye(3))
        self.assertEqual(np.count_nonzero(image), 16 * 16)
        np.testing.assert_allclose(image[8:24, 8:24], 0.001, atol=1e-12)
        self.assertFalse(depth_map([0, 0, 0.022], np.eye(3)).any())

    def test_partial_slab_and_inside_origin(self):
        image = depth_map([0, 0, 0.0206], np.eye(3))
        self.assertAlmostEqual(image[16, 16], 0.0004, places=12)
        self.assertAlmostEqual(depth_map([0, 0, 0], np.eye(3))[16, 16], 0.001)

    def test_translation_and_quarter_turn(self):
        image = depth_map([0.01, 0, 0.02], np.eye(3))
        np.testing.assert_allclose(image[8:24, 12:28], 0.001)
        rot = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
        np.testing.assert_allclose(
            depth_map([0, 0, 0.02], rot), depth_map([0, 0, 0.02], np.eye(3))
        )

    def test_histories_and_environment_isolation(self):
        reference = depth_map([0, 0, 0.02], np.eye(3))
        for center in ([0.02, 0, 0.02], [0, 0, 0.04], [0, 0, 0.02]):
            other = depth_map(center, np.eye(3), resolution=64)
            other[:] = -99
        np.testing.assert_array_equal(reference, depth_map([0, 0, 0.02], np.eye(3)))

    def test_tilted_box_center_ray(self):
        a = np.pi / 4
        rot = np.array(
            [[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]]
        )
        # Center line enters the diamond at center_z - sqrt(2)*half_size.
        z = np.sqrt(2) * 0.02 + 0.0007
        self.assertAlmostEqual(
            depth_map([0, 0, z], rot, resolution=1)[0, 0], 0.0003, places=12
        )

    def test_invalid_frame_rejected(self):
        for rot in (np.diag([1, 1, -1]), np.eye(3) * 2, np.full((3, 3), np.nan)):
            with self.assertRaises(ValueError):
                depth_map([0, 0, 0.02], rot)
        with self.assertRaises(ValueError):
            depth_map([0, 0, 0.02], np.eye(3), resolution=0)
