"""Rescore archived tangent measurements without importing a physics engine."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.contact_tangent import score
from dexlab.physx_baseline import digest


def verify(directory):
    directory = Path(directory)
    receipt = json.loads((directory / "receipt.json").read_text())
    paths = {"arrays_sha256": "states.npz", "contacts_sha256": "contacts.jsonl.gz"}
    if any(digest(directory / name) != receipt[key] for key, name in paths.items()):
        raise ValueError("Measurement archive hash mismatch")
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    ledger, counts, completed = [], [], []
    with gzip.open(directory / "contacts.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            points = row["contacts"]
            ledger.append(
                np.sum([point["force_on_box"] for point in points], axis=0)
                if points
                else np.zeros(3)
            )
            counts.append(len(points))
            completed.append(row["status"] in ("CONVERGED", "STOPPED"))
    reconstructed = {
        "ledger": np.asarray(ledger),
        "contacts": np.asarray(counts),
        "completed": np.asarray(completed, dtype=bool),
    }
    if any(
        not np.array_equal(data[key], value) for key, value in reconstructed.items()
    ):
        raise ValueError("Raw per-step contacts disagree with recorded arrays")
    return score(receipt["load_n"], receipt["timestep_s"], data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
