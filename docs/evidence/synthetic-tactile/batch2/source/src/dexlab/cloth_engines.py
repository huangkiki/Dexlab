"""Native cloth models behind the shared measured-state UniLab task."""

import base64
import hashlib
import json
from importlib.metadata import distribution, version

import numpy as np

from dexlab.engine_versions import mujoco_profile_identity


def package_identity(name):
    """Reject locally modified package code and retain the installation origin."""
    dist = distribution(name)
    hashes = {}
    for entry in dist.files or ():
        if not (str(entry).endswith(".py") or ".so" in entry.name):
            continue
        if entry.hash is None or entry.hash.mode != "sha256":
            raise RuntimeError(f"Missing SHA256 RECORD entry for {entry}")
        digest = hashlib.sha256(dist.locate_file(entry).read_bytes()).digest()
        if base64.urlsafe_b64encode(digest).rstrip(b"=").decode() != entry.hash.value:
            raise RuntimeError(f"Modified {name} package file: {entry}")
        hashes[str(entry)] = digest.hex()
    if not hashes:
        raise RuntimeError(f"No auditable package files for {name}")
    return {
        "version": dist.version,
        "record_verified": True,
        "code_sha256": hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest(),
        "installation_origin": json.loads(dist.read_text("direct_url.json") or "null"),
    }


class MuJoCoCloth:
    def __init__(self, case, dt, *, device="cpu", iterations=50):
        import mujoco

        identity = mujoco_profile_identity(package_identity("mujoco"),
                                           mujoco.mj_versionString())
        if device != "cpu":
            raise ValueError("This adapter uses native CPU MuJoCo, not MuJoCo Warp")
        self.mj = mujoco
        self.case = case
        self.dt = dt
        # Explicit candidate profile follows the official 3.13 flex migration.
        # Historical records retain their original integration scheme.
        integrator = (
            "discrete"
            if identity["compatibility_profile"] in ("qualification-3.14.0", "qualification-3.15.0")
            else "implicitfast"
        )
        vertices, triangles, masses = case.mesh()
        points = " ".join(map(str, vertices.ravel()))
        elements = " ".join(map(str, triangles.ravel()))
        pins = (
            '<pin id="' + " ".join(map(str, case.pins)) + '"/>'
            if len(case.pins)
            else ""
        )
        obstacle = '<geom type="plane" size="1 1 .1"/>' if case.experiment in ("drape", "folded-drop") else ""
        if case.experiment == "drape":
            obstacle += f'<geom type="sphere" pos="0 0 {case.sphere_height}" size="{case.sphere_radius}"/>'
        self.xml = f'''<mujoco model="cloth-{case.name}">
          <default><geom friction=".5 .005 .0001" solref=".005 1" solimp=".9 .95 .001"/></default>
          <option timestep="{dt}" gravity="{" ".join(map(str, case.gravity))}"
                  solver="Newton" integrator="{integrator}" iterations="{iterations}" tolerance="1e-10"/>
          <worldbody>{obstacle}
            <flexcomp name="cloth" type="direct" dim="2" point="{points}" element="{elements}"
                      radius="{case.radius}" mass="{masses.sum()}">
              {pins}<contact selfcollide="auto" {('internal="true"' if mujoco.mj_version() < 315 else '')} friction="0.5 .005 .0001"
                solref=".005 1" solimp=".9 .95 .001"/>
              <elasticity young="20000" poisson="0" thickness=".0005" elastic2d="both" damping=".001"/>
            </flexcomp>
          </worldbody>
        </mujoco>'''
        self.model = mujoco.MjModel.from_xml_string(self.xml)
        self.data = mujoco.MjData(self.model)
        bodies = self.model.flex_vertbodyid.copy()
        self.free = np.flatnonzero(bodies != 0)
        self.dofs = np.array([self.model.body_dofadr[bodies[i]] for i in self.free])
        for i in self.free:
            self.model.body_mass[bodies[i]] = masses[i]
        mujoco.mj_setConst(self.model, self.data)
        mujoco.mj_forward(self.model, self.data)
        self.metadata = {
            "engine": "mujoco",
            "version": version("mujoco"),
            "solver": "Newton",
            "integrator": integrator,
            "device": "cpu",
            "precision": "float64",
            "iterations": iterations,
            "tolerance": 1e-10,
            "material": {
                "young_Pa": 20000,
                "poisson": 0,
                "thickness_m": 0.0005,
                "elastic2d": "both",
                "damping": 0.001,
            },
            "contact": {
                "radius_m": case.radius,
                "friction": [0.5, 0.005, 0.0001],
                "solref": [0.005, 1],
                "solimp": [0.9, 0.95, 0.001],
                "selfcollide": "auto",
            },
            "mass_distribution": "triangle-area lumped; pinned vertices fixed to world",
            "nominal_mass_kg": float(masses.sum()),
            "dynamic_mass_kg": float(self.model.body_mass.sum()),
            "package_identity": identity,
        }

    def observe(self):
        # mj_step leaves position-dependent arrays at the pre-integration state.
        self.mj.mj_fwdPosition(self.model, self.data)
        velocities = np.zeros((self.model.nflexvert, 3))
        velocities[self.free] = self.data.qvel[self.dofs[:, None] + np.arange(3)]
        return self.data.flexvert_xpos.copy(), velocities

    def step(self, forces):
        previous_time = self.data.time
        self.data.qfrc_applied[:] = 0
        self.data.qfrc_applied[self.dofs[:, None] + np.arange(3)] = forces[self.free]
        self.mj.mj_step(self.model, self.data)
        if self.data.warning.number.any():
            raise RuntimeError(
                f"MuJoCo physics warning: {self.data.warning.number.tolist()}"
            )
        if not np.isclose(self.data.time - previous_time, self.dt, atol=1e-10, rtol=0):
            raise RuntimeError("MuJoCo did not advance the declared timestep")


class NewtonCloth:
    def __init__(self, case, dt, *, solver, device="cpu", iterations=10):
        import newton
        import warp as wp
        from newton import solvers

        identity = package_identity("newton")
        warp_identity = package_identity("warp-lang")
        if (identity["version"], warp_identity["version"]) != ("1.7.0.dev0", "1.17.0"):
            raise ValueError("Use the pinned Newton and Warp optional requirements")
        self.wp = wp
        self.dt = dt
        self.case = case
        self.device = wp.get_device(device)
        if solver not in ("xpbd", "vbd", "semi_implicit", "featherstone", "style3d"):
            raise ValueError(f"Unknown Newton cloth solver: {solver}")
        vertices, triangles, masses = case.mesh()
        builder = newton.ModelBuilder(gravity=case.gravity)
        if solver == "style3d":
            solvers.SolverStyle3D.register_custom_attributes(builder)
        shape = builder.default_shape_cfg.copy()
        shape.ke, shape.kd, shape.mu = 100.0, 1.0, 0.5
        if case.experiment in ("drape", "folded-drop"):
            builder.add_ground_plane(cfg=shape)
        if case.experiment == "drape":
            builder.add_shape_sphere(
                -1,
                radius=case.sphere_radius,
                xform=wp.transform((0, 0, case.sphere_height), wp.quat_identity()),
                cfg=shape,
            )
        common = dict(
            pos=wp.vec3(0),
            rot=wp.quat_identity(),
            scale=1.0,
            vel=wp.vec3(0),
            vertices=vertices.tolist(),
            indices=triangles.ravel().tolist(),
            density=case.areal_density,
            particle_radius=case.radius,
        )
        material = dict(
            tri_ke=5.0,
            tri_ka=5.0,
            tri_kd=0.01 if solver == "vbd" else 0.001,
            edge_ke=0.0001,
            edge_kd=0.0,
        )
        if solver == "style3d":
            material = {
                "tri_aniso_ke": (10.0, 10.0, 5.0),
                "edge_aniso_ke": (2e-6, 1e-6, 5e-6),
                "tri_ka": 10.0,
                "tri_kd": 0.001,
                "edge_kd": 0.0,
            }
            native_material = dict(
                material,
                tri_aniso_ke=wp.vec3(*material["tri_aniso_ke"]),
                edge_aniso_ke=wp.vec3(*material["edge_aniso_ke"]),
            )
            solvers.style3d.add_cloth_mesh(builder, **common, **native_material)
        else:
            if solver == "xpbd":
                material.update(add_springs=True, spring_ke=10.0, spring_kd=0.001)
            builder.add_cloth_mesh(**common, **material)
        for i, mass in enumerate(masses):
            builder.particle_mass[i] = 0.0 if i in case.pins else float(mass)
        if solver == "vbd":
            builder.color(include_bending=True)
        self.model = builder.finalize(device=self.device)
        self.model.soft_contact_ke = 100.0
        self.model.soft_contact_kd = 100.0 if solver in ("vbd", "style3d") else 1.0
        self.model.soft_contact_mu = 0.5
        if solver == "vbd":
            self.solver = solvers.SolverVBD(
                self.model,
                iterations=iterations,
                particle_enable_self_contact=True,
                particle_self_contact_margin=case.radius * 4,
                particle_self_contact_gap=case.radius * 2,
            )
        elif solver == "xpbd":
            self.solver = solvers.SolverXPBD(self.model, iterations=iterations)
        elif solver == "style3d":
            self.solver = solvers.SolverStyle3D(self.model, iterations=iterations)
        elif solver == "featherstone":
            self.solver = solvers.SolverFeatherstone(self.model)
        else:
            self.solver = solvers.SolverSemiImplicit(self.model)
        self.current, self.next = self.model.state(), self.model.state()
        self.control = self.model.control()
        self.pipeline = newton.CollisionPipeline(self.model)
        self.contacts = self.pipeline.contacts()
        self.metadata = {
            "engine": "newton",
            "version": version("newton"),
            "warp": version("warp-lang"),
            "solver": solver,
            "device": str(self.device),
            "precision": "float32",
            "iterations": None if solver in ("semi_implicit", "featherstone") else iterations,
            "material": material,
            "parameter_provenance": "nominal, adapted from official cloth_hanging example; not calibrated",
            "contact": {
                "radius_m": case.radius,
                "ke": self.model.soft_contact_ke,
                "kd": self.model.soft_contact_kd,
                "mu": 0.5,
                "self_contact": solver in ("vbd", "style3d"),
            },
            "cloth_method": "shared semi-implicit particle kernels" if solver == "featherstone" else solver,
            "nominal_mass_kg": float(masses.sum()),
            "dynamic_mass_kg": float(self.model.particle_mass.numpy().sum()),
            "mass_distribution": "triangle-area lumped; pinned masses zero",
            "particle_velocity_limit_m_s": float(self.model.particle_max_velocity),
            "reference_source_commit": "2dee323416ab34763d8680fa5108a28ea688efff",
            "package_identity": identity,
            "warp_identity": warp_identity,
        }

    def observe(self):
        return self.current.particle_q.numpy().astype(
            float
        ), self.current.particle_qd.numpy().astype(float)

    def step(self, forces):
        self.current.clear_forces()
        self.current.particle_f.assign(np.asarray(forces, dtype=np.float32))
        self.pipeline.collide(self.current, self.contacts)
        self.solver.step(self.current, self.next, self.control, self.contacts, self.dt)
        self.current, self.next = self.next, self.current
        # Timings include actual completion, not only asynchronous dispatch.
        self.wp.synchronize_device(self.device)
