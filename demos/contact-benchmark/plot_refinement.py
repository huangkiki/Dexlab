"""Plot archived adjacent-grid differences without declaring accuracy rankings."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if report["comparable_pairs"] != report["expected_pairs"]:
        parser.error("Incomplete comparisons cannot produce this complete-cohort plot")
    figure, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    metrics = (("maximum_position_m", "mm"), ("maximum_linear_velocity_m_s", "mm/s"))
    for column, control in enumerate(("forward", "frictionless")):
        for engine, color in (("mujoco", "#1565c0"), ("superdex", "#e65100")):
            rows = [row for row in report["pairs"]
                    if row["engine"] == engine and row["control"] == control]
            timesteps = [row["metrics"]["coarse_timestep_s"] * 1000 for row in rows]
            for index, (key, unit) in enumerate(metrics):
                values = [row["metrics"][key] * 1000 for row in rows]
                if any(value <= 0 for value in values):
                    parser.error("Logarithmic plot requires positive differences")
                axis = axes[index, column]
                axis.plot(timesteps, values, "o-", color=color, label=engine)
                axis.set(xscale="log", yscale="log", xlabel="Coarse timestep (ms)",
                         ylabel=f"Max adjacent-grid difference ({unit})")
                axis.set_xlim(1.1, .22)
                axis.set_xticks([1, .5, .25], ["1 → 0.5", "0.5 → 0.25", "0.25 → 0.125"])
                axis.set_xticks([], minor=True)
                axis.grid(alpha=.2)
        axes[0, column].set_title(control + " contact onset")
        for index in range(2):
            axes[index, column].legend()
    figure.suptitle(
        "Fresh-scene timestep sensitivity — not physical accuracy\n"
        "Shared times only; no interpolation. SuperDex forward: 4/4 engineering failures.",
        fontsize=12,
    )
    figure.savefig(args.output, dpi=160)
    plt.close(figure)
    print(args.output.name)


if __name__ == "__main__":
    main()
