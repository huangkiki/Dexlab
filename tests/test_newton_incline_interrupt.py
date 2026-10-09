"""An interrupted recorder must preserve progress without claiming completion."""

from contextlib import nullcontext
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dexlab import newton_incline as recorder
from dexlab.newton_incline_score import score_campaign


class NewtonInterruptionTests(unittest.TestCase):
    def test_interrupt_preserves_partial_observations_and_rejects_acceptance(self):
        fixtures = Path(__file__).parent / 'fixtures'
        protocol = json.loads((fixtures / 'newton-incline-protocol.json').read_text())
        admission = json.loads((fixtures / 'newton-incline-admission.json').read_text())
        identity = {'version': 'test', 'record_verified': True}
        proof = dict(source_commit=protocol['source_commit'], packages={
            name: {'identity': identity} for name in ('newton', 'warp-lang')})
        calls = []

        def step(index, dt):
            calls.append(index)
            if index == 1:
                raise KeyboardInterrupt('injected interruption')
            state = list(admission['initial_state'])
            state[0] = dt
            return dict(state=state, net_force=[0, 0, 0], native_step_wall_s=0.)

        scene = SimpleNamespace(admission=admission, step=step)
        warp = SimpleNamespace(config=SimpleNamespace(), init=lambda: None,
                               ScopedDevice=lambda device: nullcontext())
        with TemporaryDirectory() as directory:
            root = Path(directory)
            admission_path = root / 'expected.json'
            recorder.write_json(admission_path, admission)
            protocol['recorder_sha256'] = recorder.sha256(Path(recorder.__file__))
            protocol['admission_sha256'] = {
                case['id']: recorder.sha256(admission_path) for case in protocol['cases']}
            recorder.write_json(root / 'manifest.json', protocol)
            recorder.write_json(root / 'proof.json', proof)
            with (patch.dict('sys.modules', {'warp': warp}),
                  patch.object(recorder, 'package_identity', return_value=dict(identity)),
                  patch.object(recorder, 'NewtonIncline', return_value=scene),
                  patch('dexlab.newton_incline_score.validate_admission')):
                with self.assertRaises(KeyboardInterrupt):
                    recorder.run(root / 'manifest.json', root / 'proof.json', root / 'output')
            campaign = json.loads((root / 'output/campaign.json').read_text())
            self.assertEqual(campaign['state'], 'interrupted')
            self.assertEqual(len(campaign['cases']), 1)
            case = campaign['cases'][0]
            self.assertEqual(case['completed_steps'], 1)
            self.assertEqual(case['attempted_steps'], 2)
            self.assertIn('KeyboardInterrupt', case['error'])
            with gzip.open(root / 'output' / protocol['cases'][0]['id'] / 'steps.jsonl.gz', 'rt') as stream:
                self.assertEqual(len(stream.readlines()), 1)
            with self.assertRaisesRegex(ValueError, 'completed'):
                score_campaign(root / 'output')


if __name__ == '__main__':
    unittest.main()
