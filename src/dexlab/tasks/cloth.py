"""Measured cloth states and force boundary conditions through UniLab."""

from dataclasses import dataclass, field

import gymnasium as gym
import numpy as np
from unilab.base import registry
from unilab.base.base import ABEnv, EnvCfg
from unilab.base.np_env import NpEnvState

from dexlab.cloth import ClothCase
from dexlab.cloth_engines import MuJoCoCloth, NewtonCloth
from dexlab.cloth_superdex import SuperDexCloth

TASK = "DexLab-Cloth-v0"


@registry.envcfg(TASK)
@dataclass
class ClothCfg(EnvCfg):
    sim_dt: float = 0.0005
    ctrl_dt: float = 0.0005
    max_episode_seconds: float = 3.0
    case: dict = field(default_factory=dict)
    solver: str = "xpbd"
    device: str = "cpu"
    iterations: int = 10


class ClothEnv(ABEnv):
    """One native step per call; prescribed forces are not learned actions.

    DexLab owns these native scenes. This is a UniLab task registration, not a
    claim that UniSim's built-in robot adapters support cloth state or forces.
    """

    def __init__(self, cfg, *, num_envs=1, backend_type="mujoco"):
        if num_envs != 1 or backend_type not in ("mujoco", "newton", "superdex"):
            raise ValueError("A single MuJoCo, Newton, or SuperDex cloth scene is required")
        if not np.isfinite(cfg.sim_dt) or cfg.sim_dt <= 0 or cfg.ctrl_dt != cfg.sim_dt:
            raise ValueError("sim_dt and ctrl_dt must match and be positive")
        steps = 3 / cfg.sim_dt
        if cfg.max_episode_seconds != 3 or not np.isclose(
            steps, round(steps), rtol=0, atol=1e-8
        ):
            raise ValueError("The timestep must divide the 3-second protocol")
        if type(cfg.iterations) is not int or cfg.iterations < 1:
            raise ValueError("A positive integer iteration limit is required")
        self._cfg = cfg
        self.case = ClothCase(**cfg.case)
        self.backend = backend_type
        self.native = None
        self._state = None
        self.steps = 0

    @property
    def cfg(self):
        return self._cfg

    @property
    def num_envs(self):
        return 1

    @property
    def obs_groups_spec(self):
        return {"obs": self.case.nx * self.case.ny * 6 + 1}

    @property
    def observation_space(self):
        return gym.spaces.Box(
            -np.inf, np.inf, (self.obs_groups_spec["obs"],), np.float64
        )

    @property
    def action_space(self):
        return gym.spaces.Box(
            -np.inf, np.inf, (self.case.nx * self.case.ny, 3), np.float64
        )

    @property
    def state(self):
        return self._state

    def _observe(self):
        positions, velocities = self.native.observe()
        if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
            raise RuntimeError("Native cloth state became nonfinite")
        self._state = NpEnvState(
            obs={
                "obs": np.r_[
                    positions.ravel(), velocities.ravel(), self.steps * self.cfg.sim_dt
                ][None]
            },
            reward=np.zeros(1),
            terminated=np.array([self.steps >= round(3 / self.cfg.sim_dt)]),
            truncated=np.zeros(1, dtype=bool),
            info={
                "positions": positions,
                "velocities": velocities,
                "time_s": self.steps * self.cfg.sim_dt,
                "observation_source": self.native.metadata.get(
                    "velocity_observation", "actual native particle positions and velocities"
                ),
            },
        )
        return self._state

    def init_state(self):
        self.close()
        kwargs = dict(device=self.cfg.device, iterations=self.cfg.iterations)
        if self.backend == "mujoco":
            self.native = MuJoCoCloth(self.case, self.cfg.sim_dt, **kwargs)
        elif self.backend == "superdex":
            self.native = SuperDexCloth(self.case, self.cfg.sim_dt, **kwargs)
        else:
            self.native = NewtonCloth(
                self.case, self.cfg.sim_dt, solver=self.cfg.solver, **kwargs
            )
        self.steps = 0
        return self._observe()

    reset = init_state

    def step(self, actions):
        if self.native is None or self.state.terminated[0]:
            raise RuntimeError("Call init_state() to start a new cloth episode")
        forces = np.asarray(actions, dtype=float)
        if (
            forces.shape != (1, self.case.nx * self.case.ny, 3)
            or not np.isfinite(forces).all()
        ):
            raise ValueError(
                "Expected finite per-vertex forces with shape (1, vertices, 3)"
            )
        if np.any(forces[0, self.case.pins]):
            raise ValueError(
                "External loads on fixed vertices are outside this protocol"
            )
        self.native.step(forces[0])
        self.steps += 1
        return self._observe()

    def close(self):
        if self.native is not None and self.backend == "superdex":
            self.native.close()
        self.native = None
        self._state = None


for backend in ("mujoco", "newton", "superdex"):
    registry.register_env(TASK, ClothEnv, sim_backend=backend)
