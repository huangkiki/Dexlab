"""Run and independently rescore the frozen cloth experiments."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from dexlab.cloth import ClothCase, score_record

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks/cloth-v1.json"
SOLVERS = (
    "mujoco",
    "superdex-shell",
    "newton-xpbd",
    "newton-vbd",
    "newton-semi_implicit",
    "newton-featherstone",
    "newton-style3d",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def batch(args):
    """Freeze one matrix before launching isolated episodes; retain every failure."""
    suites = [path.resolve() for path in args.suite]
    entries = [
        (path, entry["case"]["name"])
        for path in suites
        for entry in json.loads(path.read_text())["cases"]
        if entry["split"] == args.split
    ]
    names = [name for _, name in entries]
    if not names or len(names) != len(set(names)):
        raise ValueError("Batch requires nonempty, uniquely named cases")
    if args.timeout <= 0:
        raise ValueError("Episode timeout must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    frozen = source_identity()
    suite_hashes = {str(path): digest(path) for path in suites}
    report = {
        "status": "running",
        "split": args.split,
        "source_sha256": frozen,
        "suite_sha256": suite_hashes,
        "configuration": {
            "dt_s": args.dt,
            "iterations": args.iterations,
            "device": args.device,
            "timeout_s": args.timeout,
            "material": "nominal native profiles; no cross-solver calibration",
        },
        "jobs": [
            {"solver": solver, "case": name, "suite": str(path), "status": "queued"}
            for path, name in entries
            for solver in args.solver
        ],
    }
    report_path = args.output / "batch.json"
    write_json(report_path, report)
    for number, job in enumerate(report["jobs"], 1):
        if frozen != source_identity() or any(
            digest(Path(path)) != value for path, value in suite_hashes.items()
        ):
            report["status"] = "source_or_suite_changed"
            write_json(report_path, report)
            raise RuntimeError("Frozen batch inputs changed; remaining cases not run")
        output = args.output / f"{job['case']}-{job['solver']}"
        command = [
            sys.executable, "-m", "dexlab.cloth_benchmark", "run",
            "--suite", job["suite"], "--case", job["case"],
            "--solver", job["solver"], "--device", args.device,
            "--dt", str(args.dt), "--iterations", str(args.iterations),
            "--output", str(output),
        ]
        job.update(status="running", command=command)
        write_json(report_path, report)
        print(f"[{number}/{len(report['jobs'])}] {output.name}", flush=True)
        started = time.perf_counter()
        with output.with_suffix(".log").open("w") as log:
            try:
                result = subprocess.run(
                    command, stdout=log, stderr=subprocess.STDOUT,
                    timeout=args.timeout, check=False,
                )
                job.update(status="completed", exit_code=result.returncode)
            except subprocess.TimeoutExpired:
                job.update(status="timeout", exit_code=None)
        job["wall_seconds"] = time.perf_counter() - started
        summary_path = output / "summary.json"
        job["protocol_checks_passed"] = False
        if summary_path.is_file():
            summary = json.loads(summary_path.read_text())
            job["summary_sha256"] = digest(summary_path)
            job["failed_checks"] = [
                name for name, passed in summary["checks"].items() if not passed
            ]
            job["protocol_checks_passed"] = bool(
                job["exit_code"] == 0 and summary["protocol_checks_passed"]
            )
        write_json(report_path, report)
    report["status"] = "completed"
    report["passed_count"] = sum(j["protocol_checks_passed"] for j in report["jobs"])
    report["total_count"] = len(report["jobs"])
    write_json(report_path, report)
    return report["passed_count"] == report["total_count"]


def source_identity():
    return {
        str(path.relative_to(ROOT)): digest(path)
        for path in sorted((ROOT / "src/dexlab").rglob("*.py"))
    }


def verify(directory):
    """Recompute physics measurements; do not trust the saved summary."""
    meta = json.loads((directory / "run.json").read_text())
    case = ClothCase(**meta["case"])
    with np.load(directory / "trajectory.npz", allow_pickle=False) as archive:
        data = dict(archive)
    vertices, triangles, masses = case.mesh()
    if (
        data["positions"].shape != (len(data["time"]), len(vertices), 3)
        or data["velocities"].shape != data["positions"].shape
    ):
        raise ValueError("Trajectory dimensions do not match the case")
    result = score_record(
        case, meta["dt_s"], data["time"], data["positions"], data["velocities"]
    )
    forces = np.array([case.forces(t) for t in data["time"][:-1]])
    result["checks"].update(
        successful_runtime=meta["status"] == "completed",
        exact_record_hash=meta["trajectory_sha256"]
        == digest(directory / "trajectory.npz"),
        declared_mesh=bool(
            np.array_equal(data["triangles"], triangles)
            and np.array_equal(data["rest_positions"], vertices)
            and np.array_equal(data["nominal_masses"], masses)
        ),
        prescribed_loads=bool(
            data["forces"].shape == forces.shape
            and np.array_equal(data["forces"], forces)
        ),
        frozen_source=meta["source_before"] == meta["source_after"],
        source_snapshot_matches=all(
            (directory / "source" / name).is_file()
            and digest(directory / "source" / name) == expected
            for name, expected in meta["source_before"].items()
        ),
        declared_initial_state=bool(
            len(data["positions"])
            and np.allclose(data["positions"][0], vertices, rtol=0, atol=1e-6)
            and np.all(data["velocities"][0] == 0)
        ),
    )
    limit = meta.get("engine", {}).get("particle_velocity_limit_m_s")
    if limit is not None:
        result["checks"]["no_native_velocity_clipping"] = bool(
            np.max(np.linalg.norm(data["velocities"], axis=-1), initial=0)
            < limit * 0.99999
        )
    result["protocol_checks_passed"] = all(result["checks"].values())
    result["verifier_sha256"] = {
        name: digest(Path(__file__).with_name(name))
        for name in ("cloth.py", "cloth_self_contact.py", "cloth_benchmark.py")
    }
    result["scope"] = (
        "Recorded nominal cloth experiment; no real-material accuracy claim"
    )
    write_json(directory / "summary.json", result)
    return result


def run(args):
    from unilab.base import registry
    from dexlab.tasks.cloth import TASK  # registers the native scenes

    suite = json.loads(args.suite.read_text())
    entry = next(
        (entry for entry in suite["cases"] if entry["case"]["name"] == args.case), None
    )
    if entry is None:
        raise ValueError(f"Unknown case {args.case}")
    case = ClothCase(**entry["case"])
    if args.refine == 2:
        case = replace(case, nx=2 * case.nx - 1, ny=2 * case.ny - 1)
    if args.output.exists():
        raise FileExistsError(
            "Use a fresh output directory; failed evidence is preserved"
        )
    backend = args.solver.split("-")[0]
    env = registry.make(
        TASK,
        sim_backend=backend,
        env_cfg_override={
            "case": asdict(case),
            "sim_dt": args.dt,
            "ctrl_dt": args.dt,
            "device": args.device,
            "solver": args.solver.removeprefix("newton-"),
            "iterations": args.iterations,
        },
    )
    args.output.mkdir(parents=True)
    meta = {
        "task": TASK,
        "case": asdict(case),
        "split": entry["split"],
        "suite_sha256": digest(args.suite),
        "dt_s": args.dt,
        "solver": args.solver,
        "device": args.device,
        "iterations": args.iterations,
        "source_before": source_identity(),
        "status": "running",
        "error": None,
        "command": sys.argv,
        "system": platform.platform(),
        "timing_context": args.timing_context,
        "execution": "UniLab task owning native engine scene; not UniSim built-in cloth backend",
    }
    write_json(args.output / "run.json", meta)
    for name, expected_hash in meta["source_before"].items():
        source = ROOT / name
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise RuntimeError("Source changed while creating the experiment snapshot")
        destination = args.output / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    samples, positions, velocities, forces, step_times = [], [], [], [], []
    started = time.perf_counter()
    try:
        state = env.init_state()
        meta["prepare_seconds"] = time.perf_counter() - started
        meta["engine"] = env.native.metadata
        if backend == "mujoco":
            (args.output / "model.xml").write_text(env.native.xml)
            # XML is before area-lumped mass assignment; the native binary is authoritative.
            env.native.mj.mj_saveModel(
                env.native.model, str(args.output / "model.mjb"), None
            )
        while True:
            samples.append(state.info["time_s"])
            positions.append(state.info["positions"].copy())
            velocities.append(state.info["velocities"].copy())
            if state.terminated[0]:
                break
            applied = case.forces(state.info["time_s"])
            before = time.perf_counter()
            state = env.step(applied[None])
            step_times.append(time.perf_counter() - before)
            forces.append(applied)
        meta["status"] = "completed"
    except Exception as error:
        meta["status"] = "runtime_error"
        meta["error"] = f"{type(error).__name__}: {error}"
    finally:
        meta["run_wall_seconds"] = time.perf_counter() - started
        meta["source_after"] = source_identity()
        meta["step_and_observation_seconds"] = float(sum(step_times))
        meta["first_step_seconds"] = step_times[0] if step_times else None
        meta["step_time_p95_seconds"] = (
            float(np.quantile(step_times[1:], 0.95)) if len(step_times) > 1 else None
        )
        meta["timing_definition"] = (
            "Per-step force upload, collision/solver completion, state readback and task validation; first-step JIT included separately"
        )
        vertices, triangles, masses = case.mesh()
        np.savez_compressed(
            args.output / "trajectory.npz",
            time=np.array(samples),
            positions=np.asarray(positions).reshape(-1, len(vertices), 3),
            velocities=np.asarray(velocities).reshape(-1, len(vertices), 3),
            forces=np.asarray(forces).reshape(-1, len(vertices), 3),
            step_seconds=np.array(step_times),
            rest_positions=vertices,
            triangles=triangles,
            nominal_masses=masses,
        )
        meta["trajectory_sha256"] = digest(args.output / "trajectory.npz")
        if meta["source_before"] != meta["source_after"]:
            meta["status"] = "source_changed"
        write_json(args.output / "run.json", meta)
        env.close()
    result = verify(args.output)
    print(
        json.dumps(
            {"status": meta["status"], "error": meta["error"], **result}, indent=2
        )
    )
    return result["protocol_checks_passed"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--suite", type=Path, default=SUITE)
    run_parser.add_argument("--case", default="dev-extension")
    run_parser.add_argument("--solver", choices=SOLVERS, default="mujoco")
    run_parser.add_argument("--device", default="cpu")
    run_parser.add_argument("--dt", type=float, default=0.0005)
    run_parser.add_argument("--iterations", type=int, default=10)
    run_parser.add_argument("--refine", type=int, choices=(1, 2), default=1)
    run_parser.add_argument(
        "--timing-context", default="uncontrolled local run; no speed ranking"
    )
    run_parser.add_argument("--output", type=Path, required=True)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("directory", type=Path)
    batch_parser = commands.add_parser("batch")
    batch_parser.add_argument("--suite", type=Path, nargs="+", default=[SUITE])
    batch_parser.add_argument("--split", choices=("development", "test"), default="test")
    batch_parser.add_argument("--solver", choices=SOLVERS, nargs="+", default=list(SOLVERS))
    batch_parser.add_argument("--device", default="cpu")
    batch_parser.add_argument("--dt", type=float, default=0.0005)
    batch_parser.add_argument("--iterations", type=int, default=10)
    batch_parser.add_argument("--timeout", type=float, default=600)
    batch_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "run":
        passed = run(args)
    elif args.command == "batch":
        passed = batch(args)
    else:
        result = verify(args.directory)
        print(json.dumps(result, indent=2))
        passed = result["protocol_checks_passed"]
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
