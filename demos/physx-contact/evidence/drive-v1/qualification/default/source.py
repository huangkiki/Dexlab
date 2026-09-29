"""Qualify a force-limited prismatic PhysX drive through the UniSim adapter."""

from __future__ import annotations

import argparse
from importlib.metadata import distribution, version
import json
from pathlib import Path
import subprocess
import traceback

import numpy as np

from dexlab.physx_baseline import digest, write_json


DT, DURATION = 0.001, 2.0
MASS, KP, KD, EFFORT = 0.1, 500.0, 10.0, 2.0
BASE_POSITION = np.array([-0.0152, 0.0, 0.2])
# Engineering tolerances frozen before qualification; not hardware accuracy claims.
LIMITS = {"position_m": 5e-5, "steady_velocity_m_s": 1e-4,
          "kinematic_position_m": 1e-6, "kinematic_velocity_m_s": 1e-6,
          "inferred_effort_n": 0.05}
PROTOCOL = "prismatic-drive-load-return-v1"


def commands(time_s: float) -> tuple[float, float]:
    target = 0.01 if time_s < 1.5 else 0.0
    load = -1.0 if 0.5 <= time_s < 1.0 else -3.0 if 1.0 <= time_s < 1.04 else 0.0
    return target, load


def create_scene(directory: Path):
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    directory.mkdir()
    source = directory / "fixture.xml"
    source.write_text(
        '<mujoco model="drive"><option gravity="0 0 0"/>'
        '<worldbody><body name="base">'
        '<inertial pos="0 0 0" mass="0.1" diaginertia="0.001 0.001 0.001"/>'
        '<body name="pad"><inertial pos="0 0 0" mass="0.1" '
        'diaginertia="0.000074166667 0.000054166667 0.000021666667"/>'
        '<joint name="slide" type="slide" axis="1 0 0" range="-0.02 0.02" damping="0"/>'
        '<geom name="surface" type="box" size="0.005 0.025 0.04" friction="0 0 0"/>'
        '</body></body></worldbody><actuator><position name="drive" joint="slide" '
        'kp="500" kv="10" ctrlrange="-0.02 0.02" forcerange="-2 2"/>'
        '</actuator></mujoco>\n'
    )
    return SceneCfg(entity_assets=(SceneEntitySpec(
        "fixture", ModelSourceDescriptor(str(source.resolve())), kind="articulation",
        root_mode="fixed", gravity_disabled=True,
        initial_state=EntityInitialState(position=tuple(BASE_POSITION)),
    ),))


def score(archive: dict[str, np.ndarray]) -> dict:
    """Use actual state, static compliance and a short analytically saturated interval."""
    count = round(DURATION / DT)
    shapes = {"time": (count,), "target": (count,), "external_load": (count,),
              "q": (count,), "dq": (count,), "position": (count, 2, 3),
              "velocity": (count, 2, 3), "quaternion": (count, 2, 4)}
    checks = {"complete_finite_record": all(
        key in archive and archive[key].shape == shape and np.isfinite(archive[key]).all()
        for key, shape in shapes.items()
    )}
    metrics = {}
    if not checks["complete_finite_record"]:
        return {"passed": False, "checks": checks, "metrics": metrics}
    times, q, dq = archive["time"], archive["q"], archive["dq"]
    expected = np.array([commands(step * DT) for step in range(count)])
    checks.update(
        complete_time_grid=bool(np.allclose(times, np.arange(1, count + 1)*DT, rtol=0, atol=1e-10)),
        declared_commands_only=bool(np.allclose(archive["target"], expected[:, 0], rtol=0, atol=1e-9)
                                    and np.array_equal(archive["external_load"], expected[:, 1])),
    )
    if not checks["complete_time_grid"]:
        return {"passed": False, "checks": checks, "metrics": metrics}
    position, velocity = archive["position"], archive["velocity"]
    expected_pose = np.tile(BASE_POSITION, (count, 2, 1))
    expected_pose[:, 1, 0] += q
    expected_velocity = np.zeros_like(velocity)
    expected_velocity[:, 1, 0] = dq
    position_error = float(np.abs(position - expected_pose).max())
    velocity_error = float(np.abs(velocity - expected_velocity).max())
    checks.update(
        fixed_base_and_prismatic_pose=position_error < LIMITS["kinematic_position_m"],
        body_joint_velocity_agree=velocity_error < LIMITS["kinematic_velocity_m_s"],
        no_body_rotation=bool(np.max(np.abs(archive["quaternion"][:, :, 1:])) < 1e-6
                              and np.allclose(np.linalg.norm(archive["quaternion"], axis=-1), 1, atol=1e-6)),
        away_from_joint_limits=bool(np.max(np.abs(q)) < 0.019),
    )
    metrics.update(body_joint_position_error_m=position_error, body_joint_velocity_error_m_s=velocity_error)
    for name, start, end, target in (("unloaded", .3, .5, .01),
                                    ("loaded", .8, 1., .01 - 1./KP),
                                    ("returned", 1.8, 2., 0.)):
        window = (times > start) & (times <= end)
        error = float(np.max(np.abs(q[window] - target)))
        speed = float(np.max(np.abs(dq[window])))
        metrics.update({f"{name}_position_error_m": error, f"{name}_max_speed_m_s": speed})
        checks[f"{name}_equilibrium"] = error < LIMITS["position_m"]
        checks[f"{name}_stationary_velocity"] = speed < LIMITS["steady_velocity_m_s"]
    loaded = (times > .8) & (times <= 1.)
    metrics["loaded_integrated_velocity_m"] = float(np.trapezoid(dq[loaded], times[loaded]))
    metrics["loaded_position_change_m"] = float(q[loaded][-1] - q[loaded][0])
    pulse = (times > 1.01) & (times <= 1.035)
    acceleration = float(np.polyfit(times[pulse], dq[pulse], 1)[0])
    inferred_effort = MASS * acceleration + 3.0
    metrics.update(pulse_acceleration_m_s2=acceleration, velocity_inferred_drive_effort_n=inferred_effort)
    checks["overload_matches_force_limit"] = abs(inferred_effort - EFFORT) < LIMITS["inferred_effort_n"]
    return {"passed": bool(all(checks.values())), "checks": checks, "metrics": metrics}


def run(output: Path, substep_forces: bool) -> dict:
    from unisim.backend.isaacsim import backend as adapter, physx_solver, scene_worker
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.factory import create_backend
    from unisim import factory

    output.mkdir(parents=True, exist_ok=False)
    snapshots = {"source.py": Path(__file__), "unisim-factory.py": Path(factory.__file__),
                 "unisim-backend.py": Path(adapter.__file__), "unisim-physx-solver.py": Path(physx_solver.__file__),
                 "unisim-scene-worker.py": Path(scene_worker.__file__)}
    hashes = {name: digest(path) for name, path in snapshots.items()}
    for name, path in snapshots.items():
        (output / name).write_bytes(path.read_bytes())
    receipt = {"protocol": PROTOCOL, "limits": LIMITS, "status": "preparing",
               "external_forces_every_iteration": substep_forces, "source_sha256": hashes,
               "unisim_version": version("unisim-core"),
               "unisim_install_origin": distribution("unisim-core").read_text("direct_url.json"),
               "scope": "one prismatic drive; no contacts, robot grasp or measured actuator force"}
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
            "isaacsim", create_scene(output / "scene"), num_envs=1, sim_dt=DT,
            isaacsim_worker_timeout_s=600, isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_external_forces_every_iteration=substep_forces,
        )
        backend.materialize()
        write_json(output / "layout.json", backend.get_scene_layout().to_dict())
        write_json(output / "import-report.json", backend.get_import_report().to_dict())
        if backend.num_actuators != 1:
            raise RuntimeError("Expected exactly one position drive")
        ids = backend.get_body_ids(["fixture/base", "fixture/pad"])
        receipt.update(status="running", body_mass_readback=backend.get_body_mass().tolist())
        write_json(output / "run.json", receipt)
        for step in range(round(DURATION / DT)):
            target, load = commands(step * DT)
            force = np.zeros((1, 2, 3), dtype=np.float32)
            force[0, 1, 0] = load
            backend.apply_body_force(ids, force)
            backend.step(np.array([[target]], dtype=np.float32))
            rows.append({"time": (step + 1)*DT, "target": target, "external_load": load,
                         "q": float(backend.get_dof_pos()[0, 0]), "dq": float(backend.get_dof_vel()[0, 0]),
                         "position": backend.get_body_pos_w(ids)[0].copy(),
                         "velocity": backend.get_body_lin_vel_w(ids)[0].copy(),
                         "quaternion": backend.get_body_quat_w(ids)[0].copy()})
        receipt["status"] = "completed"
    except Exception:
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:
                receipt["cleanup_error"] = traceback.format_exc()
        arrays = {key: np.array([row[key] for row in rows]) for key in rows[0]} if rows else {}
        np.savez_compressed(output / "states.npz", **arrays)
        receipt["source_unchanged"] = all(digest(path) == hashes[name] for name, path in snapshots.items())
        receipt["artifact_sha256"] = {str(p.relative_to(output)): digest(p) for p in output.rglob("*")
                                      if p.is_file() and p.name != "run.json"}
        write_json(output / "run.json", receipt)
    return verify(output)


def verify(output: Path) -> dict:
    receipt = json.loads((output / "run.json").read_text())
    with np.load(output / "states.npz", allow_pickle=False) as saved:
        result = score(dict(saved))
    hashes = receipt["artifact_sha256"]
    required = {"states.npz", "source.py", "unisim-factory.py", "unisim-backend.py",
                "unisim-physx-solver.py", "unisim-scene-worker.py", "scene/fixture.xml",
                "layout.json", "import-report.json"}
    matched = required <= hashes.keys() and all(
        (output / name).is_file() and digest(output / name) == sha for name, sha in hashes.items())
    layout = json.loads((output / "layout.json").read_text()) if matched else {}
    report = json.loads((output / "import-report.json").read_text()) if matched else {}
    fields = {field["field"]: field for field in report.get("fields", [])}
    option = fields.get("external_forces_every_iteration", {})
    masses = np.asarray(receipt.get("body_mass_readback", []))
    result["checks"].update(
        frozen_protocol=receipt["protocol"] == PROTOCOL and receipt["limits"] == LIMITS,
        archive_hashes_match=matched,
        native_run_completed=receipt["status"] == "completed" and "cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True and all(
            (output / name).is_file() and digest(output / name) == sha
            for name, sha in receipt["source_sha256"].items()),
        native_option_readback=option.get("effective") is receipt["external_forces_every_iteration"]
                               and any(p["kind"] == "engine_readback" for p in option.get("provenance", [])),
        fixture_topology=(layout.get("nq"), layout.get("nv"), layout.get("nu"), layout.get("nbody")) == (1, 1, 1, 3),
        native_mass_matches=bool(masses.shape == (1, 3) and np.allclose(masses, [[0, .1, .1]], atol=1e-7)),
    )
    result["passed"] = bool(all(result["checks"].values()))
    result["verifier_sha256"] = digest(Path(__file__))
    write_json(output / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--force-timing", choices=("default", "substep"), required=True)
    check = sub.add_parser("verify")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = run(args.output.resolve(), args.force_timing == "substep") if args.command == "run" else verify(args.directory.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
