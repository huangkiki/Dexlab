"""Plot all three frozen XPBD episodes, including the unsupported negative."""

import argparse
import gzip
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dexlab.newton_contact_score import score

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("record", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new output path")
with gzip.open(args.record, "rt") as stream:
    record = json.load(stream)
if not score(record)["valid"]:
    raise ValueError("Incomplete or incompatible records")
fig, axes = plt.subplots(2, 2, figsize=(10, 6), layout="constrained")
for episode, color in zip(record["episodes"], ("#236ca2", "#228860", "#c04c35")):
    rows = episode["rows"]
    times = [row["step"] * 0.001 for row in rows]
    negative = episode["case"] == "collision-disabled"
    axis = axes[0, 1] if negative else axes[0, 0]
    axis.plot(
        times,
        [row["q"][2] * 1000 for row in rows],
        color=color,
        linestyle="--" if episode["case"] == "support-repeat" else "-",
        label=episode["case"],
    )
    if not negative:
        forces = [
            sum(
                force[2] * (1 if episode["shape_body"][s0] == 0 else -1)
                for s0, force in zip(row["shape0"], row["force"])
            )
            for row in rows
        ]
        for axis in axes[1]:
            axis.plot(
                times,
                forces,
                color=color,
                linestyle="--" if episode["case"] == "support-repeat" else "-",
                label=episode["case"],
            )
axes[0, 1].plot(
    times,
    [(0.1 - 9.81 * 0.001**2 * n * (n + 1) / 2) * 1000 for n in range(1, 1001)],
    color="#555555",
    linestyle=":",
    label="Discrete free-fall reference",
)
for axis in axes[0]:
    axis.set(xlabel="Time (s)", ylabel="Sphere center height (mm)")
    axis.axhline(50, color="#999999", linestyle=":", label="Touch height")
for axis in axes[1]:
    axis.set(xlabel="Time (s)", ylabel="Signed upward contact force (N)")
    axis.axhline(0.981, color="#999999", linestyle=":", label="mg = 0.981 N")
axes[1, 1].set(xlim=(0.75, 1), ylim=(0.92, 1.04))
axes[0, 0].set_title("Supported drop and rebuild repeat")
axes[0, 1].set_title("Collision-disabled negative: support fails")
axes[1, 0].set_title("Full impact retained")
axes[1, 1].set_title("Hold window: force is near mg")
for axis in axes.flat:
    axis.grid(alpha=0.2)
    axis.legend(fontsize=7)
fig.suptitle(
    "Newton 1.6.1 XPBD / Warp 1.18.0 | CPU FP32 | synthetic primitive admission",
    fontsize=11,
)
fig.savefig(args.output, dpi=160)
plt.close(fig)
