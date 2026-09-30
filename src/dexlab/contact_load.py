"""Force-controlled normal response; engineering target, not measured material.

The 2/6 N plateaus are fitting data. The intermediate 4 N plateau, changed
masses and changed timesteps are validation only. Never adapt from these rows.
"""

from dataclasses import dataclass

import numpy as np

from dexlab.contact_plane import PlaneCase
from dexlab.physx_baseline import box_plane_clearance


@dataclass(frozen=True)
class LoadCase:
    name: str = "dev-normal-load"
    mass: float = 0.2
    half_size: float = 0.02
    gravity: float = 9.81
    timestep: float = 0.0005
    settle: float = 0.0
    duration: float = 0.8
    max_force: float = 40.0

    def __post_init__(self):
        self.plane()
        if self.duration != 0.8 or self.settle != 0:
            raise ValueError("This protocol fixes duration at 0.8 s without settling")
        if (
            not np.isfinite(self.max_force)
            or self.max_force < self.mass * self.gravity + 6
        ):
            raise ValueError("Force limit must cover the prescribed loading sequence")
        if not np.isclose(
            0.05 / self.timestep, round(0.05 / self.timestep), atol=1e-8, rtol=0
        ):
            raise ValueError("Timestep must divide the 50 ms scoring window")

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

    def loads(self):
        return np.repeat([2.0, 4.0, 6.0, -1.0], round(0.2 / self.timestep))

    def command(self, step, pose, velocity, previous):
        # No state feedback: gravity compensation plus a fixed world-COM load.
        load = (2.0, 4.0, 6.0, -1.0)[step // round(0.2 / self.timestep)]
        return np.array([0, 0, self.mass * self.gravity - load], dtype=np.float32)


# Declared before fitting; these are task design values, not hardware tolerances.
LIMITS = {
    "target_stiffness_n_m": 20000.0,
    "relative_response_error": 0.05,
    "plateau_std_m": 5e-6,
    "penetration_m": 0.001,
    "momentum_peak_weight_ratio": 0.05,
    "orientation_change_rad": 0.05,
    "lateral_drift_m": 0.001,
    "released_clearance_m": 0.0005,
    "released_contact_force_n": 0.01,
    "normal_tension_n": 1e-6,
    "command_rounding_n": 2e-6,
}


def score(case, data):
    """Measure all physical steps; score plateaus separately from transients."""
    n = case.steps
    shapes = {
        "time": (n + 1,),
        "pose": (n + 1, 7),
        "velocity": (n + 1, 6),
        "contact_force": (n, 3),
        "external_force": (n, 3),
        "downward_load": (n,),
        "contact_known": (n,),
        "step_completed": (n,),
    }
    checks = {
        "complete_shapes": all(
            k in data and np.shape(data[k]) == s for k, s in shapes.items()
        )
    }
    result = {
        "passed": False,
        "checks": checks,
        "metrics": {},
        "scope": "Static normal response to a declared engineering target; not full material calibration",
    }
    if not checks["complete_shapes"]:
        return result
    checks.update(
        finite_states_and_forces=all(np.isfinite(data[k]).all() for k in shapes),
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
        declared_loads=bool(np.array_equal(data["downward_load"], case.loads())),
    )
    if not all(checks.values()):
        return result
    pose, velocity, force = data["pose"], data["velocity"], data["contact_force"]
    expected = np.zeros((n, 3))
    expected[:, 2] = case.mass * case.gravity - case.loads()
    checks["declared_force_commands"] = bool(
        np.allclose(
            data["external_force"], expected, atol=LIMITS["command_rounding_n"], rtol=0
        )
    )
    try:
        depth = -box_plane_clearance(pose, case.half_size)
    except ValueError:
        checks["unit_quaternions"] = False
        return result
    checks["unit_quaternions"] = True
    residual = (
        case.mass * np.diff(velocity[:, :3], axis=0) / case.timestep
        - force
        - data["external_force"]
    )
    residual[:, 2] += case.mass * case.gravity
    residual_ratio = float(
        np.linalg.norm(residual, axis=1).max() / (case.mass * case.gravity)
    )
    angle = float((2 * np.arccos(np.clip(np.abs(pose[:, 3]), 0, 1))).max())
    width, window = round(0.2 / case.timestep), round(0.05 / case.timestep)
    plateaus = []
    for i, load in enumerate((2.0, 4.0, 6.0, -1.0)):
        stop = (i + 1) * width
        depths = depth[stop - window + 1 : stop + 1]
        forces = force[stop - window : stop, 2]
        plateaus.append(
            {
                "load_n": load,
                "indentation_mean_m": float(depths.mean()),
                "indentation_std_m": float(depths.std()),
                "contact_force_mean_n": float(forces.mean()),
            }
        )
    errors = [
        abs(p["indentation_mean_m"] * LIMITS["target_stiffness_n_m"] / p["load_n"] - 1)
        for p in plateaus[:3]
    ]
    force_errors = [
        abs(p["contact_force_mean_n"] / p["load_n"] - 1) for p in plateaus[:3]
    ]
    release_start = 3 * width + width - window
    dx = plateaus[2]["indentation_mean_m"] - plateaus[0]["indentation_mean_m"]
    slope = 4 / dx if dx > 1e-9 else None
    checks.update(
        initially_at_rest=bool(np.allclose(velocity[0], 0, atol=1e-7, rtol=0)),
        declared_initial_pose=bool(
            np.allclose(pose[0], [0, 0, case.half_size, 1, 0, 0, 0], atol=1e-7, rtol=0)
        ),
        bounded_penetration=bool(depth.max() < LIMITS["penetration_m"]),
        momentum_balance=residual_ratio < LIMITS["momentum_peak_weight_ratio"],
        no_tipping=angle < LIMITS["orientation_change_rad"],
        no_lateral_drift=bool(np.abs(pose[:, :2]).max() < LIMITS["lateral_drift_m"]),
        no_tensile_normal_force=bool(force[:, 2].min() >= -LIMITS["normal_tension_n"]),
        loaded_force_balance=max(force_errors) < LIMITS["relative_response_error"],
        settled_plateaus=max(p["indentation_std_m"] for p in plateaus[:3])
        < LIMITS["plateau_std_m"],
        fitting_load_response=max(errors[0], errors[2])
        < LIMITS["relative_response_error"],
        intermediate_load_validation=errors[1] < LIMITS["relative_response_error"],
        released_geometry=bool(
            (-depth[release_start + 1 :]).min() > LIMITS["released_clearance_m"]
        ),
        fully_unloaded=bool(
            np.linalg.norm(force[release_start:], axis=1).max()
            < LIMITS["released_contact_force_n"]
        ),
    )
    result["metrics"] = {
        "plateaus": plateaus,
        "response_relative_errors": errors,
        "fit_secant_stiffness_n_m": slope,
        "fit_zero_load_intercept_m": None
        if slope is None
        else plateaus[0]["indentation_mean_m"] - 2 / slope,
        "maximum_penetration_m": float(max(depth.max(), 0)),
        "peak_momentum_residual_weight_ratio": residual_ratio,
        "maximum_orientation_rad": angle,
    }
    result["passed"] = all(checks.values())
    return result
