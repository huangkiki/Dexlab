"""Force-driven PhysX pinch, overload and release qualification.

An ideal prismatic fixture isolates contact physics from robot actuator tuning.
The floating object receives gravity compensation only during preparation.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from importlib.metadata import distribution, version
import json
from pathlib import Path
import subprocess
import time
import traceback

import numpy as np

from dexlab.physx_baseline import digest, write_json


@dataclass(frozen=True)
class PinchCase:
    name: str
    mass: float
    friction: float
    should_hold: bool


CASES = {
    "hold": PinchCase("hold", 0.2, 0.3, True),
    "overload": PinchCase("overload", 0.5, 0.3, False),
    "frictionless": PinchCase("frictionless", 0.2, 0.0, False),
}
DT, DURATION, GRAVITY = 0.001, 3.5, 9.81
PREPARE_END, RELEASE_START, PAD_FORCE = 0.5, 2.5, 4.0
PAD_HALF_SIZE = np.array([0.005, 0.025, 0.04])
OBJECT_HALF_SIZE = np.array([0.01, 0.01, 0.03])
BODY_NAMES = ("left/pad", "right/pad", "object/body")
# Frozen after development probes, before new qualification runs. Not hardware limits.
LIMITS = {
    "penetration_m": 0.001,
    "hold_drift_m": 0.001,
    "hold_speed_m_s": 0.005,
    "normal_load_relative_error": 0.05,
    "minimum_hold_normal_force_n": 0.1,
    "minimum_drop_m": 0.05,
    "released_force_n": 0.01,
    "freefall_acceleration_relative_error": 0.02,
    "freefall_velocity_fit_error_m_s": 0.01,
}
REPORT_FILES = ("layout.json", "import-report.json", "capabilities.json")


def commands(case: PinchCase, time_s: float) -> np.ndarray:
    """World-frame COM forces; no position target or attachment on the object."""
    force = np.zeros((3, 3), dtype=np.float32)
    normal = PAD_FORCE if time_s < RELEASE_START else -2.0
    force[0, 0], force[1, 0] = normal, -normal
    if time_s < PREPARE_END:
        force[2, 2] = case.mass * GRAVITY
    return force


def create_scene(case: PinchCase, directory: Path):
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    directory.mkdir(parents=True, exist_ok=False)
    option = f'<option gravity="0 0 -{GRAVITY}" timestep="{DT}"/>'
    entities = []
    for name, direction in (("left", 1), ("right", -1)):
        source = directory / f"{name}.xml"
        source.write_text(
            f'<mujoco model="{name}">{option}<worldbody><body name="base">'
            '<inertial pos="0 0 0" mass="0.1" diaginertia="0.001 0.001 0.001"/>'
            '<body name="pad"><inertial pos="0 0 0" mass="0.1" '
            'diaginertia="0.000074166667 0.000054166667 0.000021666667"/>'
            f'<joint name="slide" type="slide" axis="{direction} 0 0" '
            'range="-0.02 0.02" damping="0"/>'
            f'<geom name="surface" type="box" size="0.005 0.025 0.04" '
            f'friction="{case.friction} 0 0" condim="3"/>'
            '</body></body></worldbody></mujoco>\n'
        )
        entities.append(SceneEntitySpec(
            name, ModelSourceDescriptor(str(source.resolve())), kind="articulation",
            root_mode="fixed", gravity_disabled=True,
            initial_state=EntityInitialState(position=(-direction * 0.0152, 0, 0.2)),
        ))
    source = directory / "object.xml"
    inertia = case.mass / 3 * np.array([0.01**2 + 0.03**2] * 2 + [2 * 0.01**2])
    source.write_text(
        f'<mujoco model="object">{option}<worldbody><body name="body"><freejoint/>'
        f'<inertial pos="0 0 0" mass="{case.mass}" diaginertia="{" ".join(map(str, inertia))}"/>'
        f'<geom name="surface" type="box" size="0.01 0.01 0.03" '
        f'friction="{case.friction} 0 0" condim="3"/>'
        '</body></worldbody></mujoco>\n'
    )
    entities.append(SceneEntitySpec(
        "object", ModelSourceDescriptor(str(source.resolve())), kind="rigid", root_mode="floating",
        initial_state=EntityInitialState(position=(0, 0, 0.2)),
    ))
    sensors = directory / "sensors.xml"
    sensors.write_text('<mujoco><sensor>' + "".join(
        f'<contact name="{side}_force" geom1="object/surface" geom2="{side}/surface" '
        'data="force" reduce="netforce"/>' for side in ("left", "right")
    ) + '</sensor></mujoco>\n')
    return SceneCfg(entity_assets=tuple(entities), fragment_files=[str(sensors.resolve())])


def rotation_matrices(quaternion: np.ndarray) -> np.ndarray:
    if not np.allclose(np.linalg.norm(quaternion, axis=-1), 1, atol=1e-5, rtol=0):
        raise ValueError("Non-unit quaternion")
    w, x, y, z = np.moveaxis(quaternion, -1, 0)
    return np.stack((
        1 - 2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y),
        2*(x*y+w*z), 1 - 2*(x*x+z*z), 2*(y*z-w*x),
        2*(x*z-w*y), 2*(y*z+w*x), 1 - 2*(x*x+y*y),
    ), axis=-1).reshape(quaternion.shape[:-1] + (3, 3))


def box_overlap(position_a, rotation_a, half_a, position_b, rotation_b, half_b):
    """OBB overlap depth using the 15 separating axes; zero for separated boxes."""
    axes_a, axes_b = np.swapaxes(rotation_a, -1, -2), np.swapaxes(rotation_b, -1, -2)
    cross = np.cross(axes_a[:, :, None, :], axes_b[:, None, :, :]).reshape(-1, 9, 3)
    axes = np.concatenate((axes_a, axes_b, cross), axis=1)
    lengths = np.linalg.norm(axes, axis=-1)
    valid = lengths > 1e-7
    axes = axes / np.maximum(lengths[..., None], 1e-7)
    radius_a = (np.abs(np.einsum("nki,nij->nkj", axes, rotation_a)) * half_a).sum(axis=-1)
    radius_b = (np.abs(np.einsum("nki,nij->nkj", axes, rotation_b)) * half_b).sum(axis=-1)
    distance = np.abs(np.einsum("nki,ni->nk", axes, position_b-position_a))
    overlap = np.where(valid, radius_a + radius_b - distance, np.inf)
    return np.maximum(overlap.min(axis=1), 0)


def score(case: PinchCase, archive: dict[str, np.ndarray]) -> dict:
    count = round(DURATION / DT)
    shapes = {"time": (count,), "position": (count, 3, 3), "quaternion": (count, 3, 4),
              "velocity": (count, 3, 3), "angular_velocity": (count, 3, 3),
              "q": (count, 2), "dq": (count, 2), "external_force": (count, 3, 3),
              "contact_normal_force": (count, 2, 3)}
    complete = all(k in archive and archive[k].shape == shape for k, shape in shapes.items())
    finite = complete and all(np.isfinite(archive[k]).all() for k in shapes)
    checks = {"complete_finite_archive": bool(finite)}
    metrics = {}
    if not finite:
        return {"passed": False, "checks": checks, "metrics": metrics}
    times = np.arange(1, count + 1) * DT
    checks["complete_time_grid"] = bool(np.allclose(archive["time"], times, atol=1e-10, rtol=0))
    expected_forces = np.array([commands(case, step * DT) for step in range(count)])
    checks["declared_external_forces_only"] = bool(np.array_equal(archive["external_force"], expected_forces))
    try:
        rotations = rotation_matrices(archive["quaternion"])
    except ValueError:
        checks["unit_quaternions"] = False
        return {"passed": False, "checks": checks, "metrics": metrics}
    checks["unit_quaternions"] = True
    positions, velocity = archive["position"], archive["velocity"]
    expected_pads = np.zeros((count, 2, 3))
    expected_pads[:, :, 0] = [-0.0152, 0.0152] + archive["q"] * [1, -1]
    expected_pads[:, :, 2] = 0.2
    checks["actual_prismatic_fixture"] = bool(
        np.allclose(positions[:, :2], expected_pads, atol=1e-6, rtol=0)
        and np.allclose(rotations[:, :2], np.eye(3), atol=1e-5, rtol=0))
    normal = archive["contact_normal_force"]
    penetration = max(float(box_overlap(
        positions[:, i], rotations[:, i], PAD_HALF_SIZE,
        positions[:, 2], rotations[:, 2], OBJECT_HALF_SIZE,
    ).max()) for i in (0, 1))
    checks["bounded_object_pad_penetration"] = penetration < LIMITS["penetration_m"]
    load_window = (times > 0.52) & (times <= 0.60)
    measured = normal[load_window, :, 0].mean(axis=0) * [1, -1]
    checks["normal_load_matches_command"] = bool(
        np.all(np.abs(measured / PAD_FORCE - 1) < LIMITS["normal_load_relative_error"]))
    metrics.update(max_object_pad_penetration_m=penetration, normal_load_n=measured.tolist(),
                   nominal_friction_capacity_n=float(case.friction * measured.sum()),
                   weight_n=case.mass * GRAVITY)
    hold = (times > 0.7) & (times <= RELEASE_START)
    origin = positions[round(PREPARE_END / DT)-1, 2]
    if case.should_hold:
        drift = float(np.linalg.norm(positions[hold, 2] - origin, axis=1).max())
        speed = float(np.linalg.norm(velocity[hold, 2], axis=1).max())
        checks.update(holds_load=drift < LIMITS["hold_drift_m"],
                      bounded_hold_speed=speed < LIMITS["hold_speed_m_s"],
                      continuous_normal_support=bool(np.all(
                          normal[hold, :, 0] * [1, -1] > LIMITS["minimum_hold_normal_force_n"])))
        metrics.update(hold_drift_m=drift, hold_max_speed_m_s=speed)
    else:
        drop = float(origin[2] - positions[round(0.7 / DT)-1, 2, 2])
        checks["negative_control_drops"] = drop > LIMITS["minimum_drop_m"]
        metrics["drop_after_200ms_m"] = drop
    released = times > 2.8
    release_force = float(np.linalg.norm(normal[released], axis=-1).max())
    slope, intercept = np.polyfit(times[released], velocity[released, 2, 2], 1)
    fit_error = float(np.abs(velocity[released, 2, 2] - slope*times[released] - intercept).max())
    release_drop = float(positions[round(RELEASE_START / DT)-1, 2, 2] - positions[-1, 2, 2])
    checks.update(
        fully_released=release_force < LIMITS["released_force_n"] and release_drop > LIMITS["minimum_drop_m"],
        freefall_acceleration=bool(abs(slope / -GRAVITY - 1) < LIMITS["freefall_acceleration_relative_error"]),
        freefall_velocity_fit=fit_error < LIMITS["freefall_velocity_fit_error_m_s"],
    )
    metrics.update(released_normal_force_n=release_force, released_acceleration_m_s2=float(slope),
                   released_velocity_fit_error_m_s=fit_error, release_drop_m=release_drop)
    return {"passed": bool(all(checks.values())), "checks": checks, "metrics": metrics}


def run(case: PinchCase, output: Path) -> dict:
    from unisim.backend.isaacsim import scene_worker
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.factory import create_backend

    output.mkdir(parents=True, exist_ok=False)
    source, adapter = Path(__file__).resolve(), Path(scene_worker.__file__).resolve()
    for path, name in ((source, "source.py"), (adapter, "unisim-scene-worker.py")):
        (output / name).write_bytes(path.read_bytes())
    receipt = {"case": asdict(case), "limits": LIMITS, "source_sha256": digest(source),
               "adapter_source_sha256": digest(adapter), "unisim_version": version("unisim-core"),
               "unisim_install_origin": distribution("unisim-core").read_text("direct_url.json"),
               "protocol": "ideal-force-prismatic-box-v1", "status": "preparing",
               "geometry": "analytic boxes; not SDF, cylinder or robot qualification",
               "contact_measurement": "world-frame normal forces only; tangential force not observed"}
    write_json(output / "run.json", receipt)
    backend, rows = None, []
    try:
        runtime = resolve_isaacsim_runtime()
        metadata = subprocess.run(
            [str(runtime.python), "-c", "import importlib.metadata as m,json,sys; "
             "print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in "
             "['isaacsim','isaacsim-kernel','isaaclab','torch']}}))"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        receipt["worker"] = json.loads(metadata.stdout)
        backend = create_backend(
            "isaacsim", create_scene(case, output / "scene"), num_envs=1, sim_dt=DT,
            isaacsim_worker_timeout_s=600, isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_contact_offset=0.001, isaacsim_rest_offset=0.0,
        )
        backend.materialize()
        for name, report in (("layout.json", backend.get_scene_layout()),
                             ("import-report.json", backend.get_import_report()),
                             ("capabilities.json", backend.get_capabilities())):
            write_json(output / name, report.to_dict())
        ids = backend.get_body_ids(list(BODY_NAMES))
        if backend.num_actuators != 0:
            raise RuntimeError("This force fixture must have no position actuators")
        controls = np.zeros((1, 0), dtype=np.float32)
        receipt.update(status="running", body_mass_readback=backend.get_body_mass().tolist(),
                       geom_friction_readback=backend.get_geom_friction().tolist())
        write_json(output / "run.json", receipt)
        start = time.perf_counter()
        for step in range(round(DURATION / DT)):
            forces = commands(case, step * DT)
            backend.apply_body_force(ids, forces[None])
            backend.step(controls)
            row = {"time": (step+1)*DT, "external_force": forces.copy(),
                   "contact_normal_force": np.array([backend.get_sensor_data(f"{side}_force")[0]
                                                     for side in ("left", "right")])}
            for key, method in (("position", backend.get_body_pos_w), ("quaternion", backend.get_body_quat_w),
                                ("velocity", backend.get_body_lin_vel_w), ("angular_velocity", backend.get_body_ang_vel_w)):
                row[key] = method(ids)[0].copy()
            row.update(q=backend.get_dof_pos()[0].copy(), dq=backend.get_dof_vel()[0].copy())
            rows.append(row)
            if not all(np.isfinite(value).all() for value in row.values()):
                raise RuntimeError("Non-finite native observation")
        receipt.update(status="completed", step_and_observation_seconds=time.perf_counter()-start)
    except Exception:
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:
                receipt["cleanup_error"] = traceback.format_exc()
        archive = {k: np.array([row[k] for row in rows]) for k in rows[0]} if rows else {}
        np.savez_compressed(output / "states.npz", **archive)
        receipt["source_unchanged"] = digest(source) == receipt["source_sha256"]
        receipt["adapter_unchanged"] = digest(adapter) == receipt["adapter_source_sha256"]
        receipt["artifact_sha256"] = {
            str(p.relative_to(output)): digest(p) for p in output.rglob("*")
            if p.is_file() and p.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    return verify(output)


def verify(output: Path) -> dict:
    receipt = json.loads((output / "run.json").read_text())
    case = PinchCase(**receipt["case"])
    with np.load(output / "states.npz", allow_pickle=False) as saved:
        result = score(case, dict(saved))
    hashes = receipt["artifact_sha256"]
    matched = all((output / name).is_file() and digest(output / name) == sha for name, sha in hashes.items())
    required = {"states.npz", "source.py", "unisim-scene-worker.py", *REPORT_FILES,
                "scene/left.xml", "scene/right.xml", "scene/object.xml", "scene/sensors.xml"}
    layout = json.loads((output / "layout.json").read_text()) if matched and required <= hashes.keys() else {}
    topology = (layout.get("nu") == 0 and layout.get("nbody") == 6 and layout.get("ngeom") == 3
                and [(e.get("name"), e.get("root_mode"), e.get("body_ids")) for e in layout.get("entities", [])]
                == [("left", "fixed", [1, 2]), ("right", "fixed", [3, 4]), ("object", "floating", [5])])
    mass, friction = np.asarray(receipt.get("body_mass_readback", [])), np.asarray(receipt.get("geom_friction_readback", []))
    result["checks"].update(
        frozen_case=case == CASES.get(case.name), frozen_limits=receipt["limits"] == LIMITS,
        archive_hashes_match=matched and required <= hashes.keys(),
        native_run_completed=receipt["status"] == "completed" and "cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True and digest(output / "source.py") == receipt["source_sha256"],
        adapter_unchanged=receipt.get("adapter_unchanged") is True and digest(output / "unisim-scene-worker.py") == receipt["adapter_source_sha256"],
        declared_fixture_topology=topology,
        native_mass_matches=bool(mass.shape == (1, 6) and np.allclose(mass, [[0, .1, .1, .1, .1, case.mass]], atol=1e-7, rtol=1e-6)),
        native_friction_matches=bool(friction.shape == (1, 3, 3) and np.allclose(friction, [[[case.friction, case.friction, 0]]*3], atol=1e-7, rtol=1e-6)),
    )
    result["passed"] = bool(all(result["checks"].values()))
    result["verifier_sha256"] = digest(Path(__file__).resolve())
    write_json(output / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--case", choices=CASES, required=True)
    execute.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = run(CASES[args.case], args.output.resolve()) if args.command == "run" else verify(args.directory.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
