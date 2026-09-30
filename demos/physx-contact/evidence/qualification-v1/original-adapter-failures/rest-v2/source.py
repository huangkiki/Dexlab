"""PhysX contact qualification through UniSim's public entity interface.

These primitive rigid-body tests do not qualify SDF contact or apple grasping.
The observation archive contains actual completed-step states and contact forces.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import time
import traceback

import numpy as np


@dataclass(frozen=True)
class ContactCase:
    name: str
    friction: float
    initial_speed: float = 0.0
    mass: float = 0.2
    half_size: float = 0.02
    timestep: float = 0.001
    duration: float = 2.0
    settle: float = 0.5
    gravity: float = 9.81

    def __post_init__(self) -> None:
        values = np.array(list(asdict(self).values())[1:], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Case values must be finite")
        if min(self.mass, self.half_size, self.timestep, self.duration, self.gravity) <= 0:
            raise ValueError("Mass, size, timestep, duration and gravity must be positive")
        if min(self.friction, self.initial_speed, self.settle) < 0:
            raise ValueError("Friction, initial speed and settle time cannot be negative")
        for duration in (self.settle, self.duration):
            if not np.isclose(duration / self.timestep, round(duration / self.timestep)):
                raise ValueError("Duration and settle time must be integer physics steps")


CASES = {
    "rest": ContactCase("rest", friction=0.5),
    "slide": ContactCase("slide", friction=0.3, initial_speed=0.5),
    "slide-frictionless": ContactCase("slide-frictionless", friction=0.0, initial_speed=0.5),
}

# Engineering acceptance, fixed before the native runs. Not hardware accuracy.
LIMITS = {
    "penetration_m": 0.001,
    "support_relative_error": 0.05,
    "rest_drift_m": 0.001,
    "rest_speed_m_s": 0.005,
    "slide_distance_relative_error": 0.1,
    "slide_distance_absolute_error_m": 0.002,
    "slide_final_speed_m_s": 0.005,
    "frictionless_velocity_error_m_s": 0.01,
}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_scene(case: ContactCase, directory: Path):
    """Write two explicit-mass primitives and a body-net contact force sensor."""
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    directory.mkdir(parents=True, exist_ok=False)
    inertia = 2 * case.mass * case.half_size**2 / 3
    common = f'<option gravity="0 0 -{case.gravity}" timestep="{case.timestep}"/>'
    box = directory / "box.xml"
    box.write_text(
        f'<mujoco model="box">{common}<worldbody><body name="body">'
        '<freejoint name="root"/>'
        f'<inertial pos="0 0 0" mass="{case.mass}" diaginertia="{inertia} {inertia} {inertia}"/>'
        f'<geom name="surface" type="box" size="{case.half_size} {case.half_size} {case.half_size}" '
        f'friction="{case.friction} 0 0" condim="3"/>'
        '</body></worldbody></mujoco>\n'
    )
    table = directory / "table.xml"
    table.write_text(
        f'<mujoco model="table">{common}<worldbody><body name="body">'
        '<inertial pos="0 0 0" mass="10" diaginertia="1 1 1"/>'
        f'<geom name="surface" type="box" size="2 0.5 0.05" friction="{case.friction} 0 0" condim="3"/>'
        '</body></worldbody></mujoco>\n'
    )
    sensors = directory / "sensors.xml"
    sensors.write_text(
        '<mujoco><sensor><contact name="box_force" geom1="box/surface" '
        'data="force" reduce="netforce"/></sensor></mujoco>\n'
    )
    return SceneCfg(
        entity_assets=(
            SceneEntitySpec(
                "box", ModelSourceDescriptor(str(box.resolve())), kind="rigid",
                root_mode="floating", initial_state=EntityInitialState(position=(0, 0, case.half_size)),
            ),
            SceneEntitySpec(
                "table", ModelSourceDescriptor(str(table.resolve())), kind="rigid",
                root_mode="fixed", initial_state=EntityInitialState(position=(0, 0, -0.05)),
            ),
        ),
        fragment_files=[str(sensors.resolve())],
    )


def box_plane_clearance(pose: np.ndarray, half_size: float) -> np.ndarray:
    """Exact box-versus-z=0 clearance from measured xyz/wxyz poses."""
    quaternion = np.asarray(pose)[..., 3:7]
    norms = np.linalg.norm(quaternion, axis=-1)
    if not np.allclose(norms, 1, atol=1e-5, rtol=0):
        raise ValueError("Recorded orientations must be unit quaternions")
    w, x, y, z = np.moveaxis(quaternion, -1, 0)
    # The third row of the rotation matrix projects the three half axes onto z.
    extent = half_size * (
        np.abs(2 * (x * z - w * y))
        + np.abs(2 * (y * z + w * x))
        + np.abs(1 - 2 * (x * x + y * y))
    )
    return pose[..., 2] - extent


def score(case: ContactCase, archive: dict[str, np.ndarray]) -> dict:
    expected_steps = round(case.duration / case.timestep)
    shapes = {"time": (expected_steps,), "pose": (expected_steps, 7),
              "velocity": (expected_steps, 6), "force": (expected_steps, 3),
              "initial_pose": (7,)}
    complete = all(name in archive and archive[name].shape == shape for name, shape in shapes.items())
    finite = complete and all(np.isfinite(archive[name]).all() for name in shapes)
    grid = finite and np.allclose(
        archive["time"], np.arange(1, expected_steps + 1) * case.timestep, atol=1e-10, rtol=0,
    )
    checks = {"complete_finite_archive": bool(finite), "complete_time_grid": bool(grid)}
    if not grid:
        return {"passed": False, "checks": checks, "metrics": {}}
    try:
        clearance = box_plane_clearance(archive["pose"], case.half_size)
    except ValueError:
        checks["unit_quaternions"] = False
        return {"passed": False, "checks": checks, "metrics": {}}
    tail = archive["time"] > case.duration - min(0.5, case.duration / 2)
    distance = float(archive["pose"][-1, 0] - archive["initial_pose"][0])
    support_error = abs(float(archive["force"][tail, 2].mean()) / (case.mass * case.gravity) - 1)
    penetration = float(np.maximum(-clearance, 0).max())
    metrics = {"max_penetration_m": penetration, "support_relative_error": support_error,
               "travel_x_m": distance, "final_speed_m_s": float(np.linalg.norm(archive["velocity"][-1, :3]))}
    checks.update(unit_quaternions=True, bounded_penetration=penetration < LIMITS["penetration_m"],
                  support_matches_weight=support_error < LIMITS["support_relative_error"])
    if case.initial_speed == 0:
        drift = float(np.linalg.norm(archive["pose"][:, :3] - archive["initial_pose"][:3], axis=1).max())
        speed = float(np.linalg.norm(archive["velocity"][tail, :3], axis=1).max())
        metrics.update(max_drift_m=drift, tail_max_speed_m_s=speed)
        checks.update(bounded_drift=drift < LIMITS["rest_drift_m"], bounded_speed=speed < LIMITS["rest_speed_m_s"])
    elif case.friction == 0:
        error = float(np.max(np.abs(archive["velocity"][:, 0] - case.initial_speed)))
        metrics["max_velocity_error_m_s"] = error
        checks["frictionless_motion_preserved"] = error < LIMITS["frictionless_velocity_error_m_s"]
    else:
        reference = case.initial_speed**2 / (2 * case.friction * case.gravity)
        metrics["coulomb_stop_distance_m"] = reference
        checks["sliding_distance_matches_reference"] = abs(distance - reference) < max(
            LIMITS["slide_distance_absolute_error_m"], LIMITS["slide_distance_relative_error"] * reference,
        )
        checks["stopped"] = metrics["final_speed_m_s"] < LIMITS["slide_final_speed_m_s"]
    return {"passed": all(checks.values()), "checks": checks, "metrics": metrics}


def run(case: ContactCase, output: Path, worker_timeout: float) -> dict:
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.entities import EntityStatePatch, SceneResetRequest
    from unisim.factory import create_backend

    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve()
    (output / "source.py").write_bytes(source.read_bytes())
    receipt = {"case": asdict(case), "limits": LIMITS, "source_sha256": digest(source),
               "unisim_version": version("unisim-core"), "host": platform.platform(),
               "geometry": "analytic box primitives; no SDF qualification",
               "contact_measurement": "box body-net force; table is the only other collision body",
               "status": "preparing"}
    write_json(output / "run.json", receipt)
    backend = None
    samples: list[tuple] = []
    initial_pose = np.empty(0)
    preparation_start = time.perf_counter()
    result = {"passed": False, "checks": {}, "metrics": {}}
    try:
        runtime = resolve_isaacsim_runtime()
        worker_metadata = subprocess.run(
            [str(runtime.python), "-c", "import importlib.metadata as m,json,sys; "
             "print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in "
             "['isaacsim','isaacsim-kernel','isaaclab','torch']}}))"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        receipt["worker"] = json.loads(worker_metadata.stdout)
        scene = create_scene(case, output / "scene")
        receipt["assets"] = {p.name: digest(p) for p in (output / "scene").glob("*.xml")}
        backend = create_backend(
            "isaacsim", scene, num_envs=1, sim_dt=case.timestep,
            isaacsim_worker_timeout_s=worker_timeout,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_contact_offset=0.001, isaacsim_rest_offset=0.0,
        )
        backend.materialize()
        write_json(output / "import-report.json", backend.get_import_report().to_dict())
        write_json(output / "capabilities.json", backend.get_capabilities().to_dict())
        write_json(output / "layout.json", backend.get_scene_layout().to_dict())
        controls = np.zeros((1, backend.num_actuators), dtype=np.float32)
        for _ in range(round(case.settle / case.timestep)):
            backend.step(controls)
        state = backend.get_entity_state("box")
        initial_pose = state["root_pose"][0].copy()
        if case.initial_speed:
            velocity = np.zeros((1, 6), dtype=np.float32)
            velocity[0, 0] = case.initial_speed
            backend.reset_entities(SceneResetRequest(
                env_ids=(0,), patches=(EntityStatePatch("box", root_velocity=velocity),),
            ))
        receipt["preparation_seconds"] = time.perf_counter() - preparation_start
        receipt["status"] = "running"
        receipt["geom_friction_readback"] = backend.get_geom_friction().tolist()
        receipt["body_mass_readback"] = backend.get_body_mass().tolist()
        write_json(output / "run.json", receipt)
        start = time.perf_counter()
        for step in range(round(case.duration / case.timestep)):
            backend.step(controls)
            state = backend.get_entity_state("box")
            samples.append(((step + 1) * case.timestep, state["root_pose"][0].copy(),
                            state["root_velocity"][0].copy(), backend.get_sensor_data("box_force")[0].copy()))
            if not all(np.isfinite(value).all() for value in samples[-1][1:]):
                raise RuntimeError("Non-finite native observation")
        receipt["step_and_observation_seconds"] = time.perf_counter() - start
        receipt["status"] = "completed"
    except Exception:
        receipt["status"] = "error"
        receipt["error"] = traceback.format_exc()
    finally:
        if backend is not None:
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:
                receipt["cleanup_error"] = traceback.format_exc()
        archive = {"time": np.array([s[0] for s in samples]),
                   "pose": np.array([s[1] for s in samples]).reshape(-1, 7),
                   "velocity": np.array([s[2] for s in samples]).reshape(-1, 6),
                   "force": np.array([s[3] for s in samples]).reshape(-1, 3),
                   "initial_pose": initial_pose}
        np.savez_compressed(output / "states.npz", **archive)
        receipt["source_unchanged"] = digest(source) == receipt["source_sha256"]
        receipt["assets_unchanged"] = all(
            digest(output / "scene" / name) == expected
            for name, expected in receipt.get("assets", {}).items()
        )
        receipt["archive_sha256"] = digest(output / "states.npz")
        write_json(output / "run.json", receipt)
        result = verify(output)
    return result


def verify(output: Path) -> dict:
    """Rescore immutable observations without constructing a physics backend."""
    receipt = json.loads((output / "run.json").read_text())
    case = ContactCase(**receipt["case"])
    with np.load(output / "states.npz", allow_pickle=False) as saved:
        result = score(case, dict(saved))
    result["checks"].update(
        native_run_completed=receipt["status"] == "completed",
        clean_shutdown="cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True,
        source_snapshot_matches=digest(output / "source.py") == receipt["source_sha256"],
        recorded_assets_unchanged=receipt.get("assets_unchanged") is True,
        asset_files_match=bool(receipt.get("assets")) and all(
            digest(output / "scene" / name) == expected for name, expected in receipt.get("assets", {}).items()
        ),
        exact_archive_hash=digest(output / "states.npz") == receipt["archive_sha256"],
        frozen_engineering_limits=receipt["limits"] == LIMITS,
    )
    result["passed"] = all(result["checks"].values())
    result["verifier_sha256"] = digest(Path(__file__).resolve())
    write_json(output / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="Run actual Isaac Sim physics")
    run_parser.add_argument("--case", choices=CASES, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--worker-timeout", type=float, default=600)
    verify_parser = commands.add_parser("verify", help="Score a saved observation archive")
    verify_parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "verify":
        result = verify(args.directory.resolve())
    else:
        if not np.isfinite(args.worker_timeout) or args.worker_timeout <= 0:
            parser.error("Worker timeout must be finite and positive")
        result = run(CASES[args.case], args.output.resolve(), args.worker_timeout)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
