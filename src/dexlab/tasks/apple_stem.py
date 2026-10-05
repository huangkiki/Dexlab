"""Registered UniLab environment for the native SDF apple-stem experiment."""

import json
import os
import time
from dataclasses import dataclass, field, replace
from importlib.metadata import version
from pathlib import Path

import gymnasium as gym
import numpy as np
from unilab.base import registry
from unilab.base.base import ABEnv, EnvCfg
from unilab.base.np_env import NpEnvState

from dexlab.episode import SCENE_LOCK
from dexlab.apple_admission import APPLE_PARAMETERS as PARAMETERS

TASK = "DexLab-AppleStem-v0"


@registry.envcfg(TASK)
@dataclass
class AppleStemCfg(EnvCfg):
    max_episode_seconds: float = 14.0
    output: str = ""
    headless: bool = True
    parameters: dict[str, float | str | None] = field(default_factory=dict)


class AppleStemEnv(ABEnv):
    """Single-scene experiment; no autoreset, reward shaping, or engine patches.

    Actions are absolute joint targets in radians. Observations contain measured
    joint angles, privileged apple pose (xyz/xyzw), and elapsed episode time.
    A coroutine retains the native scene between calls; each send advances
    exactly one physics step and records the independent contact evidence.
    """

    def __init__(self, cfg, *, num_envs=1, backend_type="mujoco"):
        if num_envs != 1:
            raise ValueError(
                "This native SDF task supports exactly one scene per process"
            )
        if backend_type not in ("mujoco", "superdex"):
            raise ValueError(f"Unsupported backend: {backend_type}")
        if cfg.max_episode_seconds != 14:
            raise ValueError("The audited episode duration is 14 seconds")
        if set(cfg.parameters) - set(PARAMETERS):
            raise ValueError("Unknown physics parameter override")
        dt = cfg.parameters.get("timestep")
        if dt is None:
            dt = 0.0005 if backend_type == "mujoco" else 0.002
        if dt not in (0.002, 0.001, 0.0005, 0.00025, 0.000125):
            raise ValueError("Unsupported benchmark timestep")
        if (cfg.sim_dt, cfg.ctrl_dt) not in ((0.01, 0.01), (dt, dt)):
            raise ValueError(
                f"This episode requires sim_dt = ctrl_dt = {dt}; set timestep overrides in parameters"
            )
        self._cfg = replace(cfg, sim_dt=dt, ctrl_dt=dt)
        self.backend_type = backend_type
        self._episode = None
        self._frame = None
        self._state = None
        self._steps = 0
        self._owns_scene = False

    @property
    def cfg(self):
        return self._cfg

    @property
    def num_envs(self):
        return 1

    @property
    def state(self):
        return self._state

    def _require_frame(self):
        if self._frame is None:
            raise RuntimeError(
                "Call init_state() before accessing the native task layout"
            )
        return self._frame

    @property
    def obs_groups_spec(self):
        return {"obs": len(self._require_frame().joint_names) + 8}

    @property
    def observation_space(self):
        return gym.spaces.Box(
            -np.inf, np.inf, (self.obs_groups_spec["obs"],), np.float64
        )

    @property
    def action_space(self):
        return gym.spaces.Box(
            -np.inf, np.inf, (len(self._require_frame().joint_names),), np.float64
        )

    def _state_from_frame(self):
        frame = self._require_frame()
        obs = np.r_[frame.joint_position, frame.apple_pose, frame.time][None, :]
        if not np.isfinite(obs).all():
            raise RuntimeError("Nonfinite native observation")
        done = frame.summary is not None
        self._state = NpEnvState(
            obs={"obs": obs},
            reward=np.zeros(1),
            terminated=np.array([done]),
            truncated=np.zeros(1, dtype=bool),
            info={
                "steps": np.array([self._steps]),
                "joint_names": frame.joint_names,
                "scripted_target": frame.target[None, :].copy(),
                "summary": frame.summary,
                "observation_source": "measured joints, privileged apple pose, time",
            },
        )
        return self._state

    def init_state(self):
        return self.reset()

    def reset(self):
        """Rebuild and settle the scene; never reuse the previous apple state."""
        self.close()
        if not SCENE_LOCK.acquire(blocking=False):
            raise RuntimeError(
                "Close the active native scene before resetting another environment"
            )
        self._owns_scene = True
        try:
            return self._reset_scene()
        except BaseException:
            self.close()
            raise

    def _reset_scene(self):
        os.environ["SUPERDEX_PRECISION"] = "fp64"
        from wuji_stem_grasp import episode, parse_args

        argv = ["--backend", self.backend_type, "--stem-only"]
        if self.cfg.headless:
            argv.append("--headless")
        if self.cfg.output:
            argv.extend(["--output", self.cfg.output])
        for key, value in self.cfg.parameters.items():
            if value is not None:
                argv.append(f"--{key.replace('_', '-')}={value}")
        args = parse_args(argv)
        self._episode = episode(args)
        self._steps = 0
        self._frame = next(self._episode)
        metadata = {
            "task": TASK,
            "unilab": version("unilab"),
            "unisim_core": version("unisim-core"),
            "backend": self.backend_type,
            "execution": "DexLab native scene coroutine; not UniSim built-in backend",
            "dt_s": self.cfg.sim_dt,
            "duration_s": 14,
            "joint_names": self._frame.joint_names,
            "action": "absolute joint targets (rad), one native step per env.step",
            "observation": ["actual joint angles", "privileged apple xyz/xyzw", "time"],
            "parameters": {key: getattr(args, key) for key in PARAMETERS},
        }
        (Path(args.output) / "unilab.json").write_text(
            json.dumps(metadata, indent=2) + "\n"
        )
        return self._state_from_frame()

    def step(self, actions):
        frame = self._require_frame()
        if frame.summary is not None or self._episode is None:
            raise RuntimeError("Episode ended; call reset() before stepping again")
        action = np.asarray(actions, dtype=np.float64)
        expected = (1, len(frame.joint_names))
        if action.shape != expected or not np.isfinite(action).all():
            raise ValueError(
                f"Expected finite absolute joint targets of shape {expected}"
            )
        try:
            self._frame = self._episode.send(action[0].copy())
            self._steps += 1
            state = self._state_from_frame()
            if self._frame.summary is not None:
                self._release_scene()
            return state
        except BaseException:
            self.close()
            raise

    def _release_scene(self):
        try:
            if self._episode is not None:
                self._episode.close()
        finally:
            self._episode = None
            if self._owns_scene:
                self._owns_scene = False
                SCENE_LOCK.release()

    def close(self):
        self._release_scene()
        self._frame = None
        self._state = None


for backend in ("mujoco", "superdex"):
    registry.register_env(TASK, AppleStemEnv, sim_backend=backend)


def main():
    os.environ["SUPERDEX_PRECISION"] = "fp64"
    from wuji_stem_grasp import parse_args

    args = parse_args()
    if args.sequence or args.seconds != 14:
        raise SystemExit("UniLab task supports the 14-second stem grasp only")
    env = registry.make(
        TASK,
        sim_backend=args.backend,
        env_cfg_override={
            "output": str(args.output),
            "headless": args.headless,
            "parameters": {key: getattr(args, key) for key in PARAMETERS},
        },
    )
    from dexlab.apple_admission import observe_runtime, apple_profile
    from dexlab.benchmark import source_hashes, write_json

    qualification = None
    if os.environ.get("DEXLAB_MUJOCO_PROFILE", "").startswith("qualification-"):
        qualification = {
            "schema_version": 1, "backend": args.backend,
            "source_sha256": source_hashes(), "runtime": observe_runtime(),
            "profile": apple_profile(args.backend, {key: getattr(args, key) for key in PARAMETERS}),
        }
    started = time.perf_counter()
    timing = {"schema_version": 1, "backend": args.backend,
              "headless": args.headless, "preparation_seconds": None,
              "episode_and_recording_seconds": None,
              "rendering": "disabled" if args.headless else "included_in_episode",
              "scope": "Preparation includes settling/planning/model build. Episode includes control, native steps, recording and internal scoring. Native step-only time is in engine.json; independent verification is timed separately."}
    try:
        state = env.init_state()
        prepared = time.perf_counter()
        timing["preparation_seconds"] = prepared - started
        while not state.terminated[0]:
            state = env.step(state.info["scripted_target"])
        timing["episode_and_recording_seconds"] = time.perf_counter() - prepared
        if not state.info["summary"]["passed"]:
            raise SystemExit("Stem grasp verification failed")
    finally:
        env.close()
        timing["total_task_seconds"] = time.perf_counter() - started
        if Path(args.output).is_dir():
            (Path(args.output) / "runtime-timing.json").write_text(json.dumps(timing, indent=2))
            if qualification is not None:
                qualification["source_unchanged"] = source_hashes() == qualification["source_sha256"]
                qualification["runtime_unchanged"] = observe_runtime() == qualification["runtime"]
                write_json(Path(args.output) / "qualification-observation.json", qualification)
                if not qualification["source_unchanged"] or not qualification["runtime_unchanged"]:
                    raise RuntimeError("Source or native runtime changed during qualification episode")



if __name__ == "__main__":
    main()
