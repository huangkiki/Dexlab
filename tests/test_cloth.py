"""Independent geometry, boundary-condition and measured-state regressions."""

import os
import unittest
from dataclasses import replace

import numpy as np

from dexlab.cloth import ClothCase, frame_metrics, score_record
from dexlab.tasks.cloth import ClothCfg, ClothEnv


class ClothMeasurementsTest(unittest.TestCase):
    def test_area_lumped_mass_and_refinement(self):
        case = ClothCase()
        vertices, triangles, masses = case.mesh()
        refined = replace(case, nx=17, ny=9)
        self.assertEqual((vertices.shape, triangles.shape), ((45, 3), (64, 3)))
        self.assertAlmostEqual(masses.sum(), 0.004)
        self.assertAlmostEqual(refined.mesh()[2].sum(), masses.sum())
        self.assertGreater(masses[case.nx + 1], masses[0])
        for time in (0, 0.25, 0.75, 1.75, 2.25):
            self.assertAlmostEqual(case.forces(time).sum(), refined.forces(time).sum())
        self.assertAlmostEqual(case.forces(0.25).sum(), 0.0025)
        self.assertEqual(case.forces(2.25).sum(), 0)

    def test_rigid_translation_is_not_strain(self):
        case = ClothCase()
        rest, _, _ = case.mesh()
        result = frame_metrics(case, rest + (0, 0, -0.01), np.zeros_like(rest))
        self.assertLess(result["maximum_absolute_edge_strain"], 1e-12)
        self.assertAlmostEqual(result["maximum_pin_error_m"], 0.01)
        self.assertAlmostEqual(result["tip_sag_m"], 0.01)

    def test_stretch_and_velocity_have_physical_units(self):
        case = ClothCase()
        rest, _, _ = case.mesh()
        stretched = rest.copy()
        stretched[:, 0] = (stretched[:, 0] + 0.1) * 1.1 - 0.1
        result = frame_metrics(case, stretched, np.ones_like(rest) * 0.01)
        self.assertAlmostEqual(result["tip_extension_m"], 0.02)
        self.assertAlmostEqual(result["maximum_absolute_edge_strain"], 0.1)
        self.assertAlmostEqual(result["speed_rms_m_s"], np.sqrt(3) * 0.01)

    def test_triangle_interior_can_penetrate_without_vertex_penetration(self):
        case = ClothCase(experiment="drape", nx=3, ny=3, width=0.2, height=0.18)
        positions = case.mesh()[0].copy()
        # The first triangle crosses the sphere center, while all vertices stay outside.
        positions[[0, 1, 3]] = [[-0.15, -0.1, 0.07], [0.15, -0.1, 0.07], [0, 0.2, 0.07]]
        center = np.array([0, 0, 0.07])
        self.assertGreater(np.linalg.norm(positions - center, axis=1).min(), 0.061)
        result = frame_metrics(case, positions, np.zeros_like(positions))
        self.assertAlmostEqual(result["sphere_penetration_m"], 0.061)

    def test_truncated_or_nonfinite_record_cannot_pass(self):
        case = ClothCase()
        rest = case.mesh()[0]
        positions = np.repeat(rest[None], 4, axis=0)
        velocity = np.zeros_like(positions)
        full = score_record(case, 1, np.arange(4), positions, velocity)
        self.assertTrue(full["protocol_checks_passed"])
        truncated = score_record(case, 1, np.arange(3), positions[:3], velocity[:3])
        self.assertFalse(truncated["protocol_checks_passed"])
        positions[2, 0, 0] = np.nan
        self.assertFalse(
            score_record(case, 1, np.arange(4), positions, velocity)[
                "protocol_checks_passed"
            ]
        )


class ClothTaskTest(unittest.TestCase):
    def test_superdex_shell_freefall_and_reset(self):
        os.environ.setdefault("SUPERDEX_PRECISION", "double")
        import superdex.physics as physics

        owned_context = not physics.is_initialized()
        env = ClothEnv(ClothCfg(case={"experiment": "drape"}), backend_type="superdex")
        try:
            first = env.init_state()
            initial = first.info["positions"].copy()
            solver = env.native.scene.get_solver_params()
            solver.non_linear_solver.abs_tol = 1e-12
            solver.non_linear_solver.rel_tol = 1e-12
            solver.linear_solver.abs_tol = 1e-15
            solver.linear_solver.rel_tol = 1e-12
            env.native.scene.set_solver_params(solver)
            for _ in range(10):
                state = env.step(np.zeros((1, 45, 3)))
            # Backward Euler free fall: sum of end-of-step velocities.
            expected_drop = 9.81 * env.cfg.sim_dt**2 * 10 * 11 / 2
            np.testing.assert_allclose(
                state.info["positions"][:, 2], initial[:, 2] - expected_drop,
                rtol=0, atol=1e-9,
            )
            np.testing.assert_allclose(
                state.info["velocities"][:, 2], -9.81 * 10 * env.cfg.sim_dt,
                rtol=0, atol=1e-8,
            )
            self.assertIn("backward difference", state.info["observation_source"])
            np.testing.assert_allclose(env.init_state().info["positions"], initial)
        finally:
            env.close()
            if owned_context:
                physics.shutdown()

    def test_actual_native_step_and_mass(self):
        env = ClothEnv(ClothCfg())
        try:
            first = env.init_state()
            rest = first.info["positions"].copy()
            force = env.case.forces(0.75)
            current = env.step(force[None])
            self.assertAlmostEqual(current.info["time_s"], 0.0005)
            self.assertGreater(
                current.info["positions"][env.case.tip, 0].mean(),
                rest[env.case.tip, 0].mean(),
            )
            self.assertTrue(
                np.allclose(
                    current.info["positions"][env.case.pins], rest[env.case.pins]
                )
            )
            self.assertAlmostEqual(env.native.metadata["dynamic_mass_kg"], 0.00375)
            expected_integrator = (
                "discrete" if env.native.metadata["version"] == "3.14.0" else "implicitfast"
            )
            self.assertEqual(env.native.metadata["integrator"], expected_integrator)
            self.assertEqual(
                env.native.model.opt.integrator,
                getattr(env.native.mj.mjtIntegrator, "mjINT_" + expected_integrator.upper()),
            )
            self.assertEqual(current.obs["obs"].shape, (1, 271))
        finally:
            env.close()

    def test_invalid_boundary_action_does_not_step(self):
        env = ClothEnv(ClothCfg())
        try:
            env.init_state()
            with self.assertRaises(ValueError):
                env.step(np.ones((1, 45, 3)))
            self.assertEqual(env.steps, 0)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
