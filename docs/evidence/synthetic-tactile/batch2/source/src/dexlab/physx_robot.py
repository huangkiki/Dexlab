"""Prepare and qualify the actual OpenArm/Wuji articulation before contact tests.

This stage disables contacts and gravity. It does not qualify SDF collisions,
loaded grasping, hardware actuator limits, or equality of native drive dynamics.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

from dexlab.physx_baseline import digest, write_json
from dexlab.robot_transfer import DT, prepare

DURATION = 4.0
PROTOCOL = "openarm-wuji-unloaded-articulation-v1"
# Engineering qualification bounds; frozen before the qualification batch.
LIMITS = {
    "fk_position_m": 1e-4,
    "fk_rotation_rad": 1e-3,
    "return_position_rad": 1e-3,
    "return_velocity_rad_s": 1e-3,
    "minimum_excursion_rad": 0.01,
    "joint_limit_rad": 1e-4,
}


def excitation(home, ranges):
    margin = np.stack((home - ranges[:, 0], ranges[:, 1] - home))
    if np.any(margin < 0):
        raise ValueError("Initial posture lies outside joint limits")
    # Excite toward the roomier side, including joints starting at a limit.
    return np.where(margin[1] >= margin[0], 1.0, -1.0) * np.minimum(
        0.03, 0.25 * margin.max(axis=0)
    )


def target_at(time, home, amplitude):
    return home + amplitude * np.sin(np.pi * time) ** 2 if time < 2 else home.copy()


def run(source_run: Path, output: Path) -> dict:
    from importlib.metadata import version

    from unisim.backend.isaacsim import backend as adapter
    from unisim.backend.isaacsim import physx_solver, scene_worker
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.backend.subprocess_ipc import scene_materialization
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.factory import create_backend
    from unisim.scene import SceneCfg

    from dexlab import robot_transfer

    output.mkdir(parents=True, exist_ok=False)
    paths = {
        "source.py": Path(__file__),
        "robot_transfer.py": Path(robot_transfer.__file__),
        "unisim-backend.py": Path(adapter.__file__),
        "unisim-physx-solver.py": Path(physx_solver.__file__),
        "unisim-scene-worker.py": Path(scene_worker.__file__),
        "unisim-scene-materialization.py": Path(scene_materialization.__file__),
    }
    source_hashes = {name: digest(path) for name, path in paths.items()}
    for name, path in paths.items():
        shutil.copyfile(path, output / name)
    receipt = {
        "status": "preparing",
        "source_sha256": digest(Path(__file__)),
        "dt": DT,
        "dependency_sha256": source_hashes,
        "versions": {
            name: version(name) for name in ("mujoco", "unisim-core", "numpy")
        },
        "duration": DURATION,
        "protocol": PROTOCOL,
        "limits": LIMITS,
        "scope": "54-DOF robot, no contact or gravity; no SDF/grasp claim",
    }
    write_json(output / "run.json", receipt)
    backend, rows = None, []
    try:
        runtime = resolve_isaacsim_runtime()
        identity_script = (
            "import importlib.metadata as m,json,sys; "
            "print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in "
            "['isaacsim','isaacsim-kernel','isaaclab','torch']}}))"
        )
        metadata = subprocess.run(
            [str(runtime.python), "-c", identity_script],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        receipt["worker"] = json.loads(metadata.stdout)
        transfer = prepare(source_run, output / "model")
        filename = output / "model/robot.xml"
        reference = mujoco.MjModel.from_xml_path(str(output / "model/kinematics.xml"))
        data = mujoco.MjData(reference)
        robot = ET.parse(filename).find("./worldbody/body")
        scene = SceneCfg(
            entity_assets=(
                SceneEntitySpec(
                    "robot",
                    ModelSourceDescriptor(str(filename)),
                    kind="articulation",
                    root_mode="fixed",
                    initial_state=EntityInitialState(
                        position=tuple(map(float, robot.get("pos").split())),
                        quaternion=tuple(map(float, robot.get("quat").split())),
                    ),
                    collision_enabled=False,
                    gravity_disabled=True,
                ),
            ),
            default_keyframe_name="home",
        )
        backend = create_backend(
            "isaacsim",
            scene,
            num_envs=1,
            sim_dt=DT,
            isaacsim_worker_timeout_s=600,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
        )
        backend.materialize()
        layout = backend.get_scene_layout().to_dict()
        write_json(output / "layout.json", layout)
        write_json(output / "import-report.json", backend.get_import_report().to_dict())
        entity = layout["entities"][0]
        names = entity["body_names"]
        ids = backend.get_body_ids(["robot/" + name for name in names])
        reference_ids = [reference.body(name).id for name in names]
        joint_names = transfer["joint_names"]
        backend_names = backend.get_actuator_joint_names()
        if backend_names != tuple("robot/" + name for name in joint_names):
            raise ValueError(f"Unexpected actuator ordering: {backend_names}")
        home = np.asarray(transfer["home"])
        amplitude = excitation(home, reference.jnt_range)
        receipt.update(
            status="running",
            amplitude_rad=amplitude.tolist(),
            body_mass=backend.get_body_mass().tolist(),
        )
        write_json(output / "run.json", receipt)
        for step in range(round(DURATION / DT)):
            time = step * DT
            # Smooth bounded exercise of all 54 joints, then return and settle.
            target = target_at(time, home, amplitude)
            backend.step(target[None].astype(np.float32))
            q, dq = backend.get_dof_pos()[0].copy(), backend.get_dof_vel()[0].copy()
            data.qpos[:], data.qvel[:] = q, dq
            mujoco.mj_forward(reference, data)
            rows.append(
                {
                    "time": (step + 1) * DT,
                    "target": target,
                    "q": q,
                    "dq": dq,
                    "position": backend.get_body_pos_w(ids)[0].copy(),
                    "quaternion": backend.get_body_quat_w(ids)[0].copy(),
                    "reference_position": data.xpos[reference_ids].copy(),
                    "reference_quaternion": data.xquat[reference_ids].copy(),
                }
            )
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 -- preserve native failure and close the worker.
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:  # noqa: BLE001 -- preserve native failure and close the worker.
                receipt["cleanup_error"] = traceback.format_exc()
        arrays = (
            {key: np.asarray([row[key] for row in rows]) for key in rows[0]}
            if rows
            else {}
        )
        np.savez_compressed(output / "states.npz", **arrays)
        receipt["source_unchanged"] = all(
            digest(path) == source_hashes[name] for name, path in paths.items()
        )
        receipt["artifact_sha256"] = {
            str(path.relative_to(output)): digest(path)
            for path in output.rglob("*")
            if path.is_file() and path.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    return verify(output)


def score(archive: dict[str, np.ndarray], model: mujoco.MjModel) -> dict:
    """Recompute FK from actual joint state; do not trust recorded reference poses."""
    count, joints, bodies = round(DURATION / DT), model.nq, model.nbody - 1
    shapes = {
        "time": (count,),
        "q": (count, joints),
        "dq": (count, joints),
        "target": (count, joints),
        "position": (count, bodies, 3),
        "quaternion": (count, bodies, 4),
    }
    checks = {
        "complete_finite_record": all(
            key in archive
            and archive[key].shape == shape
            and np.isfinite(archive[key]).all()
            for key, shape in shapes.items()
        )
    }
    metrics = {}
    if not checks["complete_finite_record"]:
        return {"passed": False, "checks": checks, "metrics": metrics}
    q, dq, time = archive["q"], archive["dq"], archive["time"]
    home = model.key_qpos[0]
    amplitude = excitation(home, model.jnt_range)
    expected = np.array([target_at(i * DT, home, amplitude) for i in range(count)])
    checks["complete_time_grid"] = bool(
        np.allclose(time, np.arange(1, count + 1) * DT, rtol=0, atol=1e-10)
    )
    checks["declared_targets"] = bool(
        np.allclose(archive["target"], expected, rtol=0, atol=1e-9)
    )
    checks["within_joint_limits"] = bool(
        np.all(q >= model.jnt_range[:, 0] - LIMITS["joint_limit_rad"])
        and np.all(q <= model.jnt_range[:, 1] + LIMITS["joint_limit_rad"])
    )
    norms = np.linalg.norm(archive["quaternion"].astype(float), axis=-1)
    checks["unit_quaternions"] = bool(np.allclose(norms, 1, rtol=0, atol=1e-5))
    if np.any(norms < 1e-12):
        return {"passed": False, "checks": checks, "metrics": metrics}
    data = mujoco.MjData(model)
    position_error = rotation_error = 0.0
    for index in range(count):
        data.qpos[:] = q[index]
        mujoco.mj_kinematics(model, data)
        position_error = max(
            position_error,
            float(
                np.linalg.norm(
                    archive["position"][index] - data.xpos[1:], axis=-1
                ).max()
            ),
        )
        measured = archive["quaternion"][index].astype(float) / norms[index, :, None]
        reference = data.xquat[1:]
        sign = np.where(np.sum(measured * reference, axis=-1) >= 0, 1, -1)
        distance = np.linalg.norm(measured * sign[:, None] - reference, axis=-1)
        rotation_error = max(
            rotation_error, float((4 * np.arcsin(np.clip(distance / 2, 0, 1))).max())
        )
    settled = time > 3.5
    if not checks["complete_time_grid"]:
        return {"passed": False, "checks": checks, "metrics": metrics}
    return_error = float(np.max(np.abs(q[settled] - home)))
    return_speed = float(np.max(np.abs(dq[settled])))
    minimum_excursion = float(np.ptp(q, axis=0).min())
    metrics.update(
        fk_max_position_error_m=position_error,
        fk_max_rotation_error_rad=rotation_error,
        return_max_position_error_rad=return_error,
        return_max_velocity_rad_s=return_speed,
        minimum_joint_excursion_rad=minimum_excursion,
        tracking_max_error_rad=float(np.abs(q - archive["target"]).max()),
    )
    checks.update(
        actual_joint_fk_position=position_error < LIMITS["fk_position_m"],
        actual_joint_fk_rotation=rotation_error < LIMITS["fk_rotation_rad"],
        return_to_initial_posture=return_error < LIMITS["return_position_rad"],
        settled_joint_velocity=return_speed < LIMITS["return_velocity_rad_s"],
        every_joint_exercised=minimum_excursion > LIMITS["minimum_excursion_rad"],
    )
    return {"passed": bool(all(checks.values())), "checks": checks, "metrics": metrics}


def verify(output: Path) -> dict:
    receipt = json.loads((output / "run.json").read_text())
    hashes = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        "source.py",
        "layout.json",
        "import-report.json",
        "model/robot.xml",
        "model/kinematics.xml",
        "model/model-transfer.json",
        "robot_transfer.py",
        "unisim-backend.py",
        "unisim-physx-solver.py",
        "unisim-scene-worker.py",
        "unisim-scene-materialization.py",
    }
    matched = required <= hashes.keys() and all(
        (output / name).is_file() and digest(output / name) == sha
        for name, sha in hashes.items()
    )
    result = {"passed": False, "checks": {}, "metrics": {}}
    if matched:
        model = mujoco.MjModel.from_xml_path(str(output / "model/kinematics.xml"))
        with np.load(output / "states.npz", allow_pickle=False) as states:
            result = score(dict(states), model)
        transfer = json.loads((output / "model/model-transfer.json").read_text())
        layout = json.loads((output / "layout.json").read_text())
        native = json.loads((output / "import-report.json").read_text())
        fields = {item["field"]: item for item in native["fields"]}
        mass = fields.get("body_mass", {})
        result["checks"].update(
            all_54_joints=(
                model.nq,
                model.nv,
                model.nu,
                layout["nq"],
                layout["nv"],
                layout["nu"],
            )
            == (54,) * 6,
            native_body_order=layout["entities"][0]["body_names"]
            == [model.body(i).name for i in range(1, model.nbody)],
            reduction_matches_source=transfer["reduction_checks"]["passed"]
            and transfer["scoring_model_checks"]["passed"],
            native_mass_readback=mass.get("unit") == "kg"
            and any(p["kind"] == "engine_readback" for p in mass.get("provenance", []))
            and np.asarray(mass.get("effective")).shape == (1, model.nbody - 1)
            and bool(
                np.allclose(
                    mass["effective"], model.body_mass[None, 1:], rtol=1e-5, atol=1e-9
                )
            ),
            unchanged_model_mass=bool(
                np.allclose(
                    np.asarray(receipt["body_mass"])[0],
                    model.body_mass,
                    rtol=1e-5,
                    atol=1e-9,
                )
            ),
        )
    result["checks"].update(
        archive_hashes_match=matched,
        frozen_protocol=receipt.get("protocol") == PROTOCOL
        and receipt.get("limits") == LIMITS,
        native_run_completed=receipt["status"] == "completed"
        and "cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True
        and digest(output / "source.py") == receipt["source_sha256"]
        and all(
            (output / name).is_file() and digest(output / name) == sha
            for name, sha in receipt.get("dependency_sha256", {}).items()
        ),
    )
    result["passed"] = bool(all(result["checks"].values()))
    result["verifier_sha256"] = digest(Path(__file__))
    write_json(output / "summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--source-run", required=True, type=Path)
    execute.add_argument("--output", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = (
        run(args.source_run.resolve(), args.output.resolve())
        if args.command == "run"
        else verify(args.directory.resolve())
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
