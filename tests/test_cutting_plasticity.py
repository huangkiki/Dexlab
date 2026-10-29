"""Independent J2 choice and paper-parameter provenance checks."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

try:
    from dexlab.cutting import CutConfig
    from dexlab.cutting_score import score_run
    from dexlab.tofu_cut import BLADEMASTER_BANANA_MATERIAL, run, uses_blademaster_banana_material
except ModuleNotFoundError as error:
    if error.name not in ('numba', 'scipy'):
        raise
    raise unittest.SkipTest('Install dexlab[cutting]') from error


class CuttingPlasticityTests(unittest.TestCase):
    def test_frozen_material_protocol_matches_implementation_sources(self):
        root = Path(__file__).resolve().parents[1]
        protocol = json.loads((root / 'demos/banana-force/material-protocol.json').read_text())
        self.assertEqual(protocol['status'], 'analytical-qualification-only')
        for relative, expected in protocol['source_sha256'].items():
            self.assertEqual(hashlib.sha256((root / relative).read_bytes()).hexdigest(), expected)

    def test_paper_banana_material_values_are_explicit_and_do_not_change_defaults(self):
        baseline = CutConfig()
        self.assertEqual(baseline.yield_stress, 0.)
        self.assertEqual(baseline.young_modulus, 6000.)
        paper = CutConfig(**BLADEMASTER_BANANA_MATERIAL)
        self.assertEqual(paper.young_modulus, 400_000.)
        self.assertEqual(paper.poisson_ratio, .45)
        self.assertEqual(paper.density, 1100.)
        self.assertEqual(paper.yield_stress, 30_000.)
        self.assertEqual(paper.cutting_energy, 700.)
        self.assertEqual(paper.sharpness, .9)
        self.assertEqual(paper.blade_mass, .1)
        self.assertEqual((paper.friction_static, paper.friction_dynamic), (.2, .2))
        self.assertFalse(uses_blademaster_banana_material(baseline))
        paper_banana = CutConfig(shape='banana', size=(.12, .06, .03), grid_spacing=.006,
                                 **BLADEMASTER_BANANA_MATERIAL)
        self.assertTrue(uses_blademaster_banana_material(paper_banana))
        stated = json.loads((Path(__file__).resolve().parents[1]
                             / 'demos/banana-force/material-protocol.json').read_text())[
                                 'paper']['specified_banana_values']
        self.assertEqual(stated['young_modulus_pa'], paper.young_modulus)
        self.assertEqual(stated['yield_stress_pa'], paper.yield_stress)
        self.assertEqual(stated['cutting_energy_j_m2'], paper.cutting_energy)

    def test_plastic_record_requires_nonnegative_dissipation_telemetry(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'plastic'
            config = CutConfig(size=(.015, .015, .015), dt=.00025, yield_stress=100.)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, config, duration=.001)
            self.assertFalse(result['passed'])
            self.assertTrue(result['checks']['nonnegative_plastic_dissipation'])
            self.assertGreaterEqual(result['constitutive_plastic_dissipation_j'], 0.)

            manifest_path = folder / 'manifest.json'
            trace_path = folder / 'trace.npz'
            manifest = json.loads(manifest_path.read_text())
            with np.load(trace_path) as archive:
                trace = {key: archive[key] for key in archive.files}
            for missing in (False, True):
                changed = dict(trace)
                if missing:
                    del changed['plastic_dissipation_j']
                else:
                    changed['plastic_dissipation_j'] = np.full(len(trace['time_s']), -1.)
                np.savez_compressed(trace_path, **changed)
                manifest['artifacts']['trace.npz'] = hashlib.sha256(trace_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest))
                if missing:
                    with self.assertRaisesRegex(ValueError, 'plastic dissipation'):
                        score_run(folder)
                else:
                    self.assertFalse(score_run(folder)['checks']['nonnegative_plastic_dissipation'])

    def test_paper_banana_mode_preserves_balance_in_a_short_smoke_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'paper-banana-smoke'
            config = CutConfig(shape='banana', size=(.12, .06, .03), grid_spacing=.006,
                               dt=.000125, blade_half_size=(.0005, .04, .02),
                               blade_bevel_height=.005, **BLADEMASTER_BANANA_MATERIAL)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, config, duration=.0005, task='banana')
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertIn('BladeMaster IV-C reported values', manifest['material_parameter_source'])
            self.assertIn('not measured food or author code', result['evidence_scope'])
            self.assertTrue(result['checks']['momentum_balance'])
            self.assertTrue(result['checks']['external_impulse_matches'])
            self.assertTrue(result['checks']['positive_jacobian'])
            self.assertTrue(result['checks']['nonnegative_plastic_dissipation'])
            self.assertFalse(result['passed'])  # A short probe cannot qualify the complete task.


if __name__ == '__main__':
    unittest.main()
