"""Display measurements derived from saved states, independent of task scoring.

The face opening is an affine material-face estimate. The volume is the signed
volume of fixed, interior reference tetrahedra, not a rendered-surface volume.
Neither estimator is asserted to reproduce BladeMaster's unpublished sampling.
"""

from itertools import permutations, product

import numpy as np

from dexlab.cutting_geometry import recorded_cut_geometry
from dexlab.cutting_score import SCORING_ACCEPTANCE, grid_components


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


def face_pairs(reference, plane, spacing, axis=0):
    """Pair material neighbours across an axis-normal plane."""
    left_x = reference[reference[:, axis] < plane, axis].max()
    right_x = reference[reference[:, axis] > plane, axis].min()
    if not np.isclose(right_x - left_x, spacing, atol=1e-12):
        raise ValueError('The cut must lie between adjacent material lattice planes')
    other = reference[:, [a for a in range(3) if a != axis]]
    transverse = np.rint((other - other.min(axis=0)) / spacing).astype(int)
    right = {tuple(transverse[i]): i for i in np.flatnonzero(np.isclose(reference[:, axis], right_x))}
    pairs = [(i, right[tuple(transverse[i])]) for i in np.flatnonzero(np.isclose(reference[:, axis], left_x))
             if tuple(transverse[i]) in right]
    pairs = np.asarray(pairs, dtype=int).reshape(-1, 2)
    locations = reference[pairs[:, 0]].copy()
    locations[:, axis] = plane
    return pairs, locations


def face_opening(reference, positions, deformation, codes, pairs, locations, cut_index, axis=0):
    """Signed normal opening of faces with opposing native histories for this cut."""
    digits = codes[pairs] // (3 ** cut_index) % 3
    valid = (digits[:, 0] != 0) & (digits[:, 1] != 0) & (digits[:, 0] != digits[:, 1])
    if not valid.any():
        return None, 0
    owners, rest = pairs[valid], locations[valid]
    moved = positions[owners] + np.einsum(
        'pkij,pkj->pki', deformation[owners], rest[:, None] - reference[owners])
    return float(np.mean(moved[:, 1, axis] - moved[:, 0, axis]) * 1000), int(valid.sum())


class ReplayMeasurements:
    """Fixed spatial regions and estimators for one immutable recorded run."""

    def __init__(self, states, trace, manifest):
        self.states, self.trace, self.manifest = states, trace, manifest
        self.reference = states['reference']
        self.task = manifest['task']
        spacing = manifest['config']['grid_spacing'] / 2
        self.planes, self.axes = recorded_cut_geometry(trace, spacing)
        self.pairs = [face_pairs(self.reference, plane, spacing, axis)
                      for plane, axis in zip(self.planes, self.axes, strict=True)]
        self.regions = np.searchsorted(sorted(plane for plane, axis in zip(self.planes, self.axes)
                                              if axis == 0), self.reference[:, 0])
        if self.task == 'tofu-scoring':
            self.base = self.reference[:, 2] < SCORING_ACCEPTANCE['base_height_m']
            self.tetrahedra = reference_tetrahedra(self.reference, spacing, self.base)
        else:
            included = (1,) if self.task == 'tofu-sequential' else range(len(self.planes) + 1)
            self.tetrahedra = np.concatenate([
                reference_tetrahedra(self.reference, spacing, self.regions == region)
                for region in included])
        self.reference_volume = float(signed_volumes(self.reference, self.tetrahedra).sum())
        if self.reference_volume <= 0:
            raise ValueError('No interior reference volume available')
        self.motion_start = (4. if manifest.get('motion_protocol') in ('knife-push', 'no-push')
                             else manifest['probe_time_s'])
        if manifest.get('motion_protocol') in ('cut-push', 'cut-no-push'):
            self.motion_start = 5.3 if self.task == 'banana' else 3.3
        if manifest.get('motion_start_time_s', self.motion_start) != self.motion_start:
            raise ValueError('Motion baseline disagrees with the recorded protocol')
        self.probe_frame = (None if self.motion_start is None else
                            int(np.argmin(abs(states['time'] - self.motion_start))))
        if self.probe_frame is not None and not np.isclose(states['time'][self.probe_frame], self.motion_start):
            raise ValueError('The initial motion needs an exact saved pre-probe frame')

    def frame(self, index):
        time = float(self.states['time'][index])
        positions = self.states['position'][index]
        deformation = self.states['deformation'][index]
        codes = self.states['sides'][index]
        trace_index = max(0, int(np.searchsorted(self.trace['time_s'], time + 1e-12, side='right')) - 1)
        if index == 0:
            phase = 'Initial'
        elif self.probe_frame is not None and time > self.motion_start:
            if self.manifest.get('motion_protocol') in ('cut-push', 'cut-no-push'):
                elapsed = time - self.motion_start
                phase = ('Clear board / blade stays in cut' if elapsed <= .2 else
                         ('Knife-face push' if self.manifest['motion_protocol'] == 'cut-push' else 'No lateral push')
                         if elapsed <= 1.4 else 'Withdraw' if elapsed <= 2. else 'Settle')
            elif self.manifest.get('motion_protocol') == 'knife-push':
                phase = ('Re-entering kerf' if time <= 4.8 else 'Knife-face push' if time <= 6.
                         else 'Withdrawing' if time <= 6.6 else 'Settling')
            else:
                phase = 'No-push control' if self.manifest.get('motion_protocol') == 'no-push' else 'Motion probe'
        elif self.trace['cutting_active'][trace_index]:
            phase = f'Cut {int(self.trace["cut_index"][trace_index])+1}'
        else:
            edge = self.trace['blade_position_m'][trace_index, 2] - self.manifest['config']['blade_half_size'][2]
            phase = 'Knife clear' if edge > self.manifest['config']['size'][2] else 'Withdrawing'
        gaps, counts = zip(*(face_opening(self.reference, positions, deformation, codes, pairs,
                                        locations, cut, self.axes[cut])
                             for cut, (pairs, locations) in enumerate(self.pairs)))
        volumes = signed_volumes(positions, self.tetrahedra)
        displacement = [] if self.task == 'tofu-scoring' else [float(np.mean(positions[self.regions == region, 0] -
                                     self.reference[self.regions == region, 0]) * 1000)
                        for region in range(len(self.planes) + 1)]
        probe_displacement = None
        if self.probe_frame is not None and index >= self.probe_frame:
            before = self.states['position'][self.probe_frame]
            probe_displacement = [float(np.mean(positions[self.regions == region, 0] -
                                               before[self.regions == region, 0]) * 1000)
                                  for region in range(len(self.planes) + 1)]
        result = {'state_frame': index, 'trace_frame': trace_index, 'time_s': time, 'phase': phase,
                'face_opening_mm': list(gaps), 'paired_faces': list(counts),
                'interior_volume_change_percent': float((volumes.sum() / self.reference_volume - 1) * 100),
                'inverted_tetrahedra': int((volumes <= 0).sum()),
                'centroid_x_from_start_mm': displacement,
                'centroid_x_from_probe_mm': probe_displacement,
                'motion_protocol': self.manifest.get('motion_protocol',
                    None if self.motion_start is None else 'impulse'),
                'knife_on_material_x_n': (-float(self.trace['material_reaction_n'][trace_index, 0])
                                          if index else 0.),
                'knife_on_material_n': (-self.trace['material_reaction_n'][trace_index]).tolist()
                                      if index else [0., 0., 0.],
                'dynamic_viscosity_pa_s': self.manifest['config'].get('dynamic_viscosity', 0.),
                'knife_material_force_n': (float(np.linalg.norm(self.trace['material_reaction_n'][trace_index]))
                                           if index else 0.)}
        if self.task == 'tofu-scoring':
            components = len(grid_components(self.states['nodes'], self.states['weights'], codes)[1])
            result.update(native_components=components,
                          base_intact=components == 1 and not bool(codes[self.base].any()),
                          blade_depth_mm=max(0., (self.manifest['config']['size'][2] -
                              self.trace['blade_position_m'][trace_index, 2] +
                              self.manifest['config']['blade_half_size'][2]) * 1000))
        return result

    def definitions(self):
        result = {'face_opening_mm': 'Mean signed normal distance between affine images of the same reference face; only opposing nonzero native digits for that cut are included. Null means no eligible pairs.',
                'interior_volume_change_percent': '100 * (current signed tetrahedral volume / reference volume - 1); six tetrahedra per complete interior lattice cell, excluding cells crossing recorded cut planes. Middle third for two-cut tofu, all sampled piece interiors otherwise. Inverted tets are counted, never hidden with abs().',
                'centroid_x_from_start_mm': 'Equal-mass native particle centroids of fixed reference regions, ordered left to right; displacement from reference positions.',
                'centroid_x_from_probe_mm': 'Same centroids relative to the exact saved motion-start frame; null before it. Continuous push: final-cut end (tofu 3.30 s, banana 5.30 s); legacy knife-push/no-push: 4.00 s; impulse: probe_time_s.',
                'knife_on_material_x_n': 'Negative of recorded material reaction on the knife in world x at the preceding completed substep; negative means the knife pushes material left. Excludes drive and board.',
                'knife_on_material_n': 'World xyz force of the knife on the material, N; negative of the saved material reaction on the knife at the preceding completed substep. Zero at the initial state. Excludes drive and board.',
                'dynamic_viscosity_pa_s': 'Newtonian dynamic viscosity from the saved material configuration, Pa s; missing historical configuration fields mean the elastic value zero.',
                'motion_start_time_s': self.motion_start,
                'knife_material_force_n': 'Norm of recorded material reaction on the knife at the preceding completed substep; excludes guide, drive and board forces.',
                'reference_volume_m3': self.reference_volume, 'tetrahedra': len(self.tetrahedra),
                'cut_planes_m_in_execution_order': list(self.planes),
                'cut_plane_source': 'Median recorded blade position while cutting; uncut controls use the densest recorded position cluster. Axis-aligned paths that sweep laterally by more than half a material spacing are rejected.',
                'cut_normal_axes': list(self.axes),
                'comparison_scope': 'Native DexLab measurements; original authors sampling and full configuration are unavailable, so these are not same-condition cross-method scores.'}
        if self.task == 'tofu-scoring':
            result.update(interior_volume_change_percent='Signed tetrahedral volume change of the fixed reference base below 15 mm; not the volume of a separated piece.',
                          blade_depth_mm='Positive downward distance of the recorded knife edge below the original material top; zero after withdrawal. Not prescribed groove depth.',
                          native_components='Number of components in the native reference transfer graph, including unassigned bridges.',
                          base_intact='One native component and no assigned cut digits in the fixed lower 15 mm of reference material; an empty gap metric does not establish intactness.')
        return result
