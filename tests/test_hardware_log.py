"""Synthetic intake fixtures: no hardware operation or calibration evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from dexlab.hardware_log import validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'docs/hardware/template'


class HardwareLogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.manifest = json.loads((TEMPLATE / 'manifest.json').read_text())
        self.rows = []

    def write(self):
        (self.directory / 'manifest.json').write_text(json.dumps(self.manifest))
        (self.directory / 'samples.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in self.rows))

    def check(self):
        self.write()
        return validate(self.directory)

    def complete_synthetic(self):
        """Test mechanics only; this evidence file explicitly declares synthetic data."""
        artifact = self.directory / 'synthetic-evidence.txt'
        artifact.write_text('Synthetic unit-test evidence; not a real sensor verification.\n')
        self.manifest['artifacts'] = {artifact.name: hashlib.sha256(artifact.read_bytes()).hexdigest()}
        self.manifest['kind'] = 'synthetic'
        self.manifest['trials'] = self.manifest['trials'][:1]
        self.manifest['trials'][0]['status'] = 'complete'
        self.manifest['devices']['reference_sensor'].update(firmware='fixture', interface='fixture')
        for name in ['host', 'reference']:
            self.manifest['clocks'][name].update(offset_to_host_s=0, scale_to_host=1,
                                               uncertainty_s=0.001, evidence=artifact.name)
        self.manifest['frames']['reference_axis']['evidence'] = artifact.name
        for name, value in [('normal_force', 1.0), ('compression', 0.001)]:
            self.manifest['channels'][name].update(status='verified', source_field='synthetic_source',
                evidence=artifact.name, uncertainty={'absolute_bounds': [0.0001], 'basis': 'synthetic bound',
                                                    'evidence': artifact.name})
            for index in range(2):
                self.rows.append(dict(trial_id='development-001', channel=name, sequence=index,
                    host_time_s=index * 0.01, device_time_s=index * 0.01, value=[value],
                    quality='valid', reason=None))

    def test_preparation_is_not_measured(self):
        result = validate(TEMPLATE)
        self.assertTrue(result['format_valid'])
        self.assertFalse(result['measured_intake_ready'])
        self.assertEqual(result['sample_count'], 0)
        self.assertTrue(result['intake_blockers'])

    def test_synthetic_cannot_pass_measured_requirement(self):
        self.complete_synthetic()
        result = self.check()
        self.assertEqual(result['intake_blockers'], [])
        self.assertFalse(result['measured_intake_ready'])
        self.assertEqual(result['scientific_acceptance'], 'not_assessed')

    def test_format_ready_does_not_claim_science_or_require_unused_arm(self):
        self.complete_synthetic()
        # Exercises the claimed kind, not authenticity: the validator cannot infer fabrication.
        self.manifest['kind'] = 'measured'
        result = self.check()
        self.assertTrue(result['measured_intake_ready'])
        self.assertTrue(result['missing_metadata_or_data'])  # unused arms remain unknown
        self.assertEqual(result['scientific_acceptance'], 'not_assessed')

    def test_target_joint_field_cannot_be_actual(self):
        self.manifest['channels']['left_q_actual']['source_field'] = 'target_q'
        with self.assertRaisesRegex(ValueError, 'wrong UR source'):
            self.check()

    def test_units_and_provenance_cannot_be_relabelled(self):
        for field, value in [('unit', 'mm'), ('kind', 'command')]:
            with self.subTest(field=field):
                original = self.manifest['channels']['normal_force'][field]
                self.manifest['channels']['normal_force'][field] = value
                with self.assertRaisesRegex(ValueError, 'unit or provenance'):
                    self.check()
                self.manifest['channels']['normal_force'][field] = original

    def test_unknown_channel_cannot_be_zero_filled(self):
        self.complete_synthetic()
        self.manifest['channels']['normal_force']['status'] = 'unverified'
        self.rows[0]['value'] = [0.0]
        with self.assertRaisesRegex(ValueError, 'unverified channel'):
            self.check()

    def test_missing_value_is_null_and_reasoned(self):
        self.complete_synthetic()
        self.rows[0].update(quality='missing', value=None, reason='packet lost')
        self.assertEqual(self.check()['observed_gap_counts']['normal_force'], 1)
        self.rows[0]['value'] = [0]
        with self.assertRaisesRegex(ValueError, 'null and reason'):
            self.check()

    def test_nonfinite_wrong_shape_and_boolean_rejected(self):
        self.complete_synthetic()
        for bad in [[float('nan')], [float('inf')], [True], [1, 2], 1]:
            with self.subTest(bad=bad):
                self.rows[0]['value'] = bad
                with self.assertRaisesRegex(ValueError, 'shape/number'):
                    self.check()

    def test_split_leakage_by_specimen_or_condition(self):
        for field in ['specimen_id', 'condition_id']:
            with self.subTest(field=field):
                original = self.manifest['trials'][1][field]
                self.manifest['trials'][1][field] = self.manifest['trials'][0][field]
                with self.assertRaisesRegex(ValueError, 'leaks across splits'):
                    self.check()
                self.manifest['trials'][1][field] = original

    def test_repeats_within_same_split_allowed(self):
        trial = copy.deepcopy(self.manifest['trials'][0])
        trial.update(id='development-002', repeat=2)
        self.manifest['trials'].append(trial)
        self.assertTrue(self.check()['format_valid'])

    def test_force_displacement_required_for_contact_protocol(self):
        self.manifest['trials'][0]['required_channels'] = ['left_q_target']
        with self.assertRaisesRegex(ValueError, 'independent force/displacement'):
            self.check()

    def test_reordering_and_device_reset_rejected(self):
        self.complete_synthetic()
        for field, bad in [('sequence', 0), ('host_time_s', -1), ('device_time_s', 0)]:
            with self.subTest(field=field):
                original = self.rows[1][field]
                self.rows[1][field] = bad
                with self.assertRaises(ValueError):
                    self.check()
                self.rows[1][field] = original

    def test_missing_timestamp_does_not_hide_reset(self):
        self.complete_synthetic()
        self.rows[0]['device_time_s'] = 10
        self.rows[1]['device_time_s'] = None
        row = copy.deepcopy(self.rows[1])
        row.update(sequence=2, host_time_s=0.02, device_time_s=2)
        self.rows.append(row)
        with self.assertRaisesRegex(ValueError, 'clock repeated/reset'):
            self.check()

    def test_sequence_gap_kept_not_interpolated(self):
        self.complete_synthetic()
        self.rows[1]['sequence'] = 3
        self.manifest['kind'] = 'measured'
        result = self.check()
        self.assertEqual(result['observed_gap_counts']['normal_force'], 2)
        self.assertFalse(result['measured_intake_ready'])
        self.assertEqual(result['sample_count'], 4)

    def test_artifact_corruption_and_path_escape(self):
        self.complete_synthetic()
        self.write()
        (self.directory / 'synthetic-evidence.txt').write_text('altered')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            validate(self.directory)
        self.manifest['artifacts'] = {'../elsewhere': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'escapes bundle'):
            self.check()

    def test_duplicate_json_keys_rejected(self):
        self.write()
        p = self.directory / 'manifest.json'
        p.write_text(p.read_text().replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            validate(self.directory)

    def test_aborted_trials_preserved_and_need_reason(self):
        self.manifest['trials'][0]['status'] = 'aborted'
        with self.assertRaisesRegex(ValueError, 'failure reason missing'):
            self.check()
        self.manifest['trials'][0]['failure_reason'] = 'sensor saturated'
        result = self.check()
        self.assertEqual(result['trial_status_counts']['aborted'], 1)
        self.assertFalse(result['measured_intake_ready'])

    def test_validator_does_not_modify_inputs(self):
        self.complete_synthetic()
        self.write()
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        validate(self.directory)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def test_cli_exit_codes(self):
        command = [sys.executable, '-m', 'dexlab.hardware_log', str(TEMPLATE)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(command + ['--require-measured'], capture_output=True).returncode, 2)
        self.write()
        (self.directory / 'samples.jsonl').write_text('{bad json}\n')
        result = subprocess.run([*command[:-1], str(self.directory)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['format_valid'])


if __name__ == '__main__':
    unittest.main()
