"""Admit complete, pinned LIBERO HDF5 inputs without reading success outcomes.

This module checks recorded input identity, not physics or native execution.
Install DexLab's ``libero-inputs`` extra to use the HDF5 reader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET

import h5py
import numpy as np

from dexlab.libero_inputs import DATASET_REVISION, inventory
from dexlab.migration_budget import json_bytes, publish

CHUNK_BYTES = 8 * 1024 * 1024
EXPOSED_TASK = "libero_object/pick_up_the_cream_cheese_and_place_it_in_the_basket"
SPLIT_PROTOCOL = {
    "schema_version": 1,
    "dataset_revision": DATASET_REVISION,
    "salt": "dexlab-libero-inputs-v1-2026-10-12",
    "validation_fraction": {"numerator": 1, "denominator": 5},
    "rule": "Per task, rank unexposed IDs by SHA256(salt + LF + task_id + LF + demo_id), "
            "breaking ties by numeric demo ID. Assign floor(unexposed_count / 5) to validation.",
    "exposed_development": {EXPOSED_TASK: [f"demo_{i}" for i in range(13)]},
    "small_cohort": "Fewer than five unexposed demonstrations gives zero validation cases.",
    "baseline_scope": "Every demonstration, independently of split assignment.",
    "outcomes": "No rewards, dones, success labels or images are read to assign the split.",
}


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if not isinstance(value, str):
        raise ValueError("Expected a UTF-8 text attribute")
    return value


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _integer(value: Any, label: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def split_assignments(task_id: str, demo_ids: list[str]) -> dict[str, str]:
    if (len(set(demo_ids)) != len(demo_ids)
            or any(not re.fullmatch(r"demo_(0|[1-9][0-9]*)", name) for name in demo_ids)):
        raise ValueError("Duplicate or malformed demonstration IDs")
    exposed = set(SPLIT_PROTOCOL["exposed_development"].get(task_id, []))
    eligible = set(demo_ids) - exposed
    salt = SPLIT_PROTOCOL["salt"]
    ranked = sorted(eligible, key=lambda name: (
        _digest(f"{salt}\n{task_id}\n{name}".encode()), int(name[5:])))
    validation = set(ranked[:len(ranked) // 5])
    return {name: "validation" if name in validation else "development" for name in demo_ids}


def _internal_objects(root: h5py.File) -> None:
    """Reject content whose identity is not confined to this file's bytes."""
    seen = {h5py.h5o.get_info(root.id).addr}
    pending = [root]
    while pending:
        group = pending.pop()
        for name in group:
            if not isinstance(group.get(name, getlink=True), h5py.HardLink):
                raise ValueError("Soft/external HDF5 links are not admissible")
            obj = group[name]
            address = h5py.h5o.get_info(obj.id).addr
            if address in seen:
                raise ValueError("Aliased/cyclic HDF5 objects are not admissible")
            seen.add(address)
            if isinstance(obj, h5py.Group):
                pending.append(obj)
            elif isinstance(obj, h5py.Dataset):
                if obj.is_virtual or obj.external:
                    raise ValueError("Virtual/external HDF5 storage is not admissible")
            else:
                raise ValueError("Unexpected HDF5 object type")


def _matches_bddl_path(value: str, task: dict[str, Any]) -> bool:
    path = PurePosixPath(value)
    return (".." not in path.parts and len(path.parts) >= 3
            and path.parts[-3:] == ("bddl_files", task["suite"], task["task"] + ".bddl"))


def _metadata(data: h5py.Group, task: dict[str, Any], bddl: bytes) -> dict[str, Any]:
    definition = task["definition"]
    if not _matches_bddl_path(_text(data.attrs["bddl_file_name"]), task):
        raise ValueError("Canonical dataset BDDL task identity differs")
    info = json.loads(_text(data.attrs["problem_info"]))
    for field, expected in (("problem_name", definition["problem"]),
                            ("domain_name", definition["domain"])):
        if _normalize(_text(info[field])) != expected:
            raise ValueError(f"Dataset {field} differs from pinned BDDL")
    language = _normalize(_text(info["language_instruction"]))
    language_matches = {"bddl": language == definition["language"],
                        "benchmark": language == _normalize(task["benchmark_language"])}
    if not any(language_matches.values()):
        raise ValueError("Dataset language_instruction matches neither pinned source declaration")
    if _normalize(_text(data.attrs["env_name"])) != definition["problem"]:
        raise ValueError("Dataset environment differs from pinned BDDL problem")
    raw_env = _text(data.attrs["env_args"])
    env = json.loads(raw_env)
    for field in ("env_name", "problem_name"):
        if _normalize(_text(env[field])) != definition["problem"]:
            raise ValueError(f"Environment {field} differs from pinned BDDL problem")
    # Official historical files can retain pre-rename filenames here. These are
    # auxiliary declarations, not a validated path to use for native execution.
    references = {}
    for label, value in (("bddl_file", env.get("bddl_file")),
                         ("env_kwargs.bddl_file_name", env.get("env_kwargs", {}).get("bddl_file_name"))):
        references[label] = ("not-provided" if value is None else
                             "matches" if _matches_bddl_path(_text(value), task) else "differs")
    embedded = "not-provided"
    if "bddl_file_content" in data.attrs:
        if _text(data.attrs["bddl_file_content"]).encode() != bddl:
            raise ValueError("Embedded BDDL bytes differ from pinned source")
        embedded = "exact-byte-match"
    return {"canonical_task_linkage": "matches", "problem_domain_linkage": "matches",
            "language": {"dataset": language, "bddl": definition["language"],
                         "benchmark": task["benchmark_language"], "matches": language_matches},
            "embedded_bddl": embedded, "environment_bddl_references": references,
            "env_args_sha256": _digest(raw_env.encode()),
            "native_environment_configuration_qualified": False}


def _matrix(group: h5py.Group, name: str, rows: int, width: int | None = None) -> h5py.Dataset:
    value = group[name]
    if (not isinstance(value, h5py.Dataset) or value.ndim != 2 or value.shape[0] != rows
            or value.shape[1] == 0 or (width is not None and value.shape[1] != width)
            or value.dtype.kind != "f"):
        raise ValueError(f"Invalid {name} shape or floating dtype")
    row_bytes = value.shape[1] * value.dtype.itemsize
    if row_bytes > CHUNK_BYTES:
        raise ValueError(f"One {name} row exceeds the declared read buffer")
    step = max(1, CHUNK_BYTES // row_bytes)
    for start in range(0, rows, step):
        if not np.isfinite(value[start:start + step]).all():
            raise ValueError(f"Non-finite {name}")
    return value


def _array_identity(value: np.ndarray) -> dict[str, Any]:
    return {"dtype": value.dtype.str, "shape": list(value.shape),
            "sha256": _digest(value.tobytes(order="C"))}


def _demonstrations(data: h5py.Group, task_id: str) -> list[dict[str, Any]]:
    names = list(data)
    splits = split_assignments(task_id, names)
    if not names or _integer(data.attrs["num_demos"], "num_demos") != len(names):
        raise ValueError("Declared demonstration count differs or is empty")
    result = []
    exposed = set(SPLIT_PROTOCOL["exposed_development"].get(task_id, []))
    for name in sorted(names, key=lambda value: int(value[5:])):
        demo = data[name]
        if not isinstance(demo, h5py.Group):
            raise ValueError("A demonstration must be an HDF5 group")
        rows = _integer(demo.attrs["num_samples"], "num_samples")
        if rows <= 0:
            raise ValueError("Empty demonstration")
        actions = _matrix(demo, "actions", rows, 7)
        states = _matrix(demo, "states", rows)
        initial = np.asarray(demo.attrs["init_state"])
        first = states[0]
        if (initial.shape != first.shape or initial.dtype.kind != "f"
                or not np.isfinite(initial).all() or not np.array_equal(initial, first)):
            raise ValueError("Initial state differs from first recorded state or is invalid")
        model = _text(demo.attrs["model_file"]).encode()
        if b"<!DOCTYPE" in model.upper() or b"<!ENTITY" in model.upper():
            raise ValueError("Model XML must not contain entity declarations")
        if ET.fromstring(model).tag != "mujoco":
            raise ValueError("Expected a MuJoCo model XML root")
        result.append({"demo_id": name, "action_count": rows,
                       "actions_dtype": actions.dtype.str, "state_width": states.shape[1],
                       "states_dtype": states.dtype.str, "initial_state": _array_identity(initial),
                       "first_recorded_state": _array_identity(first),
                       "initial_matches_first_state": True, "model_xml_sha256": _digest(model),
                       "split": splits[name], "previously_exposed": name in exposed})
    if _integer(data.attrs["total"], "total") != sum(row["action_count"] for row in result):
        raise ValueError("Declared total differs from all demonstration action counts")
    return result


def _file_identity(stat: os.stat_result) -> tuple[int, ...]:
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def admit_file(path: Path, task: dict[str, Any], bddl: bytes,
               inventory_sha256: str) -> dict[str, Any]:
    """Hash first, inspect the same read-only descriptor, retain every demo."""
    if _digest(bddl) != task["bddl_sha256"]:
        raise ValueError("Pinned BDDL hash differs")
    expected = task["dataset"]
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_size != expected["bytes"]:
            raise ValueError("Dataset byte count differs from pinned metadata")
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != expected["sha256"]:
            raise ValueError("Dataset hash differs from pinned metadata")
        stream.seek(0)
        with h5py.File(stream, "r") as hdf:
            _internal_objects(hdf)
            if set(hdf) != {"data"} or not isinstance(hdf["data"], h5py.Group):
                raise ValueError("Expected only the data root group")
            linkage = _metadata(hdf["data"], task, bddl)
            demos = _demonstrations(hdf["data"], task["task_id"])
        after = os.fstat(stream.fileno())
        if _file_identity(before) != _file_identity(after) or _file_identity(after) != _file_identity(path.stat()):
            raise ValueError("Dataset changed while being admitted")
    return {"schema_version": 1, "task_id": task["task_id"], "dataset_revision": DATASET_REVISION,
            "inventory_sha256": inventory_sha256,
            "split_protocol_sha256": _digest(json_bytes(SPLIT_PROTOCOL)),
            "reader_sha256": _digest(Path(__file__).read_bytes()),
            "reader": {"h5py": h5py.__version__, "hdf5": h5py.version.hdf5_version,
                       "numpy": np.__version__},
            "dataset": expected, "bddl_sha256": task["bddl_sha256"], "linkage": linkage,
            "demonstration_count": len(demos), "action_count": sum(d["action_count"] for d in demos),
            "validation_count": sum(d["split"] == "validation" for d in demos),
            "demonstrations": demos, "status": "content-admitted", "native_qualified": False}


def freeze_inputs(libero_root: Path, destination: Path) -> None:
    inputs = inventory(libero_root)
    destination.mkdir(parents=True, exist_ok=False)
    publish(destination / "inventory.json", json_bytes(inputs))
    publish(destination / "split-protocol.json", json_bytes(SPLIT_PROTOCOL))


def frozen_inputs(libero_root: Path, frozen: Path) -> tuple[dict[str, Any], str]:
    raw = (frozen / "inventory.json").read_bytes()
    if raw != json_bytes(inventory(libero_root)):
        raise ValueError("Frozen inventory differs from clean pinned source/metadata")
    if (frozen / "split-protocol.json").read_bytes() != json_bytes(SPLIT_PROTOCOL):
        raise ValueError("Frozen split protocol differs; do not reassign exposed outcomes")
    return json.loads(raw), _digest(raw)


def write_receipt(destination: Path, result: dict[str, Any]) -> None:
    raw = json_bytes(result)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != raw:
            raise ValueError("Admission receipt already exists with different evidence; preserve it")
        return
    publish(destination, raw)


def _validate_receipt(result: dict[str, Any], task: dict[str, Any], inventory_hash: str) -> None:
    expected = {"schema_version": 1, "task_id": task["task_id"], "status": "content-admitted",
                "dataset_revision": DATASET_REVISION, "inventory_sha256": inventory_hash,
                "split_protocol_sha256": _digest(json_bytes(SPLIT_PROTOCOL)),
                "dataset": task["dataset"], "bddl_sha256": task["bddl_sha256"],
                "native_qualified": False}
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError("Receipt identity differs from frozen inputs")
    if (result["native_qualified"] is not False
            or not re.fullmatch(r"[0-9a-f]{64}", result["reader_sha256"])
            or any(not isinstance(result["reader"][key], str) or not result["reader"][key]
                   for key in ("h5py", "hdf5", "numpy"))):
        raise ValueError("Receipt lacks reader provenance or misstates native qualification")
    linkage = result["linkage"]
    language = linkage["language"]
    declared = language["dataset"]
    matches = {"bddl": declared == task["definition"]["language"],
               "benchmark": declared == _normalize(task["benchmark_language"])}
    references = linkage["environment_bddl_references"]
    if (linkage["canonical_task_linkage"] != "matches"
            or linkage["problem_domain_linkage"] != "matches"
            or linkage["native_environment_configuration_qualified"] is not False
            or language["bddl"] != task["definition"]["language"]
            or language["benchmark"] != task["benchmark_language"]
            or declared != _normalize(_text(declared)) or not any(matches.values())
            or language["matches"] != matches
            or any(type(value) is not bool for value in language["matches"].values())
            or linkage["embedded_bddl"] not in {"not-provided", "exact-byte-match"}
            or set(references) != {"bddl_file", "env_kwargs.bddl_file_name"}
            or any(value not in {"not-provided", "matches", "differs"} for value in references.values())
            or not re.fullmatch(r"[0-9a-f]{64}", linkage["env_args_sha256"])):
        raise ValueError("Receipt linkage contradicts its pinned task or lacks evidence")
    demos = result["demonstrations"]
    splits = split_assignments(task["task_id"], [d["demo_id"] for d in demos])
    exposed = set(SPLIT_PROTOCOL["exposed_development"].get(task["task_id"], []))
    for demo in demos:
        width = demo["state_width"]
        if (type(width) is not int or width <= 0
                or demo["initial_matches_first_state"] is not True
                or demo["previously_exposed"] is not (demo["demo_id"] in exposed)
                or not re.fullmatch(r"[0-9a-f]{64}", demo["model_xml_sha256"])
                or not isinstance(demo["actions_dtype"], str)
                or not isinstance(demo["states_dtype"], str)
                or np.dtype(demo["actions_dtype"]).kind != "f"
                or np.dtype(demo["states_dtype"]).kind != "f"):
            raise ValueError("Receipt demonstration lacks input identity or contradicts admission")
        for key in ("initial_state", "first_recorded_state"):
            identity = demo[key]
            if (identity["shape"] != [width] or type(identity["shape"][0]) is not int
                    or not isinstance(identity["dtype"], str) or np.dtype(identity["dtype"]).kind != "f"
                    or not re.fullmatch(r"[0-9a-f]{64}", identity["sha256"])):
                raise ValueError("Receipt state identity is incomplete")
        if demo["first_recorded_state"]["dtype"] != demo["states_dtype"]:
            raise ValueError("Receipt first-state dtype differs from recorded states")
    if (not demos or result["demonstration_count"] != len(demos)
            or any(type(result[key]) is not int
                   for key in ("demonstration_count", "action_count", "validation_count"))
            or any(type(d["action_count"]) is not int or d["action_count"] <= 0
                   or d["split"] != splits[d["demo_id"]] for d in demos)
            or result["action_count"] != sum(d["action_count"] for d in demos)
            or result["validation_count"] != sum(s == "validation" for s in splits.values())):
        raise ValueError("Receipt demonstration inventory differs from frozen protocol")


def aggregate(inputs: dict[str, Any], inventory_hash: str, data_root: Path,
              receipt_root: Path) -> dict[str, Any]:
    """Keep every expected task; distinguish historical admission from availability.

    This is a receipt index, not a fresh content hash. Use admit again to check a
    changed or untrusted local file; never infer its current digest from its size.
    """
    rows = []
    for task in inputs["tasks"]:
        path = data_root / task["dataset"]["path"]
        partial = path.with_name(path.name + ".partial")
        receipt = receipt_root / (task["task_id"] + ".json")
        available = ("missing" if not path.exists() else "not-file" if not path.is_file() else
                     "present-size-match" if path.stat().st_size == task["dataset"]["bytes"] else "size-mismatch")
        row = {"task_id": task["task_id"], "expected": task["dataset"],
               "availability": available, "content_admission": "missing-receipt"}
        if available == "missing" and partial.is_file():
            row.update(availability="partial", partial_bytes=partial.stat().st_size)
        if receipt.exists():
            try:
                raw = receipt.read_bytes()
                result = json.loads(raw)
                _validate_receipt(result, task, inventory_hash)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                row["content_admission"] = "invalid-receipt"
            else:
                row.update(content_admission="recorded-admitted", receipt_sha256=_digest(raw),
                           demonstration_count=result["demonstration_count"],
                           action_count=result["action_count"], validation_count=result["validation_count"],
                           linkage=result["linkage"])
        rows.append(row)
    return {"schema_version": 1, "dataset_revision": DATASET_REVISION,
            "inventory_sha256": inventory_hash,
            "scope": "Receipt index and size-only availability; not a fresh file hash or native qualification.",
            "expected_files": len(rows), "expected_bytes": sum(r["expected"]["bytes"] for r in rows),
            "available_files": sum(r["availability"] == "present-size-match" for r in rows),
            "admitted_files": sum(r["content_admission"] == "recorded-admitted" for r in rows),
            "missing_files": sum(r["availability"] == "missing" for r in rows),
            "partial_files": sum(r["availability"] == "partial" for r in rows),
            "invalid_receipts": sum(r["content_admission"] == "invalid-receipt" for r in rows),
            "observed_demonstrations": sum(r.get("demonstration_count", 0) for r in rows),
            "observed_actions": sum(r.get("action_count", 0) for r in rows),
            "native_qualified": False, "tasks": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("libero_root", type=Path)
    freeze.add_argument("destination", type=Path)
    admit = sub.add_parser("admit")
    admit.add_argument("libero_root", type=Path)
    admit.add_argument("frozen", type=Path)
    admit.add_argument("task_id")
    admit.add_argument("dataset", type=Path)
    admit.add_argument("receipt", type=Path)
    summary = sub.add_parser("aggregate")
    summary.add_argument("libero_root", type=Path)
    summary.add_argument("frozen", type=Path)
    summary.add_argument("data_root", type=Path)
    summary.add_argument("receipt_root", type=Path)
    summary.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze_inputs(args.libero_root, args.destination)
        print("Frozen all 130 source identities and the prospective split protocol")
        return
    inputs, digest = frozen_inputs(args.libero_root, args.frozen)
    if args.command == "aggregate":
        result = aggregate(inputs, digest, args.data_root, args.receipt_root)
        write_receipt(args.output, result)
        print(json.dumps({key: value for key, value in result.items() if key != "tasks"}))
        return
    tasks = {task["task_id"]: task for task in inputs["tasks"]}
    if args.task_id not in tasks:
        parser.error("Task is absent from the frozen official inventory")
    task = tasks[args.task_id]
    result = admit_file(args.dataset, task, (args.libero_root / task["bddl_path"]).read_bytes(), digest)
    write_receipt(args.receipt, result)
    print(json.dumps({key: result[key] for key in ("task_id", "status", "demonstration_count",
                                                  "action_count", "validation_count", "linkage")}))


if __name__ == "__main__":
    main()
