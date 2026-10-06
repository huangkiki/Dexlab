"""Reproduce the 18-case development matrix inside an external resource guard."""

import argparse
import gzip
import json
import shutil
from pathlib import Path

import numpy as np

from dexlab.contact_feedthrough import PROFILES, verify
from dexlab.contact_plane import PlaneCase
from dexlab.contact_tangent import DURATION, LOADS, TIMESTEPS, commands
from dexlab.physx_baseline import digest, write_json


def run_case(load, dt, normal, output):
    from dexlab.contact_plane_native import MuJoCoPlane

    output.mkdir(parents=True, exist_ok=False)
    case = PlaneCase(
        name="dev-mujoco-tangent",
        initial_speed=0,
        friction=0,
        settle=0,
        duration=DURATION,
        timestep=dt,
    )
    native = MuJoCoPlane(case, output, normal_parameters=normal)
    prescribed = commands(load, dt)
    poses, velocities, times, forces, ledger, counts, completed = ([] for _ in range(7))
    try:
        write_json(output / "native.json", native.metadata)
        native.start()
        pose, velocity = native.observe()
        poses.append(pose)
        velocities.append(velocity)
        times.append(native.clock())
        with gzip.open(output / "contacts.jsonl.gz", "wt") as stream:
            for load_value in prescribed:
                pose, velocity, force, contacts, ok, warnings = native.step(
                    np.array([0.0, 0.0, case.mass * case.gravity - load_value])
                )
                poses.append(pose)
                velocities.append(velocity)
                times.append(native.clock())
                forces.append(force)
                ledger.append(
                    np.sum([point["force_on_box"] for point in contacts], axis=0)
                    if contacts
                    else np.zeros(3)
                )
                counts.append(len(contacts))
                completed.append(ok)
                stream.write(
                    json.dumps({"warnings": warnings, "contacts": contacts}) + "\n"
                )
        np.savez_compressed(
            output / "states.npz",
            time=np.asarray(times),
            pose=np.asarray(poses),
            velocity=np.asarray(velocities),
            force=np.asarray(forces),
            ledger=np.asarray(ledger),
            load=prescribed,
            contacts=np.asarray(counts),
            completed=np.asarray(completed, dtype=bool),
        )
        write_json(
            output / "receipt.json",
            {
                "load_n": load,
                "timestep_s": dt,
                "normal": normal,
                "hashes": {
                    name: digest(output / name)
                    for name in (
                        "states.npz",
                        "contacts.jsonl.gz",
                        "native.json",
                        "model.xml",
                    )
                },
            },
        )
        result = verify(output)
        write_json(output / "score.json", result)
        return result
    finally:
        native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent
    # Freeze the actual imported Python package, including the scorer and native adapter.
    paths = sorted(source.glob("*.py"))
    hashes = {path.name: digest(path) for path in paths}
    snapshot = args.output / "source"
    snapshot.mkdir()
    for path in paths:
        shutil.copyfile(path, snapshot / path.name)
    write_json(args.output / "source-hashes.json", hashes)
    rows = []
    for name, normal in PROFILES.items():
        for dt in TIMESTEPS:
            for load in LOADS:
                identifier = f"{name}-load-{load:g}-dt-{round(dt * 1e6)}us"
                result = run_case(load, dt, normal, args.output / identifier)
                rows.append({"id": identifier, "result": result})
                write_json(args.output / "results.json", rows)
                print(
                    json.dumps({"id": identifier, "valid": result["valid"]}), flush=True
                )
    if any(digest(source / name) != value for name, value in hashes.items()):
        raise RuntimeError("Source changed during study")


if __name__ == "__main__":
    main()
