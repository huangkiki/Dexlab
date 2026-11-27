"""Record the frozen incline cases in native PyBullet DIRECT."""

import argparse
import csv
import json
import math
import shutil
from importlib.metadata import version
from pathlib import Path

import pybullet as bullet


STATE_FIELDS = (
    "step", "start_s", "dt_s", "x_m", "y_m", "z_m", "qw", "qx", "qy", "qz",
    "vx_m_s", "vy_m_s", "vz_m_s", "wx_rad_s", "wy_rad_s", "wz_rad_s",
)
CONTACT_FIELDS = (
    "step", "distance_m", "jx_ns", "jy_ns", "jz_ns", "px_kg_m", "py_kg_m", "pz_kg_m",
    "normal_force_n", "nx", "ny", "nz",
    "lateral1_n", "tx1", "ty1", "tz1", "lateral2_n", "tx2", "ty2", "tz2",
)


def record_case(protocol, case, directory):
    directory.mkdir()
    client = bullet.connect(bullet.DIRECT)
    if client < 0:
        raise RuntimeError("DIRECT client failed to start")
    try:
        run_case(protocol, case, directory, client)
    finally:
        bullet.disconnect(client)


def run_case(protocol, case, directory, client):
    step_size = case["timestep"]
    half_side = protocol["side_m"] / 2
    angle = math.radians(case["angle_deg"])
    rotation = [0, math.sin(angle / 2), 0, math.cos(angle / 2)]
    normal = [math.sin(angle), 0, math.cos(angle)]
    bullet.setPhysicsEngineParameter(
        fixedTimeStep=step_size, numSubSteps=0, numSolverIterations=50,
        deterministicOverlappingPairs=1, physicsClientId=client,
    )
    bullet.setGravity(0, 0, -protocol["gravity_m_s2"], physicsClientId=client)
    plane_shape = bullet.createCollisionShape(
        bullet.GEOM_PLANE, planeNormal=[0, 0, 1], physicsClientId=client,
    )
    shape = bullet.createCollisionShape(
        bullet.GEOM_BOX, halfExtents=[half_side] * 3, physicsClientId=client,
    )
    floor = bullet.createMultiBody(
        baseMass=0, baseCollisionShapeIndex=plane_shape,
        baseOrientation=rotation, physicsClientId=client,
    )
    box = bullet.createMultiBody(
        baseMass=protocol["mass_kg"], baseCollisionShapeIndex=shape,
        basePosition=[half_side * n for n in normal],
        baseOrientation=rotation, physicsClientId=client,
    )
    bullet.changeDynamics(floor, -1, lateralFriction=1.0, restitution=0, physicsClientId=client)
    bullet.changeDynamics(
        box, -1, lateralFriction=case["friction"], restitution=0, linearDamping=0,
        angularDamping=0, activationState=bullet.ACTIVATION_STATE_DISABLE_SLEEPING,
        physicsClientId=client,
    )
    if case.get("negative_no_floor"):
        bullet.setCollisionFilterPair(box, floor, -1, -1, 0, physicsClientId=client)
    settings = bullet.getPhysicsEngineParameters(physicsClientId=client)
    box_info = bullet.getDynamicsInfo(box, -1, physicsClientId=client)
    floor_info = bullet.getDynamicsInfo(floor, -1, physicsClientId=client)
    readback = {
        "binding": version("pybullet"), "api_version": bullet.getAPIVersion(),
        "settings": settings, "mass_kg": box_info[0], "inertia_kg_m2": box_info[2],
        "lateral_friction_box_floor": [box_info[1], floor_info[1]],
        "floor_pose": bullet.getBasePositionAndOrientation(floor, physicsClientId=client),
        "floor_shape": read_shape(floor, client),
        "box_shape": read_shape(box, client),
        "clock": "one explicit stepSimulation per row, indexed by native fixedTimeStep",
        "force_epoch": "contact forces exported after the completed step",
    }
    completed = 0
    try:
        with (directory / "states.csv").open("w", newline="") as state_file, (
            directory / "contacts.csv"
        ).open("w", newline="") as contact_file:
            states, contacts = csv.writer(state_file), csv.writer(contact_file)
            states.writerow(STATE_FIELDS)
            contacts.writerow(CONTACT_FIELDS)
            states.writerow((0, 0, 0, *read_state(box, client)))
            native_dt = settings["fixedTimeStep"]
            for step in range(1, round(protocol["duration_s"] / step_size) + 1):
                bullet.stepSimulation(physicsClientId=client)
                states.writerow((step, (step - 1) * native_dt, native_dt, *read_state(box, client)))
                for contact in bullet.getContactPoints(box, floor, physicsClientId=client):
                    contacts.writerow(contact_row(step, native_dt, contact))
                completed = step
    finally:
        readback["completed_steps"] = completed
        (directory / "readback.json").write_text(json.dumps(readback, indent=2) + "\n")


def read_state(box, client):
    position, (qx, qy, qz, qw) = bullet.getBasePositionAndOrientation(box, physicsClientId=client)
    velocity, angular = bullet.getBaseVelocity(box, physicsClientId=client)
    return (*position, qw, qx, qy, qz, *velocity, *angular)


def read_shape(body, client):
    (_, _, kind, dimensions, _, position, orientation), = bullet.getCollisionShapeData(
        body, -1, physicsClientId=client,
    )
    return {"type": kind, "dimensions": dimensions, "position": position, "orientation": orientation}


def contact_row(step, dt, contact):
    normal, distance, normal_force, lateral1, tangent1, lateral2, tangent2 = contact[7:14]
    impulse = tuple(
        dt * (normal_force * n + lateral1 * t1 + lateral2 * t2)
        for n, t1, t2 in zip(normal, tangent1, tangent2, strict=True)
    )
    return (step, distance, *impulse, 0, 0, 0, normal_force, *normal,
            lateral1, *tangent1, lateral2, *tangent2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=float, help="Run only cases at this timestep")
    args = parser.parse_args()
    protocol = json.loads(args.manifest.read_text())
    cases = [case for case in protocol["cases"] if args.step is None or case["timestep"] == args.step]
    if not cases:
        parser.error("No cases selected")
    args.output.mkdir(parents=True)
    shutil.copyfile(args.manifest, args.output / "manifest.json")
    for case in cases:
        record_case(protocol, case, args.output / case["id"])


if __name__ == "__main__":
    main()
