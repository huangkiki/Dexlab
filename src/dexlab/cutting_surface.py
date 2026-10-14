"""Side-aware material-cell surface extracted from recorded cutting states.

Each point represents one material voxel. Faces between conflicting histories
become exposed; compatible neighbours retain their shared surface vertices.
No trajectory, cut time or separation displacement is prescribed here.
"""

from itertools import product

import numpy as np
from scipy.spatial import cKDTree

from dexlab.cutting_score import histories_compatible


OFFSETS = np.array(list(product((0, 1), repeat=3)), dtype=int)
FACES = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
         (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
DIRECTIONS = ((-1, 0, 0), (1, 0, 0), (0, -1, 0),
              (0, 1, 0), (0, 0, -1), (0, 0, 1))


class MaterialSurface:
    """Fixed material inventory with observed, persistent cut connectivity."""

    def __init__(self, reference, spacing):
        self.reference = np.asarray(reference)
        self.spacing = spacing
        self.origin = self.reference.min(axis=0) - spacing / 2
        self.cells = np.rint((self.reference - self.origin) / spacing - .5).astype(int)
        if not np.allclose(self.origin + (self.cells + .5) * spacing, reference, atol=1e-12):
            raise ValueError('Surface extraction requires the recorded material lattice')
        self.inventory = {tuple(cell): p for p, cell in enumerate(self.cells)}
        self.corner_owners = {}
        for p, cell in enumerate(self.cells):
            for offset in OFFSETS:
                self.corner_owners.setdefault(tuple(cell + offset), []).append(p)
        _, self.neighbours = cKDTree(reference).query(reference, k=min(32, len(reference)))

    def estimated_deformation(self, positions, codes):
        """Affine reconstruction for older records lacking saved F; never cross a cut."""
        deformation = []
        for p, neighbours in enumerate(self.neighbours):
            selected = [q for q in neighbours if histories_compatible(int(codes[p]), int(codes[q]))]
            source = self.reference[selected] - self.reference[p]
            target = positions[selected] - positions[p]
            gradient = np.linalg.lstsq(source, target, rcond=None)[0].T
            deformation.append(gradient)
        return np.asarray(deformation)

    def mesh(self, positions, codes, deformation=None):
        if deformation is None:
            deformation = self.estimated_deformation(positions, codes)
        vertices, rest_vertices, cut_vertices, quads, keys = [], [], [], [], {}
        corner_groups = {}
        for p, cell in enumerate(self.cells):
            for direction, face in zip(DIRECTIONS, FACES, strict=True):
                q = self.inventory.get(tuple(cell + direction))
                if q is not None and histories_compatible(int(codes[p]), int(codes[q])):
                    continue
                polygon = []
                for offset in OFFSETS[list(face)]:
                    corner = tuple(cell + offset)
                    if (corner, p) not in corner_groups:
                        connected = {p}
                        while True:
                            grown = connected | {q for q in self.corner_owners[corner] if any(
                                histories_compatible(int(codes[q]), int(codes[r])) for r in connected)}
                            if grown == connected:
                                break
                            connected = grown
                        owners = tuple(sorted(connected))
                        for owner in owners:
                            corner_groups[corner, owner] = owners
                    owners = corner_groups[corner, p]
                    key = (corner, owners)
                    if key not in keys:
                        rest = self.origin + np.asarray(corner) * self.spacing
                        selected = np.asarray(owners)
                        moved = positions[selected] + np.einsum(
                            'pij,pj->pi', deformation[selected], rest - self.reference[selected])
                        keys[key] = len(vertices)
                        vertices.append(moved.mean(axis=0))
                        rest_vertices.append(rest)
                        cut_vertices.append(q is not None)
                    elif q is not None:
                        cut_vertices[keys[key]] = True
                    polygon.append(keys[key])
                quads.append(polygon)
        return np.asarray(vertices), np.asarray(quads, dtype=np.int64), np.asarray(rest_vertices), np.asarray(cut_vertices)


class BananaSkin:
    """Authored reference skin with locally history-aware straight-cut seams.

    Native side conflicts expose cut faces progressively. Unassigned regions
    weld the two skin representatives and retain the uncut bridge. This is a
    particle-affine display embedding, not the paper's dual-contouring method.
    """

    PLANES = (-.03, 0., .03)

    def __init__(self, reference):
        self.reference = np.asarray(reference)
        self.rest, self.faces, self.cap_vertices, self.face_cut, self.anchors = self._rest_mesh()
        self.particle_regions = np.searchsorted(self.PLANES, self.reference[:, 0])
        self.vertex_regions = self.particle_regions[self.anchors]
        distances, self.neighbours = cKDTree(reference).query(self.rest, k=min(64, len(reference)))
        self.neighbours[:, 0] = self.anchors
        distances[:, 0] = np.linalg.norm(self.rest-reference[self.anchors], axis=1)
        self.weights = np.exp(-.5*(distances/.006)**2)
        self.seams = []
        by_position = {}
        for i, point in enumerate(self.rest):
            key = tuple(np.rint(point*1e12).astype(np.int64))
            if key in by_position:
                self.seams.append((by_position[key], i))
            else:
                by_position[key] = i

    def mesh(self, positions, deformation, codes, components):
        anchors = self.anchors.copy()
        # The authored seam lies in reference space, while a deformed cut can
        # assign its nearest reference particle to the neighbouring piece.
        # Bind each authored interval to its dominant observed component;
        # local histories still decide partial openings inside that component.
        for region in range(len(self.PLANES)+1):
            candidates = np.flatnonzero(self.particle_regions == region)
            labels, counts = np.unique(components[candidates], return_counts=True)
            component = labels[counts.argmax()]
            misplaced = (self.vertex_regions == region) & (components[anchors] != component)
            if misplaced.any():
                candidates = candidates[components[candidates] == component]
                _, nearest = cKDTree(self.reference[candidates]).query(self.rest[misplaced])
                anchors[misplaced] = candidates[nearest]
        neighbours, weights = self.neighbours.copy(), self.weights.copy()
        neighbours[:, 0] = anchors
        distances = np.linalg.norm(self.rest-self.reference[anchors], axis=1)
        weights[:, 0] = np.exp(-.5*(distances/.006)**2)
        anchor_codes = codes[anchors]
        anchor_components = components[anchors]
        compatible = components[neighbours] == anchor_components[:, None]
        for cut in range(3):
            first = (anchor_codes // 3**cut % 3)[:, None]
            second = codes[neighbours] // 3**cut % 3
            compatible &= (first == 0) | (second == 0) | (first == second)
        weights *= compatible
        weights /= weights.sum(axis=1, keepdims=True)
        mapped = positions[neighbours] + np.einsum(
            'pkij,pkj->pki', deformation[neighbours], self.rest[:, None]-self.reference[neighbours])
        moved = np.einsum('pk,pki->pi', weights, mapped)
        representatives = np.arange(len(self.rest))
        separated = np.zeros(len(self.rest), dtype=bool)
        for left, right in self.seams:
            if (anchor_components[left] == anchor_components[right]
                    and histories_compatible(int(anchor_codes[left]), int(anchor_codes[right]))):
                representatives[right] = left
                moved[left] = (moved[left]+moved[right])/2
            else:
                separated[[left, right]] = True
        visible = (self.face_cut < 0) | separated[self.faces].all(axis=1)
        faces = representatives[self.faces[visible]]
        used, inverse = np.unique(faces, return_inverse=True)
        return moved[used], inverse.reshape(-1, 3), self.rest[used], self.cap_vertices[used]

    def _rest_mesh(self):
        vertices, faces, caps, face_cut, anchors = [], [], [], [], []
        sectors = 64
        theta = np.arange(sectors)*2*np.pi/sectors
        boundaries = (-.06, *self.PLANES, .06)
        for low, high in zip(boundaries[:-1], boundaries[1:], strict=True):
            start = len(vertices)
            rings = max(8, round((high-low)/.0015))+1
            axial = np.linspace(low, high, rings)
            piece = []
            for x in axial:
                u = x/.06
                radius = (.003+.009*max(0., 1-u*u)**.55)*(1+.025*np.cos(5*theta+.3))
                piece.extend(np.column_stack((np.full(sectors, x),
                             .035*(u*u-.5)+radius*np.cos(theta), .012+radius*np.sin(theta))))
            for ring in range(rings-1):
                for angle in range(sectors):
                    a = start+ring*sectors+angle
                    b = start+ring*sectors+(angle+1)%sectors
                    faces.extend(((a,b,b+sectors), (a,b+sectors,a+sectors)))
                    face_cut.extend((-1, -1))
            is_cap = [False]*len(piece)
            for ring, sign in [(0, -1), (rings-1, 1)]:
                x = axial[ring]
                cut = self.PLANES.index(x) if x in self.PLANES else -1
                center = np.array([x, .035*((x/.06)**2-.5), .012])
                outer = np.asarray(piece[ring*sectors:(ring+1)*sectors])
                is_cap[ring*sectors:(ring+1)*sectors] = [True]*sectors
                previous = np.arange(sectors)+start+ring*sectors
                for scale in (.75, .5, .25):
                    current = np.arange(sectors)+start+len(piece)
                    piece.extend(center+(outer-center)*scale)
                    is_cap.extend([True]*sectors)
                    for angle in range(sectors):
                        nxt = (angle+1)%sectors
                        triangles = [(previous[angle],current[nxt],current[angle]),
                                     (previous[angle],previous[nxt],current[nxt])]
                        faces.extend(triangles if sign > 0 else [t[::-1] for t in triangles])
                        face_cut.extend((cut, cut))
                    previous = current
                center_index = start+len(piece)
                piece.append(center)
                is_cap.append(True)
                for angle in range(sectors):
                    triangle = (previous[angle], previous[(angle+1)%sectors], center_index)
                    faces.append(triangle if sign > 0 else triangle[::-1])
                    face_cut.append(cut)
            piece = np.asarray(piece)
            selected = np.flatnonzero((self.reference[:, 0] > low) & (self.reference[:, 0] < high))
            _, nearest = cKDTree(self.reference[selected]).query(piece)
            vertices.extend(piece)
            caps.extend(is_cap)
            anchors.extend(selected[nearest])
        return (np.asarray(vertices), np.asarray(faces), np.asarray(caps),
                np.asarray(face_cut), np.asarray(anchors))
