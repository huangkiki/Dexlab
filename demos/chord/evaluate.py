#!/usr/bin/env python3
"""Reload one locally trained Sharpa checkpoint and record finite native steps.

Use the pinned CHORD runtime under research_guard and a verified resource
envelope. This evaluator preserves the upstream first-frame reset and VOC-off
contract. The optional recorder must qualify against a separate process with
the recorder disabled before its pre-reset records support task conclusions.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from prepare import ASSETS, HERE, sha256, source_check
from runtime import identity as runtime_identity


def disable_initial_reset_assistance(command):
    """Remove upstream's hard-coded reset scale before the first policy action.

    The pinned command resets the per-environment scale to one even with a
    zero curriculum target and zero decay steps. Its first command update is
    after physics. Do not advance physics to make this configuration effective.
    """
    if (command.cfg.initial_virtual_object_control_curriculum_scale != 0.0
            or command.cfg.virtual_object_control_decay_steps != 0
            or bool(command.virtual_object_controller_scale_factor.ne(0).any())):
        raise ValueError("Evaluation requires a zero VOC target and zero decay steps")
    reset_scale = command.virtual_object_controller_scale_factor_per_env.tolist()
    command.virtual_object_controller_scale_factor_per_env.zero_()
    return reset_scale


def main():
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("tissue-box", "synthbox-smoke"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--record", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.steps < 1 or args.seed < 0:
        parser.error("steps must be positive and seed must be nonnegative")
    manifest = json.loads((HERE / "tasks.json").read_text())
    task = next(t for t in manifest["tasks"] if t["id"] == args.task)
    source = args.source.resolve()
    identity = source_check(source, manifest["upstream"]["commit"])
    if identity["status"] != "pinned-clean":
        raise ValueError(f"Unqualified source: {identity}")
    sys.path.insert(0, str(source / "robotic_grounding/source/robotic_grounding"))
    data_root = (args.data_root or source / ASSETS / "human_motion_data").resolve()
    os.environ["HUMAN_MOTION_DATA_DIR"] = str(data_root)
    attempt = args.attempt.resolve()
    attempt.mkdir(parents=True, exist_ok=False)
    checkpoint = attempt / "checkpoint.pt"
    shutil.copyfile(args.checkpoint, checkpoint)
    checkpoint_hash = sha256(checkpoint)
    if checkpoint_hash != sha256(args.checkpoint):
        raise ValueError("Checkpoint changed during copy")
    invocation = {"status": "starting", "task": args.task, "seed": args.seed,
                  "steps_requested": args.steps, "recorder": args.record,
                  "checkpoint_sha256": checkpoint_hash, "source": identity,
                  "manifest_sha256": sha256(HERE / "tasks.json"),
                  "adapter_sha256": {name: sha256(HERE / name)
                                     for name in ("evaluate.py", "record.py", "motion.py", "prepare.py", "runtime.py")}}
    invocation_path = attempt / "invocation.json"
    invocation_path.write_text(json.dumps(invocation, indent=2) + "\n")
    app = None
    env = None
    try:
        app = AppLauncher(args).app
        import gymnasium as gym
        import torch
        from rsl_rl.runners import OnPolicyRunner
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from isaaclab_tasks.utils import load_cfg_from_registry
        from isaaclab.utils.io import dump_yaml
        import robotic_grounding.tasks  # noqa: F401
        from robotic_grounding.tasks.scene_utils import SceneConfig, apply_scene_config
        from motion import load
        from record import NativeRecorderCfg, json_value

        invocation["motion"] = load(data_root / task["partition"])
        invocation["runtime"] = runtime_identity()
        invocation["packages"] = invocation["runtime"]["packages"]
        env_cfg = load_cfg_from_registry("Sharpa-V2D-v0", "env_cfg_entry_point")
        agent_cfg = load_cfg_from_registry("Sharpa-V2D-v0", "rsl_rl_cfg_entry_point")
        env_cfg.scene.num_envs = 1
        env_cfg.seed = agent_cfg.seed = args.seed
        if args.device is not None:
            env_cfg.sim.device = agent_cfg.device = args.device
        env_cfg.motion_file = str(data_root / task["partition"])
        scene = SceneConfig.from_motion_file(env_cfg.motion_file)
        apply_scene_config(env_cfg, scene, use_primitive_urdfs=task["kind"] == "synthetic-smoke")
        # The evaluation contract removes the curriculum, so only initial
        # reward weights apply; reward is recorded but is not our task score.
        for override in task["reward_overrides"]:
            key, value = override.split("=", 1)
            if key.startswith("env.rewards."):
                _, _, name, attribute = key.split(".")
                setattr(getattr(env_cfg.rewards, name), attribute, float(value))
        command_cfg = env_cfg.commands.dual_hands_object_tracking_command
        command_cfg.always_reset_to_first_frame = True
        command_cfg.initial_virtual_object_control_curriculum_scale = 0.0
        command_cfg.virtual_object_control_decay_steps = 0
        env_cfg.curriculum = None
        env_cfg.log_dir = str(attempt)
        if args.record:
            env_cfg.recorders = NativeRecorderCfg()
            env_cfg.recorders.native.path = str(attempt / "native.jsonl")
        dump_yaml(str(attempt / "env.yaml"), env_cfg)
        dump_yaml(str(attempt / "agent.yaml"), agent_cfg)
        env = RslRlVecEnvWrapper(gym.make("Sharpa-V2D-v0", cfg=env_cfg), clip_actions=agent_cfg.clip_actions)
        native = env.unwrapped
        command = native.command_manager.get_term("dual_hands_object_tracking_command")
        reset_scale = disable_initial_reset_assistance(command)
        import omni.kit.app
        import omni.usd
        from pxr import Usd, UsdPhysics

        manager = omni.kit.app.get_app().get_extension_manager()
        invocation["native_identity"] = {
            "usd_version": Usd.GetVersion(),
            "extension_ids": {name: manager.get_enabled_extension_id(name)
                              for name in ("omni.physx", "omni.physx.tensors", "isaacsim.asset.importer.urdf")},
            "physx_core_version": None,
            "physx_core_version_status": "not_exposed_by_this_readback; extension IDs are not core versions",
            "device": str(native.device),
            "torch_default_dtype": str(torch.get_default_dtype()),
            "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        }
        invocation["native_physics_scenes"] = {
            str(prim.GetPath()): {attribute.GetName(): str(attribute.Get())
                                for attribute in prim.GetAttributes()}
            for prim in omni.usd.get_context().get_stage().Traverse()
            if prim.IsA(UsdPhysics.Scene)
        }
        invocation["timing"] = {"physics_dt_s": native.physics_dt,
                                "control_dt_s": native.step_dt,
                                "motion_speed": command.cfg.motion_speed,
                                "resampled_frames": command.retargeted_horizon}
        invocation["assistance"] = {"upstream_initial_reset_scale": reset_scale,
                                    "initial_voc_scale": command.virtual_object_controller_scale_factor_per_env.tolist(),
                                    "initial_reset_correction": "zero per-env VOC scale before first action; no physics advance",
                                    "curriculum": None, "reset_to_first_frame": True}
        invocation["signal_epochs"] = {
            "native_state": "post control step, before reset and reference advance",
            "contact_force": "native sensor history at post control step; N in world frame",
            "virtual_control": "applied body-frame force/torque command at each physics substep; not measured contact",
            "contact_position": "zero fill only where contact_position_valid is false",
            "missing_signals": ["tangential contact force decomposition", "hardware forces", "material calibration"]}
        invocation["contact_sensors"] = {
            name: {"history_length": sensor.cfg.history_length,
                   "update_period_s": sensor.cfg.update_period,
                   "filter_prim_paths_expr": sensor.cfg.filter_prim_paths_expr}
            for name, sensor in native.scene.sensors.items()}
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(str(checkpoint))
        policy = runner.get_inference_policy(device=native.device)
        policy_nn = getattr(runner.alg, "policy", None)
        if policy_nn is None:
            policy_nn = runner.alg.actor_critic
        obs = env.get_observations()
        # The same light observer runs in both parity processes. It captures
        # returned states (which may be reset); native.jsonl captures pre-reset.
        with (attempt / "trajectory.jsonl").open("x") as stream:
            for step in range(args.steps):
                if not app.is_running():
                    raise RuntimeError("Simulator stopped before the finite step budget")
                if bool(command.virtual_object_controller_scale_factor_per_env.ne(0).any()):
                    raise RuntimeError("VOC assistance became nonzero before a policy action")
                with torch.inference_mode():
                    actions = policy(obs)
                    obs, reward, dones, _ = env.step(actions)
                    policy_nn.reset(dones)
                row = {"step": step, "action": actions, "observations": obs,
                       "reward": reward, "done": dones,
                       "object_position_e_after_reset": command.object_position_e,
                       "object_wxyz_e_after_reset": command.object_orientation_e}
                stream.write(json.dumps(json_value(row), allow_nan=False) + "\n")
                stream.flush()
        invocation.update(status="completed", steps_completed=args.steps)
    except BaseException as error:
        invocation.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            if env is not None:
                env.close()
        finally:
            invocation_path.write_text(json.dumps(invocation, indent=2, allow_nan=False) + "\n")
            if app is not None:
                app.close()


if __name__ == "__main__":
    main()
