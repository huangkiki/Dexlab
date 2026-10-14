"""Prepare all admitted task demonstrations once, then load hash-bound inputs.

Only actions and the first state are exported. Reward/done labels and later
recorded states never become execution evidence. Historical v1 inputs are not
rewritten into this format.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

import h5py
import numpy as np

from dexlab.libero_dataset import (
    CHUNK_BYTES, _array_identity, _file_identity, _metadata, _text,
    _validate_receipt, frozen_inputs,
)
from dexlab.libero_inputs import bddl_identity
from dexlab.libero_workflow import UPSTREAM, file_hash
from dexlab.migration_budget import json_bytes, publish

COMMON_FILES = {"task.json", "admission.json", "metadata.json", "task.bddl"}


def _demo_arrays(actions, initial, declaration):
    if (actions.shape != (declaration["action_count"], 7)
            or actions.dtype.str != declaration["actions_dtype"]
            or not np.isfinite(actions).all()
            or _array_identity(initial) != declaration["first_recorded_state"]
            or not np.isfinite(initial).all()):
        raise ValueError("Demonstration input differs from its admitted shape, dtype or state")


def prepare_task(libero_root, frozen, task_id, data_root, receipt_path, destination):
    """Hash one complete HDF5 descriptor and export every admitted demonstration.

    Publish the completion manifest last. A failed/partial directory is retained
    and cannot be reused. Run under the repository's bounded execution ledger.
    """
    inputs, inventory_hash = frozen_inputs(Path(libero_root), Path(frozen))
    task = next((row for row in inputs["tasks"] if row["task_id"] == task_id), None)
    if task is None:
        raise ValueError("Task is absent from the frozen inventory")
    receipt_raw = Path(receipt_path).read_bytes()
    receipt = json.loads(receipt_raw)
    _validate_receipt(receipt, task, inventory_hash)
    bddl = (Path(libero_root) / task["bddl_path"]).read_bytes()
    if hashlib.sha256(bddl).hexdigest() != task["bddl_sha256"]:
        raise ValueError("Task BDDL changed before input preparation")
    root = Path(data_root).resolve(strict=True)
    relative = Path(task["dataset"]["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Dataset path differs from the relative inventory contract")
    # The admitted corpus can reuse an existing mounted cache through symlinks.
    # Hash the opened bytes and compare descriptor/path identities afterwards.
    dataset = root / relative
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    phase, selected = "file-identity", None
    try:
        with dataset.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if before.st_size != task["dataset"]["bytes"]:
                raise ValueError("Dataset byte count differs from admitted input")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(CHUNK_BYTES), b""):
                digest.update(block)
            if digest.hexdigest() != task["dataset"]["sha256"]:
                raise ValueError("Dataset hash differs from admitted input")
            stream.seek(0)
            phase = "metadata"
            with h5py.File(stream, "r") as hdf:
                data = hdf["data"]
                if (_metadata(data, task, bddl) != receipt["linkage"]
                        or set(data) != {row["demo_id"] for row in receipt["demonstrations"]}
                        or int(data.attrs["num_demos"]) != receipt["demonstration_count"]
                        or int(data.attrs["total"]) != receipt["action_count"]):
                    raise ValueError("Dataset metadata or demonstration denominator changed")
                publish(destination / "metadata.json", _text(data.attrs["env_args"]).encode())
                phase = "demonstrations"
                for declaration in receipt["demonstrations"]:
                    selected = declaration["demo_id"]
                    demo = data[selected]
                    if (demo["actions"].shape != (declaration["action_count"], 7)
                            or demo["actions"].dtype.str != declaration["actions_dtype"]
                            or demo["states"].shape != (declaration["action_count"], declaration["state_width"])
                            or int(demo.attrs["num_samples"]) != declaration["action_count"]):
                        raise ValueError("Demonstration dimensions changed after admission")
                    actions, initial = demo["actions"][:], demo["states"][0]
                    _demo_arrays(actions, initial, declaration)
                    if _array_identity(np.asarray(demo.attrs["init_state"])) != declaration["initial_state"]:
                        raise ValueError("Demonstration initialization declaration changed")
                    xml = _text(demo.attrs["model_file"]).encode()
                    if hashlib.sha256(xml).hexdigest() != declaration["model_xml_sha256"]:
                        raise ValueError("Demonstration model changed after admission")
                    with (destination / (selected + ".npz")).open("xb") as output:
                        np.savez_compressed(output, actions=actions, initial=initial)
                    publish(destination / (selected + ".xml"), xml)
            after = os.fstat(stream.fileno())
            if not _file_identity(before) == _file_identity(after) == _file_identity(dataset.stat()):
                raise ValueError("Dataset changed during input preparation")
        publish(destination / "task.json", json_bytes(task))
        publish(destination / "task.bddl", bddl)
        publish(destination / "admission.json", receipt_raw)
        manifest = {"schema_version": 2, "kind": "libero-task-input", "status": "prepared",
                    "upstream_commit": inputs["upstream_commit"], "inventory_sha256": inventory_hash,
                    "task_id": task_id, "demonstrations": receipt["demonstrations"],
                    "demonstration_count": receipt["demonstration_count"],
                    "action_count": receipt["action_count"], "producer_sha256": file_hash(__file__),
                    "files": {p.name: file_hash(p) for p in sorted(destination.iterdir())}}
        publish(destination / "manifest.json", json_bytes(manifest))
        return manifest
    except BaseException as error:
        publish(destination / "failure.json", json_bytes({"status": "failed", "phase": phase,
                "demo_id": selected, "error_type": type(error).__name__}))
        raise


def load_demo(directory, manifest_sha256, demo_id):
    """Load one input from an externally frozen manifest without dropping peers."""
    directory = Path(directory).resolve(strict=True)
    raw = (directory / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest_sha256:
        raise ValueError("Prepared input manifest differs from the frozen case")
    manifest = json.loads(raw)
    if (manifest.get("schema_version") != 2 or manifest.get("kind") != "libero-task-input"
            or manifest.get("status") != "prepared" or manifest.get("upstream_commit") != UPSTREAM):
        raise ValueError("Expected a complete version-2 native input snapshot")
    if (directory / "failure.json").exists():
        raise ValueError("Failed preparation cannot become an execution input")
    names = [row["demo_id"] for row in manifest["demonstrations"]]
    if demo_id not in names:
        raise ValueError("Demonstration is absent from the frozen denominator")
    expected = COMMON_FILES | {name + suffix for name in names for suffix in (".npz", ".xml")}
    if set(manifest["files"]) != expected:
        raise ValueError("Input manifest omits or adds demonstration files")

    def read(name):
        path = directory / name
        if not path.resolve(strict=True).is_relative_to(directory):
            raise ValueError("Snapshot input escapes its root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["files"][name]:
            raise ValueError("Prepared input file changed: " + name)
        return raw

    task, admission = json.loads(read("task.json")), json.loads(read("admission.json"))
    _validate_receipt(admission, task, manifest["inventory_sha256"])
    if (task["task_id"] != manifest["task_id"]
            or manifest["demonstrations"] != admission["demonstrations"]
            or manifest["demonstration_count"] != admission["demonstration_count"]
            or manifest["action_count"] != admission["action_count"]):
        raise ValueError("Prepared denominator differs from content admission")
    bddl, metadata_raw = read("task.bddl"), read("metadata.json")
    if (hashlib.sha256(bddl).hexdigest() != task["bddl_sha256"]
            or bddl_identity(bddl) != task["definition"]
            or hashlib.sha256(metadata_raw).hexdigest() != admission["linkage"]["env_args_sha256"]):
        raise ValueError("Task or environment configuration differs from admission")
    declaration = next(row for row in admission["demonstrations"] if row["demo_id"] == demo_id)
    xml = read(demo_id + ".xml")
    if hashlib.sha256(xml).hexdigest() != declaration["model_xml_sha256"]:
        raise ValueError("Prepared demonstration model differs from admission")
    import io
    with np.load(io.BytesIO(read(demo_id + ".npz")), allow_pickle=False) as archive:
        if set(archive.files) != {"actions", "initial"}:
            raise ValueError("Prepared execution input has unexpected channels")
        actions, initial = archive["actions"], archive["initial"]
    _demo_arrays(actions, initial, declaration)
    return {"manifest": manifest, "task": task, "admission": admission,
            "metadata": json.loads(metadata_raw), "demonstration": declaration,
            "model_xml": xml.decode(), "bddl": bddl, "actions": actions, "initial": initial}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("libero_root", "frozen", "task_id", "data_root", "receipt", "destination"):
        parser.add_argument(name)
    args = parser.parse_args()
    result = prepare_task(args.libero_root, args.frozen, args.task_id, args.data_root,
                          args.receipt, args.destination)
    print(json.dumps({"task_id": result["task_id"], "demonstrations": result["demonstration_count"],
                      "actions": result["action_count"],
                      "manifest_sha256": file_hash(Path(args.destination) / "manifest.json")}))


if __name__ == "__main__":
    main()
