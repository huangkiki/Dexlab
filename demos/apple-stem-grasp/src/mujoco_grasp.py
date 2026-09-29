"""Run the shared stem-grasp command prior with official MuJoCo dynamics."""

import hashlib
import importlib.metadata
import json
import time
from contextlib import ExitStack
from pathlib import Path

import mujoco
import numpy as np
import trimesh
from apple_scene import APPLE, TABLE_TOP
from grasp_display import open_viewer, set_frame
from mujoco_model import build_model
from scipy.spatial.transform import Rotation
from stem_trajectory import smooth, stem_target
from verify_sdf_grasp import verify_grasp
from dexlab.episode import GraspFrame


def official_engine():
    """Reject the known local patch and validate the wheel's native library hash."""
    package = Path(mujoco.__file__).parent
    if (package / "sdf_patch_info.json").exists():
        raise RuntimeError(
            "Use the official MuJoCo wheel, not the local patched engine."
        )
    distribution = importlib.metadata.distribution("mujoco")
    library = next(package.glob("libmujoco.so.*"))
    entry = next(p for p in distribution.files if p.name == library.name)
    import base64

    digest = hashlib.sha256(library.read_bytes()).digest()
    matches = (
        entry.hash is not None
        and entry.hash.mode == "sha256"
        and base64.urlsafe_b64encode(digest).rstrip(b"=").decode() == entry.hash.value
    )
    if not matches:
        raise RuntimeError(
            "MuJoCo native library does not match the installed wheel RECORD."
        )
    return {
        "backend": "mujoco",
        "version": mujoco.__version__,
        "native_library_sha256": digest.hex(),
        "wheel_record_matches": matches,
        "engine_patch": None,
    }


def translated_targets(model, names, targets, times, displacement):
    """Translate wrist targets using isolated FK, never editing live dynamics."""
    data = mujoco.MjData(model)
    qi = np.array([model.joint(name).qposadr[0] for name in names])
    vi = np.array([model.joint(name).dofadr[0] for name in names])
    arm = np.array(
        [i for i, n in enumerate(names) if n.startswith("arm_openarm_right_")]
    )
    wrist = model.body("r_wrist").id
    jp, jr = np.zeros((3, model.nv)), np.zeros((3, model.nv))
    offsets = []
    for target in targets:
        data.qpos[qi] = target
        mujoco.mj_kinematics(model, data)
        position = data.xpos[wrist].copy() + displacement
        orientation = Rotation.from_matrix(data.xmat[wrist].reshape(3, 3))
        for _ in range(12):
            mujoco.mj_kinematics(model, data)
            mujoco.mj_comPos(model, data)
            rotation = Rotation.from_matrix(data.xmat[wrist].reshape(3, 3))
            error = np.r_[
                position - data.xpos[wrist], (orientation * rotation.inv()).as_rotvec()
            ]
            if np.linalg.norm(error) < 1e-9:
                break
            mujoco.mj_jacBody(model, data, jp, jr, wrist)
            data.qpos[qi[arm]] += np.linalg.lstsq(
                np.vstack([jp[:, vi[arm]], jr[:, vi[arm]]]), error, rcond=1e-5
            )[0]
        if np.linalg.norm(error) > 0.0002:
            raise RuntimeError(f"Wrist translation failed: {error}")
        offsets.append(data.qpos[qi[arm]] - target[arm])
    return arm, np.asarray(offsets)


def contact_forces(model, data, apple_id):
    """Read solved forces before refreshing post-integration kinematics."""
    totals = {key: np.zeros(3) for key in ("total", "hand", "table", "other")}
    contacts = []
    force = np.zeros(6)
    for i in range(data.ncon):
        contact = data.contact[i]
        first, second = int(contact.geom1), int(contact.geom2)
        first_apple = model.geom_bodyid[first] == apple_id
        second_apple = model.geom_bodyid[second] == apple_id
        if first_apple == second_apple or contact.efc_address < 0:
            continue
        other_geom = second if first_apple else first
        other_body = int(model.geom_bodyid[other_geom])
        name = model.body(other_body).name
        mujoco.mj_contactForce(model, data, i, force)
        world_force = contact.frame.reshape(3, 3).T @ force[:3]
        if first_apple:
            world_force *= -1
        totals["total"] += world_force
        group = (
            "hand" if name.startswith("r_") else "table" if name == "table" else "other"
        )
        totals[group] += world_force
        if group == "hand":
            local = data.xmat[apple_id].reshape(3, 3).T @ (
                contact.pos - data.xpos[apple_id]
            )
            contacts.append(
                [other_body, *local, contact.dist, abs(force[0]), *world_force]
            )
    return totals, contacts


def run_mujoco(
    args, prefab, links, scene, apple, joints, plan, display, display_data, camera
):
    dest = args.output
    engine = official_engine()
    print("Building native MuJoCo SDF-SDF model", flush=True)
    model = build_model(prefab, links, scene, apple, dest)
    names = [joint.name for joint in joints]
    model_names = [info.name for info in prefab.links]
    native_positions = np.array(
        [link.get_root_transform().translation for link in links]
    )
    fk = mujoco.MjData(model)
    fk.qpos[[model.joint(n).qposadr[0] for n in names]] = plan["pre"]
    mujoco.mj_kinematics(model, fk)
    ids = [model.body(n if n != "world" else "robot_world").id for n in model_names]
    native_rotations = Rotation.from_quat(
        [link.get_root_transform().rotation for link in links]
    )
    compiled_rotations = Rotation.from_quat(fk.xquat[ids][:, [1, 2, 3, 0]])
    error = float((compiled_rotations * native_rotations.inv()).magnitude().max())
    if error > 1e-7:
        raise RuntimeError(f"Native/MuJoCo FK rotation mismatch: {error} radians")
    engine["fk_max_rotation_error_rad"] = error
    np.savez_compressed(
        dest / "command-plan.npz",
        **plan,
        joint_names=names,
        body_names=model_names,
        native_initial_positions=native_positions,
    )
    return (
        yield from simulate(
            args,
            model,
            plan,
            names,
            model_names,
            native_positions,
            display,
            display_data,
            camera,
            engine,
        )
    )


def simulate(
    args,
    model,
    plan,
    names,
    model_names,
    native_positions,
    display,
    display_data,
    camera,
    engine,
):
    """Execute a prepared command prior from a fresh physics state."""
    dest = args.output
    if args.timestep is not None:
        model.opt.timestep = args.timestep
    model.geom_friction[:, 0] = args.mujoco_friction
    data = mujoco.MjData(model)
    qi = np.array([model.joint(n).qposadr[0] for n in names])
    aids = np.array([model.actuator("pos_" + n).id for n in names])
    data.qpos[qi] = plan["pre"]
    body_ids = [
        model.body(n if n != "world" else "robot_world").id for n in model_names
    ] + [model.body("apple").id]
    apple_id = model.body("apple").id
    initial_apple = data.qpos[model.joint("apple_free").qposadr[0] :][:3].copy()
    mujoco.mj_forward(model, data)
    fk_error = float(
        np.max(np.linalg.norm(data.xpos[body_ids[:-1]] - native_positions, axis=1))
    )
    if fk_error > 1e-7:
        raise RuntimeError(f"Native/MuJoCo FK mismatch: {fk_error} m")
    engine.update(
        {
            "joint_names": names,
            "dt": float(model.opt.timestep),
            "duration": args.seconds,
            "fk_max_position_error_m": fk_error,
            "mass_kg": float(model.body_mass[apple_id]),
            "apple_free_joint": model.joint("apple_free").type[0]
            == mujoco.mjtJoint.mjJNT_FREE,
            "equality_constraints": model.neq,
            "mocap_bodies": model.nmocap,
            "grasp_collider_types": {
                n: "SDF" for n in ("apple", "r_thumb_pad", "r_index_finger_pad")
            },
            "height_offset_m": args.mujoco_height_offset,
            "friction": args.mujoco_friction,
            "pinch_gain_multiplier": args.mujoco_pinch_gain,
            "control": "Known object pose, shared scripted joint-target prior; isolated FK alignment once at 1 s.",
            "completed": False,
        }
    )
    engine["apple_free_joint"] = bool(engine["apple_free_joint"])
    engine["sdf_meshes"] = {}
    for name in ("apple", "r_thumb_pad", "r_index_finger_pad"):
        mesh = int(model.geom("collision_" + name).dataid[0])
        start, count = int(model.mesh_octadr[mesh]), int(model.mesh_octnum[mesh])
        engine["sdf_meshes"][name] = {
            "nodes": count,
            "maximum_depth": int(model.oct_depth[start : start + count].max()),
        }
    (dest / "engine.json").write_text(json.dumps(engine, indent=2))
    fruit = trimesh.load_mesh(APPLE / "apple-collision.obj", process=False)
    dt = float(model.opt.timestep)
    kp = np.array(
        [
            args.stiffness
            if n.startswith(("r_thumb", "r_index"))
            else 0.8
            if n.startswith(("r_", "l_"))
            else 1000
            for n in names
        ]
    )
    kp[[i for i, n in enumerate(names) if n.startswith(("r_thumb", "r_index"))]] *= (
        args.mujoco_pinch_gain
    )
    kd = np.array([0.02 if n.startswith(("r_", "l_")) else 40 for n in names])
    model.actuator_gainprm[aids, 0] = kp
    model.actuator_biasprm[aids, 1] = -kp
    model.actuator_biasprm[aids, 2] = -(kd + dt * kp)
    mujoco.mj_saveModel(model, str(dest / "model.mjb"))
    from dexlab.model_audit import record_mujoco

    record_mujoco(model, data, dest)
    count = round(args.seconds / dt)
    log = {
        k: []
        for k in (
            "time",
            "qpos",
            "apple_pose",
            "wrist_pose",
            "base_pose",
            "clearance",
            "velocity_before",
            "velocity",
            "total",
            "hand",
            "table",
            "other",
            "penetration",
            "warnings",
        )
    }
    frames, contact_rows = [], []
    previous = stem_target(plan, 0)
    knots = np.arange(0, 14.0001, 0.05)
    knot_targets = np.array([stem_target(plan, t) for t in knots])
    corrections = None
    jac, jr = np.zeros((3, model.nv)), np.zeros((3, model.nv))

    def snapshot(t, target, summary=None):
        return GraspFrame(
            t,
            tuple(names),
            data.qpos[qi].copy(),
            np.r_[data.xpos[apple_id], data.xquat[apple_id][[1, 2, 3, 0]]],
            target.copy(),
            summary,
        )

    physics_step_seconds = 0.0
    started = time.monotonic()
    with ExitStack() as stack:
        viewer = (
            None
            if args.headless
            else stack.enter_context(open_viewer(display, display_data))
        )
        if viewer:
            viewer.cam.lookat[:] = camera.lookat
            viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = (
                camera.distance,
                camera.azimuth,
                camera.elevation,
            )
        for step in range(count):
            t = step * dt
            if viewer and not viewer.is_running():
                raise RuntimeError("Viewer closed before completion")
            target = stem_target(plan, t)
            if t >= 1:
                if corrections is None:
                    displacement = data.xpos[apple_id] - initial_apple
                    displacement[2] += args.mujoco_height_offset
                    arm, corrections = translated_targets(
                        model, names, knot_targets, knots, displacement
                    )
                target[arm] += smooth(t, 1, 2) * np.array(
                    [np.interp(t, knots, c) for c in corrections.T]
                )
            target = yield snapshot(t, target)
            target_velocity = (
                (target - previous) / dt if step else np.zeros_like(target)
            )
            data.ctrl[aids] = target + kd * target_velocity / kp
            previous = target
            mujoco.mj_jacBodyCom(model, data, jac, jr, apple_id)
            before = jac @ data.qvel
            step_started = time.perf_counter()
            mujoco.mj_step(model, data)
            physics_step_seconds += time.perf_counter() - step_started
            forces, contacts = contact_forces(model, data, apple_id)
            contact_rows.extend([[t, *row] for row in contacts])
            penetration = max([max(0, -r[4]) for r in contacts], default=0)
            mujoco.mj_kinematics(model, data)
            mujoco.mj_comPos(model, data)
            mujoco.mj_jacBodyCom(model, data, jac, jr, apple_id)
            velocity = jac @ data.qvel
            if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                raise RuntimeError("Nonfinite MuJoCo state")
            log["time"].append(t)
            log["qpos"].append(data.qpos.copy())
            for key, body_id in (
                ("apple_pose", apple_id),
                ("wrist_pose", model.body("r_wrist").id),
                ("base_pose", model.body("openarm_body_link0").id),
            ):
                log[key].append(
                    np.r_[data.xpos[body_id], data.xquat[body_id][[1, 2, 3, 0]]]
                )
            clearance = float(
                np.min(fruit.vertices @ data.xmat[apple_id].reshape(3, 3)[2])
                + data.xpos[apple_id, 2]
                - TABLE_TOP
            )
            log["clearance"].append(clearance)
            log["velocity_before"].append(before)
            log["velocity"].append(velocity)
            for key, value in forces.items():
                log[key].append(value)
            log["penetration"].append(penetration)
            log["warnings"].append(int(np.sum(data.warning.number)))
            if step % round(0.05 / dt) == 0:
                frame = np.c_[
                    data.xpos[body_ids], data.xquat[body_ids][:, [1, 2, 3, 0]]
                ]
                frames.append(frame.copy())
                if viewer:
                    set_frame(display, display_data, frame)
                    viewer.sync()
            if step % round(1 / dt) == 0:
                print(
                    f"MuJoCo {t:.1f}s clearance={clearance:.5f} handFz={forces['hand'][2]:.3f}",
                    flush=True,
                )
    np.savez_compressed(dest / "sdf-dynamics.npz", **log)
    np.savez_compressed(
        dest / "sdf-contacts.npz", contacts=np.asarray(contact_rows).reshape(-1, 10)
    )
    np.savez_compressed(
        dest / "trajectory.npz", frames=frames, names=model_names + ["apple"], dt=0.05
    )
    engine.update(completed=True, steps=count, wall_seconds=time.monotonic() - started)
    (dest / "engine.json").write_text(json.dumps(engine, indent=2))
    engine["physics_step_seconds"] = physics_step_seconds
    (dest / "engine.json").write_text(json.dumps(engine, indent=2))
    result = verify_grasp(dest, expected_mass=args.apple_mass)
    (dest / "summary.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)
    yield snapshot(args.seconds, target, result)
    return result
