#!/usr/bin/env python3
"""Export portable full-rate records, derived summaries and synchronized replay data."""
import argparse
import gzip
import json
import posixpath
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from dexlab.libero_workflow import file_hash
from events import events


def write(path, value):
    raw = (
        json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def public_raw(source, target):
    """Redact deployment paths; retain native hashes and label the derived package."""
    target.mkdir(parents=True, exist_ok=False)
    run = json.loads((source / "run.json").read_text())
    for name in (
        "trajectory.npz",
        "contacts.jsonl",
        "parameters-before.json",
        "parameters-effective.json",
        "parameters-after.json",
    ):
        shutil.copyfile(source / name, target / name)
    if (source / "observation-audit.json").exists():
        shutil.copyfile(
            source / "observation-audit.json", target / "observation-audit.json"
        )
    # Change only file locations; preserve every XML physical attribute.
    for name in ("input-model.xml", "relocated-model.xml", "effective-model.xml"):
        tree = ET.fromstring((source / name).read_text())
        for element in tree.findall("./asset/*"):
            original = element.get("file")
            if original is None:
                continue
            parts = Path(original).parts
            if "robosuite" in parts:
                start = max(i for i, value in enumerate(parts) if value == "robosuite")
                prefix, relative = "robosuite", Path(*parts[start + 1 :]).as_posix()
            elif "assets" in parts and any("libero" in part.lower() for part in parts):
                start = max(i for i, value in enumerate(parts) if value == "assets")
                prefix, relative = (
                    "LIBERO/libero/libero/assets",
                    Path(*parts[start + 1 :]).as_posix(),
                )
            else:
                raise ValueError("Unknown asset provider in export")
            relative = posixpath.normpath(relative)
            if relative == ".." or relative.startswith("../"):
                raise ValueError("Asset path escapes its provider")
            element.set("file", prefix + "/" + relative)
        (target / name).write_text(ET.tostring(tree, encoding="unicode") + "\n")
    shutil.copyfile(source / "assets.json", target / "assets.json")
    run["native_run_sha256"] = file_hash(source / "run.json")
    run["native_files_sha256"] = run["files"]
    run["input_sha256"] = [
        dict(path=Path(item["path"]).name, sha256=item["sha256"])
        for item in run["input_sha256"]
    ]
    run["export_note"] = (
        "Derived portable record; input paths redacted; XML paths use portable upstream identifiers and assets come from the pinned official sources. Numerical arrays, contacts and full-precision parameters are byte-identical."
    )
    run["files"] = {p.name: file_hash(p) for p in sorted(target.iterdir())}
    write(target / "run.json", run)


def export(campaign, output):
    import numpy as np
    from dexlab.libero_score import score

    campaign, output = Path(campaign), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((campaign / "manifest.json").read_text())
    selection = json.loads((campaign / "selection.json").read_text())
    write(output / "selection.json", selection)
    manifest["native_manifest_sha256"] = file_hash(campaign / "manifest.json")
    for key in ("libero_root", "dataset", "python", "config_dir", "cache_dir"):
        manifest[key] = Path(manifest[key]).name
    manifest["inputs"] = [
        dict(path=Path(r["path"]).name, sha256=r["sha256"]) for r in manifest["inputs"]
    ]
    if manifest.get("prior_budget"):
        manifest["prior_budget"]["directory"] = Path(
            manifest["prior_budget"]["directory"]
        ).name
    write(output / "manifest.json", manifest)
    summaries = []
    for path in sorted((campaign / "attempts").glob("*/result.json")):
        result = json.loads(path.read_text())
        row = {
            k: result[k] for k in ("candidate", "demo", "split", "outcome", "wall_s")
        }
        row.update(attempt=path.parent.name, native_result_sha256=file_hash(path))
        if result["outcome"] == "recorded":
            raw = path.parent / "raw"
            original_score = score(raw)
            if (
                original_score != result["score"]
                or not original_score["checks"]["source_hashes"]
            ):
                raise ValueError("Original score or hashed evidence changed")
            target = output / "cases" / f"{row['candidate']['id']}-{row['demo']}"
            public_raw(raw, target)
            row["score"] = score(target)
            receipt = json.loads((raw / "run.json").read_text())
            row["native_step_seconds"] = receipt["native_step_seconds"]
            row["duration_s"] = receipt["final_time_s"] - receipt["initial_time_s"]
            row["case_sha256"] = {
                p.name: file_hash(p) for p in sorted(target.iterdir())
            }
            if row["candidate"]["mode"] == "actions" and row["candidate"]["instrument"]:
                row["events"] = events(raw)
                params = json.loads((raw / "parameters-effective.json").read_text())
                contacts = [
                    json.loads(line)
                    for line in (raw / "contacts.jsonl").read_text().splitlines()
                ]
                worst = max(
                    (
                        (c["distance"], frame["time_s"], c)
                        for frame in contacts
                        for c in frame["contacts"]
                    ),
                    key=lambda v: -v[0],
                    default=None,
                )
                if worst:
                    distance, t, c = worst
                    row["max_overlap_event"] = dict(
                        time_s=t,
                        overlap_m=max(0, -distance),
                        geoms=[params["geom_names"][c[k]] for k in ("geom1", "geom2")],
                        solref=c["solref"],
                        effective_timeconst_s=c["effective_timeconst_s"],
                    )
        summaries.append(row)
    parity = {}
    paths = {
        f"{r['candidate']['id']}-{r['demo']}": output
        / "cases"
        / f"{r['candidate']['id']}-{r['demo']}"
        for r in summaries
        if r["outcome"] == "recorded"
    }
    with (
        np.load(paths["baseline-demo_0"] / "trajectory.npz") as on,
        np.load(paths["recording-off-demo_0"] / "trajectory.npz") as off,
    ):
        parity = {
            key: bool(np.array_equal(on[key], off[key]))
            for key in (
                "state",
                "time",
                "initial",
                "actions",
                "success",
                "measurements",
                "controller_targets",
            )
        }
    summary = dict(
        schema_version=1,
        source_manifest_sha256=file_hash(campaign / "manifest.json"),
        selection=selection,
        recording_parity=parity,
        cases=summaries,
        scope="Single task, action replay, fixed seed, split by demonstration. No trained-policy result or material calibration. Coverage unchanged.",
    )
    write(output / "summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.campaign, args.output)
