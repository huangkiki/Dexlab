"""Protocol/control/compiled-model checks; no native physics stepping."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import numpy as np
from dexlab.pinch_run import commands, model_xml

P = json.loads((Path(__file__).resolve().parents[1]/'docs/evidence/pinch-load/manifest.json').read_text())


class PinchProtocolTests(unittest.TestCase):
    def test_commands_have_exact_epoch_and_equal_inward_force(self):
        for c in P['cases']:
            h = c['timestep']; onset = round(P['preload_s']/h)
            normal = c['capacity_ratio']*P['cube_mass_kg']*P['gravity_m_s2']/(2*P['friction'])
            np.testing.assert_array_equal(commands(P,c,0)[0], [0,0])
            np.testing.assert_allclose(commands(P,c,round(P['ramp_s']/h))[0], [normal,normal])
            np.testing.assert_array_equal(commands(P,c,onset-1)[1], [0,0,0])
            np.testing.assert_array_equal(commands(P,c,onset)[1], [0,0,-P['cube_mass_kg']*P['gravity_m_s2']])

    def test_only_cube_free_and_jaws_inward(self):
        root = ET.fromstring(model_xml(P,P['cases'][0]))
        self.assertEqual(len(root.findall('.//freejoint')),1)
        axes = [j.attrib['axis'] for j in root.findall('.//joint')]
        self.assertEqual(axes,['1 0 0','-1 0 0'])
        self.assertEqual(len(root.findall('.//geom[@type="box"]')),3)
        self.assertFalse(root.findall('.//geom[@type="plane"]'))

    def test_all_native_models_compile_with_no_hidden_damping(self):
        import mujoco as mj
        for c in P['cases']:
            m = mj.MjModel.from_xml_string(model_xml(P,c))
            self.assertEqual((m.nq,m.nv,m.nu),(9,8,2))
            np.testing.assert_array_equal(m.dof_damping,0)
            np.testing.assert_array_equal(m.dof_frictionloss,0)
            np.testing.assert_array_equal(m.dof_armature,0)
            np.testing.assert_array_equal(m.opt.gravity,0)
            np.testing.assert_allclose(m.body_mass[1:],[.1,.1,.064])
            self.assertEqual(m.opt.timestep,c['timestep'])
            np.testing.assert_array_equal(m.actuator_gear[:,0],1)


if __name__ == '__main__':
    unittest.main()
