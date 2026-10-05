"""Native development fixtures for the controlled planar contact protocol.

These are explicit nominal profiles, not cross-engine calibrated materials.
Only development cases are accepted until the complete contact suite is frozen.
"""

import argparse
import json
import os
import subprocess
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import numpy as np

from dexlab.engine_versions import mujoco_profile_identity

from dexlab import contact_archive, contact_parameters
from dexlab.cloth_engines import package_identity
from dexlab.contact_plane import LIMITS, PlaneCase, score
from dexlab.physx_baseline import digest, write_json


class MuJoCoPlane:
    """Official MuJoCo; force epoch is the solve that produced the velocity step."""

    def __init__(self, case, output, *, normal_parameters=None, solver_parameters=None):
        import mujoco as mj

        self.mj, self.case = mj, case
        identity = mujoco_profile_identity(package_identity("mujoco"),
                                           mj.mj_versionString())
        normal = contact_parameters.normal_parameters("mujoco", normal_parameters)
        solver_values = {"iterations": 100, "tolerance": 1e-10} | contact_parameters.solver_parameters("mujoco", solver_parameters)
        solref = " ".join(map(str, normal["solref"]))
        solimp = " ".join(map(str, normal["solimp"]))
        h, b, mu = case.timestep, case.half_size, case.friction
        inertia = " ".join(map(str, case.inertia))
        xml = f'''<mujoco model="controlled-plane">
  <option timestep="{h}" gravity="0 0 -{case.gravity}" integrator="Euler"
          solver="Newton" cone="elliptic" iterations="{solver_values['iterations']}" tolerance="{solver_values['tolerance']}"/>
  <default><geom condim="3" friction="{mu} 0 0"
                 solref="{solref}" solimp="{solimp}"/></default>
  <worldbody>
    <geom name="plane" type="plane" size="2 2 0.1"/>
    <body name="box" pos="0 0 {b}"><freejoint/>
      <inertial pos="0 0 0" mass="{case.mass}" diaginertia="{inertia}"/>
      <geom name="box" type="box" size="{b} {b} {b}"/>
    </body>
  </worldbody>
</mujoco>'''
        (output / "model.xml").write_text(xml)
        self.model = mj.MjModel.from_xml_string(xml)
        self.data = mj.MjData(self.model)
        mj.mj_forward(self.model, self.data)
        self.metadata = {
            "normal_parameters_readback": {
                "solref": self.model.geom_solref[1].tolist(),
                "solimp": self.model.geom_solimp[1].tolist(),
            },
            "engine": "mujoco",
            "identity": identity,
            "mass_readback": float(self.model.body_mass[1]),
            "inertia_readback": self.model.body_inertia[1].tolist(),
            "friction_readback": self.model.geom_friction.tolist(),
            "solver": {
                "integrator": int(self.model.opt.integrator),
                "algorithm": int(self.model.opt.solver),
                "cone": int(self.model.opt.cone),
                "iterations": int(self.model.opt.iterations),
                "tolerance": float(self.model.opt.tolerance),
                "impratio": float(self.model.opt.impratio),
                "disableflags": int(self.model.opt.disableflags),
                "enableflags": int(self.model.opt.enableflags),
            },
            "contact_parameter_observability": "Per-contact native readback at solve epoch",
            "geometry_readback": {
                "type": self.model.geom_type.tolist(),
                "size": self.model.geom_size.tolist(),
                "priority": self.model.geom_priority.tolist(),
                "solmix": self.model.geom_solmix.tolist(),
                "solref": self.model.geom_solref.tolist(),
                "solimp": self.model.geom_solimp.tolist(),
                "condim": self.model.geom_condim.tolist(),
            },
            "profile": "Explicit native normal profile; not hardware material calibration",
            "force_epoch": "Native solved contact force before any forward recomputation; poses after integration",
            "solver_status": "Native warning counters; absence of warnings is not a convergence proof",
        }

    def observe(self):
        pose = self.data.qpos.copy()
        rotation = np.empty(9)
        self.mj.mju_quat2Mat(rotation, pose[3:])
        velocity = np.r_[
            self.data.qvel[:3], rotation.reshape(3, 3) @ self.data.qvel[3:]
        ]
        return pose, velocity

    def start(self):
        self.data.qvel[:] = [self.case.initial_speed, 0, 0, 0, 0, 0]
        self.mj.mj_forward(self.model, self.data)

    def step(self, external_force=None):
        self.data.xfrc_applied[1, :3] = 0 if external_force is None else external_force
        self.mj.mj_step(self.model, self.data)
        force = np.zeros(3)
        contacts = []
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            local = np.zeros(6)
            self.mj.mj_contactForce(self.model, self.data, i, local)
            frame = contact.frame.reshape(3, 3)
            on_box = frame.T @ local[:3] * (1 if contact.geom2 == 1 else -1)
            force += on_box
            contacts.append(
                {
                    "geom1": int(contact.geom1),
                    "geom2": int(contact.geom2),
                    "distance": float(contact.dist),
                    "point": contact.pos.tolist(),
                    "frame": frame.tolist(),
                    "force_local": local.tolist(),
                    "force_on_box": on_box.tolist(),
                    "parameters": {
                        "dimension": int(contact.dim),
                        "friction": contact.friction.tolist(),
                        "solref": contact.solref.tolist(),
                        "solimp": contact.solimp.tolist(),
                        "include_margin": float(contact.includemargin),
                    },
                }
            )
        pose, velocity = self.observe()
        warnings = self.data.warning.number.tolist()
        return pose, velocity, force, contacts, not any(warnings), warnings

    def clock(self):
        return float(self.data.time)

    def close(self):
        pass


class SuperDexPlane:
    """Official FP64 API with actual COM state and signed per-contact forces."""

    def __init__(self, case, output, *, normal_parameters=None, solver_parameters=None):
        os.environ.setdefault("SUPERDEX_PRECISION", "fp64")
        import trimesh
        from superdex import physics as p

        normal = contact_parameters.normal_parameters("superdex", normal_parameters)
        solver_values = contact_parameters.solver_parameters("superdex", solver_parameters)
        self.p, self.case = p, case
        identity = package_identity("superdex-physics-fp64")
        if identity["version"] != "1.0.0" or not p.uses_double_precision():
            raise ValueError("The frozen native profile requires SuperDex 1.0.0 FP64")
        if not p.is_initialized():
            p.initialize(num_worker_threads=0)
        self.scene = p.create_scene(case.name)
        try:
            self.scene.set_gravity([0, 0, -case.gravity])
            solver = self.scene.get_solver_params()
            solver.integration_method = p.IntegrationMethod.BACKWARD_EULER
            solver.non_linear_solver.max_iter = solver_values.get("iterations", 100)
            for key, attribute in (("absolute_tolerance", "abs_tol"), ("relative_tolerance", "rel_tol")):
                if key in solver_values:
                    setattr(solver.non_linear_solver, attribute, solver_values[key])
            self.scene.set_solver_params(solver)
            solver = self.scene.get_solver_params()
            contact = p.ContactParams()
            for key, value in normal.items():
                setattr(contact, key, value)
            contact.coulomb_friction_coefficient = case.friction
            contact.friction_falloff_vel = 0.001
            contact.viscous_friction_coefficient = 0
            mesh = trimesh.creation.box(extents=[2 * case.half_size] * 3)
            np.savez(output / "geometry.npz", vertices=mesh.vertices, faces=mesh.faces)
            shape = p.create_tri_mesh_shape(
                mesh.vertices.ravel(), mesh.faces.astype(np.int32).ravel()
            )
            try:
                self.box = self.scene.create_rigid_actor(
                    p.RigidActorParams(
                        name="box",
                        shape=shape,
                        collider_type=p.ColliderType.BOX,
                        mass=case.mass,
                        moment_of_inertia=[
                            case.inertia[0],
                            0,
                            0,
                            case.inertia[1],
                            0,
                            case.inertia[2],
                        ],
                        center_of_mass=[0, 0, 0],
                        contact=contact,
                        world_from_local=p.TransformRT(
                            translation=[0, 0, case.half_size]
                        ),
                    )
                )
            finally:
                p.release_shape(shape)
            plane = p.create_plane_shape([0, 0, 1], 0)
            try:
                self.plane = self.scene.create_rigid_actor(
                    p.RigidActorParams(
                        name="plane",
                        shape=plane,
                        is_static=True,
                        contact=contact,
                        collider_type=p.ColliderType.PLANE,
                    )
                )
            finally:
                p.release_shape(plane)
            self.box.register_query(p.QueryType.CONTACT_POINTS)
            self.box.register_query(p.QueryType.TOTAL_CONTACT_FORCE)
            self.scene.step(0)
            self.metadata = {
                "normal_parameters_readback": {
                    key: float(getattr(self.box.get_contact_params(), key))
                    for key in normal
                },
                "engine": "superdex",
                "contact_parameter_observability": "Actor parameters only; ContactPoint exposes no combined contact law",
                "actor_contact_parameters": {
                    name: {
                        key: float(getattr(actor.get_contact_params(), key))
                        for key in (
                            "penalty_coefficient", "penalty_threshold_default",
                            "penalty_smoothing_half_distance", "coulomb_friction_coefficient",
                            "friction_falloff_vel", "normal_viscous_damping_coefficient",
                            "viscous_friction_coefficient",
                        )
                    }
                    for name, actor in (("box", self.box), ("plane", self.plane))
                },
                "identity": identity,
                "api_identity": package_identity("superdex-physics"),
                "mass_readback": float(self.box.get_mass()),
                "inertia_readback": np.asarray(
                    self.box.get_rigid_moment_of_inertia_local()
                ).tolist(),
                "friction_readback": [
                    float(a.get_contact_params().coulomb_friction_coefficient)
                    for a in (self.box, self.plane)
                ],
                "contact": {
                    key: float(getattr(self.box.get_contact_params(), key))
                    for key in (
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
                    "absolute_tolerance": solver.non_linear_solver.abs_tol,
                    "relative_tolerance": solver.non_linear_solver.rel_tol,
                },
                "profile": "Explicit native penalty and friction constants; not hardware material calibration",
                "force_epoch": "Actual total force and per-contact native queries after the solved step",
            }
        except Exception:
            self.close()
            raise

    def observe(self):
        transform = self.box.get_root_transform()
        xyzw = np.asarray(transform.rotation)
        pose = np.r_[transform.translation, xyzw[3], xyzw[:3]]
        velocity = np.r_[
            self.box.get_linear_velocity(), self.box.get_angular_velocity()
        ]
        return pose, velocity

    def start(self):
        self.box.set_velocity([self.case.initial_speed, 0, 0], [0, 0, 0])

    def step(self, external_force=None):
        self.box.set_external_forces_on_dofs(
            np.arange(3, dtype=np.int32),
            np.zeros(3) if external_force is None else external_force,
        )
        self.scene.step(self.case.timestep)
        contacts = []
        for point in self.box.get_contact_points_world():
            sign = 1 if point.actor_a == self.box.get_handle() else -1
            contacts.append(
                {
                    "force_on_box": (sign * np.asarray(point.force)).tolist(),
                    "distance": float(point.distance),
                    "normal_native": np.asarray(point.normal).tolist(),
                    "point_a": np.asarray(point.pos_a).tolist(),
                    "point_b": np.asarray(point.pos_b).tolist(),
                    "velocity_a": np.asarray(point.point_velocity_a).tolist(),
                    "velocity_b": np.asarray(point.point_velocity_b).tolist(),
                }
            )
        status = self.box.get_convergence_status().name
        pose, velocity = self.observe()
        return (
            pose,
            velocity,
            np.asarray(self.box.get_contact_force_world()).copy(),
            contacts,
            status != "DIVERGED",
            status,
        )

    def clock(self):
        return float(self.scene.get_total_simulation_time())

    def close(self):
        if self.scene is not None:
            self.p.destroy_scene(self.scene)
            self.scene = None


class PhysXPlane:
    """Qualified UniSim adapter; preserve separate normal/friction patch records."""

    def __init__(self, case, output, *, normal_parameters=None):
        from unisim.backend.isaacsim import (
            backend as adapter,
        )
        from unisim.backend.isaacsim import (
            contact_details,
            physx_solver,
            scene_worker,
        )
        from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
        from unisim.backend.subprocess_ipc import scene_materialization
        from unisim.factory import create_backend

        from dexlab.physx_baseline import create_scene

        normal = contact_parameters.normal_parameters("physx", normal_parameters)
        self.case, self.output, self.steps = case, output, 0
        runtime = resolve_isaacsim_runtime()
        worker = subprocess.run(
            [
                str(runtime.python),
                "-c",
                (
                    "import importlib.metadata as m,json,sys; print(json.dumps({'python':sys.version,"
                    "'packages':{n:m.version(n) for n in ['isaacsim','isaacsim-kernel','isaaclab','torch']}}))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        worker_identity = json.loads(worker.stdout)
        if worker_identity["packages"]["isaacsim"] != "5.1.0.0":
            raise ValueError("The native profile requires Isaac Sim 5.1.0.0")
        for module in (
            scene_worker,
            contact_details,
            adapter,
            physx_solver,
            scene_materialization,
        ):
            path = Path(module.__file__)
            (output / f"unisim-{path.name}").write_bytes(path.read_bytes())
        self.backend = create_backend(
            "isaacsim",
            create_scene(case, output / "scene"),
            num_envs=1,
            sim_dt=case.timestep,
            isaacsim_worker_timeout_s=600,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_contact_offset=0.0001,
            isaacsim_rest_offset=0.0,
            **(
                {"isaacsim_" + k: v for k, v in normal.items()}
                if normal_parameters
                else {}
            ),
        )
        try:
            self.backend.materialize()
            self.backend.enable_contact_details("box")
            write_json(
                output / "native-records.json", self.backend._native_entity_records
            )
            for name, value in (
                ("layout", self.backend.get_scene_layout()),
                ("import-report", self.backend.get_import_report()),
                ("capabilities", self.backend.get_capabilities()),
            ):
                write_json(output / f"{name}.json", value.to_dict())
            self.controls = np.empty((1, 0), dtype=np.float32)
            self.box_ids = self.backend.get_body_ids(["box/body"])
            self.metadata = {
                "normal_parameters_readback": {}
                if not normal_parameters
                else {
                    row["field"]: row["effective"]
                    for row in self.backend.get_import_report().to_dict()["fields"]
                    if row["field"] in normal
                },
                "engine": "physx",
                "adapter_identity": package_identity("unisim-core"),
                "worker": worker_identity,
                "mass_readback": self.backend.get_body_mass().tolist(),
                "friction_readback": self.backend.get_geom_friction().tolist(),
                "profile": "TGS8/2, contact_offset0.1mm, rest_offset0; explicit native profile, not hardware calibration",
                "time_observation": "Count of completed synchronous steps at declared sim_dt; not native clock readback",
                "force_epoch": "Normal and friction patches from completed native step; no pointwise pairing",
                "solver_status": "Public RPC completion; native convergence residual unavailable",
            }
        except Exception:
            self.close()
            raise

    def observe(self):
        state = self.backend.get_entity_state("box")
        return state["root_pose"][0].copy(), state["root_velocity"][0].copy()

    def start(self):
        from unisim.entities import EntityStatePatch, SceneResetRequest

        velocity = np.array(
            [[self.case.initial_speed, 0, 0, 0, 0, 0]], dtype=np.float32
        )
        self.backend.reset_entities(
            SceneResetRequest(
                env_ids=(0,), patches=(EntityStatePatch("box", root_velocity=velocity),)
            )
        )

    def step(self, external_force=None):
        force = np.zeros(3) if external_force is None else external_force
        self.backend.apply_body_force(
            self.box_ids, np.asarray(force, dtype=np.float32)[None, None]
        )
        self.backend.step(self.controls)
        self.steps += 1
        raw = {
            k: np.asarray(v).tolist()
            for k, v in self.backend.get_contact_details().items()
        }
        force = np.zeros(3)
        for kind in ("normal", "friction"):
            values = np.asarray(raw[f"{kind}_force"], dtype=float).reshape(-1, 3)
            ids = np.asarray(raw[f"{kind}_body_ids"])
            if values.shape[0] != len(ids) or np.any(ids != 2):
                raise ValueError(
                    "Unexpected contact partner or incomplete force ledger"
                )
            force += values.sum(axis=0)
        pose, velocity = self.observe()
        return pose, velocity, force, raw, True, "step_completed_convergence_unknown"

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
                    "returncode": process.returncode if process is not None else None,
                    "terminated": process is not None and process.poll() is not None,
                },
            )


def run(case, engine, output, *, solver_parameters=None):
    """Archive every measured step and failures; never overwrite an experiment."""
    if not case.name.startswith("dev-"):
        raise ValueError("Only development cases are admitted before the suite freeze")
    solver_values = contact_parameters.solver_parameters(engine, solver_parameters)
    output.mkdir(parents=True, exist_ok=False)
    from dexlab import cloth_engines, contact_plane, physx_baseline
    from dexlab.tasks import contact_plane as contact_task

    sources = [
        Path(__file__),
        Path(contact_archive.__file__),
        Path(contact_parameters.__file__),
        Path(contact_plane.__file__),
        Path(physx_baseline.__file__),
        Path(cloth_engines.__file__),
        Path(contact_task.__file__),
    ]
    source_hashes = {str(path): digest(path) for path in sources}
    for path in sources:
        name = (
            "contact_plane_task.py"
            if path == Path(contact_task.__file__)
            else path.name
        )
        (output / name).write_bytes(path.read_bytes())
    receipt = {
        "case": asdict(case),
        "limits": LIMITS,
        "engine": engine,
        "source_sha256": source_hashes,
        "status": "preparing",
        "solver_overrides": solver_values,
        "scope": "Development only; uncalibrated nominal planar response",
    }
    write_json(output / "run.json", receipt)
    native, states, forces, clocks, contacts, statuses, completed = (
        None,
        [],
        [],
        [],
        [],
        [],
        [],
    )
    start = time.perf_counter()
    step_seconds = 0.0
    try:
        native = contact_task.ContactPlaneEnv(
            contact_task.ContactPlaneCfg(
                case=asdict(case),
                sim_dt=case.timestep,
                ctrl_dt=case.timestep,
                max_episode_seconds=case.duration,
                output_dir=str(output),
                solver_parameters=solver_values,
            ),
            backend_type="isaacsim" if engine == "physx" else engine,
        )
        state = native.init_state()
        receipt["native"] = native.native.metadata
        receipt["unilab_task"] = contact_task.TASK
        states.append((state.info["pose"], state.info["velocity"]))
        clocks.append(0.0)
        receipt.update(
            status="running", preparation_seconds=time.perf_counter() - start
        )
        write_json(output / "run.json", receipt)
        for _ in range(case.steps):
            started = time.perf_counter()
            state = native.step(np.empty((1, 0)))
            step_seconds += time.perf_counter() - started
            states.append((state.info["pose"], state.info["velocity"]))
            clocks.append(state.info["time_s"])
            forces.append(state.info["contact_force"])
            contacts.append(state.info["contacts"])
            statuses.append(state.info["native_status"])
            completed.append(state.info["step_completed"])
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 -- preserve native failures in the experiment receipt.
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if native is not None:
            try:
                native.close()
            except Exception:  # noqa: BLE001 -- retain failed native cleanup separately.
                receipt["cleanup_error"] = traceback.format_exc()
        data = {
            "time": np.asarray(clocks),
            "pose": np.asarray([s[0] for s in states]).reshape(-1, 7),
            "velocity": np.asarray([s[1] for s in states]).reshape(-1, 6),
            "contact_force": np.asarray(forces).reshape(-1, 3),
            "contact_known": np.ones(len(forces), dtype=bool),
            "step_completed": np.asarray(completed, dtype=bool),
        }
        np.savez_compressed(output / "states.npz", **data)
        receipt["contact_archive"] = contact_archive.write_contacts(output, contacts)
        write_json(output / "native-status.json", statuses)
        receipt.update(
            total_seconds=time.perf_counter() - start,
            step_and_observation_seconds=step_seconds,
            source_unchanged=all(digest(p) == source_hashes[str(p)] for p in sources),
        )
        receipt["artifact_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file() and p.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    result = verify(output)
    write_json(output / "summary.json", result)
    return result


def verify(directory):
    """Independently rescore states, signed contact ledger and archive integrity.

    This development receipt is not a substitute for a separately frozen suite.
    """
    receipt = json.loads((directory / "run.json").read_text())
    case = PlaneCase(**receipt["case"])
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        data = dict(saved)
    result = score(case, data)
    artifacts = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        contact_archive.contact_file(receipt),
        "native-status.json",
        "contact_plane.py",
        "contact_plane_native.py",
        "physx_baseline.py",
        "cloth_engines.py",
    }
    if receipt.get("unilab_task"):
        required.add("contact_plane_task.py")
    required |= {
        "mujoco": {"model.xml"},
        "superdex": {"geometry.npz"},
        "physx": {
            "scene/box.xml",
            "scene/table.xml",
            "scene/sensors.xml",
            "layout.json",
            "import-report.json",
            "native-records.json",
            "worker-exit.json",
            "worker-stderr.log",
        },
    }[receipt["engine"]]
    hashes_match = required <= artifacts.keys() and all(
        not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and (directory / name).is_file()
        and digest(directory / name) == expected
        for name, expected in artifacts.items()
    )
    checks = result["checks"]
    checks.update(
        native_run_completed=receipt.get("status") == "completed",
        source_unchanged=receipt.get("source_unchanged") is True,
        archived_source_hashes_match=contact_archive.source_snapshots_match(
            directory, receipt
        ),
        clean_shutdown="cleanup_error" not in receipt,
        declared_limits=receipt.get("limits") == LIMITS,
        artifact_hashes_match=hashes_match,
    )
    ledger = []
    try:
        raw = contact_archive.read_contacts(directory, receipt)
        if len(raw) != case.steps:
            raise ValueError("Incomplete contact ledger")
        for row in raw:
            values = (
                (row["normal_force"] + row["friction_force"])
                if receipt["engine"] == "physx"
                else [p["force_on_box"] for p in row]
            )
            force = np.asarray(values, dtype=float).reshape(-1, 3)
            if not np.isfinite(force).all():
                raise ValueError("Nonfinite contact force")
            ledger.append(force.sum(axis=0))
        checks["contact_ledger_matches"] = bool(
            np.allclose(ledger, data["contact_force"], atol=1e-7, rtol=1e-6)
        )
    except (KeyError, TypeError, ValueError):
        checks["contact_ledger_matches"] = False
    checks.update(contact_parameters.native_checks(directory, receipt, case))
    if receipt.get("solver_overrides"):
        declared = receipt["solver_overrides"]
        actual = receipt.get("native", {}).get("solver", {})
        checks["solver_overrides_match"] = contact_parameters.solver_readback_matches(
            receipt["engine"], declared, actual
        )
    result["passed"] = all(checks.values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        type=Path,
        help="Rescore an existing development archive without running physics",
    )
    parser.add_argument("--engine", choices=("mujoco", "superdex", "physx"))
    parser.add_argument(
        "--case", type=Path, help="Development PlaneCase JSON; default: dev-slide"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--solver-parameters", type=Path, help="Explicit native solver controls JSON")
    args = parser.parse_args()
    if args.verify:
        if args.engine or args.case or args.output or args.solver_parameters:
            parser.error("--verify cannot be combined with run arguments")
        result = verify(args.verify.resolve())
    else:
        if not args.engine or not args.output:
            parser.error("--engine and --output are required for a native run")
        case = (
            PlaneCase(**json.loads(args.case.read_text())) if args.case else PlaneCase()
        )
        result = run(case, args.engine, args.output.resolve(), solver_parameters=(
            json.loads(args.solver_parameters.read_text()) if args.solver_parameters else None))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
