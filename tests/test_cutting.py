"""Physical invariants for the independent persistent-cut TLMPM implementation."""

import unittest

import numpy as np

try:
    from dexlab.cutting import (
        CutConfig, CuttingSimulation, assign_cut_sides, box_query, corotated_stress,
        couple_grids, friction_impulse, material_step, particle_contacts, rigid_contacts,
    )
except ModuleNotFoundError as error:
    if error.name not in ("numba", "scipy"):
        raise
    raise unittest.SkipTest("Install dexlab[cutting] to run cutting physics checks") from error
from dexlab.cutting_score import grid_components


class CuttingInvariants(unittest.TestCase):
    def test_guided_blade_contact_is_rotation_covariant(self):
        from dexlab.cutting import blade_query, oriented_blade_query
        rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        center = np.array([.01, -.02, .06])
        half = np.array([.00025, .0275, .02])
        for bevel in (0., .005):
            for local in ([-.001, .01, 0.], [.0001, -.03, -.019], [.00005, 0., -.018]):
                point, normal, distance = blade_query(np.asarray(local), np.zeros(3), half, bevel)
                actual = oriented_blade_query(center + rotation @ local, center, half, bevel, np.pi/2)
                np.testing.assert_allclose(actual[0], center + rotation @ point, atol=1e-14)
                np.testing.assert_allclose(actual[1], rotation @ normal, atol=1e-12)
                self.assertAlmostEqual(actual[2], distance, places=13)

    def test_crossed_labels_retain_first_cut_and_unassigned_base(self):
        sim = CuttingSimulation(CutConfig(size=(.03, .03, .03), grid_spacing=.005))
        blade = np.array([0., 0., .044])  # Edge at24mm, leaving a connected base.
        half = np.array([.00025, .02, .02])
        args = (sim.x, sim.velocity, sim.sides, blade, np.zeros(3), half, .005, .00025)
        assign_cut_sides(*args)
        first = sim.sides.copy()
        assign_cut_sides(*args, cut_index=1, yaw=np.pi/2)
        np.testing.assert_array_equal(sim.sides % 3, first)
        top = sim.reference[:, 2] > .024
        np.testing.assert_array_equal(sim.sides[top] // 3, np.where(sim.reference[top, 1] < 0, 1, 2))
        self.assertFalse(sim.sides[sim.reference[:, 2] < .015].any())
        self.assertEqual(len(grid_components(sim.nodes, sim.weights, sim.sides)[1]), 1)

    def test_guide_cannot_rotate_inside_material(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        sim.blade_x[2] = sim.half_size[2] + .01
        before = sim.x.copy()
        with self.assertRaisesRegex(ValueError, 'Withdraw'):
            sim.step(np.array([0., 0., .01]), blade_yaw=np.pi/2)
        np.testing.assert_array_equal(sim.x, before)
        self.assertEqual(sim.blade_yaw, 0.)

    def test_multiple_cut_digits_preserve_earlier_discontinuities(self):
        from dexlab.cutting import codes_compatible
        from dexlab.cutting_score import histories_compatible
        self.assertFalse(codes_compatible(4, 5))  # Same second side, opposing first sides.
        self.assertTrue(codes_compatible(1, 4))   # Unassigned second digit stays compatible.
        x = np.array([[-.002, 0., .01], [.002, 0., .01]])
        sides = np.zeros(2, dtype=np.int64)
        args = (x, np.zeros_like(x), sides, np.array([0., 0., .025]),
                np.zeros(3), np.array([.0005, .02, .02]), .005, .0005)
        assign_cut_sides(*args)
        np.testing.assert_array_equal(sides, [1, 2])
        args = (*args[:3], np.array([-.01, 0., .025]), *args[4:])
        assign_cut_sides(*args, cut_index=1)
        np.testing.assert_array_equal(sides, [7, 8])
        self.assertFalse(histories_compatible(*sides))
        nodes = np.zeros((2, 8), dtype=int)
        self.assertEqual(len(grid_components(nodes, np.full((2, 8), .125), sides)[1]), 2)

    def test_multicut_exchange_conserves_and_preserves_common_velocity(self):
        rng = np.random.default_rng(197)
        mass = rng.uniform(.1, 2., (27, 3))
        momentum = rng.normal(size=(27, 3, 3))
        coupled = couple_grids(mass, momentum)
        np.testing.assert_allclose(coupled.sum(axis=0), momentum.sum(axis=0), atol=1e-13)
        common = mass[:, :, None] * np.array([.2, -.1, .3])
        np.testing.assert_allclose(couple_grids(mass, common), common, atol=1e-14)

    def test_banana_geometry_is_curved_connected_and_equal_volume(self):
        from dexlab.cutting_geometry import material_points
        points = material_points((.12, .06, .03), .006, 'banana')
        self.assertGreater(len(points), 500)
        middle = np.abs(points[:, 0]) < .015
        ends = np.abs(points[:, 0]) > .045
        self.assertGreater(points[ends, 1].mean() - points[middle, 1].mean(), .015)
        sim = CuttingSimulation(CutConfig(shape='banana', size=(.12, .06, .03), grid_spacing=.006))
        self.assertEqual(len(grid_components(sim.nodes, sim.weights, sim.sides)[1]), 1)

    def test_configuration_rejects_nonfinite_and_invalid_geometry(self):
        for kwargs in ({'dt': np.nan}, {'density': -1}, {'poisson_ratio': .5},
                       {'sharpness': 1}, {'grid_spacing': .011}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                CutConfig(**kwargs)

    def test_reference_basis_reproduces_linear_fields(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        np.testing.assert_allclose(sim.weights.sum(axis=1), 1, atol=1e-14)
        np.testing.assert_allclose(sim.gradients.sum(axis=1), 0, atol=1e-12)
        cells = np.array([2, 2, 2])
        coordinates = np.array(np.unravel_index(np.arange(27), cells + 1)).T * .0075 + sim.origin
        np.testing.assert_allclose((coordinates[sim.nodes] * sim.weights[:, :, None]).sum(axis=1),
                                   sim.reference, atol=1e-14)
        gradient = np.einsum('paj,pak->pjk', coordinates[sim.nodes], sim.gradients)
        np.testing.assert_allclose(gradient, np.broadcast_to(np.eye(3), gradient.shape), atol=1e-12)

    def test_stress_free_rest_and_rotation(self):
        theta = .8
        rotation = np.array([[np.cos(theta), -np.sin(theta), 0],
                             [np.sin(theta), np.cos(theta), 0], [0, 0, 1.]])
        for deformation in (np.eye(3), rotation):
            np.testing.assert_allclose(corotated_stress(deformation, 2000., 3000.), 0, atol=1e-10)
        with self.assertRaises(ValueError):
            corotated_stress(np.diag([1., 1., -1.]), 2000., 3000.)

    def test_grid_exchange_conserves_momentum_and_shared_velocity(self):
        rng = np.random.default_rng(3)
        mass = rng.uniform(.1, 1, (3, 7))
        state = rng.normal(size=(3, 7, 3))
        coupled = couple_grids(mass, state)
        np.testing.assert_allclose(coupled.sum(axis=0), state.sum(axis=0), atol=1e-14)
        common = np.array([1., -2., 3.])
        common_state = mass[:, :, None] * common
        np.testing.assert_allclose(couple_grids(mass, common_state), common_state, atol=1e-14)
        mass[0] = 0
        state[0] = 0
        np.testing.assert_array_equal(couple_grids(mass, state), state)

    def test_musl_preserves_rigid_translation_and_total_impulse(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        sim.velocity[:] = [.1, .2, -.05]
        expected = sim.x + sim.config.dt * sim.velocity
        impulse = np.zeros_like(sim.x)
        material_step(sim.x, sim.velocity, sim.deformation, sim.sides,
                      sim.nodes, sim.weights, sim.gradients, impulse, sim.mass,
                      sim.volume, 2000., 3000., sim.config.dt, .95, sim.node_count)
        np.testing.assert_allclose(sim.x, expected, atol=1e-14)
        np.testing.assert_allclose(sim.deformation, np.tile(np.eye(3), (len(sim.x), 1, 1)), atol=1e-13)
        impulse[0] = [1e-6, -2e-6, 3e-6]
        initial = sim.mass * sim.velocity.sum(axis=0)
        material_step(sim.x, sim.velocity, sim.deformation, sim.sides,
                      sim.nodes, sim.weights, sim.gradients, impulse, sim.mass,
                      sim.volume, 2000., 3000., sim.config.dt, .95, sim.node_count)
        np.testing.assert_allclose(sim.mass * sim.velocity.sum(axis=0) - initial,
                                   impulse.sum(axis=0), atol=1e-14)

    def test_flip_matches_paper_equation_17(self):
        # Two fully compatible states with equal/opposite velocity. Eq. 17
        # leaves beta * particle velocity after coupled grid momentum is zero.
        x = np.zeros((2, 3))
        velocity = np.array([[1., 0., 0.], [-1., 0., 0.]])
        original = velocity.copy()
        deformation = np.tile(np.eye(3), (2, 1, 1))
        material_step(x, velocity, deformation, np.array([0, 1]),
                      np.tile(np.arange(8), (2, 1)), np.full((2, 8), 1 / 8),
                      np.zeros((2, 8, 3)), np.zeros((2, 3)), 1., 1.,
                      2000., 3000., .0005, .95, 8)
        np.testing.assert_allclose(velocity, .95 * original, atol=1e-14)

    def test_partial_cut_remains_connected_and_labels_persist(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        partial_blade = np.array([0., 0., .009 + sim.half_size[2]])
        assign_cut_sides(sim.x, sim.velocity, sim.sides, partial_blade, np.array([0., 0., -.1]),
                         sim.half_size, .0075, .0005)
        self.assertGreater(np.count_nonzero(sim.sides), 0)
        self.assertEqual(len(grid_components(sim.nodes, sim.weights, sim.sides)[1]), 1)
        saved = sim.sides.copy()
        assign_cut_sides(sim.x, sim.velocity, sim.sides, np.array([.02, 0., .05]), np.zeros(3),
                         sim.half_size, .0075, .0005)
        np.testing.assert_array_equal(sim.sides, saved)
        assign_cut_sides(sim.x, sim.velocity, sim.sides, np.array([0., 0., sim.half_size[2]]),
                         np.array([0., 0., -.1]), sim.half_size, .0075, .0005)
        _, sizes = grid_components(sim.nodes, sim.weights, sim.sides)
        np.testing.assert_array_equal(sorted(sizes), [len(sim.x) // 2] * 2)

    def test_box_normal_and_contact_reaction(self):
        center = np.array([0., 0., .02])
        half = np.array([.0005, .025, .02])
        point, normal, distance = box_query(np.array([.001, 0., .02]), center, half)
        np.testing.assert_allclose(normal, [1, 0, 0])
        self.assertAlmostEqual(distance, .0005)
        x = np.array([[.001, 0., .02]])
        v = np.array([[-.1, 0., 0.]])
        result = rigid_contacts(x, v, center, np.zeros(3), half, .001, .001,
                                .2, .0005, .1, .3, .2, .05, .1,
                                np.zeros((2, 1, 3)), np.zeros(1), 1e-6, False)
        impulse, reaction, _, board, _, _ = result
        self.assertGreater(impulse[0, 0], 0)
        np.testing.assert_allclose(impulse.sum(axis=0) + reaction, board, atol=1e-14)
        # A free blade's velocity changes by this actual reaction impulse.
        self.assertLess((reaction / .2)[0], 0)

    def test_moving_knife_pushes_resting_material_only_in_contact(self):
        half = np.array([.0005, .025, .02])
        material = np.array([[-.001, 0., .02]])
        for blade_x, touching in [(0., True), (.02, False)]:
            damage = np.zeros(1)
            impulse, reaction, _, board, _, _ = rigid_contacts(
                material, np.zeros((1, 3)), np.array([blade_x, 0., .02]),
                np.array([-.01, 0., 0.]), half, .001, .001,
                .2, .0005, .1, .3, .2, .05, .1,
                np.zeros((2, 1, 3)), damage, 1e-6, False)
            np.testing.assert_allclose(impulse.sum(axis=0) + reaction, board, atol=1e-14)
            np.testing.assert_array_equal(damage, 0.)
            if touching:
                self.assertLess(impulse[0, 0], 0.)
                self.assertGreater(reaction[0], 0.)
            else:
                np.testing.assert_array_equal(impulse, 0.)

    def test_cut_faces_recontact_without_reconnecting(self):
        x = np.array([[-.0008, 0., 0.], [.0008, 0., 0.]])
        velocity = np.array([[.1, 0., 0.], [-.1, 0., 0.]])
        sides = np.array([1, 2])
        def contact(labels):
            return particle_contacts(
                x, x.copy(), velocity, labels, np.array([[0, 1]]),
                .001, .004, .001, .0005, .1, .3, .2, .05, .1,
                np.zeros((2, 2, 3)), np.full((2, 2), -2, dtype=np.int32), 0)
        impulse, overlap = contact(sides)
        self.assertGreater(overlap, 0)
        self.assertLess(impulse[0, 0], 0)
        np.testing.assert_allclose(impulse.sum(axis=0), 0, atol=1e-14)
        np.testing.assert_array_equal(sides, [1, 2])
        # Same reference neighbours in intact material receive continuum
        # stress, not a duplicate proxy contact force.
        np.testing.assert_array_equal(contact(np.array([0, 0]))[0], 0)

    def test_beveled_blade_closest_point_and_normal(self):
        from dexlab.cutting import blade_query
        half = np.array([.0005, .04, .02])
        center = np.array([.03, 0., .025])
        normal = np.array([1., 0., -.1]) / np.sqrt(1.01)
        surface = np.array([.0002, 0., -.018])
        for signed_distance in [-.00005, .00005]:
            point = center + surface + signed_distance * normal
            closest, observed_normal, distance = blade_query(point, center, half, .005)
            np.testing.assert_allclose(closest, center + surface, atol=1e-14)
            np.testing.assert_allclose(observed_normal, normal, atol=1e-14)
            self.assertAlmostEqual(distance, signed_distance)
        # The width end cap and edge corner are part of the same solid.
        for point, expected in [(np.array([0., .041, 0.]), .001),
                                (np.array([0., 0., -.021]), .001)]:
            closest, observed_normal, distance = blade_query(center + point, center, half, .005)
            self.assertAlmostEqual(distance, expected)
            np.testing.assert_allclose(center + point - closest, distance * observed_normal, atol=1e-14)
        point = center + np.array([.001, .003, -.019])
        for observed, expected in zip(blade_query(point, center, half), box_query(point, center, half)):
            np.testing.assert_allclose(observed, expected, atol=1e-14)

    def test_friction_opposes_slip_and_satisfies_coulomb_bound(self):
        impulse, history = friction_impulse(np.array([0., 0., 1.]),
                                            np.array([10., 0., 0.]), .001,
                                            np.zeros(3), .001, .0005, .3, .2, .05, .1)
        self.assertLess(impulse[0], 0)
        self.assertAlmostEqual(np.linalg.norm(impulse), .2 * .001)
        self.assertEqual(history[2], 0)


if __name__ == '__main__':
    unittest.main()
