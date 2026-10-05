"""Explicit compliance changes preserve geometry and select the native pair response."""
from pathlib import Path
import sys
import tempfile
import unittest

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from cloth_model import build_model


class ClothComplianceTests(unittest.TestCase):
    def test_floor_override_reaches_native_pair_without_changing_material_or_geometry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            robot = root / 'robot.xml'
            robot.write_text('<mujoco><compiler/><option/><default><geom/></default>'
                             '<asset/><worldbody/><actuator/></mujoco>')
            original, *_ = build_model(robot, root/'original')
            changed, *_ = build_model(robot, root/'changed', floor_time_constant=.0005,
                                      edge_time_constant=.0005)
            for field in ('body_mass', 'body_pos', 'flex_elem', 'flexedge_length0',
                          'flex_radius', 'geom_size', 'geom_pos', 'geom_friction'):
                np.testing.assert_array_equal(getattr(original, field), getattr(changed, field))
            np.testing.assert_allclose(original.eq_solref[:, 0], .002)
            np.testing.assert_allclose(changed.eq_solref[:, 0], .0005)
            data = mujoco.MjData(changed)
            data.qpos[2::3] = -.503
            mujoco.mj_fwdPosition(changed, data)
            floor = changed.geom('floor').id
            contacts = [c for c in data.contact if floor in c.geom and np.any(c.flex >= 0)]
            self.assertTrue(contacts)
            for contact in contacts:
                self.assertAlmostEqual(contact.solref[0], .0005)
