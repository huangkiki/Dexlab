"""Plot every enabled-limit upper-target trace. Requires matplotlib."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dexlab.genesis_joint_score import score

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("directory", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
if args.output.exists():
    parser.error("Choose a new output path")
score(args.directory)  # Reject incomplete or incompatible records before plotting.
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
for ax, profile in zip(axes, ("as_imported", "zero")):
    for response, color in (("default", "#c04c35"), ("explicit004", "#236ca2")):
        record = json.loads((args.directory / f"{profile}-{response}-True-0.1.json").read_text())
        rows = record["samples"]
        ax.plot([r["step"] * .002 for r in rows],
                [max(r["q_m"] - .05, 0) * 1000 for r in rows], color=color,
                label="10 ms default" if response == "default" else "4 ms explicit")
    ax.axhline(1, color="#555555", linestyle="--", label="1 mm engineering limit")
    ax.set(xlabel="Time after command (s)", ylabel="Upper-limit violation (mm)",
           title="Imported armature: 0.1 kg" if profile == "as_imported" else "Explicit zero armature",
           ylim=(0, 2.1), xlim=(0, 1))
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
fig.suptitle("Genesis 1.4.3 | measured joint position, same 2 ms step and PD gains", fontsize=11)
fig.savefig(args.output, dpi=160)
plt.close(fig)
