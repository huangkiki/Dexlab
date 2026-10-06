"""Explicit cloth boundary conditions and engine-independent measurements.

SI units throughout. These nominal materials are not hardware calibrated.
Measurements operate on recorded vertices, not native contact identifiers.
"""

from dataclasses import asdict, dataclass

import numpy as np
from trimesh.triangles import closest_point


@dataclass(frozen=True)
class ClothCase:
    name: str = "strip"
    experiment: str = "extension"
    length: float = 0.2
    width: float = 0.1
    nx: int = 9
    ny: int = 5
    areal_density: float = 0.2
    height: float = 0.3
    force: float = 0.005
    radius: float = 0.001
    duration: float = 3.0
    sphere_radius: float = 0.06
    sphere_height: float = 0.07

    def __post_init__(self):
        if self.experiment not in ("extension", "sag", "drape", "folded-drop"):
            raise ValueError("Expected extension, sag, drape, or folded-drop")
        if any(type(n) is not int or n < 3 for n in (self.nx, self.ny)):
            raise ValueError("A cloth grid needs at least three vertices per axis")
        for key, value in asdict(self).items():
            if isinstance(value, (int, float)) and (
                not np.isfinite(value) or value <= 0
            ):
                raise ValueError(f"{key} must be finite and positive")
        if self.duration != 3:
            raise ValueError("This protocol has a fixed 3-second duration")
        if self.experiment == "folded-drop" and self.nx % 2 != 1:
            raise ValueError("Folded-drop requires an odd nx with a center fold edge")
        if self.experiment == "drape" and self.height <= (
            self.sphere_height + self.sphere_radius + self.radius
        ):
            raise ValueError("Drape cloth must start above the obstacle")

    @property
    def gravity(self):
        return (0.0, 0.0, 0.0 if self.experiment == "extension" else -9.81)

    def mesh(self):
        x, y = np.meshgrid(
            np.linspace(-self.length / 2, self.length / 2, self.nx),
            np.linspace(-self.width / 2, self.width / 2, self.ny),
        )
        vertices = np.c_[x.ravel(), y.ravel(), np.full(x.size, self.height)]
        if self.experiment == "folded-drop":
            # Isometric fold about y. The upper half starts 0.3 rad above
            # the lower panel; no weld or prescribed vertex motion is used.
            left = vertices[:, 0] < 0
            unfolded_x = vertices[left, 0].copy()
            vertices[left, 0] = np.cos(np.pi - 0.3) * unfolded_x
            vertices[left, 2] -= np.sin(np.pi - 0.3) * unfolded_x
        triangles = []
        for j in range(self.ny - 1):
            for i in range(self.nx - 1):
                a = j * self.nx + i
                triangles.extend(
                    ((a, a + 1, a + self.nx), (a + 1, a + self.nx + 1, a + self.nx))
                )
        triangles = np.asarray(triangles, dtype=np.int32)
        areas = (
            np.linalg.norm(
                np.cross(
                    vertices[triangles[:, 1]] - vertices[triangles[:, 0]],
                    vertices[triangles[:, 2]] - vertices[triangles[:, 0]],
                ),
                axis=1,
            )
            / 2
        )
        masses = np.zeros(len(vertices))
        for column in triangles.T:
            np.add.at(masses, column, areas * self.areal_density / 3)
        return vertices, triangles, masses

    @property
    def pins(self):
        return (
            np.arange(0, self.nx * self.ny, self.nx, dtype=int)
            if self.experiment in ("extension", "sag")
            else np.empty(0, dtype=int)
        )

    @property
    def tip(self):
        return np.arange(self.nx - 1, self.nx * self.ny, self.nx)

    def forces(self, time):
        """Prescribed total traction: ramp, hold, unload, then relax."""
        forces = np.zeros((self.nx * self.ny, 3))
        if self.experiment == "extension":
            scale = min(time / 0.5, 1.0, max(0.0, (2.0 - time) / 0.5))
            # Trapezoidal edge quadrature preserves uniform traction on refinement.
            weights = np.ones(self.ny)
            weights[[0, -1]] = 0.5
            forces[self.tip, 0] = self.force * scale * weights / weights.sum()
        return forces


def frame_metrics(case, positions, velocities):
    """Geometric checks include triangle interiors, not only collision samples.

    Sphere distance is exact for each piecewise-linear triangle. It does not
    prove inter-step collision continuity. Self-crossings are audited separately.
    """
    rest, triangles, _ = case.mesh()
    if positions.shape != rest.shape or velocities.shape != rest.shape:
        raise ValueError("Recorded vertices do not match the declared mesh")
    if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
        raise ValueError("Nonfinite cloth state")
    edges = np.unique(
        np.sort(
            np.vstack((triangles[:, :2], triangles[:, 1:], triangles[:, [2, 0]])),
            axis=1,
        ),
        axis=0,
    )
    rest_length = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    lengths = np.linalg.norm(positions[edges[:, 0]] - positions[edges[:, 1]], axis=1)
    result = {
        "maximum_absolute_edge_strain": float(
            np.max(np.abs(lengths / rest_length - 1))
        ),
        "tip_extension_m": float(np.mean(positions[case.tip, 0] - rest[case.tip, 0])),
        "tip_sag_m": float(np.mean(rest[case.tip, 2] - positions[case.tip, 2])),
        "center_sag_m": float(rest[len(rest) // 2, 2] - positions[len(rest) // 2, 2]),
        "speed_rms_m_s": float(np.sqrt(np.mean(np.sum(velocities**2, axis=1)))),
        "maximum_pin_error_m": float(
            np.max(
                np.linalg.norm(positions[case.pins] - rest[case.pins], axis=1),
                initial=0,
            )
        ),
        "ground_penetration_m": 0.0,
        "sphere_penetration_m": 0.0,
    }
    if case.experiment in ("drape", "folded-drop"):
        result["ground_penetration_m"] = float(
            max(0, case.radius - positions[:, 2].min())
        )
    if case.experiment == "drape":
        centers = np.tile([0, 0, case.sphere_height], (len(triangles), 1))
        distance = np.linalg.norm(
            closest_point(positions[triangles], centers) - centers, axis=1
        )
        result["sphere_penetration_m"] = float(
            max(0, case.sphere_radius + case.radius - distance.min())
        )
    return result


def score_record(case, dt, time, positions, velocities):
    expected = round(case.duration / dt) + 1  # includes the unstepped initial state
    checks = {
        "complete_time_grid": bool(
            len(time) == expected
            and np.allclose(time, np.arange(expected) * dt, atol=1e-10, rtol=0)
        ),
        "finite_states": bool(
            np.isfinite(positions).all() and np.isfinite(velocities).all()
        ),
    }
    if not checks["finite_states"] or len(positions) == 0:
        return {"protocol_checks_passed": False, "checks": checks, "metrics": {}}
    frames = [
        frame_metrics(case, p, v) for p, v in zip(positions, velocities, strict=True)
    ]
    series = {key: np.array([row[key] for row in frames]) for key in frames[0]}
    maxima = {key: float(values.max()) for key, values in series.items()}
    checks["fixed_boundary_within_1_um"] = maxima["maximum_pin_error_m"] < 1e-6
    checks["obstacle_penetration_below_1_5_mm"] = (
        max(maxima["ground_penetration_m"], maxima["sphere_penetration_m"]) < 0.0015
    )
    from dexlab.cloth_self_contact import audit_record

    self_contact = audit_record(time, positions, case.mesh()[1])
    checks["no_sampled_surface_crossings"] = self_contact["maximum_crossing_pairs"] == 0
    checks["no_sampled_degenerate_triangles"] = self_contact["maximum_degenerate_triangles"] == 0
    # These are protocol checks, not calibrated material-accuracy certification.
    return {
        "protocol_checks_passed": all(checks.values()),
        "checks": checks,
        "metrics": {"maximum": maxima, "final": frames[-1]},
        "self_intersection_audit": self_contact,
        "material_accuracy": "uncalibrated; no shared stiffness equivalence claimed",
    }
