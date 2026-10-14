"""Native numerical qualification and deliberate corruption of substep records."""

from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.libero_dynamics import diagnostics, mass_matrix, constraint_matrix
from dexlab.libero_physics import model_record, record_substeps

try:
    import mujoco
except ImportError:
    mujoco = None


FREE = '''<worldbody><body name="object" pos="0 0 1"><freejoint/>
<inertial pos=".02 .01 0" mass="1" diaginertia=".03 .04 .05"/>
<geom type="sphere" size=".1"/></body></worldbody>'''
DAMPED = '''<worldbody><body name="slider"><joint name="j" type="slide" damping="3"/>
<geom size=".1" mass="2"/></body></worldbody><actuator><motor joint="j" gear="2"/></actuator>'''
LIMITED = '''<worldbody><body name="hinge"><joint name="j" range="-.1 .1" damping=".2"
actuatorforcerange="-3 3"/><geom type="capsule" size=".03" fromto="0 0 0 .3 0 0" mass="1"/>
<body name="child" pos=".3 0 0"><joint name="j2"/><geom size=".05" mass=".5"/></body>
</body></worldbody><actuator><motor joint="j" gear="2"/></actuator>'''
CONTACT = '''<worldbody><geom type="plane" size="1 1 .1"/>
<body name="object" pos="0 0 .099"><freejoint/><geom type="sphere" size=".1" mass="1"
condim="6" friction=".8 .03 .003"/></body></worldbody>'''
BALL = '''<worldbody><body name="ball" pos="0 0 1"><joint type="ball"/>
<geom type="ellipsoid" size=".1 .15 .2" mass="1"/></body></worldbody>'''


def xml(body, *, jacobian="dense", cone="pyramidal", integrator="Euler"):
    return ('<mujoco><compiler angle="radian" autolimits="true"/>'
            f'<option timestep=".002" integrator="{integrator}" jacobian="{jacobian}" '
            f'cone="{cone}" tolerance="1e-12" iterations="100"/>' + body + '</mujoco>')


class NativeSim:
    def __init__(self, source):
        self.model = SimpleNamespace(_model=mujoco.MjModel.from_xml_string(source))
        self.data = SimpleNamespace(_data=mujoco.MjData(self.model._model))
        self.calls = 0

    def step(self):
        self.calls += 1
        mujoco.mj_step(self.model._model, self.data._data)


@unittest.skipIf(mujoco is None or mujoco.__version__ != "2.3.7", "Requires pinned native MuJoCo 2.3.7")
class LiberoPhysicsTests(unittest.TestCase):
    def setUp(self):
        self.evidence = []

    def tearDown(self):
        destination = os.environ.get("DEXLAB_FIXTURE_EVIDENCE")
        if destination:
            path = Path(destination) / (self.id().rsplit('.', 1)[-1] + '.json')
            path.parent.mkdir(exist_ok=True)
            with path.open('x') as stream:
                json.dump(self.evidence, stream, default=lambda a: a.tolist(), allow_nan=False)

    def capture(self, body=FREE, *, steps=12, jacobian="dense", cone="pyramidal", external=False):
        source = xml(body, jacobian=jacobian, cone=cone)
        sim, control = NativeSim(source), NativeSim(source)
        for obj in (sim, control):
            data, model = obj.data._data, obj.model._model
            data.qvel[:] = .3
            if model.nu:
                data.ctrl[:] = 4
            if body == LIMITED:
                data.qpos[0] = .12
            if external:
                data.xfrc_applied[1] = [.4, -.3, .2, -.1, .25, .5]
                data.qfrc_applied[:] = .07
            mujoco.mj_forward(model, data)
        rows = []
        evidence = {"xml": source, "rows": rows}
        self.evidence.append(evidence)
        with record_substeps(sim, rows.append) as model:
            evidence["model"] = model
            for _ in range(steps):
                sim.step()
                control.step()
                # Test actual native state and caches, not just the hook's own output.
                for key in ("qpos", "qvel", "act", "qacc", "qacc_warmstart", "ctrl", "qM",
                            "efc_force", "qfrc_constraint", "actuator_force", "xpos"):
                    np.testing.assert_array_equal(getattr(sim.data._data, key), getattr(control.data._data, key))
                self.assertEqual(sim.data._data.time, control.data._data.time)
        self.assertEqual(sim.calls, steps)
        self.assertNotIn("step", vars(sim))
        return model, rows, sim

    def assert_residuals(self, model, rows):
        for row in rows:
            residuals = diagnostics(model, row)
            # Fixed numeric fixture tolerance; no universal physical acceptance.
            for key, residual in residuals.items():
                self.assertLessEqual(float(np.max(np.abs(residual), initial=0)), 1e-8, key)

    def test_free_body_external_wrench_and_native_mass_expansion(self):
        model, rows, sim = self.capture(external=True)
        self.assert_residuals(model, rows)
        native = np.empty((sim.model._model.nv, sim.model._model.nv))
        mujoco.mj_fullM(sim.model._model, native, sim.data._data.qM)
        np.testing.assert_array_equal(mass_matrix(model, rows[-1]["force"]["qM"]), native)
        self.assertEqual(len(rows[-1]["force"]["external_jacobians"]), 1)

    def test_damped_euler_requires_implicit_damping_not_saved_qacc(self):
        model, rows, _ = self.capture(DAMPED)
        self.assert_residuals(model, rows)
        row = rows[0]
        finite_difference = (row["state_after"]["qvel"] - row["state_before"]["qvel"]) / .002
        self.assertGreater(np.max(np.abs(finite_difference - row["force"]["qacc"])), 1e-3)

    def test_ball_quaternion_and_changed_position(self):
        model, rows, _ = self.capture(BALL)
        self.assert_residuals(model, rows)
        row = deepcopy(rows[0]); row["state_after"]["qpos"][1] += .1
        self.assertGreater(np.max(np.abs(diagnostics(model, row)["euler_position"])), .09)

    def test_articulated_limit_and_clipped_motor_effort(self):
        for storage in ("dense", "sparse"):
            with self.subTest(storage=storage):
                model, rows, _ = self.capture(LIMITED, jacobian=storage)
                self.assert_residuals(model, rows)
                self.assertIn(3, rows[0]["force"]["efc_type"])
                self.assertEqual(rows[0]["force"]["qfrc_actuator"][0], 3)
                self.assertEqual(rows[0]["force"]["jacobian"]["native_storage"], storage)

    def test_contact_wrenches_and_jacobians_in_both_cones_and_storage_paths(self):
        for cone in ("pyramidal", "elliptic"):
            for storage in ("dense", "sparse"):
                with self.subTest(cone=cone, storage=storage):
                    model, rows, sim = self.capture(CONTACT, jacobian=storage, cone=cone)
                    self.assert_residuals(model, rows)
                    self.assertTrue(any(row["force"]["contacts"] for row in rows))
                    last = rows[-1]["force"]
                    native = np.empty(sim.model._model.nv)
                    mujoco.mj_mulJacTVec(sim.model._model, sim.data._data, native, sim.data._data.efc_force)
                    np.testing.assert_allclose(constraint_matrix(last["jacobian"], len(last["efc_force"]), len(native)).T @ last["efc_force"], native, atol=1e-12)

    def test_changed_force_channels_create_independent_residuals(self):
        model, rows, _ = self.capture(DAMPED, steps=1)
        for channel, check in (("qfrc_actuator", "actuator_transmission"),
                               ("qfrc_smooth", "smooth_force"), ("qacc", "constrained_acceleration"),
                               ("qfrc_constraint", "constraint_transmission")):
            row = deepcopy(rows[0]); row["force"][channel][0] += 1
            with self.subTest(channel=channel):
                self.assertGreater(np.max(np.abs(diagnostics(model, row)[check])), .9)
        row = deepcopy(rows[0]); row["state_after"]["qvel"][0] += .2
        self.assertGreater(np.max(np.abs(diagnostics(model, row)["euler_velocity"])), 1)

    def test_invalid_epochs_missing_signals_and_external_mapping_rejected(self):
        model, rows, _ = self.capture(external=True, steps=1)
        for mutate in (lambda row: row.update(force_time=.2),
                       lambda row: row["state_after"].update(time=.3),
                       lambda row: row["force"].update(qfrc_applied=[float('nan')] * 6),
                       lambda row: row["force"].update(external_jacobians=[]),
                       lambda row: row["force"]["xipos"].fill(float('nan')),
                       lambda row: row["state_after"].update(warning_number=[1] * 8)):
            row = deepcopy(rows[0]); mutate(row)
            with self.assertRaises(ValueError):
                diagnostics(model, row)
        row = deepcopy(rows[0]); del row["force"]["qfrc_constraint"]
        with self.assertRaises(KeyError):
            diagnostics(model, row)

    def test_contact_corruption_and_aliased_constraint_mapping(self):
        model, rows, _ = self.capture(CONTACT, steps=1)
        row = deepcopy(rows[0]); row["force"]["contacts"][0]["local_wrench"][0] += 1
        self.assertGreater(np.max(np.abs(diagnostics(model, row)["contact_wrench"])), .9)
        row = deepcopy(rows[0]); row["force"]["contacts"][0]["efc_address"] = 999
        with self.assertRaisesRegex(ValueError, "mapping"):
            diagnostics(model, row)
        row = deepcopy(rows[0]); row["force"]["jacobian"]["indices"][1] = row["force"]["jacobian"]["indices"][0]
        with self.assertRaisesRegex(ValueError, "Aliased"):
            diagnostics(model, row)

    def test_hook_restoration_and_failed_partial_record(self):
        sim = NativeSim(xml(FREE)); rows = []
        original = sim.step
        def fail():
            raise RuntimeError("native step failed")
        sim.step = fail
        with self.assertRaisesRegex(RuntimeError, "native step failed"):
            with record_substeps(sim, rows.append):
                sim.step()
        self.assertIs(sim.step, fail)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "failed")
        self.assertEqual(rows[0]["error_type"], "RuntimeError")
        sim.step = original
        with self.assertRaisesRegex(RuntimeError, "sink failed"):
            with record_substeps(sim, lambda row: (_ for _ in ()).throw(RuntimeError("sink failed"))):
                sim.step()
        self.assertEqual(sim.step, original)
        sim.step = fail
        with self.assertRaisesRegex(RuntimeError, "native step failed") as caught:
            with record_substeps(sim, lambda row: (_ for _ in ()).throw(OSError("sink failed"))):
                sim.step()
        self.assertIsInstance(caught.exception.__cause__, OSError)
        self.assertIs(sim.step, fail)

    def test_unsupported_integrator_is_rejected_before_execution(self):
        sim = NativeSim(xml(FREE, integrator="RK4"))
        with self.assertRaisesRegex(ValueError, "Euler"):
            with record_substeps(sim, lambda row: None):
                sim.step()
        self.assertEqual(sim.calls, 0)

    def test_model_topology_corruption_is_rejected(self):
        model, rows, _ = self.capture(steps=1)
        model = deepcopy(model)
        model["arrays"]["dof_parentid"][0] = 0
        with self.assertRaisesRegex(ValueError, "topology"):
            diagnostics(model, rows[0])

    def test_json_roundtrip_retains_empty_dimensions(self):
        model, rows, _ = self.capture(steps=1)
        model, rows = json.loads(json.dumps([model, rows], default=lambda a: a.tolist()))
        self.assert_residuals(model, rows)


if __name__ == "__main__":
    unittest.main()
