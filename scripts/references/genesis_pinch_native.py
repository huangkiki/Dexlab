"""Native-only comparison reference; never a production fallback.

Based on genesis_pinch_probe at c34e74e1415742bfe7d3884a435db4f14adc5609.
The default retains the original setup. --batched-info explicitly selects the
storage-aligned native reference; it is not identical to the historical path.
Model, controls, reset and score thresholds are unchanged in either profile.
"""
import argparse
import hashlib
import json
import os
import time
from importlib.metadata import version
from pathlib import Path

MODEL = '<mujoco><compiler angle="radian"/><worldbody><body name="base"><body name="carriage"><joint name="lift" type="slide" axis="0 0 1" range="0 0.15" limited="true"/><inertial pos="0 0 0" mass="1" diaginertia="0.01 0.01 0.01"/>\n<body name="left" pos="-0.04 0 0.025"><joint name="left_slide" type="slide" axis="1 0 0" range="0 0.03" limited="true"/><geom type="box" size="0.01 0.03 0.02" mass="0.1" friction="0.5"/></body>\n<body name="right" pos="0.04 0 0.025"><joint name="right_slide" type="slide" axis="-1 0 0" range="0 0.03" limited="true"/><geom type="box" size="0.01 0.03 0.02" mass="0.1" friction="0.5"/></body></body></body></worldbody></mujoco>'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_case(case_id):
    manifest = Path(__file__).resolve().parents[2] / "demos/contact-benchmark/force-limit-v1.json"
    protocol = json.loads(manifest.read_text())
    for case in protocol["cases"]:
        if case["id"] == case_id:
            return case
    raise ValueError(f"Unknown preregistered case: {case_id}")


def complete_contacts(scene, t, dt):
    """Record untouched native identities and B-to-A normals for offline translation."""
    contacts = scene.rigid_solver.collider.get_contacts(as_tensor=True, to_torch=True)
    return {
        "native": {key: value.tolist() for key, value in contacts.items()},
        "state_time": t + dt, "geometry_time": t,
        "force_start_time": t, "force_end_time": t + dt,
        "normal_orientation": "native B to A", "force_side": "B",
    }


def run(output, dt, case_id=None, *, batched_info=False):
    case = load_case(case_id) if case_id is not None else None
    if case is not None and dt != .0005:
        raise ValueError("Force-limit protocol requires dt=0.0005")
    cap = case["force_limit_N"] if case else 10.
    initial_x = case["initial_x_m"] if case else 0.
    conditions = [case["condition"]] if case else ["pinch", "open_negative"]
    repeats = 1 if case else 2
    os.environ.setdefault("QD_NUM_THREADS", "2")
    import genesis as gs
    if version("genesis-world") != "1.4.3":
        raise RuntimeError("Frozen protocol requires Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    if case is not None:
        manifest = Path(__file__).resolve().parents[2] / 'demos/contact-benchmark/force-limit-v1.json'
        (output / manifest.name).write_bytes(manifest.read_bytes())
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    write_json(output / "protocol.json", {
        "schema": 2 if case else 1, "case": case, "engine": version("genesis-world"),
        "route": "frozen_native_reference", "native_base_revision": "c34e74e1415742bfe7d3884a435db4f14adc5609",
        "batched_info": batched_info,
        "quadrants": version("quadrants"), "torch": version("torch"),
        "dt_s": dt, "steps": round(4 / dt), "duration_s": 4,
        "mass_kg": .064, "cube_size_m": .04, "mu": .5, "gravity_m_s2": 9.81,
        "backend": "cpu", "precision": "64", "seed": 0,
        "repeats": repeats, "conditions": conditions,
        "plane_cube_geom_timeconst_s": .002,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Preregistered fixed challenge; not hardware calibration" if case else
                 "Primitive development fixture, not SDF or hardware calibration",
    })
    model = output / "gripper.xml"
    model.write_text(MODEL)
    timings = {"clock": "perf_counter; synchronous CPU readback", "trials": [],
               "rendering": "not executed", "archival": "not executed",
               "scope": "instrumented CPU run; process import and package installation excluded"}
    started = time.perf_counter()
    try:
        phase = time.perf_counter()
        gs.init(backend=gs.cpu, precision="64", seed=0,
                use_deterministic_algorithms=True, logging_level="warning")
        timings["init_s"] = time.perf_counter() - phase
        phase = time.perf_counter()
        options = gs.options.RigidOptions(noslip_iterations=0, friction_cone=gs.friction_cone.elliptic,
                                         batch_links_info=batched_info, batch_dofs_info=batched_info)
        scene = gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=dt), rigid_options=options)
        plane = scene.add_entity(gs.morphs.Plane(), material=gs.materials.Rigid(friction=.5))
        gripper = scene.add_entity(gs.morphs.MJCF(file=str(model)), material=gs.materials.Rigid(friction=.5))
        cube = scene.add_entity(gs.morphs.Box(size=(.04,) * 3, pos=(initial_x, 0, .02)),
                                material=gs.materials.Rigid(rho=1000, friction=.5))
        scene.build()
        timings["scene_build_s"] = time.perf_counter() - phase
        if gripper.n_dofs != 3:
            raise RuntimeError("Expected three prismatic gripper DOFs")
        joints = [gripper.get_joint(name) for name in ("lift", "left_slide", "right_slide")]
        indices = [joint.dofs_idx_local[0] for joint in joints]
        gripper.set_dofs_armature([0] * 3)
        gripper.set_dofs_kp([1000, 500, 500], dofs_idx_local=indices)
        gripper.set_dofs_kv([50, 20, 20], dofs_idx_local=indices)
        gripper.set_dofs_force_range([-50, -cap, -cap], [50, cap, cap], dofs_idx_local=indices)
        for geom in (*plane.geoms, *cube.geoms):
            values = geom.get_sol_params().tolist()
            values[0] = .002
            geom.set_sol_params(values)
        for condition in conditions:
            for repeat in range(repeats):
                trial_cost = {"condition": condition, "repeat": repeat, "control_s": 0.,
                              "step_s": 0., "observations_s": 0., "step_count": round(4/dt)}
                phase = time.perf_counter()
                scene.reset()
                trial_cost["reset_s"] = time.perf_counter() - phase
                phase = time.perf_counter()
                gripper.control_dofs_position([0, 0, 0], dofs_idx_local=indices)
                initial = {
                    "cube_mass": cube.get_links_mass().tolist(),
                    "cube_inertia": cube.get_links_inertia().tolist(),
                    "geom_friction": [g.get_friction().item() for g in (*plane.geoms, *cube.geoms, *gripper.geoms)],
                    "gripper_mass": gripper.get_links_mass().tolist(),
                    "armature": gripper.get_dofs_armature().tolist(),
                    "kp": gripper.get_dofs_kp().tolist(), "kv": gripper.get_dofs_kv().tolist(),
                    "force_range": [v.tolist() for v in gripper.get_dofs_force_range()],
                    "q": gripper.get_dofs_position().tolist(),
                    "object_pos": cube.get_pos().tolist(), "object_vel": cube.get_vel().tolist(),
                    "object_quat": cube.get_quat().tolist(), "object_ang": cube.get_ang().tolist(),
                    "qvel": gripper.get_dofs_velocity().tolist(),
                    "geom_sol_params": [g.get_sol_params().tolist() for g in (*plane.geoms, *cube.geoms)],
                    "joint_sol_params": [j.get_sol_params().tolist() for j in joints],
                    "cube_link": cube.link_start, "plane_link": plane.link_start,
                    "pad_links": [gripper.get_link(n).idx for n in ("left", "right")],
                    "requested_options": options.model_dump(mode="json"),
                    "options": scene.rigid_solver._options.model_dump(mode="json"),
                    "reference_geometry_names": {
                        str(plane.geoms[0].idx): "ground/plane",
                        str(cube.geoms[0].idx): "block/cube",
                        **{str(g.idx): "gripper/" + g.link.name + "_pad" for g in gripper.geoms},
                    },
                }
                trial_cost["setup_readback_s"] = time.perf_counter() - phase
                rows = []
                for step in range(round(4 / dt)):
                    t = step * dt
                    closure = .012 * min(t / .5, 1) if condition == "pinch" and t < 3.2 else 0
                    lift = .08 * max(0, min(t - 1, 1))
                    phase = time.perf_counter()
                    gripper.control_dofs_position([lift, closure, closure], dofs_idx_local=indices)
                    trial_cost["control_s"] += time.perf_counter() - phase
                    phase = time.perf_counter()
                    scene.step()
                    elapsed = time.perf_counter() - phase
                    trial_cost["step_s"] += elapsed
                    if step == 0:
                        trial_cost["first_step_s"] = elapsed
                    phase = time.perf_counter()
                    rows.append({
                        "time": (step + 1) * dt, "command": [lift, closure, closure],
                        "q": gripper.get_dofs_position().tolist(),
                        "qvel": gripper.get_dofs_velocity().tolist(),
                        "object_ang": cube.get_ang().tolist(),
                        "object_quat": cube.get_quat().tolist(),
                        "object_pos": cube.get_pos().tolist(), "object_vel": cube.get_vel().tolist(),
                        "object_contact_force": cube.get_links_net_contact_force().tolist(),
                        "contacts": {k: v.tolist() for k, v in cube.get_contacts().items()},
                        "complete_contacts": complete_contacts(scene, t, dt),
                    })
                    trial_cost["observations_s"] += time.perf_counter() - phase
                phase = time.perf_counter()
                write_json(output / f"{condition}-{repeat}.json", {
                    "condition": condition, "repeat": repeat, "case_id": case_id,
                    "initial": initial, "samples": rows})
                trial_cost["serialize_write_s"] = time.perf_counter() - phase
                timings["trials"].append(trial_cost)
    except Exception as error:
        write_json(output / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        phase = time.perf_counter()
        gs.destroy()
        timings["destroy_s"] = time.perf_counter() - phase
        timings["total_after_import_s"] = time.perf_counter() - started
        write_json(output / "timings.json", timings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dt", type=float, choices=(.001, .0005, .00025), default=.0005)
    parser.add_argument("--case-id", help="One frozen force-limit-v1 case in a fresh process")
    parser.add_argument("--batched-info", action="store_true", help="Explicit storage-aligned native profile")
    args = parser.parse_args()
    run(args.output, args.dt, args.case_id, batched_info=args.batched_info)
