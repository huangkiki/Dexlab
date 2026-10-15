"""Constitutive and discrete checks, separate from cutting-task acceptance."""

from dataclasses import replace
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

try:
    from dexlab.cutting import CutConfig, CuttingSimulation, material_step, newtonian_stress
    from dexlab.cutting_score import score_run
    from dexlab.tofu_cut import run
except ModuleNotFoundError as error:
    if error.name not in ('numba', 'scipy'):
        raise
    raise unittest.SkipTest('Install dexlab[cutting]') from error


class NewtonianViscosityTests(unittest.TestCase):
    def test_simple_shear_and_volumetric_rate_have_declared_units(self):
        eta, shear = 5., 2.
        rate = np.zeros((3, 3))
        rate[0, 1] = shear
        expected = np.zeros((3, 3))
        expected[0, 1] = expected[1, 0] = eta * shear
        stress = newtonian_stress(np.eye(3), rate, eta)
        np.testing.assert_allclose(stress, expected, atol=1e-14)
        self.assertAlmostEqual(float(np.sum(stress * rate)), eta * shear**2)
        np.testing.assert_allclose(newtonian_stress(np.eye(3), .3 * np.eye(3), eta),
                                   2 * eta * .3 * np.eye(3), atol=1e-14)

    def test_rigid_spin_has_no_viscous_stress_in_a_deformed_body(self):
        deformation = np.array([[1.2, .2, 0], [0, .9, .1], [0, 0, 1.1]])
        spin = np.array([[0., -2., .5], [2., 0., -.8], [-.5, .8, 0.]])
        for rate in (np.zeros((3, 3)), spin @ deformation):
            np.testing.assert_allclose(newtonian_stress(deformation, rate, 5.), 0, atol=1e-13)

    def test_superposed_rotating_frame_preserves_stress_and_dissipation(self):
        deformation = np.array([[1.2, .2, 0], [0, .9, .1], [0, 0, 1.1]])
        gradient = np.array([[.2, 1., 0.], [-.1, -.3, .4], [.2, .1, .1]])
        angle = .7
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0.],
                             [np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
        spin = np.array([[0., -3., 0.], [3., 0., 0.], [0., 0., 0.]])
        rate = gradient @ deformation
        transformed_f = rotation @ deformation
        transformed_rate = (rotation @ gradient @ rotation.T + spin) @ transformed_f
        stress = newtonian_stress(deformation, rate, 5.)
        transformed = newtonian_stress(transformed_f, transformed_rate, 5.)
        np.testing.assert_allclose(transformed, rotation @ stress, atol=1e-12)
        symmetric_rate = (gradient + gradient.T) / 2
        expected_power = 10 * np.linalg.det(deformation) * np.sum(symmetric_rate**2)
        self.assertAlmostEqual(float(np.sum(stress * rate)), expected_power, places=12)
        self.assertAlmostEqual(float(np.sum(transformed * transformed_rate)), expected_power, places=12)

    def test_viscosity_must_be_finite_and_nonnegative(self):
        self.assertEqual(CutConfig().dynamic_viscosity, 0.)
        self.assertEqual(replace(CutConfig(), dynamic_viscosity=5.).dynamic_viscosity, 5.)
        for value in (-1., np.nan, np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CutConfig(dynamic_viscosity=value)

    @staticmethod
    def advance(sim, viscosity):
        return material_step(sim.x, sim.velocity, sim.deformation, sim.sides,
                             sim.nodes, sim.weights, sim.gradients, np.zeros_like(sim.x),
                             sim.mass, sim.volume, 2000., 3000., 1e-6, 1., sim.node_count,
                             viscosity)

    def test_internal_viscosity_loses_energy_without_external_impulse(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        sim.velocity[:, 0] = 10 * sim.reference[:, 0]
        momentum = sim.mass * sim.velocity.sum(axis=0)
        initial_energy = .5 * sim.mass * np.sum(sim.velocity**2)
        dissipated = self.advance(sim, 5.)
        energy_loss = initial_energy - .5 * sim.mass * np.sum(sim.velocity**2)
        self.assertGreater(dissipated, 0.)
        self.assertGreater(energy_loss, 0.)
        self.assertLess(abs(energy_loss - dissipated), .01 * dissipated)
        np.testing.assert_allclose(sim.mass * sim.velocity.sum(axis=0), momentum, atol=1e-14)

    def test_cut_fragments_translate_independently_without_viscous_drag(self):
        sim = CuttingSimulation(CutConfig(size=(.015, .015, .015)))
        sim.sides[:] = np.where(sim.reference[:, 0] < 0, 1, 2)
        sim.velocity[:, 0] = np.where(sim.sides == 1, -.1, .1)
        initial = sim.velocity.copy()
        dissipation = self.advance(sim, 5.)
        np.testing.assert_allclose(sim.velocity, initial, atol=1e-14)
        self.assertAlmostEqual(dissipation, 0., places=14)

    def test_recorded_viscosity_requires_dissipation_telemetry(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'viscous'
            config = CutConfig(size=(.015, .015, .015), dt=.00025, dynamic_viscosity=5.)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, config, duration=.002)
            self.assertFalse(result['passed'])  # A short run is not task acceptance.
            self.assertTrue(result['checks']['nonnegative_viscous_dissipation'])
            self.assertGreater(result['constitutive_viscous_dissipation_j'], 0.)
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest['config']['dynamic_viscosity'], 5.)
            trace_path = folder / 'trace.npz'
            with np.load(trace_path) as archive:
                trace = {key: archive[key] for key in archive.files}
            for missing in (False, True):
                changed = dict(trace)
                if missing:
                    del changed['viscous_dissipation_j']
                else:
                    changed['viscous_dissipation_j'] = np.full(len(trace['time_s']), -1.)
                np.savez_compressed(trace_path, **changed)
                manifest['artifacts']['trace.npz'] = hashlib.sha256(trace_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest))
                if missing:
                    with self.assertRaisesRegex(ValueError, 'viscous dissipation'):
                        score_run(folder)
                else:
                    self.assertFalse(score_run(folder)['checks']['nonnegative_viscous_dissipation'])


if __name__ == '__main__':
    unittest.main()
