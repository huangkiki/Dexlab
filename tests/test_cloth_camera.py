"""Keep falling cloth in the playback frustum, independent of the distant hand."""
from itertools import product
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from render_cloth import cloth_view


class ClothCameraTests(unittest.TestCase):
    def test_translation_to_floor_preserves_closeup_and_tracks_cloth(self):
        points = np.array(list(product((-.1, .1), repeat=3))) + [0, 0, .6]
        center, distance = cloth_view(points, 45)
        lower_center, lower_distance = cloth_view(points - [0, 0, .6], 45)
        np.testing.assert_allclose(center - lower_center, [0, 0, .6], atol=1e-15)
        self.assertAlmostEqual(distance, lower_distance)
        self.assertLess(distance, 1)

    def test_complete_cloth_fits_perspective_frustum_at_multiple_orbits(self):
        points = np.array(list(product((-.1, .1), (-.15, .15), (-.3, .1))))
        for fovy in (30, 45, 60):
            center, distance = cloth_view(points, fovy)
            for degrees in (0, 25, 60, 90):
                theta = np.deg2rad(degrees)
                outward = np.array([np.cos(theta), 0, np.sin(theta)])
                screen_up = np.array([-np.sin(theta), 0, np.cos(theta)])
                relative = points - (center + distance * outward)
                depth = relative @ -outward
                self.assertTrue(np.all(depth > 0))
                tangent = np.tan(np.deg2rad(fovy) / 2)
                self.assertTrue(np.all(np.abs(relative @ screen_up) < depth * tangent))
                self.assertTrue(np.all(np.abs(relative[:, 1]) < depth * tangent * 4 / 3))
