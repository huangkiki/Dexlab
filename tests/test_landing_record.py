"""Native CPU controls verify contact-force semantics, not Warp qualification."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import mujoco
import numpy as np

from dexlab.landing_record import ContactRecorder, ground_forces, native_contacts, warp_candidates


def copy_fixture(destination, model, source):
    mujoco.mj_copyData(destination, model, source.data)


class LandingRecordTests(unittest.TestCase):
    def test_pre_state_is_captured_after_newton_refreshes_the_core_input(self):
        model = mujoco.MjModel.from_xml_string('''<mujoco><option gravity="0 0 0" timestep=".005"/>
          <worldbody><geom type="plane" size="1 1 .1"/>
          <body name="left_ankle_roll_link" pos="0 0 1"><freejoint/><geom type="sphere" size=".1"/></body>
          <body name="right_ankle_roll_link" pos="1 0 1"><geom type="sphere" size=".1"/></body>
          </worldbody></mujoco>''')
        source = mujoco.MjData(model)

        def core_step():
            mujoco.mj_step(model, source)
        solver = SimpleNamespace(mj_model=model, mjw_data=SimpleNamespace(nworld=1, data=source),
                                 _mujoco_warp_step=core_step)
        manager = SimpleNamespace(_solver=solver, _cfg=SimpleNamespace(use_cuda_graph=False),
                                  get_solver_dt=lambda: .005)
        with patch.dict("sys.modules", {"mujoco_warp": SimpleNamespace(get_data_into=copy_fixture)}), \
                patch("dexlab.landing_record._contact_count", return_value=0), \
                patch("dexlab.landing_record.warp_candidates", return_value={"dist": np.array([])}):
            recorder = ContactRecorder(SimpleNamespace(sim=SimpleNamespace(backend_manager=manager)))
            try:
                # The outer Newton step refreshes the core state before this hook.
                source.qpos[0] = .123
                source.qvel[0] = 1
                solver._mujoco_warp_step()
                self.assertEqual(recorder.samples[0]["pre_qpos"][0], .123)
                self.assertAlmostEqual(recorder.samples[0]["qpos"][0], .128)
                self.assertEqual(len(recorder.samples), 1)
            finally:
                recorder.close()
        self.assertIs(solver._mujoco_warp_step, core_step)

    def test_overflow_is_rejected_before_host_copy_can_truncate_it(self):
        for contacts, constraints in ((33, 8), (20, 51), (-1, 8)):
            data = SimpleNamespace(nacon=SimpleNamespace(numpy=lambda: np.array([contacts])),
                                   nefc=SimpleNamespace(numpy=lambda: np.array([constraints])),
                                   naconmax=32, njmax=50)
            with self.subTest(contacts=contacts, constraints=constraints), self.assertRaisesRegex(ValueError, "overflow"):
                warp_candidates(data)

    def test_solved_contact_copy_does_not_step_or_recompute(self):
        model = mujoco.MjModel.from_xml_string('''<mujoco><option timestep=".005"/>
          <worldbody><geom name="floor" type="plane" size="1 1 .1"/>
          <body pos="0 0 .095"><freejoint/><geom type="sphere" size=".1" mass="1"/>
          </body></worldbody></mujoco>''')
        data = mujoco.MjData(model)
        mujoco.mj_step(model, data)
        state = data.qpos.copy(), data.qvel.copy(), data.time, data.efc_force.copy()
        contacts = native_contacts(model, data)
        self.assertGreater(len(contacts["pairs"]), 0)
        result = ground_forces(contacts, {0}, [{1}, set()])
        self.assertGreater(result["forces"][0, 2], 0)
        self.assertEqual(result["contact_counts"][0], 1)
        self.assertEqual(result["nonfoot_contacts"], 0)
        np.testing.assert_array_equal(data.qpos, state[0])
        np.testing.assert_array_equal(data.qvel, state[1])
        self.assertEqual(data.time, state[2])
        np.testing.assert_array_equal(data.efc_force, state[3])

    def test_cancelling_forces_do_not_hide_loaded_pairs(self):
        contacts = {"pairs": np.array([[0, 3], [0, 4]]), "frames": np.tile(np.eye(3), (2, 1, 1)),
                    "local_forces": np.array([[1., 0, 0, 0, 0, 0], [-1., 0, 0, 0, 0, 0]])}
        result = ground_forces(contacts, {0}, [{1}, {2}])
        np.testing.assert_array_equal(result["nonfoot_force"], np.zeros(3))
        self.assertEqual(result["nonfoot_contacts"], 2)

    def test_reversing_pair_and_force_preserves_world_result(self):
        contacts = {"pairs": np.array([[0, 1]]), "frames": np.eye(3)[None],
                    "local_forces": np.array([[0., 0, 5, 0, 0, 0]])}
        original = ground_forces(contacts, {0}, [{1}, {2}])
        contacts["pairs"] = contacts["pairs"][:, ::-1]
        contacts["local_forces"] *= -1
        reversed_pair = ground_forces(contacts, {0}, [{1}, {2}])
        np.testing.assert_array_equal(original["forces"], reversed_pair["forces"])


if __name__ == "__main__":
    unittest.main()
