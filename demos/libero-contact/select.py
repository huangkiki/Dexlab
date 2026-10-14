#!/usr/bin/env python3
"""Freeze the development-only challenger before any heldout execution."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from dexlab.libero_workflow import file_hash
from dexlab.migration_budget import json_bytes, publish


def select(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    rows = [
        json.loads(p.read_text()) | {"result_path": p}
        for p in sorted((root / "attempts").glob("*/result.json"))
    ]
    if any(row["split"] == "heldout" for row in rows):
        raise ValueError("Cannot select after viewing heldout outcomes")
    candidates = []
    sources = {}
    for candidate in manifest["candidates"]:
        if candidate["mode"] != "actions" or not candidate["instrument"]:
            continue
        trials = [
            r
            for r in rows
            if r["candidate"]["id"] == candidate["id"] and r["outcome"] == "recorded"
        ]
        if sorted(r["demo"] for r in trials) != sorted(manifest["development"]):
            raise ValueError(
                "Every development case must be recorded exactly once before selection"
            )
        for row in trials:
            sources[str(row["result_path"].relative_to(root))] = file_hash(
                row["result_path"]
            )
        candidates.append(
            dict(
                id=candidate["id"],
                valid=all(r["score"]["observation_valid"] for r in trials),
                task_pass=all(r["score"]["native_success_final"] for r in trials),
                screen_pass=all(
                    r["score"]["physical_acceptance"] == "diagnostic-pass"
                    for r in trials
                ),
                max_overlap_m=max(
                    r["score"]["physics"]["max_overlap_m"] for r in trials
                ),
                native_seconds=sum(
                    json.loads((r["result_path"].parent / "raw/run.json").read_text())[
                        "native_step_seconds"
                    ]
                    for r in trials
                ),
            )
        )
    eligible = [
        r for r in candidates if r["id"] != "baseline" and r["valid"] and r["task_pass"]
    ]
    if not eligible:
        raise ValueError(
            "No valid task-preserving challenger; retain failures and diagnose before another package"
        )
    best = min(
        eligible,
        key=lambda r: (not r["screen_pass"], r["max_overlap_m"], r["native_seconds"]),
    )
    selection = dict(
        candidate=best["id"],
        diagnostic_qualified=best["screen_pass"],
        recommendation=False,
        reason="Heldout validation is still required; an unqualified challenger is a sensitivity comparison only.",
        manifest_sha256=file_hash(root / "manifest.json"),
        development=candidates,
        sources=sources,
    )
    publish(root / "selection.json", json_bytes(selection))
    return selection


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    print(json.dumps(select(parser.parse_args().root), indent=2))
