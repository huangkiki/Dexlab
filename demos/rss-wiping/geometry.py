"""Capture official CoACD outputs once, then replay their exact arrays."""

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

import numpy as np


def load_parts(path: Path, expected_sha256: str):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError(f"Frozen collision geometry changed: {path.name}")
    with np.load(path, allow_pickle=False) as data:
        return [(data[f"vertices_{i}"], data[f"indices_{i}"])
                for i in range(len(data.files) // 2)]


@contextmanager
def frozen_colliders(folder: Path, capture: bool):
    """Interpose only at asset preprocessing; restore the method after build."""
    from robosimstudio.robots.entity import EntityEmbodiment

    original = EntityEmbodiment._convex_pieces
    index_path = folder / "index.json"
    if capture:
        folder.mkdir(parents=True, exist_ok=False)
        entries = []
    else:
        entries = json.loads(index_path.read_text())
    seen = []

    def pieces(entity, mesh, threshold):
        ordinal = len(seen)
        digest = hashlib.sha256()
        digest.update(np.asarray(mesh.vertices, dtype=np.float64).tobytes())
        digest.update(np.asarray(mesh.indices, dtype=np.int32).tobytes())
        digest.update(json.dumps([
            entity.spec.name, threshold, getattr(mesh, "maxhullvert", 64),
            entity.SLIVER_FLOOR,
        ]).encode())
        input_sha = digest.hexdigest()
        name = f"{ordinal:04d}.npz"
        if capture:
            result = original(entity, mesh, threshold)
            arrays = {}
            for i, (vertices, indices) in enumerate(result):
                arrays[f"vertices_{i}"] = vertices
                arrays[f"indices_{i}"] = indices
            np.savez(folder / name, **arrays)
            entry = {
                "file": name, "input_sha256": input_sha, "parts": len(result),
                "sha256": hashlib.sha256((folder / name).read_bytes()).hexdigest(),
            }
            entries.append(entry)
        else:
            if ordinal >= len(entries) or entries[ordinal]["input_sha256"] != input_sha:
                raise ValueError("Collision preprocessing inputs or call order changed")
            entry = entries[ordinal]
            result = load_parts(folder / entry["file"], entry["sha256"])
        seen.append(entry)
        return result

    EntityEmbodiment._convex_pieces = pieces
    try:
        yield seen
        if capture:
            index_path.write_text(json.dumps(entries, indent=2) + "\n")
        elif len(seen) != len(entries):
            raise ValueError("Not all frozen collision geometry was used")
    finally:
        EntityEmbodiment._convex_pieces = original
