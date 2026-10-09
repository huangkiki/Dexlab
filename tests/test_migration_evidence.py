"""Frozen case, model and source identities cannot be substituted during resume."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dexlab.contact_migration import comparison_matrix, read_recording
from dexlab.migration_budget import MigrationBudget, digest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('migration_runner', ROOT/'scripts/run_contact_migration.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class MigrationEvidenceTests(unittest.TestCase):
    def test_new_resource_plan_is_frozen_and_historical_batches_keep_their_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(RUNNER.resource_flags(root, {}), ['--profile', 'experiment'])
            manifest = {'resources': {'profile': 'adaptive', 'cpu_cores': 4,
                                      'peak_receipt_sha256': digest(b'{}')}}
            flags = RUNNER.resource_flags(root, manifest)
            self.assertIn(str(root/'resource-plan.json'), flags)
            self.assertIn(str(root/'prior-resources.json'), flags)
            (root/'prior-resources.json').write_bytes(b'{"changed": true}')
            with self.assertRaisesRegex(ValueError, 'resource measurement'):
                RUNNER.verify_sources(root, manifest, live=False)

    def test_matrix_has_38_launches_and_56_episodes(self):
        protocol = json.loads((ROOT/'demos/contact-benchmark/force-limit-v1.json').read_bytes())
        matrix = comparison_matrix(protocol['cases'])
        self.assertEqual(len(matrix), 38)
        self.assertEqual(len({row['id'] for row in matrix}), 38)
        self.assertEqual(sum(1 if row['case'] else 4 for row in matrix), 56)
        self.assertEqual({row['route'] for row in matrix}, {'native', 'unisim'})

    def test_changed_source_model_or_file_set_refuses_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code = root/'live/src/example.py'
            code.parent.mkdir(parents=True)
            code.write_text('value = 1\n')
            archived = root/'sources/unisim/src/example.py'
            archived.parent.mkdir(parents=True)
            archived.write_bytes(code.read_bytes())
            model = root/'models/cube.xml'
            model.parent.mkdir()
            model.write_text('<mujoco/>')
            manifest = dict(sources={'unisim': {'src/example.py': digest(code.read_bytes())}},
                            roots={'unisim': str(root/'live')}, models={'cube.xml': digest(model.read_bytes())})
            RUNNER.verify_sources(root, manifest, live=False)
            RUNNER.verify_sources(root, manifest, live=True)
            (code.parent/'extra.py').write_text('unexpected = True\n')
            with self.assertRaisesRegex(ValueError, 'file set'):
                RUNNER.verify_sources(root, manifest, live=True)
            code.write_text('value = 2\n')
            with self.assertRaisesRegex(ValueError, 'source hash'):
                RUNNER.verify_sources(root, manifest, live=True)
            model.write_text('<mujoco><changed/></mujoco>')
            with self.assertRaisesRegex(ValueError, 'model bytes'):
                RUNNER.verify_sources(root, manifest, live=False)

    def test_recording_binds_runner_and_case_before_scoring(self):
        trial = {'id': 'dev-open', 'condition': 'open_negative', 'force_limit_N': 10., 'initial_x_m': 0.}
        case = dict(case=trial, dt_s=.0005, route='native')
        source = b'# frozen native acquisition\n'
        protocol = dict(schema=2, case=trial, engine='1.4.3', dt_s=.0005, steps=8000, duration_s=4,
                        mass_kg=.064, cube_size_m=.04, mu=.5, gravity_m_s2=9.81,
                        backend='cpu', precision='64', seed=0, repeats=1,
                        conditions=['open_negative'], plane_cube_geom_timeconst_s=.002,
                        route='frozen_native_reference', source_sha256=digest(source))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'runner.py').write_bytes(source)
            (root/'protocol.json').write_text(json.dumps(protocol))
            record = dict(condition='open_negative', repeat=0, case_id='dev-open')
            (root/'open_negative-0.json').write_text(json.dumps(record))
            self.assertEqual(read_recording(root, case, digest(source)), {'open_negative-0': record})
            matched = {**case, 'matched_batched_info': True}
            with self.assertRaisesRegex(ValueError, 'explicitly batched'):
                read_recording(root, matched, digest(source))
            protocol['batched_info'] = True
            (root/'protocol.json').write_text(json.dumps(protocol))
            record['initial'] = {'options': {'batch_links_info': True, 'batch_dofs_info': False}}
            (root/'open_negative-0.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'effective storage'):
                read_recording(root, matched, digest(source))
            record['initial']['options']['batch_dofs_info'] = True
            (root/'open_negative-0.json').write_text(json.dumps(record))
            self.assertEqual(read_recording(root, matched, digest(source)), {'open_negative-0': record})
            record['case_id'] = 'another-case'
            (root/'open_negative-0.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Mislabeled'):
                read_recording(root, case, digest(source))
            (root/'runner.py').write_bytes(source + b'# altered\n')
            with self.assertRaisesRegex(ValueError, 'source'):
                read_recording(root, case, digest(source))

    def test_live_service_does_not_release_budget_and_changed_source_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'campaign'
            ledger = MigrationBudget.create(root, dict(matrix=[{'id': 'native'}],
                                                       dependencies={}, runtime_stamps={}))
            ledger.reserve('native', {'pid': 123})
            folder = root/'attempts/0000'
            folder.mkdir()
            (folder/'resources.json').write_text(json.dumps(dict(state='completed', wall_s=12.5,
                                                                  service='test-unit')))
            attempt = ledger.status()['attempts'][0]
            with patch.object(RUNNER.subprocess, 'run', return_value=SimpleNamespace(stdout='active\n')):
                with self.assertRaisesRegex(RuntimeError, 'still active'):
                    RUNNER.seal_attempt(root, ledger, attempt)
            self.assertIsNone(ledger.status()['attempts'][0]['terminal'])
            with patch.object(RUNNER.subprocess, 'run', return_value=SimpleNamespace(stdout='inactive\n')):
                with patch.object(RUNNER, 'verify_sources', side_effect=ValueError('changed source')):
                    RUNNER.seal_attempt(root, ledger, attempt)
            terminal = ledger.status()['attempts'][0]['terminal']
            self.assertEqual(terminal['outcome'], 'failed')
            self.assertEqual(terminal['wall_s'], 12.5)
            self.assertEqual(json.loads((folder/'evidence.json').read_bytes())['admission_error'], 'changed source')
