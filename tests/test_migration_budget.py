"""Interruptions, invalid reuse and exhausted budgets must block native launches."""
import json
from pathlib import Path
import tempfile
import unittest

from dexlab.migration_budget import MigrationBudget, digest


class MigrationBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'comparison'
        self.budget = MigrationBudget.create(self.root, {'matrix': [{'id': str(i)} for i in range(60)]})

    def finish(self, index, *, outcome='recorded', wall_s=1.):
        self.budget.finish(index, outcome=outcome, wall_s=wall_s, evidence_sha256='1'*64)

    def test_restart_keeps_reservation_and_blocks_duplicate_dispatch(self):
        self.budget.reserve('0', {'controller': 123})
        recovered = MigrationBudget(self.root)
        self.assertEqual(recovered.status()['remaining_wall_s'], 4500)
        with self.assertRaisesRegex(RuntimeError, 'Recover'):
            recovered.reserve('1', {'controller': 124})
        self.finish(0, outcome='interrupted', wall_s=None)
        self.assertEqual(recovered.status()['wall_charged_or_reserved_s'], 900)

    def test_crash_after_event_before_head_update_still_charges_launch(self):
        head = (self.root/'head.json').read_bytes()
        self.budget.reserve('0', {'controller': 123})
        (self.root/'head.json').write_bytes(head)
        self.assertEqual(MigrationBudget(self.root).status()['starts_used'], 1)
        self.assertEqual(json.loads((self.root/'head.json').read_bytes())['sequence'], 1)

    def test_truncated_history_and_wrong_manifest_hash_cannot_reset_budget(self):
        self.budget.reserve('0', {'controller': 123})
        self.finish(0)
        last = self.root/'events/0002.json'
        raw = last.read_bytes()
        last.unlink()
        with self.assertRaisesRegex(ValueError, 'Lost'):
            self.budget.status()
        last.write_bytes(raw)
        (self.root/'manifest.json').write_text('{"matrix": []}')
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.budget.status()

    def test_recorded_physical_failure_is_never_rerun_to_success(self):
        self.budget.reserve('0', {'controller': 123})
        self.finish(0)
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.budget.reserve('0', {'controller': 123}, retry_reason='try again')
        with self.assertRaisesRegex(ValueError, 'No matching'):
            self.finish(0)

    def test_one_reviewed_infrastructure_retry_retains_both_attempts(self):
        self.budget.reserve('0', {'controller': 123})
        self.finish(0, outcome='failed')
        with self.assertRaisesRegex(ValueError, 'recovery'):
            self.budget.reserve('0', {'controller': 123})
        index = self.budget.reserve('0', {'controller': 456}, retry_reason='disk fault repaired')
        self.finish(index, outcome='failed')
        self.assertEqual(self.budget.status()['starts_used'], 2)
        with self.assertRaisesRegex(ValueError, 'recovery'):
            self.budget.reserve('0', {'controller': 789}, retry_reason='third try')

    def test_wall_limit_checks_full_reservation_and_retains_overruns(self):
        for case in range(6):
            self.budget.reserve(str(case), {'controller': 123})
            self.finish(case, wall_s=900.)
        self.assertEqual(self.budget.status()['remaining_wall_s'], 0)
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            self.budget.reserve('6', {'controller': 123}, timeout_s=1)

    def test_start_limit_is_cumulative_even_for_fast_failures(self):
        for case in range(48):
            self.budget.reserve(str(case), {'controller': 123})
            self.finish(case, outcome='failed', wall_s=0.)
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            self.budget.reserve('48', {'controller': 123})

    def test_revised_source_retires_old_dispatch_and_inherits_all_cost(self):
        self.budget.reserve('0', {'controller': 123})
        self.finish(0, wall_s=32.)
        state = self.budget.status()
        manifest = dict(matrix=[{'id': '0'}], prior_budget=dict(
            directory=str(self.root), manifest_sha256=state['manifest_sha256'],
            head_sha256=digest((self.root/'head.json').read_bytes()), starts_used=1, wall_s=32.))
        revised = MigrationBudget.create(self.root.parent/'revised', manifest)
        self.assertEqual(revised.status()['starts_used'], 1)
        self.assertEqual(revised.status()['remaining_wall_s'], 5368)
        with self.assertRaisesRegex(ValueError, 'retired'):
            self.budget.reserve('1', {'controller': 123})
        revised.reserve('0', {'controller': 456})
        self.assertEqual(revised.status()['starts_used'], 2)
        self.assertEqual(revised.status()['remaining_wall_s'], 4468)

    def successor(self, name, package):
        state = self.budget.status()
        manifest = dict(matrix=[{'id': str(i)} for i in range(70)], work_package=package,
                        prior_budget=dict(directory=str(self.budget.root),
                                          manifest_sha256=state['manifest_sha256'],
                                          head_sha256=digest((self.budget.root/'head.json').read_bytes()),
                                          starts_used=state['starts_used'],
                                          wall_s=state['wall_charged_or_reserved_s']))
        return MigrationBudget.create(self.root.parent/name, manifest)

    def package(self, **changes):
        return dict(id='native-isolation-1', max_starts=64, wall_s=21600,
                    hypothesis='Thread count changes native low-force repeatability',
                    evidence_sha256=['a'*64], **changes)

    def test_new_package_preserves_lifetime_and_reserves_only_its_own_allowance(self):
        self.budget.reserve('0', {'controller': 123})
        self.finish(0, wall_s=32.)
        old = self.budget
        self.budget = self.successor('package', self.package())
        state = self.budget.status()
        self.assertEqual((state['starts_used'], state['wall_charged_or_reserved_s']), (1, 32.))
        self.assertEqual((state['remaining_starts'], state['remaining_wall_s']), (64, 21600))
        with self.assertRaisesRegex(ValueError, 'retired'):
            old.reserve('1', {'controller': 123})
        self.budget.reserve('0', {'controller': 456})
        self.finish(0, outcome='interrupted', wall_s=None)
        self.assertEqual(self.budget.status()['package_wall_s'], 900.)
        self.budget = self.successor('revision', self.package())
        self.assertEqual(self.budget.status()['remaining_starts'], 63)
        self.assertEqual(self.budget.status()['remaining_wall_s'], 20700)
        for case in range(63):
            self.budget.reserve(str(case), {'controller': 789})
            self.finish(case, wall_s=0.)
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            self.budget.reserve('63', {'controller': 789}, timeout_s=1)

    def test_package_revisions_cannot_raise_drop_or_reuse_allowance(self):
        self.budget = self.successor('package', self.package())
        self.budget.reserve('0', {'controller': 123})
        self.finish(0)
        for name, package in [('changed', {**self.package(), 'wall_s': 20000}), ('dropped', None),
                              ('unevidenced', {**self.package(), 'id': 'second'})]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.successor(name, package)
        self.assertFalse((self.budget.root/'superseded.json').exists())
        second = {**self.package(), 'id': 'storage-isolation-2',
                  'hypothesis': 'Parameter storage changes the numerical trajectory',
                  'evidence_sha256': ['b'*64]}
        self.budget = self.successor('second', second)
        with self.assertRaisesRegex(ValueError, 'restarted'):
            self.successor('reused', self.package())

    def test_package_requires_finite_limits_and_evidence_before_retirement(self):
        for index, change in enumerate(({'max_starts': 65}, {'wall_s': 21601},
                                        {'wall_s': float('inf')}, {'evidence_sha256': []},
                                        {'hypothesis': ''}, {'max_starts': True})):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.successor('invalid'+str(index), {**self.package(), **change})
        self.assertFalse((self.root/'superseded.json').exists())
        self.budget.reserve('0', {'controller': 123})
