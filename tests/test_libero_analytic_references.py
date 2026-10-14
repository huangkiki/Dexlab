"""Independent ideal-system references for recorded body loads and integration.

The constants describe synthetic models, not measured LIBERO materials. Closed
forms below do not use native inertia, bias, acceleration or force caches as
their reference. The 1e-10 roundoff allowance applies only to these fixtures.
"""

from copy import deepcopy
import math
import unittest

import numpy as np

from dexlab.libero_body_dynamics import body_accounting, free_com_balance
from dexlab.libero_physics import record_substeps
import test_libero_physics as fixtures


ATOL = 1e-10
GRAVITY = 9.81
STEPS = (.004, .002, .001)
DURATION = .04


@unittest.skipIf(fixtures.mujoco is None or fixtures.mujoco.__version__ != "2.3.7",
                 "Requires pinned native MuJoCo 2.3.7")
class LiberoAnalyticReferenceTests(unittest.TestCase):
    setUp = fixtures.LiberoPhysicsTests.setUp
    tearDown = fixtures.LiberoPhysicsTests.tearDown

    def capture(self, body, *, timestep, steps, position, velocity, control=(), gravity="0 0 -9.81"):
        source = fixtures.xml(body).replace('timestep=".002"', f'timestep="{timestep}"')
        source = source.replace('<option ', f'<option gravity="{gravity}" ')
        sim, original = fixtures.NativeSim(source), fixtures.NativeSim(source)
        for instance in (sim, original):
            data, model = instance.data._data, instance.model._model
            data.qpos[:] = position
            data.qvel[:] = velocity
            data.ctrl[:] = control
            fixtures.mujoco.mj_forward(model, data)
        rows = []
        evidence = {"xml": source, "rows": rows, "reference_errors": []}
        self.evidence.append(evidence)
        with record_substeps(sim, rows.append) as model:
            evidence["model"] = model
            for _ in range(steps):
                sim.step()
                original.step()
                for field in ("qpos", "qvel", "qacc", "qfrc_actuator", "qfrc_constraint"):
                    np.testing.assert_array_equal(getattr(sim.data._data, field),
                                                  getattr(original.data._data, field))
        return model, rows, evidence

    def test_damped_slider_loads_and_finite_time_discretization(self):
        body = '''<worldbody><body name="slider">
        <joint name="slide" type="slide" axis="1 0 0" damping="3"/>
        <inertial pos="0 0 0" mass="2" diaginertia=".03 .04 .05"/>
        <geom type="sphere" size=".05" contype="0" conaffinity="0"/>
        </body></worldbody><actuator><motor joint="slide" gear="2"/></actuator>'''
        mass, damping, drive, initial_q, initial_v = 2., 3., 4., .1, .3
        equilibrium = drive / damping
        exact_v = equilibrium + (initial_v - equilibrium) * math.exp(-damping * DURATION / mass)
        exact_q = initial_q + equilibrium * DURATION + (initial_v - equilibrium) * (
            1 - math.exp(-damping * DURATION / mass)) * mass / damping
        continuous_errors = []
        for h in STEPS:
            count = round(DURATION / h)
            model, rows, evidence = self.capture(body, timestep=h, steps=count,
                                                  position=[initial_q], velocity=[initial_v], control=[2.])
            ratio = mass / (mass + h * damping)
            for index, row in enumerate(rows):
                before_v = equilibrium + (initial_v - equilibrium) * ratio ** index
                after_v = equilibrium + (initial_v - equilibrium) * ratio ** (index + 1)
                after_q = initial_q + h * ((index + 1) * equilibrium +
                    (initial_v - equilibrium) * ratio * (1 - ratio ** (index + 1)) / (1 - ratio))
                expected_load = np.array([0., 0., 0., drive - damping * before_v, 0., mass * GRAVITY])
                actual_load = body_accounting(model, row)["inferred_net_subtree_wrench"][1]
                np.testing.assert_allclose(actual_load, expected_load, rtol=0, atol=ATOL)
                np.testing.assert_allclose(row["state_after"]["qvel"], [after_v], rtol=0, atol=ATOL)
                np.testing.assert_allclose(row["state_after"]["qpos"], [after_q], rtol=0, atol=ATOL)
                evidence["reference_errors"].append({"body_wrench_Nm_N": actual_load - expected_load,
                    "velocity_m_s": float(row["state_after"]["qvel"][0] - after_v),
                    "position_m": float(row["state_after"]["qpos"][0] - after_q)})
            error = np.abs([rows[-1]["state_after"]["qpos"][0] - exact_q,
                            rows[-1]["state_after"]["qvel"][0] - exact_v])
            evidence["continuous_reference_error_m_m_s"] = error
            continuous_errors.append(error)
        # Check convergence to the continuous solution separately from agreement
        # with the discrete recurrence; never call the finite-step error zero.
        self.assertTrue(np.all(np.asarray(continuous_errors)[1:] < np.asarray(continuous_errors)[:-1]))
        self.assertTrue(np.all(np.asarray(continuous_errors) > ATOL))

    def test_hinge_acceleration_and_support_load_from_planar_newton_euler(self):
        body = '''<worldbody><body name="link">
        <joint name="hinge" type="hinge" axis="0 0 1" damping=".2"/>
        <inertial pos=".3 0 0" mass="2" diaginertia=".04 .06 .08"/>
        <geom type="sphere" size=".05" contype="0" conaffinity="0"/>
        </body></worldbody><actuator><motor joint="hinge"/></actuator>'''
        mass, length, inertia, damping, torque = 2., .3, .08, .2, 1.2
        for angle, speed in ((.4, .7), (-.6, -.8)):
            model, rows, evidence = self.capture(body, timestep=.002, steps=1,
                position=[angle], velocity=[speed], control=[torque], gravity="0 -9.81 0")
            row = rows[0]
            alpha = (torque - damping * speed - mass * GRAVITY * length * math.cos(angle)) / (
                inertia + mass * length ** 2)
            acceleration = length * np.array([-math.cos(angle) * speed ** 2 - math.sin(angle) * alpha,
                                              -math.sin(angle) * speed ** 2 + math.cos(angle) * alpha, 0.])
            reaction = mass * (acceleration - np.array([0., -GRAVITY, 0.]))
            expected = np.r_[[0., 0., inertia * alpha], reaction]
            result = body_accounting(model, row)
            actual = result["inferred_net_subtree_wrench"][1]
            np.testing.assert_allclose(row["force"]["qacc"], [alpha], rtol=0, atol=ATOL)
            np.testing.assert_allclose(actual, expected, rtol=0, atol=ATOL)
            boundary = result["root_boundary_wrenches"][0]["world_origin_wrench"]
            np.testing.assert_allclose(boundary, np.r_[[0., 0., torque - damping * speed], reaction],
                                       rtol=0, atol=ATOL)
            evidence["reference_errors"].append({"acceleration_rad_s2": row["force"]["qacc"] - alpha,
                                                  "body_wrench_Nm_N": actual - expected})
            # A damaged acceleration can no longer agree with the independent
            # physical reference, even if a consumer ignores its task success.
            altered = deepcopy(row)
            altered["force"]["qacc"][0] += .5
            wrong = body_accounting(model, altered)["inferred_net_subtree_wrench"][1]
            self.assertGreater(np.max(np.abs(wrong - expected)), .01)
            evidence["corrupted_acceleration_wrench_error_Nm_N"] = wrong - expected

    def test_centered_free_fall_impulse_and_known_position_error(self):
        body = '''<worldbody><body name="falling"><freejoint/>
        <inertial pos="0 0 0" mass="2" diaginertia=".03 .04 .05"/>
        <geom type="sphere" size=".05" contype="0" conaffinity="0"/>
        </body></worldbody>'''
        for h in STEPS:
            count = round(DURATION / h)
            model, rows, evidence = self.capture(body, timestep=h, steps=count,
                position=[0., 0., 1., 1., 0., 0., 0.], velocity=[.1, 0., .3, 0., 0., 0.])
            for row in rows:
                result = free_com_balance(model, row, body_accounting(model, row))[0]
                expected = np.array([0., 0., -2 * GRAVITY * h])
                np.testing.assert_allclose(result["measured_momentum_change"], expected, rtol=0, atol=ATOL)
                np.testing.assert_allclose(result["expected_impulse"], expected, rtol=0, atol=ATOL)
                evidence["reference_errors"].append({"impulse_N_s": result["measured_momentum_change"] - expected})
            actual_q = rows[-1]["state_after"]["qpos"][2]
            continuous_q = 1 + .3 * DURATION - .5 * GRAVITY * DURATION ** 2
            known_error = -.5 * GRAVITY * DURATION * h
            self.assertAlmostEqual(actual_q - continuous_q, known_error, delta=ATOL)
            evidence["continuous_vertical_position_error_m"] = actual_q - continuous_q
            evidence["analytical_euler_position_error_m"] = known_error


if __name__ == "__main__":
    unittest.main()
