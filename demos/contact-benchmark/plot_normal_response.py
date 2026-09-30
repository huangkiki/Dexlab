"""Regenerate the normal-response figure from the complete public report."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot(report_path, output):
    report = json.loads(report_path.read_text())
    rows = {r["id"]: r for r in report["results"]}
    colors = {"mujoco": "#2674b8", "superdex": "#ce7725", "physx": "#208765"}
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 4.4), layout="constrained")
    loads = np.array([0, 2, 4, 6])
    axes[0].plot(loads / 20000 * 1000, loads, "k--", label="Declared 20 kN/m target")
    for engine, color in colors.items():
        ref = rows[f"validation-{engine}-reference"]["result"]["metrics"]
        pts = ref["plateaus"][:3]
        axes[0].plot(
            [p["indentation_mean_m"] * 1000 for p in pts],
            [p["load_n"] for p in pts],
            ".-",
            color=color,
            label=engine,
        )
        values = [
            rows[f"validation-{engine}-{label}"]["result"]["metrics"][
                "fit_secant_stiffness_n_m"
            ]
            / 1000
            for label in ("mass01", "reference", "mass04")
        ]
        axes[1].plot(
            [0.1, 0.2, 0.4], values, "o-", color=color, label=engine + " fixed native"
        )
    converted = [
        rows[f"validation-mujoco-mass{m}-converted"]["result"]["metrics"][
            "fit_secant_stiffness_n_m"
        ]
        / 1000
        for m in (0.1, 0.4)
    ]
    axes[1].plot(
        [0.1, 0.4],
        converted,
        "x--",
        color=colors["mujoco"],
        label="mujoco mass conversion",
    )
    axes[1].axhspan(19, 21, color="grey", alpha=0.15, label="Target ±5%")
    for i, (engine, color) in enumerate(colors.items()):
        jitter = [
            max(
                p["indentation_std_m"]
                for p in rows[f"validation-{engine}-{label}"]["result"]["metrics"][
                    "plateaus"
                ][:3]
            )
            * 1e6
            for label in ("reference", "mass01", "mass04", "h2")
        ]
        axes[2].bar(
            np.arange(4) + (i - 1) * 0.24, jitter, 0.23, color=color, label=engine
        )
    axes[2].axhline(5, color="black", linestyle="--", label="5 μm limit")
    axes[2].set_xticks(range(4), ["0.2 kg", "0.1 kg", "0.4 kg", "h/2"])
    axes[0].set(
        xlabel="Mean geometric indentation (mm)",
        ylabel="Downward load (N)",
        title="Reference case after fitting",
    )
    axes[1].set(
        xlabel="Mass (kg)",
        ylabel="2–6 N secant (kN/m)",
        title="Frozen-profile mass transfer",
        xticks=[0.1, 0.2, 0.4],
    )
    axes[2].set(
        ylabel="Maximum plateau standard deviation (μm)",
        title="Static matching does not imply settling",
    )
    for ax in axes:
        ax.grid(alpha=0.2, axis="y")
        ax.legend(fontsize=7, loc="best")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "Normal contact response · development evidence · 17 completed / 11 pass / 6 fail",
        fontsize=12,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    plot(a.report, a.output)
