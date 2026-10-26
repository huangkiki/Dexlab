"""Read the six immutable Wuji v4 episodes without importing a simulator."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("wuji_response_score", ROOT / "demos/wuji-contact/score.py")
SCORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORE)


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def physical_digest(raw):
    """Ignore archive encoding and wall-clock costs when identifying copies."""
    digest = hashlib.sha256()
    for name in sorted(raw):
        if name in ("step_wall_s", "solver_niter", "solver_last_gradient", "solver_last_improvement"):
            continue
        values = np.asarray(raw[name]).copy()
        if name in ("qpos_before", "qpos_after"):
            quaternions = values[:, 23:27]
            # q and -q represent the same orientation, including w == 0.
            first = np.argmax(quaternions != 0, axis=1)
            sign = np.where(quaternions[np.arange(len(first)), first] < 0, -1., 1.)
            values[:, 23:27] *= sign[:, None]
        values[values == 0] = 0  # Canonicalize signed floating zero.
        values = np.ascontiguousarray(values.astype(values.dtype.newbyteorder("<")))
        digest.update(json.dumps([name, values.dtype.str, values.shape]).encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def validate_shapes(raw):
    n = len(raw["time_s"])
    expected = {"qpos_before": (n, 27), "qpos_after": (n, 27),
                "qvel_before": (n, 26), "qvel_after": (n, 26), "target": (n, 20),
                "requested_torque": (n, 20), "support_force": (n, 3),
                "object_contact_force": (n, 3), "qfrc_applied": (n, 26)}
    for name, shape in expected.items():
        if raw[name].shape != shape:
            raise ValueError(f"Unexpected shape for {name}: {raw[name].shape}")
    if raw["contacts"].ndim != 2 or raw["contacts"].shape[1] != 22:
        raise ValueError("Expected complete 22-column native contacts")
    if np.any(raw["contacts"][:, 16] < -1e-12) or np.any(raw["contacts"][:, :3] != np.floor(raw["contacts"][:, :3])):
        raise ValueError("Invalid native contact identity or tensile normal force")
    if any(not np.isfinite(v).all() for v in raw.values()):
        raise ValueError("Non-finite observations")
    for name in ("qpos_before", "qpos_after"):
        if not np.allclose(np.linalg.norm(raw[name][:, 23:27], axis=1), 1., atol=1e-10, rtol=0):
            raise ValueError("Non-unit object quaternion")


def pad_observations(raw, effective):
    """Keep pair normal load, net force and present contact distance distinct."""
    n = len(raw["time_s"])
    pads = [effective["body_names"].index("r_" + finger + "_pad")
            for finger in ("index_finger", "thumb")]
    loads = np.zeros((n, 2))
    distances = np.full((n, 2), np.nan)
    offsets = raw["contact_offsets"]
    for i in range(n):
        for contact in raw["contacts"][offsets[i]:offsets[i + 1]]:
            if contact[2] in pads:
                pad = pads.index(contact[2])
                loads[i, pad] += contact[16]
                if np.isnan(distances[i, pad]) or contact[15] < distances[i, pad]:
                    distances[i, pad] = contact[15]
    # A missing contact is not a measured positive separation distance.
    return loads, distances


def load_episode(directory, expected_files=None):
    directory = Path(directory)
    if expected_files is not None:
        for name in ("manifest.json", "observations.npz"):
            if sha256(directory / name) != expected_files[name]:
                raise ValueError(f"Pinned bundle file differs: {directory.name}/{name}")
    manifest = json.loads((directory / "manifest.json").read_text())
    with np.load(directory / "observations.npz", allow_pickle=False) as archive:
        raw = dict(archive)
    validate_shapes(raw)
    # Reuse the corrected independent scorer; never trust a saved pass flag.
    qualification = SCORE.evaluate(directory)
    if not qualification["record_integrity_pass"] or not qualification["numerical_balance_pass"]:
        raise ValueError("Record integrity or numerical balance failed")
    loads, distances = pad_observations(raw, manifest["effective"])
    return dict(directory=directory, manifest=manifest, raw=raw, loads=loads,
                distances=distances, qualification=qualification,
                physical_sha256=physical_digest(raw), manifest_sha256=sha256(directory / "manifest.json"))


def load_cohort(bundle, protocol):
    manifest_path = ROOT / "demos/wuji-contact/evidence-bundle.json"
    if sha256(manifest_path) != protocol["bundle_manifest_sha256"]:
        raise ValueError("Bundle index changed; select and review a new offline cohort explicitly")
    manifest = json.loads(manifest_path.read_text())
    expected = manifest["archives"][0]["files"]
    frozen = json.loads((ROOT / "demos/wuji-contact/protocol-v4.json").read_text())
    episodes, copies, seen = [], [], {}
    for relative in protocol["episode_paths"]:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Episode path must remain within the bundle")
        hashes = {name: expected[f"{relative}/{name}"] for name in ("manifest.json", "observations.npz")}
        episode = load_episode(Path(bundle) / relative, hashes)
        if episode["manifest"]["config"] != frozen:
            raise ValueError("Episode does not use the frozen v4 protocol")
        episode["relative_path"] = relative
        fingerprint = episode["physical_sha256"]
        if fingerprint in seen:
            copies.append(dict(path=relative, duplicate_of=seen[fingerprint], physical_sha256=fingerprint))
        else:
            seen[fingerprint] = relative
            episodes.append(episode)
    return episodes, copies
