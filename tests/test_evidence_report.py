"""Evidence failures must not turn into low error, success or a smaller cohort."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.cloth import ClothCase
from dexlab.cloth_benchmark import verify
from dexlab.evidence_report import (
    digest, historical_records, input_manifest, quantities, time_coverage,
    verdict, verify_hashes,
)


class EvidenceFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def cloth_record(self):
        # Analytical stationary cloth fixture; never launch an engine.
        case = ClothCase()
        vertices, triangles, masses = case.mesh()
        times = np.arange(4, dtype=float)
        np.savez(self.root / 'trajectory.npz', time=times,
                 positions=np.repeat(vertices[None], 4, axis=0),
                 velocities=np.zeros((4, len(vertices), 3)),
                 triangles=triangles, rest_positions=vertices, nominal_masses=masses,
                 forces=np.array([case.forces(t) for t in times[:-1]]))
        self.write('run.json', dict(case=asdict(case), dt_s=1., status='completed',
                                   solver='mujoco', source_before={}, source_after={},
                                   trajectory_sha256=digest(self.root / 'trajectory.npz')))


class EvidenceReportTest(EvidenceFixture):
    def test_readonly_verifier_retains_original_summary_and_bytes(self):
        self.cloth_record()
        self.write('summary.json', {'legacy': 'immutable'})
        before = {p.name: digest(p) for p in self.root.iterdir()}
        result = verify(self.root, write_summary=False)
        self.assertTrue(result['protocol_checks_passed'])
        self.assertEqual(before, {p.name: digest(p) for p in self.root.iterdir()})
        verify(self.root)  # Existing CLI/API behavior remains the default.
        self.assertNotEqual(before['summary.json'], digest(self.root / 'summary.json'))

    def test_missing_corrupt_and_escaping_inputs_are_rejected(self):
        self.write('record.json', {'value': 1})
        frozen = {'record.json': digest(self.root / 'record.json')}
        self.assertEqual(verify_hashes(self.root, frozen), frozen)
        self.write('record.json', {'value': 2})
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            verify_hashes(self.root, frozen)
        (self.root / 'record.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            verify_hashes(self.root, frozen)
        for name in ('../outside', '/tmp/outside'):
            with self.assertRaises(ValueError):
                verify_hashes(self.root, {name: 'not-a-hash'})

    def test_duplicate_truncated_and_nonfinite_grids_rejected(self):
        self.cloth_record()
        self.assertEqual(time_coverage('cloth', self.root)['samples'], 4)
        for times in ([0, 1, 1, 3], [0, 1, 2], [0, 1, np.nan, 3], [.1, 1.1, 2.1, 3.1]):
            np.savez(self.root / 'trajectory.npz', time=times)
            with self.assertRaisesRegex(ValueError, 'time grid'):
                time_coverage('cloth', self.root)

    def test_cylinder_grid_uses_the_declared_protocol_constant(self):
        from dexlab.contact_pinch import CylinderCase, DURATION
        case = CylinderCase()
        self.write('run.json', {'case': asdict(case)})
        np.savez(self.root/'states.npz', time=np.arange(case.steps+1)*case.timestep)
        self.assertEqual(time_coverage('contact', self.root)['episode_duration_s'], DURATION)

    def test_unknown_table_geometry_is_neither_zero_nor_pass(self):
        values = quantities('robot_cloth', {}, {'metrics': {'r': {'maximum_anchor_error_m': .001, 'lift_m': .1}},
                           'table_surface_diagnostic': {'status': 'unsupported_geometry'}})
        self.assertIsNone(values['robot_cloth.table_depth']['value'])
        self.assertEqual(values['robot_cloth.table_depth']['status'], 'unavailable')

    def test_summary_must_agree_with_boolean_checks(self):
        self.assertEqual(verdict({'passed': False, 'checks': {'retention': False}}), 'protocol_fail')
        for result in ({'passed': True, 'checks': {'retention': False}},
                       {'passed': False, 'checks': {'retention': 0}},
                       {'passed': True, 'checks': {}}):
            with self.assertRaises(ValueError):
                verdict(result)

    def test_complete_cohort_and_unsupported_are_preserved(self):
        report = {'records': [dict(run='a', run_sha256='a', metadata={'status': 'completed'},
                                  job={'status': 'completed', 'solver': 'mujoco', 'protocol_checks_passed': False, 'summary_sha256': 'b'},
                                  summary={'protocol_checks_passed': False, 'checks': {'geometry': False}}),
                              dict(run='b', run_sha256='c', metadata={'status': 'unsupported'},
                                   job={'status': 'completed', 'solver': 'physx', 'protocol_checks_passed': False, 'summary_sha256': 'd'},
                                   summary={'protocol_checks_passed': False, 'checks': {'finite': False}})]}
        spec = dict(kind='cloth', count=2, historical_counts={'protocol_fail': 1, 'unsupported': 1})
        records = historical_records(spec, report)
        self.assertEqual([r['historical'] for r in records], ['protocol_fail', 'unsupported'])
        duplicate = deepcopy(report)
        duplicate['records'][1]['run'] = 'a'
        for invalid in (duplicate, {'records': report['records'][:1]}):
            with self.assertRaisesRegex(ValueError, 'cohort'):
                historical_records(spec, invalid)
        with self.assertRaisesRegex(ValueError, 'counts'):
            historical_records({**spec, 'historical_counts': {'protocol_pass': 2}}, report)

    def test_physical_drift_is_si_and_never_material_slip(self):
        values = quantities('apple', {}, {'metrics': {
            'maximum_penetration_mm': .2, 'maximum_wrist_relative_displacement_mm': 2,
            'maximum_wrist_relative_rotation_deg': 180, 'minimum_clearance_mm': 120,
            'mean_hand_support_weight_ratio': 1., 'maximum_momentum_residual_weight_ratio': .01}})
        self.assertAlmostEqual(values['apple.wrist_translation']['value'], .002)
        self.assertAlmostEqual(values['apple.wrist_rotation']['value'], np.pi)
        self.assertIsNone(values['material_slip']['value'])
        self.assertEqual(values['material_slip']['status'], 'unavailable')

    def test_absent_obstacles_and_pins_are_not_observed_zero(self):
        result = {'metrics': {'maximum': {'ground_penetration_m': 0., 'sphere_penetration_m': 0.,
                    'maximum_absolute_edge_strain': .01, 'maximum_pin_error_m': 0.},
                    'final': {'tip_sag_m': .02}},
                  'self_intersection_audit': {'maximum_crossing_pairs': 0}}
        extension = quantities('cloth', {'experiment': 'extension'}, result)
        self.assertIsNone(extension['cloth.ground_depth']['value'])
        self.assertEqual(extension['cloth.sphere_depth']['status'], 'not_applicable')
        self.assertEqual(extension['cloth.pin_error']['status'], 'observed')
        drape = quantities('cloth', {'experiment': 'drape'}, result)
        self.assertEqual(drape['cloth.sphere_depth']['status'], 'observed')
        self.assertIsNone(drape['cloth.pin_error']['value'])

    def test_legacy_cloth_verdict_comes_from_frozen_source(self):
        report = dict(protocol_controls={'original': {'old_protocol_passed': False}}, input_sha256={'trace.json': 'a'})
        spec = dict(kind='robot_cloth', count=1, historical_counts={'protocol_fail': 1})
        self.assertEqual(historical_records(spec, report)[0]['historical'], 'protocol_fail')

class TerminalEvidenceTest(unittest.TestCase):
    def test_timeout_without_episode_keeps_its_denominator(self):
        spec = dict(kind='cloth', count=1, historical_counts={'timeout': 1})
        frozen = {'records': [dict(run='timed-out', metadata=None, summary=None,
                                  job={'status': 'timeout', 'solver': 'mujoco', 'protocol_checks_passed': False})]}
        record = historical_records(spec, frozen)[0]
        self.assertEqual(record['historical'], 'timeout')
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(input_manifest('cloth', Path(temporary), record), {})

    def test_unsupported_summary_cannot_claim_pass(self):
        spec = dict(kind='cloth', count=1, historical_counts={'unsupported': 1})
        frozen = {'records': [dict(run='unsupported', run_sha256='a', metadata={'status': 'unsupported'},
                                  job={'status': 'completed', 'solver': 'physx', 'protocol_checks_passed': False, 'summary_sha256': 'b'},
                                  summary={'protocol_checks_passed': True, 'checks': {'finite': True}})]}
        with self.assertRaisesRegex(ValueError, 'terminal'):
            historical_records(spec, frozen)

    def test_nested_artifact_cannot_override_published_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'run.json').write_text(json.dumps({'artifact_sha256': {'run.json': 'forged'}}))
            with self.assertRaisesRegex(ValueError, 'conflict'):
                input_manifest('contact', root, {'expected': {'run.json': digest(root/'run.json')}, 'historical': 'protocol_pass'})

class EndToEndEvidenceTest(EvidenceFixture):
    def build_fixture(self):
        from dexlab.evidence_report import ROOT
        self.cloth_record()
        summary = verify(self.root)
        self.project = self.root / 'project'
        (self.project/'docs/evidence').mkdir(parents=True)
        (self.project/'demos/cloth-folding/src').mkdir(parents=True)
        (self.project/'demos/cloth-folding/src/verify_cloth.py').write_text('# fixture source identity')
        (self.project/'docs/evidence/metrics.json').write_bytes((ROOT/'docs/evidence/metrics.json').read_bytes())
        report = {'records': [dict(run='fixture', run_sha256=digest(self.root/'run.json'),
                                  metadata={'status': 'completed'}, summary=summary,
                                  job={'status': 'completed', 'solver': 'mujoco', 'protocol_checks_passed': True,
                                       'summary_sha256': digest(self.root/'summary.json')})]}
        frozen = self.project/'frozen.json'
        frozen.write_text(json.dumps(report))
        self.selection = self.project/'selection.json'
        self.selection.write_text(json.dumps({'cohorts': [dict(id='fixture-cohort',kind='cloth',report='frozen.json',
            report_sha256=digest(frozen),count=1,historical_counts={'protocol_pass':1},raw_source={'url':None})]}))
        return {'fixture-cohort': {'fixture': str(self.root)}}

    def test_complete_report_is_readonly_and_contains_no_private_directory(self):
        from dexlab.evidence_report import build_report
        locations = self.build_fixture()
        before = {name:digest(self.root/name) for name in ('run.json','summary.json','trajectory.npz')}
        with patch('dexlab.evidence_report.ROOT', self.project):
            result = build_report(self.selection, locations)
        self.assertEqual(result['cohorts'][0]['counts'], {'protocol_pass':1})
        self.assertEqual(result['records'][0]['metrics']['material_slip']['value'], None)
        self.assertNotIn(str(self.root), json.dumps(result))
        self.assertEqual(before, {name:digest(self.root/name) for name in before})

    def test_corruption_aborts_whole_report(self):
        from dexlab.evidence_report import build_report
        locations = self.build_fixture()
        with (self.root/'trajectory.npz').open('ab') as stream:
            stream.write(b'corrupt')
        with patch('dexlab.evidence_report.ROOT', self.project):
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                build_report(self.selection, locations)


if __name__ == '__main__':
    unittest.main()
