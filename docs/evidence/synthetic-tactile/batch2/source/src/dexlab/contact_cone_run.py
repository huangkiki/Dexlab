"""Execute the fixed 26-case matrix inside an admitted external resource guard."""

import argparse
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import shutil
import time

import numpy as np

from dexlab.contact_cone import (
    PROTOCOL_SHA256,
    IMPEDANCE,
    case_for,
    jobs,
    verify,
    verify_matrix,
)
from dexlab.physx_baseline import digest, write_json


def run_case(job, output):
    from dexlab.contact_plane_native import MuJoCoPlane

    output.mkdir(parents=True, exist_ok=False)
    case = case_for(job)
    normal = {"solref": [job["timeconst"], 1.0], "solimp": IMPEDANCE}
    native = MuJoCoPlane(
        case, output, normal_parameters=normal, friction_cone=job["cone"]
    )
    poses, velocities, times, forces, completed = ([] for _ in range(5))
    try:
        write_json(output / "native.json", native.metadata)
        native.start()
        pose, velocity = native.observe()
        poses.append(pose)
        velocities.append(velocity)
        times.append(native.clock())
        with gzip.open(output / "contacts.jsonl.gz", "wt") as stream:
            for _ in range(case.steps):
                pose, velocity, force, contacts, ok, warnings = native.step(np.zeros(3))
                poses.append(pose)
                velocities.append(velocity)
                times.append(native.clock())
                forces.append(force)
                completed.append(ok)
                stream.write(
                    json.dumps(
                        {"warnings": warnings, "contacts": contacts}, allow_nan=False
                    )
                    + "\n"
                )
        np.savez_compressed(
            output / "states.npz",
            time=np.asarray(times),
            pose=np.asarray(poses),
            velocity=np.asarray(velocities),
            contact_force=np.asarray(forces),
            contact_known=np.ones(case.steps, dtype=bool),
            step_completed=np.asarray(completed, dtype=bool),
            external_force=np.zeros((case.steps, 3)),
        )
        write_json(
            output / "receipt.json",
            {
                "job": job,
                "case": asdict(case),
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
    except Exception as error:
        write_json(
            output / "error.json", {"type": type(error).__name__, "message": str(error)}
        )
        np.savez_compressed(
            output / "partial-states.npz",
            time=np.asarray(times),
            pose=np.asarray(poses).reshape(-1, 7),
            velocity=np.asarray(velocities).reshape(-1, 6),
            contact_force=np.asarray(forces).reshape(-1, 3),
        )
        raise
    finally:
        native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_matrix(args.output), indent=2))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent
    protocol = source.parents[1] / "benchmarks/contact-cone-timeconst-v1.json"
    if digest(protocol) != PROTOCOL_SHA256:
        raise ValueError("Protocol changed before execution")
    shutil.copyfile(protocol, args.output / "protocol.json")
    paths = sorted(source.glob("*.py"))
    hashes = {path.name: digest(path) for path in paths}
    snapshot = args.output / "source"
    snapshot.mkdir()
    for path in paths:
        shutil.copyfile(path, snapshot / path.name)
    write_json(args.output / "source-hashes.json", hashes)
    started = time.monotonic()
    results = []
    for job in jobs():
        if time.monotonic() - started >= 600:
            raise TimeoutError(
                "Fixed study budget exhausted; partial evidence retained"
            )
        result = run_case(job, args.output / job["id"])
        results.append({"job": job, "result": result})
        write_json(args.output / "results.json", results)
        print(
            json.dumps(
                {
                    "id": job["id"],
                    "valid": result["valid"],
                    "engineering_pass": result["engineering"]["passed"],
                }
            ),
            flush=True,
        )
        physical_checks = {
            "momentum_balance",
            "native_steps_completed",
            "native_warnings",
        }
        if not all(
            value
            for key, value in result["checks"].items()
            if key not in physical_checks
        ):
            raise RuntimeError(
                "Record integrity failed; remaining cases were not launched"
            )
    if any(digest(source / name) != value for name, value in hashes.items()):
        raise RuntimeError("Source changed during experiment")
    write_json(args.output / "matrix-score.json", verify_matrix(args.output))


if __name__ == "__main__":
    main()
