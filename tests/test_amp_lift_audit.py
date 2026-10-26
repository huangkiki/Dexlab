"""Analytical conversion fixtures; these do not qualify a GPU recorder."""

from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.amp_lift_audit import (articulated_momentum, compare_contact_decoding,
                                 decode_contact_forces, object_contact_loads)
from dexlab.amp_lift_record import native_counts


class AmpLiftAuditTests(unittest.TestCase):
    def test_momentum_frame_conversion_matches_cpu_subtree_kinematics(self):
        import mujoco

        model = mujoco.MjModel.from_xml_string('''
        <mujoco><worldbody><body name="root" quat=".923879533 0 0 .382683432">
          <freejoint/><inertial pos=".2 0 0" mass="2" diaginertia=".2 .3 .4"/>
          <body name="child" pos="1 .2 0">
            <joint axis="0 0 1"/><inertial pos=".4 .1 0" mass="1" diaginertia=".1 .2 .25"/>
          </body>
        </body></worldbody></mujoco>''')
        data = mujoco.MjData(model)
        data.qpos[-1] = .7
        data.qvel[:] = [1, 2, 3, .3, .4, .5, 1]
        mujoco.mj_forward(model, data)
        mujoco.mj_subtreeVel(model, data)
        result = articulated_momentum(
            mass=model.body_mass, inertia=model.body_inertia, body_ids=[1, 2],
            body_rootid=model.body_rootid, xipos=data.xipos, ximat=data.ximat.reshape(-1, 3, 3),
            cvel=data.cvel, subtree_com=data.subtree_com)
        np.testing.assert_allclose(result["com_world_m"], data.subtree_com[1], atol=1e-12, rtol=0)
        np.testing.assert_allclose(result["linear_momentum_kg_m_s"],
                                   model.body_subtreemass[1] * data.subtree_linvel[1], atol=1e-12, rtol=0)
        np.testing.assert_allclose(result["angular_momentum_about_com_kg_m2_s"],
                                   data.subtree_angmom[1], atol=1e-12, rtol=0)

    def test_opposing_contacts_do_not_erase_loaded_pairs_and_support_is_separate(self):
        contacts = {"geom": np.array([[1, 0], [1, 0], [0, 2], [3, 0], [4, 0]]),
                    "frame": np.tile(np.eye(3), (5, 1, 1)),
                    "pos": np.zeros((5, 3)),
                    "local_force": np.array([[2, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0],
                                             [4, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0],
                                             [2, 0, 0, 0, 0, 0.]])}
        contacts["frame"][1] = np.diag([-1, -1, 1])
        contacts["frame"][2] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
        contacts["frame"][3:] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
        loads = object_contact_loads(contacts, object_geoms=[0], left_geoms=[1], right_geoms=[2],
                                     ground_geoms=[3], object_com=[1., 0, 0], ngeom=5,
                                     loaded_threshold_n=.001)
        self.assertEqual(loads["left"]["loaded_pairs"], 2)
        np.testing.assert_array_equal(loads["left"]["force_n"], [0, 0, 0])
        np.testing.assert_array_equal(loads["right"]["force_n"], [0, 0, 4])
        np.testing.assert_array_equal(loads["right"]["torque_nm"], [0, 4, 0])
        self.assertEqual(loads["ground"]["force_n"][2], 3)
        self.assertEqual(loads["other"]["force_n"][2], 2)

    def test_articulated_momentum_uses_each_body_com_and_rotational_offset(self):
        # Two equal bodies at x=-1,+1 rotate about their common COM with
        # omega_z=2. An internal slider adds +3 m/s to the second body.
        velocity = np.zeros((3, 6))
        velocity[1:, 2] = 2
        velocity[2, 3] = 3
        result = articulated_momentum(
            mass=np.array([0., 1., 1.]), inertia=np.array([[0, 0, 0], [1, 1, 1], [1, 1, 1]]),
            body_ids=[1, 2], body_rootid=[0, 1, 1], xipos=[[0, 0, 0], [-1, 0, 0], [1, 0, 0]],
            ximat=np.tile(np.eye(3), (3, 1, 1)), cvel=velocity, subtree_com=np.zeros((3, 3)))
        self.assertEqual(result["mass_kg"], 2.)
        np.testing.assert_array_equal(result["com_world_m"], [0, 0, 0])
        np.testing.assert_array_equal(result["linear_momentum_kg_m_s"], [3, 0, 0])
        np.testing.assert_array_equal(result["angular_momentum_about_com_kg_m2_s"], [0, 0, 8])

    def test_pyramidal_force_and_torque_components(self):
        contacts = {"dim": np.array([4]), "efc_address": np.arange(6).reshape(1, 6),
                    "friction": np.array([[.5, .25, .1, .01, .01]]),
                    "local_force": np.array([[19, 1, 1, .5, 0, 0.]])}
        raw = np.array([3., 1., 5., 1., 7., 2.])
        np.testing.assert_array_equal(decode_contact_forces(contacts, raw, cone=0), contacts["local_force"])
        self.assertTrue(compare_contact_decoding(contacts, raw, cone=0, atol=0, rtol=0)["passed"])
        contacts["local_force"][0, 0] = 0
        self.assertFalse(compare_contact_decoding(contacts, raw, cone=0, atol=0, rtol=0)["passed"])

    def test_elliptic_noncontiguous_addresses_and_inactive_contact(self):
        contacts = {"dim": np.array([6, 3]),
                    "efc_address": np.array([[4, 2, 0, 5, 1, 3], [-1] * 6]),
                    "friction": np.ones((2, 5))}
        expected = np.array([[5, 3, 1, 6, 2, 4], [0, 0, 0, 0, 0, 0]])
        np.testing.assert_array_equal(decode_contact_forces(contacts, np.arange(1, 7), cone=1), expected)

    def test_truncated_partial_inactive_and_reused_constraints_are_rejected(self):
        for addresses in ([0, 1, 2], [0, -1, 2, 3], [0, 0, 2, 3], [0, 1, 2, 8]):
            with self.subTest(addresses=addresses):
                contacts = {"dim": np.array([3]), "efc_address": np.array([addresses]),
                            "friction": np.ones((1, 5))}
                with self.assertRaises(ValueError):
                    decode_contact_forces(contacts, np.arange(4.), cone=0)
        contacts = {"dim": np.array([1, 1]), "efc_address": np.array([[0], [0]]),
                    "friction": np.ones((2, 5))}
        with self.assertRaisesRegex(ValueError, "different contacts"):
            decode_contact_forces(contacts, np.array([9.81]), cone=0)

    def test_capacity_overflow_is_rejected_before_host_export_can_clip_it(self):
        def array(value):
            return SimpleNamespace(numpy=lambda: np.array(value))
        data = SimpleNamespace(nacon=array([2]), nefc=array([4]), naconmax=2, njmax=4)
        self.assertEqual(native_counts(data), (2, 4))
        for name, value in (("nacon", [3]), ("nacon", [-1]), ("nefc", [5]), ("nefc", [1, 1])):
            previous = getattr(data, name)
            setattr(data, name, array(value))
            with self.assertRaises(ValueError):
                native_counts(data)
            setattr(data, name, previous)


if __name__ == "__main__":
    unittest.main()
