#!/usr/bin/env python3
"""Prepare the pinned public AMP inputs without installing or training anything."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


REPOSITORY = "https://github.com/shuayyy/humanoid-amp-ppo.git"
COMMIT = "4889389118e0c88d3945dff54d2cd3f992ed815e"
INPUTS = {
    "models/dualarm.pt": (11932163, "092db6423e6c593d049ec81e3ac78d04c8286973"),
    "dataset/dualarm/dual_arm1.npy": (30224, "b8c981b20bc8d09b0853728eb870a072da74fbf2"),
    "dataset/dualarm/dual_arm2.npy": (30224, "48326c6b83234b8f9990e34af8feae76325991f3"),
}


def inspect_input(path, expected_size, expected_blob):
    """Bind a Git blob identity to the actual downloaded bytes, not an LFS pointer."""
    size = path.stat().st_size
    if size != expected_size:
        raise ValueError(f"Input size differs: {path.name}")
    blob = hashlib.sha1(f"blob {size}\0".encode())
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            blob.update(block)
            sha256.update(block)
    if blob.hexdigest() != expected_blob:
        raise ValueError(f"Input Git identity differs: {path.name}")
    return {"bytes": size, "git_blob": expected_blob, "sha256": sha256.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory on the data volume")
    args = parser.parse_args()
    parent = args.output.resolve().parent
    if not parent.is_dir() or shutil.disk_usage(parent).free < 50 * 1024**3:
        parser.error("Existing parent directory with 50 GiB free is required")
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    source = output / "source"
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1", "GIT_CONFIG_COUNT": "3",
           "GIT_CONFIG_KEY_0": "index.threads", "GIT_CONFIG_VALUE_0": "1",
           "GIT_CONFIG_KEY_1": "pack.threads", "GIT_CONFIG_VALUE_1": "1",
           "GIT_CONFIG_KEY_2": "checkout.workers", "GIT_CONFIG_VALUE_2": "1"}

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(source), *arguments], env=env, text=True).strip()

    subprocess.run(["git", "init", str(source)], env=env, check=True)
    git("remote", "add", "origin", REPOSITORY)
    git("sparse-checkout", "set", "--no-cone", "/src/", "/rsl_rl/", "/dataset/dualarm/",
        "/models/dualarm.pt", "/README.md", "/pyproject.toml", "/uv.lock")
    git("fetch", "--depth=1", "--filter=blob:none", "origin", COMMIT)
    git("checkout", "--detach", COMMIT)
    if git("rev-parse", "HEAD") != COMMIT or git("status", "--porcelain"):
        raise ValueError("Source checkout differs from the pinned commit")
    inputs = {name: inspect_input(source / name, size, blob)
              for name, (size, blob) in INPUTS.items()}
    manifest = {
        "schema_version": 1, "repository": REPOSITORY, "commit": COMMIT,
        "task": "Mjlab-G1-DualArm", "inputs": inputs,
        "uv_lock_sha256": hashlib.sha256((source / "uv.lock").read_bytes()).hexdigest(),
        "role": "Public AMP baseline inputs; distinct from G1-SMTrack-Lift",
        "license_evidence": {
            "repository_declaration": "Apache-2.0 in README and pyproject.toml",
            "asset_motion_weight_provenance": "Separate verification required before native admission or redistribution",
        },
        "native_qualification": "not run", "training": False,
    }
    with (output / "inputs.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    print(output / "inputs.json")


if __name__ == "__main__":
    main()
