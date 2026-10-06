"""Independent force-driven indentation/unloading protocol and measurements."""

from dataclasses import dataclass

import numpy as np

from dexlab.contact_plane import PlaneCase
from dexlab.physx_baseline import box_plane_clearance


@dataclass(frozen=True)
class IndentCase:
    name: str = "dev-indent"
    mass: float = 0.2
    half_size: float = 0.02
    gravity: float = 9.81
    timestep: float = 0.0005
    settle: float = 0.2
    duration: float = 1.5
    controller_period: float = 0.001
    kp: float = 20000.0
    kd: float = 126.49110640673517
    max_force: float = 40.0

    def __post_init__(self):
        self.plane()
        extra = [self.controller_period, self.kp, self.kd, self.max_force]
        if not np.isfinite(extra).all() or min(extra) <= 0:
            raise ValueError("Finite positive control parameters are required")
        ratio = self.controller_period / self.timestep
        if ratio < 1 or not np.isclose(ratio, round(ratio), atol=1e-8, rtol=0):
            raise ValueError("Physics timestep must divide the fixed controller period")

    def plane(self):
        return PlaneCase(
            name=self.name,
            mass=self.mass,
            half_size=self.half_size,
            gravity=self.gravity,
            timestep=self.timestep,
            settle=self.settle,
            duration=self.duration,
            initial_speed=0,
            friction=0,
        )

    @property
    def steps(self):
        return self.plane().steps

    def target(self, time_s):
        knots = (
            np.array([0, 0.15, 0.30, 0.50, 0.65, 0.85, 1.0, 1.20, 1.50])
            * self.duration
            / 1.5
        )
        offsets = [0, 0.001, 0.001, -0.0001, -0.0001, -0.0003, -0.0003, 0.001, 0.001]
        return self.half_size + np.interp(time_s, knots, offsets)

    def command(self, step, pose, velocity, previous):
        """PD force from actual pre-step state, held at a fixed physical rate."""
        if step % round(self.controller_period / self.timestep):
            return previous.copy()
        force = (
            self.mass * self.gravity
            + self.kp * (self.target(step * self.timestep) - pose[2])
            - self.kd * velocity[2]
        )
        return np.array(
            [0, 0, np.clip(force, -self.max_force, self.max_force)], dtype=np.float32
        )


# Declared engineering checks for the fixture, not calibrated material accuracy.
LIMITS = {
    "penetration_m": 0.001,
    "momentum_peak_weight_ratio": 0.05,
    "lateral_drift_m": 0.001,
    "orientation_change_rad": 0.05,
    "released_clearance_m": 0.0005,
    "released_contact_force_n": 0.01,
    "minimum_loaded_force_weight_ratio": 1.25,
    "command_rounding_n": 2e-6,
    "normal_tension_n": 1e-6,
    "stiffness_resolution_m": 1e-9,
}


def score(case, data):
    n = case.steps
    shapes = {
        "time": (n + 1,),
        "pose": (n + 1, 7),
        "velocity": (n + 1, 6),
        "contact_force": (n, 3),
        "external_force": (n, 3),
        "target_height": (n,),
        "contact_known": (n,),
        "step_completed": (n,),
    }
    checks = {
        "complete_shapes": all(
            k in data and np.shape(data[k]) == shape for k, shape in shapes.items()
        )
    }
    result = {
        "passed": False,
        "checks": checks,
        "metrics": {},
        "scope": "Force-driven response measurement and release; not matched material accuracy",
    }
    if not checks["complete_shapes"]:
        return result
    checks.update(
        finite_record=all(np.isfinite(data[k]).all() for k in shapes),
        complete_contact_coverage=bool(
            data["contact_known"].dtype == bool and data["contact_known"].all()
        ),
        native_steps_completed=bool(
            data["step_completed"].dtype == bool and data["step_completed"].all()
        ),
        uniform_time_grid=bool(
            np.allclose(
                data["time"], np.arange(n + 1) * case.timestep, atol=1e-10, rtol=0
            )
        ),
    )
    if not all(checks.values()):
        return result
    pose, vel, force, external = (
        data["pose"],
        data["velocity"],
        data["contact_force"],
        data["external_force"],
    )
    try:
        clearance = box_plane_clearance(pose, case.half_size)
    except ValueError:
        checks["unit_quaternions"] = False
        return result
    checks["unit_quaternions"] = True
    command = np.zeros(3, dtype=np.float32)
    commands = []
    for step in range(n):
        command = case.command(step, pose[step], vel[step], command)
        commands.append(command.copy())
    checks["declared_feedback_and_control_period"] = bool(
        np.allclose(external, commands, atol=LIMITS["command_rounding_n"], rtol=0)
    )
    checks["declared_targets"] = bool(
        np.allclose(
            data["target_height"],
            case.target(np.arange(n) * case.timestep),
            atol=1e-12,
            rtol=0,
        )
    )
    checks["force_limit"] = bool(
        np.max(np.abs(external)) <= case.max_force + LIMITS["command_rounding_n"]
    )
    residual = (
        case.mass * np.diff(vel[:, :3], axis=0) / case.timestep - force - external
    )
    residual[:, 2] += case.mass * case.gravity
    momentum_ratio = np.linalg.norm(residual, axis=1) / (case.mass * case.gravity)
    phase = data["time"][1:] / case.duration * 1.5
    loaded = (phase > 0.96) & (phase <= 1.0)
    released = phase > 1.35
    angle = 2 * np.arccos(np.clip(np.abs(pose[:, 3:] @ pose[0, 3:]), 0, 1))
    penetration = np.maximum(-clearance, 0)
    lateral = np.linalg.norm(pose[:, :2] - pose[0, :2], axis=1)
    checks.update(
        momentum_balance=bool(
            momentum_ratio.max() < LIMITS["momentum_peak_weight_ratio"]
        ),
        bounded_penetration=bool(penetration.max() < LIMITS["penetration_m"]),
        vertical_fixture=bool(
            lateral.max() < LIMITS["lateral_drift_m"]
            and angle.max() < LIMITS["orientation_change_rad"]
        ),
        compression_measured=bool(
            force[loaded, 2].mean()
            > LIMITS["minimum_loaded_force_weight_ratio"] * case.mass * case.gravity
        ),
        no_tensile_contact=bool(force[:, 2].min() >= -LIMITS["normal_tension_n"]),
        fully_unloaded=bool(
            clearance[1:][released].min() > LIMITS["released_clearance_m"]
            and np.linalg.norm(force[released], axis=1).max()
            < LIMITS["released_contact_force_n"]
        ),
    )
    plateaus = []
    for start, end in ((0.61, 0.65), (0.96, 1.0)):
        window = (phase > start) & (phase <= end)
        plateaus.append(
            {
                "mean_signed_indentation_m": float(-clearance[1:][window].mean()),
                "mean_normal_force_n": float(force[window, 2].mean()),
                "normal_force_std_n": float(force[window, 2].std()),
            }
        )
    dx = (
        plateaus[1]["mean_signed_indentation_m"]
        - plateaus[0]["mean_signed_indentation_m"]
    )
    df = plateaus[1]["mean_normal_force_n"] - plateaus[0]["mean_normal_force_n"]
    stiffness = df / dx if dx > LIMITS["stiffness_resolution_m"] else None
    result["metrics"] = {
        "maximum_penetration_m": float(penetration.max()),
        "penetration_over_limit_sample_duration_s": float(
            np.count_nonzero(penetration[1:] >= LIMITS["penetration_m"]) * case.timestep
        ),
        "maximum_momentum_residual_weight_ratio": float(momentum_ratio.max()),
        "maximum_normal_force_n": float(force[:, 2].max()),
        "released_contact_force_n": float(
            np.linalg.norm(force[released], axis=1).max()
        ),
        "minimum_released_clearance_m": float(clearance[1:][released].min()),
        "external_force_work_j": float(np.sum(external * np.diff(pose[:, :3], axis=0))),
        "plateaus": plateaus,
        "secant_stiffness_n_per_m": stiffness,
        "stiffness_scope": "Secant of measured geometric overlap, including native contact offsets; not fingertip material modulus",
    }
    result["passed"] = all(checks.values())
    return result
