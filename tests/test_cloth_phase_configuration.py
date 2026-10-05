"""A phase must not inherit numerical constants from a different timestep."""
from pathlib import Path
import sys
import unittest

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from run_cloth import configure_phase


class PhaseConfigurationTests(unittest.TestCase):
    def model(self, timestep):
        integrator = 'discrete' if hasattr(mujoco.MjModel, 'efm0_L') else 'implicitfast'
        return mujoco.MjModel.from_xml_string(f'''
          <mujoco><option timestep="{timestep}" integrator="{integrator}"
            solver="CG" iterations="100" jacobian="sparse"/>
          <worldbody><flexcomp name="cloth" type="grid" count="3 3 1"
            spacing=".02 .02 .02" dim="2" mass=".01" pos="0 0 .1">
            <edge equality="true"/>
            <elasticity young="1e5" poisson="0" thickness=".0005"
              elastic2d="bend" damping=".0001"/>
          </flexcomp></worldbody></mujoco>''')

    def test_refresh_matches_fresh_phase_and_preserves_live_state(self):
        reference = self.model(.0005)
        for compiled_step in (.00025, .000125):
            with self.subTest(compiled_step=compiled_step):
                model = self.model(compiled_step)
                data = mujoco.MjData(model)
                data.qpos[:] = np.linspace(-.001, .001, model.nq)
                data.qvel[:] = .01
                data.qfrc_applied[:] = .001
                data.time = 1.25
                before = [data.qpos.copy(), data.qvel.copy(), data.qfrc_applied.copy()]
                configure_phase(model, solver=mujoco.mjtSolver.mjSOL_CG, timestep=.0005)
                for actual, expected in zip((data.qpos, data.qvel, data.qfrc_applied), before):
                    np.testing.assert_array_equal(actual, expected)
                self.assertEqual(data.time, 1.25)
                if hasattr(model, 'efm0_L'):
                    self.assertGreater(model.efm0_L.size, 0)
                    np.testing.assert_array_equal(model.efm0_L, reference.efm0_L)
                fresh = mujoco.MjData(reference)
                fresh.qpos[:], fresh.qvel[:], fresh.qfrc_applied[:] = before
                fresh.time = data.time
                for current_model, current in ((model, data), (reference, fresh)):
                    mujoco.mj_forward(current_model, current)
                    for _ in range(50):
                        mujoco.mj_step(current_model, current)
                    self.assertFalse(np.any(current.warning.number))
                np.testing.assert_array_equal(data.qpos, fresh.qpos)
                np.testing.assert_array_equal(data.qvel, fresh.qvel)
