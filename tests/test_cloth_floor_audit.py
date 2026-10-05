"""Floor contact must not disappear behind successful table-only diagnostics."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import mujoco
import numpy as np

from dexlab.cloth_floor_audit import audit_floor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from run_cloth import contact_measurements


class FloorAuditTests(unittest.TestCase):
    def model(self):
        return mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
          <geom name="floor" type="plane" size="1 1 .1"/>
          <flexcomp name="cloth" type="grid" count="2 2 1" spacing=".1 .1 .1"
            dim="2" pos="0 0 .1" radius=".0012"><edge equality="true"/>
          </flexcomp></worldbody></mujoco>''')

    def test_independent_plane_negative_and_clear_controls(self):
        model = self.model()
        points = np.zeros((2, 4, 3))
        points[0, :, 2] = .01
        points[1, :, 2] = -.0007
        with patch('mujoco.mj_step', side_effect=AssertionError('integration')), \
             patch('mujoco.mj_fwdPosition', side_effect=AssertionError('native collisions')):
            report = audit_floor(model, [0, 1], points)
            clear = audit_floor(model, [0, 1], points + [0, 0, .1])
        self.assertEqual(report['frames_with_intrusion'], 1)
        self.assertAlmostEqual(report['maximum_midsurface_depth_m'], .0007)
        self.assertAlmostEqual(report['maximum_radius_envelope_depth_m'], .0019)
        self.assertEqual(clear['status'], 'no_sampled_intrusion')

    def test_native_floor_contact_is_included_in_per_step_measurement(self):
        model = self.model()
        data = mujoco.MjData(model)
        data.qpos[2::3] = -.1007
        mujoco.mj_fwdPosition(model, data)
        forces, hand, table, self_depth, floor = contact_measurements(model, data)
        self.assertEqual(forces, {})
        self.assertEqual((hand, table, self_depth), (0, 0, 0))
        self.assertAlmostEqual(floor, .0019)

    def test_missing_geometry_and_incomplete_states_cannot_pass(self):
        empty = mujoco.MjModel.from_xml_string('<mujoco/>')
        self.assertEqual(audit_floor(empty, [], [])['status'], 'unsupported_geometry')
        self.assertEqual(audit_floor(self.model(), [], [])['status'], 'insufficient_evidence')
