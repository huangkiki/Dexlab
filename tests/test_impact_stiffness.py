"""Frozen-grid matching and separate geometry acceptance, without new physics."""
import copy
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree

import numpy as np

from dexlab.impact_run import model_xml
from dexlab.impact_score import verify_readback
from dexlab.impact_stiffness import make_row, validate_pair

ROOT = Path(__file__).parents[1]


class StiffnessTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((ROOT/'docs/evidence/elastic-impact/results.json').read_text())
        self.protocol = json.loads((ROOT/'docs/evidence/impact-stiffness/manifest.json').read_text())
        self.current = dict(protocol=self.protocol, campaign=self.baseline['campaign'])

    def test_nine_matching_baselines(self):
        self.assertEqual(len(validate_pair(self.baseline, self.current)), 9)

    def test_reject_changed_bindings_and_settings(self):
        changes = [
            lambda d: d['protocol'].__setitem__('impedance', .8),
            lambda d: d['protocol'].__setitem__('baseline_manifest_sha256', 'wrong'),
            lambda d: d['protocol']['baseline_bindings'][0].__setitem__('trace_sha256', 'wrong'),
            lambda d: d['protocol']['cases'][0].__setitem__('timestep', .0001),
            lambda d: d['protocol'].__setitem__('overlap_budget_m', .002),
            lambda d: d['campaign']['runtime'].__setitem__('code_sha256', 'different'),
        ]
        for mutate in changes:
            candidate = copy.deepcopy(self.current)
            mutate(candidate)
            with self.assertRaises(ValueError):
                validate_pair(self.baseline, candidate)

    def test_final_state_pass_does_not_imply_geometry_pass(self):
        case = self.protocol['cases'][0]
        result = copy.deepcopy(self.baseline['results'][0])
        forces = np.zeros((2, 2, 3))
        row = make_row(self.protocol, case, result, forces, [1, 0], reused=False)
        self.assertTrue(row['final_state_passed'])
        self.assertFalse(row['joint_passed'])
        result['penetration_m'] = .0005
        row = make_row(self.protocol, case, result, forces, [1, 0], reused=False)
        self.assertTrue(row['joint_passed'])
        result['passed'] = False
        row = make_row(self.protocol, case, result, forces, [1, 0], reused=False)
        self.assertFalse(row['joint_passed'])

    def test_per_case_stiffness_and_legacy_default(self):
        for case, expected in [(self.protocol['cases'][0], '-100000.0 0'),
                               (self.baseline['protocol']['cases'][0], '-10000 0')]:
            xml = ElementTree.fromstring(model_xml(self.protocol, case))
            self.assertEqual(xml.find('default/geom').get('solref'), expected)

    def test_native_stiffness_mismatch_rejected(self):
        # Compile, but do not step physics. Read all fields used by the verifier.
        import mujoco
        case = self.protocol['cases'][0]
        model = mujoco.MjModel.from_xml_string(model_xml(self.protocol, case))
        readback = dict(nq=model.nq, nv=model.nv, nu=model.nu, neq=model.neq,
                        timestep=model.opt.timestep, integrator=int(model.opt.integrator),
                        solver=int(model.opt.solver), iterations=int(model.opt.iterations),
                        tolerance=model.opt.tolerance)
        for name, native in dict(gravity=model.opt.gravity, mass=model.body_mass,
                                 inertia=model.body_inertia, condim=model.geom_condim,
                                 solref=model.geom_solref, solimp=model.geom_solimp,
                                 size=model.geom_size, friction=model.geom_friction,
                                 margin=model.geom_margin, gap=model.geom_gap,
                                 damping=model.dof_damping, armature=model.dof_armature).items():
            readback[name] = native.tolist()
        verify_readback(self.protocol, case, readback)
        readback['solref'][0][0] = -10000
        with self.assertRaisesRegex(ValueError, 'solref'):
            verify_readback(self.protocol, case, readback)


if __name__ == '__main__':
    unittest.main()
