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
from dexlab.cutting_score import score_run, scoring_topology


class ScoringTopologyTests(unittest.TestCase):
    def test_record_requires_observed_guided_orientation(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'scoring'
            with contextlib.redirect_stdout(io.StringIO()):
                result = run(folder, CutConfig(size=(.015, .015, .015)),
                             duration=.001, task='tofu-scoring')
            self.assertFalse(result['passed'])
            self.assertIsNone(result['relative_motion_m'])
            self.assertNotIn('motion_protocol', result)
            self.assertEqual(result['piece_displacements_m'], [])
            path = folder / 'trace.npz'
            with np.load(path) as archive:
                trace = {key: archive[key] for key in archive.files}
            trace['blade_yaw_rad'][:] = np.pi / 2  # The first stroke must face x.
            np.savez_compressed(path, **trace)
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            self.assertIsNone(manifest['probe_time_s'])
            manifest['artifacts']['trace.npz'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'orientation'):
                score_run(folder)

    def test_partial_cross_passes_but_cut_base_is_rejected(self):
        import numpy as np
        from dexlab.cutting import CuttingSimulation
        sim = CuttingSimulation(CutConfig(size=(.03, .03, .03), grid_spacing=.005))
        top = sim.reference[:, 2] > .024
        first = np.where(top, np.where(sim.reference[:, 0] < 0, 1, 2), 0)
        both = first + np.where(top, 3*np.where(sim.reference[:, 1] < 0, 1, 2), 0)
        states = dict(reference=sim.reference, nodes=sim.nodes, weights=sim.weights,
                      time=np.array([0., 1.2, 2., 3.2, 4., 4.2]),
                      sides=np.stack((np.zeros_like(first), first, first, both, both, both)))
        trace = dict(cut_index=np.array([0, 1]), blade_position_m=np.array([[0., 0., .044], [0., 0., .044]]))
        config = dict(size=(.03, .03, .03), blade_half_size=(.00025, .02, .02))
        self.assertTrue(all(scoring_topology(states, trace, config)[0].values()))
        # Keep two visible top cuts but disconnect the base: this cannot pass.
        states['sides'][-1] = np.where(sim.reference[:, 0] < 0, 1, 2) + 3*np.where(sim.reference[:, 1] < 0, 1, 2)
        checks = scoring_topology(states, trace, config)[0]
        self.assertTrue(checks['two_opposing_partial_cuts'])
        self.assertFalse(checks['uncut_connected_base'])
        self.assertFalse(checks['one_component_at_scoring_events'])


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
    def test_material_kick_is_not_an_allowed_external_input_for_knife_push(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'knife-push'
            config = CutConfig(size=(.09, .03, .03), dt=.00025)
            with contextlib.redirect_stdout(io.StringIO()):
                original = run(folder, config, duration=.001, task='tofu-sequential')
            self.assertTrue(original['checks']['external_impulse_matches'])
            path = folder / 'trace.npz'
            with np.load(path) as data:
                trace = {key: data[key] for key in data.files}
            trace['external_impulse_ns'][0, 0] -= .001
            np.savez_compressed(path, **trace)
            manifest_path = folder / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['artifacts']['trace.npz'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            altered = score_run(folder)
            self.assertFalse(altered['checks']['external_impulse_matches'])
            self.assertFalse(altered['checks']['momentum_balance'])

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
            self.assertEqual(manifest['motion_protocol'], 'cut-push')
            self.assertIsNone(manifest['probe_time_s'])
            self.assertEqual(manifest['motion_start_time_s'], 3.3)
            self.assertFalse(result['checks']['knife_supplies_push_impulse'])
            manifest['probe_time_s'] = 6.2
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'probe protocol'):
                score_run(folder)
