"""Body-level analytical references and native epoch/telemetry qualification."""

from copy import copy, deepcopy
import unittest

import numpy as np

from dexlab.libero_body_dynamics import body_accounting, free_com_balance, solver_observation
from dexlab.libero_dynamics import diagnostics
import test_libero_physics as fixtures


@unittest.skipIf(fixtures.mujoco is None or fixtures.mujoco.__version__ != "2.3.7", "Requires pinned native MuJoCo 2.3.7")
class LiberoBodyDynamicsTests(unittest.TestCase):
    setUp = fixtures.LiberoPhysicsTests.setUp
    tearDown = fixtures.LiberoPhysicsTests.tearDown
    capture = fixtures.LiberoPhysicsTests.capture

    def test_body_equations_cover_free_articulated_contact_and_ball(self):
        for source in (fixtures.FREE, fixtures.DAMPED, fixtures.LIMITED, fixtures.CONTACT, fixtures.BALL):
            with self.subTest(source=source):
                model, rows, _ = self.capture(source, steps=3, external=True)
                for row in rows:
                    for name, values in body_accounting(model, row)["residuals"].items():
                        self.assertLessEqual(np.max(np.abs(values), initial=0), 1e-8, name)
                    self.assertEqual(solver_observation(model, row)["termination_reason"], "not-exposed-by-native-api")

    def test_native_rne_agrees_only_with_force_epoch_velocity(self):
        model, rows, sim = self.capture(fixtures.LIMITED, steps=1, external=True)
        row = rows[0]
        result = body_accounting(model, row)
        original = sim.data._data.qvel.copy()
        scratch = copy(sim.data._data)
        scratch.qvel[:] = row["state_before"]["qvel"]
        fixtures.mujoco.mj_rnePostConstraint(sim.model._model, scratch)
        np.testing.assert_allclose(result["acceleration"], scratch.cacc, rtol=0, atol=1e-10)
        np.testing.assert_allclose(result["inferred_net_subtree_wrench"][1:], scratch.cfrc_int[1:], rtol=0, atol=1e-10)
        np.testing.assert_array_equal(sim.data._data.qvel, original)
        scratch.qvel[:] = original
        fixtures.mujoco.mj_rnePostConstraint(sim.model._model, scratch)
        self.assertGreater(np.max(np.abs(result["acceleration"] - scratch.cacc)), 1e-6)

    def test_fixed_supports_have_weight_and_world_origin_moment(self):
        source = '''<worldbody>
        <body name="left" pos="1 0 0"><geom size=".1" mass="2"/></body>
        <body name="right" pos="-2 0 0"><geom size=".1" mass="3"/></body>
        </worldbody>'''
        model, rows, _ = self.capture(source, steps=1)
        result = body_accounting(model, rows[0])
        supports = result["root_boundary_wrenches"]
        self.assertEqual(len(supports), 2)
        np.testing.assert_allclose(supports[0]["world_origin_wrench"], [0, -19.62, 0, 0, 0, 19.62], rtol=0, atol=1e-12)
        np.testing.assert_allclose(supports[1]["world_origin_wrench"], [0, 58.86, 0, 0, 0, 29.43], rtol=0, atol=1e-12)

    def test_centered_free_impulse_includes_external_and_generalized_forces(self):
        source = fixtures.FREE.replace('pos=".02 .01 0"', 'pos="0 0 0"')
        model, rows, _ = self.capture(source, steps=3, external=True)
        for row in rows:
            balance = free_com_balance(model, row, body_accounting(model, row))[0]
            self.assertEqual(balance["status"], "diagnostic-only")
            np.testing.assert_allclose(balance["expected_impulse"], .002 * np.array([.47, -.23, .27 - 9.81]), rtol=0, atol=1e-14)
            np.testing.assert_allclose(balance["residual_N_s"], 0, rtol=0, atol=1e-12)

    def test_com_offset_and_unsupported_armature_are_explicit(self):
        model, rows, _ = self.capture(steps=2)
        row = rows[0]
        balance = free_com_balance(model, row, body_accounting(model, row))[0]
        naive = np.asarray(row["state_after"]["qvel"][:3]) - row["state_before"]["qvel"][:3]
        self.assertGreater(np.linalg.norm(naive - balance["measured_momentum_change"]), 1e-6)
        altered = deepcopy(model)
        altered["arrays"]["dof_armature"][0] = .1
        self.assertEqual(free_com_balance(altered, row, body_accounting(altered, row))[0]["status"], "unqualified")

    def test_body_channels_and_topology_corruption_are_detected(self):
        model, rows, _ = self.capture(fixtures.LIMITED, steps=1)
        row = deepcopy(rows[0]); row["force"]["cinert"][1, 9] += 1
        self.assertGreater(np.max(np.abs(body_accounting(model, row)["residuals"]["spatial_inertia"])), .99)
        row = deepcopy(rows[0]); row["force"]["cvel"][1, 0] += 1
        self.assertGreater(np.max(np.abs(body_accounting(model, row)["residuals"]["spatial_velocity"])), .99)
        for key, index, value in (("body_rootid", 2, 2), ("body_dofadr", 2, 0), ("body_parentid", 1, 1)):
            altered = deepcopy(model); altered["arrays"][key][index] = value
            with self.assertRaises(ValueError):
                body_accounting(altered, rows[0])
        row = deepcopy(rows[0]); del row["force"]["cdof_dot"]
        with self.assertRaises(KeyError):
            body_accounting(model, row)

    def test_solver_current_prefix_and_stale_channel_rejection(self):
        model, rows, sim = self.capture(fixtures.CONTACT, steps=2)
        record = rows[-1]["force"]["solver"]
        count = record["iterations"]
        self.assertGreater(count, 0)
        for key, value in record["statistics"].items():
            np.testing.assert_array_equal(value, getattr(sim.data._data.solver, key)[:count])
        observation = solver_observation(model, rows[-1])
        self.assertTrue(observation["primal_gradient_comparable"])
        self.assertAlmostEqual(observation["scaled_equation_residual_norm"], record["statistics"]["gradient"][-1], places=10)
        for mutate in (lambda r: r["solver"].update(iterations=count + 1),
                       lambda r: r["solver"].update(fwdinv=[0., 0.]),
                       lambda r: r["solver"].update(termination_reason="converged")):
            altered = deepcopy(rows[-1]); mutate(altered["force"])
            with self.assertRaises(ValueError):
                solver_observation(model, altered)

    def test_no_constraint_stats_are_empty_and_legacy_rows_stay_readable(self):
        model, rows, _ = self.capture(steps=1)
        record = rows[0]["force"]["solver"]
        self.assertEqual(record["iterations"], 0)
        self.assertIsNone(record["nnz"])
        self.assertTrue(all(len(v) == 0 for v in record["statistics"].values()))
        old = deepcopy(model); old["schema_version"] = 1
        diagnostics(old, rows[0])
        with self.assertRaisesRegex(ValueError, "schema 2"):
            solver_observation(old, rows[0])


if __name__ == "__main__":
    unittest.main()
