"""Paired frozen apple experiments. Outcome failures remain benchmark data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = ROOT / "benchmarks/apple-stem-v1.json"
SCENE_KEYS = {"apple_mass", "apple_x_offset", "apple_y_offset", "apple_yaw"}


def write_json(path: Path, value: dict) -> None:
    """A terminal receipt is visible only after it is completely written."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [ROOT / "pyproject.toml"]
    paths += sorted((ROOT / "src/dexlab").rglob("*.py"))
    paths += sorted((ROOT / "demos/apple-stem-grasp/src").glob("*.py"))
    paths += sorted(
        p
        for p in (ROOT / "demos/apple-stem-grasp/assets").rglob("*")
        if p.is_file() and p.suffix.lower() not in (".png", ".jpg", ".jpeg")
    )
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def read_suite(path: Path) -> dict:
    spec = json.loads(path.read_text())
    if spec.get("schema_version") != 1 or spec.get("track") != "task-robustness":
        raise ValueError("Expected a version 1 task-robustness suite")
    identities, seeds = set(), set()
    for case in spec["cases"]:
        name = case["id"]
        if not name or any(
            c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name
        ):
            raise ValueError("Case IDs must be safe lowercase directory names")
        if name in identities or case["seed"] in seeds:
            raise ValueError("Cases and seeds must be disjoint across splits")
        identities.add(name)
        seeds.add(case["seed"])
        if case["split"] not in ("development", "regression", "test"):
            raise ValueError("Unknown split")
        parameters = case["parameters"]
        if set(parameters) != SCENE_KEYS:
            raise ValueError("Every physical case must declare all scene parameters")
        for key, value in parameters.items():
            if not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError("Scene parameters must be finite")
            low, high = spec["ranges"][key]
            if not low <= value <= high:
                raise ValueError(f"{name}: {key} outside its frozen range")
        if parameters["apple_mass"] <= 0:
            raise ValueError("Mass must be positive")
    return spec


def select_cases(spec: dict, split: str, case_id: str | None) -> list[dict]:
    if case_id == "baseline":
        return [
            {
                "id": "baseline",
                "split": "baseline",
                "seed": None,
                "parameters": {
                    "apple_mass": 0.2,
                    "apple_x_offset": 0.0,
                    "apple_y_offset": 0.0,
                    "apple_yaw": 0.0,
                },
            }
        ]
    cases = [
        c
        for c in spec["cases"]
        if c["split"] == split and (case_id is None or c["id"] == case_id)
    ]
    if not cases:
        raise ValueError("No matching cases in the selected split")
    return cases


def wilson_interval(successes: int, count: int) -> list[float] | None:
    if not count:
        return None
    z = 1.959963984540054
    fraction = successes / count
    denominator = 1 + z * z / count
    center = (fraction + z * z / (2 * count)) / denominator
    radius = (
        z
        * math.sqrt(fraction * (1 - fraction) / count + z * z / (4 * count**2))
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def aggregate(jobs: list[dict]) -> dict:
    """All scheduled cases stay in denominators, including missing receipts."""
    groups: dict[str, list[dict]] = {}
    for row in jobs:
        key = f"{row['backend']}/dt={row['parameters']['timestep']:g}"
        groups.setdefault(key, []).append(row)
    summaries = {}
    for key, rows in groups.items():
        passed = sum(
            r.get("status") == "scored" and r.get("outcome", {}).get("passed") is True
            for r in rows
        )
        terminal = sum(
            r.get("status") in ("scored", "runtime_error", "timeout") for r in rows
        )
        summaries[key] = {
            "scheduled": len(rows),
            "terminal": terminal,
            "passed": passed,
            "failed_or_unavailable": len(rows) - passed,
            "success_rate": passed / len(rows),
            "success_rate_wilson_95": wilson_interval(passed, len(rows)),
            "statuses": {
                s: sum(r.get("status", "pending") == s for r in rows)
                for s in ("scored", "runtime_error", "timeout", "pending")
            },
        }
    return {
        "groups": summaries,
        "jobs": jobs,
        "limits": [
            "Confidence intervals describe this declared case distribution, not real deployment.",
            "Different backend calibration: task robustness, not an engine accuracy ranking.",
            "Relative wrist motion is not contact-material cumulative slip.",
        ],
    }


def environment() -> dict:
    packages = {}
    for name in (
        "dexlab",
        "unilab",
        "unisim-core",
        "mujoco",
        "superdex-physics",
        "numpy",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    cpu = next(
        (
            line.partition(":")[2].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        platform.processor(),
    )
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpu_count": os.cpu_count(),
        "packages": packages,
        "execution": "Serial native CPU scenes; eight SuperDex workers; rendering disabled",
    }


def execute_episode(job_path: Path) -> None:
    """Worker imports engines only after setting native precision."""
    os.environ["SUPERDEX_PRECISION"] = "fp64"
    from unilab.base import registry
    from dexlab.tasks.apple_stem import TASK

    job = json.loads(job_path.read_text())
    expected_source = json.loads((job_path.parent.parent / "run.json").read_text())[
        "source_hashes"
    ]
    if source_hashes() != expected_source:
        raise RuntimeError("Source changed after benchmark was frozen")
    env = registry.make(
        TASK,
        sim_backend=job["backend"],
        env_cfg_override={
            "output": str(job_path.parent),
            "headless": True,
            "parameters": job["parameters"],
        },
    )
    prepared = time.perf_counter()
    try:
        state = env.init_state()
        preparation = time.perf_counter() - prepared
        stepping = time.perf_counter()
        while not state.terminated[0]:
            state = env.step(state.info["scripted_target"])
        elapsed = time.perf_counter() - stepping
        if source_hashes() != expected_source:
            raise RuntimeError(
                "Source changed during this episode; refusing mixed-code evidence"
            )
        engine = json.loads((job_path.parent / "engine.json").read_text())
        write_json(
            job_path.parent / "timing.json",
            {
                "preparation_seconds": preparation,
                "physics_step_seconds": engine["physics_step_seconds"],
                "stepping_with_control_observation_and_export_seconds": elapsed,
                "render_seconds": 0.0,
                "rendering": "Disabled; display-model construction is included in preparation",
                "preparation_settling": "3 s at 2 ms in SuperDex, shared by both paths",
                "simulation_seconds": 14.0,
                "physics_realtime_factor": 14 / engine["physics_step_seconds"],
            },
        )
    finally:
        env.close()


def score_job(directory: Path, job: dict, returncode: int, elapsed: float) -> dict:
    result = {
        **job,
        "returncode": returncode,
        "subprocess_seconds": elapsed,
        "status": "runtime_error",
        "outcome": {"passed": False},
    }
    try:
        if returncode:
            raise RuntimeError(f"Worker exited {returncode}; see episode.log")
        # The scorer takes expected mass from the frozen job, not from the engine.
        from verify_sdf_grasp import verify_grasp
        from dexlab.jitter import diagnose_run
        from dexlab.mujoco_artifacts import pack_model

        engine = json.loads((directory / "engine.json").read_text())
        if (
            engine["backend"] != job["backend"]
            or engine["dt"] != job["parameters"]["timestep"]
        ):
            raise ValueError("Engine or timestep differs from the frozen job")
        pack_model(directory, shared_store=directory.parent / ".model-chunks")

        result["outcome"] = verify_grasp(
            directory, expected_mass=job["parameters"]["apple_mass"]
        )
        result["timing"] = json.loads((directory / "timing.json").read_text())
        write_json(directory / "jitter-diagnostics.json", diagnose_run(directory))
        result["status"] = "scored"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["artifacts"] = {
        p.relative_to(directory).as_posix(): sha256(p)
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p != directory / "result.json"
    }
    write_json(directory / "result.json", result)
    return result


def load_receipt(directory: Path, expected: dict) -> dict:
    result = json.loads((directory / "result.json").read_text())
    if any(result.get(k) != v for k, v in expected.items()):
        raise ValueError(f"Receipt does not match frozen job: {directory}")
    for name, digest in result["artifacts"].items():
        if (
            Path(name).is_absolute()
            or ".." in Path(name).parts
            or sha256(directory / name) != digest
        ):
            raise ValueError(f"Artifact changed after scoring: {directory / name}")
    return result


def run_suite(args: argparse.Namespace) -> dict:
    spec = read_suite(args.suite)
    cases = select_cases(spec, args.split, args.case)
    backends = ("mujoco", "superdex") if args.backend == "all" else (args.backend,)
    factors = spec["timestep_sweep_factors"] if args.timestep_sweep else [1.0]
    jobs = []
    for case in cases:
        for backend in backends:
            for factor in factors:
                parameters = (
                    spec["defaults"]["shared"]
                    | spec["defaults"][backend]
                    | case["parameters"]
                )
                parameters["timestep"] *= factor
                jobs.append(
                    {
                        "id": f"{case['id']}-{backend}-{round(parameters['timestep'] * 1e6)}us",
                        "case": case,
                        "backend": backend,
                        "parameters": parameters,
                    }
                )
    signature = {
        "suite_sha256": sha256(args.suite),
        "source_hashes": source_hashes(),
        "jobs": jobs,
        "environment": environment(),
    }
    output = args.output.resolve()
    if output.exists():
        if not args.resume:
            raise ValueError(
                "Output exists; use --resume to validate and continue an unchanged run"
            )
        if json.loads((output / "run.json").read_text()) != signature:
            raise ValueError(
                "Suite, source, environment or selection changed; use a new output directory"
            )
    else:
        output.mkdir(parents=True)
        write_json(output / "run.json", signature)
        write_json(output / "suite.json", spec)
    rows = []
    if not (output / "report.json").exists():
        write_json(output / "report.json", aggregate(jobs))
    for index, job in enumerate(jobs):
        if source_hashes() != signature["source_hashes"]:
            raise RuntimeError(
                "Source changed during suite execution; preserve this run and use a new directory"
            )
        directory = output / job["id"]
        if (directory / "result.json").exists():
            rows.append(load_receipt(directory, job))
        else:
            if directory.exists():
                raise RuntimeError(
                    f"Unfinished worker output preserved at {directory}; inspect its process before retrying in a NEW run directory"
                )
            if shutil.disk_usage(output).free < 4 * 1024**3:
                raise RuntimeError(
                    "Less than 4 GiB free: stopping before another model build; completed evidence is preserved"
                )
            directory.mkdir()
            write_json(directory / "job.json", job)
            started = time.perf_counter()
            print(f"[{index + 1}/{len(jobs)}] {job['id']}", flush=True)
            with (directory / "episode.log").open("w") as log:
                try:
                    process = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "dexlab.benchmark",
                            "_episode",
                            str(directory / "job.json"),
                        ],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        timeout=args.timeout,
                        check=False,
                    )
                    returncode = process.returncode
                except subprocess.TimeoutExpired:
                    returncode = -9
            result = score_job(
                directory, job, returncode, time.perf_counter() - started
            )
            if returncode == -9:
                result["status"] = "timeout"
                write_json(directory / "result.json", result)
            rows.append(result)
            print(
                f"  {result['status']}, passed={result['outcome']['passed']}",
                flush=True,
            )
        # Pending trials stay visible, even during an interrupted sweep.
        write_json(output / "report.json", aggregate(rows + jobs[len(rows) :]))
    return aggregate(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    run.add_argument(
        "--split", choices=("development", "regression", "test"), default="regression"
    )
    run.add_argument("--case")
    run.add_argument("--backend", choices=("all", "mujoco", "superdex"), default="all")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--timestep-sweep", action="store_true")
    run.add_argument("--timeout", type=float, default=1200)
    commands.add_parser("_episode").add_argument("job", type=Path)
    args = parser.parse_args()
    if args.command == "_episode":
        execute_episode(args.job)
    else:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            parser.error("Timeout must be finite and positive")
        result = run_suite(args)
        print(json.dumps(result["groups"], indent=2))
        if any(r["status"] != "scored" for r in result["jobs"]):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
