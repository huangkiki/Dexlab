#!/usr/bin/env python3
"""Evaluate the pinned public AMP policy with original resets and control timing.

Run only inside the shared research guard and bounded resource runner after
provenance admission. This entry never trains, installs or chooses checkpoints.
"""

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


def file_sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_identity(source, protocol):
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if commit != protocol["source_commit"] or subprocess.check_output(
            ["git", "-C", str(source), "diff", "HEAD", "--", "src", "rsl_rl", "dataset", "models",
             "pyproject.toml", "uv.lock"]):
        raise ValueError("AMP reference source differs from the frozen commit")
    fetch = runpy.run_path(str(Path(__file__).with_name("fetch_source.py")))
    if {path.name for path in (source / "dataset/dualarm").iterdir()} != {"dual_arm1.npy", "dual_arm2.npy"}:
        raise ValueError("The original motion loader must see exactly the two pinned clips")
    inputs = {name: fetch["inspect_input"](source / name, size, blob)
              for name, (size, blob) in fetch["INPUTS"].items()}
    if inputs["models/dualarm.pt"]["sha256"] != protocol["checkpoint_sha256"]:
        raise ValueError("AMP checkpoint differs from the protocol")
    assets = {}
    for path in sorted((source / "src/mjlab_g1/assets").rglob("*")):
        if path.is_symlink():
            raise ValueError("Reference assets must not be symlinks")
        if path.is_file() and "__pycache__" not in path.parts:
            assets[str(path.relative_to(source))] = file_sha256(path)
    return {"commit": commit, "inputs": inputs, "assets_sha256": assets,
            "uv_lock_sha256": file_sha256(source / "uv.lock")}


def runtime_identity(protocol):
    actual = {name: importlib.metadata.version(name) for name in protocol["runtime"]}
    if actual != protocol["runtime"]:
        raise ValueError(f"Native versions differ from the frozen AMP candidate: {actual}")
    sources = {}
    for name, commit in protocol["dependency_sources"].items():
        raw = importlib.metadata.distribution(name).read_text("direct_url.json")
        provenance = json.loads(raw) if raw else {}
        if provenance.get("vcs_info", {}).get("commit_id") != commit:
            raise ValueError(f"Pinned Git dependency provenance is missing or changed: {name}")
        sources[name] = provenance
    raw = importlib.metadata.distribution("mujoco-warp").read_text("direct_url.json")
    provenance = json.loads(raw) if raw else {}
    if provenance.get("archive_info", {}).get("hashes", {}).get("sha256") != \
            protocol["runtime_revision"]["wheel_sha256"]:
        raise ValueError("Install the verified official MuJoCo Warp wheel by its local path")
    return {"packages": actual, "sources": sources, "mujoco_warp_wheel": provenance,
            "installed_packages": sorted([d.metadata["Name"], d.version]
                                         for d in importlib.metadata.distributions())}


def require_probe_qualification(budget, output, protocol_sha, source, runtime):
    qualification = budget.root / "qualification.json"
    result = json.loads(qualification.read_text())
    if result.get("passed") is not True or result.get("protocol_sha256") != protocol_sha:
        raise ValueError("Native recorder parity has not qualified for this protocol")
    qualifier = runpy.run_path(str(Path(__file__).with_name("qualify.py")))["qualify"]
    protocol = json.loads(Path(__file__).with_name("protocol.json").read_text())
    if qualifier(budget, protocol, protocol_sha) != result:
        raise ValueError("Probe records or final resource telemetry changed after qualification")
    attempts = budget.status()["attempts"]
    for case in ("probe-native", "probe-recorded"):
        matches = [a for a in attempts if a["case_id"] == case]
        if len(matches) != 1 or not matches[0]["terminal"] or \
                matches[0]["terminal"]["outcome"] != "recorded":
            raise ValueError("A completed parity probe is required")
        directory = Path(matches[0]["handle"]["output"])
        invocation_path = directory / "invocation.json"
        invocation = json.loads(invocation_path.read_text())
        if result["probe_invocation_sha256"][case] != file_sha256(invocation_path) or \
                invocation["status"] != "completed" or invocation["source"] != source or \
                invocation["runtime"] != runtime:
            raise ValueError("Probe inputs/runtime/evidence changed after qualification")
    # Retain the exact admission artifact with every dependent evaluation.
    (output / "probe-qualification.json").write_bytes(qualification.read_bytes())


def disable_hands(cfg):
    """Apply the predeclared negative through source scene configuration only."""
    from mjlab.utils.spec_config import CollisionCfg

    cfg.scene.entities["robot"].collisions += (CollisionCfg(
        geom_names_expr=(r"^(left|right)_(hand|wrist)_collision$",),
        contype=0, conaffinity=0, condim=1, priority=0, disable_other_geoms=False,
    ),)


def check_source_conditions(env, wrapper, case, protocol):
    import numpy as np

    conditions = protocol["conditions"]
    cfg = env.cfg
    observed = {
        "worlds": env.num_envs, "physics_dt_s": env.physics_dt, "decimation": cfg.decimation,
        "control_dt_s": env.step_dt, "episode_s": float(cfg.episode_length_s),
        "policy_observation_corruption": cfg.observations["policy"].enable_corruption,
        "virtual_pd_enabled": cfg.virtual_pd_cfg.enabled,
        "assistance_scale": env.virtual_pd_assistance_scale,
        "reset_height_fraction": env.object_reset_height_frac, "rsi_fraction": cfg.rsi_fraction,
        "render_mode": env.render_mode,
    }
    if any(observed[key] != conditions[key] for key in observed) or not cfg.eval_mode or \
            cfg.curriculum or "push_robot" in cfg.events or set(cfg.terminations) != {"time_out"}:
        raise ValueError(f"Source play conditions changed: {observed}")
    if cfg.seed != case["seed"] or wrapper.clip_actions != 1.5 or env.max_episode_length != 3000:
        raise ValueError("Seed, action clipping or source episode length changed")
    if cfg.hold_steps != protocol["checks"]["source_hold_control_steps"] or \
            cfg.trajectory_position_tolerance != protocol["checks"]["source_height_tolerance_m"]:
        raise ValueError("Source hold predicate differs from the frozen protocol")
    model = env.sim.mj_model
    names = {model.geom(i).name: i for i in range(model.ngeom)}
    hands = [names[f"robot/{side}_{part}_collision"]
             for side in ("left", "right") for part in ("hand", "wrist")]
    if case["disable_hand_contacts"]:
        # Read the compiled payload, not only the requested config. Explicit
        # pairs bypass bitmasks and would invalidate this negative control.
        if np.any(model.geom_contype[hands]) or np.any(model.geom_conaffinity[hands]) or \
                np.isin(model.pair_geom1, hands).any() or np.isin(model.pair_geom2, hands).any():
            raise ValueError("Compiled hand-contact removal is incomplete")
    return {**observed, "seed": cfg.seed, "clip_actions": wrapper.clip_actions,
            "max_episode_length": env.max_episode_length, "hand_geom_ids": hands,
            "negative_control": case["disable_hand_contacts"]}


def evaluate(source, output, protocol, case, manifest):
    import numpy as np
    import torch
    import mujoco

    from dexlab.amp_lift_record import (AmpEpisodeObserver, AmpLiftRecorder, host_tensor,
                                      single_world, save_model_snapshot)
    from dexlab.apple_admission import loaded_mujoco_library, record_native_file
    from dexlab.cloth_engines import package_identity
    from dexlab.libero_substeps import write_chunk
    from mjlab.utils.torch import configure_torch_backends
    from mjlab_g1.envs.g1_dualarm_rl_env import G1DualarmManagerBasedRlEnv
    from mjlab_g1.rl import RslRlVecEnvWrapper
    from mjlab_g1.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
    from rsl_rl.runners import OnPolicyRunner
    import mjlab_g1
    import rsl_rl

    for module, expected in ((mjlab_g1, source / "src/mjlab_g1"), (rsl_rl, source / "rsl_rl/rsl_rl")):
        if Path(module.__file__).resolve().parent != expected:
            raise ValueError(f"Imported source does not belong to the pinned checkout: {module.__name__}")
    if mujoco.mj_versionString() != protocol["runtime"]["mujoco"] or not torch.cuda.is_available():
        raise ValueError("The frozen native MuJoCo/CUDA runtime is unavailable")
    manifest["native_payload"] = {
        "mujoco_version": mujoco.mj_versionString(),
        "mujoco_sha256": record_native_file("mujoco", loaded_mujoco_library()),
        "package_code_sha256": {name: package_identity(name)["code_sha256"]
                                for name in ("mujoco", "mujoco-warp", "mjlab")},
        "torch_cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
        "gpu_capability": list(torch.cuda.get_device_capability(0)),
    }
    qualification = output / "probe-qualification.json"
    if qualification.exists() and manifest["native_payload"] != \
            json.loads(qualification.read_text())["native_payload"]:
        raise ValueError("Native payload or GPU changed after recorder qualification")
    configure_torch_backends()
    cfg = load_env_cfg(protocol["task"], play=True)
    cfg.scene.num_envs = 1
    cfg.seed = case["seed"]
    if case["disable_hand_contacts"]:
        disable_hands(cfg)
    agent_cfg = load_rl_cfg(protocol["task"])
    env = observer = recorder = None
    completed = False
    try:
        env = G1DualarmManagerBasedRlEnv(cfg=cfg, device="cuda:0", render_mode=None)
        wrapper = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        # The source wrapper performs the sole initial reset. No extra reset,
        # reseeding, joint writes or bootstrap changes are made here.
        manifest["effective_conditions"] = check_source_conditions(env, wrapper, case, protocol)
        (output / "environment-config.txt").write_text(repr(cfg) + "\n")
        (output / "agent-config.txt").write_text(repr(agent_cfg) + "\n")
        runner_cls = load_runner_cls(protocol["task"]) or OnPolicyRunner
        runner = runner_cls(wrapper, asdict(agent_cfg), device="cuda:0")
        runner.load(str(source / "models/dualarm.pt"), load_cfg={
            "actor": True, "critic": False, "optimizer": False,
            "iteration": False, "rnd": False, "discriminator": False,
        }, map_location="cuda:0")
        policy = runner.get_inference_policy(device="cuda:0")
        if case["record_substeps"]:
            recorder = AmpLiftRecorder(env.sim, output / "native")
        else:
            save_model_snapshot(env.sim, output / "native")
        observer = AmpEpisodeObserver(env)
        actions_dir = output / "actions"
        actions_dir.mkdir()
        obs = wrapper.get_observations().to("cuda:0")
        write_chunk(output / "initial-state.npz", [{
            "qpos": single_world(env.sim.wp_data.qpos), "qvel": single_world(env.sim.wp_data.qvel),
            "time": float(single_world(env.sim.wp_data.time)),
            "goal": host_tensor(env.trajectory_goal_pos_w),
            "root_pos_w": host_tensor(env.robot.data.root_link_pos_w),
            "initialization_classification": "Unclassified; actual state retained. Source RSI probability is not an observed label.",
        }])
        with torch.inference_mode():
            for index in range(case["actions"]):
                command = policy(obs)
                row = {
                    "action_index": index, "status": "started",
                    "policy_action": host_tensor(command),
                    "executed_action": host_tensor(torch.clamp(command, -wrapper.clip_actions, wrapper.clip_actions)),
                    "observations": {name: host_tensor(value) for name, value in obs.items()},
                }
                if not np.isfinite(row["policy_action"]).all():
                    write_chunk(actions_dir / f"action-{index:06d}.npz", [row])
                    raise ValueError("Nonfinite policy command")
                if recorder is not None:
                    recorder.start_action(index)
                try:
                    (next_obs, reward, dones, _), feedback = observer.step(wrapper, command)
                    row.update(status="completed", feedback=feedback, reward=host_tensor(reward),
                               dones=host_tensor(dones),
                               returned_observations={name: host_tensor(value) for name, value in next_obs.items()})
                    if feedback["automatic_reset"] != (index + 1 == 3000):
                        raise ValueError("Unexpected source reset boundary")
                    if feedback["assistance_scale"] != 0 or np.any(feedback["assist_force_frac"] != 0):
                        raise ValueError("Unexpected virtual assistance in the AMP play run")
                    obs = next_obs.to("cuda:0")
                except BaseException as error:
                    row.update(status="failed", error=f"{type(error).__name__}: {error}")
                    if observer.terminal is not None:
                        row["terminal_feedback_before_failed_reset"] = observer.terminal
                    raise
                finally:
                    write_chunk(actions_dir / f"action-{index:06d}.npz", [row])
                    if recorder is not None:
                        recorder.flush()
                manifest["completed_actions"] = index + 1
        completed = True
    finally:
        # Close hooks before the source environment; a failed action's native
        # prefix and pre-reset feedback remain in their original output.
        try:
            if recorder is not None:
                recorder.close(completed=completed)
        finally:
            if observer is not None:
                observer.close()
            if env is not None:
                env.close()


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--budget", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path,
                        help="The enclosing bounded_run.py receipt; qualification requires its final telemetry")
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    raw = Path(__file__).with_name("protocol.json").read_bytes()
    protocol = json.loads(raw)
    cases = {case["id"]: case for case in protocol["cases"]}
    if args.case not in cases:
        parser.error("Choose a named case from protocol.json")
    source = args.upstream.resolve(strict=True)
    output = args.output.resolve()
    protocol_sha = hashlib.sha256(raw).hexdigest()
    sys.path[:0] = [str(Path(__file__).resolve().parents[2] / "src"),
                   str(source / "src"), str(source / "rsl_rl")]
    from dexlab.migration_budget import MigrationBudget

    budget = MigrationBudget(args.budget)
    budget_manifest = json.loads((budget.root / "manifest.json").read_text())
    if budget_manifest["protocol_sha256"] != protocol_sha:
        parser.error("Budget and protocol differ; preserve the existing campaign")
    output.mkdir(parents=True, exist_ok=False)
    attempt = budget.reserve(args.case, {
        "pid": os.getpid(), "output": str(output),
        "process_start_ticks": Path("/proc/self/stat").read_text().split(") ", 1)[1].split()[19],
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "cgroup": Path("/proc/self/cgroup").read_text().strip(),
    }, timeout_s=protocol["repeat_plan"]["max_process_wall_s"])
    manifest = {
        "schema_version": 1, "case": cases[args.case], "protocol_sha256": protocol_sha,
        "budget_attempt": attempt, "status": "started", "completed_actions": 0,
        "runner_sha256": file_sha256(__file__), "training": False, "task_success": None,
        "python": sys.executable,
        "recorder_sha256": file_sha256(Path(__file__).resolve().parents[2] / "src/dexlab/amp_lift_record.py"),
        "resources_receipt": str(args.resources.resolve()),
        "cgroup": Path("/proc/self/cgroup").read_text().strip(),
    }
    path = output / "invocation.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    original_cwd = Path.cwd()
    try:
        if "dexlab-bounded-" not in manifest["cgroup"]:
            raise ValueError("AMP native evaluation requires the existing bounded runner")
        telemetry_path = args.resources.with_name(args.resources.name + ".cgroup.json")
        telemetry = json.loads(telemetry_path.read_text())
        cgroup_path = manifest["cgroup"].split("0::", 1)[1]
        if telemetry.get("state") != "running" or telemetry.get("cgroup_path") != "/sys/fs/cgroup" + cgroup_path:
            raise ValueError("Resource telemetry does not belong to this live bounded service")
        if telemetry.get("profile") != budget_manifest["resource_plan"]["profile"]:
            raise ValueError("Bounded service profile differs from the frozen native resource plan")
        checker = runpy.run_path(str(Path(__file__).with_name("qualify.py")))["check_gpu_resources"]
        gpu_budget = checker(telemetry, protocol["gpu_budget"])
        if os.environ.get("CUDA_VISIBLE_DEVICES") != gpu_budget["uuid"]:
            raise ValueError("Select the bounded GPU UUID explicitly through CUDA_VISIBLE_DEVICES")
        manifest["gpu_budget"] = gpu_budget
        manifest["source"] = source_identity(source, protocol)
        manifest["runtime"] = runtime_identity(protocol)
        if not args.case.startswith("probe-"):
            require_probe_qualification(budget, output, protocol_sha, manifest["source"], manifest["runtime"])
        # Source motion paths are relative to its project directory.
        os.chdir(source)
        evaluate(source, output, protocol, cases[args.case], manifest)
        manifest["status"] = "completed"
    except BaseException as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        os.chdir(original_cwd)
        evidence = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode()
        path.write_bytes(evidence)
        budget.finish(attempt, wall_s=time.monotonic() - started,
                      evidence_sha256=hashlib.sha256(evidence).hexdigest(),
                      outcome="recorded" if manifest["status"] == "completed" else "failed")


if __name__ == "__main__":
    main()
