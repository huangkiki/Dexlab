"""Lossless MuJoCo model storage for large, independently scorable sweeps."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path


def model_inputs(directory: Path) -> list[Path]:
    raw = directory / "model.mjb"
    if raw.exists():
        return [raw]
    manifest = directory / "model-artifact.json"
    metadata = json.loads(manifest.read_text())
    if metadata["format"] == "chunked-gzip-v1":
        return [manifest, *dict.fromkeys(_chunk_paths(directory, metadata))]
    if metadata["format"] != "gzip":
        raise ValueError("Unknown model archive format")
    return [directory / "model.mjb.gz", manifest]


def _chunk_paths(directory: Path, metadata: dict) -> list[Path]:
    paths = []
    for entry in metadata["chunks"]:
        digest = entry["sha256"]
        if (
            len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
            or type(entry["bytes"]) is not int or not 0 < entry["bytes"] <= 1024 * 1024
        ):
            raise ValueError("Invalid model chunk identity or size")
        paths.append(directory / "model-chunks" / f"{digest}.gz")
    if not paths:
        raise ValueError("Empty model archive")
    return paths


def _read_chunk(path: Path, digest: str, size: int) -> bytes:
    with gzip.open(path, "rb") as stream:
        block = stream.read(size + 1)
    if len(block) != size or hashlib.sha256(block).hexdigest() != digest:
        raise ValueError(f"Model chunk does not match its original bytes: {path.name}")
    return block


def _pack_chunks(directory: Path, shared_store: Path) -> None:
    """Each record stays standalone; immutable gzip chunks share disk inodes."""
    original = directory / "model.mjb"
    shared_store.mkdir(parents=True, exist_ok=True)
    local = directory / "model-chunks"
    local.mkdir(exist_ok=True)
    digest = hashlib.sha256()
    entries = []
    total = 0
    with original.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            identity = hashlib.sha256(block).hexdigest()
            digest.update(block)
            total += len(block)
            cached = shared_store / f"{identity}.gz"
            if not cached.exists():
                with tempfile.NamedTemporaryFile(dir=shared_store, delete=False) as tmp:
                    temporary = Path(tmp.name)
                    tmp.write(gzip.compress(block, compresslevel=1, mtime=0))
                try:
                    _read_chunk(temporary, identity, len(block))
                    # Another writer may already have completed this same immutable chunk.
                    try:
                        os.link(temporary, cached)
                    except FileExistsError:
                        pass
                finally:
                    temporary.unlink()
            _read_chunk(cached, identity, len(block))
            destination = local / cached.name
            if not destination.exists():
                os.link(cached, destination)
            _read_chunk(destination, identity, len(block))
            entries.append({"sha256": identity, "bytes": len(block)})
    metadata = {
        "format": "chunked-gzip-v1",
        "uncompressed_sha256": digest.hexdigest(),
        "uncompressed_bytes": total,
        "chunks": entries,
        "storage": "Record-local immutable chunks; hard links share identical compressed bytes across records",
    }
    manifest = directory / "model-artifact.json"
    temporary = manifest.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(metadata, indent=2) + "\n")
    # Reconstruct and verify the full ordered byte stream before discarding the raw copy.
    restored = hashlib.sha256()
    size = 0
    for path, entry in zip(_chunk_paths(directory, metadata), entries, strict=True):
        block = _read_chunk(path, entry["sha256"], entry["bytes"])
        restored.update(block)
        size += len(block)
    if restored.hexdigest() != digest.hexdigest() or size != original.stat().st_size:
        raise ValueError("Chunked model did not preserve the original bytes")
    temporary.replace(manifest)
    original.unlink()


def pack_model(directory: Path, *, shared_store: Path | None = None) -> None:
    """Replace only this run's generated binary after verifying a lossless round trip."""
    original = directory / "model.mjb"
    if not original.exists():
        return
    if shared_store is not None:
        _pack_chunks(directory, shared_store)
        return
    packed = directory / "model.mjb.gz"
    temporary = directory / "model.mjb.gz.tmp"
    digest = hashlib.sha256()
    with (
        original.open("rb") as source,
        gzip.open(temporary, "wb", compresslevel=1) as target,
    ):
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
            target.write(block)
    restored = hashlib.sha256()
    size = 0
    with gzip.open(temporary, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            restored.update(block)
            size += len(block)
    if restored.digest() != digest.digest() or size != original.stat().st_size:
        raise ValueError("Model compression did not preserve the original bytes")
    metadata = {
        "format": "gzip",
        "uncompressed_sha256": digest.hexdigest(),
        "uncompressed_bytes": size,
        "packed_bytes": temporary.stat().st_size,
    }
    temporary.replace(packed)
    manifest = directory / "model-artifact.json"
    manifest.write_text(json.dumps(metadata, indent=2) + "\n")
    original.unlink()


def load_model(directory: Path):
    """Load raw or compressed evidence, validating restored bytes before MuJoCo."""
    import mujoco

    original = directory / "model.mjb"
    if original.exists():
        return mujoco.MjModel.from_binary_path(str(original))
    metadata = json.loads((directory / "model-artifact.json").read_text())
    digest = hashlib.sha256()
    size = 0
    with tempfile.TemporaryDirectory(prefix="dexlab-model-") as folder:
        restored = Path(folder) / "model.mjb"
        with restored.open("wb") as target:
            for block in _model_blocks(directory, metadata):
                size += len(block)
                if size > metadata["uncompressed_bytes"]:
                    raise ValueError("Model archive expands beyond its declared size")
                digest.update(block)
                target.write(block)
        if (
            digest.hexdigest() != metadata["uncompressed_sha256"]
            or size != metadata["uncompressed_bytes"]
        ):
            raise ValueError("Model archive does not match its original binary hash")
        return mujoco.MjModel.from_binary_path(str(restored))


def _model_blocks(directory: Path, metadata: dict):
    if metadata["format"] == "chunked-gzip-v1":
        for path, entry in zip(_chunk_paths(directory, metadata), metadata["chunks"], strict=True):
            yield _read_chunk(path, entry["sha256"], entry["bytes"])
    elif metadata["format"] == "gzip":
        with gzip.open(directory / "model.mjb.gz", "rb") as source:
            yield from iter(lambda: source.read(1024 * 1024), b"")
    else:
        raise ValueError("Unknown model archive format")
