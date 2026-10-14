"""Display measurements derived from saved states, independent of task scoring.

The face opening is an affine material-face estimate. The volume is the signed
volume of fixed, interior reference tetrahedra, not a rendered-surface volume.
Neither estimator is asserted to reproduce BladeMaster's unpublished sampling.
"""

from itertools import permutations, product

import numpy as np


def reference_tetrahedra(reference, spacing, selected):
    """Split complete selected lattice cells into six consistently oriented tets."""
    cells = np.rint((reference - reference.min(axis=0)) / spacing).astype(int)
    inventory = {tuple(cell): i for i, cell in enumerate(cells) if selected[i]}
    tetrahedra = []
    for corner in inventory:
        base = np.asarray(corner)
        if not all(tuple(base + offset) in inventory for offset in product((0, 1), repeat=3)):
            continue
        for axes in permutations(range(3)):
            points = [base.copy()]
            for axis in axes:
                point = points[-1].copy()
                point[axis] += 1
                points.append(point)
            indices = [inventory[tuple(point)] for point in points]
            xyz = reference[indices]
            if np.linalg.det(xyz[1:] - xyz[0]) < 0:
                indices[1], indices[2] = indices[2], indices[1]
            tetrahedra.append(indices)
    return np.asarray(tetrahedra, dtype=int).reshape(-1, 4)


def signed_volumes(positions, tetrahedra):
    xyz = positions[tetrahedra]
    return np.linalg.det(xyz[:, 1:] - xyz[:, :1]) / 6


def face_pairs(reference, plane, spacing):
    """Pair adjacent particles across an x-normal cut at equal reference y/z."""
    left_x = reference[reference[:, 0] < plane, 0].max()
    right_x = reference[reference[:, 0] > plane, 0].min()
    if not np.isclose(right_x - left_x, spacing, atol=1e-12):
        raise ValueError('The cut must lie between adjacent material lattice planes')
    transverse = np.rint((reference[:, 1:] - reference[:, 1:].min(axis=0)) / spacing).astype(int)
    right = {tuple(transverse[i]): i for i in np.flatnonzero(np.isclose(reference[:, 0], right_x))}
    pairs = [(i, right[tuple(transverse[i])]) for i in np.flatnonzero(np.isclose(reference[:, 0], left_x))
             if tuple(transverse[i]) in right]
    pairs = np.asarray(pairs, dtype=int).reshape(-1, 2)
    locations = reference[pairs[:, 0]].copy()
    locations[:, 0] = plane
    return pairs, locations


def face_opening(reference, positions, deformation, codes, pairs, locations, cut_index):
    """Signed x opening of faces whose native histories conflict for this cut."""
    digits = codes[pairs] // (3 ** cut_index) % 3
    valid = (digits[:, 0] != 0) & (digits[:, 1] != 0) & (digits[:, 0] != digits[:, 1])
    if not valid.any():
        return None, 0
    owners, rest = pairs[valid], locations[valid]
    moved = positions[owners] + np.einsum(
        'pkij,pkj->pki', deformation[owners], rest[:, None] - reference[owners])
    return float(np.mean(moved[:, 1, 0] - moved[:, 0, 0]) * 1000), int(valid.sum())


class ReplayMeasurements:
    """Fixed spatial regions and estimators for one immutable recorded run."""

    def __init__(self, states, trace, manifest):
        self.states, self.trace, self.manifest = states, trace, manifest
        self.reference = states['reference']
        self.task = manifest['task']
        self.planes = {'tofu': (0.,), 'tofu-sequential': (.015, -.015),
                       'banana': (-.03, 0., .03)}[self.task]
        spacing = manifest['config']['grid_spacing'] / 2
        self.pairs = [face_pairs(self.reference, plane, spacing) for plane in self.planes]
        self.regions = np.searchsorted(sorted(self.planes), self.reference[:, 0])
        included = (1,) if self.task == 'tofu-sequential' else range(len(self.planes) + 1)
        self.tetrahedra = np.concatenate([reference_tetrahedra(self.reference, spacing, self.regions == region)
                                         for region in included])
        self.reference_volume = float(signed_volumes(self.reference, self.tetrahedra).sum())
        if self.reference_volume <= 0:
            raise ValueError('No interior reference volume available')
        self.probe_frame = int(np.argmin(abs(states['time'] - manifest['probe_time_s'])))
        if not np.isclose(states['time'][self.probe_frame], manifest['probe_time_s']):
            raise ValueError('The initial motion needs an exact saved pre-probe frame')

    def frame(self, index):
        time = float(self.states['time'][index])
        positions = self.states['position'][index]
        deformation = self.states['deformation'][index]
        codes = self.states['sides'][index]
        trace_index = max(0, int(np.searchsorted(self.trace['time_s'], time + 1e-12, side='right')) - 1)
        if index == 0:
            phase = 'Initial'
        elif time > self.manifest['probe_time_s']:
            phase = 'Motion probe'
        elif self.trace['cutting_active'][trace_index]:
            phase = f'Cut {int(self.trace["cut_index"][trace_index])+1}'
        else:
            edge = self.trace['blade_position_m'][trace_index, 2] - self.manifest['config']['blade_half_size'][2]
            phase = 'Knife clear' if edge > self.manifest['config']['size'][2] else 'Withdrawing'
        gaps, counts = zip(*(face_opening(self.reference, positions, deformation, codes, pairs,
                                        locations, cut) for cut, (pairs, locations) in enumerate(self.pairs)))
        volumes = signed_volumes(positions, self.tetrahedra)
        displacement = [float(np.mean(positions[self.regions == region, 0] -
                                     self.reference[self.regions == region, 0]) * 1000)
                        for region in range(len(self.planes) + 1)]
        probe_displacement = None
        if index >= self.probe_frame:
            before = self.states['position'][self.probe_frame]
            probe_displacement = [float(np.mean(positions[self.regions == region, 0] -
                                               before[self.regions == region, 0]) * 1000)
                                  for region in range(len(self.planes) + 1)]
        return {'state_frame': index, 'trace_frame': trace_index, 'time_s': time, 'phase': phase,
                'face_opening_mm': list(gaps), 'paired_faces': list(counts),
                'interior_volume_change_percent': float((volumes.sum() / self.reference_volume - 1) * 100),
                'inverted_tetrahedra': int((volumes <= 0).sum()),
                'centroid_x_from_start_mm': displacement,
                'centroid_x_from_probe_mm': probe_displacement,
                'knife_material_force_n': (float(np.linalg.norm(self.trace['material_reaction_n'][trace_index]))
                                           if index else 0.)}

    def definitions(self):
        return {'face_opening_mm': 'Mean signed x distance between affine images of the same reference face; only opposing nonzero native digits for that cut are included. Null means no eligible pairs.',
                'interior_volume_change_percent': '100 * (current signed tetrahedral volume / reference volume - 1); six tetrahedra per complete interior lattice cell, excluding cells crossing planned cut planes. Middle third for two-cut tofu, all sampled piece interiors otherwise. Inverted tets are counted, never hidden with abs().',
                'centroid_x_from_start_mm': 'Equal-mass native particle centroids of fixed reference regions, ordered left to right; displacement from reference positions.',
                'centroid_x_from_probe_mm': 'Same centroids relative to the exact saved pre-probe frame; null before the probe.',
                'knife_material_force_n': 'Norm of recorded material reaction on the knife at the preceding completed substep; excludes guide, drive and board forces.',
                'reference_volume_m3': self.reference_volume, 'tetrahedra': len(self.tetrahedra),
                'cut_planes_m_in_execution_order': list(self.planes),
                'comparison_scope': 'Native DexLab measurements; original authors sampling and full configuration are unavailable, so these are not same-condition cross-method scores.'}
