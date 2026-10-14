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


class BananaRecordTests(unittest.TestCase):
    def test_cut_clock_and_deformation_are_required(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'banana'
            config = CutConfig(shape='banana', size=(.12, .06, .03), grid_spacing=.006)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, config, duration=.001, task='banana')
            self.assertFalse(result['passed'])
            self.assertEqual(result['initial_components'], 1)
            manifest_path = folder / 'manifest.json'
            original_manifest = json.loads(manifest_path.read_text())
            for filename, field in [('trace.npz', 'cut_index'), ('states.npz', 'deformation')]:
                with self.subTest(field=field):
                    path = folder / filename
                    original = path.read_bytes()
                    with np.load(path) as archive:
                        data = {key: archive[key] for key in archive.files}
                    if field == 'cut_index':
                        data[field][:] = 2  # A third cut cannot happen in the initial millisecond.
                    else:
                        del data[field]
                    np.savez_compressed(path, **data)
                    manifest = json.loads(json.dumps(original_manifest))
                    manifest['artifacts'][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
                    manifest_path.write_text(json.dumps(manifest))
                    with self.assertRaises(ValueError):
                        score_run(folder)
                    path.write_bytes(original)
                    manifest_path.write_text(json.dumps(original_manifest))


class SequentialTofuRecordTests(unittest.TestCase):
    def test_short_tofu_comparison_is_a_distinct_three_piece_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'two-cuts'
            config = CutConfig(size=(.09, .03, .03), dt=.00025,
                               blade_half_size=(.00025, .025, .02), blade_bevel_height=.005)
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, config, duration=.001, task='tofu-sequential')
            self.assertEqual(result['task'], 'tofu-sequential')
            self.assertFalse(result['passed'])
            self.assertFalse(result['checks']['three_mechanical_components'])
            self.assertNotIn('four_mechanical_components', result['checks'])
            self.assertEqual(len(result['piece_displacements_m']), 3)
            path = folder / 'manifest.json'
            manifest = json.loads(path.read_text())
            manifest['probe_time_s'] = 6.2
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'probe protocol'):
                score_run(folder)
