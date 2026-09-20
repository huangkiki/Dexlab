"""Pinch the original apple stem using one native SuperDex SDF rigid body."""

# Native preload before importing the display module.
# ruff: noqa: I001
from apple_scene import (
    ASSET,
    PALM_ROTATION,
    APPLE,
    OUT,
    TABLE_TOP,
    TABLE_CENTER,
    TABLE_SIZE,
    solve_arm,
    make_display,
    physics,
    robotics,
)
from physics_utils import actor_poses, create_mesh_actor, smooth
from plan_wuji_pinch import (
    pinch_pose,
    gravity_offset,
    MIDPOINT,
    PINCH_AXIS,
    PAD_CONTACT_POINTS,
    PINCH_SEED,
)
from grasp_display import open_viewer, set_frame
from wuji_regrasp import plan_body_grasp, body_target
from verify_wuji_sequence import verify_sequence
from contextlib import ExitStack
from pathlib import Path
from scipy.spatial.transform import Rotation
import argparse
import json
import time
import numpy as np
import trimesh

DT = 0.002


def trial(args):
    dest = args.output
    dest.mkdir(parents=True, exist_ok=True)
    physics.initialize(num_worker_threads=8)
    scene = physics.create_scene("Wuji stem pinch")
    scene.set_gravity([0, 0, -9.81])
    solver = scene.get_solver_params()
    solver.non_linear_solver.max_iter = 128
    solver.non_linear_solver.rel_step_tol = 0
    solver.linear_solver.solver_type = getattr(
        physics.LinearSolverType, args.linear_solver
    )
    if args.linear_solver == "GMRES":
        solver.linear_solver.max_iter = 200
    solver.experimental_eval.fitted_saturation_hessian.contact_friction = False
    scene.set_solver_params(solver)
    context = robotics.create_context()
    bot = None
    with ExitStack() as stack:
        try:
            body_mesh = trimesh.load_mesh(APPLE / "apple-collision.obj", process=False)
            stem_mesh = trimesh.load_mesh(APPLE / "stem-collision.obj", process=False)
            table = create_mesh_actor(
                scene,
                trimesh.creation.box(extents=TABLE_SIZE),
                "table",
                TABLE_CENTER,
                static=True,
                box=True,
            )
            print("Building the apple/stem SDF (0.2 mm target voxels)", flush=True)
            union = trimesh.load_mesh(APPLE / "apple-stem-union.obj", process=False)
            shape = physics.create_tri_mesh_shape(
                coordinates=np.asarray(union.vertices, float).ravel(),
                connectivity=np.asarray(union.faces, np.int32).ravel(),
            )
            try:
                body = scene.create_rigid_actor(
                    name="apple_with_stem",
                    shape=shape,
                    mass=0.2,
                    collider_type=physics.ColliderType.SDF,
                    sdf=physics.GridSdfParams(
                        resolution_mode=physics.GridSdfResolutionMode.EXPLICIT,
                        resolution_delta=[0.0002] * 3,
                    ),
                    world_from_local=physics.TransformRT(
                        translation=[
                            0.30,
                            0.40,
                            TABLE_TOP - body_mesh.bounds[0, 2] + 0.001,
                        ]
                    ),
                )
            finally:
                physics.release_shape(shape)
            body.register_query(physics.QueryType.TOTAL_CONTACT_FORCE)
            body.register_query(physics.QueryType.CONTACT_POINTS)
            print("Settling the apple on the table", flush=True)
            # Resolve the fruit's resting pose before planning the narrow stem pinch.
            for _ in range(round(3 / DT)):
                scene.step(DT)
            apple_transform = body.get_root_transform()
            stem_info = json.loads((APPLE / "stem.json").read_text())
            section = min(stem_info["sections"], key=lambda row: abs(row["z"] - 0.056))
            contact_local = np.array(section["center"])
            contact_local[2] += args.height_offset
            contact_world = Rotation.from_quat(
                np.array(apple_transform.rotation)
            ).apply(contact_local) + np.array(apple_transform.translation)
            print("Stem target", contact_world, flush=True)
            print("Loading OpenArm / Wuji", flush=True)
            prefab = robotics.load_bot_prefab_from_file(
                str(ASSET / "openarm_v20_wuji_trimmed.superdex_bot")
            )
            bot = robotics.create_bot(scene, prefab, context)
            actor = bot.get_articulated_actor()
            links = [scene.get_actor(h) for h in actor.get_nested_link_actors()]
            names = [l.name for l in prefab.links]
            lookup = dict(zip(names, links))
            robot_handles = {
                link.get_handle().value: name for name, link in zip(names, links)
            }
            apple_handle = body.get_handle()
            joints = [
                j
                for j in prefab.joints
                if j.type == physics.ArticulatedJointType.REVOLUTE
            ]
            arm = np.array(
                [
                    i
                    for i, j in enumerate(joints)
                    if j.name.startswith("arm_openarm_right_joint")
                ]
            )
            hand = np.array(
                [i for i, j in enumerate(joints) if j.name.startswith("r_")]
            )
            bounds = np.array(
                [
                    [
                        np.dot(
                            np.array(getattr(joints[i], k)), np.array(joints[i].axis)
                        )
                        for i in arm
                    ]
                    for k in ["min_limit", "max_limit"]
                ]
            )
            home = np.empty(
                actor.get_num_dofs(),
                np.float64 if physics.USE_DOUBLE_PRECISION else np.float32,
            )
            actor.get_articulated_pose(home)
            home[hand] = 0
            pinch_ids = np.array(
                [
                    i
                    for prefix in ("r_index_finger", "r_thumb")
                    for i, j in enumerate(joints)
                    if j.name.startswith(prefix)
                ]
            )
            home[pinch_ids] = PINCH_SEED
            hand_path = [pinch_pose(actor, lookup, joints, home, 0.026)]
            for gap in np.linspace(0.026, args.gap, 13)[1:]:
                hand_path.append(pinch_pose(actor, lookup, joints, hand_path[-1], gap))
            hand_path = np.asarray(hand_path)
            opened, closed = hand_path[0], hand_path[-1]
            base_rotation = (
                Rotation.from_euler("z", args.yaw, degrees=True) * PALM_ROTATION
            )
            rotation = (
                Rotation.from_rotvec(
                    base_rotation.apply(PINCH_AXIS) * np.deg2rad(args.roll)
                )
                * base_rotation
            )
            wrist_position = contact_world - rotation.apply(MIDPOINT)
            grasp = solve_arm(
                actor, lookup["r_wrist"], opened, arm, bounds, wrist_position, rotation
            )
            pre = solve_arm(
                actor,
                lookup["r_wrist"],
                grasp,
                arm,
                bounds,
                wrist_position + [0, 0, 0.08],
                rotation,
            )
            lift_path = [grasp]
            for height in np.linspace(0.01, 0.12, 12):
                lift_path.append(
                    solve_arm(
                        actor,
                        lookup["r_wrist"],
                        lift_path[-1],
                        arm,
                        bounds,
                        wrist_position + [0, 0, height],
                        rotation,
                    )
                )
            lift_path = np.asarray(lift_path)
            raised = lift_path[-1]
            gains = np.full(len(home), 1000.0)
            gains[hand] = 0.8
            for i, joint in enumerate(joints):
                if joint.name.startswith(("r_index_finger", "r_thumb")):
                    gains[i] = args.stiffness
            grasp_closed = grasp.copy()
            grasp_closed[hand] = closed[hand]
            raised_closed = raised.copy()
            raised_closed[hand] = closed[hand]
            active = np.r_[arm, hand]
            ff_pre, ff_open, ff_closed, ff_raised = [
                gravity_offset(actor, prefab, links, q, active, gains)
                for q in [pre, grasp, grasp_closed, raised_closed]
            ]
            for link in [body] + [
                l
                for info, l in zip(prefab.links, links)
                if info.name.startswith("r_") and info.shape_file
            ]:
                contact = link.get_contact_params()
                contact.penalty_threshold_default = 0.0001
                contact.penalty_smoothing_half_distance = 0.00015
                contact.penalty_coefficient = 1e10
                contact.friction_falloff_vel = args.friction_velocity
                link.set_contact_params(contact)
            actor.set_articulated_pose_from_joints(pose=pre)
            params = physics.PoseControllerParams(len(links))
            for i, j in enumerate(prefab.joints):
                if j.type == physics.ArticulatedJointType.REVOLUTE:
                    is_hand = j.name.startswith(("l_", "r_"))
                    finger_gain = (
                        args.stiffness
                        if j.name.startswith(("r_index_finger", "r_thumb"))
                        else 0.8
                    )
                    params.joint_tracking[i] = physics.PoseTrackingParams(
                        stiffness=finger_gain if is_hand else 1000,
                        damping=0.02 if is_hand else 40,
                    )
            actor.add_articulated_pose_controller(params)
            actor.reset_articulated_target_pose(pose=pre)
            report = {
                "native_worker_threads": 8,
                "solver": {
                    "linear_solver": args.linear_solver,
                    "max_non_linear_iterations": 128,
                    "line_search": solver.non_linear_solver.line_search_type.name,
                    "fitted_contact_friction_hessian": solver.experimental_eval.fitted_saturation_hessian.contact_friction,
                    "relative_step_tolerance": 0,
                },
                "apple_model": "One free rigid body, watertight union of original fruit and stem",
                "sdf_target_max_voxel_m": 0.0002,
                "active_dofs": actor.get_num_dofs(),
                "contact_world": contact_world.tolist(),
                "contact_local": contact_local.tolist(),
                "wrist_position": wrist_position.tolist(),
                "rotation_xyzw": rotation.as_quat().tolist(),
                "roll_deg": args.roll,
                "height_offset_m": args.height_offset,
                "pinch_axis_wrist": PINCH_AXIS.tolist(),
                "pinch_midpoint_wrist_m": MIDPOINT.tolist(),
                "pad_contact_points_m": {
                    n: p.tolist() for n, p in PAD_CONTACT_POINTS.items()
                },
                "other_finger_stiffness": 0.8,
                "open_hand": opened[hand].tolist(),
                "closed_hand": closed[hand].tolist(),
                "gap_m": args.gap,
                "stiffness": args.stiffness,
                "apple_collider": str(body.get_collider_type()),
                "stem_geometry": stem_info,
                "lift_cartesian_waypoint_spacing_m": 0.01,
                "hand_cartesian_waypoint_count": len(hand_path),
                "gravity_compensation": "unloaded potential gradient / joint stiffness",
                "contact_parameters": {
                    "penalty_threshold_m": 0.0001,
                    "penalty_smoothing_half_distance_m": 0.00015,
                    "penalty_coefficient_pa_per_m": 1e10,
                    "friction_falloff_velocity_m_per_s": args.friction_velocity,
                    "friction_coefficient": 0.5,
                },
            }
            (dest / "plan.json").write_text(json.dumps(report, indent=2))
            print("Pinch plan ready", flush=True)
            model, data, camera = make_display(
                prefab,
                dest,
                title="OpenArm + Wuji | SuperDex Apple Grasp",
            )
            xml = (
                (dest / "display.xml")
                .read_text()
                .replace("APPLE LIVE", "APPLE STEM LIVE")
            )
            (dest / "display.xml").write_text(xml)
            viewer = None
            if not args.headless:
                viewer = stack.enter_context(open_viewer(model, data))
                viewer.cam.lookat[:] = camera.lookat
                viewer.cam.distance = camera.distance
                viewer.cam.azimuth = camera.azimuth
                viewer.cam.elevation = camera.elevation
            frames = []
            records = []
            dynamics = []
            regrasp_plan = None
            start = time.monotonic()
            hold_vertical_impulse = 0.0
            hold_duration = 0.0
            solver_counts = {}
            for step in range(round(args.seconds / DT)):
                t = step * DT
                if viewer is not None and not viewer.is_running():
                    return None
                if args.sequence and step == round(23 / DT):
                    released_pose = np.empty_like(home)
                    actor.get_articulated_pose(released_pose)
                    regrasp_plan = plan_body_grasp(
                        prefab,
                        context,
                        released_pose,
                        arm,
                        hand,
                        bounds,
                        np.array(body.get_root_transform().translation),
                    )
                    for i, joint in enumerate(prefab.joints):
                        if (
                            joint.type == physics.ArticulatedJointType.REVOLUTE
                            and joint.name.startswith("r_")
                        ):
                            params.joint_tracking[i] = physics.PoseTrackingParams(
                                stiffness=0.8, damping=0.01
                            )
                    actor.set_articulated_pose_controller_params(params=params)
                    (dest / "body-plan.json").write_text(
                        json.dumps(
                            {
                                "apple_position": np.array(
                                    body.get_root_transform().translation
                                ).tolist(),
                                "keyframes": [
                                    (time, pose.tolist()) for time, pose in regrasp_plan
                                ],
                                "isolated_planning_robot": True,
                            },
                            indent=2,
                        )
                    )
                    print("Body grasp planned from released apple pose", flush=True)
                target = pre.copy()
                target[arm] += smooth(t, 0.5, 2) * (grasp[arm] - pre[arm])
                closing = smooth(t, 3, 3)
                if args.sequence:
                    closing *= 1 - smooth(t, 17.5, 2)
                hand_coordinate = closing * (len(hand_path) - 1)
                hand_lower = min(int(hand_coordinate), len(hand_path) - 2)
                hand_blend = hand_coordinate - hand_lower
                target[hand] = (
                    (1 - hand_blend) * hand_path[hand_lower]
                    + hand_blend * hand_path[hand_lower + 1]
                )[hand]
                lift_fraction = smooth(t, 7, 3)
                if args.sequence:
                    lift_fraction *= 1 - smooth(t, 14, 3)
                path_coordinate = lift_fraction * (len(lift_path) - 1)
                lower = min(int(path_coordinate), len(lift_path) - 2)
                blend = path_coordinate - lower
                lift_pose = (1 - blend) * lift_path[lower] + blend * lift_path[
                    lower + 1
                ]
                target[arm] += lift_pose[arm] - grasp[arm]
                target += (
                    ff_pre
                    + smooth(t, 0.5, 2) * (ff_open - ff_pre)
                    + smooth(t, 3, 3) * (ff_closed - ff_open)
                    + smooth(t, 7, 3) * (ff_raised - ff_closed)
                )
                if args.sequence:
                    target += smooth(t, 14, 3) * (ff_closed - ff_raised)
                    target += smooth(t, 17.5, 2) * (ff_open - ff_closed)
                    retreat = smooth(t, 20, 2)
                    target[arm] += retreat * (pre[arm] - grasp[arm])
                    target += retreat * (ff_pre - ff_open)
                    if regrasp_plan is not None:
                        target = body_target(regrasp_plan, t)
                actor.set_articulated_target_pose(pose=target)
                velocity_before = np.array(body.get_linear_velocity())
                scene.step(DT)
                stats = scene.get_solver_stats()
                status = stats.convergence_status.name
                solver_counts[status] = solver_counts.get(status, 0) + 1
                if 11 <= t < 14:
                    hold_vertical_impulse += DT * (
                        body.get_contact_force_world()[2]
                        - body.get_contact_force_from_actor_world(table)[2]
                    )
                    hold_duration += DT
                total_force = np.array(body.get_contact_force_world())
                table_force = np.array(body.get_contact_force_from_actor_world(table))
                dynamics.append(
                    {
                        "time": t,
                        "total_force": total_force.tolist(),
                        "table_force": table_force.tolist(),
                        "hand_force": (total_force - table_force).tolist(),
                        "velocity_before": velocity_before.tolist(),
                        "velocity": np.array(body.get_linear_velocity()).tolist(),
                        "apple_status": body.get_convergence_status().name,
                        "scene_status": status,
                    }
                )
                if step % round(0.05 / DT) == 0:
                    frame = actor_poses(links + [body])
                    frames.append(frame)
                    if not np.isfinite(frame).all():
                        raise RuntimeError("Nonfinite state")
                    vertices = (
                        Rotation.from_quat(frame[-1, 3:]).apply(body_mesh.vertices)
                        + frame[-1, :3]
                    )
                    robot_contact_forces = {
                        n: np.array(body.get_contact_force_from_actor_world(l)).tolist()
                        for n, l in zip(names, links)
                    }
                    fruit_forces = {}
                    hand_depths = []
                    min_hand_contact_z = None
                    contact_rows = []
                    apple_rotation = Rotation.from_quat(frame[-1, 3:]).inv()
                    for point in body.get_contact_points_world():
                        on_a = point.actor_a == apple_handle
                        other = point.actor_b if on_a else point.actor_a
                        name = robot_handles.get(other.value)
                        if name is None:
                            continue
                        force = np.array(point.force) * (1 if on_a else -1)
                        if np.linalg.norm(force) < 1e-6:
                            continue
                        pos = np.array(point.pos_a if on_a else point.pos_b)
                        local_z = float(apple_rotation.apply(pos - frame[-1, :3])[2])
                        min_hand_contact_z = (
                            local_z
                            if min_hand_contact_z is None
                            else min(local_z, min_hand_contact_z)
                        )
                        hand_depths.append(max(0.0, -point.distance))
                        contact_rows.append(
                            (name, force, apple_rotation.apply(pos - frame[-1, :3]))
                        )
                    off_stem_force = 0.0
                    min_fruit_distance = None
                    min_match_margin = None
                    if contact_rows:
                        points = np.array([item[2] for item in contact_rows])
                        _, fruit_distances, _ = trimesh.proximity.closest_point(
                            body_mesh, points
                        )
                        _, stem_distances, _ = trimesh.proximity.closest_point(
                            stem_mesh, points
                        )
                        min_fruit_distance = float(fruit_distances.min())
                        min_match_margin = float(
                            (fruit_distances - stem_distances).min()
                        )
                        for (name, force, _), df, ds in zip(
                            contact_rows, fruit_distances, stem_distances
                        ):
                            if df <= ds + 0.0002:
                                off_stem_force += float(np.linalg.norm(force))
                                fruit_forces.setdefault(name, np.zeros(3))
                                fruit_forces[name] += force
                    fruit_forces = {n: f.tolist() for n, f in fruit_forces.items()}
                    row = {
                        "time": t,
                        "solver_status": status,
                        "solver_residual_norm": stats.residual_norm,
                        "solver_iterations": stats.max_non_linear_iters,
                        "maximum_robot_apple_penetration_m": max(
                            hand_depths, default=0.0
                        ),
                        "minimum_hand_contact_local_z_m": min_hand_contact_z,
                        "off_stem_contact_force_n": off_stem_force,
                        "minimum_fruit_surface_distance_at_hand_contact_m": min_fruit_distance,
                        "minimum_stem_match_margin_m": min_match_margin,
                        "clearance": float(vertices[:, 2].min() - TABLE_TOP),
                        "robot_contact_forces": robot_contact_forces,
                        "fruit_forces": fruit_forces,
                        "table_force": np.array(
                            body.get_contact_force_from_actor_world(table)
                        ).tolist(),
                        "apple_position": frame[-1, :3].tolist(),
                    }
                    records.append(row)
                    if viewer is not None:
                        set_frame(model, data, frame)
                        viewer.sync()
                        time.sleep(max(0, start + t - time.monotonic()))
                if step % round(1 / DT) == 0:
                    np.savez_compressed(
                        dest / "trajectory.npz",
                        frames=frames,
                        names=names + ["apple"],
                        dt=0.05,
                    )
                    (dest / "metrics.json").write_text(json.dumps(records))
                    row = records[-1]
                    sf = sum(
                        np.linalg.norm(v) for v in row["robot_contact_forces"].values()
                    )
                    ff = sum(np.linalg.norm(v) for v in row["fruit_forces"].values())
                    print(
                        f"{t:.1f}s clearance={row['clearance']:.4f} robot_contact={sf:.3f}N nonstem_contact={ff:.3f}N solver={status} iters={stats.max_non_linear_iters}",
                        flush=True,
                    )
            np.savez_compressed(
                dest / "trajectory.npz", frames=frames, names=names + ["apple"], dt=0.05
            )
            (dest / "metrics.json").write_text(json.dumps(records, indent=2))
            (dest / "dynamics.json").write_text(json.dumps(dynamics))
            if args.sequence:
                summary = verify_sequence(records, dynamics, DT)
                (dest / "summary.json").write_text(json.dumps(summary, indent=2))
                print(json.dumps(summary, indent=2), flush=True)
                return summary
            held = [r for r in records if 11 <= r["time"] < 14]
            norm = lambda values: sum(np.linalg.norm(v) for v in values)
            summary = {
                "minimum_hold_clearance_m": min(
                    (r["clearance"] for r in held), default=-1
                ),
                "mean_hand_weight_support_ratio": (
                    hold_vertical_impulse / hold_duration / (0.2 * 9.81)
                    if hold_duration
                    else 0.0
                ),
                "hold_force_sampling_hz": round(1 / DT),
                "maximum_nonstem_contact_n": max(
                    r["off_stem_contact_force_n"] for r in records
                ),
                "mean_thumb_force_n": float(
                    np.mean(
                        [
                            norm(
                                v
                                for n, v in r["robot_contact_forces"].items()
                                if "thumb" in n
                            )
                            for r in held
                        ]
                    )
                )
                if held
                else 0,
                "mean_index_force_n": float(
                    np.mean(
                        [
                            norm(
                                v
                                for n, v in r["robot_contact_forces"].items()
                                if "index" in n
                            )
                            for r in held
                        ]
                    )
                )
                if held
                else 0,
                "maximum_hold_table_force_n": max(
                    (np.linalg.norm(r["table_force"]) for r in held), default=1e9
                ),
                "final_robot_contact_n": norm(
                    records[-1]["robot_contact_forces"].values()
                ),
                "final_clearance_m": records[-1]["clearance"],
                "maximum_robot_apple_penetration_m": max(
                    r["maximum_robot_apple_penetration_m"] for r in records
                ),
                "maximum_other_robot_contact_n": max(
                    norm(
                        v
                        for n, v in r["robot_contact_forces"].items()
                        if not n.startswith(("r_thumb", "r_index_finger"))
                    )
                    for r in records
                ),
                "solver_status_counts": solver_counts,
                "finite_state": True,
                "friction_falloff_velocity_m_per_s": args.friction_velocity,
                "dt_s": DT,
                "gap_m": args.gap,
                "stiffness": args.stiffness,
                "yaw_deg": args.yaw,
                "roll_deg": args.roll,
            }
            contact_heights = [
                r["minimum_hand_contact_local_z_m"]
                for r in records
                if r["minimum_hand_contact_local_z_m"] is not None
            ]
            summary["minimum_hand_contact_local_z_m"] = min(
                contact_heights, default=None
            )
            summary["fruit_max_local_z_m"] = float(body_mesh.bounds[1, 2])
            summary["checks"] = {
                "contact_geometry_available": bool(contact_heights),
                "no_solver_divergence": solver_counts.get("DIVERGED", 0) == 0,
                "finite_state": summary["finite_state"],
                "bounded_penetration": summary["maximum_robot_apple_penetration_m"]
                < 0.0005,
                "only_thumb_index_contact_apple": summary[
                    "maximum_other_robot_contact_n"
                ]
                < 0.05,
                "lifted": summary["minimum_hold_clearance_m"] > 0.07,
                "hand_supports_weight": 0.8
                < summary["mean_hand_weight_support_ratio"]
                < 1.2,
                "only_stem_contact": summary["maximum_nonstem_contact_n"] < 0.05,
                "thumb": summary["mean_thumb_force_n"] > 0.1,
                "index": summary["mean_index_force_n"] > 0.1,
                "no_table_support": summary["maximum_hold_table_force_n"] < 0.05,
            }
            summary["sequence"] = "pinch_lift_hold"
            summary["checks"]["retained_at_end"] = (
                summary["final_clearance_m"] > 0.07
                and summary["final_robot_contact_n"] > 0.2
            )
            summary["checks"]["both_fingers_contact_throughout_hold"] = bool(
                held
            ) and all(
                norm(
                    v
                    for n, v in r["robot_contact_forces"].items()
                    if n.startswith(prefix)
                )
                > 0.1
                for r in held
                for prefix in ("r_thumb", "r_index_finger")
            )
            summary["checks"] = {k: bool(v) for k, v in summary["checks"].items()}
            summary["passed"] = all(summary["checks"].values())
            (dest / "summary.json").write_text(json.dumps(summary, indent=2))
            print(json.dumps(summary, indent=2), flush=True)
            return summary
        finally:
            stack.close()
            if bot is not None:
                robotics.destroy_bot(scene, bot)
            physics.destroy_scene(scene)
            physics.shutdown()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=OUT.parent / "runs/latest")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--seconds", type=float)
    p.add_argument("--sequence", action="store_true")
    p.add_argument("--gap", type=float, default=0.001)
    p.add_argument("--stiffness", type=float, default=30)
    p.add_argument("--friction-velocity", type=float, default=0.00002)
    p.add_argument("--roll", type=float, default=-20)
    p.add_argument("--yaw", type=float, default=0)
    p.add_argument("--height-offset", type=float, default=0.0015)
    p.add_argument("--linear-solver", choices=["CG", "GMRES"], default="GMRES")
    args = p.parse_args()
    if args.seconds is None:
        args.seconds = 40 if args.sequence else 14
    result = trial(args)
    if result is not None and not result["passed"]:
        raise SystemExit("Stem grasp verification failed")


if __name__ == "__main__":
    main()
