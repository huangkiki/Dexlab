"""A surface may explain recorded motion; it must not invent separation."""

import unittest

import numpy as np

try:
    from dexlab.cutting_surface import BananaSkin, MaterialSurface
except ModuleNotFoundError as error:
    if error.name != 'scipy':
        raise
    raise unittest.SkipTest('Install cutting dependencies') from error
from dexlab.cutting_geometry import material_points


def components(faces):
    parent = {int(v): int(v) for v in faces.ravel()}
    def root(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for face in faces:
        for vertex in face[1:]:
            parent[root(int(vertex))] = root(int(face[0]))
    return len({root(v) for v in parent})


class SurfaceEvidence(unittest.TestCase):
    def setUp(self):
        self.reference = material_points((.03, .015, .015), .0075)
        self.surface = MaterialSurface(self.reference, .00375)

    def test_uncut_surface_is_connected_and_rigid_motion_is_exact(self):
        angle = .6
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                             [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        displacement = np.array([.01, .02, .03])
        positions = self.reference @ rotation.T + displacement
        deformation = np.tile(rotation, (len(positions), 1, 1))
        moved, faces, rest, _ = self.surface.mesh(positions, np.zeros(len(positions), dtype=int), deformation)
        self.assertEqual(components(faces), 1)
        np.testing.assert_allclose(moved, rest @ rotation.T + displacement, atol=1e-14)

    def test_observed_cut_creates_two_surfaces_without_added_gap(self):
        sides = np.where(self.reference[:, 0] < 0, 1, 2)
        vertices, faces, rest, _ = self.surface.mesh(self.reference, sides)
        self.assertEqual(components(faces), 2)
        np.testing.assert_allclose(vertices, rest, atol=1e-14)
        positions = self.reference.copy()
        positions[sides == 2, 0] += .004
        vertices, faces, rest, _ = self.surface.mesh(positions, sides)
        shifts = vertices[:, 0] - rest[:, 0]
        self.assertTrue(np.all(np.isclose(shifts, 0) | np.isclose(shifts, .004)))

    def test_unassigned_material_retains_bridge_at_partial_cut(self):
        sides = np.where(self.reference[:, 0] < 0, 1, 2)
        sides[self.reference[:, 2] < .0075] = 0
        _, faces, _, _ = self.surface.mesh(self.reference, sides)
        self.assertEqual(components(faces), 1)

    def test_banana_skin_blend_does_not_drag_the_other_cut_piece(self):
        reference = material_points((.12, .06, .03), .006, 'banana')
        surface = BananaSkin(reference)
        sides = np.where(reference[:, 0] < 0, 1, 2)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        positions = reference.copy()
        positions[sides == 2, 0] += .004
        moved, faces, rest, _ = surface.mesh(positions, deformation, sides)
        self.assertEqual(components(faces), 2)
        self.assertTrue(np.isfinite(moved).all())
        shifts = moved[:, 0] - rest[:, 0]
        self.assertTrue(np.all(np.isclose(shifts, 0) | np.isclose(shifts, .004)))


if __name__ == '__main__':
    unittest.main()
