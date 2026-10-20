"""Fit a fixed playback camera to measured points, including caption margins."""

import numpy as np


def fixed_view(vertices, azimuth, elevation, fovy=45, aspect=4 / 3):
    """Return look-at and distance without assuming a spherical motion envelope."""
    azimuth, altitude = np.deg2rad([azimuth, -elevation])
    right = np.array([-np.sin(azimuth), np.cos(azimuth), 0])
    outward = np.array([np.cos(altitude) * np.cos(azimuth),
                        np.cos(altitude) * np.sin(azimuth), np.sin(altitude)])
    up = np.cross(outward, right)
    basis = np.array([right, up, outward])
    projected = np.asarray(vertices).reshape(-1, 3) @ basis.T
    center = (projected.min(axis=0) + projected.max(axis=0)) / 2
    relative = projected - center
    tangent = np.tan(np.deg2rad(fovy) / 2)
    required = relative[:, 2] + np.maximum(
        np.abs(relative[:, 0]) / (tangent * aspect * .85),
        np.abs(relative[:, 1]) / (tangent * .75),
    )
    return center @ basis, max(.25, float(required.max() + .025))
