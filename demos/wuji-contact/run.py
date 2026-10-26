"""Record a bounded fixed-wrist grasp attempt. Score separately from raw data."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import mujoco
import numpy as np

import scene
import plan_wuji_pinch


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3 - 2 * value)


def target_at(t, case, plan, config):
    opened, closed = np.array(plan["open"]), np.array(plan["closed"])
    if case == "open":
        return opened
    target = opened + smooth((t - .2) / .6) * (closed - opened)
    if t >= config["action_start_s"]:
        ratio = smooth((t - config["action_start_s"]) / config["action_ramp_s"])
        if case.startswith("unload-"):
            finger = case.removeprefix("unload-")
            ids = [i for i, name in enumerate(plan["joint_names"]) if name.startswith("r_" + finger)]
            target[ids] += ratio * (opened[ids] - target[ids])
        else:
            target += ratio * (opened - target)
    return target


def record(output, robot_root, protocol_path, case):
    config = json.loads(protocol_path.read_text())
    if case not in config["cases"]:
        raise ValueError("Case must be frozen in the protocol")
    if mujoco.__version__ != config["mujoco_version"]:
        raise ValueError("Native runtime differs from frozen protocol")
    asset_sha = scene.verify_assets(robot_root, Path(__file__).with_name("assets.json"))
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (Path(__file__), Path(scene.__file__), Path(plan_wuji_pinch.__file__), protocol_path)}
    metadata = dict(state="started", case=case, source_sha256=source,
                    asset_manifest_sha256=asset_sha, version=mujoco.__version__, config=config)
    (output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    plan = scene.build(robot_root, output / "model", config)
    model = mujoco.MjModel.from_xml_path(str(output / "model/scene.xml"))
    data = mujoco.MjData(model)
    object_body, object_geom = model.body("object").id, model.geom("object").id
    if model.nu != 20 or model.nq != 27 or model.neq != 0:
        raise ValueError("Unexpected native model topology or auxiliary equality")
    if case == "no-contact":
        model.geom_contype[object_geom] = model.geom_conaffinity[object_geom] = 0
    if case == "zero-friction":
        model.geom_friction[:] = 0
    data.qpos[:20] = plan["open"]
    initial = np.asarray(plan["object_position"])
    dt, control_steps = model.opt.timestep, config["control_steps"]
    steps = round(config["duration_s"] / dt)
    if not np.isclose(steps * dt, config["duration_s"], atol=1e-12):
        raise ValueError("Duration must be a whole number of native steps")
    limits = model.actuator_forcerange[:, 1].copy()
    raw = {"qpos_before": [], "qpos_after": [], "qvel_before": [], "qvel_after": [],
           "time_s": [], "target": [], "requested_torque": [], "actuator_force": [],
           "support_force": [], "object_contact_force": [], "solver_niter": [],
           "solver_last_gradient": [], "solver_last_improvement": [], "warnings": [],
           "max_penetration_m": [], "step_wall_s": [], "qfrc_applied": [], "external_wrenches": []}
    contacts = []
    contact_offsets = [0]
    requested = np.zeros(model.nu)
    target = target_at(0., case, plan, config)
    try:
        for step in range(steps):
            t = step * dt
            if step % control_steps == 0:
                target = target_at(t, case, plan, config)
                mujoco.mj_forward(model, data)
                requested = (config["kp_nm_rad"] * (target - data.qpos[:20])
                             - config["kd_nms_rad"] * data.qvel[:20] + data.qfrc_bias[:20])
                data.ctrl[:] = np.clip(requested, -limits, limits)
            data.xfrc_applied[:] = 0
            if t < config["support_end_s"]:
                data.xfrc_applied[object_body, :3] = (
                    -model.body_mass[object_body] * model.opt.gravity
                    + config["preparation_kp_n_m"] * (initial - data.qpos[20:23])
                    - config["preparation_kd_ns_m"] * data.qvel[20:23])
            raw["qpos_before"].append(data.qpos.copy())
            raw["qvel_before"].append(data.qvel.copy())
            raw["time_s"].append(t)
            raw["target"].append(target)
            raw["requested_torque"].append(requested.copy())
            raw["support_force"].append(data.xfrc_applied[object_body, :3].copy())
            raw["qfrc_applied"].append(data.qfrc_applied.copy())
            raw["external_wrenches"].append(data.xfrc_applied.copy())
            tick = time.monotonic()
            mujoco.mj_step(model, data)
            raw["step_wall_s"].append(time.monotonic() - tick)
            total = np.zeros(3)
            for index, contact in enumerate(data.contact):
                if object_geom not in (contact.geom1, contact.geom2):
                    continue
                local = np.zeros(6)
                mujoco.mj_contactForce(model, data, index, local)
                sign = 1. if contact.geom2 == object_geom else -1.
                force = sign * contact.frame.reshape(3, 3).T @ local[:3]
                total += force
                other = int(contact.geom1 if contact.geom2 == object_geom else contact.geom2)
                # Native force is on geom2; preserve ordering and frame for independent reconstruction.
                contacts.append(np.r_[contact.geom1, contact.geom2, model.geom_bodyid[other],
                                       contact.pos, contact.frame, contact.dist, local])
            contact_offsets.append(len(contacts))
            raw["object_contact_force"].append(total)
            raw["actuator_force"].append(data.actuator_force.copy())
            raw["qpos_after"].append(data.qpos.copy())
            raw["qvel_after"].append(data.qvel.copy())
            raw["solver_niter"].append(data.solver_niter.copy())
            gradients, improvements = [], []
            for island, count in enumerate(data.solver_niter):
                if count:
                    stat = data.solver[island * mujoco.mjNSOLVER + min(count, mujoco.mjNSOLVER) - 1]
                    gradients.append(stat.gradient)
                    improvements.append(stat.improvement)
            raw["solver_last_gradient"].append(max(gradients, default=0.))
            raw["solver_last_improvement"].append(max(improvements, default=0.))
            raw["warnings"].append(data.warning.number.copy())
            raw["max_penetration_m"].append(max(0., max((-c.dist for c in data.contact), default=0.)))
            if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                raise ValueError("Non-finite native state; preserve the unfinished attempt")
    except BaseException as error:
        np.savez_compressed(output / "partial-observations.npz", **{k: np.asarray(v) for k, v in raw.items()},
                            contacts=np.asarray(contacts).reshape(-1, 22), contact_offsets=np.asarray(contact_offsets))
        metadata.update(state="failed", error=f"{type(error).__name__}: {error}", wall_s=time.monotonic()-started)
        (output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
        raise
    raw = {key: np.asarray(value) for key, value in raw.items()}
    raw["contacts"] = np.asarray(contacts).reshape(-1, 22)
    raw["contact_offsets"] = np.asarray(contact_offsets)
    np.savez_compressed(output / "observations.npz", **raw)
    metadata.update(state="recorded", wall_s=time.monotonic() - started,
                    force_epoch="Pre-integration solve of each mj_step; qpos/qvel before and after saved. Native force is on geom2 in contact frame.",
                    effective=dict(timestep=dt, control_period_s=control_steps * dt,
                                   gravity=model.opt.gravity.tolist(), object_mass=float(model.body_mass[object_body]),
                                   object_inertia=model.body_inertia[object_body].tolist(), object_geom_id=object_geom,
                                   object_body_id=object_body, eq_count=model.neq,
                                   actuator_force_limits=limits.tolist(), geom_friction=model.geom_friction.tolist(),
                                   geom_solref=model.geom_solref.tolist(), geom_solimp=model.geom_solimp.tolist(),
                                   geom_condim=model.geom_condim.tolist(), joint_range=model.jnt_range.tolist(),
                                   geom_contype=model.geom_contype.tolist(), geom_conaffinity=model.geom_conaffinity.tolist(),
                                   body_names=[model.body(i).name for i in range(model.nbody)],
                                   geom_names=[model.geom(i).name for i in range(model.ngeom)],
                                   solver=int(model.opt.solver), iterations=model.opt.iterations,
                                   tolerance=model.opt.tolerance, cone=int(model.opt.cone),
                                   integrator=int(model.opt.integrator), precision="float64"))
    metadata["observations_sha256"] = hashlib.sha256((output / "observations.npz").read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(dict(case=case, state="recorded", wall_s=metadata["wall_s"], steps=steps)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--robot-assets", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=Path(__file__).with_name("protocol.json"))
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    record(args.output, args.robot_assets, args.protocol, args.case)


if __name__ == "__main__":
    main()
