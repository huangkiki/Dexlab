"""Audit native Chaos, Bullet and SOFA traces against the frozen incline cases."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from dexlab.incline_run import axes
from dexlab.incline_score import ImpulseConsistencyError, file_hash, measure_response, require_close


STATE = ("x_m", "y_m", "z_m", "qw", "qx", "qy", "qz",
         "vx_m_s", "vy_m_s", "vz_m_s", "wx_rad_s", "wy_rad_s", "wz_rad_s")
IMPULSE = ("jx_ns", "jy_ns", "jz_ns")
PUSH_OUT = ("px_kg_m", "py_kg_m", "pz_kg_m")


def load_columns(path, fields):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not set(fields).issubset(reader.fieldnames):
            raise ValueError(f"Missing fields in {path.name}")
        data = np.array([[float(row[key]) for key in fields] for row in reader]).reshape(-1, len(fields))
    if not np.isfinite(data).all():
        raise ValueError(f"Nonfinite observations in {path.name}")
    return data


def readback_checks(engine, readback, protocol, case, normal, rotation):
    mass, side, gravity = (protocol[key] for key in ("mass_kg", "side_m", "gravity_m_s2"))
    require_close(readback["mass_kg"], mass, "native mass", 1e-8)
    require_close(readback["inertia_kg_m2"], np.full(3, mass * side ** 2 / 6), "native inertia", 1e-8)
    if engine == "chaos":
        require_close(readback["gravity_m_s2"], [0, 0, -gravity], "native gravity", 1e-6)
        require_close(readback["floor_height_m"], 0, "native floor surface", 1e-8)
        require_close(readback["floor_normal"], normal, "native floor normal", 1e-7)
        require_close(readback["box_side_m"], [side] * 3, "native side length", 1e-8)
        return
    if engine == "sofa":
        require_close(readback["gravity_m_s2"], [0, 0, -gravity], "native gravity")
        require_close(readback["floor_pose"][:3], -0.1 * normal, "slab center")
        require_close(readback["floor_pose"][3:], [*rotation[1:], rotation[0]], "slab orientation")
        require_close(readback["box_side_m"], [side] * 3, "native side length")
        if not case.get("negative_no_floor"):
            require_close(readback["floor_half_extents"], [20, 20, .1], "slab half extents")
        elif readback["floor_half_extents"] is not None:
            raise ValueError("Negative control still has a floor collision shape")
        require_close(float(readback["response_params"].removeprefix("mu=")), case["friction"],
                      "contact manager friction")
        return
    settings = readback["settings"]
    require_close([settings[f"gravityAcceleration{axis}"] for axis in "XYZ"], [0, 0, -gravity],
                  "native gravity")
    require_close(settings["fixedTimeStep"], case["timestep"], "native fixed timestep")
    require_close(settings["numSubSteps"], 0, "extra substeps")
    require_close(readback["floor_pose"][0], [0, 0, 0], "plane origin")
    require_close(readback["floor_pose"][1], [*rotation[1:], rotation[0]], "plane orientation")
    require_close(readback["floor_shape"]["dimensions"], [0, 0, 1], "untransformed plane normal")
    require_close(readback["box_shape"]["dimensions"], [side] * 3, "native side length")
    require_close(readback["lateral_friction_box_floor"], [case["friction"], 1.0], "body friction")


def geometric_distance(positions, quaternions, normal, side):
    # Inverse-rotate the plane normal into each box frame and project all three half extents.
    w, vector = quaternions[:, :1], quaternions[:, 1:]
    cross = np.cross(vector, normal)
    local_normals = normal + 2 * np.cross(vector, cross) - 2 * w * cross
    return positions @ normal - (side / 2) * np.abs(local_normals).sum(axis=1)


def read_case(engine, protocol, case, directory):
    step_size = case["timestep"]
    steps = round(protocol["duration_s"] / step_size)
    readback = json.loads((directory / "readback.json").read_text())
    _, normal, rotation = axes(case["angle_deg"])
    readback_checks(engine, readback, protocol, case, normal, rotation)
    if readback["completed_steps"] != steps:
        raise ValueError("Incomplete native run")
    state_data = load_columns(directory / "states.csv", ("step", "start_s", "dt_s", *STATE))
    require_close(state_data[:, 0], np.arange(steps + 1), "sample counts", 0)
    # UE passes a float32 dt through UWorld::Tick; its native solver clock is retained.
    clock_tolerance = 2e-7 if engine == "chaos" else 1e-10
    require_close(state_data[1:, 1], np.arange(steps) * step_size, "step starts", clock_tolerance)
    require_close(state_data[1:, 2], np.full(steps, step_size), "native timestep", 2e-10)
    time = state_data[:, 1] + state_data[:, 2]
    if np.any(np.diff(time) <= 0):
        raise ValueError("Nonmonotonic native clock")
    states = np.c_[time, state_data[:, 3:]]
    require_close(states[0, 1:4], protocol["side_m"] * normal / 2, "initial center", 1e-8)
    require_close(states[0, 4:8], rotation, "initial orientation", 1e-7)
    require_close(states[0, 8:], np.zeros(6), "initial velocities", 1e-8)
    require_close(np.linalg.norm(states[:, 4:8], axis=1), np.ones(steps + 1), "unit quaternions", 1e-7)

    dt = state_data[1:, 2]
    if engine == "sofa":
        summed, contacts = sofa_impulses(directory, steps)
    else:
        summed, contacts = pair_impulses(engine, case, directory, dt)
    distances = geometric_distance(states[1:, 1:4], states[1:, 4:8], normal, protocol["side_m"])
    return dict(states=states, forces=summed / dt[:, None], force_times=time[:-1],
                contact_count=contacts, contact_distance=distances)


def sofa_impulses(directory, steps):
    impulses = load_columns(directory / "impulses.csv", ("step", "solver_rows", *IMPULSE))
    require_close(impulses[:, 0], np.arange(1, steps + 1), "SOFA impulse sample sequence", 0)
    rows = load_columns(directory / "constraint-rows.csv", ("step", "row_index", "multiplier"))
    indices = step_indices(rows[:, 0], steps)
    counts = np.bincount(indices, minlength=steps)
    require_close(impulses[:, 1], counts, "SOFA solver row counts", 0)
    row_indices = np.concatenate([np.arange(count) for count in counts])
    require_close(rows[:, 1], row_indices, "SOFA solver row order", 0)
    if np.any(impulses[counts == 0, 2:] != 0):
        raise ValueError("SOFA reported impulse without constraint rows")
    # Each nonempty solver step proves a contact constraint; scalar multipliers
    # are not a count of geometric contact points.
    return impulses[:, 2:], (counts > 0).astype(int)


def step_indices(native_steps, total):
    steps = native_steps.astype(int)
    if np.any(steps != native_steps) or np.any((steps < 1) | (steps > total)):
        raise ValueError("Contact records outside completed intervals")
    return steps - 1


def pair_impulses(engine, case, directory, dt):
    extra = ("mu_static", "mu_dynamic") if engine == "chaos" else (
        "normal_force_n", "nx", "ny", "nz", "lateral1_n", "tx1", "ty1", "tz1",
        "lateral2_n", "tx2", "ty2", "tz2",
    )
    observed = load_columns(directory / "contacts.csv", ("step", "distance_m", *IMPULSE, *PUSH_OUT, *extra))
    indices = step_indices(observed[:, 0], len(dt))
    impulses = observed[:, 2:5]
    if engine == "chaos":
        require_close(observed[:, 8:10], np.full((len(observed), 2), case["friction"]),
                      "native contact friction", 1e-5)
        # Chaos reports both velocity impulse and position correction. Its contact
        # solver's accumulated impulse adds the correction divided by this step's dt.
        impulses = impulses + observed[:, 5:8] / dt[indices, None]
    else:
        forces = sum(observed[:, i, None] * observed[:, i+1:i+4] for i in (8, 12, 16))
        require_close(impulses, forces * dt[indices, None], "independent Bullet contact sum", 1e-12)
    summed = np.zeros((len(dt), 3))
    np.add.at(summed, indices, impulses)
    return summed, np.bincount(indices, minlength=len(dt))


def score_case(engine, protocol, case, directory):
    result = {"id": case["id"], "regime": case["regime"], "timestep": case["timestep"]}
    native_files = ("impulses.csv", "constraint-rows.csv") if engine == "sofa" else ("contacts.csv",)
    result["hashes"] = {
        name: file_hash(directory / name) for name in ("states.csv", "readback.json", *native_files)
        if (directory / name).is_file()
    }
    try:
        trace = read_case(engine, protocol, case, directory)
        if case.get("negative_no_floor"):
            assert_no_floor(protocol, case, trace)
            return dict(result, status="negative-rejected")
        metrics = measure_response(protocol, case, trace)
        return dict(result, status="pass" if metrics["passed"] else "fail", **metrics)
    except (OSError, KeyError, ValueError) as error:
        result.update(status="invalid", reason=str(error))
        if isinstance(error, ImpulseConsistencyError):
            g = protocol["gravity_m_s2"]
            residual = protocol["mass_kg"] * np.diff(trace["states"][:, 8:11], axis=0)
            residual -= (trace["forces"] + [0, 0, -protocol["mass_kg"] * g]) * case["timestep"]
            residual = np.linalg.norm(residual, axis=1)
            result.update(impulse_residual_max_ns=error.residual,
                          first_invalid_step=int(np.flatnonzero(residual > 1e-7)[0]) + 1)
        return result


def assert_no_floor(protocol, case, trace):
    if np.any(trace["contact_count"]):
        raise ValueError("Disabled floor generated contacts")
    expected_vz = -protocol["gravity_m_s2"] * trace["states"][:, 0]
    require_close(trace["states"][:, 10], expected_vz, "free-fall velocity", 1e-4)
    if trace["states"][-1, 3] >= 0:
        raise ValueError("Disabled floor was not crossed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", choices=["bullet", "chaos", "sofa"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--step", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.manifest.read_text())
    cases = [case for case in protocol["cases"] if args.step is None or case["timestep"] == args.step]
    if not cases:
        parser.error("No cases selected")
    results = [score_case(args.engine, protocol, case, args.records / case["id"]) for case in cases]
    with args.output.open("x") as destination:
        json.dump(dict(engine=args.engine, manifest_sha256=file_hash(args.manifest), cases=results),
                  destination, indent=2, allow_nan=False)
        destination.write("\n")


if __name__ == "__main__":
    main()
