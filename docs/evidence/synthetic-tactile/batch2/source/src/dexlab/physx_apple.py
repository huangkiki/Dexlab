"""Run the OpenArm/Wuji SDF apple scene in native PhysX through UniSim.

This is a known-state scripted controller. Completion is not grasp acceptance;
use the independent offline scorer and retain failed runs.
"""

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

from dexlab.physx_baseline import digest, write_json
from dexlab.robot_transfer import prepare

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "demos/apple-stem-grasp/src"))
from mujoco_grasp import translated_targets
from stem_trajectory import smooth, stem_target


def scene_files(source: Path, output: Path):
    """Reuse the verified compiled-inertia reduction, preserving source assets."""
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    transfer = prepare(source, output / "robot-model")
    robot_file = output / "robot-model/robot.xml"
    robot = ET.parse(robot_file).getroot()
    for mesh in robot.findall("./asset/mesh"):
        mesh.set(
            "file", str(Path(mesh.get("file")).relative_to(output / "robot-model"))
        )
    for geom in robot.iter("geom"):
        if geom.get("name") in transfer["original_sdf_geoms"]:
            geom.set("type", "sdf")
    robot.find("option").set("gravity", "0 0 -9.81")
    ET.ElementTree(robot).write(robot_file, encoding="unicode")
    original = ET.parse(source / "model.xml").getroot()
    entities = []
    for name in ("robot", "apple", "table"):
        if name == "robot":
            body = robot.find("./worldbody/body")
            filename = robot_file
        else:
            root = ET.Element("mujoco", model=name)
            ET.SubElement(root, "compiler", angle="radian")
            root.append(copy.deepcopy(robot.find("option")))
            root.append(copy.deepcopy(original.find("default")))
            asset = ET.SubElement(root, "asset")
            body = copy.deepcopy(original.find(f"./worldbody/body[@name='{name}']"))
            if name == "table":
                ET.SubElement(
                    body, "inertial", mass="1", pos="0 0 0", diaginertia="1 1 1"
                )
            used = {g.get("mesh") for g in body.iter("geom")}
            for item in original.findall("./asset/mesh"):
                if item.get("name") not in used:
                    continue
                mesh = copy.deepcopy(item)
                path = Path(mesh.get("file"))
                if not path.is_absolute():
                    path = source / path
                local = output / (name + path.suffix)
                shutil.copyfile(path, local)
                mesh.set("file", local.name)
                asset.append(mesh)
            ET.SubElement(root, "worldbody").append(body)
            filename = output / (name + ".xml")
            ET.ElementTree(root).write(filename, encoding="unicode")
        entities.append(
            SceneEntitySpec(
                name,
                ModelSourceDescriptor(str(filename)),
                kind="articulation" if name == "robot" else "rigid",
                root_mode="floating" if name == "apple" else "fixed",
                self_collision=name == "robot",
                gravity_disabled=name == "table",
                initial_state=EntityInitialState(
                    position=tuple(map(float, body.get("pos", "0 0 0").split())),
                    quaternion=tuple(map(float, body.get("quat", "1 0 0 0").split())),
                ),
            )
        )
    sensor = ET.Element("mujoco")
    sensors = ET.SubElement(sensor, "sensor")
    for name, geom in (
        ("thumb_normal", "robot/collision_r_thumb_pad"),
        ("index_normal", "robot/collision_r_index_finger_pad"),
        ("table_normal", "table/table_collision"),
    ):
        ET.SubElement(
            sensors,
            "contact",
            name=name,
            geom1="apple/collision_apple",
            geom2=geom,
            data="force",
            reduce="netforce",
        )
    ET.ElementTree(sensor).write(output / "sensors.xml", encoding="unicode")
    return SceneCfg(
        entity_assets=tuple(entities),
        default_keyframe_name="home",
        fragment_files=[str(output / "sensors.xml")],
    ), transfer


def scale_closure(path: np.ndarray, fraction: float) -> np.ndarray:
    """Follow a prefix of the explicit hand synergy, keeping its open posture."""
    if not np.isfinite(fraction) or not 0 < fraction <= 1:
        raise ValueError("Closure fraction must be in (0, 1]")
    coordinates = np.linspace(0, (len(path) - 1) * fraction, len(path))
    return np.stack(
        [np.interp(coordinates, np.arange(len(path)), column) for column in path.T],
        axis=1,
    )


def run(args):
    from scipy.spatial.transform import Rotation
    from unisim.backend.isaacsim import (
        backend as adapter,
    )
    from unisim.backend.isaacsim import (
        contact_details,
        physx_solver,
        scene_worker,
        sdf_collision,
        worker,
    )
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.factory import create_backend

    if (
        not np.isfinite(args.dt)
        or not 0 < args.dt <= 0.01
        or any(
            not np.isclose(seconds / args.dt, round(seconds / args.dt))
            for seconds in (3, 14)
        )
    ):
        raise ValueError("dt must divide both 3 and 14 seconds and be at most 10 ms")
    if not np.isfinite(args.height_offset):
        raise ValueError("Height offset must be finite")
    if (
        not np.isfinite(args.min_torsional_patch_radius)
        or args.min_torsional_patch_radius < 0
    ):
        raise ValueError("Torsional radius must be finite and nonnegative")
    scale_closure(np.zeros((2, 1)), args.closure_fraction)

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = args.source_run.resolve()
    snapshots = {
        "source.py": Path(__file__),
        "unisim-scene-worker.py": Path(scene_worker.__file__),
        "unisim-sdf-collision.py": Path(sdf_collision.__file__),
        "stem_trajectory.py": ROOT / "demos/apple-stem-grasp/src/stem_trajectory.py",
        "mujoco_grasp.py": ROOT / "demos/apple-stem-grasp/src/mujoco_grasp.py",
    }
    snapshots["unisim-physx-solver.py"] = Path(physx_solver.__file__)
    snapshots["robot_transfer.py"] = ROOT / "src/dexlab/robot_transfer.py"
    snapshots.update(
        {
            "unisim-contact-details.py": Path(contact_details.__file__),
            "unisim-worker.py": Path(worker.__file__),
            "unisim-backend.py": Path(adapter.__file__),
        }
    )
    hashes = {name: digest(path) for name, path in snapshots.items()}
    for name, path in snapshots.items():
        shutil.copyfile(path, output / name)
    receipt = {
        "protocol": "physx-apple-development-v1",
        "status": "preparing",
        "dt": args.dt,
        "duration": args.seconds,
        "height_offset_m": args.height_offset,
        "min_torsional_patch_radius_m": args.min_torsional_patch_radius,
        "source_sha256": hashes,
        "scope": "Development SDF apple trajectory; unqualified support/penetration; no success claim",
        "control": "Known-state shared scripted prior, one apple-settling alignment at1s, compiled gains and kd*dq_target/kp",
        "force_measurement": "Native normal contacts and friction anchors recorded separately against every declared colliding body",
        "robot_self_collision": True,
        "closure_fraction": args.closure_fraction,
        "collision_scope": "Source explicit and implicit exclude pairs; table retained; distant floor omitted; robot self-collision enabled",
    }
    write_json(output / "run.json", receipt)
    backend, rows, contact_rows = None, [], []
    started = time.monotonic()
    try:
        runtime = resolve_isaacsim_runtime()
        identity = subprocess.run(
            [
                str(runtime.python),
                "-c",
                (
                    "import importlib.metadata as m,json,sys,torch; "
                    "print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in "
                    "['isaacsim','isaacsim-kernel','isaaclab','torch']},'gpu':torch.cuda.get_device_name()}))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        receipt["worker"] = json.loads(identity.stdout)
        for name, original in (
            ("fruit", "apple-collision.obj"),
            ("stem", "stem-collision.obj"),
        ):
            shutil.copyfile(
                ROOT / "demos/apple-stem-grasp/assets/apple" / original,
                output / f"reference-{name}.obj",
            )
        scene, transfer = scene_files(source, output)
        receipt["source_compiled_model_sha256"] = transfer[
            "source_compiled_model_sha256"
        ]
        with np.load(source / "command-plan.npz") as saved:
            plan = dict(saved)
        shutil.copyfile(source / "command-plan.npz", output / "command-plan.npz")
        plan["hand_path"] = scale_closure(plan["hand_path"], args.closure_fraction)
        names = plan["joint_names"].tolist()
        reference = mujoco.MjModel.from_xml_path(
            str(output / "robot-model/kinematics.xml")
        )
        kp = reference.actuator_gainprm[:, 0]
        kd = np.array([0.02 if n.startswith(("r_", "l_")) else 40.0 for n in names])
        backend = create_backend(
            "isaacsim",
            scene,
            num_envs=1,
            sim_dt=args.dt,
            isaacsim_worker_timeout_s=600,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_contact_offset=0.0001,
            isaacsim_rest_offset=0.0,
            isaacsim_min_torsional_patch_radius=args.min_torsional_patch_radius,
        )
        backend.materialize()
        receipt["contact_details"] = backend.enable_contact_details("apple")
        layout = backend.get_scene_layout().to_dict()
        for filename, value in (
            ("layout.json", layout),
            ("native-records.json", backend._native_entity_records),
            ("import-report.json", backend.get_import_report().to_dict()),
        ):
            write_json(output / filename, value)
        if backend.get_actuator_joint_names() != tuple(
            "robot/" + name for name in names
        ):
            raise ValueError("Actuator ordering mismatch")
        body_names = ["robot/" + n for n in layout["entities"][0]["body_names"]] + [
            "apple/apple",
            "table/table",
        ]
        ids = backend.get_body_ids(body_names)
        receipt.update(
            status="running",
            body_names=body_names,
            native_mass=backend.get_body_mass().tolist(),
            joint_names=names,
            initial_joint_state=backend.get_entity_state("robot")[
                "joint_positions"
            ].tolist(),
        )
        initial_apple = backend.get_entity_state("apple")["root_pose"][0, :3].copy()
        apple_id = backend.get_body_ids(["apple/apple"])
        angular = backend.get_body_ang_vel_w(apple_id)[0, 0]
        orientation = backend.get_body_quat_w(apple_id)[0, 0][[1, 2, 3, 0]]
        com = np.asarray(backend._native_entity_records["apple"]["body_com"])[0, 0]
        receipt["initial_apple_com_velocity"] = (
            backend.get_body_lin_vel_w(apple_id)[0, 0]
            + np.cross(angular, Rotation.from_quat(orientation).apply(com))
        ).tolist()
        previous = stem_target(plan, 0)
        knots = np.arange(0, 14.0001, 0.05)
        targets = np.array([stem_target(plan, t) for t in knots])
        corrections = None
        write_json(output / "run.json", receipt)
        for step in range(round(args.seconds / args.dt)):
            t = step * args.dt
            target = stem_target(plan, t)
            if t >= 1:
                if corrections is None:
                    offset = (
                        backend.get_entity_state("apple")["root_pose"][0, :3]
                        - initial_apple
                    )
                    offset[2] += args.height_offset
                    arm, corrections = translated_targets(
                        reference, names, targets, knots, offset
                    )
                    receipt["alignment_displacement_m"] = offset.tolist()
                    np.savez_compressed(
                        output / "alignment.npz",
                        times=knots,
                        corrections=corrections,
                        arm=arm,
                    )
                target[arm] += smooth(t, 1, 2) * np.array(
                    [np.interp(t, knots, c) for c in corrections.T]
                )
            target_velocity = (
                (target - previous) / args.dt if step else np.zeros_like(target)
            )
            ctrl = target + kd * target_velocity / kp
            backend.step(ctrl[None].astype(np.float32))
            contacts = backend.get_contact_details()
            contacts["normal_step"] = np.full(
                len(contacts["normal_body_ids"]), step, dtype=np.int64
            )
            contacts["friction_step"] = np.full(
                len(contacts["friction_body_ids"]), step, dtype=np.int64
            )
            contact_rows.append(contacts)
            previous = target
            state = backend.get_entity_state("robot")
            rows.append(
                {
                    "time": (step + 1) * args.dt,
                    "target": target,
                    "ctrl": ctrl,
                    "q": state["joint_positions"][0].copy(),
                    "dq": state["joint_velocities"][0].copy(),
                    "position": backend.get_body_pos_w(ids)[0].copy(),
                    "quaternion": backend.get_body_quat_w(ids)[0].copy(),
                    "velocity": backend.get_body_lin_vel_w(ids)[0].copy(),
                    "angular_velocity": backend.get_body_ang_vel_w(ids)[0].copy(),
                    "normal_force": np.array(
                        [
                            backend.get_sensor_data(n)[0]
                            for n in ("thumb_normal", "index_normal", "table_normal")
                        ]
                    ),
                }
            )
            if (step + 1) % round(1 / args.dt) == 0:
                print(
                    json.dumps(
                        {
                            "time": (step + 1) * args.dt,
                            "apple": rows[-1]["position"][-2].tolist(),
                            "maximum_joint_error_rad": float(
                                np.abs(rows[-1]["q"] - target).max()
                            ),
                            "elapsed_s": time.monotonic() - started,
                        }
                    ),
                    flush=True,
                )
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 -- archive the failure and close the native worker.
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            stderr_fd = (
                os.dup(backend._stderr_file.fileno())
                if backend._stderr_file is not None
                else None
            )
            process = backend._proc
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:  # noqa: BLE001 -- retain a failed native shutdown.
                receipt["cleanup_error"] = traceback.format_exc()
            finally:
                if stderr_fd is not None:
                    with os.fdopen(stderr_fd, "rb") as log:
                        log.seek(0)
                        (output / "worker-stderr.log").write_bytes(log.read())
                    receipt["complete_worker_stderr"] = (
                        process is not None and process.poll() is not None
                    )
                    receipt["worker_exit_code"] = (
                        process.returncode if process is not None else None
                    )
        np.savez_compressed(
            output / "states.npz",
            **({k: np.asarray([r[k] for r in rows]) for k in rows[0]} if rows else {}),
        )
        np.savez_compressed(
            output / "contacts.npz",
            **(
                {
                    k: np.concatenate([r[k] for r in contact_rows])
                    for k in contact_rows[0]
                }
                if contact_rows
                else {}
            ),
        )
        receipt["elapsed_s"] = time.monotonic() - started
        receipt["contact_polls"] = len(contact_rows)
        receipt["source_unchanged"] = all(
            digest(path) == hashes[name] for name, path in snapshots.items()
        )
        receipt["artifact_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file() and p.name != "run.json"
        }
        write_json(output / "run.json", receipt)
        print(
            json.dumps(
                {
                    k: v
                    for k, v in receipt.items()
                    if k
                    not in (
                        "artifact_sha256",
                        "body_names",
                        "native_mass",
                        "initial_joint_state",
                        "contact_details",
                    )
                },
                indent=2,
            )
        )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-run",
        type=Path,
        required=True,
        help="Completed MuJoCo source run with compiled inertials, meshes and command plan",
    )
    parser.set_defaults(seconds=14.0)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--height-offset", type=float, default=0.01075)
    parser.add_argument("--min-torsional-patch-radius", type=float, default=0.001)
    parser.add_argument("--closure-fraction", type=float, default=0.95)
    args = parser.parse_args()
    receipt = run(args)
    raise SystemExit(0 if receipt["status"] == "completed" else 1)
