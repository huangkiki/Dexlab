"""Lossless MuJoCo model storage for large, independently scorable sweeps."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path


def cpu_contact_address_valid(address, dimension, pyramidal, constraint_count):
    """Check converted CPU bounds before passing a contact to native C code."""
    if dimension not in (1, 3, 4, 6) or constraint_count < 0:
        raise ValueError('Invalid contact dimension or constraint count')
    if address == -1:
        return True  # MuJoCo explicitly returns zero for an inactive contact.
    width = 2 * (dimension - 1) if pyramidal and dimension > 1 else dimension
    return 0 <= address and address + width <= constraint_count


def warp_model_parameters(model):
    """Read the effective GPU fields used by this rigid-body diagnostic.

    Keep CPU authoring data separate: framework synchronization can overwrite
    these arrays after put_model. Missing fields fail instead of guessing a
    version's defaults. This is a scoped readback, not full model serialization.
    """
    import numpy as np

    fields = {
        '': ('body_pos', 'body_quat', 'body_ipos', 'body_iquat', 'body_mass',
             'body_inertia', 'body_gravcomp', 'body_invweight0', 'qpos0',
             'dof_armature', 'dof_damping', 'dof_frictionloss',
             'geom_type', 'geom_bodyid', 'geom_pos', 'geom_quat', 'geom_size',
             'geom_friction', 'geom_solref', 'geom_solimp', 'geom_margin',
             'geom_gap', 'geom_condim', 'geom_priority', 'geom_solmix',
             'geom_contype', 'geom_conaffinity', 'tree_sleep_policy'),
        'opt': ('timestep', 'tolerance', 'ls_tolerance', 'ccd_tolerance',
                'sleep_tolerance', 'gravity', 'wind', 'density', 'viscosity',
                'integrator', 'cone', 'solver', 'iterations', 'ls_iterations',
                'ccd_iterations', 'disableflags', 'enableflags',
                'impratio_invsqrt', 'broadphase', 'broadphase_filter',
                'graph_conditional', 'run_collision_detection'),
        'stat': ('meaninertia',),
        'block_dim': ('linesearch_iterative', 'update_gradient_grad',
                      'update_gradient_cholesky', 'contact_jac_tiled'),
    }
    values, dtypes = {}, {}
    for prefix, names in fields.items():
        owner = getattr(model, prefix) if prefix else model
        for name in names:
            value = getattr(owner, name)
            array = np.asarray(value.numpy() if hasattr(value, 'numpy') else value)
            key = f'{prefix}.{name}' if prefix else name
            if not np.isfinite(array).all():
                raise ValueError(f'Non-finite GPU parameter: {key}')
            values[key], dtypes[key] = array.tolist(), str(array.dtype)
    return {'values': values, 'dtypes': dtypes,
            'scope': 'Selected effective rigid-body GPU parameters; not all engine state.'}


def warp_execution_options():
    """Record compilation choices separately from mechanical model parameters."""
    import importlib
    import warp

    result = {}
    for name in ('solver', 'forward', 'smooth', 'collision_driver', 'collision_convex'):
        module = importlib.import_module('mujoco_warp._src.' + name)
        options = warp.get_module_options(module)
        result[name] = {
            key: options.get(key) for key in
            ('enable_backward', 'fast_math', 'fuse_fp', 'max_unroll',
             'deterministic_max_records')
        }
        result[name]['deterministic'] = str(options.get('deterministic'))
    return result


def conversion_parameters(model):
    """Read the compiled model, including frames and drives often changed by import.

    This is an initialization readback. A GPU solver can set its own effective
    timestep later; this snapshot must not be presented as an observed clock.
    """
    import mujoco
    from dexlab.incline_run import native_readback

    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    values = native_readback(model, data)
    for name in (
        'body_pos', 'body_quat', 'qpos0', 'jnt_type', 'jnt_bodyid', 'jnt_pos',
        'jnt_axis', 'jnt_range', 'jnt_limited', 'jnt_stiffness',
        'actuator_trntype', 'actuator_trnid', 'actuator_dyntype',
        'actuator_gaintype', 'actuator_biastype', 'actuator_dynprm',
        'actuator_gainprm', 'actuator_biasprm', 'actuator_gear',
        'actuator_ctrlrange', 'actuator_forcerange',
    ):
        values[name] = getattr(model, name).tolist()
    return values


def parameter_differences(before, after):
    """Report exact structural changes and absolute errors; apply no tolerance.

    A missing field or changed shape must never masquerade as a zero error.
    Physical acceptance and unit-specific limits belong to the frozen protocol.
    """
    import numpy as np

    if before.keys() != after.keys():
        raise ValueError('Parameter fields differ')
    differences = {}
    for name, original in before.items():
        a, b = np.asarray(original), np.asarray(after[name])
        if a.shape != b.shape:
            differences[name] = {'shape_before': list(a.shape), 'shape_after': list(b.shape),
                                 'max_abs': None, 'equal': False}
            continue
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError(f'Non-finite parameter: {name}')
        differences[name] = {
            'equal': bool(np.array_equal(a, b)),
            'max_abs': float(np.max(np.abs(a.astype(float) - b.astype(float)), initial=0.)),
        }
    return differences


def save_conversion_evidence(model, directory, *, intermediate):
    """Preserve the in-memory model and quantify a framework's MJCF export loss.

    The caller preserves and hashes input assets and conversion sources. Use the
    framework's own intermediate MJCF; MjSpec-built models cannot be exported
    with mj_saveLastXML. Refuse to overwrite any earlier evidence.
    """
    import mujoco

    directory, intermediate = Path(directory), Path(intermediate)
    binary, receipt = directory / 'model.mjb', directory / 'conversion-readback.json'
    if binary.exists() or receipt.exists():
        raise FileExistsError('Preserve earlier conversion evidence')
    before = conversion_parameters(model)
    # Reserve the path before the native writer opens it.
    with binary.open('xb'):
        pass
    mujoco.mj_saveModel(model, str(binary), None)
    restored = conversion_parameters(mujoco.MjModel.from_binary_path(str(binary)))
    binary_diff = parameter_differences(before, restored)
    if not all(row['equal'] for row in binary_diff.values()):
        raise ValueError('Binary model readback changed during save/reload')
    exported = conversion_parameters(mujoco.MjModel.from_xml_path(str(intermediate)))
    values = {
        'schema_version': 1,
        'epoch': 'initialization; effective GPU timestep must be observed at step',
        'compiled': before,
        'binary_readback_exact': True,
        'intermediate_readback': exported,
        'intermediate_differences': parameter_differences(before, exported),
        'sha256': {
            'model.mjb': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'intermediate_mjcf': hashlib.sha256(intermediate.read_bytes()).hexdigest(),
        },
    }
    with receipt.open('x') as stream:
        json.dump(values, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return values


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
