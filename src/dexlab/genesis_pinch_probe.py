"""Native primitive pinch/hold/release diagnostic; not an SDF or hardware task."""
import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path

MODEL = '<mujoco><compiler angle="radian"/><worldbody><body name="base"><body name="carriage"><joint name="lift" type="slide" axis="0 0 1" range="0 0.15" limited="true"/><inertial pos="0 0 0" mass="1" diaginertia="0.01 0.01 0.01"/>\n<body name="left" pos="-0.04 0 0.025"><joint name="left_slide" type="slide" axis="1 0 0" range="0 0.03" limited="true"/><geom type="box" size="0.01 0.03 0.02" mass="0.1" friction="0.5"/></body>\n<body name="right" pos="0.04 0 0.025"><joint name="right_slide" type="slide" axis="-1 0 0" range="0 0.03" limited="true"/><geom type="box" size="0.01 0.03 0.02" mass="0.1" friction="0.5"/></body></body></body></worldbody></mujoco>'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(output, dt):
    os.environ.setdefault("QD_NUM_THREADS", "2")
    import genesis as gs
    if version("genesis-world") != "1.4.3":
        raise RuntimeError("Frozen protocol requires Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    write_json(output / "protocol.json", {
        "schema": 1, "engine": version("genesis-world"),
        "quadrants": version("quadrants"), "torch": version("torch"),
        "dt_s": dt, "steps": round(4 / dt), "duration_s": 4,
        "mass_kg": .064, "cube_size_m": .04, "mu": .5, "gravity_m_s2": 9.81,
        "backend": "cpu", "precision": "64", "seed": 0,
        "repeats": 2, "conditions": ["pinch", "open_negative"],
        "plane_cube_geom_timeconst_s": .002,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Primitive development fixture, not SDF or hardware calibration",
    })
    model = output / "gripper.xml"
    model.write_text(MODEL)
    try:
        gs.init(backend=gs.cpu, precision="64", seed=0,
                use_deterministic_algorithms=True, logging_level="warning")
        options = gs.options.RigidOptions(noslip_iterations=0, friction_cone=gs.friction_cone.elliptic)
        scene = gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=dt), rigid_options=options)
        plane = scene.add_entity(gs.morphs.Plane(), material=gs.materials.Rigid(friction=.5))
        gripper = scene.add_entity(gs.morphs.MJCF(file=str(model)), material=gs.materials.Rigid(friction=.5))
        cube = scene.add_entity(gs.morphs.Box(size=(.04,) * 3, pos=(0, 0, .02)),
                                material=gs.materials.Rigid(rho=1000, friction=.5))
        scene.build()
        if gripper.n_dofs != 3:
            raise RuntimeError("Expected three prismatic gripper DOFs")
        joints = [gripper.get_joint(name) for name in ("lift", "left_slide", "right_slide")]
        indices = [joint.dofs_idx_local[0] for joint in joints]
        gripper.set_dofs_armature([0] * 3)
        gripper.set_dofs_kp([1000, 500, 500], dofs_idx_local=indices)
        gripper.set_dofs_kv([50, 20, 20], dofs_idx_local=indices)
        gripper.set_dofs_force_range([-50, -10, -10], [50, 10, 10], dofs_idx_local=indices)
        for geom in (*plane.geoms, *cube.geoms):
            values = geom.get_sol_params().tolist()
            values[0] = .002
            geom.set_sol_params(values)
        for condition in ("pinch", "open_negative"):
            for repeat in range(2):
                scene.reset()
                gripper.control_dofs_position([0, 0, 0], dofs_idx_local=indices)
                initial = {
                    "cube_mass": cube.get_links_mass().tolist(),
                    "gripper_mass": gripper.get_links_mass().tolist(),
                    "armature": gripper.get_dofs_armature().tolist(),
                    "kp": gripper.get_dofs_kp().tolist(), "kv": gripper.get_dofs_kv().tolist(),
                    "force_range": [v.tolist() for v in gripper.get_dofs_force_range()],
                    "q": gripper.get_dofs_position().tolist(),
                    "object_pos": cube.get_pos().tolist(), "object_vel": cube.get_vel().tolist(),
                    "geom_sol_params": [g.get_sol_params().tolist() for g in (*plane.geoms, *cube.geoms)],
                    "joint_sol_params": [j.get_sol_params().tolist() for j in joints],
                    "cube_link": cube.link_start, "plane_link": plane.link_start,
                    "pad_links": [gripper.get_link(n).idx for n in ("left", "right")],
                    "options": options.model_dump(mode="json"),
                }
                rows = []
                for step in range(round(4 / dt)):
                    t = step * dt
                    closure = .012 * min(t / .5, 1) if condition == "pinch" and t < 3.2 else 0
                    lift = .08 * max(0, min(t - 1, 1))
                    gripper.control_dofs_position([lift, closure, closure], dofs_idx_local=indices)
                    scene.step()
                    rows.append({
                        "time": (step + 1) * dt, "command": [lift, closure, closure],
                        "q": gripper.get_dofs_position().tolist(),
                        "object_quat": cube.get_quat().tolist(),
                        "object_pos": cube.get_pos().tolist(), "object_vel": cube.get_vel().tolist(),
                        "object_contact_force": cube.get_links_net_contact_force().tolist(),
                        "contacts": {k: v.tolist() for k, v in cube.get_contacts().items()},
                    })
                write_json(output / f"{condition}-{repeat}.json", {
                    "condition": condition, "repeat": repeat, "initial": initial, "samples": rows})
    except Exception as error:
        write_json(output / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        gs.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dt", type=float, choices=(.001, .0005, .00025), default=.0005)
    args = parser.parse_args()
    run(args.output, args.dt)
