"""Prescribed actuator clamp/lift/release; no cloth attachments or learned policy."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from time import monotonic

from dexlab.genesis_cloth_probe import write_grid
from dexlab.genesis_pinch_probe import MODEL


def run(output, gravity_compensation=False):
    output.mkdir(parents=True, exist_ok=False)
    mesh = output / "cloth.obj"
    write_grid(mesh)
    model = output / "gripper.xml"
    model.write_text(MODEL)
    record = {
        "completed": False,
        "scenes": [],
        "dt_s": 0.002,
        "steps": 2000,
        "repeats": 2,
        "gravity_compensation": gravity_compensation,
        "scope": "Synthetic prismatic gripper, prescribed PD; not hardware or learned control",
    }
    start = monotonic()
    try:
        import genesis as gs

        record["version"] = version("genesis-world")
        if record["version"] != "1.4.3":
            raise RuntimeError("Frozen runtime changed")
        record["runner_sha256"] = hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()
        for coupled in (True, False):
            case = {"coupled": coupled, "episodes": []}
            record["scenes"].append(case)
            print("Building coupling", coupled, flush=True)
            gs.init(
                backend=gs.cpu,
                precision="64",
                seed=0,
                use_deterministic_algorithms=True,
                logging_level="warning",
            )
            try:
                begin = monotonic()
                pbd = gs.options.PBDOptions(
                    particle_size=0.008,
                    lower_bound=(-1, -1, -1),
                    upper_bound=(1, 1, 1),
                    max_stretch_solver_iterations=4,
                    max_bending_solver_iterations=1,
                )
                scene = gs.Scene(
                    show_viewer=False,
                    sim_options=gs.options.SimOptions(dt=0.002, substeps=1),
                    pbd_options=pbd,
                    rigid_options=gs.options.RigidOptions(
                        noslip_iterations=0, friction_cone=gs.friction_cone.elliptic
                    ),
                )
                scene.add_entity(
                    gs.morphs.Plane(), material=gs.materials.Rigid(friction=0.5)
                )
                gripper = scene.add_entity(
                    gs.morphs.MJCF(file=str(model)),
                    material=gs.materials.Rigid(
                        friction=0.5, coup_friction=0.5, needs_coup=coupled
                    ),
                )
                material = gs.materials.PBD.Cloth(
                    rho=0.2,
                    static_friction=0.5,
                    kinetic_friction=0.5,
                    stretch_compliance=1e-7,
                    bending_compliance=1e-5,
                    stretch_relaxation=0.3,
                    bending_relaxation=0.1,
                    air_resistance=0,
                )
                cloth = scene.add_entity(
                    gs.morphs.Mesh(
                        file=str(mesh),
                        pos=(0, 0, 0.024),
                        euler=(0, 90, 0),
                        decimate=False,
                    ),
                    material=material,
                )
                scene.build()
                case["build_s"] = monotonic() - begin
                if gripper.n_dofs != 3:
                    raise RuntimeError("Expected three prismatic DOFs")
                joints = [
                    gripper.get_joint(name)
                    for name in ("lift", "left_slide", "right_slide")
                ]
                indices = [j.dofs_idx_local[0] for j in joints]
                pads = [gripper.get_link(name).idx_local for name in ("left", "right")]
                gripper.set_dofs_armature([0] * 3)
                gripper.set_dofs_kp([1000, 500, 500], dofs_idx_local=indices)
                gripper.set_dofs_kv([50, 20, 20], dofs_idx_local=indices)
                gripper.set_dofs_force_range(
                    [-50, -10, -10], [50, 10, 10], dofs_idx_local=indices
                )
                mass = float(gripper.get_mass())
                lift_kp = float(gripper.get_dofs_kp()[indices[0]])
                bias = 9.81 * mass / lift_kp if gravity_compensation else 0.0
                case["native"] = {
                    "gripper_movable_mass_kg": mass,
                    "lift_bias_m": bias,
                    "faces": cloth._mesh.faces.tolist(),
                    "mass": cloth.solver.particles_info.mass.to_numpy().tolist(),
                    "particle_count": cloth.n_particles,
                    "pbd": pbd.model_dump(mode="json"),
                    "material": material.model_dump(mode="json"),
                    "kp": gripper.get_dofs_kp().tolist(),
                    "kv": gripper.get_dofs_kv().tolist(),
                    "armature": gripper.get_dofs_armature().tolist(),
                    "force_range": [x.tolist() for x in gripper.get_dofs_force_range()],
                    "pad_halfsize_m": [0.01, 0.03, 0.02],
                }

                def sample(step, command):
                    return {
                        "step": step,
                        "command": command,
                        "q": gripper.get_dofs_position().tolist(),
                        "qvel": gripper.get_dofs_velocity().tolist(),
                        "actuator_force": gripper.get_dofs_control_force().tolist(),
                        "pad_pos": gripper.get_links_pos(links_idx_local=pads).tolist(),
                        "pad_quat": gripper.get_links_quat(
                            links_idx_local=pads
                        ).tolist(),
                        "pos": cloth.get_particles_pos().tolist(),
                        "vel": cloth.get_particles_vel().tolist(),
                    }

                for repeat in range(2):
                    scene.reset()
                    gripper.set_dofs_position(
                        [0, 0.0255, 0.0255], dofs_idx_local=indices
                    )
                    initial = [bias, 0.0255, 0.0255]
                    gripper.control_dofs_position(initial, dofs_idx_local=indices)
                    episode = {
                        "repeat": repeat,
                        "rows": [sample(0, initial)],
                        "step_s": 0.0,
                        "observation_s": 0.0,
                    }
                    case["episodes"].append(episode)
                    for step in range(2000):
                        t = step * 0.002
                        closure = 0.0255 + 0.00075 * min(t / 0.2, 1) if t < 3.2 else 0
                        lift = 0.08 * max(0, min(t - 1, 1)) + bias
                        command = [lift, closure, closure]
                        gripper.control_dofs_position(command, dofs_idx_local=indices)
                        begin = monotonic()
                        scene.step()
                        episode["step_s"] += monotonic() - begin
                        begin = monotonic()
                        episode["rows"].append(sample(step + 1, command))
                        episode["observation_s"] += monotonic() - begin
                    print("coupled", coupled, "repeat", repeat, "complete", flush=True)
            finally:
                gs.destroy()
        record["completed"] = True
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        record["wall_s"] = monotonic() - start
        (output / "record.json").write_text(
            json.dumps(record, indent=2, allow_nan=True) + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--gravity-compensation", action="store_true")
    args = parser.parse_args()
    run(args.output, args.gravity_compensation)
