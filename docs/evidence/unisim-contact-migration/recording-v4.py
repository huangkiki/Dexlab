"""Candidate public-UniSim recording route for the existing pinch protocol.

Production remains on the frozen native reference until physical comparison
and the repository delivery gates pass. This module owns no engine handles.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np

from dexlab.genesis_pinch_probe import MODEL, load_case, write_json

JOINTS = ("lift", "left_slide", "right_slide")
GEOMS = ("ground/plane", "block/cube", "gripper/left_pad", "gripper/right_pad")


def create_scene(output: Path, cap: float, initial_x: float):
    """Author the protocol's geometry and drive inputs using portable sources."""
    from unisim import EntityInitialState, SceneEntitySpec
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.scene import SceneCfg

    gripper = ET.fromstring(MODEL)
    for geom, name in zip(gripper.iter("geom"), ("left_pad", "right_pad"), strict=True):
        geom.set("name", name)
    actuators = ET.SubElement(gripper, "actuator")
    for name, kp, kd, limit in zip(JOINTS, (1000, 500, 500), (50, 20, 20), (50, cap, cap)):
        ET.SubElement(actuators, "position", name=name, joint=name, kp=str(kp), kv=str(kd),
                      forcerange=f"{-limit} {limit}")
    # Preserve the native Box's analytic FP64 mass/inertia, including operation
    # order. Implicit MJCF inertia differs by one ULP and can perturb contacts.
    cube_mass = (.04 * .04 * .04) * 1000.
    cube_inertia = (cube_mass / 12.) * (.04**2 + .04**2)
    sources = {
        "gripper": ET.tostring(gripper, encoding="unicode"),
        "ground": '<mujoco><worldbody><body name="ground"><geom name="plane" '
                  'type="plane" size="0 0 .1" friction=".5 0 0" solref=".002 1"/>'
                  '</body></worldbody></mujoco>',
        "block": '<mujoco><worldbody><body name="block"><freejoint name="free"/>'
                 f'<inertial pos="0 0 0" mass="{cube_mass!r}" '
                 f'diaginertia="{cube_inertia!r} {cube_inertia!r} {cube_inertia!r}"/>'
                 '<geom name="cube" type="box" size=".02 .02 .02" mass=".064" '
                 'friction=".5 0 0" solref=".002 1"/></body></worldbody></mujoco>',
    }
    for name, xml in sources.items():
        (output / f"{name}.xml").write_text(xml)
    return SceneCfg(entity_assets=(
        SceneEntitySpec("ground", ModelSourceDescriptor(str(output / "ground.xml")),
                        kind="rigid", root_mode="fixed"),
        SceneEntitySpec("gripper", ModelSourceDescriptor(str(output / "gripper.xml")),
                        root_mode="fixed"),
        SceneEntitySpec("block", ModelSourceDescriptor(str(output / "block.xml")),
                        kind="rigid", root_mode="floating",
                        initial_state=EntityInitialState(position=(initial_x, 0., .02))),
    ))


def require_contacts(backend) -> None:
    capability = backend.get_contact_capabilities()
    if not all((capability.supported, capability.normal,
                capability.signed_distance, capability.body_net_force)):
        raise RuntimeError("Pinch recording requires complete contacts and native body net forces")


def read_initial(backend) -> dict:
    """Project effective public readbacks into the existing scoring schema."""
    report = backend.get_import_report().to_dict()
    effective = {entry["field"]: entry["effective"] for entry in report["fields"]}
    for key, expected in (("native_precision", "float64"), ("native_device", "cpu"),
                          ("native_deterministic_algorithms", True),
                          ("native_friction_cone", "elliptic")):
        if effective.get(key) != expected:
            raise RuntimeError(f"Required native readback differs: {key}")
    entities = effective["native_entities"]
    gripper, cube = entities["gripper"], entities["block"]
    gripper_state = backend.get_entity_state("gripper")
    cube_state = backend.get_entity_state("block")
    geom_ids = [backend.get_geom_id(name) for name in GEOMS]
    sol_params = np.concatenate((backend.get_geom_solref(), backend.get_geom_solimp()), axis=1)
    return {
        "cube_mass": cube["mass"][0], "cube_inertia": cube["inertia"][0],
        "gripper_mass": gripper["mass"][0], "armature": gripper["armature"][0],
        "kp": gripper["kp"][0], "kv": gripper["kv"][0],
        "force_range": [value[0] for value in gripper["force_range"]],
        "geom_friction": backend.get_geom_friction()[geom_ids, 0].tolist(),
        "geom_sol_params": sol_params[geom_ids[:2]].tolist(),
        "joint_sol_params": [gripper["joints"][name]["sol_params"] for name in JOINTS],
        "options": effective["native_rigid_options"],
        "q": gripper_state["joint_positions"][0].tolist(),
        "qvel": gripper_state["joint_velocities"][0].tolist(),
        "object_pos": cube_state["root_pose"][0, :3].tolist(),
        "object_quat": cube_state["root_pose"][0, 3:].tolist(),
        "object_vel": cube_state["root_velocity"][0, :3].tolist(),
        "object_ang": cube_state["root_velocity"][0, 3:].tolist(),
        "cube_link": backend.get_body_id("block/block"),
        "plane_link": backend.get_body_id("ground/ground"),
        "pad_links": backend.get_body_ids(("gripper/left", "gripper/right")).tolist(),
        "identity_domain": "UniSim public body and geometry IDs",
        "geom_names": list(backend.get_geom_names()),
        "geom_body_ids": backend.get_geom_body_ids().tolist(),
        "import_report": report,
    }


def contact_record(snapshot) -> dict:
    """Serialize detached observations without altering unavailable fields."""
    return {field.name: value.tolist() if isinstance(value, np.ndarray) else value
            for field in fields(snapshot) for value in (getattr(snapshot, field.name),)}


def read_sample(backend, initial: dict, command: np.ndarray) -> dict:
    snapshot = backend.get_contact_snapshot()
    if snapshot.available.shape != (1,) or not snapshot.available[0]:
        raise RuntimeError("Expected one observed world after the native solve")
    if snapshot.signed_distance is None or snapshot.normal is None:
        raise RuntimeError("Contact geometry readback is missing")
    if snapshot.body_ids is None or snapshot.body_net_force is None:
        raise RuntimeError("Independent native net contact force is missing")
    body_ids = np.asarray(initial["geom_body_ids"])
    a, b = body_ids[snapshot.geom_a], body_ids[snapshot.geom_b]
    cube_id = initial["cube_link"]
    selected = (a == cube_id) | (b == cube_id)
    body_columns = np.flatnonzero(snapshot.body_ids == cube_id)
    if body_columns.size != 1:
        raise RuntimeError("Object net contact force has no unique public body column")
    cube = backend.get_entity_state("block")
    gripper = backend.get_entity_state("gripper")
    return {
        "time": float(snapshot.state_time[0]), "command": command[0].tolist(),
        "q": gripper["joint_positions"][0].tolist(),
        "qvel": gripper["joint_velocities"][0].tolist(),
        "object_pos": cube["root_pose"][0, :3].tolist(),
        "object_quat": cube["root_pose"][0, 3:].tolist(),
        "object_vel": cube["root_velocity"][0, :3].tolist(),
        "object_ang": cube["root_velocity"][0, 3:].tolist(),
        "object_contact_force": snapshot.body_net_force[0, body_columns].tolist(),
        "contacts": {
            "link_a": a[selected].tolist(), "link_b": b[selected].tolist(),
            "force_a": snapshot.force_a[selected].tolist(),
            "force_b": snapshot.force_b[selected].tolist(),
            "penetration": (-snapshot.signed_distance[selected]).tolist(),
        },
        "complete_contacts": contact_record(snapshot),
    }


def run(output: Path, dt: float, case_id: str | None = None) -> None:
    """Record the unchanged four-second protocol through public UniSim calls."""
    if dt not in (.001, .0005, .00025):
        raise ValueError("Unsupported timestep")
    case = load_case(case_id) if case_id is not None else None
    if case is not None and dt != .0005:
        raise ValueError("Force-limit protocol requires dt=0.0005")
    cap = case["force_limit_N"] if case else 10.
    initial_x = case["initial_x_m"] if case else 0.
    conditions = [case["condition"]] if case else ["pinch", "open_negative"]
    repeats = 1 if case else 2
    os.environ.setdefault("QD_NUM_THREADS", "2")
    if version("genesis-world") != "1.4.3":
        raise RuntimeError("Frozen protocol requires Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    if case is not None:
        manifest = Path(__file__).resolve().parents[2] / "demos/contact-benchmark/force-limit-v1.json"
        (output / manifest.name).write_bytes(manifest.read_bytes())
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    write_json(output / "protocol.json", {
        "schema": 2 if case else 1, "case": case, "engine": version("genesis-world"),
        "unisim": version("unisim-core"), "route": "unisim_public_candidate",
        "quadrants": version("quadrants"), "torch": version("torch"),
        "dt_s": dt, "steps": round(4 / dt), "duration_s": 4,
        "mass_kg": .064, "cube_size_m": .04, "mu": .5, "gravity_m_s2": 9.81,
        "backend": "cpu", "precision": "64", "seed": 0,
        "repeats": repeats, "conditions": conditions,
        "plane_cube_geom_timeconst_s": .002,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Candidate migration comparison; not hardware calibration",
    })
    timings = {"clock": "perf_counter; synchronous public CPU readback", "trials": [],
               "rendering": "not executed", "archival": "not executed"}
    started = time.perf_counter()
    backend = None
    try:
        from unisim import create_backend

        scene = create_scene(output, cap, initial_x)
        backend = create_backend("genesis", scene=scene, num_envs=1, sim_dt=dt,
                                 device="cpu", precision="64", seed=0,
                                 use_deterministic_algorithms=True, actuated_armature=0.,
                                 noslip_iterations=0, genesis_friction_cone="elliptic")
        backend.materialize()
        require_contacts(backend)
        timings["adapter_materialize_s"] = time.perf_counter() - started
        for condition in conditions:
            for repeat in range(repeats):
                phase = time.perf_counter()
                backend.reset()
                initial = read_initial(backend)
                reset_contacts = backend.get_contact_snapshot()
                if reset_contacts.available.any() or reset_contacts.env_ids.size:
                    raise RuntimeError("Reset published a stale solved contact")
                rows = []
                for step in range(round(4 / dt)):
                    t = step * dt
                    closure = .012 * min(t / .5, 1) if condition == "pinch" and t < 3.2 else 0
                    lift = .08 * max(0, min(t - 1, 1))
                    command = np.array([[lift, closure, closure]], dtype=np.float64)
                    backend.step(command)
                    rows.append(read_sample(backend, initial, command))
                write_json(output / f"{condition}-{repeat}.json", {
                    "condition": condition, "repeat": repeat, "case_id": case_id,
                    "initial": initial, "reset_contacts": contact_record(reset_contacts),
                    "samples": rows,
                })
                timings["trials"].append({"condition": condition, "repeat": repeat,
                                           "step_count": len(rows),
                                           "wall_including_reset_and_write_s": time.perf_counter() - phase})
    except BaseException as error:
        write_json(output / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        if backend is not None:
            backend.close()
        timings["total_after_import_s"] = time.perf_counter() - started
        write_json(output / "timings.json", timings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dt", type=float, choices=(.001, .0005, .00025), default=.0005)
    parser.add_argument("--case-id")
    args = parser.parse_args()
    run(args.output, args.dt, args.case_id)
