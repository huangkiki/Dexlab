"""Recovery attribution cannot erase failed attempts or change completed cases."""

from copy import deepcopy
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dexlab.incline_score import file_hash
from dexlab.newton_incline_recovery import validate_recovery


class NewtonRecoveryTests(unittest.TestCase):
    def fixture(self, root):
        protocol = json.loads((Path(__file__).parent / 'fixtures' /
                               'newton-incline-protocol.json').read_text())
        original = root / 'interrupted-attempt'
        original.mkdir()
        previous = dict(state='interrupted', admission_only=False, cases=[], packages={'fixture': True})
        protocol['admission_sha256'] = {}
        for case in protocol['cases']:
            directory = original / case['id']
            directory.mkdir()
            (directory / 'admission.json').write_text('{}')
            with gzip.open(directory / 'steps.jsonl.gz', 'wt') as stream:
                for step in range(2):
                    stream.write(json.dumps(dict(state=[step], net_force=[0, 0, 0])) + '\n')
            hashes = {p.name: file_hash(p) for p in directory.iterdir()}
            protocol['admission_sha256'][case['id']] = hashes['admission.json']
            negative = case.get('negative_no_floor', False)
            item = dict(case=case, completed_steps=2 if negative else round(2 / case['timestep']),
                        error='KeyboardInterrupt: fixture' if negative else None, hashes=hashes)
            (directory / 'metadata.json').write_text(json.dumps(item))
            previous['cases'].append(item)
        for name, key in [('manifest.json', 'protocol_sha256'), ('recorder.py', 'recorder_sha256'),
                          ('official-proof.json', 'proof_sha256')]:
            (original / name).write_text('fixture')
            previous[key] = file_hash(original / name)
        (original / 'campaign.json').write_text(json.dumps(previous))
        campaign = deepcopy(previous)
        campaign['state'] = 'completed'
        campaign['cases'][-1].update(completed_steps=2000, error=None)
        (root / 'continuation.py').write_text('fixture')
        name = protocol['cases'][-1]['id']
        (root / name).mkdir()
        with gzip.open(root / name / 'steps.jsonl.gz', 'wt') as stream:
            for step in range(3):
                stream.write(json.dumps(dict(state=[step], net_force=[0, 0, 0])) + '\n')
        campaign['continuation'] = dict(original_campaign_sha256=file_hash(original / 'campaign.json'),
                                        runner_sha256=file_hash(root / 'continuation.py'),
                                        replaced_case=name, original_completed_steps=2)
        return protocol, campaign

    def test_preserved_attempt_and_overlap_are_verified(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, campaign = self.fixture(root)
            report = validate_recovery(root, campaign, protocol)
            self.assertEqual(report['identical_prefix_steps'], 2)
            self.assertEqual(report['reused_positive_cases'], 9)

    def test_recovery_cannot_replace_positive_or_hide_original_corruption(self):
        for change in ('positive', 'original-data', 'runner'):
            with self.subTest(change=change), TemporaryDirectory() as directory:
                root = Path(directory)
                protocol, campaign = self.fixture(root)
                if change == 'positive':
                    campaign['cases'][0]['completed_steps'] -= 1
                elif change == 'runner':
                    (root / 'continuation.py').write_text('changed')
                else:
                    (root / 'interrupted-attempt' / protocol['cases'][0]['id'] /
                     'admission.json').write_text('changed')
                with self.assertRaises(ValueError):
                    validate_recovery(root, campaign, protocol)

    def test_different_negative_prefix_is_not_silently_combined(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, campaign = self.fixture(root)
            with gzip.open(root / protocol['cases'][-1]['id'] / 'steps.jsonl.gz', 'wt') as stream:
                for step in range(3):
                    stream.write(json.dumps(dict(state=[step + 1], net_force=[0, 0, 0])) + '\n')
            with self.assertRaisesRegex(ValueError, 'prefix differs'):
                validate_recovery(root, campaign, protocol)
