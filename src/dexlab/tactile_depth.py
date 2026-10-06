"""Synthetic box occupancy in a sensing slab; not force or gel deformation."""

import numpy as np


def depth_map(
    center, rotation, *, resolution=32, half_size=0.02, extent=0.04, height=0.001
):
    """Return occupied vertical length in sensor-frame z=[0,height], in meters.

    Rotation maps body coordinates to sensor coordinates. The function owns its
    output and retains no history; sensing parameters never touch native physics.
    """
    center = np.asarray(center, dtype=float)
    rotation = np.asarray(rotation, dtype=float)
    if (
        center.shape != (3,)
        or rotation.shape != (3, 3)
        or not np.isfinite(center).all()
        or not np.isfinite(rotation).all()
        or not isinstance(resolution, int)
        or isinstance(resolution, bool)
        or not 1 <= resolution <= 1024
        or not np.isfinite([half_size, extent, height]).all()
        or min(half_size, extent, height) <= 0
        or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-12, rtol=0)
        or abs(np.linalg.det(rotation) - 1) > 1e-12
    ):
        raise ValueError("Require finite rigid pose and positive bounded sensing grid")
    axis = (np.arange(resolution) + 0.5) * (2 * extent / resolution) - extent
    x, y = np.meshgrid(axis, axis, indexing="xy")
    origin = np.stack((x, y, np.zeros_like(x)), axis=-1)
    local = (origin - center) @ rotation
    direction = rotation[2, :]
    lower = np.zeros((resolution, resolution))
    upper = np.full_like(lower, height)
    valid = np.ones_like(lower, dtype=bool)
    for i in range(3):
        if abs(direction[i]) <= 1e-15:
            valid &= abs(local[..., i]) <= half_size
        else:
            a = (-half_size - local[..., i]) / direction[i]
            b = (half_size - local[..., i]) / direction[i]
            lower = np.maximum(lower, np.minimum(a, b))
            upper = np.minimum(upper, np.maximum(a, b))
    return np.where(valid, np.maximum(0, upper - lower), 0)
