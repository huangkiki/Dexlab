"""Known-state cloth manipulation with native, frictional Wuji contacts."""

import os

os.environ.setdefault("MUJOCO_GL", "egl")

import argparse
import base64
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import mujoco
import numpy as np

from dexlab import engine_versions

from cloth_control import (
    arm_pose,
    grasp_candidates,
    initial_pose,
    joint_ids,
    robot_penetration,
    smooth,
)
from cloth_model import build_model
from verify_cloth import verify_episode
from render_cloth import render
from settling_trace import capture_settling


def engine_identity():
    package = Path(mujoco.__file__).parent
    library = next(package.glob("libmujoco.so.*"))
    distribution = importlib.metadata.distribution("mujoco")
    entry = next(path for path in distribution.files if path.name == library.name)
    digest = hashlib.sha256(library.read_bytes()).digest()
    matches = (
        entry.hash is not None
        and entry.hash.mode == "sha256"
        and entry.hash.value == base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    )
    if not matches or (package / "sdf_patch_info.json").exists():
        raise RuntimeError(
            "Use an unmodified MuJoCo wheel; native library RECORD validation failed"
        )
    return engine_versions.mujoco_profile_identity(dict(
        version=mujoco.__version__,
        native_library_sha256=digest.hex(),
        wheel_record_matches=True,
    ), mujoco.mj_versionString())


def controls(model):
    joints = model.actuator_trnid[:, 0]
    return model.jnt_qposadr[joints], model.jnt_dofadr[joints]


def step(model, data, target):
    positions, velocities = controls(model)
    data.ctrl[:] = target[positions]
    data.qfrc_applied[velocities] = data.qfrc_bias[velocities]
    previous_time = data.time
    mujoco.mj_step(model, data)
    if (
        data.time <= previous_time
        or np.any(data.warning.number)
        or not np.isfinite(data.qpos).all()
        or not np.isfinite(data.qvel).all()
    ):
        raise RuntimeError(
            "Physics warning, reset, or nonfinite state; this episode failed"
        )


def configure_phase(model, *, solver, timestep):
    """Refresh timestep-dependent model constants without resetting live state."""
    model.opt.solver = solver
    model.opt.iterations = 100
    model.opt.timestep = timestep
    mujoco.mj_setConst(model, mujoco.MjData(model))


def settle_cloth(model, data, opened, *, output=None, engine=None):
    """Initialize at a fixed timestep independently of the manipulation phase."""
    configure_phase(model, solver=mujoco.mjtSolver.mjSOL_CG, timestep=0.0005)
    mujoco.mj_forward(model, data)
    steps = round(2 / model.opt.timestep)
    with capture_settling(model, data, output, steps=steps, engine=engine) as capture:
        for _ in range(steps):
            step(model, data, opened)
            if capture is not None:
                capture()


def trajectory(point, task, pre_lift_retreat=0.06):
    """Retreat from the table before lifting; release above the support surface."""
    waypoints = [point.copy()]
    for fraction in np.linspace(0, 1, 11)[1:]:
        waypoints.append(point + (0, -pre_lift_retreat * fraction, 0))
    if task == "grasp":
        for fraction in np.linspace(0, 1, 21)[1:]:
            waypoints.append(point + (0, -pre_lift_retreat, 0.12 * fraction))
    else:
        for fraction in np.linspace(0, 1, 21)[1:]:
            waypoints.append(point + (0, -pre_lift_retreat, 0.13 * fraction))
        raised = waypoints[-1].copy()
        target = np.array([point[0], 0.535, point[2] + 0.11])
        for fraction in np.linspace(0, 1, 21)[1:]:
            waypoints.append((1 - fraction) * raised + fraction * target)
    return np.asarray(waypoints)


def plan_grasp(model, state, side, indices, task, inset=0.3, pre_lift_retreat=0.06,
               release_retreat=0.08):
    columns = (
        (14, 13, 12)
        if task == "fold" and side == "r"
        else ((4, 5, 6) if task == "fold" else (10, 11, 12))
    )
    inward = -1 if side == "r" else 1
    row = 0
    for column in columns:
        upper_column = column + 1 if side == "l" else column
        material = [
            indices[(column, row)],
            indices[(column + inward, row)],
            indices[(upper_column, row + 1)],
        ]
        for candidate in grasp_candidates(
            model,
            state,
            side,
            material,
            np.array([(1 - inset) * 4 / 7, (1 - inset) * 3 / 7, inset]),
        ):
            print(
                f"Candidate {side} column={column} normal={candidate['normal_sign']} roll={candidate['angle']}",
                flush=True,
            )
            poses = [candidate["opened"]]
            try:
                for knot, point in enumerate(
                    trajectory(candidate["point"], task, pre_lift_retreat)[1:], start=1
                ):
                    poses.append(
                        arm_pose(
                            model,
                            poses[-1],
                            side,
                            point,
                            candidate["rotation"],
                            relax_orientation=task == "fold" and knot > 10,
                        )
                    )
                retreat = arm_pose(
                    model,
                    poses[-1],
                    side,
                    trajectory(candidate["point"], task, pre_lift_retreat)[-1] + (0, -release_retreat, 0),
                    candidate["rotation"],
                    relax_orientation=task == "fold",
                )
            except ValueError as error:
                print(f"Rejected path: {error}", flush=True)
                continue
            candidate["path"] = np.asarray(poses)
            candidate["retreat"] = retreat
            arm = "left" if side == "l" else "right"
            candidate["arm"] = model.jnt_qposadr[
                joint_ids(model, f"arm_openarm_{arm}_joint")
            ]
            if task == "fold":
                candidate["far_id"] = indices[(column, 7)]
                data = mujoco.MjData(model)
                data.qpos[:] = state
                mujoco.mj_fwdPosition(model, data)
                candidate["fold_target"] = data.flexvert_xpos[
                    candidate["far_id"]
                ].copy()
            return candidate
    raise RuntimeError(f"No collision-free {side} grasp and motion path found")


def contact_measurements(model, data):
    forces = {}
    hand_depth = table_depth = self_depth = floor_depth = 0.0
    force = np.zeros(6)
    for index, contact in enumerate(data.contact):
        if not np.any(contact.flex >= 0):
            continue
        if np.all(contact.flex >= 0):
            self_depth = max(self_depth, -float(contact.dist))
        for geom in contact.geom:
            if geom < 0:
                continue
            name = model.geom(int(geom)).name
            if name.startswith("collision_"):
                mujoco.mj_contactForce(model, data, index, force)
                forces[name] = forces.get(name, 0.0) + float(force[0])
                hand_depth = max(hand_depth, -float(contact.dist))
            elif name.startswith("table_"):
                table_depth = max(table_depth, -float(contact.dist))
            elif name == "floor":
                floor_depth = max(floor_depth, -float(contact.dist))
    return forces, hand_depth, table_depth, self_depth, floor_depth


def verify_combined_path(model, state, plans):
    data = mujoco.MjData(model)
    data.qpos[:] = state
    for fraction in np.linspace(0, 1, 151):
        for plan in plans:
            arm, path = plan["arm"], plan["path"]
            position = fraction * (len(path) - 1)
            lower = min(int(position), len(path) - 2)
            blend = position - lower
            data.qpos[arm] = (1 - blend) * path[lower, arm] + blend * path[
                lower + 1, arm
            ]
        mujoco.mj_fwdPosition(model, data)
        if robot_penetration(model, data) > 0.0003:
            raise ValueError("The simultaneous arm path has a rigid collision")


def run(args):
    destination = args.output.resolve()
    if (
        not 0 < args.grasp_inset < 1
        or not 0 < args.pre_lift_retreat <= 0.2
        or not 0 < args.release_retreat <= 0.2
        or not 0 < args.floor_time_constant <= 0.02
        or not 0 < args.edge_time_constant <= 0.02
        or args.hand_friction < 0
        or not 0 < args.timestep <= 0.001
        or not np.isfinite(args.hand_friction)
        or not np.isclose(
            0.01 / args.timestep, round(0.01 / args.timestep), rtol=0, atol=1e-8
        )
    ):
        raise ValueError(
            "Require inset in (0, 1), pre-lift and release retreats in (0, 0.2] m, friction >= 0, "
            "time constants in (0, 0.02], and timestep in (0, 0.001] seconds"
        )
    if (destination / "summary.json").exists():
        raise FileExistsError(
            "Choose a fresh output directory to preserve earlier evidence"
        )
    engine = engine_identity()
    snapshot = destination / "source"
    snapshot.mkdir(parents=True, exist_ok=True)
    source_sha256 = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(__file__).parent.glob("*.py")
    }
    for source in Path(__file__).parent.glob("*.py"):
        (snapshot / source.name).write_bytes(source.read_bytes())
    profile_source = Path(engine_versions.__file__)
    source_sha256["engine_versions.py"] = hashlib.sha256(profile_source.read_bytes()).hexdigest()
    (snapshot / "engine_versions.py").write_bytes(profile_source.read_bytes())
    model, vertices, triangles, indices = build_model(
        args.robot_model,
        destination,
        garment=args.task == "fold",
        hand_friction=args.hand_friction,
        timestep=args.timestep,
        table_contact=args.table_contact,
        floor_time_constant=args.floor_time_constant,
        edge_time_constant=args.edge_time_constant,
    )
    sides = ("r", "l") if args.task == "fold" else ("r",)
    data = mujoco.MjData(model)
    opened = initial_pose(model, sides)
    data.qpos[:] = opened

    print("Settling the passive cloth with the hands parked", flush=True)
    settle_cloth(model, data, opened,
                 output=destination / "settling" if args.record_settling else None,
                 engine=engine)
    configure_phase(model, solver=mujoco.mjtSolver.mjSOL_NEWTON,
                    timestep=args.timestep)

    state = data.qpos.copy()
    np.save(destination / "settled.npy", state)
    plans = []
    for side in sides:
        print(
            f"Planning {side} hand: pad contacts, table clearance and arm reach",
            flush=True,
        )
        plan = plan_grasp(model, state, side, indices, args.task, args.grasp_inset,
                          args.pre_lift_retreat, args.release_retreat)
        if not any(
            set(plan["material_ids"]) == set(triangle) for triangle in triangles
        ):
            raise ValueError("The material anchor must lie on an actual cloth triangle")
        plans.append(plan)
        state[plan["arm"]] = plan["opened"][plan["arm"]]
        np.savez_compressed(destination / f"plan-{side}.npz", **plan)
    data.qpos[:] = state
    data.qvel[:] = 0
    data.time = 0
    verify_combined_path(model, state, plans)
    mujoco.mj_forward(model, data)
    mujoco.mj_saveModel(model, str(destination / "model.mjb"))
    for plan in plans:
        wrist = model.body(plan["side"] + "_wrist").id
        plan["wrist"] = wrist
        plan["anchor_local"] = data.xmat[wrist].reshape(3, 3).T @ (
            plan["point"] - data.xpos[wrist]
        )

    move_end = 7.0 if args.task == "fold" else 4.0
    hold_end = move_end + 1
    release_start = hold_end
    release_end = release_start + 1.5
    retreat_end = release_end + 1
    duration = retreat_end + 1.5
    records, frames = [], []
    maximums = dict(
        hand_penetration_m=0.0,
        table_penetration_m=0.0,
        floor_penetration_m=0.0,
        self_contact_penetration_m=0.0,
        edge_strain=0.0,
        robot_rigid_penetration_m=0.0,
    )
    solver_observations = dict(steps=0, maximum_iterations=0, steps_reaching_iteration_budget=0)
    start = time.monotonic()
    failure = None
    try:
        for tick in range(round(duration / model.opt.timestep)):
            time_s = tick * model.opt.timestep
            if tick % round(0.04 / model.opt.timestep) == 0:
                frames.append(data.qpos.copy())
            target = state.copy()
            for plan in plans:
                arm, hand = plan["arm"], plan["hand"]
                fraction = smooth(time_s, 1.75, move_end)
                fraction *= len(plan["path"]) - 1
                lower = min(int(fraction), len(plan["path"]) - 2)
                blend = fraction - lower
                target[arm] = (1 - blend) * plan["path"][lower, arm] + blend * plan[
                    "path"
                ][lower + 1, arm]
                closing = smooth(time_s, 0.25, 1.25) * (
                    1 - smooth(time_s, release_start, release_end)
                )
                target[hand] = (1 - closing) * plan["opened"][hand] + closing * plan[
                    "closed"
                ]
                retreat = smooth(time_s, release_end, retreat_end)
                target[arm] = (1 - retreat) * target[arm] + retreat * plan["retreat"][
                    arm
                ]
            step(model, data, target)
            solver_iterations = int(np.max(data.solver_niter, initial=0))
            solver_observations["steps"] += 1
            solver_observations["maximum_iterations"] = max(
                solver_observations["maximum_iterations"], solver_iterations)
            solver_observations["steps_reaching_iteration_budget"] += int(
                solver_iterations >= model.opt.iterations)
            forces, hand_depth, table_depth, self_depth, floor_depth = contact_measurements(
                model, data
            )
            strain = float(
                np.max(np.abs(data.flexedge_length / model.flexedge_length0 - 1))
            )
            measurements = dict(
                hand_penetration_m=hand_depth,
                table_penetration_m=table_depth,
                floor_penetration_m=floor_depth,
                self_contact_penetration_m=self_depth,
                edge_strain=strain,
                robot_rigid_penetration_m=robot_penetration(model, data),
            )
            for name, value in measurements.items():
                maximums[name] = max(maximums[name], value)
            if strain > 0.5 or hand_depth > 0.01:
                raise RuntimeError(
                    f"Invalid cloth deformation/contact at {time_s:.3f} s"
                )
            if tick % round(0.01 / model.opt.timestep) == 0:
                material, anchors, far_material = {}, {}, {}
                for plan in plans:
                    side, wrist = plan["side"], plan["wrist"]
                    material[side] = (
                        plan["material_weights"]
                        @ data.flexvert_xpos[plan["material_ids"]]
                    ).tolist()
                    anchors[side] = (
                        data.xpos[wrist]
                        + data.xmat[wrist].reshape(3, 3) @ plan["anchor_local"]
                    ).tolist()
                    if args.task == "fold":
                        far_material[side] = data.flexvert_xpos[plan["far_id"]].tolist()
                heights = data.flexvert_xpos[:, 2]
                records.append(
                    dict(
                        time_s=time_s,
                        contact_measurement_complete=True,
                        solver_iterations=solver_iterations,
                        material=material,
                        anchors=anchors,
                        far_material=far_material,
                        cloth_height_range_m=[
                            float(heights.min()),
                            float(heights.max()),
                        ],
                        forces=forces,
                        edge_strain=strain,
                        hand_penetration_m=hand_depth,
                        table_penetration_m=table_depth,
                        floor_penetration_m=floor_depth,
                        self_contact_penetration_m=self_depth,
                        robot_rigid_penetration_m=measurements[
                            "robot_rigid_penetration_m"
                        ],
                    )
                )
            if tick % round(0.5 / model.opt.timestep) == 0:
                grasp_forces = {
                    side: round(
                        sum(
                            value
                            for name, value in forces.items()
                            if name.startswith(f"collision_{side}_")
                        ),
                        3,
                    )
                    for side in sides
                }
                print(
                    f"t={time_s:.1f}s contacts={data.ncon} strain={strain:.4f} hand_force_N={grasp_forces} wall={time.monotonic() - start:.1f}s",
                    flush=True,
                )
                (destination / "progress.json").write_text(
                    json.dumps(records[-1], indent=2)
                )
    except RuntimeError as error:
        failure = str(error)

    validation = verify_episode(
        records,
        maximums,
        plans,
        task=args.task,
        hold_end=hold_end,
        duration=duration,
        failure=failure,
    )
    metadata = dict(
        task=args.task,
        engine="MuJoCo",
        version=mujoco.__version__,
        timestep_s=float(model.opt.timestep),
        sample_dt_s=0.01,
        solver="Newton",
        solver_observations=solver_observations,
        friction_cone="pyramidal",
        initialization_solver="CG",
        initialization_timestep_s=0.0005,
        initial_condition="Cloth positions come from passive settling; velocities are zeroed before the pregrasp episode.",
        iterations=int(model.opt.iterations),
        wall_time_s=time.monotonic() - start,
        cloth_vertices=len(vertices),
        cloth_triangles=len(triangles),
        attachments=0,
        cloth_actuators=0,
        hand_sliding_friction=args.hand_friction,
        grasp_inset_barycentric=args.grasp_inset,
        pre_lift_retreat_m=args.pre_lift_retreat,
        release_retreat_m=args.release_retreat,
        nominal_shell_thickness_m=0.0005,
        collision_radius_m=0.0012,
        table_contact=args.table_contact,
        requested_floor_time_constant_s=args.floor_time_constant,
        requested_edge_time_constant_s=args.edge_time_constant,
        constraint_time_constant_scope="Nominal compliance parameters; native reference-safety timestep clamp remains enabled.",
        failure=failure,
        maximums=maximums,
        completed=failure is None,
        verified=validation["passed"],
        validation=validation,
        engine_identity=engine,
        integrator=mujoco.mjtIntegrator(model.opt.integrator).name,
        robot_model_sha256=hashlib.sha256(args.robot_model.read_bytes()).hexdigest(),
        schedule_s=dict(
            move_start=1.75,
            move_end=move_end,
            hold_end=hold_end,
            release_start=release_start,
            release_end=release_end,
            retreat_end=retreat_end,
            duration=duration,
        ),
        limitation="Known-state single-layer panel; uncalibrated material and controller parameters; no real-hardware validation.",
        source_sha256=source_sha256,
    )
    (destination / "summary.json").write_text(json.dumps(metadata, indent=2))
    (destination / "trace.json").write_text(json.dumps(records, indent=2))
    np.savez_compressed(
        destination / "states.npz",
        qpos=frames,
        triangles=triangles,
        rest_vertices=vertices,
        time_s=np.arange(len(frames)) * 0.04,
    )
    if not args.no_video and frames:
        render(model, frames, destination, args.task)
    if failure:
        raise RuntimeError(failure)
    print(json.dumps(metadata, indent=2), flush=True)
    if not validation["passed"]:
        raise RuntimeError(
            "Episode completed but failed acceptance checks; inspect summary.json"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=("grasp", "fold"), default="grasp")
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--table-contact", choices=("box", "convex-mesh"), default="box",
                        help="Explicit table representation control; box preserves the historical baseline")
    parser.add_argument("--record-settling", action="store_true",
                        help="Keep every passive-settling state for offline table-crossing diagnosis")
    parser.add_argument("--hand-friction", type=float, default=1.0)
    parser.add_argument("--grasp-inset", type=float, default=0.3)
    parser.add_argument("--pre-lift-retreat", type=float, default=0.06,
                        help="Horizontal clearance before lifting, in metres; does not relax collision checks")
    parser.add_argument("--release-retreat", type=float, default=0.08,
                        help="Horizontal withdrawal after opening, in metres; all contact checks remain active")
    parser.add_argument("--floor-time-constant", type=float, default=0.002,
                        help="Nominal floor-contact solref time constant (s); native reference safety remains enabled")
    parser.add_argument("--edge-time-constant", type=float, default=0.002,
                        help="Nominal edge-equality solref time constant (s); not measured material calibration")
    parser.add_argument("--timestep", type=float, default=0.00025)
    arguments = parser.parse_args()
    try:
        run(arguments)
    except (RuntimeError, ValueError) as error:
        report = arguments.output / "summary.json"
        if not report.exists():
            arguments.output.mkdir(parents=True, exist_ok=True)
            report.write_text(
                json.dumps(
                    dict(
                        task=arguments.task,
                        completed=False,
                        verified=False,
                        failure=str(error),
                    ),
                    indent=2,
                )
            )
        raise
