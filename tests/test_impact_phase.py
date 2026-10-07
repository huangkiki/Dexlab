"""Phase mapping, complete-group verdicts and native initial state; no stepping."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from dexlab.impact_run import model_xml
from dexlab.impact_score import score
from dexlab.impact_phase import summarize, validate_pair

ROOT = Path(__file__).parents[1]


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.new = json.loads((ROOT/'docs/evidence/impact-phase/manifest.json').read_text())
        report = json.loads((ROOT/'docs/evidence/impact-stiffness/results.json').read_text())
        self.old = dict(protocol=report['protocol'], campaign=report['new_campaign'],
                        results=[r for r in report['results'] if not r['reused']])
        self.current = dict(protocol=self.new, campaign=report['new_campaign'])

    def test_bindings_and_mapping(self):
        self.assertEqual(len(validate_pair(self.old, self.current)), 9)
        for mutate in (
            lambda p: p['cases'][0]['initial_x_m'].__setitem__(1, .06),
            lambda p: p['cases'][0].__setitem__('arrival_phase', .125),
            lambda p: p['baseline_bindings'][0].__setitem__('trace_sha256', 'wrong'),
            lambda p: p.__setitem__('overlap_budget_m', .002),
        ):
            candidate = copy.deepcopy(self.current)
            mutate(candidate['protocol'])
            with self.assertRaises(ValueError):
                validate_pair(self.old, candidate)

    def test_native_initial_position_and_legacy_fallback(self):
        import mujoco
        for case in (self.new['cases'][0], self.old['protocol']['cases'][0]):
            model = mujoco.MjModel.from_xml_string(model_xml(self.new, case))
            data = mujoco.MjData(model)
            np.testing.assert_array_equal(data.qpos[[0, 7]], case.get('initial_x_m', self.new['initial_x_m']))

    def test_mismatched_initial_state_is_rejected_before_dynamics(self):
        case = self.new['cases'][0]; n = round(self.new['duration_s']/case['timestep'])
        states = np.zeros((n+1, 2, 13)); states[:, :, 3] = 1
        states[0, :, 0] = self.new['initial_x_m']  # Incorrect old positions.
        states[0, :, 7] = case['initial_vx_m_s']
        trace = dict(states=states, times=np.arange(n+1)*case['timestep'],
                     force_times=np.arange(n)*case['timestep'], forces=np.zeros((n,2,3)),
                     contact_count=np.zeros(n), contact_distance=np.zeros(n), warnings=np.zeros((n,1)))
        with self.assertRaisesRegex(ValueError, 'Incorrect initial state'):
            score(self.new, case, trace)

    def test_group_requires_every_phase_and_preserves_failure(self):
        rows = []
        for case in self.new['cases']:
            rows.append(dict(id=case['id'], speed_m_s=case['initial_vx_m_s'][0],
                             timestep_s=case['timestep'], arrival_phase=case['arrival_phase'],
                             joint_passed=True, penetration_m=.0005,
                             metrics=dict(velocity_error_m_s=.001, relative_energy_error=.001)))
        rows += [dict(r, id='baseline-'+r['id'], arrival_phase=0.) for r in rows if r['arrival_phase']==.25]
        self.assertTrue(all(g['finite_phase_set_passed'] for g in summarize(rows)))
        rows[0]['joint_passed'] = False
        self.assertFalse(summarize(rows)[0]['finite_phase_set_passed'])
        with self.assertRaises(ValueError):
            summarize(rows[:-1])
