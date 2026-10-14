"""Task-aware execution reuses the existing immutable budget and recovery ledger."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from dexlab.libero_execute import INITIALIZATION_CONTRACT, NUMERICAL_ENVIRONMENT, RUNTIME_PACKAGES, source_hashes
from dexlab.libero_trials import create_tasks, run_task, task_sources
from dexlab.libero_workflow import file_hash
from dexlab.migration_budget import MigrationBudget, json_bytes, publish


class LiberoTaskTrialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.campaign = self.root / 'campaign'
        reference = self.root / 'evidence.json'; reference.write_text('{"scope":"unit fixture"}')
        self.inputs = {'task': {'task_id': 'fixture/task'},
                       'demonstration': {'split': 'development', 'action_count': 2}}
        loader = patch('dexlab.libero_demo.load_demo', return_value=self.inputs)
        loader.start(); self.addCleanup(loader.stop)
        handle = patch('dexlab.libero_trials.execution_cgroup', return_value={'cgroup': '/fixture', 'boot_id': 'fixture'})
        handle.start(); self.addCleanup(handle.stop)
        payload = {'schema_version': 2, 'recording': True, 'substep_recording': True, 'seed': 0,
                   'initialization_contract': INITIALIZATION_CONTRACT,
                   'purpose': 'development', 'runtime_versions': {name: 'fixture' for name in RUNTIME_PACKAGES},
                   'source_sha256': source_hashes(), 'input_dir': str(self.root),
                   'input_manifest_sha256': 'a' * 64, 'demo_id': 'demo_0', 'task_id': 'fixture/task',
                   'libero_root': str(self.root)}
        payload['numerical_environment'] = dict.fromkeys(NUMERICAL_ENVIRONMENT)
        payload['numerical_environment']['OPENBLAS_NUM_THREADS'] = '1'
        self.manifest = {'schema_version': 2, 'kind': 'libero-native-task-campaign',
                         'python': sys.executable, 'scoring_python': sys.executable,
                         'config_dir': str(self.root), 'cache_dir': str(self.root), 'max_output_bytes': 2**20,
                         'work_package': {'id': 'fixture', 'hypothesis': 'Run one admitted record through native and offline phases.',
                                          'max_starts': 2, 'wall_s': 20, 'evidence_sha256': [file_hash(reference)]},
                         'evidence': [{'path': str(reference), 'sha256': file_hash(reference)}],
                         'cases': [{'id': 'fixture-on', 'execution': payload,
                                    'numerical_protocol': {'schema_version': 2, 'equations': 'mujoco-2.3.7-euler-body-v2'}}]}
        self.mode = 'success'

    def child(self, argv, destination, deadline, process_record, *, environment):
        for key, value in self.manifest['cases'][0]['execution']['numerical_environment'].items():
            self.assertEqual(environment.get(key), value)
            if value is None:
                self.assertNotIn(key, environment)
        destination.write_text('mocked child; no native execution\n')
        publish(process_record, json_bytes({'pid': 99999999, 'argv': argv}), replace=True)
        if self.mode == 'timeout':
            raise subprocess.TimeoutExpired(argv, 1)
        if argv[2] == 'dexlab.libero_execute':
            raw = Path(argv[-1]); raw.mkdir()
            payload = json.loads(Path(argv[-2]).read_text())
            receipt = {'status': 'completed', 'actions_executed': 2, 'task_id': payload['task_id'],
                       'demo_id': payload['demo_id'], 'native_success_final': True}
            publish(raw / 'run.json', json_bytes(receipt))
            return 1 if self.mode == 'native-failed' else 0
        if self.mode == 'score-failed':
            return 1
        score = {'run_sha256': argv[4], 'record_valid': True, 'numerical_consistent': self.mode != 'numeric-failed',
                 'protocol': json.loads(Path(argv[7]).read_text())}
        if self.mode == 'wrong-score':
            score['run_sha256'] = '0' * 64
        publish(Path(argv[-1]), json_bytes(score))
        return 0

    def run_case(self):
        with patch('dexlab.libero_trials.command', side_effect=self.child):
            return run_task(self.campaign, 'fixture-on', timeout=5)

    def test_complete_native_and_score_phases_share_one_reservation(self):
        budget = create_tasks(self.campaign, self.manifest)
        result = self.run_case()
        self.assertEqual(result['outcome'], 'recorded')
        self.assertTrue(result['record_valid'])
        self.assertTrue(result['numerical_consistent'])
        state = budget.status()
        self.assertEqual(state['starts_used'], 1)
        self.assertIsNotNone(state['attempts'][0]['terminal'])
        attempt = self.campaign / 'attempts/0000'
        self.assertTrue((attempt / 'native-process.json').is_file())
        self.assertTrue((attempt / 'scoring-process.json').is_file())
        self.assertEqual(file_hash(attempt / 'result.json'), state['attempts'][0]['terminal']['evidence_sha256'])
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.run_case()

    def test_numerical_controls_replace_or_remove_inherited_values_before_child_import(self):
        create_tasks(self.campaign, self.manifest)
        with patch.dict('os.environ', {key: '8' for key in NUMERICAL_ENVIRONMENT}):
            result = self.run_case()
        self.assertEqual(result['outcome'], 'recorded')

    def test_negative_numeric_result_is_retained_without_claiming_consistency(self):
        create_tasks(self.campaign, self.manifest); self.mode = 'numeric-failed'
        result = self.run_case()
        self.assertEqual(result['outcome'], 'recorded')
        self.assertFalse(result['numerical_consistent'])
        self.assertTrue(result['native_success'])

    def test_child_failures_and_timeout_retain_terminal_evidence(self):
        for mode in ('native-failed', 'score-failed', 'wrong-score', 'timeout'):
            with self.subTest(mode=mode):
                self.campaign = self.root / mode; self.mode = mode
                budget = create_tasks(self.campaign, self.manifest)
                result = self.run_case()
                self.assertEqual(result['outcome'], 'interrupted' if mode == 'timeout' else 'failed')
                self.assertFalse(result['record_valid'])
                state = budget.status()
                self.assertEqual(state['starts_used'], 1)
                self.assertIsNotNone(state['attempts'][0]['terminal'])

    def test_changed_sources_task_split_and_evidence_rejected_before_launch(self):
        for change in (lambda m: m['cases'][0]['execution'].update(task_id='wrong'),
                       lambda m: m['cases'][0]['execution'].update(purpose='validation'),
                       lambda m: m['cases'][0]['execution'].update(source_sha256={}),
                       lambda m: m['cases'][0]['execution'].pop('initialization_contract'),
                       lambda m: m['cases'][0]['execution'].update(initialization_contract='undeclared'),
                       lambda m: m['cases'][0]['execution'].update(numerical_environment={}),
                       lambda m: m['cases'][0]['execution'].update(numerical_environment={key: 1 for key in NUMERICAL_ENVIRONMENT}),
                       lambda m: m.update(evidence=[])):
            manifest = deepcopy(self.manifest); change(manifest)
            with self.assertRaises(ValueError):
                create_tasks(self.campaign, manifest)
            self.assertFalse(self.campaign.exists())
        budget = create_tasks(self.campaign, self.manifest)
        with patch('dexlab.libero_trials.task_sources', return_value={}):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.run_case()
        self.assertEqual(budget.status()['starts_used'], 0)

    def test_source_revision_inherits_all_costs_and_retires_predecessor(self):
        prior = create_tasks(self.campaign, self.manifest)
        self.run_case(); state = prior.status()
        manifest = deepcopy(self.manifest)
        manifest['prior_budget'] = {'directory': str(self.campaign), 'head_sha256': file_hash(self.campaign / 'head.json'),
                                   'manifest_sha256': state['manifest_sha256'], 'starts_used': state['starts_used'],
                                   'wall_s': state['wall_charged_or_reserved_s']}
        next_root = self.root / 'revision'; successor = create_tasks(next_root, manifest)
        inherited = successor.status()
        self.assertEqual(inherited['starts_used'], state['starts_used'])
        self.assertEqual(inherited['wall_charged_or_reserved_s'], state['wall_charged_or_reserved_s'])
        self.assertEqual(inherited['work_package'], state['work_package'])
        self.assertTrue((self.campaign / 'superseded.json').exists())

    def test_archive_cap_and_unknown_case_do_not_consume_reservations(self):
        budget = create_tasks(self.campaign, self.manifest)
        with self.assertRaisesRegex(ValueError, 'outside'):
            run_task(self.campaign, 'unknown', timeout=5)
        (self.campaign / 'large.bin').write_bytes(b'0' * 2**20)
        with self.assertRaisesRegex(ValueError, 'archive allowance'):
            self.run_case()
        self.assertEqual(budget.status()['starts_used'], 0)


if __name__ == '__main__':
    unittest.main()
