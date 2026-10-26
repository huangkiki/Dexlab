"""Initial self-collision must be checked even when the object has no contact."""

import importlib.util
from pathlib import Path
import unittest

import mujoco

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wuji_preflight", ROOT / "demos/wuji-contact/preflight.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class WujiContactPreflightTests(unittest.TestCase):
    def inspect(self, separation):
        model = mujoco.MjModel.from_xml_string(f'''<mujoco><worldbody>
          <body name="palm"><freejoint/><geom name="palm" type="sphere" size=".01" mass=".1"/></body>
          <body name="finger" pos="{separation} 0 0"><freejoint/><geom name="finger" type="sphere" size=".01" mass=".01"/></body>
          <body name="object" pos="1 0 0"><freejoint/><geom name="object" type="sphere" size=".01" mass=".02"/></body>
        </worldbody></mujoco>''')
        data = mujoco.MjData(model)
        report = CHECK.inspect_initial_state(model, data, .001)
        self.assertEqual(data.time, 0.)
        return report

    def test_hand_self_overlap_rejected_without_object_contact(self):
        report = self.inspect(.015)
        self.assertFalse(report["pass_initial_geometry"])
        self.assertEqual(len(report["excessive_penetration"]), 1)
        pair = report["excessive_penetration"][0]
        self.assertEqual({pair["geom1"], pair["geom2"]}, {"palm", "finger"})

    def test_separated_links_pass_without_integrating(self):
        self.assertTrue(self.inspect(.025)["pass_initial_geometry"])


if __name__ == "__main__":
    unittest.main()
