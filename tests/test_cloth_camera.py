"""Keep falling cloth in the playback frustum, independent of the distant hand."""
from itertools import product
from pathlib import Path
import sys
import unittest

import numpy as np

from dexlab.cloth_display import fixed_view

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from render_cloth import cloth_view


class ClothCameraTests(unittest.TestCase):
    def test_fixed_camera_keeps_complete_motion_below_caption_margin(self):
        points = np.array(list(product((-.4, .2), (-.06, .08), (.01, .7))))
        for azimuth, elevation, aspect in ((15, -20, 4 / 3), (90, -25, 2 / 3)):
            center, distance = fixed_view(points, azimuth, elevation, aspect=aspect)
            az, altitude = np.deg2rad([azimuth, -elevation])
            right = np.array([-np.sin(az), np.cos(az), 0])
            outward = np.array([np.cos(altitude) * np.cos(az),
                                np.cos(altitude) * np.sin(az), np.sin(altitude)])
            up = np.cross(outward, right)
            relative = points - center - distance * outward
            depth = -relative @ outward
            self.assertTrue(np.all(depth > 0))
            tangent = np.tan(np.deg2rad(45 / 2))
            self.assertTrue(np.all(np.abs(relative @ up) < .75 * depth * tangent))
            self.assertTrue(np.all(np.abs(relative @ right) < .85 * depth * tangent * aspect))

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
