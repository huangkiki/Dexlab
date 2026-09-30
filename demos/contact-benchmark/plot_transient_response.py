"""Plot unfiltered archived motion and fixed-window transient errors."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from dexlab.contact_transient import reference


def plot(root, output):
    report = json.loads((root / "report.json").read_text())
    rows = {row["id"]: row for row in report["results"]}
    profiles = {
        "mujoco-imp09": ("MuJoCo d=0.9", "#759cbf", ":"),
        "mujoco-imp0001": ("MuJoCo d=0.001", "#185b9b", "-"),
        "superdex-load-damping": ("SuperDex load-dependent damping", "#bc621e", "-"),
        "physx-force-spring": ("PhysX force spring", "#19845b", "-"),
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for index, ax in enumerate(axes.flat[:3]):
        onset = index * 0.2
        t = np.linspace(onset, onset + 0.05, 501)
        ax.plot((t - onset) * 1000, reference(t, 0.2) * 1e6,
                "k--", label="Synthetic K=20 kN/m, D=40 N s/m")
        for name, (label, color, style) in profiles.items():
            with np.load(root / "raw" / f"{name}-125us" / "states.npz") as data:
                mask = (data["time"] >= onset) & (data["time"] <= onset + 0.05)
                ax.plot((data["time"][mask] - onset) * 1000,
                        (0.02 - data["pose"][mask, 2]) * 1e6,
                        color=color, linestyle=style, label=label)
        ax.set(title=f"{2 * (index + 1)} N stage · h = 0.125 ms",
               xlabel="Time since load step (ms)", ylabel="COM indentation (μm)")
    ax = axes[1, 1]
    for name, (label, color, style) in profiles.items():
        errors = [max(w["rms_error_m"] for w in
                      rows[f"{name}-{h}us"]["transient"]["metrics"]["windows"])
                  * 1e6 for h in (125, 250, 500)]
        ax.plot([0.125, 0.25, 0.5], errors, "o", color=color, linestyle=style, label=label)
    ax.axhline(10, color="black", linestyle="--", label="10 μm RMS limit")
    ax.set(xlabel="Physics step (ms)", ylabel="Worst 50 ms RMS error (μm)",
           title="Fixed native parameters · step refinement", yscale="log",
           xticks=[0.125, 0.25, 0.5])
    for ax in axes.flat:
        ax.grid(alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, fontsize=9)
    fig.suptitle("Contact transients · declared development candidates · all failures retained")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plot(args.directory, args.output)
