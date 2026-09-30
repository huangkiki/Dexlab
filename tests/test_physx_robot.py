"""Adversarial checks for robot frame reduction and measured-state scoring."""

import copy
import unittest
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from dexlab.physx_robot import (
    DT,
    DURATION,
    excitation,
    score,
    target_at,
)
from dexlab.robot_transfer import (
    collapse_massless_frames,
    compare_reduction,
    implicit_body_exclusions,
    move_into_parent,
    preserve_implicit_filters,
)


def fixture():
    return mujoco.MjModel.from_xml_string("""<mujoco><worldbody>
    <body name="base"><inertial mass="1" pos="0 0 0" diaginertia="1 1 1"/>
      <body name="arm" pos="0 0 1"><joint name="arm_q" range="-90 90"/>
        <inertial mass="1" pos=".1 0 0" diaginertia=".01 .02 .02"/>
        <body name="finger" pos=".2 0 0"><joint name="finger_q" range="-90 90"/>
          <inertial mass=".1" pos=".1 0 0" diaginertia=".001 .002 .002"/>
        </body>
      </body>
    </body></worldbody><actuator><position joint="arm_q"/><position joint="finger_q"/></actuator>
    <keyframe><key name="home" qpos="0 1.5707963267948966"/></keyframe></mujoco>""")


def kinematic_record(model):
    home = model.key_qpos[0]
    amplitude = excitation(home, model.jnt_range)
    target = np.array(
        [target_at(i * DT, home, amplitude) for i in range(round(DURATION / DT))]
    )
    data = mujoco.MjData(model)
    positions, rotations = [], []
    for q in target:
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        positions.append(data.xpos[1:].copy())
        rotations.append(data.xquat[1:].copy())
    return {
        "time": np.arange(1, len(target) + 1) * DT,
        "q": target.copy(),
        "target": target,
        "dq": np.gradient(target, DT, axis=0),
        "position": np.asarray(positions),
        "quaternion": np.asarray(rotations),
    }


class RobotQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = fixture()
        cls.record = kinematic_record(cls.model)

    def test_independent_forward_kinematics_passes(self):
        self.assertTrue(score(self.record, self.model)["passed"])

    def test_quaternion_sign_does_not_change_pose(self):
        data = copy.deepcopy(self.record)
        data["quaternion"] *= -1
        self.assertTrue(score(data, self.model)["passed"])

    def test_target_pose_cannot_replace_actual_joint_pose(self):
        data = copy.deepcopy(self.record)
        data["q"][500:800, 0] += 0.02
        self.assertFalse(score(data, self.model)["checks"]["actual_joint_fk_position"])

    def test_frozen_joint_cannot_pass_motion_coverage(self):
        data = copy.deepcopy(self.record)
        data["q"][:, 1] = self.model.key_qpos[0, 1]
        self.assertFalse(score(data, self.model)["checks"]["every_joint_exercised"])

    def test_missing_samples_nonfinite_clock_and_velocity_fail(self):
        for failure in ("missing", "nonfinite", "clock", "velocity"):
            data = copy.deepcopy(self.record)
            if failure == "missing":
                data["q"] = data["q"][:-1]
            elif failure == "nonfinite":
                data["position"][2, 0, 0] = np.nan
            elif failure == "clock":
                data["time"][2] = data["time"][1]
            else:
                data["dq"][-10:, 1] = 0.1
            self.assertFalse(score(data, self.model)["passed"], failure)

    def test_limit_posture_moves_inward(self):
        amplitude = excitation(
            np.array([1.0, -1.0]), np.array([[-1.0, 1.0], [-1.0, 1.0]])
        )
        np.testing.assert_equal(amplitude, [-0.03, 0.03])
        with self.assertRaises(ValueError):
            excitation(np.array([1.1]), np.array([[-1.0, 1.0]]))

    def test_rotated_fixed_frame_preserves_child_pose_and_mass_matrix(self):
        text = """<mujoco><compiler angle="radian"/><worldbody>
        <body name="base"><inertial mass="1" pos="0 0 0" diaginertia="1 1 1"/>
          <body name="frame" pos="1 2 3" quat=".7071067811865476 0 0 .7071067811865476">
            <inertial mass="1e-8" pos="0 0 0" diaginertia="1e-8 1e-8 1e-8"/>
            <body name="arm" pos="1 0 0"><joint name="joint" range="-1 1"/>
              <inertial mass="2" pos=".1 0 0" diaginertia=".1 .2 .2"/>
              <body name="tip" pos="0 0 .1">
                <inertial mass="1e-8" pos="0 0 0" diaginertia="1e-8 1e-8 1e-8"/>
              </body>
            </body>
          </body>
        </body></worldbody></mujoco>"""
        original = mujoco.MjModel.from_xml_string(text)
        for name in ("frame", "tip"):
            original.body(name).mass[:] = 0
            original.body(name).inertia[:] = 0
        mujoco.mj_setConst(original, mujoco.MjData(original))
        tree = ET.fromstring(text)
        mapping = collapse_massless_frames(
            tree.find("./worldbody/body"), {"frame", "tip"}
        )
        self.assertEqual(mapping, {"frame": "base", "tip": "arm"})
        candidate = mujoco.MjModel.from_xml_string(ET.tostring(tree).decode())
        self.assertTrue(
            compare_reduction(original, candidate, ["joint"], np.array([0.3]))["passed"]
        )
        data = mujoco.MjData(candidate)
        mujoco.mj_kinematics(candidate, data)
        np.testing.assert_allclose(
            data.xpos[candidate.body("arm").id], [1, 3, 3], atol=1e-14
        )
        self.assertIsNotNone(tree.find('.//site[@name="frame_tip"]'))

    def test_collapse_rejects_moving_joint_and_ambiguous_orientation(self):
        root = ET.fromstring(
            '<body name="root"><body name="moving"><joint/></body></body>'
        )
        with self.assertRaises(ValueError):
            collapse_massless_frames(root, {"moving"})
        with self.assertRaises(ValueError):
            move_into_parent(
                ET.fromstring('<body euler="1 0 0"/>'), ET.fromstring("<body/>")
            )


class CollisionFilterTransferTests(unittest.TestCase):
    XML = """<mujoco><worldbody><body name="robot_world">
      <geom name="base" type="sphere" size=".1"/>
      <body name="arm"><joint/><geom name="arm_geom" type="sphere" size=".1"/>
        <body name="tool"><geom type="sphere" size=".1"/>
          <body name="finger"><joint/><geom name="finger_geom" type="sphere" size=".1"/>
            <body name="tip"><geom type="sphere" size=".1"/></body>
          </body>
        </body>
      </body>
      <body name="other"><joint/><geom type="sphere" size=".1"/></body>
    </body></worldbody></mujoco>"""

    def test_fixed_descendants_inherit_parent_filter_but_other_links_still_collide(
        self,
    ):
        model = mujoco.MjModel.from_xml_string(self.XML)
        names = [model.body(i).name for i in range(1, model.nbody)]
        pairs = implicit_body_exclusions(model, names)
        self.assertEqual(
            pairs,
            {
                ("arm", "tool"),
                ("finger", "tip"),
                ("arm", "finger"),
                ("arm", "tip"),
                ("finger", "tool"),
                ("tip", "tool"),
            },
        )
        # Native collision behavior, not just the helper's own formulas.
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        actual = {
            tuple(
                sorted(
                    (
                        model.body(model.geom_bodyid[c.geom1]).name,
                        model.body(model.geom_bodyid[c.geom2]).name,
                    )
                )
            )
            for c in data.contact
        }
        self.assertFalse(actual & pairs)
        self.assertIn(("arm", "other"), actual)
        self.assertIn(("arm", "robot_world"), actual)

    def test_filterparent_disabled_keeps_only_same_weld_exclusions(self):
        model = mujoco.MjModel.from_xml_string(self.XML)
        model.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_FILTERPARENT
        names = [model.body(i).name for i in range(1, model.nbody)]
        self.assertEqual(
            implicit_body_exclusions(model, names), {("arm", "tool"), ("finger", "tip")}
        )
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        actual = {
            tuple(
                sorted(
                    (
                        model.body(model.geom_bodyid[c.geom1]).name,
                        model.body(model.geom_bodyid[c.geom2]).name,
                    )
                )
            )
            for c in data.contact
        }
        self.assertIn(("arm", "finger"), actual)

    def test_explicit_contact_override_is_not_silently_filtered(self):
        root = ET.fromstring(self.XML)
        ET.SubElement(
            ET.SubElement(root, "contact"),
            "pair",
            geom1="arm_geom",
            geom2="finger_geom",
        )
        model = mujoco.MjModel.from_xml_string(ET.tostring(root).decode())
        with self.assertRaisesRegex(ValueError, "Explicit geom-pair"):
            preserve_implicit_filters(root, model)

    def test_authoring_preserves_existing_filters_and_is_idempotent(self):
        root = ET.fromstring(self.XML)
        ET.SubElement(
            ET.SubElement(root, "contact"), "exclude", body1="arm", body2="other"
        )
        model = mujoco.MjModel.from_xml_string(ET.tostring(root).decode())
        self.assertEqual(len(preserve_implicit_filters(root, model)), 6)
        self.assertEqual(preserve_implicit_filters(root, model), [])
        self.assertEqual(len(root.findall("./contact/exclude")), 7)


if __name__ == "__main__":
    unittest.main()
