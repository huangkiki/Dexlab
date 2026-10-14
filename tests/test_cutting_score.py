"""Record rejection checks use a tiny actual run, never canned success scores."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

try:
    from dexlab.cutting import CutConfig
    from dexlab.tofu_cut import run
except ModuleNotFoundError as error:
    if error.name not in ('numba', 'scipy'):
        raise
    raise unittest.SkipTest('Install dexlab[cutting] to run cutting record checks') from error
from dexlab.cutting_score import score_run


class CuttingRecordTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name) / 'record'
        with contextlib.redirect_stdout(io.StringIO()):
            self.result = run(self.folder, CutConfig(size=(.015, .015, .015)), duration=.001)

    def test_short_probe_is_serializable_but_cannot_pass_task(self):
        self.assertFalse(self.result['passed'])
        self.assertFalse(self.result['checks']['complete_duration'])
        self.assertEqual(json.loads((self.folder / 'score.json').read_text()), self.result)

    def test_modified_artifact_is_rejected(self):
        with (self.folder / 'states.npz').open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            score_run(self.folder)

    def test_missing_digest_and_changed_threshold_are_rejected(self):
        path = self.folder / 'manifest.json'
        original = json.loads(path.read_text())
        for mutation in ('digest', 'threshold', 'status'):
            with self.subTest(mutation=mutation):
                data = json.loads(json.dumps(original))
                if mutation == 'digest':
                    data['artifacts'].pop('trace.npz')
                elif mutation == 'threshold':
                    data['acceptance']['momentum_error_ns'] = 1
                else:
                    data['status'] = 'failed'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    score_run(self.folder)

    def test_missing_observation_rejected_even_with_new_digest(self):
        import numpy as np
        path = self.folder / 'trace.npz'
        with np.load(path) as archive:
            data = {key: archive[key] for key in archive.files if key != 'material_reaction_n'}
        np.savez_compressed(path, **data)
        manifest_path = self.folder / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['artifacts']['trace.npz'] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'observation is missing'):
            score_run(self.folder)
