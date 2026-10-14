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
        moved, faces, rest, _ = surface.mesh(positions, deformation, sides, sides)
        self.assertEqual(components(faces), 2)
        self.assertTrue(np.isfinite(moved).all())
        shifts = moved[:, 0] - rest[:, 0]
        self.assertTrue(np.all(np.isclose(shifts, 0) | np.isclose(shifts, .004)))

    def test_banana_cap_rim_remains_flat_under_rigid_piece_motion(self):
        reference = material_points((.12, .06, .03), .006, 'banana')
        surface = BananaSkin(reference)
        sides = np.where(reference[:, 0] < 0, 1, 2)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        moved, _, rest, caps = surface.mesh(reference, deformation, sides, sides)
        rim = np.isclose(rest[:, 0], 0.)
        self.assertTrue(rim.any())
        self.assertTrue(caps[rim].all())
        np.testing.assert_allclose(moved[rim, 0], 0., atol=1e-14)

    def test_banana_partial_cut_keeps_bridge_and_exposes_local_caps(self):
        reference = material_points((.12, .06, .03), .006, 'banana')
        surface = BananaSkin(reference)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        codes = np.where(reference[:, 0] < 0, 1, 2)
        codes[reference[:, 2] < .012] = 0
        moved, faces, rest, _ = surface.mesh(reference, deformation, codes, np.zeros(len(reference), dtype=int))
        self.assertEqual(components(faces), 1)
        np.testing.assert_allclose(moved, rest, atol=1e-14)
        cap_faces = np.isclose(rest[faces, 0], 0.).all(axis=1)
        self.assertTrue(cap_faces.any())
        self.assertGreater(rest[faces[cap_faces], 2].mean(), .012)

    def test_banana_uncut_surface_is_connected_under_affine_deformation(self):
        reference = material_points((.12, .06, .03), .006, 'banana')
        surface = BananaSkin(reference)
        gradient = np.array([[1., .1, 0.], [0., .95, .1], [0., 0., 1.05]])
        deformation = np.tile(gradient, (len(reference), 1, 1))
        moved, faces, rest, _ = surface.mesh(reference @ gradient.T, deformation,
                                          np.zeros(len(reference), dtype=int), np.zeros(len(reference), dtype=int))
        self.assertEqual(components(faces), 1)
        np.testing.assert_allclose(moved, rest @ gradient.T, atol=1e-14)
        self.assertFalse(np.isclose(rest[faces, 0], 0.).all(axis=1).any())

    def test_banana_cut_caps_have_opposing_outward_normals(self):
        reference = material_points((.12, .06, .03), .006, 'banana')
        surface = BananaSkin(reference)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        codes = np.where(reference[:, 0] < 0, 1, 2)
        positions = reference.copy()
        positions[codes == 2, 0] += .004
        moved, faces, rest, _ = surface.mesh(positions, deformation, codes, codes)
        cap_faces = faces[np.isclose(rest[faces, 0], 0.).all(axis=1)]
        triangle = moved[cap_faces]
        normals = np.cross(triangle[:, 1]-triangle[:, 0], triangle[:, 2]-triangle[:, 0])
        x = triangle[:, :, 0].mean(axis=1)
        self.assertTrue((normals[np.isclose(x, 0.), 0] > 0).all())
        self.assertTrue((normals[np.isclose(x, .004), 0] < 0).all())

    def test_compatible_codes_cannot_reconnect_disjoint_native_components(self):
        reference = material_points((.12, .06, .03), .005, 'banana')
        surface = BananaSkin(reference)
        groups = np.searchsorted([-.03, 0., .03], reference[:, 0])
        # Compatibility alone is not spatial connectivity: an unassigned anchor
        # may belong to a native component with no shared stencil to its neighbour.
        codes = np.zeros(len(reference), dtype=int)
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        positions = reference.copy()
        positions[:, 0] += groups*.004
        moved, faces, rest, _ = surface.mesh(positions, deformation, codes, groups)
        self.assertEqual(components(faces), 4)
        shifts = (moved[:, 0]-rest[:, 0])/.004
        np.testing.assert_allclose(shifts, np.rint(shifts), atol=1e-12)

    def test_shifted_material_boundary_does_not_misassign_the_authored_seam(self):
        reference = material_points((.12, .06, .03), .005, 'banana')
        surface = BananaSkin(reference)
        # A cut in deformed material need not coincide with the nominal
        # reference plane. Some left-seam nearest particles belong to the right.
        groups = np.searchsorted([-.03, 0., .027], reference[:, 0])
        deformation = np.tile(np.eye(3), (len(reference), 1, 1))
        positions = reference.copy()
        positions[:, 0] += groups*.004
        moved, faces, rest, _ = surface.mesh(positions, deformation,
                                            np.zeros(len(reference), dtype=int), groups)
        self.assertEqual(components(faces), 4)
        shifts = (moved[:, 0]-rest[:, 0])/.004
        np.testing.assert_allclose(shifts, np.rint(shifts), atol=1e-12)
        # The third authored interval remains attached to its own native piece.
        interior = (rest[:, 0] > .001) & (rest[:, 0] < .029)
        np.testing.assert_allclose(shifts[interior], 2., atol=1e-12)



if __name__ == '__main__':
    unittest.main()
