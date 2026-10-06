"""Recompute every native tangent case and plot both solver batches."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from dexlab.contact_tangent import LOADS, TIMESTEPS
from dexlab.contact_tangent_verify import verify
from dexlab.physx_baseline import digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("default", type=Path)
    parser.add_argument("tight", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for dt in TIMESTEPS:
        for load in LOADS:
            name = f"load-{load:g}-dt-{round(dt * 1e6)}us"
            pair = []
            for batch, root, tolerance in [
                ("default", args.default, (1e-3, 1e-6)),
                ("tight", args.tight, (1e-9, 1e-9)),
            ]:
                directory = root / name
                result = verify(directory)
                original = json.loads((directory / "score.json").read_text())
                if result != original:
                    raise ValueError(
                        "Current independent scoring differs from frozen scoring"
                    )
                native = json.loads((directory / "native.json").read_text())
                normalized = deepcopy(native)
                solver = normalized["solver"]
                if (
                    solver.pop("absolute_tolerance"),
                    solver.pop("relative_tolerance"),
                ) != tolerance:
                    raise ValueError("Unregistered solver tolerance")
                with np.load(directory / "states.npz", allow_pickle=False) as data:
                    initial = np.r_[data["pose"][0], data["velocity"][0]]
                    command = data["load"].copy()
                pair.append(
                    (
                        normalized,
                        initial,
                        command,
                        digest(directory / "geometry-readback.json"),
                    )
                )
                rows.append(
                    {
                        "batch": batch,
                        "id": name,
                        "load_n": load,
                        "timestep_s": dt,
                        "result": result,
                        "receipt": json.loads((directory / "receipt.json").read_text()),
                    }
                )
            if (
                pair[0][0] != pair[1][0]
                or pair[0][3] != pair[1][3]
                or not np.array_equal(pair[0][1], pair[1][1])
                or not np.array_equal(pair[0][2], pair[1][2])
            ):
                raise ValueError(
                    "Paired native parameters, geometry or initial/control states changed"
                )
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output / "tangent-identification-v1.json",
        {
            "scope": "Synthetic local response; paired solver tolerances; no hardware or engine ranking",
            "raw_contact_rescore": True,
            "native_pair_readback": True,
            "cases": rows,
        },
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    colors = ["#0072B2", "#D55E00", "#009E73"]
    for dt, color in zip(TIMESTEPS, colors, strict=True):
        selected = [
            row for row in rows if row["batch"] == "tight" and row["timestep_s"] == dt
        ]
        for epoch, style in [("post_step", "-o"), ("pre_step", "--x")]:
            axes[0].plot(
                LOADS,
                [
                    row["result"]["epochs"][epoch]["fit"]["damping_ns_m"]
                    for row in selected
                ],
                style,
                color=color,
                label=f"{dt * 1e3:g} ms, {epoch.replace('_step', '')}",
            )
    axes[0].plot(
        LOADS, np.asarray(LOADS) * 10, ":", color="black", label="Conditional cL"
    )
    axes[0].set(
        xlabel="Preload (N)",
        ylabel="Fitted damping (Ns/m)",
        title="Tighter solver: state/force epoch matters",
    )
    axes[0].legend(fontsize=8, ncol=2)
    for batch, color in [("default", "#D55E00"), ("tight", "#0072B2")]:
        selected = [row for row in rows if row["batch"] == batch]
        axes[1].semilogy(
            range(9),
            [row["result"]["momentum_peak_n"] for row in selected],
            "o-",
            color=color,
            label=batch,
        )
    axes[1].axhline(1e-5, color="black", linestyle=":", label="Frozen validity limit")
    axes[1].set(
        xlabel="Case (step descending, load ascending)",
        ylabel="Peak momentum residual (N)",
        title="All 18 runs retained",
    )
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig(args.output / "tangent-identification-v1.png", dpi=180)
    plt.close(fig)
    print(
        json.dumps(
            {"cases": len(rows), "valid": sum(row["result"]["valid"] for row in rows)}
        )
    )


if __name__ == "__main__":
    main()
