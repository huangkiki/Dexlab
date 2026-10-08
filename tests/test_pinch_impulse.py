"""Constructed numerical diagnostics, not results from a physics campaign."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from dexlab.pinch_impulse_score import score_trace, score_campaign
from dexlab.pinch_run import compiled_readback, model_xml

P = json.loads((Path(__file__).resolve().parents[1] / 'docs/evidence/pinch-impulse/manifest.json').read_text())


def synthetic_trace(case=None):
    case = case or P['cases'][1]
    n = round(P['duration_s'] / case['timestep'])
    h = case['timestep']
    state = np.zeros((n + 1, 18)); state[:, 0] = np.arange(n + 1) * h; state[:, 6] = 1
    command = case['capacity_ratio'] * P['cube_mass_kg'] * P['gravity_m_s2'] / (2 * P['friction']) * np.minimum(np.arange(n) / round(P['ramp_s'] / h), 1)
    actuator = np.zeros((n, 8)); actuator[:, :2] = command[:, None]
    external = np.zeros((n, 3)); external[round(P['preload_s'] / h):, 2] = -P['cube_mass_kg'] * P['gravity_m_s2']
    body_load = np.zeros((n, 4, 6)); body_load[:, 3, :3] = external
    smooth = actuator.copy(); smooth[:, 2:5] += external
    diagonal = [P['jaw_mass_kg']] * 2 + [P['cube_mass_kg']] * 3 + [P['cube_mass_kg'] * P['side_m']**2 / 6] * 3
    return case, dict(states=state, qacc=np.zeros((n, 8)), mass=np.tile(np.diag(diagonal), (n, 1, 1)),
                      commands=actuator[:, :2].copy(), external=external, body_load=body_load, force_times=state[:-1, 0].copy(),
                      qfrc_smooth=smooth, qfrc_constraint=-smooth, qfrc_actuator=actuator,
                      qfrc_bias=np.zeros((n, 8)), qfrc_passive=np.zeros((n, 8)), qfrc_applied=np.zeros((n, 8)),
                      warnings=np.zeros((n, 8), int), nefc=np.full(n, 4, int), solver_niter=np.ones((n, 1), int),
                      solver_offsets=np.arange(n + 1), solver_stats=np.zeros((n, 9)))


class PinchImpulseTests(unittest.TestCase):
    def test_balanced_algebraic_trace(self):
        c, t = synthetic_trace()
        result = score_trace(P, c, t)
        self.assertEqual(result['metrics']['total_peak_n_s'], 0)
        self.assertEqual(result['status'], 'diagnostic consistent')

    def test_force_residual_is_measured_not_silently_rejected(self):
        c, t = synthetic_trace()
        t['qfrc_constraint'][800, 4] += 2e-5
        result = score_trace(P, c, t)['metrics']
        self.assertAlmostEqual(result['total_peak_n_s'], 2e-8)
        self.assertAlmostEqual(result['force_peak_n_s'], 2e-8)
        self.assertEqual(result['integration_peak_n_s'], 0)

    def test_angular_units_remain_separate(self):
        c, t = synthetic_trace(); t['qfrc_constraint'][800, 7] = 1e-4
        result = score_trace(P, c, t)['metrics']
        self.assertEqual(result['total_peak_n_s'], 0)
        self.assertAlmostEqual(result['total_peak_n_m_s'], 1e-7)

    def test_missing_or_nonfinite_observations(self):
        c, t = synthetic_trace()
        for name in t:
            with self.subTest(field=name):
                bad = dict(t); del bad[name]
                with self.assertRaises(ValueError):
                    score_trace(P, c, bad)
        t['qacc'][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'qacc'):
            score_trace(P, c, t)

    def test_wrong_state_acceleration_force_mass_and_epochs(self):
        c, t = synthetic_trace()
        for name, index, value in (
                ('states', (900, 14), 1e-4), ('qacc', (900, 4), 1e-4),
                ('qfrc_smooth', (900, 4), 1e-4), ('mass', (900, 4, 4), .1),
                ('force_times', 900, .01), ('commands', (900, 0), 1),
                ('qfrc_actuator', (900, 0), 1), ('body_load', (900, 2, 4), 1),
                ('states', (900, 5), 1e-4)):
            with self.subTest(field=name):
                bad = copy.deepcopy(t); bad[name][index] += value
                with self.assertRaises(ValueError):
                    score_trace(P, c, bad)

    def test_missing_or_reindexed_solver_history(self):
        c, t = synthetic_trace()
        for name, value in (('solver_stats', t['solver_stats'][:-1]),
                            ('solver_niter', np.full_like(t['solver_niter'], 101))):
            with self.subTest(field=name):
                bad = dict(t); bad[name] = value
                with self.assertRaises(ValueError):
                    score_trace(P, c, bad)
        t['solver_stats'][3, 1] = 9
        with self.assertRaisesRegex(ValueError, 'index'):
            score_trace(P, c, t)

    def test_rehashed_protocol_not_trusted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); evidence = root / 'trusted'; evidence.mkdir()
            (evidence / 'manifest.json').write_text(json.dumps(P))
            bad = dict(P, cube_mass_kg=1)
            (root / 'manifest.json').write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'trusted'):
                score_campaign(root, evidence, root)

    def test_native_compilation_no_steps(self):
        import mujoco as mj
        from dexlab.pinch_score import validate_readback
        for case in P['cases']:
            spec = dict(P, solver_tolerance=case['solver_tolerance'])
            model = mj.MjModel.from_xml_string(model_xml(spec, case))
            data = mj.MjData(model)
            validate_readback(spec, case, compiled_readback(model))
            self.assertGreaterEqual(len(data.solver) // len(data.solver_niter), 100)
            mj.mj_forward(model, data)
            matrix = np.zeros((model.nv, model.nv))
            mj.mj_fullM(model, data, matrix)
            self.assertTrue(np.isfinite(matrix).all())
            self.assertEqual(matrix.shape, (8, 8))
            self.assertEqual(data.time, 0)




class CampaignTests(unittest.TestCase):
    """Synthetic provenance fixtures; compiled models are never stepped."""

    def setUp(self):
        import mujoco as mj
        from dexlab import pinch_run, pinch_impulse_run
        from dexlab.pinch_impulse_score import digest
        self.digest = digest
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'run'; self.root.mkdir()
        self.evidence = self.root.parent / 'evidence'; self.evidence.mkdir()
        self.baseline = self.root.parent / 'baseline'; self.baseline.mkdir()
        self.protocol = copy.deepcopy(P)
        for case in P['cases']:
            _, trace = synthetic_trace(case)
            directory = self.root / case['id']; directory.mkdir()
            np.savez_compressed(directory / 'trace.npz', **trace)
            spec = dict(P, solver_tolerance=case['solver_tolerance'])
            xml = model_xml(spec, case); (directory / 'model.xml').write_text(xml)
            metadata = dict(case=case, readback=compiled_readback(mj.MjModel.from_xml_string(xml)),
                            cube_body=3, state_writes_after_initialization=0,
                            force_epoch='states[i].time; states[i+1] postintegration',
                            solver_island_capacity=1, solver_iteration_capacity=200,
                            statistic_fields=['island', 'iteration', 'improvement', 'gradient', 'lineslope', 'nactive', 'nchange', 'neval', 'nupdate'],
                            trace_sha256=digest(directory / 'trace.npz'), xml_sha256=digest(directory / 'model.xml'),
                            setup_s=0., control_s=0., native_step_s=0., observation_s=0., serialization_s=0., total_case_wall_s=0.)
            (directory / 'metadata.json').write_text(json.dumps(metadata))
            if case['solver_tolerance'] == 1e-10:
                ref = self.protocol['baseline'][str(case['capacity_ratio'])]
                target = self.baseline / ref['id']; target.mkdir()
                np.savez_compressed(target / 'trace.npz', states=trace['states'])
                ref['trace_sha256'] = digest(target / 'trace.npz')
        self.write_protocol()
        campaign = dict(completed_cases=6, runtime=dict(version=P['version'], record_verified=True),
                        manifest_sha256=digest(self.root / 'manifest.json'),
                        runner_sha256=digest(pinch_impulse_run.__file__), fixture_source_sha256=digest(pinch_run.__file__))
        (self.root / 'campaign.json').write_text(json.dumps(campaign))

    def write_protocol(self):
        for directory in (self.root, self.evidence):
            (directory / 'manifest.json').write_text(json.dumps(self.protocol))

    def score(self):
        return score_campaign(self.root, self.evidence, self.baseline)

    def test_all_cases_and_baseline_binding(self):
        rows = self.score()['results']
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r['status'] == 'diagnostic consistent' for r in rows))
        self.assertEqual(sum(r.get('baseline_matched', False) for r in rows), 2)

    def test_artifact_mutation_rejected(self):
        path = self.root / P['cases'][0]['id'] / 'trace.npz'
        path.write_bytes(path.read_bytes() + b'changed force archive')
        with self.assertRaisesRegex(ValueError, 'Artifact hash'):
            self.score()

    def test_wrong_compiled_mass_rejected(self):
        path = self.root / P['cases'][0]['id'] / 'metadata.json'
        meta = json.loads(path.read_text()); meta['readback']['body_mass'][3] *= 2
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
            self.score()

    def test_wrong_runner_source_rejected(self):
        path = self.root / 'campaign.json'; meta = json.loads(path.read_text()); meta['runner_sha256'] = '0' * 64
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, 'Source/protocol'):
            self.score()

    def test_changed_baseline_hash_retains_rejection_and_remaining_cases(self):
        ref = self.protocol['baseline']['1']; path = self.baseline / ref['id'] / 'trace.npz'
        path.write_bytes(path.read_bytes() + b'changed baseline')
        rows = self.score()['results']
        self.assertEqual(rows[1]['status'], 'invalid diagnostic')
        self.assertIn('Baseline artifact hash', rows[1]['error'])
        self.assertEqual(rows[-1]['status'], 'diagnostic consistent')

    def test_rehashed_invalid_acceleration_does_not_hide_remaining_cases(self):
        directory = self.root / P['cases'][0]['id']
        with np.load(directory / 'trace.npz') as f:
            trace = {k: f[k] for k in f.files}
        trace['qacc'][500, 4] = .1
        np.savez_compressed(directory / 'trace.npz', **trace)
        path = directory / 'metadata.json'; meta = json.loads(path.read_text())
        meta['trace_sha256'] = self.digest(directory / 'trace.npz'); path.write_text(json.dumps(meta))
        rows = self.score()['results']
        self.assertIn('acceleration integration', rows[0]['error'])
        self.assertEqual(rows[-1]['status'], 'diagnostic consistent')

    def test_baseline_trajectory_difference_is_not_accepted(self):
        ref = self.protocol['baseline']['1']; path = self.baseline / ref['id'] / 'trace.npz'
        with np.load(path) as f:
            states = f['states'].copy()
        states[100, 5] += .01
        np.savez_compressed(path, states=states)
        ref['trace_sha256'] = self.digest(path); self.write_protocol()
        path = self.root / 'campaign.json'; meta = json.loads(path.read_text())
        meta['manifest_sha256'] = self.digest(self.root / 'manifest.json'); path.write_text(json.dumps(meta))
        rows = self.score()['results']
        self.assertIn('Baseline trajectory mismatch', rows[1]['error'])
        self.assertEqual(rows[-1]['status'], 'diagnostic consistent')


if __name__ == '__main__':
    unittest.main()
