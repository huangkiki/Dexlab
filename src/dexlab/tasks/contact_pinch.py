"""UniLab task for a fixed force protocol with measured cylinder/pad states."""

from dataclasses import dataclass, field
from pathlib import Path

import gymnasium as gym
import numpy as np
from unilab.base import registry
from unilab.base.base import ABEnv, EnvCfg
from unilab.base.np_env import NpEnvState

from dexlab.contact_pinch import DURATION, CylinderCase
from dexlab.contact_pinch_native import MuJoCoCylinder, PhysXCylinder, SuperDexCylinder

TASK = "DexLab-ContactCylinder-v0"


@registry.envcfg(TASK)
@dataclass
class ContactCylinderCfg(EnvCfg):
    sim_dt: float = 0.0005
    ctrl_dt: float = 0.0005
    max_episode_seconds: float = DURATION
    case: dict = field(default_factory=dict)
    output_dir: str = ""


class ContactCylinderEnv(ABEnv):
    def __init__(self, cfg, *, num_envs=1, backend_type="mujoco"):
        if num_envs != 1 or backend_type not in ("mujoco", "superdex", "isaacsim"):
            raise ValueError("One supported native cylinder fixture is required")
        self.case = CylinderCase(**cfg.case)
        if (
            cfg.sim_dt != self.case.timestep
            or cfg.ctrl_dt != self.case.timestep
            or cfg.max_episode_seconds != DURATION
            or not cfg.output_dir
        ):
            raise ValueError(
                "Task timing must match the fixed protocol and output must be explicit"
            )
        self._cfg, self.backend = cfg, backend_type
        self.native, self._state = None, None
        self.steps = 0
        self.started = False

    @property
    def cfg(self):
        return self._cfg

    @property
    def num_envs(self):
        return 1

    @property
    def obs_groups_spec(self):
        return {"obs": 40}

    @property
    def observation_space(self):
        return gym.spaces.Box(-np.inf, np.inf, (40,), np.float64)

    @property
    def action_space(self):
        return gym.spaces.Box(-np.inf, np.inf, (3, 3), np.float64)

    @property
    def state(self):
        return self._state

    def _observe(self, pose, velocity, time_s, **info):
        if not np.isfinite(pose).all() or not np.isfinite(velocity).all():
            raise RuntimeError("Nonfinite native state")
        self._state = NpEnvState(
            obs={"obs": np.r_[pose.ravel(), velocity.ravel(), time_s][None]},
            reward=np.zeros(1),
            terminated=np.array([self.steps >= self.case.steps]),
            truncated=np.zeros(1, dtype=bool),
            info={"pose": pose, "velocity": velocity, "time_s": time_s, **info},
        )
        return self._state

    def init_state(self):
        if self.started:
            raise RuntimeError(
                "Use a fresh environment/output for each evidence episode"
            )
        self.started = True
        output = Path(self.cfg.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        if any(
            (output / name).exists()
            for name in ("model.xml", "geometry.npz", "scene", "cylinder.obj")
        ):
            raise FileExistsError("Refusing to overwrite a native fixture")
        native_class = {
            "mujoco": MuJoCoCylinder,
            "superdex": SuperDexCylinder,
            "isaacsim": PhysXCylinder,
        }[self.backend]
        self.native = native_class(self.case, output)
        self.origin = self.native.clock()
        return self._observe(*self.native.observe(), 0.0, contact_known=False)

    reset = init_state

    def step(self, actions):
        if self.native is None or self.state.terminated[0]:
            raise RuntimeError("An unfinished native episode is required")
        force = np.asarray(actions)
        if (
            force.shape != (1, 3, 3)
            or not np.isfinite(force).all()
            or not np.array_equal(force[0], self.case.force(self.steps))
        ):
            raise ValueError("Actions must match the frozen world-COM force protocol")
        pose, velocity, contact, normal, raw, completed, status = self.native.step(
            force[0]
        )
        if not np.isfinite(contact).all() or not np.isfinite(normal).all():
            raise RuntimeError("Nonfinite native contact force")
        self.steps += 1
        time_s = self.native.clock() - self.origin
        if not np.isclose(time_s, self.steps * self.case.timestep, atol=1e-10, rtol=0):
            raise RuntimeError("Incorrect native timestep")
        return self._observe(
            pose,
            velocity,
            time_s,
            contact_force=contact,
            normal_force=normal,
            contacts=raw,
            contact_known=True,
            step_completed=completed,
            native_status=status,
        )

    def close(self):
        if self.native is not None:
            self.native.close()
        self.native, self._state = None, None


for backend in ("mujoco", "superdex", "isaacsim"):
    registry.register_env(TASK, ContactCylinderEnv, sim_backend=backend)
