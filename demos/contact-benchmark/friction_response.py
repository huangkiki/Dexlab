"""Run the frozen small friction development matrix; preserve every outcome."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dexlab.apple_admission import observe_runtime, refresh_inventory
from dexlab.engine_versions import validate_versions
from dexlab.official_wheels import verify_official_wheel
from dexlab.physx_baseline import digest, write_json


def run(output, wheel_dir, suite_path=None):
    root = Path(__file__).resolve().parents[2]
    suite_path = root / "benchmarks/contact-friction-v1.json" if suite_path is None else suite_path.resolve()
    suite = json.loads(suite_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    sources = sorted(set(root.glob("src/dexlab/*.py")) | set(root.glob("src/dexlab/tasks/*.py")) | {Path(__file__).resolve(), suite_path})
    hashes = {str(p.relative_to(root)): digest(p) for p in sources}
    for p in sources:
        destination = output / "source" / p.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(p.read_bytes())
    freeze = {"suite": suite, "source_sha256": hashes, "status": "admitting", "runs": []}
    write_json(output / "batch.json", freeze)
    runtime = observe_runtime()
    audit = refresh_inventory()
    validate_versions(audit, runtime["installed"], runtime["native"])
    wheels = {}
    for row in audit:
        available = [(wheel_dir / name, sha) for name, sha in row["distribution_sha256"].items()
                     if name.endswith(".whl") and (wheel_dir / name).is_file()]
        if len(available) != 1:
            raise ValueError("Expected exactly one official wheel per package")
        path, sha = available[0]
        package = row["package"]
        wheels[package] = verify_official_wheel(
            path, package=package, version=runtime["installed"][package],
            official_sha256=sha, installed_code_sha256=runtime["package_code_sha256"][package])
    freeze.update(runtime=runtime, audit=audit, official_wheels=wheels, status="running")
    write_json(output / "batch.json", freeze)
    env = dict(os.environ, DEXLAB_MUJOCO_PROFILE="qualification-3.14.0")
    try:
        for parameters in suite["cases"]:
            case = suite["defaults"] | parameters
            solver_parameters = case.pop("solver_parameters", {})
            solver_path = output / (case["name"] + "-solver.json")
            if solver_parameters:
                write_json(solver_path, solver_parameters)
            case_path = output / (case["name"] + ".json")
            write_json(case_path, case)
            for engine in suite["engines"]:
                if len(freeze["runs"]) >= suite["max_runs"]:
                    raise ValueError("Declared run budget exceeded")
                remaining = suite["wall_budget_s"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("Development campaign budget exhausted")
                name = f"{engine}-{case['name']}"
                directory = output / name
                before = time.monotonic()
                solver_args = ["--solver-parameters", str(solver_path)] if solver_parameters else []
                with (output / (name + ".log")).open("w") as log:
                    completed = subprocess.run([
                        sys.executable, "-m", "dexlab.contact_plane_native", "--engine", engine,
                        "--case", str(case_path), "--output", str(directory), *solver_args,
                    ], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=remaining)
                row = {"id": name, "engine": engine, "case": case, "solver_parameters": solver_parameters,
                       "process_exit": completed.returncode, "process_wall_s": time.monotonic() - before}
                if (directory / "summary.json").is_file():
                    row["summary"] = json.loads((directory / "summary.json").read_text())
                freeze["runs"].append(row)
                write_json(output / "batch.json", freeze)
                if not (directory / "run.json").is_file() or json.loads((directory / "run.json").read_text())["status"] != "completed":
                    raise RuntimeError("Native runtime failure; retain output and stop")
        freeze["status"] = "completed"
    finally:
        freeze["total_wall_s"] = time.monotonic() - started
        freeze["source_unchanged"] = all(digest(root / name) == sha for name, sha in hashes.items())
        write_json(output / "batch.json", freeze)
    if not freeze["source_unchanged"]:
        raise RuntimeError("Frozen source changed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--wheel-dir", required=True, type=Path)
    parser.add_argument("--suite", type=Path, help="Explicit frozen development matrix")
    args = parser.parse_args()
    run(args.output.resolve(), args.wheel_dir.resolve(), args.suite)
