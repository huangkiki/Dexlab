"""Run the frozen native small-signal protocol under an external resource guard."""

import argparse
import gzip
import json
import shutil
import time
from pathlib import Path

import numpy as np

from dexlab.contact_damping import PARAMETERS
from dexlab.contact_plane import PlaneCase
from dexlab.contact_tangent import (
    DAMPING,
    DURATION,
    LIMITS,
    LOADS,
    TIMESTEPS,
    commands,
    score,
)
from dexlab.physx_baseline import digest, write_json


def run_case(load, dt, output, *, tight_solver=False):
    from dexlab.contact_plane_native import SuperDexPlane

    output.mkdir(parents=True, exist_ok=False)
    case = PlaneCase(
        name="dev-tangent",
        initial_speed=0,
        friction=0,
        settle=0,
        duration=DURATION,
        timestep=dt,
    )
    native = SuperDexPlane(
        case,
        output,
        normal_parameters=PARAMETERS | {"normal_viscous_damping_coefficient": DAMPING},
        solver_parameters={"absolute_tolerance": 1e-9, "relative_tolerance": 1e-9}
        if tight_solver
        else None,
    )
    poses, velocities, times, forces, ledgers, counts, completed = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    prescribed = commands(load, dt)
    started = time.perf_counter()
    try:
        write_json(output / "native.json", native.metadata)
        write_json(output / "geometry-readback.json", native.record_geometry())
        native.start()
        pose, velocity = native.observe()
        poses.append(pose)
        velocities.append(velocity)
        times.append(native.clock())
        with gzip.open(output / "contacts.jsonl.gz", "wt") as stream:
            for value in prescribed:
                pose, velocity, force, contacts, ok, status = native.step(
                    np.array([0.0, 0.0, case.mass * case.gravity - value])
                )
                poses.append(pose)
                velocities.append(velocity)
                times.append(native.clock())
                forces.append(force)
                ledgers.append(
                    np.sum([p["force_on_box"] for p in contacts], axis=0)
                    if contacts
                    else np.zeros(3)
                )
                counts.append(len(contacts))
                completed.append(ok)
                stream.write(
                    json.dumps({"status": status, "contacts": contacts}) + "\n"
                )
        arrays = {
            "time": np.asarray(times),
            "pose": np.asarray(poses),
            "velocity": np.asarray(velocities),
            "force": np.asarray(forces),
            "ledger": np.asarray(ledgers),
            "load": prescribed,
            "completed": np.asarray(completed, dtype=bool),
            "contacts": np.asarray(counts),
        }
        np.savez_compressed(output / "states.npz", **arrays)
        # Score from persisted arrays, independently of native success or target fit.
        with np.load(output / "states.npz", allow_pickle=False) as saved:
            result = score(load, dt, saved)
        write_json(output / "score.json", result)
        write_json(
            output / "receipt.json",
            {
                "load_n": load,
                "timestep_s": dt,
                "elapsed_s": time.perf_counter() - started,
                "arrays_sha256": digest(output / "states.npz"),
                "contacts_sha256": digest(output / "contacts.jsonl.gz"),
                "limits": LIMITS,
                "scope": "Warm serial diagnostic wall time including observation/I-O; not performance benchmark",
            },
        )
        return result
    finally:
        native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--tight-solver",
        action="store_true",
        help="Controlled follow-up: absolute/relative tolerance 1e-9",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent
    hashes = {}
    for name in (
        "contact_tangent.py",
        "contact_tangent_run.py",
        "contact_plane_native.py",
        "contact_plane.py",
        "contact_damping.py",
        "contact_parameters.py",
    ):
        shutil.copyfile(source / name, args.output / name)
        hashes[name] = digest(source / name)
    write_json(args.output / "source-hashes.json", hashes)
    rows = []
    for dt in TIMESTEPS:
        for load in LOADS:
            identifier = f"load-{load:g}-dt-{round(dt * 1e6)}us"
            result = run_case(
                load, dt, args.output / identifier, tight_solver=args.tight_solver
            )
            rows.append(
                {"id": identifier, "load_n": load, "timestep_s": dt, "result": result}
            )
            write_json(args.output / "results.json", rows)
            print(
                json.dumps(
                    {
                        "id": identifier,
                        "valid": result["valid"],
                        "epochs": result["epochs"],
                    }
                ),
                flush=True,
            )
    if any(digest(source / name) != value for name, value in hashes.items()):
        raise RuntimeError("Frozen source changed during measurement")


if __name__ == "__main__":
    main()
