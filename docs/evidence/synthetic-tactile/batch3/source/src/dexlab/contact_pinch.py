"""Controlled two-pad cylinder loading and release, independent of an engine."""

from dataclasses import asdict, dataclass

import numpy as np

from dexlab.physx_pinch import box_overlap, rotation_matrices

PAD_HALF = np.array([0.005, 0.025, 0.04])
PAD_MASS = 0.1
HEIGHT = 0.2
PREPARE_END = 0.3
RELEASE_START = 1.5
DURATION = 2.0


@dataclass(frozen=True)
class CylinderCase:
    name: str = "dev-cylinder-hold"
    mode: str = "hold"
    mass: float = 0.2
    radius: float = 0.01
    half_height: float = 0.03
    sections: int = 64
    surface_subdivisions: int = 0
    friction: float = 0.3
    normal_load: float = 4.0
    gravity: float = 9.81
    timestep: float = 0.0005
    controller_period: float = 0.001
    ramp_load: float = 4.0

    def __post_init__(self):
        values = [v for k, v in asdict(self).items() if k not in ("name", "mode")]
        if not self.name or not np.isfinite(values).all():
            raise ValueError("Finite named case required")
        if (
            min(
                self.mass,
                self.radius,
                self.half_height,
                self.normal_load,
                self.gravity,
                self.timestep,
            )
            <= 0
            or min(self.friction, self.ramp_load) < 0
        ):
            raise ValueError("Invalid physical parameters")
        if type(self.sections) is not int or self.sections < 16 or self.sections % 4:
            raise ValueError(
                "A multiple of four, at least16, cylinder sections is required"
            )
        if (
            type(self.surface_subdivisions) is not int
            or not 0 <= self.surface_subdivisions <= 4
        ):
            raise ValueError(
                "Surface subdivisions must be an integer from zero to four"
            )
        if self.mode not in ("hold", "overload", "frictionless", "ramp"):
            raise ValueError("Unknown loading mode")
        if self.mode == "frictionless" and self.friction != 0:
            raise ValueError("The frictionless control must set mu=0")
        if self.controller_period < self.timestep or not np.isclose(
            self.controller_period / self.timestep,
            round(self.controller_period / self.timestep),
            atol=1e-8,
            rtol=0,
        ):
            raise ValueError("Physics timestep must divide the fixed controller period")
        for duration in (DURATION, PREPARE_END, RELEASE_START, 0.025, 0.02):
            if not np.isclose(
                duration / self.timestep,
                round(duration / self.timestep),
                atol=1e-8,
                rtol=0,
            ):
                raise ValueError(
                    "The timestep must divide all physical protocol phases"
                )
            if not np.isclose(
                duration / self.controller_period,
                round(duration / self.controller_period),
                atol=1e-8,
                rtol=0,
            ):
                raise ValueError(
                    "The control period must divide all physical protocol phases"
                )
        capacity = 2 * self.normal_load * self.friction
        if self.mode == "hold" and self.mass * self.gravity >= capacity:
            raise ValueError("Hold control must lie below nominal capacity")
        if self.mode == "overload" and self.mass * self.gravity <= capacity:
            raise ValueError("Overload control must exceed nominal capacity")
        if (
            self.mode == "ramp"
            and self.mass * self.gravity + self.ramp_load <= capacity
        ):
            raise ValueError("Ramp must cross nominal capacity")

    @property
    def steps(self):
        return round(DURATION / self.timestep)

    @property
    def pad_x(self):
        return self.radius + PAD_HALF[0] + 0.0002

    @property
    def inertia(self):
        # Uniform regular-prism inertia; converges to the circular cylinder.
        polar = self.radius**2 * (2 + np.cos(2 * np.pi / self.sections)) / 6
        return self.mass * np.array([polar / 2 + self.half_height**2 / 3] * 2 + [polar])

    def force(self, step):
        interval = round(self.controller_period / self.timestep)
        t = (step // interval) * self.controller_period
        normal = (
            self.normal_load
            if t < RELEASE_START
            else (
                -2.0
                if t < RELEASE_START + 0.025
                else (2.0 if t < RELEASE_START + 0.05 else 0.0)
            )
        )
        force = np.zeros((3, 3), dtype=np.float32)
        force[:2, 0] = [normal, -normal]
        if t < PREPARE_END:
            force[2, 2] = self.mass * self.gravity
        elif self.mode == "ramp" and t < RELEASE_START:
            force[2, 2] = -self.ramp_load * np.clip((t - 0.6) / 0.7, 0, 1)
        return force


LIMITS = {
    "penetration_m": 0.001,
    "hold_drift_m": 0.001,
    "hold_speed_m_s": 0.005,
    "normal_load_relative_error": 0.05,
    "minimum_drop_m": 0.05,
    "released_force_n": 0.01,
    "freefall_acceleration_relative_error": 0.02,
    "momentum_peak_weight_ratio": 0.05,
    "orientation_rad": 0.05,
    "slip_speed_m_s": 0.005,
    "slip_sustain_s": 0.02,
}


def cylinder_box_overlap(cylinder_pose, pad_pose, case):
    """Exact SAT overlap depth for the declared regular prism and an OBB.

    Source cylinder faceting has radial error r*(1-cos(pi/N)); this metric is
    exact for that source prism, not a claim of exact curved-cylinder geometry.
    """
    cylinder_pose = np.atleast_2d(cylinder_pose)
    pad_pose = np.atleast_2d(pad_pose)
    rc = rotation_matrices(cylinder_pose[:, 3:])
    rp = rotation_matrices(pad_pose[:, 3:])
    theta = (np.arange(case.sections // 2) + 0.5) * 2 * np.pi / case.sections
    side = np.column_stack([np.cos(theta), np.sin(theta), np.zeros_like(theta)])
    normals = np.vstack([side, [0, 0, 1]])
    edges = np.vstack(
        [
            np.column_stack([-np.sin(theta), np.cos(theta), np.zeros_like(theta)]),
            [0, 0, 1],
        ]
    )
    box_axes = np.swapaxes(rp, 1, 2)
    faces = np.einsum("ki,nji->nkj", normals, rc)
    edge_world = np.einsum("ki,nji->nkj", edges, rc)
    crosses = np.cross(box_axes[:, :, None, :], edge_world[:, None, :, :]).reshape(
        len(rc), -1, 3
    )
    axes = np.concatenate([box_axes, faces, crosses], axis=1)
    lengths = np.linalg.norm(axes, axis=-1)
    valid = lengths > 1e-10
    axes = axes / np.maximum(lengths[..., None], 1e-10)
    local = np.einsum("nki,nij->nkj", axes, rc)
    angle = np.arctan2(local[..., 1], local[..., 0])
    nearest = np.rint(angle * case.sections / (2 * np.pi)) * 2 * np.pi / case.sections
    radius_c = case.radius * np.linalg.norm(local[..., :2], axis=-1) * np.cos(
        angle - nearest
    ) + case.half_height * np.abs(local[..., 2])
    radius_p = np.sum(np.abs(np.einsum("nki,nij->nkj", axes, rp)) * PAD_HALF, axis=-1)
    distance = np.abs(
        np.einsum("nki,ni->nk", axes, pad_pose[:, :3] - cylinder_pose[:, :3])
    )
    overlap = np.where(valid, radius_c + radius_p - distance, np.inf)
    return np.maximum(overlap.min(axis=1), 0)


def score(case, data):
    n = case.steps
    shapes = {
        "time": (n + 1,),
        "pose": (n + 1, 3, 7),
        "velocity": (n + 1, 3, 6),
        "external_force": (n, 3, 3),
        "contact_force": (n, 2, 3),
        "normal_force": (n, 2, 3),
        "contact_known": (n,),
        "step_completed": (n,),
    }
    checks = {
        "complete_shapes": all(
            k in data and np.shape(data[k]) == v for k, v in shapes.items()
        )
    }
    result = {
        "passed": False,
        "checks": checks,
        "metrics": {},
        "scope": "Nominal regular-prism pinch/load/release; not calibrated fingertips or apple grasp",
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
    pose, velocity = data["pose"], data["velocity"]
    try:
        rotations = rotation_matrices(pose[:, :, 3:])
        penetration = np.maximum(
            cylinder_box_overlap(pose[:, 2], pose[:, 0], case),
            cylinder_box_overlap(pose[:, 2], pose[:, 1], case),
        )
    except ValueError:
        checks["unit_quaternions"] = False
        return result
    checks["unit_quaternions"] = True
    pad_penetration = box_overlap(
        pose[:, 0, :3],
        rotations[:, 0],
        PAD_HALF,
        pose[:, 1, :3],
        rotations[:, 1],
        PAD_HALF,
    )
    commands = np.array([case.force(i) for i in range(n)])
    checks["declared_external_forces"] = bool(
        np.array_equal(data["external_force"], commands)
    )
    checks["actual_prismatic_pads"] = bool(
        np.allclose(pose[:, :2, 1:3], [0, HEIGHT], atol=1e-6, rtol=0)
        and np.allclose(rotations[:, :2], np.eye(3), atol=1e-5, rtol=0)
    )
    force = data["contact_force"].sum(axis=1)
    residual = (
        case.mass * np.diff(velocity[:, 2, :3], axis=0) / case.timestep
        - force
        - data["external_force"][:, 2]
    )
    residual[:, 2] += case.mass * case.gravity
    momentum_ratio = np.linalg.norm(residual, axis=1) / (case.mass * case.gravity)
    checks["momentum_balance"] = bool(
        momentum_ratio.max() < LIMITS["momentum_peak_weight_ratio"]
    )
    checks["bounded_penetration"] = bool(penetration.max() < LIMITS["penetration_m"])
    checks["bounded_pad_pad_penetration"] = bool(
        pad_penetration.max() < LIMITS["penetration_m"]
    )
    checks["pads_do_not_cross"] = bool(np.all(pose[:, 0, 0] < pose[:, 1, 0]))
    times = data["time"][1:]
    preload = (times > 0.25) & (times <= PREPARE_END)
    normal = data["normal_force"][:, :, 0] * [1, -1]
    normal_mean = normal[preload].mean(axis=0)
    checks["measured_normal_load"] = bool(
        np.all(
            np.abs(normal_mean / case.normal_load - 1)
            < LIMITS["normal_load_relative_error"]
        )
    )
    origin = pose[round(PREPARE_END / case.timestep), 2, :3]
    hold = (times > 0.5) & (times <= RELEASE_START)
    drift = np.linalg.norm(pose[1:, 2, :3] - origin, axis=1)
    speed = np.linalg.norm(velocity[1:, 2, :3], axis=1)
    angle = 2 * np.arccos(
        np.clip(
            np.abs(pose[1:, 2, 3:] @ pose[round(PREPARE_END / case.timestep), 2, 3:]),
            0,
            1,
        )
    )
    if case.mode == "hold":
        checks.update(
            holds_load=bool(drift[hold].max() < LIMITS["hold_drift_m"]),
            bounded_hold_speed=bool(speed[hold].max() < LIMITS["hold_speed_m_s"]),
            no_tipping_during_hold=bool(angle[hold].max() < LIMITS["orientation_rad"]),
        )
    else:
        end = 1.45 if case.mode == "ramp" else 0.6
        drop = origin[2] - pose[round(end / case.timestep), 2, 2]
        checks["negative_control_drops"] = bool(drop > LIMITS["minimum_drop_m"])
        result["metrics"]["negative_control_drop_m"] = float(drop)
    released = times > 1.75
    slope, _offset = np.polyfit(times[released], velocity[1:, 2, 2][released], 1)
    checks.update(
        fully_released=bool(
            np.linalg.norm(force[released], axis=1).max() < LIMITS["released_force_n"]
            and pose[round(RELEASE_START / case.timestep), 2, 2] - pose[-1, 2, 2]
            > LIMITS["minimum_drop_m"]
        ),
        freefall_acceleration=bool(
            abs(slope / -case.gravity - 1)
            < LIMITS["freefall_acceleration_relative_error"]
        ),
    )
    downward = velocity[1:, 2, 2] < -LIMITS["slip_speed_m_s"]
    downward &= (times > PREPARE_END) & (times < RELEASE_START)
    length = round(LIMITS["slip_sustain_s"] / case.timestep)
    sustained = np.flatnonzero(
        np.convolve(downward.astype(int), np.ones(length, dtype=int), "valid") == length
    )
    onset = int(sustained[0]) if len(sustained) else None
    result["metrics"].update(
        maximum_penetration_m=float(penetration.max()),
        maximum_pad_pad_penetration_m=float(pad_penetration.max()),
        penetration_over_limit_sample_duration_s=float(
            np.count_nonzero(penetration[1:] >= LIMITS["penetration_m"]) * case.timestep
        ),
        maximum_momentum_residual_weight_ratio=float(momentum_ratio.max()),
        measured_preload_n=normal_mean.tolist(),
        nominal_capacity_n=float(case.friction * normal_mean.sum()),
        hold_max_drift_m=float(drift[hold].max()),
        hold_max_speed_m_s=float(speed[hold].max()),
        released_acceleration_m_s2=float(slope),
        released_force_n=float(np.linalg.norm(force[released], axis=1).max()),
        vertical_slip_onset_time_s=float(times[onset]) if onset is not None else None,
        load_at_vertical_slip_onset_n=float(
            case.mass * case.gravity - data["external_force"][onset, 2, 2]
        )
        if onset is not None
        else None,
        normal_load_at_vertical_slip_onset_n=normal[onset].tolist()
        if onset is not None
        else None,
        slip_definition="COM vertical speed exceeds5mm/s for20ms; rigid-body drift, not material-point accumulated slip",
        cylinder_radial_faceting_error_m=float(
            case.radius * (1 - np.cos(np.pi / case.sections))
        ),
    )
    result["passed"] = all(checks.values())
    return result
