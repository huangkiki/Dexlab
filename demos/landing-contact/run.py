#!/usr/bin/env python3
"""Run the pinned upstream probe/evaluator with complete native contact copies."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse


UPSTREAM_COMMIT = "5b313d75e804cdd2ff1ce9bdcfa899a98eca856b"
CHECKPOINT_SHA256 = "7933f7638b02f0c378606b23c361e328fb3bd6da97086cc2ff9c20aff9aefab2"
RUNTIME = {"mujoco": "3.15.0", "mujoco-warp": "3.15.0",
           "warp-lang": "1.17.0+cu12", "torch": "2.11.0+cu128"}
SOURCES = {"isaaclab": "46d6cc3d7b115906fad12efd372fbf69f4e3d3ed",
           "isaaclab_newton": "46d6cc3d7b115906fad12efd372fbf69f4e3d3ed",
           "newton": "71eeba16a717d4dcf0b9dd7056a7b6f863054dc3"}


def runtime_identity():
    versions = {}
    for name in RUNTIME:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unavailable"
    if versions != RUNTIME:
        raise ValueError(f"Native versions differ from the frozen reference: {versions}")
    sources = {}
    for name, expected in SOURCES.items():
        spec = importlib.util.find_spec(name)
        if spec is None or spec.origin is None:
            raise ValueError(f"Missing reference source package: {name}")
        installed = Path(spec.origin).parent
        provenance = importlib.metadata.distribution(name).read_text("direct_url.json")
        if provenance is None:
            raise ValueError(f"Missing local source provenance: {name}")
        url = urlparse(json.loads(provenance)["url"])
        if url.scheme != "file" or url.netloc:
            raise ValueError(f"Expected the pinned local source install: {name}")
        folder = Path(unquote(url.path))
        actual = subprocess.check_output(["git", "-C", str(folder), "rev-parse", "HEAD"], text=True).strip()
        if actual != expected or subprocess.check_output(["git", "-C", str(folder), "diff", "HEAD"]):
            raise ValueError(f"Reference dependency source differs: {name}")
        source_package = folder / name
        for file in installed.rglob("*.py"):
            reference = source_package / file.relative_to(installed)
            if not reference.is_file() or file.read_bytes() != reference.read_bytes():
                raise ValueError(f"Installed source differs from pinned checkout: {file}")
        sources[name] = actual
    return {"packages": versions, "sources": sources}


def asset_identity(source):
    """Verify published inputs and retain every generated model dependency."""
    specification = json.loads((source / "environment/asset-manifest.json").read_text())
    data = source / "third_party/supermimic_vibed/data"
    expected = {"g1_description/" + row["relative_file"]: row["sha256"]
                for row in specification["assets"]}
    expected["backflip/backflip.csv"] = specification["motion_csv_sha256"]
    hashes = {}
    for directory in ("g1_description", "g1_usd", "backflip"):
        for path in sorted((data / directory).rglob("*")):
            if path.is_symlink():
                raise ValueError("Reference assets must be regular local files")
            if path.is_file():
                with path.open("rb") as stream:
                    hashes[str(path.relative_to(data))] = hashlib.file_digest(stream, "sha256").hexdigest()
    if any(hashes.get(name) != digest for name, digest in expected.items()):
        raise ValueError("Robot or motion inputs differ from the published manifest")
    for name in ("g1_description/g1_29dof.xml", "g1_usd/g1_29dof/g1_29dof.usda"):
        if name not in hashes:
            raise ValueError(f"Missing generated reference model: {name}")
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("probe", "evaluate"))
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--budget", required=True, type=Path)
    parser.add_argument("--case", required=True,
                        choices=("support-probe", "policy-repeat-1", "policy-repeat-2", "policy-repeat-3"))
    args = parser.parse_args()
    source, output = args.upstream.resolve(), args.output.resolve()
    if args.mode == "evaluate" and args.checkpoint is None:
        parser.error("Evaluation requires the frozen checkpoint")
    if args.mode == "probe" and args.checkpoint is not None:
        parser.error("The support probe does not use a checkpoint")
    if (args.mode == "probe") != (args.case == "support-probe"):
        parser.error("Mode and frozen case differ")
    actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if actual != UPSTREAM_COMMIT:
        parser.error("Upstream commit differs from the frozen reference")
    if subprocess.check_output(["git", "-C", str(source), "diff", "HEAD", "--", "scripts", "third_party", "environment"]):
        parser.error("Tracked reference source changed")
    try:
        runtime = runtime_identity()
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    # Both imported modules and the upstream executable use these exact paths.
    sys.path.insert(0, str(source / "scripts"))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    import dexlab.landing_record as recorder
    from dexlab.apple_admission import loaded_mujoco_library, record_native_file
    from dexlab.cloth_engines import package_identity
    from dexlab.migration_budget import MigrationBudget

    native_version = recorder.mujoco.mj_versionString()
    if native_version != RUNTIME["mujoco"]:
        parser.error("Loaded MuJoCo core differs from the reference package version")
    runtime["native_mujoco"] = {
        "version": native_version,
        "payload_sha256": record_native_file("mujoco", loaded_mujoco_library()),
    }
    runtime["package_code_sha256"] = {
        name: package_identity(name)["code_sha256"] for name in ("mujoco", "mujoco-warp")}
    assets = asset_identity(source)

    protocol = Path(__file__).with_name("protocol.json").read_bytes()
    budget = MigrationBudget(args.budget)
    budget_manifest = json.loads((budget.root / "manifest.json").read_text())
    if budget_manifest["protocol_sha256"] != hashlib.sha256(protocol).hexdigest():
        parser.error("Budget protocol differs from this case")
    if args.mode == "evaluate":
        probes = [a for a in budget.status()["attempts"] if a["case_id"] == "support-probe"]
        if not probes or not probes[-1]["terminal"] or probes[-1]["terminal"]["outcome"] != "recorded":
            parser.error("A completed support probe is required")
        qualification = Path(probes[-1]["handle"]["output"]) / "validation/reference_env_probe.json"
        if json.loads(qualification.read_text()).get("passed") is not True:
            parser.error("Static support probe did not qualify")
        invocation = json.loads((qualification.parents[1] / "invocation.json").read_text())
        if invocation["asset_sha256"] != assets or invocation["runtime"] != runtime:
            parser.error("Assets or runtime changed after support qualification")

    script = source / "scripts" / ("probe_reference_env.py" if args.mode == "probe"
                                   else "evaluate_reference_backflip.py")
    manifest = {
        "upstream_commit": actual, "mode": args.mode,
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "recorder_sha256": hashlib.sha256(Path(recorder.__file__).read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(protocol).hexdigest(), "runtime": runtime,
        "python": sys.executable, "status": "started", "training": False,
        "asset_sha256": assets,
    }
    if args.checkpoint is not None:
        checkpoint = args.checkpoint.resolve()
        with checkpoint.open("rb") as stream:
            manifest["checkpoint_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        if manifest["checkpoint_sha256"] != CHECKPOINT_SHA256:
            parser.error("Checkpoint differs from the frozen release")
    output.mkdir(parents=True, exist_ok=False)
    attempt = budget.reserve(args.case, {
        "pid": os.getpid(), "output": str(output),
        "process_start_ticks": Path("/proc/self/stat").read_text().split(") ", 1)[1].split()[19],
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "cgroup": Path("/proc/self/cgroup").read_text().strip(),
    }, timeout_s=600)
    started = time.monotonic()
    manifest["budget_attempt"] = attempt
    manifest_path = output / "invocation.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    os.environ["BACKFLIP_WORKDIR"] = str(output)
    sys.modules["contact_recorder"] = recorder
    sys.argv = [str(script)]
    if args.mode == "evaluate":
        sys.argv += ["--checkpoint", str(checkpoint), "--output", str(output)]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except BaseException as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    else:
        manifest["status"] = "completed"
    finally:
        if recorder.active_recorder is not None:
            partial = recorder.active_recorder
            manifest["partial_substeps"] = len(partial.samples)
            try:
                if partial.samples:
                    partial_dir = output / "partial"
                    partial_dir.mkdir(exist_ok=False)
                    partial.save(partial_dir / "contact_forces_200hz.npz")
            except Exception as error:
                manifest["partial_save_error"] = f"{type(error).__name__}: {error}"
            finally:
                partial.close()
        raw = (json.dumps(manifest, indent=2) + "\n").encode()
        manifest_path.write_bytes(raw)
        budget.finish(attempt, wall_s=time.monotonic() - started,
                      evidence_sha256=hashlib.sha256(raw).hexdigest(),
                      outcome="recorded" if manifest["status"] == "completed" else "failed")


if __name__ == "__main__":
    main()
