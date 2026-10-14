"""Deterministic material sampling in metres; no solver or rendering dependency."""

from itertools import product

import numpy as np


def material_points(size, spacing, shape='block'):
    """Equal-volume lattice samples of a box or synthetic tapered curved fruit.

    The banana's centreline bends in the board plane. Its circular section
    tapers toward both ends; this is authored geometry, not a scanned fruit.
    """
    size = np.asarray(size)
    cells = np.rint(size / spacing).astype(int)
    origin = -np.array([size[0] / 2, size[1] / 2, 0.])
    coordinates = [origin[i] + (np.arange(2 * cells[i]) + .5) * spacing / 2
                   for i in range(3)]
    points = np.array(list(product(*coordinates)))
    if shape == 'block':
        return points
    if shape != 'banana':
        raise ValueError('Unknown material shape')
    u = points[:, 0] / (size[0] / 2)
    centre_y = .035 * (u**2 - .5)
    radius = .003 + .009 * np.maximum(0, 1 - u**2)**.55
    inside = ((points[:, 1] - centre_y)**2 + (points[:, 2] - .012)**2 <= radius**2)
    return points[inside]
