"""Whole-run integrity checks on retained native data and synthetic task metadata.

No simulator is imported or started. The admitted-input boundary is mocked here;
its content/denominator checks are covered separately by test_libero_demo.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.libero_score_v2 import METRICS, BODY_METRICS, _state_link, score_run
from dexlab.libero_execute import NUMERICAL_ENVIRONMENT
from dexlab.libero_substeps import read_chunk, write_chunk
from dexlab.libero_workflow import file_hash


FIXTURE = Path(__file__).with_name('fixtures') / 'libero-damped-substeps.json'


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


class LiberoScoreV2Tests(unittest.TestCase):
    fixture_path = FIXTURE

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'run'; self.root.mkdir()
        fixture = json.loads(self.fixture_path.read_text())
        model, rows = fixture['model'], fixture['rows']
        n, per_action = 2, 2
        definition = {'objects': {'slider': 'fixture'}, 'fixtures': {}, 'regions': {},
                      'objects_of_interest': ['slider'], 'goal': ['and', ['open', 'slider'], ['open', 'slider']]}
        task = {'task_id': 'synthetic/slider', 'definition': definition}
        initial = np.r_[rows[0]['state_before']['time'], rows[0]['state_before']['qpos'], rows[0]['state_before']['qvel']]
        actions = np.zeros((n, 7), dtype=np.float32)
        self.inputs = {'task': task, 'initial': initial, 'actions': actions, 'model_xml': fixture['xml'],
                       'demonstration': {'split': 'development', 'action_count': n},
                       'admission': {'linkage': {'language': {'bddl': 'synthetic slider fixture'}}}}
        self.expected = {'schema_version': 2, 'recording': True, 'substep_recording': True,
                         'input_manifest_sha256': 'a' * 64, 'task_id': task['task_id'], 'demo_id': 'demo_0',
                         'purpose': 'development', 'runtime_versions': {'mujoco': '2.3.7'},
                         'source_sha256': {'fixture': file_hash(self.fixture_path)}}
        self.protocol = {'schema_version': 1, 'equations': 'mujoco-2.3.7-euler-v1', 'substeps_per_action': per_action,
                         'absolute_tolerances': {key: [1e-8] * (6 if key == 'contact_wrench' else 1) for key in METRICS},
                         'observations': {'obs:joint': {'shape': [1], 'dtype': '<f8'}}}
        if model['schema_version'] == 2:
            self.protocol.update(schema_version=2, equations='mujoco-2.3.7-euler-body-v2')
            for key in BODY_METRICS:
                size = model['dimensions']['nbody'] * (10 if key == 'spatial_inertia' else 6) if key != 'projected_body_effort' else model['dimensions']['nv']
                self.protocol['absolute_tolerances'][key] = [1e-8] * size
        binding = {'schema_version': 2, 'goal': definition['goal'], 'objects_of_interest': ['slider'],
                   'model_dimensions': {k: model['dimensions'][k] for k in ('nbody', 'njnt', 'nq', 'nv', 'nsite', 'ngeom')},
                   'entities': {'slider': {'kind': 'object', 'status': 'bound', 'body_id': 1, 'body_name': 'slider',
                    'body_ids': [1], 'geom_ids': [0], 'query_joint_ids': [0],
                    'joints': [{'joint_id': 0, 'joint_name': 'j', 'type': 'slide', 'body_id': 1, 'qpos_indices': [0], 'dof_indices': [0]}]}}}
        init = {'status': 'completed', 'phase': 'ready-for-actions', 'normalized_indices': [],
                'model_dimensions': {'nq': 1, 'nv': 1, 'na': 0},
                **{key: initial.tolist() for key in ('source', 'after_set', 'after_forward', 'expected_after_forward', 'after_post')}}
        for name in ('input-model.xml', 'relocated-model.xml', 'effective-model.xml'):
            (self.root / name).write_text(fixture['xml'])
        save_json(self.root / 'input.json', self.expected)
        save_json(self.root / 'task.json', task)
        save_json(self.root / 'assets.json', {})
        save_json(self.root / 'bindings.json', binding)
        save_json(self.root / 'physics-model.json', model)
        save_json(self.root / 'initialization.json', init)
        chunks, terminal, intervals, goals = [], [], [], []
        (self.root / 'substeps').mkdir()
        for action in range(n):
            selected = rows[action * per_action:(action + 1) * per_action]
            for row in selected:
                row['action_index'] = action
            name = f'action-{action:06d}.npz'
            write_chunk(self.root / 'substeps' / name, selected)
            chunks.append({'name': name, 'action_index': action, 'substeps': per_action})
            terminal.append(selected[-1])
            end = selected[-1]['state_after']['time']
            intervals.append([selected[0]['state_before']['time'], end])
            goals.append({'check_index': action, 'status': 'completed', 'time_s': end, 'time_after_s': end,
                          'native_success': True, 'queries': [{'goal_index': i, 'predicate': atom, 'value': True}
                                                             for i, atom in enumerate(definition['goal'][1:])]})
        save_json(self.root / 'goals.json', goals)
        save_json(self.root / 'visual-markers.json', [{}, {}])
        save_json(self.root / 'substeps.json', {'schema_version': 1, 'active_action': None, 'unflushed_substeps': 0,
                  'substeps': len(rows), 'chunks': chunks})
        trajectory = {'initial': initial, 'actions': actions, 'action_interval': np.array(intervals),
                      'time': np.array(intervals)[:, 1], 'done': np.ones(n, dtype=bool), 'reward': np.ones(n),
                      'state': np.array([np.r_[r['state_after']['time'], r['state_after']['qpos'], r['state_after']['qvel']] for r in terminal]),
                      'goal_event_range': np.array([[0, 1], [1, 2]], dtype=np.int64),
                      'site_rgba': np.zeros((n, 0, 4)), 'obs:joint': np.array([r['state_after']['qpos'] for r in terminal])}
        for key in ('ctrl', 'actuator_force', 'qfrc_actuator'):
            trajectory[key] = np.array([r['force'][key] for r in terminal])
        for key, native in (('body_xpos', 'xpos'), ('body_xquat', 'xquat'), ('body_xipos', 'xipos')):
            trajectory[key] = np.array([r['force'][native] for r in terminal])
        np.savez_compressed(self.root / 'trajectory.npz', **trajectory)
        self.receipt = {'schema_version': 2, 'status': 'completed', 'phase': 'terminal',
                        'recording': True, 'substep_recording': True, 'task_id': task['task_id'],
                        'demo_id': 'demo_0', 'input_manifest_sha256': 'a' * 64,
                        'source_sha256': self.expected['source_sha256'], 'versions': self.expected['runtime_versions'],
                        'purpose': 'development', 'input_split': 'development', 'expected_actions': n, 'actions_executed': n,
                        'instruction': {**self.inputs['admission']['linkage']['language'], 'native_contract': 'pinned-bddl', 'policy_used': False},
                        'model_timestep': .002, 'control_timestep': .004, 'control_freq': 250,
                        'initial_time_s': float(initial[0]), 'final_time_s': intervals[-1][1],
                        'native_success_any': True, 'native_success_final': True}
        self.seal()
        self.snapshot = self.root.parent / 'original'
        shutil.copytree(self.root, self.snapshot)

    def seal(self):
        self.receipt['files'] = {p.relative_to(self.root).as_posix(): file_hash(p) for p in self.root.rglob('*')
                                 if p.is_file() and p.name != 'run.json'}
        save_json(self.root / 'run.json', self.receipt)
        return file_hash(self.root / 'run.json')

    def restore(self):
        shutil.rmtree(self.root); shutil.copytree(self.snapshot, self.root)
        self.receipt = json.loads((self.root / 'run.json').read_text())

    def score(self, *, seal=True, digest=None):
        with patch('dexlab.libero_score_v2.load_demo', return_value=self.inputs):
            return score_run(self.root, digest or (self.seal() if seal else file_hash(self.root / 'run.json')),
                             self.expected, self.root.parent / 'prepared', self.protocol)

    def edit_json(self, name, change):
        path = self.root / name; value = json.loads(path.read_text()); change(value); save_json(path, value)

    def edit_npz(self, change):
        path = self.root / 'trajectory.npz'
        with np.load(path, allow_pickle=False) as archive:
            value = {key: archive[key] for key in archive.files}
        change(value); np.savez_compressed(path, **value)

    def edit_chunk(self, change):
        path = self.root / 'substeps/action-000000.npz'
        rows = read_chunk(path); change(rows); path.unlink(); write_chunk(path, rows)

    def test_complete_native_numeric_records_preserve_separate_outcomes(self):
        result = self.score()
        self.assertTrue(result['record_valid'])
        self.assertTrue(result['numerical_consistent'])
        self.assertTrue(result['native_success'])
        self.assertEqual((result['actions'], result['substeps']), (2, 4))
        self.assertEqual(result['contacts_checked'], 0)
        self.assertEqual(result['physical_reference'], 'not-evaluated')
        self.assertEqual(result['joint_reaction_qualification'], 'pending')

    def test_external_receipt_and_file_hashes_are_independent_pins(self):
        digest = file_hash(self.root / 'run.json')
        self.receipt['native_success_final'] = False; self.seal()
        with self.assertRaisesRegex(ValueError, 'external hash'):
            self.score(seal=False, digest=digest)
        self.restore()
        (self.root / 'effective-model.xml').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Changed native artifact'):
            self.score(seal=False)

    def test_new_environment_contract_is_checked_without_inventing_historical_metadata(self):
        self.assertIsNone(self.score()['numerical_environment'])
        frozen = dict.fromkeys(NUMERICAL_ENVIRONMENT)
        frozen['OPENBLAS_NUM_THREADS'] = '1'
        self.expected['numerical_environment'] = frozen
        save_json(self.root / 'input.json', self.expected)
        self.receipt['numerical_environment'] = frozen.copy()
        self.assertEqual(self.score()['numerical_environment'], frozen)
        self.receipt['numerical_environment']['OPENBLAS_NUM_THREADS'] = '2'
        with self.assertRaisesRegex(ValueError, 'Numerical environment differs'):
            self.score()
        del self.receipt['numerical_environment']
        with self.assertRaisesRegex(ValueError, 'Numerical environment differs'):
            self.score()
        self.expected['numerical_environment'] = {}
        self.receipt['numerical_environment'] = {}
        save_json(self.root / 'input.json', self.expected)
        with self.assertRaisesRegex(ValueError, 'Freeze every numerical environment'):
            self.score()

    def test_rehashed_task_source_split_and_instruction_changes_rejected(self):
        for key, value in (('source_sha256', {}), ('versions', {}), ('input_split', 'validation'),
                           ('instruction', {}), ('actions_executed', 1), ('task_id', 'wrong'),
                           ('substep_recording', False), ('status', 'failed')):
            self.restore(); self.receipt[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.score()

    def test_rehashed_dropped_secondary_goal_and_stale_queries_rejected(self):
        for mutate in (lambda e: e[0]['queries'].pop(), lambda e: e[0].update(time_s=.002),
                       lambda e: e[0]['queries'][1].update(value=False), lambda e: e.pop()):
            self.restore(); self.edit_json('goals.json', mutate)
            with self.assertRaises(ValueError):
                self.score()

    def test_rehashed_body_joint_and_goal_bindings_rejected(self):
        for change in (lambda b: b['entities']['slider'].update(body_id=0),
                       lambda b: b['entities']['slider'].update(joints=[]),
                       lambda b: b['entities']['slider'].update(query_joint_ids=[]),
                       lambda b: b.update(goal=['and', ['open', 'slider']])):
            self.restore(); self.edit_json('bindings.json', change)
            with self.assertRaises(ValueError):
                self.score()

    def test_rehashed_truncation_reordering_and_stale_substep_epochs_rejected(self):
        for change in (lambda rows: rows.pop(), lambda rows: rows.reverse(),
                       lambda rows: rows[0].update(sequence=1), lambda rows: rows[0].update(action_index=1),
                       lambda rows: rows[0].update(force_time=.001),
                       lambda rows: rows[1]['state_before']['qpos'].__setitem__(0, .7)):
            self.restore(); self.edit_chunk(change)
            with self.assertRaises(ValueError):
                self.score()

    def test_rehashed_terminal_state_action_force_and_observation_loss_rejected(self):
        for change in (lambda t: t['state'][-1].__setitem__(1, .8),
                       lambda t: t['actions'][-1].__setitem__(0, .8),
                       lambda t: t['ctrl'][0].__setitem__(0, 12),
                       lambda t: t.pop('obs:joint'), lambda t: t.__setitem__('done', t['done'].astype(float)),
                       lambda t: t['body_xpos'][0, 1].__setitem__(0, .8)):
            self.restore(); self.edit_npz(change)
            with self.assertRaises(ValueError):
                self.score()

    def test_rehashed_force_errors_remain_visible_as_numerical_failures(self):
        self.edit_chunk(lambda rows: rows[0]['force']['qfrc_smooth'].__setitem__(0, 100))
        result = self.score()
        self.assertTrue(result['record_valid'])
        self.assertFalse(result['numerical_consistent'])
        self.assertTrue(result['native_success'])
        self.assertGreater(result['action_diagnostics'][0]['violating_substeps']['smooth_force'], 0)

    def test_rehashed_initialization_final_time_and_chunk_index_rejected(self):
        self.edit_json('initialization.json', lambda i: i['after_post'].__setitem__(1, .4))
        with self.assertRaises(ValueError):
            self.score()
        self.restore(); self.receipt['final_time_s'] = 9
        with self.assertRaises(ValueError):
            self.score()
        for change in (lambda i: i.update(unflushed_substeps=1), lambda i: i['chunks'].reverse(),
                       lambda i: i.update(substeps=3)):
            self.restore(); self.edit_json('substeps.json', change)
            with self.assertRaises(ValueError):
                self.score()

    def test_path_escape_and_extra_chunk_are_rejected(self):
        outside = self.root.parent / 'external.json'; outside.write_text('{}')
        target = self.root / 'assets.json'; target.unlink(); target.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.score()
        self.restore(); (self.root / 'substeps/extra.npz').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'extra substep'):
            self.score()

    def test_missing_or_weakened_contract_is_not_implicitly_chosen(self):
        for key, value in (('absolute_tolerances', {}), ('observations', {}), ('substeps_per_action', 1)):
            original = deepcopy(self.protocol); self.protocol[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.score()
            self.protocol = original

    def test_quaternion_only_normalization_never_permits_velocity_or_translation_jump(self):
        model = {'dimensions': {'nq': 7, 'nv': 6}, 'arrays': {'jnt_type': [0], 'jnt_qposadr': [0]}}
        before = np.r_[.2, [1., 2., 3.], [2., .5, 0., 0.], np.zeros(6)]
        after = before.copy(); after[4:8] /= np.linalg.norm(after[4:8])
        _state_link(before, after, model)
        for index in (0, 1, 4, 8):
            bad = after.copy(); bad[index] += .00001
            with self.subTest(index=index), self.assertRaises(ValueError):
                _state_link(before, bad, model)


class LiberoBodyScoreTests(LiberoScoreV2Tests):
    fixture_path = FIXTURE.with_name('libero-damped-body-substeps.json')

    def test_body_record_requires_its_frozen_protocol(self):
        result = self.score()
        self.assertEqual(result['body_observation_schema'], 2)
        self.assertEqual(result['free_com_reference_qualification'], 'pending')
        self.assertTrue(BODY_METRICS <= set(result['abs_max']))
        self.assertEqual(result['action_diagnostics'][0]['solver_iterations'], [0, 0])
        self.assertEqual(result['action_diagnostics'][0]['free_com'], [])
        self.protocol.update(schema_version=1, equations='mujoco-2.3.7-euler-v1')
        for key in BODY_METRICS:
            del self.protocol['absolute_tolerances'][key]
        with self.assertRaisesRegex(ValueError, 'protocol'):
            self.score()

    def test_rehashed_body_cache_corruption_cannot_be_numerically_consistent(self):
        for channel, check, index in (('cinert', 'spatial_inertia', 9), ('cvel', 'spatial_velocity', 0)):
            self.restore()
            def corrupt(rows):
                rows[0]['force'][channel][1][index] += 1
            self.edit_chunk(corrupt)
            result = self.score()
            self.assertTrue(result['record_valid'])
            self.assertFalse(result['numerical_consistent'])
            self.assertEqual(result['action_diagnostics'][0]['violating_substeps'][check], 1)

    def test_rehashed_missing_body_signal_or_stale_solver_is_rejected(self):
        self.edit_chunk(lambda rows: rows[0]['force'].pop('cdof_dot'))
        with self.assertRaises(KeyError):
            self.score()
        self.restore()
        self.edit_chunk(lambda rows: rows[0]['force']['solver'].update(nnz=0))
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.score()

    def test_finite_inputs_that_overflow_derived_body_accounting_are_rejected(self):
        self.edit_json('physics-model.json', lambda model: model['arrays']['body_mass'].__setitem__(1, 1e308))
        with np.errstate(over='ignore', invalid='ignore'):
            with self.assertRaisesRegex(ValueError, 'Non-finite derived'):
                self.score()


if __name__ == '__main__':
    unittest.main()
