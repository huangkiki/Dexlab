"""Frozen synthetic sensor experiment over the existing official cube/plane fixture."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import MuJoCoPlane
from dexlab.tactile_depth import depth_map


PATHS = ("direct", "slide-return", "detach-recontact", "reset-direct")


def target(path, time):
    point = np.array([0., 0., .02])
    if .5 < time < 1.5:
        excursion = np.sin(np.pi * (time - .5)) ** 2
        if path == "slide-return":
            point[0] += .02 * excursion
        elif path == "detach-recontact":
            point[2] += .015 * excursion
    return point


def capped(vector, limit):
    return vector * min(1., limit / max(np.linalg.norm(vector), 1e-30))


def run(output, controller="compensated"):
    if controller not in ("compensated", "released-hold"):
        raise ValueError("Unknown frozen controller")
    output.mkdir(parents=True, exist_ok=False)
    case = PlaneCase(name="dev-tactile", initial_speed=0., duration=3., settle=0.)
    record = {"completed": False, "case": asdict(case), "controller": controller, "runs": []}
    started = perf_counter()
    try:
        for resolution in (32, 64):
            directory = output / str(resolution)
            directory.mkdir()
            native = MuJoCoPlane(case, directory, measure_step_timing=True)
            mj, model, data = native.mj, native.model, native.data
            record["native"] = native.metadata
            for path in PATHS:
                mj.mj_resetData(model, data)
                mj.mj_forward(model, data)
                native.start()
                pose, velocity = native.observe()
                poses, velocities = [pose], [velocity]
                forces, commands, distances, warnings = [], [], [], []
                maps, statistics = [], []
                sensor_seconds = 0.
                timing_before = dict(native.step_timing)
                for step in range(case.steps):
                    force = capped(1000 * (target(path, step * case.timestep) - pose[:3]) - 30 * velocity[:3] + [0, 0, case.mass * case.gravity], 20.)
                    if controller == "released-hold" and step * case.timestep >= 1.5:
                        force[2] = 0.
                    q = pose[3:] * (1 if pose[3] >= 0 else -1)
                    norm = np.linalg.norm(q[1:])
                    angle_axis = q[1:] * (2 * np.arctan2(norm, q[0]) / norm if norm else 0.)
                    torque = capped(-.5 * angle_axis - .05 * velocity[3:], .1)
                    data.xfrc_applied[1, 3:] = torque
                    pose, velocity, force_native, contacts, _, warn = native.step(force)
                    poses.append(pose)
                    velocities.append(velocity)
                    forces.append(force_native)
                    commands.append(np.r_[force, torque])
                    distances.append([c["distance"] for c in contacts])
                    warnings.append(warn)
                    rotation = np.empty(9)
                    mj.mju_quat2Mat(rotation, pose[3:])
                    begin = perf_counter()
                    image = depth_map(pose[:3], rotation.reshape(3, 3), resolution=resolution)
                    sensor_seconds += perf_counter() - begin
                    statistics.append([image.min(), image.max(), image.sum() * (.08 / resolution) ** 2])
                    if (step + 1) % 40 == 0:
                        maps.append(image)
                name = f'{resolution}-{path}'
                np.savez_compressed(output / (name + '.npz'), pose=poses, velocity=velocities, force=forces, command=commands, warnings=warnings, maps=maps, map_stats=statistics)
                row = {"name": name, "path": path, "resolution": resolution, "contact_distances_m": distances, "sensor_seconds": sensor_seconds,
                       "native_seconds": native.step_timing["native_call_seconds"] - timing_before["native_call_seconds"],
                       "observation_seconds": native.step_timing["observation_seconds"] - timing_before["observation_seconds"]}
                record["runs"].append(row)
                print(name, "complete", flush=True)
            native.close()
        record["completed"] = True
    except Exception as error:
        record["error"] = f'{type(error).__name__}: {error}'
        raise
    finally:
        record["wall_seconds"] = perf_counter() - started
        (output / 'record.json').write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument("--controller", choices=("compensated", "released-hold"), default="compensated")
    args = parser.parse_args()
    run(args.output, args.controller)
