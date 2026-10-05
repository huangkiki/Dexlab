"""Independently rescore the complete frozen friction campaign and plot results."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.contact_friction import diagnose
from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import verify
from dexlab.physx_baseline import digest


def report(directory):
    batch = json.loads((directory / "batch.json").read_text())
    suite = batch["suite"]
    if batch["status"] != "completed" or not batch["source_unchanged"]:
        raise ValueError("Incomplete or changed-source campaign")
    expected = [f"{engine}-{case['name']}" for case in suite["cases"] for engine in suite["engines"]]
    if [row["id"] for row in batch["runs"]] != expected or len(expected) != suite["max_runs"]:
        raise ValueError("Missing, duplicated or reordered cases")
    for name, sha in batch["source_sha256"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid source snapshot path")
        if digest(directory / "source" / relative) != sha:
            raise ValueError("Changed source snapshot")
    rows = []
    for declared, row in zip(
        (suite["defaults"] | case for case in suite["cases"] for _ in suite["engines"]),
        batch["runs"], strict=True,
    ):
        path = directory / row["id"]
        receipt = json.loads((path / "run.json").read_text())
        if row["case"] != declared or receipt["case"] != declared or receipt["engine"] != row["engine"]:
            raise ValueError("Runtime case differs from frozen matrix")
        rescored = verify(path)
        if rescored != row["summary"]:
            raise ValueError("Independent score differs from recorded outcome")
        with np.load(path / "states.npz", allow_pickle=False) as saved:
            data = dict(saved)
        diagnostic = diagnose(PlaneCase(**declared), data)
        rows.append({
            "id": row["id"], "engine": row["engine"], "case": declared,
            "acceptance": rescored, "diagnostic": diagnostic,
            "initial_pose_wxyz": data["pose"][0].tolist(),
            "initial_velocity_world": data["velocity"][0].tolist(),
            "native": receipt["native"],
            "cost_s": {"process": row["process_wall_s"],
                       "preparation": receipt["preparation_seconds"],
                       "step_and_observation": receipt["step_and_observation_seconds"],
                       "total_run": receipt["total_seconds"]},
            "raw_sha256": {"states.npz": digest(path / "states.npz"),
                           "run.json": digest(path / "run.json"),
                           receipt["contact_archive"]: digest(path / receipt["contact_archive"])},
        })
    return {"scope": suite["scope"], "suite": suite,
            "batch_sha256": digest(directory / "batch.json"),
            "source_sha256": batch["source_sha256"],
            "completed": len(rows), "passed": sum(r["acceptance"]["passed"] for r in rows),
            "batch_wall_s": batch["total_wall_s"], "rows": rows}


def plot(result, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    colors = {"mujoco": "#2471a3", "superdex": "#d35400"}
    for row in result["rows"]:
        if row["case"]["name"] not in ("dev-friction-forward", "dev-friction-slow"):
            continue
        bins = [b for b in row["diagnostic"]["bins"] if b["count"]]
        x = [np.sqrt(b["speed_lower_m_s"] * b["speed_upper_m_s"]) for b in bins]
        y = [b["resisting_force_ratio_median"] for b in bins]
        slow = row["case"]["initial_speed"] < 0.01
        axes[0].plot(x, y, marker="s" if slow else "o", linestyle="--" if slow else "-",
                     color=colors[row["engine"]], label=row["engine"] + (" slow" if slow else " forward"))
    axes[0].axhline(0.3, color="gray", linestyle=":", label="nominal coefficient")
    axes[0].set(xscale="log", xlabel="COM speed bin geometric center (m/s)", ylabel="Signed resisting force / normal force", title="Force response; bins omit rest/crossings")
    axes[0].legend(fontsize=8)
    labels = [c["name"].removeprefix("dev-friction-") for c in result["suite"]["cases"]]
    for engine, offset in (("mujoco", -0.17), ("superdex", 0.17)):
        rows = [r for r in result["rows"] if r["engine"] == engine]
        axes[1].bar(np.arange(len(rows)) + offset,
                    [r["acceptance"]["metrics"]["maximum_velocity_reference_error_m_s"] * 1000 for r in rows],
                    width=0.34, color=colors[engine], label=engine)
    axes[1].set(xticks=np.arange(len(labels)), xticklabels=labels, ylabel="Maximum velocity-reference error (mm/s)", title="All 16 outcomes; no cases omitted")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].legend(fontsize=8)
    fig.savefig(output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    result = report(args.directory.resolve())
    # Refuse overwriting reports: failed/earlier analyses remain available.
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    if args.plot:
        if args.plot.exists():
            raise FileExistsError(args.plot)
        plot(result, args.plot)
    print(json.dumps({"completed": result["completed"], "passed": result["passed"]}))
