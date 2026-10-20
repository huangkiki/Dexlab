"""Side-aware surfaces reconstructed from recorded cutting states.

The linked-volume path stores Hermite data on a uniform reference grid and
uses native cut histories to disconnect links. The older material-cell path is
kept for record compatibility. Neither path prescribes piece motion or adds a
visual separation displacement.
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


class LinkedVolumeSurface:
    """Linked reference volume with Hermite data and local dual contouring.

    The recorded cut planes identify candidate primal links. A link disconnects
    only after native particle histories on its two sides conflict, so shallow
    cuts retain their uncut bridge. Each cell is split into components of the
    remaining links; one QEF representative is generated per local region.
    Disconnected links create two coincident faces. Surface representatives use
    fixed trilinear weights in a compatible reconstructed TLMPM nodal field.
    """

    LOCAL_EDGES = tuple((a, b) for a in range(8) for b in range(a + 1, 8)
                        if np.count_nonzero(OFFSETS[a] != OFFSETS[b]) == 1)

    def __init__(self, reference, cut_planes, cut_axes=None, size=(.12, .06, .03),
                 grid_spacing=None, surface_spacing=None, shape='banana'):
        self.reference = np.asarray(reference, dtype=float)
        self.cut_planes = tuple(float(value) for value in cut_planes)
        self.cut_axes = (tuple(0 for _ in self.cut_planes) if cut_axes is None
                         else tuple(int(value) for value in cut_axes))
        self.size = np.asarray(size, dtype=float)
        self.shape = shape
        if (self.reference.ndim != 2 or self.reference.shape[1:] != (3,)
                or not len(self.reference) or not np.isfinite(self.reference).all()):
            raise ValueError('Linked volume requires a finite N x 3 reference sample')
        if (not self.cut_planes or len(set(zip(self.cut_axes, self.cut_planes, strict=True)))
                != len(self.cut_planes)):
            raise ValueError('Linked volume requires distinct recorded cuts')
        if len(self.cut_axes) != len(self.cut_planes) or any(axis not in (0, 1) for axis in self.cut_axes):
            raise ValueError('Recorded banana cuts must have x- or y-normal planes')
        if self.size.shape != (3,) or (self.size <= 0).any():
            raise ValueError('Invalid material size')
        if self.shape not in ('banana', 'block'):
            raise ValueError('Linked volume requires a supported material shape')

        if grid_spacing is None:
            differences = [np.diff(np.unique(self.reference[:, axis])) for axis in range(3)]
            positive = np.concatenate([values[values > 1e-12] for values in differences])
            inferred_particle_spacing = float(positive.min())
            self.motion_spacing = 2 * inferred_particle_spacing
        else:
            self.motion_spacing = float(grid_spacing)
            if not np.isfinite(self.motion_spacing) or self.motion_spacing <= 0:
                raise ValueError('TLMPM grid spacing must be finite and positive')
        self.surface_spacing = (self.motion_spacing / 2 if surface_spacing is None
                                else float(surface_spacing))
        if (not np.isfinite(self.surface_spacing) or self.surface_spacing <= 0
                or self.surface_spacing > self.motion_spacing):
            raise ValueError('Surface grid spacing must be finite and no larger than the TLMPM grid')
        self.motion_origin = np.array([-self.size[0] / 2, -self.size[1] / 2, 0.])
        self.motion_cells = np.rint(self.size / self.motion_spacing).astype(int)
        if not np.allclose(self.motion_cells * self.motion_spacing, self.size, atol=1e-10):
            raise ValueError('Reference samples do not define the configured TLMPM grid')

        lower = self.motion_origin - self.surface_spacing
        upper = self.motion_origin + self.size + self.surface_spacing
        if not np.allclose((upper-lower)/self.surface_spacing,
                           np.rint((upper-lower)/self.surface_spacing), atol=1e-10):
            raise ValueError('Surface spacing must tile the padded reference volume')
        self.node_shape = np.rint((upper-lower) / self.surface_spacing).astype(int) + 1
        axes = [lower[axis] + np.arange(self.node_shape[axis]) * self.surface_spacing
                for axis in range(3)]
        self.node_positions = np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1)
        self.node_level_set = self._level_set(self.node_positions.reshape(-1, 3)).reshape(
            tuple(self.node_shape))
        self.inside = self.node_level_set <= 0
        self.reference_tree = cKDTree(self.reference)
        self._component_cache = None

        self.boundary_edges = {}
        self.cut_edges = [dict() for _ in self.cut_planes]
        self._build_hermite_data()
        self.particle_nodes, self.particle_weights = self._motion_stencil(self.reference)
        self.motion_node_positions = self._build_motion_node_positions()

    def _level_set(self, points):
        points = np.asarray(points)
        if self.shape == 'block':
            centre = np.array([0., 0., self.size[2]/2])
            return np.max(np.abs(points-centre)-self.size/2, axis=-1)
        u = points[..., 0] / (self.size[0] / 2)
        centre_y = .035 * (u*u - .5)
        radius = .003 + .009 * np.maximum(0., 1-u*u)**.55
        radial = np.sqrt((points[..., 1]-centre_y)**2 + (points[..., 2]-.012)**2)-radius
        axial = np.abs(points[..., 0])-self.size[0]/2
        return np.maximum(radial, axial)

    def _normal(self, point):
        epsilon = self.surface_spacing * 1e-5
        gradient = np.array([
            self._level_set(point + np.eye(3)[axis]*epsilon)
            - self._level_set(point - np.eye(3)[axis]*epsilon)
            for axis in range(3)
        ]) / (2*epsilon)
        norm = np.linalg.norm(gradient)
        if norm <= 1e-14:
            raise ValueError('Degenerate original-boundary Hermite normal')
        return gradient / norm

    @staticmethod
    def _edge_key(first, second):
        first, second = np.asarray(first, dtype=int), np.asarray(second, dtype=int)
        difference = second-first
        axis = int(np.flatnonzero(difference)[0])
        low = np.minimum(first, second)
        return tuple(low), axis

    def _all_edges(self):
        for axis in range(3):
            limit = self.node_shape.copy()
            limit[axis] -= 1
            for low in np.ndindex(*limit):
                high = np.asarray(low) + np.eye(3, dtype=int)[axis]
                yield (tuple(low), axis), np.asarray(low), high

    def _boundary_intersection(self, first, second):
        low, high = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
        phi_low = float(self._level_set(low))
        for _ in range(30):
            middle = (low+high)/2
            phi_middle = float(self._level_set(middle))
            if (phi_low <= 0) == (phi_middle <= 0):
                low, phi_low = middle, phi_middle
            else:
                high = middle
        return (low+high)/2

    def _build_hermite_data(self):
        for key, low, high in self._all_edges():
            first_inside, second_inside = self.inside[tuple(low)], self.inside[tuple(high)]
            first = self.node_positions[tuple(low)]
            second = self.node_positions[tuple(high)]
            if first_inside != second_inside:
                point = self._boundary_intersection(first, second)
                inside_node = tuple(low if first_inside else high)
                self.boundary_edges[key] = (point, self._normal(point), inside_node)

        for cut, (axis, plane) in enumerate(zip(self.cut_axes, self.cut_planes, strict=True)):
            normal = np.eye(3)[axis]
            negative = self.reference[:, axis] < plane
            positive = ~negative
            if not negative.any() or not positive.any():
                raise ValueError('Recorded cut plane must leave material on both sides')
            for key, low, high in self._all_edges():
                if key[1] != axis or not (self.inside[tuple(low)] and self.inside[tuple(high)]):
                    continue
                first, second = self.node_positions[tuple(low)], self.node_positions[tuple(high)]
                signed_first, signed_second = first[axis]-plane, second[axis]-plane
                if not (signed_first < 0 <= signed_second):
                    continue
                fraction = -signed_first/(signed_second-signed_first)
                point = first + fraction*(second-first)
                distances, nearby = self.reference_tree.query(point, k=min(64, len(self.reference)))
                nearby = np.atleast_1d(nearby)[np.atleast_1d(distances)
                                                <= .9*self.motion_spacing]
                self.cut_edges[cut][key] = {
                    'point': point, 'normal': normal, 'negative_node': tuple(low),
                    'positive_node': tuple(high), 'nearby_anchors': nearby,
                }

    def _build_motion_node_positions(self):
        axes = [self.motion_origin[axis] + np.arange(self.motion_cells[axis]+1)*self.motion_spacing
                for axis in range(3)]
        return np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, 3)

    def _motion_stencil(self, points):
        points = np.asarray(points)
        fractional = (points-self.motion_origin)/self.motion_spacing
        base = np.floor(fractional).astype(int)
        local = fractional-base
        for axis in range(3):
            upper = base[:, axis] >= self.motion_cells[axis]
            base[upper, axis] = self.motion_cells[axis]-1
            local[upper, axis] = 1.
            lower = base[:, axis] < 0
            base[lower, axis] = 0
            local[lower, axis] = 0.
        factors = np.where(OFFSETS[None, :, :] == 1, local[:, None, :],
                           1-local[:, None, :])
        weights = factors.prod(axis=2)
        indices = base[:, None, :] + OFFSETS[None, :, :]
        nodes = np.ravel_multi_index(indices.transpose(2, 0, 1), tuple(self.motion_cells+1))
        return nodes, weights

    def _active_cut_edges(self, codes):
        active = {}
        for cut, candidates in enumerate(self.cut_edges):
            power = 3**cut
            for key, edge in candidates.items():
                digits = (codes[edge['nearby_anchors']]//power) % 3
                if 1 in digits and 2 in digits:
                    active[key] = (cut, edge)
        return active

    @staticmethod
    def _components(nodes, links):
        remaining = set(nodes)
        groups = []
        while remaining:
            seed = remaining.pop()
            group, frontier = {seed}, [seed]
            while frontier:
                node = frontier.pop()
                neighbours = {right if left == node else left for left, right in links
                              if left == node or right == node}
                fresh = neighbours & remaining
                remaining.difference_update(fresh)
                group.update(fresh)
                frontier.extend(fresh)
            groups.append(group)
        return groups

    @staticmethod
    def _qef(samples, lower, upper):
        points = np.asarray([sample[0] for sample in samples])
        normals = np.asarray([sample[1] for sample in samples])
        centre = points.mean(axis=0)
        u, singular, vt = np.linalg.svd(normals, full_matrices=False)
        coefficients = u.T @ (np.einsum('ij,ij->i', normals, points)-normals@centre)
        # Near-planar Hermite samples leave tangential directions weakly
        # constrained. Treat those directions as null and retain the mass
        # point instead of amplifying weak curvature into cell-edge spikes.
        # A 10% relative cutoff retains resolved planes/corners while dropping
        # the poorly constrained tangent of a locally smooth surface.
        inverse = np.divide(coefficients, singular, out=np.zeros_like(coefficients),
                            where=singular > max(singular[0]*.1, 1e-12))
        vertex = centre + vt.T@inverse
        return np.clip(vertex, lower, upper)

    def _cell_topology(self, active, codes, components):
        vertices, cut_vertices, anchors, vertex_codes, vertex_components = [], [], [], [], []
        cell_node_vertex = {}
        cell_limit = self.node_shape-1
        for cell in np.ndindex(*cell_limit):
            cell_array = np.asarray(cell)
            node_coordinates = [tuple(cell_array+offset) for offset in OFFSETS]
            inside_local = [index for index, node in enumerate(node_coordinates) if self.inside[node]]
            if not inside_local:
                continue
            links = []
            for first, second in self.LOCAL_EDGES:
                if first not in inside_local or second not in inside_local:
                    continue
                key = self._edge_key(node_coordinates[first], node_coordinates[second])
                if key not in active:
                    links.append((first, second))
            for group in self._components(inside_local, links):
                samples = []
                has_cut = False
                required_digits = {}
                for first, second in self.LOCAL_EDGES:
                    key = self._edge_key(node_coordinates[first], node_coordinates[second])
                    if key in self.boundary_edges:
                        point, normal, inside_node = self.boundary_edges[key]
                        local_inside = first if node_coordinates[first] == inside_node else second
                        if local_inside in group:
                            samples.append((point, normal))
                    if key in active:
                        cut, edge = active[key]
                        if first in group:
                            sign = -1 if node_coordinates[first] == edge['positive_node'] else 1
                            samples.append((edge['point'], sign*edge['normal']))
                            required_digits.setdefault(cut, set()).add(
                                2 if node_coordinates[first] == edge['positive_node'] else 1)
                            has_cut = True
                        if second in group:
                            sign = -1 if node_coordinates[second] == edge['positive_node'] else 1
                            samples.append((edge['point'], sign*edge['normal']))
                            required_digits.setdefault(cut, set()).add(
                                2 if node_coordinates[second] == edge['positive_node'] else 1)
                            has_cut = True
                if not samples:
                    continue
                lower = self.node_positions[cell]
                upper = self.node_positions[tuple(cell_array+1)]
                vertex = self._qef(samples, lower, upper)
                vertex = np.clip(vertex, self.motion_origin, self.motion_origin+self.size)
                distances, candidate_anchors = self.reference_tree.query(
                    vertex, k=min(128, len(self.reference)))
                candidate_anchors = np.atleast_1d(candidate_anchors)
                distances = np.atleast_1d(distances)
                local = candidate_anchors[distances <= 1.25*self.motion_spacing]
                if len(local):
                    candidate_anchors = local
                for cut, (axis, plane) in enumerate(
                        zip(self.cut_axes, self.cut_planes, strict=True)):
                    digits = (codes[candidate_anchors]//(3**cut)) % 3
                    signed = vertex[axis]-plane
                    if 1 in digits and 2 in digits and abs(signed) > 1e-10:
                        digit = 1 if signed < 0 else 2
                        selected = candidate_anchors[digits == digit]
                        if len(selected):
                            candidate_anchors = selected
                for cut, digits in required_digits.items():
                    if len(digits) == 1:
                        digit = next(iter(digits))
                        selected = candidate_anchors[
                            (codes[candidate_anchors]//(3**cut)) % 3 == digit]
                        if len(selected):
                            candidate_anchors = selected
                if not len(candidate_anchors):
                    raise ValueError('Linked-volume region has no particle with its cut history')
                labels, counts = np.unique(components[candidate_anchors], return_counts=True)
                component = labels[counts.argmax()]
                matching = candidate_anchors[components[candidate_anchors] == component]
                anchor = int(matching[np.argmin(np.linalg.norm(self.reference[matching]-vertex, axis=1))])
                vertex_id = len(vertices)
                vertices.append(vertex)
                cut_vertices.append(has_cut)
                anchors.append(anchor)
                vertex_codes.append(int(codes[anchor]))
                vertex_components.append(int(components[anchor]))
                for index in group:
                    cell_node_vertex[cell, node_coordinates[index]] = vertex_id
        return (np.asarray(vertices), np.asarray(cut_vertices), np.asarray(anchors),
                np.asarray(vertex_codes), np.asarray(vertex_components), cell_node_vertex)

    def _incident_cells(self, key):
        low, axis = np.asarray(key[0]), key[1]
        if axis == 0:
            offsets = ((0, -1, -1), (0, 0, -1), (0, 0, 0), (0, -1, 0))
        elif axis == 1:
            offsets = ((-1, 0, -1), (-1, 0, 0), (0, 0, 0), (0, 0, -1))
        else:
            offsets = ((-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0))
        limit = self.node_shape-1
        return [tuple(low+offset) for offset in offsets
                if np.all(low+offset >= 0) and np.all(low+offset < limit)]

    @staticmethod
    def _append_quad(faces, quad, vertices, normal):
        if len(quad) != 4 or len(set(quad)) != 4:
            return
        a, b, c, d = quad
        # A clipped dual quad can be concave. Orient its whole area, then use
        # the diagonal with the better minimum projected triangle area.
        oriented = np.cross(vertices[c]-vertices[a], vertices[d]-vertices[b])
        if np.dot(oriented, normal) < 0:
            b, d = d, b
        candidates = (((a, b, c), (a, c, d)), ((a, b, d), (b, c, d)))
        def quality(pair):
            points = vertices[np.asarray(pair)]
            areas = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0])
            return float(np.min(areas@normal))
        faces.extend(max(candidates, key=quality))

    def _faces(self, vertices, cell_node_vertex, active):
        faces = []
        for key, (_, normal, inside_node) in self.boundary_edges.items():
            quad = [cell_node_vertex.get((cell, inside_node)) for cell in self._incident_cells(key)]
            if all(vertex is not None for vertex in quad):
                self._append_quad(faces, quad, vertices, normal)
        for key, (_, edge) in active.items():
            cells = self._incident_cells(key)
            negative = [cell_node_vertex.get((cell, edge['negative_node'])) for cell in cells]
            positive = [cell_node_vertex.get((cell, edge['positive_node'])) for cell in cells]
            if all(vertex is not None for vertex in negative):
                self._append_quad(faces, negative, vertices, edge['normal'])
            if all(vertex is not None for vertex in positive):
                self._append_quad(faces, positive, vertices, -edge['normal'])
        return np.asarray(faces, dtype=np.int64)

    def _duplicate_seam_vertices(self, rest, faces, cut_vertices, anchors,
                                 vertex_codes, vertex_components, codes, components):
        """Give each side its own representative when a face meets a cut seam."""
        rest = list(rest)
        cut_vertices = list(cut_vertices)
        anchors = list(anchors)
        vertex_codes = list(vertex_codes)
        vertex_components = list(vertex_components)
        faces = faces.copy()
        component_particles = {
            int(component): np.flatnonzero(components == component)
            for component in np.unique(components)
        }
        duplicates = {}
        tolerance = self.surface_spacing*1e-6

        for row, face in enumerate(faces):
            face_components = np.asarray(vertex_components, dtype=int)[face]
            if np.all(face_components == face_components[0]):
                continue

            points = np.asarray(rest)[face]
            on_seam = np.zeros(3, dtype=bool)
            for axis, plane in zip(self.cut_axes, self.cut_planes, strict=True):
                on_seam |= np.abs(points[:, axis]-plane) <= tolerance
            off_seam = ~on_seam
            if not off_seam.any() or len(np.unique(face_components[off_seam])) != 1:
                continue
            component = int(face_components[off_seam][0])
            source = np.flatnonzero(face_components == component)[0]
            code = int(vertex_codes[face[source]])
            candidates = component_particles[component]
            compatible = np.asarray([
                particle for particle in candidates
                if histories_compatible(code, int(codes[particle]))
            ], dtype=int)
            if not len(compatible):
                raise ValueError('Cut seam has no compatible material anchor')
            for column in np.flatnonzero(on_seam & (face_components != component)):
                original = int(face[column])
                key = original, component, code
                if key not in duplicates:
                    point = np.asarray(rest[original])
                    anchor = int(compatible[np.argmin(
                        np.linalg.norm(self.reference[compatible]-point, axis=1))])
                    duplicates[key] = len(rest)
                    rest.append(point.copy())
                    cut_vertices.append(True)
                    anchors.append(anchor)
                    vertex_codes.append(code)
                    vertex_components.append(component)
                faces[row, column] = duplicates[key]
        return (np.asarray(rest), faces, np.asarray(cut_vertices), np.asarray(anchors),
                np.asarray(vertex_codes), np.asarray(vertex_components))

    def _compatible_motion(self, rest, anchors, query_codes, query_components,
                           positions, deformation, codes, components):
        nodes, weights = self._motion_stencil(rest)
        moved = np.empty_like(rest)
        for component, code in sorted(set(zip(query_components, query_codes, strict=True))):
            vertices = np.flatnonzero((query_components == component) & (query_codes == code))
            selected = np.asarray([p for p in np.flatnonzero(components == component)
                                   if histories_compatible(int(code), int(codes[p]))], dtype=int)
            if not len(selected):
                raise ValueError('Surface region has no compatible TLMPM field')
            field = np.zeros_like(self.motion_node_positions)
            needed_nodes = np.unique(nodes[vertices])
            # Historical records do not contain the logical-grid field. Each
            # compatible particle therefore predicts a fixed motion node from
            # its saved x/F state, and a local Gaussian average reconstructs
            # that node. This remains exact for a common affine field while a
            # wider neighbourhood suppresses coarse boundary-particle noise.
            tree = cKDTree(self.reference[selected])
            distances, neighbours = tree.query(
                self.motion_node_positions[needed_nodes], k=min(64, len(selected)))
            distances, neighbours = np.asarray(distances), np.asarray(neighbours)
            if distances.ndim == 1:
                shape = (1, -1) if len(needed_nodes) == 1 else (-1, 1)
                distances = distances.reshape(shape)
                neighbours = neighbours.reshape(shape)
            particle_indices = selected[neighbours]
            weights_to_node = np.exp(-.5*(distances/self.motion_spacing)**2)
            node_offsets = (self.motion_node_positions[needed_nodes, None, :]
                            - self.reference[particle_indices])
            predictions = positions[particle_indices] + np.einsum(
                'pnij,pnj->pni', deformation[particle_indices], node_offsets)
            field[needed_nodes] = np.einsum(
                'pn,pni->pi', weights_to_node, predictions
            ) / weights_to_node.sum(axis=1, keepdims=True)
            for vertex in vertices:
                local_nodes = nodes[vertex]
                moved[vertex] = weights[vertex]@field[local_nodes]
        return moved

    def _component_level_set(self, points, constraints):
        values = [self._level_set(points)]
        for cut, digit in constraints.items():
            axis, plane = self.cut_axes[cut], self.cut_planes[cut]
            values.append(points[..., axis]-plane if digit == 1 else plane-points[..., axis])
        return np.maximum.reduce(values)

    def _component_normal(self, point, constraints):
        epsilon = self.surface_spacing*1e-5
        gradient = np.array([
            self._component_level_set(point + np.eye(3)[axis]*epsilon, constraints)
            - self._component_level_set(point - np.eye(3)[axis]*epsilon, constraints)
            for axis in range(3)
        ]) / (2*epsilon)
        norm = np.linalg.norm(gradient)
        if norm <= 1e-14:
            raise ValueError('Degenerate component-boundary Hermite normal')
        return gradient/norm

    def _component_boundary_intersection(self, first, second, constraints):
        low, high = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
        phi_low = float(self._component_level_set(low, constraints))
        for _ in range(30):
            middle = (low+high)/2
            phi_middle = float(self._component_level_set(middle, constraints))
            if (phi_low <= 0) == (phi_middle <= 0):
                low, phi_low = middle, phi_middle
            else:
                high = middle
        return (low+high)/2

    def _disconnected_component_mesh(self, positions, deformation, codes, components):
        """Reconstruct each observed native component as a closed local volume."""
        key = (codes.tobytes(), components.tobytes())
        if self._component_cache is not None and self._component_cache[0] == key:
            return self._move_components(
                self._component_cache[1], positions, deformation, codes, components)
        rest, faces, anchors, cut_vertices = [], [], [], []
        query_codes, query_components = [], []
        for component in np.unique(components):
            particles = np.flatnonzero(components == component)
            constraints = {}
            for cut in range(len(self.cut_planes)):
                digits = np.unique((codes[particles]//(3**cut)) % 3)
                labelled = digits[digits != 0]
                if len(labelled) == 1:
                    constraints[cut] = int(labelled[0])

            phi = self._component_level_set(self.node_positions, constraints)
            inside = phi <= 0
            cell_vertices = {}
            component_offset = len(rest)
            for cell in np.ndindex(*(self.node_shape-1)):
                cell_array = np.asarray(cell)
                nodes = [tuple(cell_array+offset) for offset in OFFSETS]
                samples = []
                for first, second in self.LOCAL_EDGES:
                    if inside[nodes[first]] == inside[nodes[second]]:
                        continue
                    point = self._component_boundary_intersection(
                        self.node_positions[nodes[first]], self.node_positions[nodes[second]],
                        constraints)
                    samples.append((point, self._component_normal(point, constraints)))
                if not samples:
                    continue
                lower = self.node_positions[cell]
                upper = self.node_positions[tuple(cell_array+1)]
                vertex = self._qef(samples, lower, upper)
                for cut in constraints:
                    axis, plane = self.cut_axes[cut], self.cut_planes[cut]
                    # Remove finite-difference/SVD roundoff at an exact cut
                    # plane before classifying its rim (at most 30 nm here).
                    if abs(vertex[axis]-plane) <= self.surface_spacing*1e-5:
                        vertex[axis] = plane
                anchor = int(particles[np.argmin(
                    np.linalg.norm(self.reference[particles]-vertex, axis=1))])
                cell_vertices[cell] = len(rest)
                rest.append(vertex)
                anchors.append(anchor)
                query_codes.append(int(codes[anchor]))
                query_components.append(int(component))
                cut_vertices.append(any(
                    abs(vertex[self.cut_axes[cut]]-self.cut_planes[cut])
                    <= self.surface_spacing*1e-7 for cut in constraints))

            component_rest = np.asarray(rest)
            for key, low, high in self._all_edges():
                if inside[tuple(low)] == inside[tuple(high)]:
                    continue
                quad = [cell_vertices.get(cell) for cell in self._incident_cells(key)]
                if not all(vertex is not None for vertex in quad):
                    continue
                point = self._component_boundary_intersection(
                    self.node_positions[tuple(low)], self.node_positions[tuple(high)], constraints)
                self._append_quad(faces, quad, component_rest,
                                  self._component_normal(point, constraints))

            if len(rest) == component_offset:
                raise ValueError('Native component produced no reconstructed surface')

        rest = np.asarray(rest)
        faces = np.asarray(faces, dtype=np.int64)
        anchors = np.asarray(anchors, dtype=np.int64)
        query_codes = np.asarray(query_codes, dtype=np.int64)
        query_components = np.asarray(query_components, dtype=np.int64)
        topology = (rest, faces, anchors, query_codes, query_components,
                    np.asarray(cut_vertices, dtype=bool))
        self._component_cache = (key, topology)
        return self._move_components(topology, positions, deformation, codes, components)

    def _move_components(self, topology, positions, deformation, codes, components):
        """Reuse only reference topology; evaluate the current x/F field every time."""
        rest, faces, anchors, query_codes, query_components, cut_vertices = topology
        moved = self._compatible_motion(
            rest, anchors, query_codes, query_components,
            positions, deformation, codes, components)
        for component in np.unique(query_components):
            particles = np.flatnonzero(components == component)
            design = np.column_stack((self.reference[particles], np.ones(len(particles))))
            coefficients, _, _, _ = np.linalg.lstsq(design, positions[particles], rcond=None)
            fitted = design@coefficients
            if (np.linalg.matrix_rank(design) == 4
                    and np.max(np.linalg.norm(fitted-positions[particles], axis=1)) <= 1e-12):
                vertices = query_components == component
                moved[vertices] = np.column_stack(
                    (rest[vertices], np.ones(np.count_nonzero(vertices))))@coefficients
        # The caller may own/mutate its returned arrays without corrupting the cache.
        return moved, faces.copy(), rest.copy(), cut_vertices.copy()

    def mesh(self, positions, deformation, codes, components):
        positions = np.asarray(positions)
        deformation = np.asarray(deformation)
        codes = np.asarray(codes, dtype=np.int64)
        components = np.asarray(components, dtype=np.int64)
        if (positions.shape != self.reference.shape or deformation.shape != (len(self.reference), 3, 3)
                or codes.shape != (len(self.reference),) or components.shape != codes.shape):
            raise ValueError('Linked-volume state shapes do not match the reference sample')
        if len(np.unique(components)) > 1:
            return self._disconnected_component_mesh(
                positions, deformation, codes, components)
        active = self._active_cut_edges(codes)
        rest, cut_vertices, anchors, vertex_codes, vertex_components, lookup = self._cell_topology(
            active, codes, components)
        faces = self._faces(rest, lookup, active)
        if not len(faces):
            raise ValueError('Linked-volume reconstruction produced no closed surface')
        rest, faces, cut_vertices, anchors, vertex_codes, vertex_components = (
            self._duplicate_seam_vertices(
                rest, faces, cut_vertices, anchors, vertex_codes,
                vertex_components, codes, components))
        used, inverse = np.unique(faces, return_inverse=True)
        moved = self._compatible_motion(rest[used], anchors[used], vertex_codes[used],
                                        vertex_components[used], positions, deformation,
                                        codes, components)
        return moved, inverse.reshape(-1, 3), rest[used], cut_vertices[used]


# Keep the original internal name for callers pinned to the earlier renderer.
BananaSkin = LinkedVolumeSurface
