"""Adversarial evidence checks for fixed force-limit interventions."""
import unittest
from dexlab.genesis_pinch_probe import load_case
from dexlab.genesis_pinch_score import score_trial


def stationary_record(condition='open_negative', cap=.2, x=-.002):
    weight = .064 * 9.81
    return {
        'condition': condition,
        'initial': {
            'cube_link': 4, 'pad_links': [2, 3], 'plane_link': 0,
            'cube_mass': [.064], 'gripper_mass': [0., 1., .1, .1],
            'armature': [0.] * 3, 'kp': [1000., 500., 500.],
            'kv': [50., 20., 20.],
            'force_range': [[-50., -cap, -cap], [50., cap, cap]],
            'q': [0.] * 3, 'object_pos': [x, 0., .02],
            'object_vel': [0.] * 3, 'geom_sol_params': [[.002], [.002]],
            'joint_sol_params': [[.01]] * 3,
        },
        'samples': [{
            'time': (i+1)*.001, 'q': [0.] * 3,
            'object_pos': [x, 0., .02], 'object_vel': [0.] * 3,
            'object_quat': [1., 0., 0., 0.],
            'object_contact_force': [[0., 0., weight]],
            'contacts': {'link_a': [4], 'link_b': [0],
                         'force_a': [[0., 0., weight]],
                         'force_b': [[0., 0., -weight]], 'penetration': [0.]},
        } for i in range(4000)],
    }


class ForceLimitEvidenceTests(unittest.TestCase):
    def test_observed_cap_and_offset_must_match_expected_case(self):
        record = stationary_record()
        self.assertTrue(score_trial(record, .001, force_limit=.2, initial_x=-.002)['passed'])
        self.assertFalse(score_trial(record, .001)['checks']['declared_import'])
        self.assertFalse(score_trial(record, .001, force_limit=.4, initial_x=-.002)['checks']['declared_import'])
        self.assertFalse(score_trial(record, .001, force_limit=.2, initial_x=.002)['checks']['declared_import'])

    def test_numerically_consistent_table_support_does_not_count_as_grasp(self):
        result = score_trial(stationary_record('pinch'), .001, force_limit=.2, initial_x=-.002)
        self.assertTrue(result['checks']['force_ledger'])
        self.assertTrue(result['checks']['momentum_balance_5percent_weight'])
        self.assertFalse(result['checks']['hold_or_negative'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['first_failure_time_s']['hold_or_negative'], 2.)

    def test_unregistered_case_fails_before_engine_import(self):
        with self.assertRaisesRegex(ValueError, 'Unknown preregistered'):
            load_case('unregistered-retuned-case')

    def test_misspelled_condition_is_not_a_negative(self):
        with self.assertRaisesRegex(ValueError, 'Unknown trial condition'):
            score_trial(stationary_record('pinc'), .001)

    def test_force_timeline_uses_native_pad_vectors_not_cap(self):
        record = stationary_record()
        result = score_trial(record, .001, force_limit=.2, initial_x=-.002, include_timeline=True)
        self.assertEqual(result['timeline'][0]['pad_forces_on_cube_N'], [[0., 0., 0.], [0., 0., 0.]])
        self.assertEqual(result['timeline'][0]['pad_abs_x_force_proxy_N'], [0., 0.])
        self.assertEqual(result['first_failure_time_s'], {})

    def test_single_bad_force_sample_has_exact_failure_time(self):
        record = stationary_record()
        record['samples'][13]['object_contact_force'] = [[0., 0., 0.]]
        result = score_trial(record, .001, force_limit=.2, initial_x=-.002)
        self.assertFalse(result['checks']['force_ledger'])
        self.assertEqual(result['first_failure_time_s']['force_ledger'], .014)

    def test_public_scorer_rejects_source_substitution_and_case_relabeling(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from dexlab.genesis_pinch_score import score

        root = Path(__file__).resolve().parents[1]
        source = (root / 'src/dexlab/genesis_pinch_probe.py').read_bytes()
        manifest = root / 'demos/contact-benchmark/force-limit-v1.json'
        case = load_case('dev-open')
        protocol = {
            'schema': 2, 'case': case, 'engine': '1.4.3', 'dt_s': .0005,
            'steps': 8000, 'duration_s': 4, 'mass_kg': .064, 'cube_size_m': .04,
            'mu': .5, 'gravity_m_s2': 9.81, 'backend': 'cpu', 'precision': '64',
            'seed': 0, 'repeats': 1, 'conditions': ['open_negative'],
            'plane_cube_geom_timeconst_s': .002,
            'source_sha256': hashlib.sha256(source).hexdigest(),
        }
        record = stationary_record(cap=10., x=0.)
        record.update(case_id='dev-open', repeat=0)
        record['initial'].update(object_quat=[1., 0., 0., 0.],
                                 object_ang=[0., 0., 0.], qvel=[0., 0., 0.],
                                 geom_friction=[.5]*4,
                                 cube_inertia=[[[.064*.04**2/6 if i == j else 0.
                                                 for j in range(3)] for i in range(3)]])
        record['samples'] *= 2
        record['samples'] = [{**row, 'time': (i+1)*.0005}
                             for i, row in enumerate(record['samples'])]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'runner.py').write_bytes(source)
            (directory / manifest.name).write_bytes(manifest.read_bytes())
            (directory / 'protocol.json').write_text(json.dumps(protocol))
            data = directory / 'open_negative-0.json'
            data.write_text(json.dumps(record))
            result = score(directory)
            self.assertTrue(result['numerically_valid'])
            self.assertTrue(result['task_passed'])
            self.assertTrue(result['passed'])
            record['case_id'] = 'eval-left-open'
            data.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Mislabeled'):
                score(directory)
            (directory / 'runner.py').write_bytes(source + b'\n# altered\n')
            with self.assertRaisesRegex(ValueError, 'runner source'):
                score(directory)
