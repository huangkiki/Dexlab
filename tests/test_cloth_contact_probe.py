"""Static diagnostics, never a claim of repaired cloth dynamics."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'demos/cloth-folding/src'))
from diagnose_table_contact import diagnose, subdivide

REFERENCE = ROOT / 'demos/cloth-folding/evidence/grasp/table-reference.npz'


class ClothContactProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(mujoco, 'mj_step', side_effect=AssertionError('No integration allowed')):
            cls.result = diagnose(REFERENCE)

    def test_static_contact_queries_preserve_time_and_reference(self):
        result = self.result
        self.assertEqual(result['physics_steps_executed'], 0)
        self.assertEqual(result['input_sha256'], hashlib.sha256(REFERENCE.read_bytes()).hexdigest())
        self.assertTrue(result['engine']['wheel_record_matches'])
        self.assertTrue(all(c['physical_time_s'] == 0 for c in result['cases'].values()))

    def test_historical_interior_crossing_with_all_vertices_outside(self):
        self.assertEqual(self.result['triangle_id'], 42)
        self.assertEqual(self.result['vertex_interior_depth_m'], [0, 0, 0])
        self.assertAlmostEqual(self.result['cases']['single_witness']['witness_interior_depth_m'],
                               0.0025566268756169025, places=10)

    def test_reduced_witness_matches_full_panel_contact(self):
        cases = self.result['cases']
        self.assertEqual(cases['single_witness']['table_geometries'], 96)
        a = cases['single_witness']['witness_max_native_penetration_m']
        self.assertAlmostEqual(a, cases['whole_panel']['witness_max_native_penetration_m'], places=12)
        self.assertAlmostEqual(a, cases['midphase_disabled']['witness_max_native_penetration_m'], places=12)

    def test_recorded_counterexample_in_pinned_engine(self):
        self.assertEqual(self.result['engine']['version'], '3.11.0')
        case = self.result['cases']['single_witness']
        self.assertGreater(case['witness_interior_depth_m'], 0.002)
        self.assertLess(case['witness_max_native_penetration_m'], 0.00001)
        # This asserts a diagnostic reproducer, not a desired physical success condition.

    def test_subdivision_preserves_surface_and_changes_contact_sampling(self):
        witness = np.array(self.result['triangle_vertices_m'])
        vertices, faces = subdivide(witness)
        area = lambda t: np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) / 2
        self.assertAlmostEqual(sum(area(vertices[t]) for t in faces), area(witness), places=14)
        normal = np.cross(witness[1] - witness[0], witness[2] - witness[0])
        self.assertTrue(np.allclose((vertices - witness[0]) @ normal, 0, atol=1e-16))
        cases = self.result['cases']
        self.assertAlmostEqual(cases['single_witness']['witness_interior_depth_m'],
                               cases['refined_witness']['witness_interior_depth_m'], places=10)
        self.assertGreater(cases['refined_witness']['witness_max_native_penetration_m'], 0.001)

    def test_raised_negative_control_is_clear(self):
        case = self.result['cases']['raised_witness']
        self.assertEqual(case['witness_interior_depth_m'], 0)
        self.assertEqual(case['all_contacts'], 0)
        self.assertEqual(case['witness_contacts'], [])

    def test_corrupted_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with np.load(REFERENCE) as source:
                arrays = {key: source[key] for key in source.files}
            arrays['expected_depth_m'] = arrays['expected_depth_m'] + 0.01
            path = Path(folder) / 'bad.npz'
            np.savez(path, **arrays)
            with self.assertRaisesRegex(ValueError, 'historical reference'):
                diagnose(path)

    def test_cli_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'report.json'
            output.write_text('preserve me')
            result = subprocess.run([sys.executable, str(ROOT / 'demos/cloth-folding/src/diagnose_table_contact.py'),
                                     str(REFERENCE), '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), 'preserve me')


if __name__ == '__main__':
    unittest.main()
