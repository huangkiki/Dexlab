"""Fixed-control UniSim candidate comparison against the native pinch fixture.

Requires the separately frozen FP64 adapter candidate. This does not migrate
the production task or replace its independent native contact ledger.
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


def run(output, reference_file):
    dt = .0005
    reference = json.loads(reference_file.read_text())
    if reference["protocol"]["dt_s"] != dt:
        raise ValueError("Adapter qualification is fixed at dt=.0005, no case overrides")
    conditions = ["pinch", "open_negative"]
    repeats = 2
    os.environ.setdefault("QD_NUM_THREADS", "2")
    if version("genesis-world") != "1.4.3":
        raise RuntimeError("Frozen protocol requires Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    write_json(output / "protocol.json", {
        "schema": 1, "route": "isolated_adapter_candidate", "engine": version("genesis-world"),
        "quadrants": version("quadrants"), "torch": version("torch"),
        "dt_s": dt, "steps": round(4 / dt), "duration_s": 4,
        "mass_kg": .064, "cube_size_m": .04, "mu": .5, "gravity_m_s2": 9.81,
        "backend": "cpu", "precision": "64", "seed": 0,
        "repeats": repeats, "conditions": conditions,
        "plane_cube_geom_timeconst_s": .002,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Adapter equivalence qualification, not hardware calibration",
    })
    (output / "reference.json").write_bytes(reference_file.read_bytes())
    from dexlab.adapter_qualification import compare_initial
    model = output / "gripper.xml"
    model.write_text(MODEL)
    timings = {"clock": "perf_counter; synchronous CPU readback", "trials": [],
               "rendering": "not executed", "archival": "not executed",
               "scope": "instrumented CPU run; process import and package installation excluded"}
    started = time.perf_counter()
    backend = None
    try:
        phase = time.perf_counter()
        import numpy as np
        from unisim.scene import SceneCfg
        from unisim.entities import SceneEntitySpec, EntityInitialState
        from unisim.dr.types import ModelSourceDescriptor
        from unisim.backend.genesis.backend import GenesisBackend

        xml = MODEL.replace('<geom type="box"', '<geom name="left_pad" type="box"', 1)
        xml = xml.replace('<geom type="box"', '<geom name="right_pad" type="box"', 1)
        actuators = ('<actuator><position name="lift" joint="lift" kp="1000" kv="50" '
                     'forcerange="-50 50"/><position name="left" joint="left_slide" '
                     'kp="500" kv="20" forcerange="-10 10"/><position name="right" '
                     'joint="right_slide" kp="500" kv="20" forcerange="-10 10"/></actuator>')
        model.write_text(xml.replace('</mujoco>', actuators + '</mujoco>'))
        plane_file = output / "plane.xml"
        plane_file.write_text('<mujoco><worldbody><body name="ground"><geom name="plane" '
            'type="plane" size="0 0 .1" friction=".5 0 0" solref=".002 1"/>'
            '</body></worldbody></mujoco>')
        cube_file = output / "cube.xml"
        cube_file.write_text('<mujoco><worldbody><body name="block"><freejoint name="free"/>'
            '<geom name="cube" type="box" size=".02 .02 .02" mass=".064" '
            'friction=".5 0 0" solref=".002 1"/></body></worldbody></mujoco>')
        sensors = output / "sensors.xml"
        sensors.write_text('<mujoco><sensor>' + ''.join(
            f'<contact name="{name}" geom1="block/cube" geom2="{other}" '
            'data="force" reduce="netforce"/>'
            for name, other in (("left_force", "gripper/left_pad"),
                                ("right_force", "gripper/right_pad"),
                                ("ground_force", "ground/plane"))) + '</sensor></mujoco>')
        backend = GenesisBackend(SceneCfg(entity_assets=(
            SceneEntitySpec('gripper', ModelSourceDescriptor(str(model)), root_mode='fixed'),
            SceneEntitySpec('ground', ModelSourceDescriptor(str(plane_file)),
                            kind='rigid', root_mode='fixed'),
            SceneEntitySpec('block', ModelSourceDescriptor(str(cube_file)), kind='rigid',
                            root_mode='floating', initial_state=EntityInitialState(position=(0., 0., .02)))),
            fragment_files=[str(sensors)]), 1, dt,
            friction_cone='elliptic', actuated_armature=0.)
        backend.materialize()
        timings["adapter_materialize_s"] = time.perf_counter() - phase
        scene = backend._scene  # Explicit native evidence access, not portable API reuse.
        plane = next(e for e in scene.entities if e.name == 'ground')
        gripper = next(e for e in scene.entities if e.name == 'gripper')
        cube = next(e for e in scene.entities if e.name == 'block')
        joints = [gripper.get_joint(name) for name in ("lift", "left_slide", "right_slide")]
        options = scene.sim.rigid_solver._options
        for condition in conditions:
            for repeat in range(repeats):
                trial_cost = {"condition": condition, "repeat": repeat, "control_s": 0.,
                              "step_s": 0., "observations_s": 0., "step_count": round(4/dt)}
                phase = time.perf_counter()
                backend.reset()
                trial_cost["reset_s"] = time.perf_counter() - phase
                phase = time.perf_counter()
                reset_sensors = {name: backend.get_sensor_data(name).tolist()
                                 for name in ("left_force", "right_force", "ground_force")}
                assert all(np.count_nonzero(value) == 0 for value in reset_sensors.values())
                initial = {
                    "adapter_reset_sensors": reset_sensors,
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
                    "options": options.model_dump(mode="json"),
                }
                admission = compare_initial(initial, reference["trials"][f"{condition}-{repeat}.json"]["initial"], storage_trial=True)
                write_json(output / f"{condition}-{repeat}-admission.json",
                           {"initial": initial, "comparison": admission})
                if not admission["passed"]:
                    raise RuntimeError(f"Initial admission rejected: {admission['failures']}")
                trial_cost["setup_readback_s"] = time.perf_counter() - phase
                rows = []
                for step in range(round(4 / dt)):
                    t = step * dt
                    closure = .012 * min(t / .5, 1) if condition == "pinch" and t < 3.2 else 0
                    lift = .08 * max(0, min(t - 1, 1))
                    phase = time.perf_counter()
                    command = np.array([[lift, closure, closure]], dtype=np.float64)
                    trial_cost["control_s"] += time.perf_counter() - phase
                    phase = time.perf_counter()
                    backend.step(command)
                    elapsed = time.perf_counter() - phase
                    trial_cost["step_s"] += elapsed
                    if step == 0:
                        trial_cost["first_step_s"] = elapsed
                    phase = time.perf_counter()
                    rows.append({
                        "time": (step + 1) * dt, "command": [lift, closure, closure],
                        "q": gripper.get_dofs_position().tolist(),
                        "object_quat": cube.get_quat().tolist(),
                        "object_pos": cube.get_pos().tolist(), "object_vel": cube.get_vel().tolist(),
                        "object_contact_force": cube.get_links_net_contact_force().tolist(),
                        "adapter_state": {k: v.tolist() for k, v in
                                          backend.get_entity_state('block').items()},
                        "adapter_forces": {name: backend.get_sensor_data(name).tolist()
                                           for name in ("left_force", "right_force", "ground_force")},
                        "contacts": {k: v.tolist() for k, v in cube.get_contacts().items()},
                    })
                    trial_cost["observations_s"] += time.perf_counter() - phase
                phase = time.perf_counter()
                write_json(output / f"{condition}-{repeat}.json", {
                    "condition": condition, "repeat": repeat,
                    "initial": initial, "samples": rows})
                trial_cost["serialize_write_s"] = time.perf_counter() - phase
                timings["trials"].append(trial_cost)
    except Exception as error:
        write_json(output / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        phase = time.perf_counter()
        if backend is not None:
            backend.close()
        timings["destroy_s"] = time.perf_counter() - phase
        timings["total_after_import_s"] = time.perf_counter() - started
        write_json(output / "timings.json", timings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference", type=Path, required=True,
                        help="Frozen initial-state reference extracted from existing native evidence")
    args = parser.parse_args()
    run(args.output, args.reference)
