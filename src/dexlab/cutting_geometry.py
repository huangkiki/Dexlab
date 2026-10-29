"""Deterministic material sampling in metres; no solver or rendering dependency."""

from itertools import product

import numpy as np


def recorded_cut_geometry(trace, spacing):
    """Recover axis-aligned straight cuts from recorded blade motion.

    Active cutting samples are authoritative. Uncut negative controls have no
    active samples, so their intended planes use the densest position cluster
    for each recorded cut index. A path that sweeps laterally by half a material
    spacing cannot be represented by a planar replay and is rejected.
    """
    required = ('cut_index', 'cutting_active', 'blade_position_m')
    missing = [name for name in required if name not in trace]
    if missing:
        raise ValueError(f'Missing recorded cut geometry fields: {missing}')
    indices = np.asarray(trace['cut_index'], dtype=int)
    active = np.asarray(trace['cutting_active'], dtype=bool)
    positions = np.asarray(trace['blade_position_m'], dtype=float)
    yaws = np.asarray(trace.get('blade_yaw_rad', np.zeros(len(indices))), dtype=float)
    if not (len(indices) == len(active) == len(positions) == len(yaws)) or not len(indices):
        raise ValueError('Recorded cut geometry arrays have inconsistent lengths')
    cuts = np.unique(indices)
    if not np.array_equal(cuts, np.arange(cuts[-1] + 1)):
        raise ValueError('Recorded cut indices must be contiguous from zero')

    planes, axes = [], []
    for cut in cuts:
        cut_rows = indices == cut
        samples = cut_rows & active
        if not samples.any():
            samples = cut_rows
        normals = np.column_stack((np.cos(yaws[samples]), np.sin(yaws[samples])))
        dominant = np.argmax(abs(normals), axis=1)
        if not np.all(dominant == dominant[0]) or np.max(abs(normals[:, 1 - dominant[0]])) > 1e-6:
            raise ValueError('Recorded blade orientation is not one axis-aligned straight plane')
        axis = int(dominant[0])
        coordinates = positions[samples, axis]
        if active[cut_rows].any():
            plane = float(np.median(coordinates))
            spread = float(np.ptp(coordinates))
        else:
            bins = np.rint(coordinates / (spacing / 8)).astype(np.int64)
            labels, counts = np.unique(bins, return_counts=True)
            cluster = labels[counts.argmax()]
            selected = coordinates[bins == cluster]
            plane = float(np.median(selected))
            spread = float(np.ptp(selected))
        if spread > spacing / 2 + 1e-12:
            raise ValueError('Recorded blade path cannot be represented by a single straight plane')
        planes.append(plane)
        axes.append(axis)
    return tuple(planes), tuple(axes)


def recorded_sequential_regions(reference, trace, spacing, expected_cuts):
    """Partition a completed straight-cut record without nominal task planes."""
    planes, axes = recorded_cut_geometry(trace, spacing)
    if len(planes) != expected_cuts:
        raise ValueError('Completed sequential record is missing recorded cut geometry')
    if any(axis != axes[0] for axis in axes) or axes[0] != 0:
        raise ValueError('Sequential piece scoring currently requires parallel x-normal cuts')
    if len(set(planes)) != len(planes):
        raise ValueError('Recorded sequential cut planes must be distinct')
    ordered = tuple(sorted(planes))
    regions = np.searchsorted(ordered, np.asarray(reference)[:, 0])
    counts = np.bincount(regions, minlength=expected_cuts + 1)
    if np.any(counts == 0):
        raise ValueError('Recorded cut planes must leave particles in every scored region')
    return regions, planes


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
