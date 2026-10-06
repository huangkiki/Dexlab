"""Independently rescore all 18 cases; never graph rejected fits as material data."""

import argparse
from pathlib import Path

from dexlab.contact_feedthrough import PROFILES, verify
from dexlab.contact_tangent import LOADS, TIMESTEPS
from dexlab.physx_baseline import digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for profile in PROFILES:
        for dt in TIMESTEPS:
            for load in LOADS:
                name = f"{profile}-load-{load:g}-dt-{round(dt * 1e6)}us"
                directory = args.records / name
                rows.append(
                    {
                        "id": name,
                        "profile": profile,
                        "load_n": load,
                        "timestep_s": dt,
                        "result": verify(directory),
                        "receipt_sha256": digest(directory / "receipt.json"),
                    }
                )
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output / "feedthrough-v1.json",
        {
            "scope": "Synthetic local response, no hardware calibration",
            "raw_contact_rescore": True,
            "cases": rows,
        },
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
    axes[0].bar(
        ["High impedance", "Low impedance"],
        [
            sum(r["result"]["valid"] for r in rows if r["profile"] == p)
            for p in PROFILES
        ],
        color=["#999999", "#0072B2"],
    )
    axes[0].set(
        ylim=(0, 10), ylabel="Valid cases / 9", title="Data validity before fitting"
    )
    axes[0].text(
        0,
        1,
        f"{sum(not r['result']['valid'] for r in rows if r['profile'] == 'high')} invalid\n(all retained)",
        ha="center",
    )
    accepted = [row for row in rows if row["result"]["valid"]]
    for name, label, color in [
        ("pre-basic", "State only", "#D55E00"),
        ("pre-load", "State + applied load", "#0072B2"),
    ]:
        values = [
            r["result"]["models"][name]["prediction_rms_n"] / (0.01 * r["load_n"])
            for r in accepted
        ]
        axes[1].scatter(range(len(values)), values, label=label, color=color, s=18)
    axes[1].axhline(0.05, color="black", ls="--", lw=1, label="Frozen limit")
    axes[1].set(
        yscale="log",
        xlabel="Accepted low-impedance case",
        ylabel="Prediction RMS / tone amplitude",
        title="Smaller-amplitude prediction",
    )
    axes[1].legend(fontsize=7)
    for epoch, marker in [("pre", "o"), ("post", "x")]:
        for load in LOADS:
            selected = [r for r in accepted if r["load_n"] == load]
            axes[2].plot(
                [r["timestep_s"] * 1000 for r in selected],
                [
                    r["result"]["models"][epoch + "-load"]["fit"]["damping_ns_m"]
                    for r in selected
                ],
                marker=marker,
                label=f"{epoch}, {load:g}N",
                lw=0.8,
            )
    axes[2].axhline(40, color="black", ls="--", lw=1)
    axes[2].set(
        xlabel="Step (ms)",
        ylabel="Identified D (Ns/m)",
        title="Epoch diagnostic (low only)",
    )
    axes[2].legend(fontsize=7, ncol=2)
    fig.savefig(args.output / "feedthrough-v1.png", dpi=160)
    plt.close(fig)
    write_json(
        args.output / "feedthrough-v1.provenance.json",
        {
            "report_sha256": digest(args.output / "feedthrough-v1.json"),
            "figure_sha256": digest(args.output / "feedthrough-v1.png"),
            "script_sha256": digest(Path(__file__)),
            "counts": {"all": 18, "valid": sum(r["result"]["valid"] for r in rows)},
            "scope": "All cases rescored; rejected coefficients omitted from accepted-material plots",
        },
    )


if __name__ == "__main__":
    main()
