"""Record the frozen incline fixture using SOFA's rigid OBB contact constraints."""

import argparse
import csv
import json
import math
import shutil
from pathlib import Path

import Sofa.Core
import Sofa.Simulation


PLUGINS = (
    "CollisionOBBCapsule",
    "Sofa.Component.AnimationLoop",
    "Sofa.Component.Collision.Detection.Algorithm",
    "Sofa.Component.Collision.Detection.Intersection",
    "Sofa.Component.Collision.Response.Contact",
    "Sofa.Component.Constraint.Lagrangian.Correction",
    "Sofa.Component.Constraint.Lagrangian.Solver",
    "Sofa.Component.Constraint.Projective",
    "Sofa.Component.LinearSolver.Iterative",
    "Sofa.Component.Mass",
    "Sofa.Component.ODESolver.Backward",
    "Sofa.Component.StateContainer",
)


def build_scene(protocol, case):
    root = Sofa.Core.Node("Incline")
    root.gravity = [0, 0, -protocol["gravity_m_s2"]]
    root.dt = case["timestep"]
    root.addObject("RequiredPlugin", pluginName=list(PLUGINS))
    root.addObject("FreeMotionAnimationLoop")
    solver = root.addObject("BlockGaussSeidelConstraintSolver", tolerance=1e-10,
                            maxIterations=100, computeConstraintForces=True)
    root.addObject("CollisionPipeline")
    root.addObject("BruteForceBroadPhase")
    root.addObject("BVHNarrowPhase")
    proximity = root.addObject("NewProximityIntersection", alarmDistance=1e-4, contactDistance=1e-7)
    response = root.addObject("RuleBasedContactManager", response="FrictionContactConstraint",
                              responseParams=f"mu={case['friction']}")
    angle = math.radians(case["angle_deg"])
    normal = [math.sin(angle), 0, math.cos(angle)]
    rotation = [0, math.sin(angle / 2), 0, math.cos(angle / 2)]
    floor = root.addChild("Floor")
    floor_dofs = floor.addObject("MechanicalObject", template="Rigid3d",
                                 position=[[-0.1 * n for n in normal] + rotation])
    floor.addObject("FixedProjectiveConstraint", indices=[0])
    floor_shape = None
    if not case.get("negative_no_floor"):
        floor_shape = floor.addObject("OBBCollisionModel", template="Rigid3d", extents=[[20, 20, .1]],
                                      moving=False, simulated=False)
    box = root.addChild("Box")
    side = protocol["side_m"]
    box.addObject("EulerImplicitSolver", rayleighStiffness=0.0, rayleighMass=0.0)
    box.addObject("CGLinearSolver", tolerance=1e-12, threshold=1e-12, iterations=100)
    dofs = box.addObject("MechanicalObject", template="Rigid3d",
                         position=[[(side / 2) * n for n in normal] + rotation])
    unit_inertia = side ** 2 / 6
    mass = box.addObject("UniformMass", template="Rigid3d",
                         vertexMass=f"{protocol['mass_kg']} {side**3} "
                                    f"{unit_inertia} 0 0 0 {unit_inertia} 0 0 0 {unit_inertia}")
    shape = box.addObject("OBBCollisionModel", template="Rigid3d", extents=[[side / 2] * 3])
    box.addObject("UncoupledConstraintCorrection")
    return root, solver, dofs, mass, shape, floor_dofs, floor_shape, proximity, response


def state(dofs):
    x, y, z, qx, qy, qz, qw = dofs.position.value[0]
    return (x, y, z, qw, qx, qy, qz, *dofs.velocity.value[0])


def record_case(protocol, case, directory):
    directory.mkdir()
    root, solver, dofs, mass, shape, floor, floor_shape, proximity, response = build_scene(protocol, case)
    Sofa.Simulation.initRoot(root)
    components = [solver, dofs, mass, shape, proximity, response]
    component_states = {item.getClassName(): str(item.componentState.value) for item in components}
    if "Invalid" in component_states.values():
        raise RuntimeError(f"SOFA scene initialized with invalid components: {component_states}")
    # The rigid vertexMass data include the unit-mass inertia matrix.
    raw_mass = [float(part) for part in mass.vertexMass.value.replace("[", " ").replace("]", " ").replace(",", " ").split()]
    readback = {
        "mass_kg": mass.totalMass.value,
        "rigid_vertex_mass_data": raw_mass,
        "inertia_kg_m2": [raw_mass[0] * raw_mass[i] for i in (2, 6, 10)],
        "gravity_m_s2": list(root.gravity.value),
        "floor_pose": floor.position.value[0].tolist(),
        "floor_half_extents": floor_shape.extents.value[0].tolist() if floor_shape is not None else None,
        "box_side_m": (2 * shape.extents.value[0]).tolist(),
        "response_params": response.responseParams.value,
        "component_states": component_states,
        "alarm_distance_m": proximity.alarmDistance.value,
        "contact_distance_m": proximity.contactDistance.value,
        "constraint_iterations": solver.maxIterations.value,
        "constraint_tolerance": solver.tolerance.value,
        "force_epoch": "world-space rigid lambda from the completed step; units checked against state momentum",
    }
    completed = 0
    try:
        with (directory / "states.csv").open("w", newline="") as state_file, (
            directory / "impulses.csv"
        ).open("w", newline="") as impulse_file, (
            directory / "constraint-rows.csv"
        ).open("w", newline="") as constraint_file:
            states, impulses, rows = map(csv.writer, (state_file, impulse_file, constraint_file))
            states.writerow(("step", "start_s", "dt_s", "x_m", "y_m", "z_m", "qw", "qx", "qy", "qz",
                             "vx_m_s", "vy_m_s", "vz_m_s", "wx_rad_s", "wy_rad_s", "wz_rad_s"))
            impulses.writerow(("step", "solver_rows", "jx_ns", "jy_ns", "jz_ns", "lx_nms", "ly_nms", "lz_nms"))
            rows.writerow(("step", "row_index", "multiplier"))
            states.writerow((0, 0, 0, *state(dofs)))
            dt = root.dt.value
            for step in range(1, round(protocol["duration_s"] / dt) + 1):
                start = root.time.value
                Sofa.Simulation.animate(root, dt)
                states.writerow((step, start, root.time.value - start, *state(dofs)))
                multipliers = solver.constraintForces.value
                native = dofs.getData("lambda").value
                if len(multipliers) and native.shape != (1, 6):
                    raise RuntimeError("Missing rigid lambda for active constraints")
                impulses.writerow((step, len(multipliers), *(native[0] if len(native) else [0] * 6)))
                rows.writerows((step, i, value) for i, value in enumerate(multipliers))
                completed = step
    finally:
        readback["completed_steps"] = completed
        (directory / "readback.json").write_text(json.dumps(readback, indent=2) + "\n")
        Sofa.Simulation.unload(root)


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
