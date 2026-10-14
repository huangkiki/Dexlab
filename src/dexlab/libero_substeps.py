"""Lossless per-action archives of ragged native substep records, without pickle."""

import json
import math
from pathlib import Path

import numpy as np


def write_chunk(path, rows):
    """Keep array shapes/dtypes and invalid numerical evidence in an NPZ chunk."""
    arrays = []

    def encode(value):
        if isinstance(value, (np.ndarray, np.generic)) or isinstance(value, float) and not np.isfinite(value):
            array = np.asarray(value)
            if array.dtype.kind not in "biuf":
                raise ValueError("Substep arrays must be numeric and pickle-free")
            index = len(arrays)
            arrays.append(array)
            return {"__ndarray__": index}
        if isinstance(value, dict):
            if "__ndarray__" in value:
                raise ValueError("Reserved substep archive key")
            return {key: encode(item) for key, item in value.items()}
        if isinstance(value, list):
            return [encode(item) for item in value]
        return value

    tree = encode(rows)
    metadata = {"schema_version": 2, "rows": tree,
                "arrays": [{"dtype": array.dtype.str, "shape": array.shape} for array in arrays]}
    # A single byte buffer avoids thousands of ZIP/NPY headers per action.
    # C-order bytes retain dtype, byte order, signed zeros and NaN payloads.
    payload = np.frombuffer(b"".join(array.tobytes(order="C") for array in arrays), dtype=np.uint8)
    metadata = np.frombuffer(json.dumps(metadata, allow_nan=False).encode(), dtype=np.uint8)
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, payload=payload, metadata=metadata)


def _unpack_arrays(archive, metadata):
    """Validate contiguous extents before creating independent, writable arrays."""
    if set(archive.files) != {"payload", "metadata"} or not isinstance(metadata.get("arrays"), list):
        raise ValueError("Invalid packed substep members")
    payload = archive["payload"]
    if payload.dtype != np.uint8 or payload.ndim != 1:
        raise ValueError("Invalid packed substep payload")
    arrays, offset = {}, 0
    for index, spec in enumerate(metadata["arrays"]):
        if not isinstance(spec, dict) or set(spec) != {"dtype", "shape"}:
            raise ValueError("Invalid packed substep descriptor")
        shape = spec["shape"]
        if not isinstance(spec["dtype"], str) or not isinstance(shape, list) or any(type(n) is not int or n < 0 for n in shape):
            raise ValueError("Invalid packed substep dtype or shape")
        try:
            dtype = np.dtype(spec["dtype"])
        except TypeError as error:
            raise ValueError("Invalid packed substep array dtype") from error
        if dtype.kind not in "biuf" or dtype.str != spec["dtype"]:
            raise ValueError("Invalid packed substep array dtype")
        count = math.prod(shape)
        end = offset + count * dtype.itemsize
        if end > payload.size:
            raise ValueError("Truncated packed substep payload")
        arrays[index] = np.frombuffer(payload, dtype=dtype, count=count, offset=offset).reshape(shape).copy()
        offset = end
    if offset != payload.size:
        raise ValueError("Unreferenced packed substep bytes")
    return arrays


def read_chunk(path):
    with np.load(path, allow_pickle=False) as archive:
        if len(archive.files) != len(set(archive.files)):
            raise ValueError("Duplicate substep archive member")
        metadata = archive["metadata"]
        if metadata.dtype != np.uint8 or metadata.ndim != 1:
            raise ValueError("Invalid substep metadata encoding")
        tree = json.loads(metadata.tobytes())
        if not isinstance(tree, dict) or tree.get("schema_version") not in (1, 2) or not isinstance(tree.get("rows"), list):
            raise ValueError("Unsupported substep archive")
        packed = tree["schema_version"] == 2
        arrays = _unpack_arrays(archive, tree) if packed else archive
        expected = set(arrays) if packed else set(archive.files) - {"metadata"}
        seen = set()

        def decode(value):
            if isinstance(value, dict):
                if set(value) == {"__ndarray__"}:
                    key = value["__ndarray__"]
                    if type(key) is not (int if packed else str) or key in seen or key not in expected:
                        raise ValueError("Aliased or missing substep array")
                    seen.add(key)
                    array = arrays[key]
                    if array.dtype.kind not in "biuf":
                        raise ValueError("Invalid substep array dtype")
                    return array
                if "__ndarray__" in value:
                    raise ValueError("Reserved substep archive key")
                return {key: decode(item) for key, item in value.items()}
            if isinstance(value, list):
                return [decode(item) for item in value]
            return value

        rows = decode(tree["rows"])
        if seen != expected:
            raise ValueError("Unreferenced substep arrays")
        return rows


class SubstepArchive:
    """Bound memory to one action; preserve a failed action's observed prefix."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=False)
        self.rows = []
        self.action = None
        self.substeps = 0
        self.chunks = []

    def start_action(self, action):
        if self.action is not None or self.rows or action != len(self.chunks):
            raise ValueError("Substep actions must be consecutive and flushed")
        self.action = action

    def append(self, row):
        if self.action is None or row["sequence"] != self.substeps:
            raise ValueError("Substep has no action or its sequence is incomplete")
        self.rows.append({**row, "action_index": self.action})
        self.substeps += 1

    def flush(self):
        if self.action is None:
            raise ValueError("No active substep action")
        name = f"action-{self.action:06d}.npz"
        write_chunk(self.directory / name, self.rows)
        self.chunks.append({"name": name, "action_index": self.action, "substeps": len(self.rows)})
        self.rows.clear()
        self.action = None
