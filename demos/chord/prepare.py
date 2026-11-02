#!/usr/bin/env python3
"""Inventory one pinned CHORD task and prepare an isolated upstream command.

This is a preparation tool, not a simulator or an execution admission gate.
It never imports Isaac Sim, executes a policy, or downloads licensed assets.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ASSETS = Path("robotic_grounding/source/robotic_grounding/robotic_grounding/assets")
LFS = b"version https://git-lfs.github.com/spec/v1"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture(argv, *, cwd=None, timeout=30):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=True)
    return result.stdout.strip()


def inspect_file(path):
    """Record bytes, not an inferred license, schema or native qualification."""
    result = {"path": str(path), "status": "missing", "sha256": None}
    if not path.is_file():
        return result
    with path.open("rb") as stream:
        prefix = stream.read(256)
    if prefix.startswith(LFS):
        result["status"] = "lfs-pointer"
    elif not path.stat().st_size:
        result["status"] = "empty"
    elif prefix.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        result["status"] = "html-response"
    else:
        result["status"] = "present"
    result.update(size_bytes=path.stat().st_size, sha256=sha256(path))
    if result["status"] == "present" and path.suffix == ".parquet":
        footer = b""
        if result["size_bytes"] >= 8:
            with path.open("rb") as stream:
                stream.seek(-4, os.SEEK_END)
                footer = stream.read(4)
        if not prefix.startswith(b"PAR1") or footer != b"PAR1":
            result["status"] = "invalid-parquet-envelope"
    return result


def inspect_urdf(path):
    """Follow every declared mesh, including collision geometry and visual meshes."""
    rows = [inspect_file(path)]
    if rows[0]["status"] != "present":
        return rows
    try:
        root = ET.parse(path).getroot()
        meshes = sorted({node.attrib["filename"] for node in root.iter("mesh")})
        for mesh in meshes:
            if "://" in mesh:
                rows.append({"path": mesh, "status": "unresolved-mesh-uri", "sha256": None})
            else:
                rows.append(inspect_file((path.parent / mesh).resolve()))
    except (ET.ParseError, KeyError) as error:
        rows[0].update(status="invalid-urdf", detail=str(error))
    return rows


def source_check(source, commit):
    try:
        actual = capture(["git", "rev-parse", "HEAD"], cwd=source)
        # Compare content, not status's stat-cache hints after LFS materialization.
        changed = capture(["git", "diff", "--name-only", "HEAD", "--", "robotic_grounding"], cwd=source)
        untracked = capture(["git", "ls-files", "--others", "--exclude-standard",
                             "--", "robotic_grounding"], cwd=source)
        dirty = "\n".join(value for value in (changed, untracked) if value)
        return {"status": "pinned-clean" if actual == commit and not dirty else "mismatch",
                "expected_commit": commit, "actual_commit": actual, "changes": dirty}
    except (OSError, subprocess.SubprocessError) as error:
        return {"status": "unavailable", "detail": str(error),
                "stderr": getattr(error, "stderr", None)}


def runtime_check(python):
    # Metadata only: importing Isaac before AppLauncher changes its behavior.
    probe = (HERE / "runtime.py").read_text()
    try:
        output = capture([str(python), "-c", probe])
        probes = [line.removeprefix("DEXLAB_CHORD_PROBE=") for line in output.splitlines()
                  if line.startswith("DEXLAB_CHORD_PROBE=")]
        if len(probes) != 1:
            raise ValueError("runtime wrapper did not return exactly one metadata probe")
        result = json.loads(probes[0])
        releases = result["releases"]
        lab = releases["isaaclab"]["version"]
        sim = releases["isaacsim"]["version"] or ""
        required = ("isaaclab", "rsl-rl-lib", "torch", "pyarrow")
        result["status"] = ("metadata-present" if lab == "2.3.2"
                            and sim.split("-")[0] == "5.1.0"
                            and all(result["packages"].get(name) for name in required)
                            and result["robotic_grounding"] else "missing-or-incompatible")
        return result
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        return {"status": "unavailable", "detail": str(error)}


def preflight(manifest, task, source, data_root, python, checkpoint=None):
    rows = []
    for script in ("train", "eval", "cli_args"):
        rows.append({"role": "entrypoint", **inspect_file(source / "robotic_grounding/scripts/rsl_rl" / f"{script}.py")})
    partition = data_root / task["partition"]
    motions = sorted(partition.glob("*.parquet"))
    if not motions:
        rows.append({"role": "motion", "path": str(partition / "*.parquet"),
                     "status": "missing", "sha256": None})
    for motion in motions:
        rows.append({"role": "motion", **inspect_file(motion)})
    for relative in task["assets"]:
        path = data_root / relative
        files = inspect_urdf(path) if path.suffix == ".urdf" else [inspect_file(path)]
        rows.extend({"role": "object-or-support", **row} for row in files)
    suffix = "_primitive" if task["kind"] == "synthetic-smoke" else ""
    for hand in ("left", "right"):
        path = source / ASSETS / f"urdfs/sharpawave/{hand}_sharpa_wave{suffix}.urdf"
        rows.extend({"role": "robot", **row} for row in inspect_urdf(path))
    if checkpoint is not None:
        rows.append({"role": "checkpoint", **inspect_file(checkpoint)})
    for row in rows:
        path = Path(row["path"])
        if path.is_relative_to(data_root):
            relative = ASSETS / "human_motion_data" / path.relative_to(data_root)
        elif path.is_relative_to(source):
            relative = path.relative_to(source)
        else:
            continue
        expected = manifest.get("upstream_file_sha256", {}).get(str(relative))
        if expected:
            row["expected_sha256"] = expected
            if row["status"] == "present" and row["sha256"] != expected:
                row["status"] = "hash-mismatch"
    source_state = source_check(source, manifest["upstream"]["commit"])
    runtime = runtime_check(python)
    try:
        gpu = {"status": "visible", "devices": capture([
            "nvidia-smi", "--query-gpu=uuid,name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits"], timeout=5).splitlines()}
        if not gpu["devices"]:
            gpu["status"] = "unavailable"
    except (OSError, subprocess.SubprocessError) as error:
        gpu = {"status": "unavailable", "detail": str(error)}
    blockers = []
    for row in rows:
        if row["status"] != "present":
            blockers.append({"check": row["role"], "status": row["status"],
                             "path": row["path"], "recovery": task["asset_recovery"]})
    if source_state["status"] != "pinned-clean":
        blockers.append({"check": "source", "recovery": "Use a clean checkout at the manifest commit."})
    if runtime["status"] != "metadata-present":
        blockers.append({"check": "runtime", "recovery": "Use the isolated upstream Isaac Lab 2.3.2 environment; see SETUP.md."})
    elif not Path(runtime["robotic_grounding"]).resolve().is_relative_to(source.resolve()):
        blockers.append({"check": "runtime-source", "recovery": "Install robotic_grounding from the pinned checkout into the isolated runtime."})
    if gpu["status"] != "visible":
        blockers.append({"check": "gpu", "recovery": "Provide the qualified NVIDIA runtime and recheck free memory."})
    return {"schema_version": 1, "task": task["id"], "kind": task["kind"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "blocked" if blockers else "files-and-metadata-present",
            "source": source_state, "runtime": runtime, "gpu": gpu, "files": rows,
            "blockers": blockers, "license": task["license"],
            "execution_admitted": False,
            "pending_execution_checks": ["license/access attestation", "Parquet schema, sequence and asset resolution in upstream loader",
                "frozen measured resource plan and cgroup admission", "native contact/VOC readback",
                "recorder parity and independent task scoring"],
            "policy_evaluation": "not-run", "training": "not-run"}


def command(task, source, data_root, python, attempt, operation, seed,
            num_envs, iterations=None, steps=None, checkpoint=None):
    if seed < 0 or num_envs < 1:
        raise ValueError("seed must be nonnegative and num_envs must be positive")
    if operation == "train" and (iterations is None or iterations < 1 or steps is not None or checkpoint is not None):
        raise ValueError("train requires positive iterations; steps/checkpoint are eval-only")
    if operation == "eval" and (steps is None or steps < 1 or checkpoint is None or iterations is not None):
        raise ValueError("eval requires positive steps and an explicit checkpoint; iterations are train-only")
    if task["kind"] == "synthetic-smoke" and (num_envs != 1 or operation == "train" and iterations != 1):
        raise ValueError("synthetic smoke uses one environment and one training iteration")
    argv = [str(python), str(source / "robotic_grounding/scripts/rsl_rl" / f"{operation}.py"),
            "--headless", "--task", "Sharpa-V2D-v0", "--motion_file", str(data_root / task["partition"]),
            "--seed", str(seed), "--num_envs", str(num_envs)]
    if task["kind"] == "synthetic-smoke":
        argv.append("--use_primitive_urdfs")
    if operation == "train":
        argv += ["--max_iterations", str(iterations), "--logger", "tensorboard",
                 "--output_root", str(attempt), "--run_name", task["id"],
                 f"agent.num_steps_per_env={8 if task['kind'] == 'synthetic-smoke' else 24}",
                 "agent.save_interval=1"]
    else:
        # Upstream exports policy/video alongside the checkpoint. Isolate that directory.
        argv += ["--max_steps", str(steps), "--checkpoint", str(attempt / "checkpoint.pt")]
    argv += task["reward_overrides"]
    argv.append(f"hydra.run.dir={attempt / 'hydra'}")
    return {"argv": argv, "cwd": str(source / "robotic_grounding"),
            "environment": {"HUMAN_MOTION_DATA_DIR": str(data_root)},
            "operation": operation, "seed": seed, "num_envs": num_envs,
            "iterations": iterations, "evaluation_steps": steps,
            "sample_budget": num_envs * iterations * (8 if task["kind"] == "synthetic-smoke" else 24) if iterations else None,
            "checkpoint_source": str(checkpoint) if checkpoint else None,
            "evaluation_contract": {"first_reference_frame": True, "voc_scale": 0.0,
                                    "curriculum": None, "evidence": "pinned upstream source; native readback pending"},
            "execution_admitted": False}


def write_attempt(attempt, plan, report, checkpoint=None):
    # Atomic reservation: even empty or interrupted attempts must not be reused.
    attempt.mkdir(parents=True, exist_ok=False)
    for name, value in (("command.json", plan), ("preflight.json", report)):
        (attempt / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    if checkpoint is not None:
        expected = next(row for row in report["files"] if row["role"] == "checkpoint")
        if expected["status"] == "present":
            shutil.copyfile(checkpoint, attempt / "checkpoint.pt")
            if sha256(attempt / "checkpoint.pt") != expected["sha256"]:
                raise ValueError("checkpoint changed during preparation; retain this failed attempt")
    shell = "cd " + shlex.quote(plan["cwd"]) + "\n" + shlex.join([
        "env", *[f"{key}={value}" for key, value in plan["environment"].items()], *plan["argv"]])
    (attempt / "command.txt").write_text("# REVIEW ONLY: resource/native admission remains pending.\n" + shell + "\n")


def main(argv=None):
    manifest_path = HERE / "tasks.json"
    manifest = json.loads(manifest_path.read_text())
    tasks = {task["id"]: task for task in manifest["tasks"]}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("preflight", "train", "eval"))
    parser.add_argument("--task", choices=tasks, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--python", type=Path, required=True, help="Isolated CHORD interpreter, not DexLab's environment")
    parser.add_argument("--attempt", type=Path, help="New output directory; never reused")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--num-envs", type=int)
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args(argv)
    source = args.source.resolve()
    data_root = (args.data_root or source / ASSETS / "human_motion_data").resolve()
    # Do not resolve the interpreter symlink: venv identity depends on the path used.
    python = args.python.absolute()
    checkpoint = args.checkpoint.resolve() if args.checkpoint else None
    task = tasks[args.task]
    try:
        plan = None
        if args.operation != "preflight":
            if args.attempt is None or args.seed is None or args.num_envs is None:
                raise ValueError("train/eval preparation requires --attempt, --seed and --num-envs")
            plan = command(task, source, data_root, python, args.attempt.resolve(), args.operation,
                           args.seed, args.num_envs, args.iterations, args.steps, checkpoint)
            plan["manifest_sha256"] = sha256(manifest_path)
            plan["upstream"] = manifest["upstream"]
        elif any(value is not None for value in (args.attempt, args.seed, args.num_envs, args.iterations, args.steps)):
            raise ValueError("preflight does not create an attempt or accept execution budgets")
        report = preflight(manifest, task, source, data_root, python, checkpoint)
        report["manifest_sha256"] = sha256(manifest_path)
        if plan:
            write_attempt(args.attempt.resolve(), plan, report, checkpoint)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 2 if report["blockers"] else 0
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
