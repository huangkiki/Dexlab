"""Frozen protocol, sampling and saved-force integrity checks."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

try:
    from dexlab.banana_force import (
        DEFAULT_PROTOCOL, force_config, load_protocol, refined_reference,
        run_force_case, sampling_sha256, stratified_reference, suite_cases,
    )
    from dexlab.banana_force_score import score_force_run
except ModuleNotFoundError as error:
    if error.name not in ('numba', 'scipy'):
        raise
    raise unittest.SkipTest('Install dexlab[cutting]') from error


class BananaForceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = load_protocol()

    def test_paper_values_and_independent_unknowns_are_frozen(self):
        reported = self.protocol['paper']['specified_values']
        config = force_config(self.protocol)
        self.assertEqual(config.young_modulus, reported['young_modulus_pa'])
        self.assertEqual(config.poisson_ratio, reported['poisson_ratio'])
        self.assertEqual(config.yield_stress, reported['yield_stress_pa'])
        self.assertEqual(config.blade_mass, reported['knife_mass_kg'])
        self.assertIn('raw robot and simulation force samples',
                      self.protocol['paper']['unpublished_fields'])
        self.assertIn('drive_force_n', self.protocol['force_definition']['excluded_from_resistance'])
        self.assertEqual(self.protocol['execution_budget']['maximum_segments_per_case'], 4)
        self.assertEqual(self.protocol['execution_budget']['maximum_attempts_per_segment'], 1)
        self.assertEqual(self.protocol['execution_budget']['swap_mib'], 0)

    def test_twenty_sampling_seeds_are_distinct_and_reproducible(self):
        sampling = self.protocol['independent_choices']['sampling']
        spacing = self.protocol['independent_choices']['geometry']['base_grid_spacing_m']
        hashes = [sampling_sha256(stratified_reference(
            spacing, seed, sampling['jitter_fraction_of_particle_spacing']))
                  for seed in sampling['seeds']]
        self.assertEqual(len(hashes), 20)
        self.assertEqual(len(set(hashes)), 20)
        self.assertEqual(hashes[0], sampling_sha256(stratified_reference(
            spacing, 0, sampling['jitter_fraction_of_particle_spacing'])))

    def test_refinement_has_exactly_sixty_four_times_as_many_particles(self):
        spacing = self.protocol['independent_choices']['geometry']['base_grid_spacing_m']
        base = stratified_reference(spacing, 0, 0.)
        refined = refined_reference(spacing, self.protocol['refinement']['factor_per_axis'])
        self.assertEqual(len(refined), 64 * len(base))
        refined_config = force_config(self.protocol, refined=True)
        self.assertEqual(refined_config.grid_spacing, spacing / 4)
        self.assertEqual(refined_config.dt,
                         self.protocol['refinement']['timestep_s'])

    def test_suite_matrix_does_not_duplicate_the_baseline(self):
        cases = suite_cases(self.protocol, 'all')
        identifiers = [case['case_id'] for case in cases]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(sum(name.startswith('base-seed-') for name in identifiers), 20)
        self.assertIn('refined-centres', identifiers)
        self.assertEqual(sum(name.startswith('sensitivity-') for name in identifiers), 4)

    def test_short_probe_records_force_channels_but_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'probe'
            result = run_force_case(folder, duration=.00025, case_id='short-probe')
            self.assertFalse(result['passed'])
            self.assertTrue(result['checks']['force_channel_identity'])
            self.assertTrue(result['checks']['momentum_balance'])
            self.assertFalse(result['checks']['material_epoch_before_support'])
            self.assertFalse(result['checks']['support_epoch_observed'])
            self.assertIn('no raw robot-force agreement', result['evidence_scope'])

            path = folder / 'trace.npz'
            with np.load(path) as archive:
                trace = {key: archive[key] for key in archive.files
                         if key != 'material_reaction_n'}
            np.savez_compressed(path, **trace)
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['artifacts']['trace.npz'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'observations are missing'):
                score_force_run(folder)

    def test_paused_case_resumes_from_an_exact_state_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'resume'
            paused = run_force_case(folder, duration=.00025, case_id='resume-probe',
                                    segment_wall_s=0.)
            self.assertEqual(paused['status'], 'paused')
            self.assertEqual(paused['completed_steps'], 1)
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'paused')
            self.assertEqual(len(manifest['segments']), 1)
            resumed = run_force_case(folder, duration=.00025, case_id='resume-probe', resume=True)
            self.assertFalse(resumed['passed'])
            self.assertTrue(resumed['checks']['timeline_matches_manifest'])
            self.assertEqual(json.loads((folder / 'manifest.json').read_text())['completed_steps'], 2)


if __name__ == '__main__':
    unittest.main()
