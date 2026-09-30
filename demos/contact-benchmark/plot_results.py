"""Render development evidence; requires numpy and matplotlib, no native engine."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(evidence, output):
    report_path = evidence / "report.json"
    report = json.loads(report_path.read_text())
    entries = report["results"]
    colors = {"mujoco": "#3266b5", "superdex": "#cf7c20", "physx": "#21856c"}
    labels = {"mujoco": "MuJoCo", "superdex": "SuperDex", "physx": "PhysX"}
    inputs = {}
    fig, axes = plt.subplots(3, 2, figsize=(12, 12), layout="constrained")
    for engine, color in colors.items():
        row = next(
            r for r in entries if r["kind"] == "indent" and r["engine"] == engine
        )
        points = row["current_review"]["metrics"]["plateaus"]
        axes[0, 0].plot(
            [p["mean_signed_indentation_m"] * 1e6 for p in points],
            [p["mean_normal_force_n"] for p in points],
            "o-",
            color=color,
            label=labels[engine],
        )
        row = next(
            r
            for r in entries
            if r["kind"] == "cylinder"
            and r["engine"] == engine
            and r["case"]["mode"] == "hold"
        )
        path = evidence / "raw" / row["run"]
        receipt = json.loads((path / "run.json").read_text())
        states = path / "states.npz"
        checksum = digest(states)
        if (
            checksum != receipt["artifact_sha256"]["states.npz"]
            or digest(path / "run.json") != row["run_sha256"]
        ):
            raise ValueError(f"Modified plot input: {path}")
        inputs[str(states.relative_to(evidence))] = checksum
        with np.load(states, allow_pickle=False) as data:
            times = data["time"]
            reference = data["pose"][round(0.3 / row["case"]["timestep"]), 2, :3]
            drift = np.linalg.norm(data["pose"][:, 2, :3] - reference, axis=1)
            selected = (times >= 0.3) & (times <= 1.5)
            axes[0, 1].plot(
                times[selected],
                drift[selected] * 1000,
                color=color,
                label=labels[engine],
            )
        row = next(
            r
            for r in entries
            if r["kind"] == "cylinder"
            and r["engine"] == engine
            and r["case"]["mode"] == "ramp"
        )
        axes[1, 0].scatter(
            labels[engine],
            row["current_review"]["metrics"]["load_at_vertical_slip_onset_n"],
            s=60,
            color=color,
        )
    for engine in ("mujoco", "superdex"):
        rows = [
            r
            for r in entries
            if r["engine"] == engine
            and r["case"].get("mode") == "overload"
            and r["kind"] in ("cylinder", "timestep-refinement")
        ]
        rows.sort(key=lambda r: r["case"]["timestep"], reverse=True)
        key = (
            "maximum_pad_pad_penetration_m"
            if engine == "mujoco"
            else "maximum_penetration_m"
        )
        label = labels[engine] + (
            " pad / pad" if engine == "mujoco" else " object / pad"
        )
        axes[1, 1].plot(
            [r["case"]["timestep"] * 1000 for r in rows],
            [r["current_review"]["metrics"][key] * 1000 for r in rows],
            "o-",
            color=colors[engine],
            label=label,
        )
    rows = [
        r
        for r in entries
        if r["engine"] == "superdex"
        and r["case"].get("mode") == "overload"
        and r["kind"] in ("cylinder", "surface-refinement")
    ]
    rows.sort(key=lambda r: r["case"].get("surface_subdivisions", 0))
    triangles = [
        4 * r["case"]["sections"] * 4 ** r["case"].get("surface_subdivisions", 0)
        for r in rows
    ]
    for column, key, scale in [
        (0, "maximum_penetration_m", 1000),
        (1, "maximum_momentum_residual_weight_ratio", 1),
    ]:
        axes[2, column].plot(
            triangles,
            [r["current_review"]["metrics"][key] * scale for r in rows],
            "o-",
            color=colors["superdex"],
        )
        axes[2, column].set_xscale("log", base=4)
        axes[2, column].set_xticks([256, 1024, 4096], ["256", "1,024", "4,096"])
        axes[2, column].set_xlabel("Source surface triangles (same prism)")
    axes[0, 0].set(
        title="A  Normal response: two measured dwell levels",
        xlabel="Signed geometric indentation (micrometres)",
        ylabel="Normal force (N)",
    )
    axes[0, 0].axvline(0, color="#777777", lw=0.8, ls=":")
    axes[0, 0].legend()
    axes[0, 0].text(
        0.98,
        0.96,
        "Negative indentation = gap\nContact offsets are included",
        transform=axes[0, 0].transAxes,
        ha="right",
        va="top",
        fontsize=9,
    )
    axes[0, 1].set(
        title="B  0.2 kg hold: actual object drift",
        xlabel="Time (s)",
        ylabel="Displacement from t = 0.3 s (mm)",
        xlim=(0.3, 1.5),
        ylim=(0, 1.3),
    )
    axes[0, 1].axhline(1, color="#b22222", ls="--", label="1 mm limit")
    axes[0, 1].legend(fontsize=9)
    axes[1, 0].axhline(2.4, color="#777777", ls="--", label="Nominal Coulomb capacity")
    axes[1, 0].set(
        title="C  Load ramp: downward-motion onset",
        ylabel="Weight + added downward load (N)",
        ylim=(2.35, 2.63),
    )
    axes[1, 0].legend(loc="upper left", fontsize=9)
    axes[1, 0].text(
        0.03,
        0.07,
        "COM downward speed > 5 mm/s for 20 ms\nOnset only; later failures remain in the report",
        transform=axes[1, 0].transAxes,
        fontsize=9,
    )
    axes[1, 1].axhline(1, color="#b22222", ls="--", label="1 mm limit")
    axes[1, 1].set(
        title="D  Overload: timestep refinement",
        xlabel="Physics timestep (ms)",
        ylabel="Peak reference penetration (mm)",
        xticks=[0.125, 0.25, 0.5],
        ylim=(0, 3.6),
    )
    axes[1, 1].invert_xaxis()
    axes[1, 1].legend(fontsize=9, loc="lower left")
    axes[2, 0].set(
        title="E  SuperDex overload: surface refinement",
        ylabel="Peak reference penetration (mm)",
        ylim=(0, 2.6),
    )
    axes[2, 0].axhline(1, color="#b22222", ls="--", label="1 mm limit")
    axes[2, 0].legend(fontsize=9)
    axes[2, 1].set(
        title="F  SuperDex overload: momentum residual",
        ylabel="Peak residual / object weight",
        yscale="log",
        ylim=(0.0003, 15),
    )
    axes[2, 1].axhline(0.05, color="#b22222", ls="--", label="0.05 weight limit")
    axes[2, 1].legend(fontsize=9)
    for axis in axes.flat:
        axis.grid(alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "DexLab contact development — uncalibrated profiles",
        fontsize=16,
        fontweight="bold",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "report_sha256": digest(report_path),
                "script_sha256": digest(Path(__file__)),
                "image_sha256": digest(output),
                "input_state_sha256": inputs,
                "scope": "Development observations; no held-out, hardware or isolated speed ranking",
            },
            indent=2,
        )
        + "\n"
    )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "evidence", type=Path, help="Extracted archive containing report.json and raw/"
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    plot(arguments.evidence, arguments.output)
