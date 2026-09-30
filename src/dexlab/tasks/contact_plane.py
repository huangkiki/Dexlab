"""UniLab stepwise ownership of a measured, unactuated contact fixture."""

from dataclasses import dataclass, field
from pathlib import Path

import gymnasium as gym
import numpy as np
from unilab.base import registry
from unilab.base.base import ABEnv, EnvCfg
from unilab.base.np_env import NpEnvState

from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import MuJoCoPlane, PhysXPlane, SuperDexPlane

TASK = "DexLab-ContactPlane-v0"


@registry.envcfg(TASK)
@dataclass
class ContactPlaneCfg(EnvCfg):
    sim_dt: float = 0.0005
    ctrl_dt: float = 0.0005
    max_episode_seconds: float = 0.5
    case: dict = field(default_factory=dict)
    output_dir: str = ""
    normal_parameters: dict = field(default_factory=dict)


class ContactPlaneEnv(ABEnv):
    """One measured step per call; no runtime control or object pose rewriting.

    The native adapters own the physics. PhysX uses the qualified UniSim adapter;
    MuJoCo/SuperDex use their official APIs. This is not a claim that UniSim's
    built-in robot backends implement this observation contract.
    """

    def __init__(self, cfg, *, num_envs=1, backend_type="mujoco"):
        if num_envs != 1 or backend_type not in ("mujoco", "superdex", "isaacsim"):
            raise ValueError("A single supported native contact fixture is required")
        self.case = PlaneCase(**cfg.case)
        if (
            cfg.sim_dt != self.case.timestep
            or cfg.ctrl_dt != self.case.timestep
            or cfg.max_episode_seconds != self.case.duration
            or not cfg.output_dir
        ):
            raise ValueError(
                "Task timing must match PlaneCase and output_dir must be explicit"
            )
        self._cfg, self.backend = cfg, backend_type
        self.native, self._state = None, None
        self.steps = 0
        self._started = False

    @property
    def cfg(self):
        return self._cfg

    @property
    def num_envs(self):
        return 1

    @property
    def obs_groups_spec(self):
        return {"obs": 14}

    @property
    def observation_space(self):
        return gym.spaces.Box(-np.inf, np.inf, (14,), np.float64)

    @property
    def action_space(self):
        return gym.spaces.Box(-np.inf, np.inf, (0,), np.float64)

    @property
    def state(self):
        return self._state

    def _observe(self, pose, velocity, time_s, **info):
        if not np.isfinite(pose).all() or not np.isfinite(velocity).all():
            raise RuntimeError("Native contact fixture state became nonfinite")
        self._state = NpEnvState(
            obs={"obs": np.r_[pose, velocity, time_s][None]},
            reward=np.zeros(1),
            terminated=np.array([self.steps >= self.case.steps]),
            truncated=np.zeros(1, dtype=bool),
            info={"pose": pose, "velocity": velocity, "time_s": time_s, **info},
        )
        return self._state

    def init_state(self):
        if self._started:
            raise RuntimeError(
                "Each evidence episode requires a fresh environment and output directory"
            )
        self._started = True
        output = Path(self.cfg.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        if any(
            (output / name).exists() for name in ("model.xml", "geometry.npz", "scene")
        ):
            raise FileExistsError("Refusing to overwrite an existing native scene")
        native_class = {
            "mujoco": MuJoCoPlane,
            "superdex": SuperDexPlane,
            "isaacsim": PhysXPlane,
        }[self.backend]
        self.native = native_class(
            self.case, output, normal_parameters=self.cfg.normal_parameters
        )
        try:
            for _ in range(round(self.case.settle / self.case.timestep)):
                self.native.step()
            self.native.start()
            self._clock_origin = self.native.clock()
            return self._observe(*self.native.observe(), 0.0, contact_known=False)
        except Exception:
            self.close()
            raise

    reset = init_state

    def step(self, actions):
        if self.native is None or self.state.terminated[0]:
            raise RuntimeError("A live, unfinished contact episode is required")
        if np.asarray(actions).shape != (1, 0):
            raise ValueError(
                "This unactuated fixture accepts only an empty action of shape (1,0)"
            )
        return self._advance()

    def _advance(self, external_force=None):
        if self.native is None or self.state.terminated[0]:
            raise RuntimeError("A live, unfinished contact episode is required")
        pose, velocity, force, contacts, completed, status = self.native.step(
            external_force
        )
        if not np.isfinite(force).all():
            raise RuntimeError("Native contact force became nonfinite")
        self.steps += 1
        time_s = self.native.clock() - self._clock_origin
        if not np.isclose(time_s, self.steps * self.case.timestep, atol=1e-10, rtol=0):
            raise RuntimeError("Native clock did not advance by the protocol timestep")
        return self._observe(
            pose,
            velocity,
            time_s,
            contact_force=force,
            contacts=contacts,
            contact_known=True,
            step_completed=completed,
            native_status=status,
        )

    def close(self):
        if self.native is not None:
            self.native.close()
        self.native, self._state = None, None


for backend in ("mujoco", "superdex", "isaacsim"):
    registry.register_env(TASK, ContactPlaneEnv, sim_backend=backend)


INDENT_TASK = "DexLab-ContactIndent-v0"


@registry.envcfg(INDENT_TASK)
@dataclass
class ContactIndentCfg(ContactPlaneCfg):
    max_force_n: float = 40.0


class ContactIndentEnv(ContactPlaneEnv):
    """Same measured pad/plane scene with an explicit bounded vertical COM force."""

    def __init__(self, cfg, **kwargs):
        super().__init__(cfg, **kwargs)
        if self.case.initial_speed != 0 or self.case.friction != 0:
            raise ValueError(
                "The indentation protocol requires zero initial speed and friction"
            )
        if not np.isfinite(cfg.max_force_n) or cfg.max_force_n <= 0:
            raise ValueError("A finite positive force limit is required")

    @property
    def action_space(self):
        return gym.spaces.Box(
            -self.cfg.max_force_n, self.cfg.max_force_n, (3,), np.float64
        )

    def step(self, actions):
        force = np.asarray(actions, dtype=float)
        if (
            force.shape != (1, 3)
            or not np.isfinite(force).all()
            or np.any(force[0, :2])
            or np.max(np.abs(force)) > self.cfg.max_force_n
        ):
            raise ValueError(
                "Expected a bounded vertical world-frame force of shape (1,3)"
            )
        return self._advance(force[0])


for backend in ("mujoco", "superdex", "isaacsim"):
    registry.register_env(INDENT_TASK, ContactIndentEnv, sim_backend=backend)
