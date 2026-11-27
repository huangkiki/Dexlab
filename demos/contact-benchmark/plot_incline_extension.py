"""Overlay new 1 ms traces on the six published incline curves."""

import argparse
import json
from pathlib import Path

import numpy as np

from export_visual_research import ROOT, channel, plot
from score_incline_extension import axes, read_case
from visual_research import read_bundle


def plotted_series(root, engine, label, protocol, case):
    results = json.loads((root / f"{engine}-results.json").read_text())["cases"]
    score = next(row for row in results if row["id"] == case["id"])
    trace = read_case(engine, protocol, case, root / engine / case["id"])
    states = trace["states"]
    time, positions = states[:, 0], states[:, 1:4]
    tangent, normal, _ = axes(case["angle_deg"])
    channels = [
        channel("displacement", "m", time, (positions - positions[0]) @ tangent),
        channel("velocity", "m/s", time, states[:, 8:11] @ tangent),
        channel("support", "N", trace["force_times"], trace["forces"] @ normal,
                "Native mean force over each completed interval, plotted at its start"),
        channel("overlap", "mm", time[1:], np.maximum(0, -trace["contact_distance"]) * 1000),
    ]
    return {"engine": label, "id": "", "valid": score["status"] != "invalid", "channels": channels}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="Extracted native evidence archive")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((args.records / "manifest.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for case in protocol["cases"]:
        if case["timestep"] != .001 or case.get("negative_no_floor"):
            continue
        regime = case["regime"]
        original = ROOT / f"docs/evidence/visual/incline-{regime}-0.001.json.gz"
        bundle = read_bundle(original)
        for engine, label in (("chaos", "Chaos"), ("bullet", "Bullet"), ("sofa", "SOFA")):
            bundle["series"].append(plotted_series(args.records, engine, label, protocol, case))
        for language in ("en", "zh"):
            stem = f"{regime}-1ms"
            plot(bundle, stem, language, output=args.output, formats=("svg",))
            suffix = ".zh.svg" if language == "zh" else ".svg"
            path = args.output / f"{stem}-curves{suffix}"
            path.write_text("".join(line.rstrip() + "\n" for line in path.read_text().splitlines()))


if __name__ == "__main__":
    main()
