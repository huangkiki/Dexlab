"""Official FP64 SuperDex experimental thin shells, not volume FEM proxies."""

import os

import numpy as np

from dexlab.cloth_engines import package_identity


class SuperDexCloth:
    def __init__(self, case, dt, *, device="cpu", iterations=10):
        os.environ.setdefault("SUPERDEX_PRECISION", "double")
        import superdex.physics as physics

        identity = package_identity("superdex-physics-fp64")
        if identity["version"] != "1.0.0" or not physics.uses_double_precision():
            raise ValueError("This shell profile requires official SuperDex 1.0.0 FP64")
        if device != "cpu":
            raise ValueError("This SuperDex shell profile runs on CPU")
        if not physics.is_initialized():
            physics.initialize(num_worker_threads=0)
        self.physics = physics
        self.dt = dt
        self.scene = physics.create_scene(f"cloth-{case.name}")
        try:
            self._build(case, iterations, identity)
        except Exception:
            self.close()
            raise

    def _build(self, case, iterations, identity):
        physics = self.physics
        vertices, triangles, masses = case.mesh()
        self.scene.set_gravity(case.gravity)
        solver = self.scene.get_solver_params()
        solver.integration_method = physics.IntegrationMethod.BACKWARD_EULER
        solver.non_linear_solver.max_iter = iterations
        self.scene.set_solver_params(solver)
        material = physics.experimental.shell_material_params_from3d_isotropic(
            20000.0, 0.0, case.areal_density / 0.0005, 0.0005
        )
        material.stiffness_damping_coefficient = 0.001
        params = physics.experimental.ShellActorParams()
        params.name = "cloth"
        params.shape = physics.create_tri_mesh_shape(vertices.ravel(), triangles.ravel())
        params.material = material
        params.contact.penalty_threshold_default = case.radius
        params.contact.penalty_smoothing_half_distance = case.radius / 4
        params.point_cloud_collider.radius = 2 * case.radius
        params.point_cloud_collider.self_contact = True
        self.actor = physics.experimental.create_shell_actor(self.scene, params)
        if len(case.pins):
            self.actor.add_boundary_condition_nodes_world_permanent(
                case.pins.astype(np.int32), vertices[case.pins].ravel()
            )
        self.actor.register_query(physics.QueryType.NODE_POSITIONS)
        if case.experiment in ("drape", "folded-drop"):
            self.scene.create_rigid_actor(physics.RigidActorParams(
                name="ground", is_static=True,
                shape=physics.create_plane_shape([0, 0, 1], 0),
            ))
        if case.experiment == "drape":
            self.scene.create_rigid_actor(physics.RigidActorParams(
                name="sphere", is_static=True,
                shape=physics.create_sphere_shape([0, 0, case.sphere_height], case.sphere_radius),
            ))
        self.scene.step(0)
        self.positions = self._positions()
        self.velocities = np.zeros_like(self.positions)
        self.dofs = np.arange(self.actor.get_num_dofs(), dtype=np.int32)
        if len(self.dofs) != vertices.size:
            raise RuntimeError("Shell DoFs do not match three translations per vertex")
        if not np.isclose(self.actor.get_mass(), masses.sum(), rtol=1e-10, atol=1e-12):
            raise RuntimeError("Native shell mass differs from declared areal mass")
        self.metadata = {
            "engine": "superdex", "version": "1.0.0", "solver": "experimental-shell",
            "integrator": "backward_euler", "precision": "float64", "device": "cpu",
            "iterations": iterations,
            "solver_parameters": {
                "nonlinear_type": str(solver.non_linear_solver.solver_type),
                "nonlinear_abs_tol": solver.non_linear_solver.abs_tol,
                "nonlinear_rel_tol": solver.non_linear_solver.rel_tol,
                "linear_type": str(solver.linear_solver.solver_type),
                "linear_abs_tol": solver.linear_solver.abs_tol,
                "linear_rel_tol": solver.linear_solver.rel_tol,
                "linear_max_iter": solver.linear_solver.max_iter,
            },
            "package_identity": identity,
            "api_identity": package_identity("superdex-physics"),
            "material": {name: getattr(material, name) for name in (
                "membrane_lambda", "membrane_mu", "bending_alpha", "bending_beta",
                "density", "mass_damping_coefficient", "stiffness_damping_coefficient",
            )},
            "material_conversion": {
                "young_Pa": 20000, "poisson": 0, "thickness_m": 0.0005,
                "density_kg_m3": case.areal_density / 0.0005,
                "method": "official shell_material_params_from3d_isotropic; not cross-solver calibrated",
            },
            "contact": {
                "penalty_coefficient_Pa_per_m": params.contact.penalty_coefficient,
                "threshold_m": params.contact.penalty_threshold_default,
                "smoothing_half_distance_m": params.contact.penalty_smoothing_half_distance,
                "mu": params.contact.coulomb_friction_coefficient,
                "friction_falloff_velocity_m_s": params.contact.friction_falloff_vel,
                "self_contact": True,
                "point_cloud_radius_m": params.point_cloud_collider.radius,
                "self_contact_exclusion_ratio": params.point_cloud_collider.self_contact_exclusion_ratio,
                "contact_element_type": str(params.contact_element_type),
                "collider_triangle_element_type": str(params.point_cloud_collider.collider_triangle_element_type),
            },
            "nominal_mass_kg": float(masses.sum()),
            "native_mass_kg": self.actor.get_mass(),
            "dynamic_mass_kg": float(masses.sum() - masses[case.pins].sum()),
            "mass_distribution": "native shell FEM; total mass checked; free nominal mass excludes fixed vertices",
            "velocity_observation": "backward difference of native node positions; no public node velocity getter",
            "convergence_counts": {},
            "scope": "experimental triangle shell API, not tetrahedral SoftActorParams",
        }

    def _positions(self):
        # Shell world_from_local is identity and remains fixed; nodes carry deformation.
        return np.asarray(self.actor.get_node_positions_local()).reshape(-1, 3).copy()

    def observe(self):
        return self.positions.copy(), self.velocities.copy()

    def step(self, forces):
        self.actor.set_external_forces_on_dofs(self.dofs, forces.ravel())
        previous_time = self.scene.get_total_simulation_time()
        self.scene.step(self.dt)
        status = self.actor.get_convergence_status().name
        counts = self.metadata["convergence_counts"]
        counts[status] = counts.get(status, 0) + 1
        if status == "DIVERGED":
            raise RuntimeError("SuperDex shell nonlinear solver diverged")
        if not np.isclose(self.scene.get_total_simulation_time() - previous_time, self.dt, rtol=0, atol=1e-10):
            raise RuntimeError("SuperDex did not advance the declared timestep")
        positions = self._positions()
        self.velocities = (positions - self.positions) / self.dt
        self.positions = positions

    def close(self):
        if self.scene is not None:
            self.physics.destroy_scene(self.scene)
            self.scene = None
