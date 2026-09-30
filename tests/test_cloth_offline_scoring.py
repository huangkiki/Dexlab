"""Small synthetic records test reporting boundaries, not physical success."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mujoco
import numpy as np
import test_cloth_grasp_evidence as fixtures

from dexlab.archive_integrity import snapshot
from dexlab.cloth_table_audit import audit_table, triangle_box_depth

SOURCE = Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'
sys.path.insert(0, str(SOURCE))
import compare_scoring
import render_cloth
import verify_cloth


class OfflineScoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.record = self.root / 'record'
        self.record.mkdir()
        self.fixture = fixtures.ClothGraspEvidenceTest()
        self.fixture.setUp()
        self.xml = (
            '<mujoco><worldbody><geom name="table_0" type="box" size="1 1 .003"/>'
            '<flexcomp name="cloth" type="grid" count="2 2 1" spacing=".1 .1 .1" '
            'dim="2" pos="0 0 1"><edge equality="true"/></flexcomp></worldbody></mujoco>')
        self.model = mujoco.MjModel.from_xml_string(self.xml)
        mujoco.mj_saveModel(self.model, str(self.record / 'model.mjb'))
        self.positions = np.tile(self.model.qpos0, (225, 1))
        self.triangles = self.model.flex_elem.reshape(-1, 3).copy()
        self.states()
        np.savez(self.record / 'plan-r.npz', **self.fixture.plans[0])
        (self.record / 'trace.json').write_text(json.dumps(self.fixture.records))
        (self.record / 'summary.json').write_text(json.dumps({
            'task': 'grasp', 'schedule_s': {'duration': 9, 'hold_end': 5},
            'maximums': self.fixture.maximums, 'failure': None, 'sample_dt_s': .01}))

    def states(self, triangles=None):
        np.savez(self.record / 'states.npz', time_s=np.arange(225) / 25,
                 qpos=self.positions, triangles=self.triangles if triangles is None else triangles)

    def test_valid_synthetic_control_is_limited_and_read_only(self):
        before = snapshot(self.record)
        report = verify_cloth.verify_saved(self.record)
        self.assertTrue(report['protocol_passed'])
        self.assertEqual(report['assessment'], 'limited_protocol_pass')
        self.assertNotIn('passed', report)
        self.assertEqual(snapshot(self.record), before)

    def test_missing_table_geometry_cannot_be_safe(self):
        unknown = mujoco.MjModel.from_xml_string('<mujoco/>')
        result = audit_table(unknown, [], [], [], [])
        self.assertEqual(result['status'], 'unsupported_geometry')
        with patch('dexlab.cloth_table_audit.audit_table', return_value=result):
            report = verify_cloth.verify_saved(self.record)
        self.assertEqual(report['assessment'], 'geometry_review_required')

    def test_noninteger_topology_is_invalid_evidence(self):
        self.states(self.triangles.astype(float))
        report = verify_cloth.verify_saved(self.record)
        self.assertEqual(report['assessment'], 'protocol_failed')
        self.assertFalse(report['checks']['complete_surface_audit_record'])

    def test_inputs_changed_during_read_are_rejected(self):
        def mutate(*args):
            path = self.record / 'trace.json'
            path.write_text(path.read_text() + '\n')
            return {'status': 'no_sampled_intrusion'}
        with patch('dexlab.cloth_table_audit.audit_table', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                verify_cloth.verify_saved(self.record)

    def test_render_cannot_overwrite_or_write_into_record(self):
        for destination in (self.record, self.record / 'media'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                render_cloth.render(self.model, self.positions, self.record, 'grasp', output=destination)
        existing = self.root / 'old-media'
        existing.mkdir()
        with self.assertRaises(FileExistsError):
            render_cloth.render(self.model, self.positions, self.record, 'grasp', output=existing)

    def test_cli_retains_geometry_review_as_nonzero(self):
        # Put the synthetic cloth through the center of the table slab.
        self.model = mujoco.MjModel.from_xml_string(
            self.xml.replace('name="table_0"', 'name="table_0" pos="0 0 1"'))
        mujoco.mj_saveModel(self.model, str(self.record / 'model.mjb'))
        before = snapshot(self.record)
        output = self.root / 'report.json'
        result = subprocess.run([sys.executable, str(SOURCE / 'verify_cloth.py'),
                                 str(self.record), '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(output.read_text())['assessment'], 'geometry_review_required')
        self.assertEqual(snapshot(self.record), before)


class IndependentGeometryReferenceTests(unittest.TestCase):
    def test_historical_reference_matches_recorded_diagnostic(self):
        evidence = SOURCE.parent / 'evidence/grasp'
        report = json.loads((evidence / 'scoring-comparison-v2.json').read_text())
        with np.load(evidence / 'table-reference.npz', allow_pickle=False) as archive:
            self.assertEqual(str(archive['source_model_sha256']), report['input_sha256']['model.mjb'])
            self.assertEqual(str(archive['source_states_sha256']), report['input_sha256']['states.npz'])
            self.assertEqual(archive['frame_index'].tolist(), [0, 56, 112, 168, 224])
            lower, upper = archive['bounds']
            for index, vertices, expected in zip(archive['frame_index'], archive['vertices'],
                                                 archive['expected_depth_m'], strict=True):
                faces = vertices[archive['triangles']]
                lp = max(triangle_box_depth(face, lower, upper) for face in faces)
                clipped = max(compare_scoring.clipped_depth(face, lower, upper) for face in faces)
                with self.subTest(frame=int(index)):
                    self.assertAlmostEqual(lp, expected, delta=1e-8)
                    self.assertAlmostEqual(clipped, expected, delta=1e-8)
            self.assertGreater(archive['expected_depth_m'][0], .0025)

    def test_published_report_and_media_match_sources(self):
        root = SOURCE.parent
        report = json.loads((root / 'evidence/grasp/scoring-comparison-v2.json').read_text())
        media = json.loads((root / 'media/grasp-provenance.json').read_text())
        checks = {
            SOURCE / 'compare_scoring.py': report['comparison_source_sha256'],
            SOURCE / 'verify_cloth.py': report['current_report']['verifier_sha256'],
            SOURCE / 'render_cloth.py': media['renderer_sha256'],
            root / 'media/grasp.gif': media['gif_sha256'],
            root / 'media/grasp.mp4': media['video_sha256'],
            root / 'evidence/grasp/verification-cloth-evidence-v2.json': media['verification_sha256'],
        }
        for path, expected in checks.items():
            with self.subTest(file=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
        self.assertEqual(report['input_sha256'], media['inputs_sha256'])
        self.assertEqual(media['assessment'], 'geometry_review_required')
        self.assertEqual(media['physics_steps_executed'], 0)

    def test_clipping_and_lp_agree_on_fixed_controls(self):
        lower, upper = np.array([-1., -1., -.003]), np.array([1., 1., .003])
        faces = [np.array([[-2., 0, -.01], [2, 0, .01], [0, 2, .01]]),
                 np.array([[0., 0, .002], [.5, 0, .002], [0, .5, .002]])]
        random = np.random.default_rng(1202)
        faces.extend(random.uniform([-2, -2, -.01], [2, 2, .01], size=(24, 3, 3)))
        for face in faces:
            with self.subTest(face=face.tolist()):
                self.assertAlmostEqual(compare_scoring.clipped_depth(face, lower, upper),
                                       triangle_box_depth(face, lower, upper), delta=1e-8)
