#!/usr/bin/env python3
"""Plot complete recorded wiping trajectories, including unsuccessful takes."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    figure, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
    colors = {"original": "#1764ab", "no-latch": "#d85a25"}
    for folder in args.runs:
        summary = json.loads((folder / "summary.json").read_text())
        rows = [json.loads(line) for line in (folder / "observations.jsonl").read_text().splitlines()]
        times = [row["sim_time_s"] for row in rows]
        mode = summary["mode"]
        color = colors[mode]
        label = f"{mode}: {folder.name}"
        axes[0].plot(times, [100 * r["cleaned_fraction"] for r in rows], color=color, label=label, alpha=0.8)
        # Opening deliberately releases the object; it is outside the holding metric.
        slip = [1000 * r["patch_centroid_slip_m"]
                if r["patch_centroid_slip_m"] is not None and r["grip_command"] >= 0.5
                else np.nan for r in rows]
        axes[1].plot(times, slip, color=color, alpha=0.8)
        axes[2].plot(times, [r["bar_force_n"] for r in rows], color=color, alpha=0.65)
    axes[0].axhline(90, color="#777777", linestyle="--", linewidth=1, label="upstream task threshold")
    axes[0].set_ylabel("Cleaned stripe (%)")
    axes[0].set_ylim(-2, 103)
    axes[0].legend(fontsize=8, loc="lower right")
    axes[1].axhline(10, color="#777777", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Patch centroid slip (mm)")
    axes[2].set_ylabel("Bar contact force (N)")
    axes[2].set_xlabel("Simulation time (s)")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.suptitle("RSS sponge wiping: original assistance and no-latch comparison")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
