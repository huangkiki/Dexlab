"""Evidence omissions and duplicate configurations must not improve coverage."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.task_coverage import (
    ROOT, RELIABILITY_CHECKS, cloth_counts, evidence, load_inventory,
    reliable_tasks, render, update, incline_counts,
)


class TaskCoverageTests(unittest.TestCase):
    def test_incline_failures_and_negative_cannot_be_omitted_from_counts(self):
        root = ROOT / 'docs/evidence/drake-incline'
        score = json.loads((root / 'score-v2.json').read_text())
        protocol = json.loads((root / 'protocol-v2.json').read_text())
        self.assertEqual(incline_counts(score, protocol), (6, 9, True))
        for name in ('missing-failure', 'missing-negative', 'duplicate', 'false-pass'):
            invalid = deepcopy(score)
            if name == 'missing-failure':
                invalid['results'].pop(3)
            elif name == 'missing-negative':
                invalid['results'].pop()
            elif name == 'duplicate':
                invalid['results'].append(invalid['results'][0])
            else:
                invalid['results'][3]['passed'] = True
            with self.subTest(name=name), self.assertRaises(ValueError):
                incline_counts(invalid, protocol)

    def test_invalid_positive_and_negative_remain_visible_without_qualification(self):
        root = ROOT / 'docs/evidence/drake-incline'
        bundle = json.loads((root / 'score-v2.json').read_text())
        protocol = json.loads((root / 'protocol-v2.json').read_text())
        bundle['results'][0].update(record_valid=False, passed=False,
                                    failure='native force/state inconsistency', checks={'consistency': False})
        self.assertEqual(incline_counts(bundle, protocol), (5, 9, True))
        bundle['results'][0]['passed'] = True
        with self.assertRaises(ValueError):
            incline_counts(bundle, protocol)
        bundle['results'][0]['passed'] = False
        bundle['results'][-1].update(record_valid=False, failure='corrupt negative')
        self.assertEqual(incline_counts(bundle, protocol), (5, 9, False))

    def test_all_positive_passes_with_invalid_negative_cannot_render_full_pass(self):
        source = ROOT / 'docs/evidence/drake-incline'
        score = json.loads((source / 'score-v2.json').read_text())
        protocol = json.loads((source / 'protocol-v2.json').read_text())
        for result in score['results']:
            if not result['expected_negative']:
                result.update(record_valid=True, passed=True, checks={'fixture_check': True})
            else:
                result.update(record_valid=False, passed=False, checks={'consistency': False},
                              failure='invalid negative fixture')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()

            def save(name, data):
                raw = json.dumps(data).encode()
                (root / name).write_bytes(raw)
                return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

            protocol_ref = save('protocol.json', protocol)
            score['protocol_sha256'] = protocol_ref['sha256']
            score_ref = save('score.json', score)
            cell = dict(state='passed', counts_from='incline', evidence=score_ref,
                        reference='https://github.com/huangkiki/Dexlab/issues/149')
            manifest = dict(schema_version=1, current_protocol='coverage-v1',
                            groups=[dict(id='rigid', en='Rigid', zh='刚体')],
                            tasks=[dict(id='incline', group='rigid', en='Incline', zh='斜面')],
                            cohorts={'fixture': dict(incline_score=score_ref,
                                                    protocol=protocol_ref, profile='fixture')},
                            rows=[dict(engine='Newton Physics', solver='fixture',
                                       runtime_path='fixture', version='fixture',
                                       cohort='fixture', profile='fixture', groups=['rigid'],
                                       cells={'incline': cell})])
            save('docs/task-coverage.json', manifest)
            with self.assertRaisesRegex(ValueError, 'Declared state'):
                load_inventory(root)
            cell['state'] = 'partial'
            save('docs/task-coverage.json', manifest)
            observed = load_inventory(root)
            self.assertIn('Partial 9/9; invalid negative', render(observed, 'en', root))
            self.assertFalse(any(reliable_tasks(observed, root).values()))

    def setUp(self):
        self.manifest = load_inventory()
        self.cohort = self.manifest['cohorts']['cloth-heldout-v1']
        self.bundle = json.loads(evidence(ROOT, self.cohort['cloth_summaries']))

    def test_all_frozen_cloth_cases_are_counted_including_failures(self):
        counts = cloth_counts(self.bundle, self.cohort['expected_cases'])
        self.assertEqual(counts['mujoco', 'drape'], (0, 4))
        self.assertEqual(counts['newton-style3d', 'folded-drop'], (1, 3))
        self.assertEqual(sum(total for _, total in counts.values()), 105)

    def test_missing_duplicate_and_contradictory_cases_fail_closed(self):
        missing = deepcopy(self.bundle)
        missing['records'].pop()
        duplicate = deepcopy(self.bundle)
        duplicate['records'].append(duplicate['records'][0])
        contradictory = deepcopy(self.bundle)
        contradictory['records'][0]['summary']['protocol_checks_passed'] = False
        incomplete = deepcopy(self.bundle)
        incomplete['records'][0]['job']['status'] = 'running'
        for bundle in (missing, duplicate, contradictory, incomplete):
            with self.assertRaises(ValueError):
                cloth_counts(bundle, self.cohort['expected_cases'])

    def test_changed_evidence_and_repository_escape_rejected(self):
        reference = self.cohort['cloth_summaries']
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            evidence(ROOT, {**reference, 'sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'repository file'):
            evidence(ROOT, {'path': '/etc/hosts', 'sha256': '0' * 64})

    def test_history_never_becomes_new_protocol_coverage(self):
        self.assertTrue(all(not tasks for tasks in reliable_tasks(self.manifest, ROOT).values()))
        self.assertIn('not yet qualified', render(self.manifest, 'en'))

    def test_engine_union_does_not_count_another_solver_or_framework_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {'current_protocol': 'coverage-v1', 'rows': []}
            for index, path in enumerate(('native', 'framework')):
                row = dict(engine='MuJoCo', solver='Newton', runtime_path=path,
                           version='fixture-only', cohort='coverage-v1')
                report = {key: row[key] for key in ('engine', 'solver', 'runtime_path', 'version')}
                report.update(protocol_id='coverage-v1', task_type='incline',
                              checks=dict.fromkeys(RELIABILITY_CHECKS, True))
                raw = json.dumps(report).encode()
                name = f'acceptance-{index}.json'
                (root / name).write_bytes(raw)
                row['cells'] = {'incline': {'state': 'passed', 'acceptance': {
                    'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}}}
                manifest['rows'].append(row)
            self.assertEqual(reliable_tasks(manifest, root)['MuJoCo'], {'incline'})
            # A report for another runtime must not qualify this row.
            manifest['rows'][1]['runtime_path'] = 'different'
            with self.assertRaisesRegex(ValueError, 'identity'):
                reliable_tasks(manifest, root)
            manifest['rows'][1]['runtime_path'] = 'framework'
            report['checks']['negative_controls'] = False
            raw = json.dumps(report).encode()
            (root / name).write_bytes(raw)
            manifest['rows'][1]['cells']['incline']['acceptance']['sha256'] = hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex(ValueError, 'every preregistered'):
                reliable_tasks(manifest, root)

    def test_all_four_public_views_are_current(self):
        update(check=True)
