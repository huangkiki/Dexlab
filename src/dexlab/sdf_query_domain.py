"""Conservative actor-AABB membership; not native provenance or SDF accuracy.

This applies the documented actor-bounding-box guarantee to supplied pose and
bounds. A native caller must bind those inputs to the actual actor and frozen
API version before using the interior mask for signed-distance scoring.
"""
import numpy as np
from numpy.typing import ArrayLike, NDArray


def _finite_real(value: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(value)
    if array.dtype.kind not in "fiu":
        raise ValueError(f"{name} must contain real numbers")
    array = array.astype(np.float64, copy=False)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite")
    return array


def classify_actor_domain(
    points_world_m: ArrayLike,
    *,
    translation_m: ArrayLike,
    rotation_xyzw: ArrayLike,
    bounds_local_m: ArrayLike,
    coordinate_guard_m: float,
) -> dict[str, NDArray]:
    """Partition every point into AABB interior, boundary band, or exterior.

    Bounds have shape (2, 3), ordered minimum then maximum, in actor coordinates.
    The pose maps actor coordinates to world coordinates; the quaternion order
    is x, y, z, w. A unit quaternion is required within 1e-12 and normalized for
    coordinate conversion. This is a representation check, not angular accuracy.

    The strictly positive guard is a prospectively declared coordinate band in
    metres, not a distance-error tolerance or certified arithmetic-error bound.
    The guard erodes/expands the AABB along each coordinate; the intervening band
    remains uncertain, including its corners. It is not a Euclidean surface band.
    Only points strictly inside the eroded AABB receive the interior mask.
    These labels describe the AABB, not whether a point is inside the object.

    No distance outcomes enter this function. It does not establish that supplied
    pose/bounds came from native readbacks, expose an automatic SDF grid, or
    authorize expanding the guarantee to a padded or precomputed grid.
    """
    points = _finite_real(points_world_m, "points_world_m")
    translation = _finite_real(translation_m, "translation_m")
    quaternion = _finite_real(rotation_xyzw, "rotation_xyzw")
    bounds = _finite_real(bounds_local_m, "bounds_local_m")
    guard = _finite_real(coordinate_guard_m, "coordinate_guard_m")
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0:
        raise ValueError("Expected a nonempty point array of shape (N, 3)")
    if translation.shape != (3,) or quaternion.shape != (4,):
        raise ValueError("Expected translation (3,) and xyzw quaternion (4,)")
    if bounds.shape != (2, 3) or not np.all(bounds[0] < bounds[1]):
        raise ValueError("Expected ordered, nondegenerate actor-local AABB bounds")
    if guard.shape != () or guard <= 0:
        raise ValueError("coordinate_guard_m must be a finite positive real scalar")
    norm = float(np.hypot.reduce(quaternion))
    if not np.isfinite(norm) or abs(norm - 1.0) > 1e-12:
        raise ValueError("Expected a unit xyzw quaternion")
    x, y, z, w = quaternion / norm
    rotation = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ])
    try:
        with np.errstate(over="raise", invalid="raise"):
            local = (points - translation) @ rotation
            clearance = np.minimum(local - bounds[0], bounds[1] - local).min(axis=1)
    except FloatingPointError as error:
        raise ValueError("Coordinate arithmetic is not representable") from error
    if not np.isfinite(local).all() or not np.isfinite(clearance).all():
        raise ValueError("Coordinate arithmetic is not representable")
    interior = clearance > guard
    exterior = clearance < -guard
    return {
        "local_m": local,
        "interior_mask": interior,
        "boundary_mask": ~(interior | exterior),
        "exterior_mask": exterior,
    }
