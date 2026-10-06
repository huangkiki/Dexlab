"""Independent planar-contact protocol and scoring for the contact benchmark.

This subprotocol measures rigid cube/plane contact. It does not qualify the
indentation, cylinder load-sweep or release experiments tracked in issue #10.
"""

from dataclasses import asdict, dataclass

import numpy as np

from dexlab.physx_baseline import box_plane_clearance


@dataclass(frozen=True)
class PlaneCase:
    name: str = "dev-slide"
    mass: float = 0.2
    half_size: float = 0.02
    friction: float = 0.3
    initial_speed: float = 0.25
    gravity: float = 9.81
    timestep: float = 0.0005
    settle: float = 0.2
    duration: float = 0.5

    def __post_init__(self):
        values = [value for key, value in asdict(self).items() if key != "name"]
        if not self.name or not np.isfinite(values).all():
            raise ValueError("A named case with finite physical values is required")
        if (
            min(self.mass, self.half_size, self.gravity, self.timestep, self.duration)
            <= 0
        ):
            raise ValueError("Mass, dimensions, gravity and durations must be positive")
        if self.friction < 0 or self.settle < 0:
            raise ValueError("Friction and settling duration must be nonnegative")
        for duration in (self.duration, self.settle):
            if not np.isclose(
                duration / self.timestep,
                round(duration / self.timestep),
                rtol=0,
                atol=1e-8,
            ):
                raise ValueError("The timestep must divide both protocol durations")

    @property
    def steps(self):
        return round(self.duration / self.timestep)

    @property
    def inertia(self):
        return np.full(3, 2 * self.mass * self.half_size**2 / 3)


# Engineering protocol boundaries, declared before evaluation, not hardware tolerances.
LIMITS = {
    "penetration_m": 0.001,
    "support_relative_error": 0.05,
    "momentum_peak_weight_ratio": 0.05,
    "position_reference_error_m": 0.002,
    "velocity_reference_error_m_s": 0.02,
    "orientation_change_rad": 0.05,
    "normal_tension_n": 1e-6,
    "surface_clearance_m": 0.001,
}


def reference(case, time):
    """Ideal no-tip Coulomb sliding; both signs and zero friction are explicit."""
    speed, sign = abs(case.initial_speed), np.sign(case.initial_speed)
    time = np.asarray(time, dtype=float)
    if case.friction == 0:
        return case.initial_speed * time, np.full_like(time, case.initial_speed)
    deceleration = case.friction * case.gravity
    moving_time = np.minimum(time, speed / deceleration)
    position = sign * (speed * moving_time - 0.5 * deceleration * moving_time**2)
    velocity = sign * np.maximum(speed - deceleration * time, 0)
    return position, velocity


def score(case, data):
    """Score measurements without importing an engine or accepting runtime verdicts."""
    n = case.steps
    shapes = {
        "time": (n + 1,),
        "pose": (n + 1, 7),
        "velocity": (n + 1, 6),
        "contact_force": (n, 3),
        "contact_known": (n,),
        "step_completed": (n,),
    }
    checks = {
        "complete_shapes": all(
            k in data and data[k].shape == shape for k, shape in shapes.items()
        )
    }
    result = {
        "passed": False,
        "checks": checks,
        "metrics": {},
        "scope": "Nominal planar contact; no matched compliance or hardware accuracy claim",
    }
    if not checks["complete_shapes"]:
        return result
    checks["finite_states_and_forces"] = all(np.isfinite(data[k]).all() for k in shapes)
    checks["complete_contact_coverage"] = bool(
        data["contact_known"].dtype == bool and data["contact_known"].all()
    )
    checks["native_steps_completed"] = bool(
        data["step_completed"].dtype == bool and data["step_completed"].all()
    )
    checks["uniform_time_grid"] = bool(
        np.allclose(data["time"], np.arange(n + 1) * case.timestep, atol=1e-10, rtol=0)
    )
    if not all(checks.values()):
        return result
    pose, velocity, force = data["pose"], data["velocity"], data["contact_force"]
    checks["declared_initial_velocity"] = bool(
        np.allclose(velocity[0], [case.initial_speed, 0, 0, 0, 0, 0], atol=1e-7, rtol=0)
    )
    try:
        clearance = box_plane_clearance(pose, case.half_size)
    except ValueError:
        checks["unit_quaternions"] = False
        return result
    checks["unit_quaternions"] = True
    penetration = np.maximum(-clearance, 0)
    relative_cosine = np.clip(np.abs(pose[:, 3:] @ pose[0, 3:]), 0, 1)
    angle = 2 * np.arccos(relative_cosine)
    momentum = case.mass * np.diff(velocity[:, :3], axis=0) / case.timestep - force
    momentum[:, 2] += case.mass * case.gravity
    momentum_ratio = np.linalg.norm(momentum, axis=1) / (case.mass * case.gravity)
    support_error = abs(force[:, 2].mean() / (case.mass * case.gravity) - 1)
    position_ref, velocity_ref = reference(case, data["time"])
    position_error = float(np.max(np.abs(pose[:, 0] - pose[0, 0] - position_ref)))
    velocity_error = float(np.max(np.abs(velocity[:, 0] - velocity_ref)))
    transverse_error = float(np.max(np.abs(pose[:, 1] - pose[0, 1])))
    normal = force[:, 2]
    tangential = np.linalg.norm(force[:, :2], axis=1)
    checks.update(
        no_tensile_normal_force=bool(np.min(normal) >= -LIMITS["normal_tension_n"]),
        support_matches_weight=bool(support_error < LIMITS["support_relative_error"]),
        momentum_balance=bool(
            momentum_ratio.max() < LIMITS["momentum_peak_weight_ratio"]
        ),
        bounded_penetration=bool(penetration.max() < LIMITS["penetration_m"]),
        surface_contact_geometry=bool(clearance.max() < LIMITS["surface_clearance_m"]),
        no_transverse_drift=transverse_error < LIMITS["position_reference_error_m"],
        initially_level_reference_applicable=bool(
            2 * np.arccos(np.clip(abs(pose[0, 3]), 0, 1))
            < LIMITS["orientation_change_rad"]
        ),
        no_tipping_reference_applicable=bool(
            angle.max() < LIMITS["orientation_change_rad"]
        ),
        coulomb_position=position_error < LIMITS["position_reference_error_m"],
        coulomb_velocity=velocity_error < LIMITS["velocity_reference_error_m_s"],
    )
    result["metrics"] = {
        "maximum_penetration_m": float(penetration.max()),
        "penetration_p95_m": float(np.quantile(penetration, 0.95)),
        "penetration_over_limit_sample_duration_s": float(
            np.count_nonzero(penetration[1:] >= LIMITS["penetration_m"]) * case.timestep
        ),
        "support_relative_error": float(support_error),
        "maximum_momentum_residual_weight_ratio": float(momentum_ratio.max()),
        "maximum_position_reference_error_m": position_error,
        "maximum_velocity_reference_error_m_s": velocity_error,
        "maximum_transverse_drift_m": transverse_error,
        "maximum_surface_clearance_m": float(clearance.max()),
        "maximum_orientation_change_rad": float(angle.max()),
        "normal_force_range_n": [float(normal.min()), float(normal.max())],
        "maximum_tangential_force_n": float(tangential.max()),
        "travel_x_m": float(pose[-1, 0] - pose[0, 0]),
        "final_speed_m_s": float(np.linalg.norm(velocity[-1, :3])),
    }
    result["passed"] = all(checks.values())
    return result
