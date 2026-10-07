import math
import unittest
from dexlab.genesis_pinch_score import score_trial, table_depth


class PinchEvidenceTests(unittest.TestCase):
    def test_rotated_box_support_is_not_center_minus_fixed_half_height(self):
        q = [math.cos(math.pi/8), math.sin(math.pi/8), 0, 0]
        self.assertAlmostEqual(table_depth([0, 0, .02], q), .02*(math.sqrt(2)-1))

    def test_missing_physics_samples_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            score_trial({'samples': []}, .001)

    def test_invalid_body_map_rejected(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            score_trial({'condition': 'pinch', 'samples': [{}]*4000, 'initial': {
                'cube_link': 5, 'pad_links': [5, 4], 'plane_link': 0}}, .001)
