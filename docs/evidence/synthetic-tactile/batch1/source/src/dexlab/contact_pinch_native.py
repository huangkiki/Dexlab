"""Native force-driven regular-cylinder fixture, with actual per-step states."""

import os
from pathlib import Path

import numpy as np

from dexlab.engine_versions import mujoco_profile_identity

from dexlab.cloth_engines import package_identity
from dexlab.contact_pinch import HEIGHT, PAD_HALF, PAD_MASS
from dexlab.physx_baseline import write_json


def geometry(case, output):
    import trimesh

    mesh = trimesh.creation.cylinder(
        radius=case.radius, height=2 * case.half_height, sections=case.sections
    )
    # Split planar triangles without projecting new vertices onto a circle.
    # The reference prism and its inertia are unchanged; only sampling changes.
    for _ in range(case.surface_subdivisions):
        mesh = mesh.subdivide()
    mesh.export(output / "cylinder.obj")
    np.savez(output / "geometry.npz", vertices=mesh.vertices, faces=mesh.faces)
    return mesh


def pad_inertia():
    return (
        PAD_MASS
        / 3
        * np.array(
            [
                PAD_HALF[1] ** 2 + PAD_HALF[2] ** 2,
                PAD_HALF[0] ** 2 + PAD_HALF[2] ** 2,
                PAD_HALF[0] ** 2 + PAD_HALF[1] ** 2,
            ]
        )
    )


class MuJoCoCylinder:
    def __init__(self, case, output):
        import mujoco as mj

        identity = mujoco_profile_identity(package_identity("mujoco"),
                                           mj.mj_versionString())
        self.mj, self.case = mj, case
        geometry(case, output)
        pads = []
        for name, direction in [("left", 1), ("right", -1)]:
            pads.append(f'''<body name="{name}" pos="{-direction * case.pad_x} 0 {HEIGHT}" gravcomp="1">
              <joint name="{name}" type="slide" axis="{direction} 0 0" damping="0"/>
              <inertial pos="0 0 0" mass="{PAD_MASS}" diaginertia="{" ".join(map(str, pad_inertia()))}"/>
              <geom name="{name}" type="box" size="{" ".join(map(str, PAD_HALF))}"/>
            </body>''')
        xml = f'''<mujoco model="cylinder-pinch">
          <option timestep="{case.timestep}" gravity="0 0 -{case.gravity}" integrator="Euler"
                  solver="Newton" cone="elliptic" iterations="100" tolerance="1e-10"/>
          <default><geom friction="{case.friction} 0 0" condim="3" solref="0.005 1" solimp="0.95 0.99 0.001"/></default>
          <asset><mesh name="cylinder" file="cylinder.obj"/></asset>
          <worldbody>{"".join(pads)}
            <body name="cylinder" pos="0 0 {HEIGHT}"><freejoint/>
              <inertial pos="0 0 0" mass="{case.mass}" diaginertia="{" ".join(map(str, case.inertia))}"/>
              <geom name="cylinder" type="mesh" mesh="cylinder"/>
            </body>
          </worldbody></mujoco>'''
        (output / "model.xml").write_text(xml)
        self.model = mj.MjModel.from_xml_path(str(output / "model.xml"))
        self.data = mj.MjData(self.model)
        mj.mj_forward(self.model, self.data)
        self.metadata = {
            "engine": "mujoco",
            "identity": identity,
            "mass_readback": self.model.body_mass.tolist(),
            "inertia_readback": self.model.body_inertia.tolist(),
            "friction_readback": self.model.geom_friction.tolist(),
            "geometry": "Convex hull of the archived regular prism; analytic box pads",
            "force_epoch": "Native solve; recorded poses/velocities after integration",
            "initial_support": "Explicit gravity compensation on object only before0.3s",
        }

    def observe(self):
        pose = np.zeros((3, 7))
        velocity = np.zeros((3, 6))
        pose[:, 3] = 1
        pose[:2, 2] = HEIGHT
        pose[:2, 0] = [-self.case.pad_x, self.case.pad_x] + self.data.qpos[:2] * [1, -1]
        velocity[:2, 0] = self.data.qvel[:2] * [1, -1]
        pose[2] = self.data.qpos[2:9]
        rotation = np.empty(9)
        self.mj.mju_quat2Mat(rotation, pose[2, 3:])
        velocity[2, :3] = self.data.qvel[2:5]
        velocity[2, 3:] = rotation.reshape(3, 3) @ self.data.qvel[5:8]
        return pose, velocity

    def step(self, external):
        self.data.xfrc_applied[1:4, :3] = external
        self.mj.mj_step(self.model, self.data)
        force = np.zeros((2, 3))
        normal = np.zeros((2, 3))
        raw = []
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            local = np.zeros(6)
            self.mj.mj_contactForce(self.model, self.data, i, local)
            frame = c.frame.reshape(3, 3)
            if 2 not in (c.geom1, c.geom2):
                continue
            pad = int(c.geom1 if c.geom2 == 2 else c.geom2)
            sign = 1 if c.geom2 == 2 else -1
            f = sign * (frame.T @ local[:3])
            nf = sign * frame[0] * local[0]
            force[pad] += f
            normal[pad] += nf
            raw.append(
                {
                    "pad": pad,
                    "force": f.tolist(),
                    "normal_force": nf.tolist(),
                    "normal_direction": (sign * frame[0]).tolist(),
                    "point": c.pos.tolist(),
                    "distance": float(c.dist),
                    "force_local": local.tolist(),
                }
            )
        pose, velocity = self.observe()
        status = self.data.warning.number.tolist()
        return pose, velocity, force, normal, raw, not any(status), status

    def clock(self):
        return float(self.data.time)

    def close(self):
        pass


class SuperDexCylinder:
    def __init__(self, case, output):
        os.environ.setdefault("SUPERDEX_PRECISION", "fp64")
        import trimesh
        from superdex import physics as p

        identity = package_identity("superdex-physics-fp64")
        if identity["version"] != "1.0.0" or not p.uses_double_precision():
            raise ValueError("SuperDex1.0.0 FP64 required")
        if not p.is_initialized():
            p.initialize(num_worker_threads=0)
        self.p, self.case = p, case
        self.scene = p.create_scene(case.name)
        self.actors = []
        try:
            self.scene.set_gravity([0, 0, -case.gravity])
            solver = self.scene.get_solver_params()
            solver.integration_method = p.IntegrationMethod.BACKWARD_EULER
            solver.non_linear_solver.max_iter = 100
            self.scene.set_solver_params(solver)
            contact = p.ContactParams()
            contact.penalty_coefficient = 1e9
            contact.penalty_threshold_default = 0.0001
            contact.penalty_smoothing_half_distance = 0.00005
            contact.coulomb_friction_coefficient = case.friction
            contact.friction_falloff_vel = 0.001
            contact.normal_viscous_damping_coefficient = 0
            contact.viscous_friction_coefficient = 0
            cylinder = geometry(case, output)
            meshes = [
                trimesh.creation.box(extents=2 * PAD_HALF),
                trimesh.creation.box(extents=2 * PAD_HALF),
                cylinder,
            ]
            for index, (name, x, mass, mesh) in enumerate(
                zip(
                    ["left", "right", "cylinder"],
                    [-case.pad_x, case.pad_x, 0],
                    [PAD_MASS, PAD_MASS, case.mass],
                    meshes,
                )
            ):
                shape = p.create_tri_mesh_shape(
                    mesh.vertices.ravel(), mesh.faces.astype(np.int32).ravel()
                )
                inertia = pad_inertia() if index < 2 else case.inertia
                try:
                    actor = self.scene.create_rigid_actor(
                        p.RigidActorParams(
                            name=name,
                            shape=shape,
                            mass=mass,
                            moment_of_inertia=[
                                inertia[0],
                                0,
                                0,
                                inertia[1],
                                0,
                                inertia[2],
                            ],
                            center_of_mass=[0, 0, 0],
                            world_from_local=p.TransformRT(translation=[x, 0, HEIGHT]),
                            contact=contact,
                            collider_type=p.ColliderType.BOX
                            if index < 2
                            else p.ColliderType.MESH,
                            has_gravity=index == 2,
                        )
                    )
                finally:
                    p.release_shape(shape)
                if index < 2:
                    actor.add_boundary_condition_dofs_world_permanent(
                        [1, 2, 3, 4, 5], [0, HEIGHT, 0, 0, 0]
                    )
                actor.register_query(p.QueryType.TOTAL_CONTACT_FORCE)
                actor.register_query(p.QueryType.CONTACT_POINTS)
                self.actors.append(actor)
            self.scene.step(0)
            self.lookup = {
                actor.get_handle().value: i for i, actor in enumerate(self.actors)
            }
            self.metadata = {
                "engine": "superdex",
                "identity": identity,
                "api_identity": package_identity("superdex-physics"),
                "mass_readback": [a.get_mass() for a in self.actors],
                "inertia_readback": [
                    np.asarray(a.get_rigid_moment_of_inertia_local()).tolist()
                    for a in self.actors
                ],
                "collider_readback": [a.get_collider_type().name for a in self.actors],
                "friction_readback": [
                    float(a.get_contact_params().coulomb_friction_coefficient)
                    for a in self.actors
                ],
                "contact": {
                    k: float(getattr(self.actors[2].get_contact_params(), k))
                    for k in (
                        "penalty_coefficient",
                        "penalty_threshold_default",
                        "penalty_smoothing_half_distance",
                        "coulomb_friction_coefficient",
                        "friction_falloff_vel",
                        "normal_viscous_damping_coefficient",
                        "viscous_friction_coefficient",
                    )
                },
                "solver": {
                    "integrator": solver.integration_method.name,
                    "iterations": solver.non_linear_solver.max_iter,
                },
                "geometry": "Native mesh collider regular prism, native box pads; no SDF substitution",
                "force_epoch": "Native completed-step contact points and queries",
            }
        except Exception:
            self.close()
            raise

    def observe(self):
        pose = []
        velocity = []
        for actor in self.actors:
            transform = actor.get_root_transform()
            xyzw = np.asarray(transform.rotation)
            pose.append(np.r_[transform.translation, xyzw[3], xyzw[:3]])
            velocity.append(
                np.r_[actor.get_linear_velocity(), actor.get_angular_velocity()]
            )
        return np.array(pose), np.array(velocity)

    def step(self, external):
        for actor, force in zip(self.actors, external):
            actor.set_external_forces_on_dofs([0, 1, 2], force)
        self.scene.step(self.case.timestep)
        force = np.zeros((2, 3))
        normal = np.zeros((2, 3))
        raw = []
        body = self.actors[2]
        for point in body.get_contact_points_world():
            on_a = point.actor_a == body.get_handle()
            pad = self.lookup[(point.actor_b if on_a else point.actor_a).value]
            if pad not in (0, 1):
                raise ValueError("Unexpected cylinder contact partner")
            sign = 1 if on_a else -1
            f = sign * np.asarray(point.force)
            direction = sign * np.asarray(point.normal)
            nf = direction * np.dot(f, direction)
            force[pad] += f
            normal[pad] += nf
            raw.append(
                {
                    "pad": pad,
                    "force": f.tolist(),
                    "normal_force": nf.tolist(),
                    "normal_direction": direction.tolist(),
                    "point": np.asarray(point.pos_a if on_a else point.pos_b).tolist(),
                    "distance": float(point.distance),
                    "velocity_a": np.asarray(point.point_velocity_a).tolist(),
                    "velocity_b": np.asarray(point.point_velocity_b).tolist(),
                }
            )
        if not np.allclose(
            force.sum(axis=0), body.get_contact_force_world(), atol=1e-7, rtol=1e-6
        ):
            raise RuntimeError(
                "Cylinder contact ledger differs from actual total contact force"
            )
        pose, velocity = self.observe()
        status = [a.get_convergence_status().name for a in self.actors]
        return pose, velocity, force, normal, raw, "DIVERGED" not in status, status

    def clock(self):
        return float(self.scene.get_total_simulation_time())

    def close(self):
        if self.scene is not None:
            self.p.destroy_scene(self.scene)
            self.scene = None


def physx_scene(case, output):
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    geometry(case, output)
    directory = output / "scene"
    directory.mkdir(exist_ok=False)
    option = f'<option timestep="{case.timestep}" gravity="0 0 -{case.gravity}"/>'
    entities = []
    for name, direction in [("left", 1), ("right", -1)]:
        path = directory / f"{name}.xml"
        path.write_text(f'''<mujoco>{option}<worldbody><body name="base">
          <inertial pos="0 0 0" mass="0.1" diaginertia="0.001 0.001 0.001"/>
          <body name="pad"><joint name="slide" type="slide" axis="{direction} 0 0" range="-0.2 0.2" damping="0"/>
            <inertial pos="0 0 0" mass="{PAD_MASS}" diaginertia="{" ".join(map(str, pad_inertia()))}"/>
            <geom name="surface" type="box" size="{" ".join(map(str, PAD_HALF))}" friction="{case.friction} 0 0" condim="3"/>
          </body></body></worldbody></mujoco>''')
        entities.append(
            SceneEntitySpec(
                name,
                ModelSourceDescriptor(str(path.resolve())),
                kind="articulation",
                root_mode="fixed",
                gravity_disabled=True,
                initial_state=EntityInitialState(
                    position=(-direction * case.pad_x, 0, HEIGHT)
                ),
            )
        )
    path = directory / "cylinder.xml"
    path.write_text(f'''<mujoco>{option}<asset><mesh name="cylinder" file="../cylinder.obj"/></asset>
      <worldbody><body name="body"><freejoint/>
        <inertial pos="0 0 0" mass="{case.mass}" diaginertia="{" ".join(map(str, case.inertia))}"/>
        <geom name="surface" type="mesh" mesh="cylinder" friction="{case.friction} 0 0" condim="3"/>
      </body></worldbody></mujoco>''')
    entities.append(
        SceneEntitySpec(
            "cylinder",
            ModelSourceDescriptor(str(path.resolve())),
            kind="rigid",
            root_mode="floating",
            initial_state=EntityInitialState(position=(0, 0, HEIGHT)),
        )
    )
    sensors = directory / "sensors.xml"
    sensors.write_text(
        "<mujoco><sensor>"
        + "".join(
            f'<contact name="{side}_force" geom1="cylinder/surface" geom2="{side}/surface" data="force" reduce="netforce"/>'
            for side in ("left", "right")
        )
        + "</sensor></mujoco>"
    )
    return SceneCfg(
        entity_assets=tuple(entities), fragment_files=[str(sensors.resolve())]
    )


class PhysXCylinder:
    def __init__(self, case, output):
        import json
        import subprocess

        from unisim.backend.isaacsim import backend as adapter
        from unisim.backend.isaacsim import contact_details, scene_worker
        from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
        from unisim.factory import create_backend

        self.case, self.output, self.steps = case, output, 0
        runtime = resolve_isaacsim_runtime()
        worker = subprocess.run(
            [
                str(runtime.python),
                "-c",
                "import importlib.metadata as m,json,sys; print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in ['isaacsim','isaacsim-kernel','isaaclab','torch']}}))",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        identity = json.loads(worker.stdout)
        if identity["packages"]["isaacsim"] != "5.1.0.0":
            raise ValueError("Isaac Sim5.1.0.0 required")
        for module in (scene_worker, contact_details, adapter):
            path = Path(module.__file__)
            (output / f"unisim-{path.name}").write_bytes(path.read_bytes())
        self.backend = create_backend(
            "isaacsim",
            physx_scene(case, output),
            num_envs=1,
            sim_dt=case.timestep,
            isaacsim_worker_timeout_s=600,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_contact_offset=0.0001,
            isaacsim_rest_offset=0.0,
        )
        try:
            self.backend.materialize()
            self.backend.enable_contact_details("cylinder")
            self.ids = self.backend.get_body_ids(
                ["left/pad", "right/pad", "cylinder/body"]
            )
            self.lookup = {int(body): i for i, body in enumerate(self.ids)}
            self.controls = np.empty((1, 0), dtype=np.float32)
            if self.backend.num_actuators:
                raise RuntimeError("No position actuators allowed in this fixture")
            for name, value in [
                ("layout", self.backend.get_scene_layout()),
                ("import-report", self.backend.get_import_report()),
                ("capabilities", self.backend.get_capabilities()),
            ]:
                write_json(output / f"{name}.json", value.to_dict())
            write_json(
                output / "native-records.json", self.backend._native_entity_records
            )
            self.metadata = {
                "engine": "physx",
                "worker": identity,
                "adapter_identity": package_identity("unisim-core"),
                "body_ids": np.asarray(self.ids).tolist(),
                "mass_readback": self.backend.get_body_mass().tolist(),
                "friction_readback": self.backend.get_geom_friction().tolist(),
                "geometry": "Native convex hull of regular prism; analytic box pads; import report retained",
                "time_observation": "Completed synchronous steps at configured timestep; not native clock readback",
                "profile": "TGS8position/2velocity;0.1mmcontact/0rest offset; not calibrated",
                "force_epoch": "Native normal patches and friction anchors after completed step; not pointwise paired",
            }
        except Exception:
            self.close()
            raise

    def observe(self):
        pose = np.c_[
            self.backend.get_body_pos_w(self.ids)[0],
            self.backend.get_body_quat_w(self.ids)[0],
        ]
        velocity = np.c_[
            self.backend.get_body_lin_vel_w(self.ids)[0],
            self.backend.get_body_ang_vel_w(self.ids)[0],
        ]
        return pose, velocity

    def step(self, external):
        self.backend.apply_body_force(
            self.ids, np.asarray(external, dtype=np.float32)[None]
        )
        self.backend.step(self.controls)
        self.steps += 1
        details = self.backend.get_contact_details()
        raw = {k: np.asarray(v).tolist() for k, v in details.items()}
        force = np.zeros((2, 3))
        normal = np.zeros((2, 3))
        for kind in ["normal", "friction"]:
            values = np.asarray(details[f"{kind}_force"]).reshape(-1, 3)
            for other, vector in zip(details[f"{kind}_body_ids"], values):
                pad = self.lookup[int(other)]
                if pad not in (0, 1):
                    raise ValueError("Unexpected cylinder contact partner")
                force[pad] += vector
                if kind == "normal":
                    normal[pad] += vector
        pose, velocity = self.observe()
        return (
            pose,
            velocity,
            force,
            normal,
            raw,
            True,
            "step_completed_convergence_unknown",
        )

    def clock(self):
        return self.steps * self.case.timestep

    def close(self):
        fd = (
            os.dup(self.backend._stderr_file.fileno())
            if self.backend._stderr_file is not None
            else None
        )
        process = self.backend._proc
        try:
            self.backend.close()
            self.backend.cleanup_scene_assets()
        finally:
            if fd is not None:
                with os.fdopen(fd, "rb") as stream:
                    stream.seek(0)
                    (self.output / "worker-stderr.log").write_bytes(stream.read())
            write_json(
                self.output / "worker-exit.json",
                {
                    "returncode": process.returncode if process else None,
                    "terminated": process is not None and process.poll() is not None,
                },
            )
