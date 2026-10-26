"""Rescore one saved attempt and plot its measured motion, force and torque."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from score import evaluate


def make_report(directory, output):
    """Validate the complete raw record before creating an independent report."""
    directory, output = Path(directory), Path(output)
    if output.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Write reports outside the immutable input attempt")
    report = evaluate(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    with np.load(directory / "observations.npz", allow_pickle=False) as archive:
        raw = dict(archive)
    config, effective = manifest["config"], manifest["effective"]
    time = raw["time_s"]
    anchor_index = round(config["support_end_s"] / effective["timestep"])
    anchor = raw["qpos_before"][anchor_index, 20:23]
    displacement_mm = 1000 * np.linalg.norm(raw["qpos_after"][:, 20:23] - anchor, axis=1)
    speed_mm_s = 1000 * np.linalg.norm(raw["qvel_after"][:, 20:23], axis=1)
    torque_ratio = np.max(np.abs(raw["actuator_force"]) / effective["actuator_force_limits"], axis=1)
    contact_z = raw["object_contact_force"][:, 2]
    weight = -effective["object_mass"] * effective["gravity"][2]
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    with (output / "measurements.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "displacement_mm", "speed_mm_s", "contact_z_n", "max_torque_fraction"])
        writer.writerows(zip(time, displacement_mm, speed_mm_s, contact_z, torque_ratio, strict=True))

    figure, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    curves = [displacement_mm, speed_mm_s, contact_z, torque_ratio]
    labels = ["Displacement from support removal (mm)", "Object speed (mm/s)",
              "Measured upward contact force (N)", "Largest actual torque / source limit"]
    limits = [1000 * config["hold_max_displacement_m"],
              1000 * config["hold_max_speed_m_s"], weight, 1.]
    for axis, curve, label, limit in zip(axes.flat, curves, labels, limits, strict=True):
        axis.plot(time, curve, color="#216e8e", linewidth=1)
        axis.axhline(limit, color="#b44838", linestyle="--", linewidth=1,
                     label="Weight" if label.endswith("(N)") else "Hold criterion / effort cap")
        axis.axvspan(config["hold_start_s"], config["action_start_s"], color="#d8e8dd", alpha=.55,
                     label="Scored hold")
        axis.axvline(config["support_end_s"], color="#666666", linestyle=":", linewidth=1)
        axis.set(xlabel="Simulation time (s)", ylabel=label, xlim=(0, config["duration_s"]))
        axis.grid(alpha=.2)
    # Full free fall remains visible without hiding the millimetre-scale hold.
    axes[0, 0].set_yscale("symlog", linthresh=3)
    axes[0, 1].set_yscale("symlog", linthresh=50)
    axes[0, 0].legend(fontsize=8)
    figure.suptitle(f"{manifest['config'].get('cohort', 'v1')} | {manifest['case']} | "
                   f"hold: {'PASS' if report['hold_pass'] else 'FAIL'}")
    figure.savefig(output / "measurements.png", dpi=150)
    plt.close(figure)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(make_report(args.directory, args.output), indent=2))


if __name__ == "__main__":
    main()
