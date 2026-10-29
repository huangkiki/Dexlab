#!/usr/bin/env python3
"""Verify and rescore the published RSS wiping pair without a simulator or network."""

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import re
import time

import numpy as np


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def member_path(root, name):
    relative = PurePosixPath(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or relative.as_posix() != name):
        raise ValueError(f"Unsafe bundle path: {name}")
    return root.joinpath(*relative.parts)


def compiled_model_digest(path):
    """Match the recorder's array identity, independently of NPZ ZIP metadata."""
    digest = hashlib.sha256()
    with np.load(path, allow_pickle=False) as arrays:
        for name in sorted(arrays.files):
            value = arrays[name]
            digest.update(name.encode())
            digest.update(str((value.shape, value.dtype.str)).encode())
            digest.update(value.tobytes())
    return digest.hexdigest()


def verify_bundle(root, manifest):
    """The reviewed repository manifest, not a downloaded summary, defines completeness."""
    if manifest["version"] != 1 or manifest["files"] or manifest.get("repository_files"):
        raise ValueError("Expected the self-contained RSS archive manifest")
    expected = {}
    for archive in manifest["archives"]:
        for name, digest in archive["files"].items():
            member_path(root, name)
            if name in expected or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("Duplicate file or invalid digest in the manifest")
            expected[name] = digest
    if not expected or set(expected) != set(manifest["provenance"]):
        raise ValueError("Every file requires provenance and an expected hash")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Non-regular bundle entry: {path.name}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(expected):
        raise ValueError("Bundle is missing files or contains unexpected files")
    for name, digest in expected.items():
        path = member_path(root, name)
        info = manifest["provenance"][name]
        if (path.stat().st_size != info["bytes"] or sha256(path) != digest):
            raise ValueError(f"Bundle size or SHA-256 mismatch: {name}")
    cases = manifest["evidence"]["cases"]
    if len(cases) != 2 or {case["mode"] for case in cases} != {"original", "no-latch"}:
        raise ValueError("Expected one original/no-latch pair")
    if len({case["id"] for case in cases}) != 2:
        raise ValueError("Duplicate attempt identity")
    for case in cases:
        if not re.fullmatch(r"[a-z0-9-]+", case["id"]):
            raise ValueError("Invalid attempt identity")
        prefix = f"runs/{case['id']}/"
        for required in ("observations.jsonl", "summary.json", "manifest.json", "tracked-patch.npy",
                         "video-times.npy", "initial-particles.npy", "settled-particles.npy", "compiled-model.npz"):
            if prefix + required not in expected:
                raise ValueError(f"Missing raw input for {case['id']}: {required}")
        if not any(name.startswith(prefix + "states/") and name.endswith(".npz") for name in expected):
            raise ValueError("A summary-only bundle cannot be rescored")
        recorded = json.loads((root / prefix / "manifest.json").read_text())
        if (recorded["mode"] != case["mode"]
                or recorded["rss_commit"] != manifest["evidence"]["rss_commit"]):
            raise ValueError("Attempt mode or upstream identity differs from the selected cohort")
        actual_model = compiled_model_digest(root / prefix / "compiled-model.npz")
        if actual_model != recorded["compiled_model"]["sha256"] or actual_model != manifest["evidence"]["compiled_model_sha256"]:
            raise ValueError("Compiled model arrays differ from the frozen cohort")
    for name in ("initial-particles.npy", "settled-particles.npy", "tracked-patch.npy"):
        if len({expected[f"runs/{case['id']}/{name}"] for case in cases}) != 1:
            raise ValueError(f"Pair does not share the frozen cohort: {name}")
    scorer_path = Path(__file__).with_name("score.py")
    if sha256(scorer_path) != expected["source/scoring/score.py"]:
        raise ValueError("Use the reviewed scorer version recorded in the bundle manifest")
    return cases


def plot_curves(cases, curves, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, constrained_layout=True)
    for case in cases:
        rows = curves[case["id"]]
        times = [row["sim_time_s"] for row in rows]
        color = "#1764ab" if case["mode"] == "original" else "#d85a25"
        axes[0].plot(times, [100 * row["cleaned_fraction"] for row in rows],
                     color=color, label=case["id"])
        axes[1].plot(times, [1000 * row["patch_centroid_slip_m"]
                            if row["patch_centroid_slip_m"] is not None and row["grip_command"] >= 0.5
                            else np.nan for row in rows], color=color)
    axes[0].axhline(90, color="#777777", linestyle="--", linewidth=1)
    axes[0].set(ylabel="Cleaned stripe (%)", ylim=(-2, 103))
    axes[0].legend(fontsize=8)
    axes[1].axhline(10, color="#777777", linestyle="--", linewidth=1)
    axes[1].set(ylabel="Holding patch displacement (mm)", xlabel="Simulation time (s)")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.suptitle("One frozen RSS pair: assistance present / removed")
    figure.savefig(output, dpi=180)
    plt.close(figure)


def rescore(root, manifest_path, output):
    started = time.monotonic()
    if output.is_symlink():
        raise ValueError("Choose a new output directory, not a symlink")
    root, output = root.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError("Choose a new output directory outside the immutable bundle")
    manifest = json.loads(manifest_path.read_text())
    cases = verify_bundle(root, manifest)
    # Import reviewed checkout code only; downloaded Python files are evidence.
    spec = importlib.util.spec_from_file_location("rss_wiping_score", Path(__file__).with_name("score.py"))
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    reports, curves = {}, {}
    for case in cases:
        result = scorer.score(root / "runs" / case["id"], include_curves=True)
        if not result["record_integrity_pass"] or result["mode"] != case["mode"]:
            raise ValueError(f"Invalid saved record: {case['id']}: {result['record_failures']}")
        curves[case["id"]] = result.pop("curves")
        reports[case["id"]] = result
    verify_bundle(root, manifest)  # Reject input changes during independent scoring.
    output.mkdir(parents=True, exist_ok=False)
    for attempt, rows in curves.items():
        with (output / f"{attempt}.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    plot_curves(cases, curves, output / "comparison.png")
    report = {
        "schema_version": 1, "bundle_id": manifest["evidence"]["bundle_id"],
        "manifest_sha256": sha256(manifest_path), "python": platform.python_version(),
        "numpy": np.__version__, "records": reports,
        "wall_s": time.monotonic() - started,
        "scope": "One existing paired cohort, saved-state checks and raw-state curves. "
                 "Task failure is retained. No physics execution, hardware validation or solver attribution.",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("evidence-bundle.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(rescore(args.bundle, args.manifest, args.output), indent=2))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Offline rescore failed: {error}\n")


if __name__ == "__main__":
    main()
