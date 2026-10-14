#!/usr/bin/env python3
"""Freeze the official single-task dataset and create an isolated LIBERO campaign."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from dexlab.libero_trials import create
from dexlab.libero_workflow import TASK, UPSTREAM, file_hash

DATASET_SHA256 = "7ae50ed3a64bab8418fd6c8e346ba1c39da0fdaa62916a87b9d20f3745b45406"
DATASET_REVISION = "f13aa24a3da8c43c7225569f28c562979fa0e35a"


def main():
    import h5py

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libero-root", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source, dataset, output = (
        p.resolve() for p in (args.libero_root, args.dataset, args.output)
    )
    if file_hash(dataset) != DATASET_SHA256:
        raise ValueError(
            "Expected the frozen official cream-cheese dataset; do not substitute another cohort"
        )
    with h5py.File(dataset, "r") as stream:
        names = sorted(stream["data"], key=lambda name: int(name.split("_")[-1]))
        if len(names) != 50 or not str(stream["data"].attrs["bddl_file_name"]).endswith(
            f"libero_object/{TASK}.bddl"
        ):
            raise ValueError("Unexpected dataset identity")
    output.mkdir(parents=True, exist_ok=False)
    config, cache = output / "config", output / "cache"
    config.mkdir()
    cache.mkdir()
    base = source / "libero/libero"
    paths = dict(
        benchmark_root=base,
        bddl_files=base / "bddl_files",
        init_states=base / "init_files",
        assets=base / "assets",
        datasets=dataset.parent,
    )
    (config / "config.yaml").write_text(
        "\n".join(f"{key}: {json.dumps(str(value))}" for key, value in paths.items())
        + "\n"
    )
    versions = {
        dist.metadata["Name"]: dist.version
        for dist in importlib.metadata.distributions()
    }
    (output / "runtime.json").write_text(json.dumps(versions, indent=2) + "\n")
    inputs = [
        {"path": str(p), "sha256": file_hash(p)}
        for p in (
            dataset,
            output / "runtime.json",
            config / "config.yaml",
            source / "libero/lifelong/evaluate.py",
            source / "libero/lifelong/metric.py",
            base / f"bddl_files/libero_object/{TASK}.bddl",
        )
    ]
    protocol = json.loads(Path(__file__).with_name("protocol.json").read_text())
    manifest = dict(
        schema_version=1,
        task=TASK,
        upstream_commit=UPSTREAM,
        libero_root=str(source),
        dataset=str(dataset),
        python=sys.executable,
        config_dir=str(config),
        cache_dir=str(cache),
        seed=0,
        inputs=inputs,
        runtime_versions=versions,
        development=protocol["development"],
        heldout=protocol["heldout"],
        candidates=protocol["candidates"],
        diagnostic_protocol=protocol["diagnostic_protocol"],
        work_package=dict(
            id="libero-native-v1",
            hypothesis="Native action and observation consistency",
            max_starts=64,
            wall_s=21600,
            evidence_sha256=[r["sha256"] for r in inputs],
        ),
    )
    create(output / "campaign", manifest)
    print(output / "campaign")


if __name__ == "__main__":
    main()
