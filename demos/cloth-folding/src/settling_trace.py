"""Record passive settling; locate the first sampled table intrusion offline."""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from dexlab import cloth_table_audit
from dexlab.cloth_table_audit import (
    NUMERICAL_EPS_M, verified_table_bounds, triangle_box_depth,
)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@contextmanager
def capture_settling(model, data, directory, *, steps, engine):
    """Copy state only. Retain the successful prefix on a Python exception.

    Call the yielded function after every successful step. No forward dynamics,
    contact query, or integration is performed by this recorder.
    """
    if directory is None:
        yield None
        return
    directory = Path(directory)
    if steps < 1 or model.nflex != 1 or model.flex_dim[0] != 2:
        raise ValueError("Expected a positive step count and one triangular flex")
    directory.mkdir(parents=True, exist_ok=False)
    mujoco.mj_saveModel(model, str(directory / "model.mjb"))
    source = Path(__file__).parent
    source_hashes = {name: digest(source / name) for name in
                     ("settling_trace.py", "run_cloth.py", "cloth_model.py", "cloth_control.py")}
    times, positions, velocities = [], [], []
    dt, start_time = float(model.opt.timestep), float(data.time)

    def capture():
        expected = start_time + len(times) * dt
        if (len(times) > steps or not np.isclose(data.time, expected, atol=1e-10, rtol=0)
                or not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all()):
            raise ValueError("Settling record has a missing, duplicate or invalid step")
        times.append(float(data.time))
        positions.append(data.qpos.copy())
        velocities.append(data.qvel.copy())

    completed, error_type = False, None
    try:
        capture()
        yield capture
        if len(times) != steps + 1:
            raise ValueError("Settling ended before all requested steps were recorded")
        completed = True
    except BaseException as error:
        error_type = type(error).__name__
        np.savez_compressed(directory / "failed-state.npz", time_s=data.time,
                            qpos=data.qpos, qvel=data.qvel, warnings=data.warning.number)
        raise
    finally:
        np.savez_compressed(directory / "states.npz", time_s=times,
                            qpos=np.asarray(positions).reshape(-1, model.nq),
                            qvel=np.asarray(velocities).reshape(-1, model.nv),
                            triangles=model.flex_elem.reshape(-1, 3))
        manifest = {
            "schema_version": 1, "classification": "passive_settling_trace",
            "completed": completed, "error_type": error_type, "engine": engine,
            "expected_steps": steps, "recorded_steps": max(0, len(times) - 1),
            "timestep_s": dt, "initial_time_s": start_time,
            "solver": int(model.opt.solver), "iterations": int(model.opt.iterations),
            "files": {p.name: digest(p) for p in directory.iterdir() if p.is_file()},
            "source_sha256": source_hashes,
            "limits": ["A Python exception preserves the recorded prefix; a killed process may leave an incomplete directory",
                       "No grasp acceptance, timing isolation or restart-state equivalence is claimed"],
        }
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")


def first_table_intrusion(model, times, poses, triangles):
    """Inspect every recorded state up to the first midsurface intersection."""
    if (model.nflex != 1 or model.flex_dim[0] != 2 or model.nplugin
            or triangles.dtype.kind not in "iu"
            or not np.array_equal(triangles, model.flex_elem.reshape(-1, 3))
            or times.ndim != 1 or poses.shape != (len(times), model.nq) or not len(times)
            or np.any(np.diff(times) <= 0)
            or not np.isfinite(times).all() or not np.isfinite(poses).all()):
        raise ValueError("Unsupported model or invalid recorded poses/topology")
    data = mujoco.MjData(model)
    witness, previous_time, bounds = None, None, None
    for index, (time, pose) in enumerate(zip(times, poses, strict=True)):
        data.qpos[:] = pose
        mujoco.mj_kinematics(model, data)
        mujoco.mj_flex(model, data)
        if bounds is None:
            lo, hi, geometry = verified_table_bounds(model, data)
            bounds = (lo, hi)
        points = data.flexvert_xpos
        depths = [triangle_box_depth(face, *bounds) for face in points[triangles]]
        triangle_id = int(np.argmax(depths))
        if depths[triangle_id] > NUMERICAL_EPS_M:
            witness = {"frame_index": index, "time_s": float(time),
                       "previous_sample_without_intrusion_s": previous_time,
                       "triangle_id": triangle_id, "depth_m": depths[triangle_id],
                       "triangle_vertices_m": points[triangles[triangle_id]].tolist()}
            break
        previous_time = float(time)
    return {"first_intrusion": witness, "evaluated_frames": index + 1,
            "recorded_frames": len(times), "table_bounds_m": np.asarray(bounds).tolist(),
            "numerical_zero_tolerance_m": NUMERICAL_EPS_M,
            "table_geometry_verification": geometry}


def audit_saved(directory):
    directory = Path(directory)
    manifest_path = directory / "manifest.json"
    manifest_hash = digest(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get("schema_version") != 1 or manifest.get("classification") != "passive_settling_trace"
            or type(manifest.get("completed")) is not bool):
        raise ValueError("Unsupported settling manifest")
    files = manifest["files"]
    if not {"model.mjb", "states.npz"} <= files.keys() or not files.keys() <= {
            "model.mjb", "states.npz", "failed-state.npz"}:
        raise ValueError("Invalid settling file list")

    def check_inputs():
        if digest(manifest_path) != manifest_hash or any(digest(directory / name) != sha for name, sha in files.items()):
            raise ValueError("Settling input hash mismatch")

    check_inputs()
    model = mujoco.MjModel.from_binary_path(str(directory / "model.mjb"))
    with np.load(directory / "states.npz", allow_pickle=False) as states:
        times, poses, velocities, triangles = (states[k] for k in ("time_s", "qpos", "qvel", "triangles"))
    count, expected = manifest["recorded_steps"], manifest["expected_steps"]
    if (type(count) is not int or type(expected) is not int or not 0 <= count <= expected
            or expected < 1 or times.shape != (count + 1,)
            or velocities.shape != (len(times), model.nv) or not np.isfinite(velocities).all()
            or not np.isclose(model.opt.timestep, manifest["timestep_s"], rtol=0, atol=1e-15)
            or int(model.opt.solver) != manifest["solver"]
            or int(model.opt.iterations) != manifest["iterations"]
            or not np.allclose(times, manifest["initial_time_s"] + np.arange(count + 1) * model.opt.timestep,
                               rtol=0, atol=1e-10)
            or (manifest["completed"] and (count != expected or manifest["error_type"] is not None
                                           or "failed-state.npz" in files))
            or (not manifest["completed"] and (not manifest["error_type"] or "failed-state.npz" not in files))):
        raise ValueError("Incomplete or inconsistent settling sampling metadata")
    result = first_table_intrusion(model, times, poses, triangles)
    check_inputs()
    return {"schema_version": 1, "classification": "exploratory_settling_onset_diagnostic",
            "record_completed": manifest["completed"], "scientific_acceptance": "not_assessed",
            "input_sha256": {**files, "manifest.json": manifest_hash},
            "auditor_sha256": digest(__file__),
            "table_auditor_sha256": digest(cloth_table_audit.__file__),
            "runtime_mujoco_version": mujoco.__version__,
            **result,
            "limits": ["Zero-thickness midsurface versus the verified solid table only",
                       "Stops at the first sampled intrusion; later states are not geometrically assessed",
                       "Consecutive physical steps do not prove continuous inter-step separation",
                       "The previous clear sample is not a continuous-time onset bound",
                       "No robot contact, support force, grasp success or physical repair is assessed"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()) or args.output.exists():
        parser.error("Choose a new output file outside the original record")
    report = audit_saved(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
