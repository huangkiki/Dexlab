"""Attempt isolation at the shared native entry and the public UniLab lifecycle."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wuji_stem_grasp as grasp


def snapshot(directory):
    return {str(p.relative_to(directory)): p.read_bytes()
            for p in directory.rglob('*') if p.is_file()}


class AppleOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_default_parser_selects_distinct_paths_without_writing(self):
        for backend in ('mujoco', 'superdex'):
            with self.subTest(backend=backend):
                first = grasp.parse_args(['--backend', backend])
                second = grasp.parse_args(['--backend', backend])
                self.assertNotEqual(first.output, second.output)
                self.assertFalse(first.output.exists())
                self.assertFalse(second.output.exists())

    def test_existing_record_rejected_before_native_init_without_any_changes(self):
        for backend in ('mujoco', 'superdex'):
            with self.subTest(backend=backend):
                dest = self.root / backend
                dest.mkdir()
                for name in ('source-sha256.json', 'summary.json', 'runtime-timing.json',
                             'qualification-observation.json', 'trajectory.npz'):
                    (dest / name).write_bytes(b'old success or failure evidence\n')
                before = snapshot(dest)
                args = grasp.parse_args(['--backend', backend, '--output', str(dest)])
                with patch.object(grasp.physics, 'uses_double_precision', return_value=True), \
                     patch.object(grasp.physics, 'initialize', side_effect=RuntimeError('native sentinel')) as init:
                    with self.assertRaises(FileExistsError):
                        grasp.trial(args)
                init.assert_not_called()
                self.assertEqual(snapshot(dest), before)

    def test_startup_failure_kept_and_cannot_be_reused(self):
        args = grasp.parse_args(['--output', str(self.root)])  # an empty directory is valid
        with patch.object(grasp.physics, 'uses_double_precision', return_value=True), \
             patch.object(grasp.physics, 'initialize', side_effect=RuntimeError('native sentinel')) as init:
            with self.assertRaisesRegex(RuntimeError, 'native sentinel'):
                grasp.trial(args)
            self.assertTrue((self.root / 'source-sha256.json').is_file())
            self.assertFalse((self.root / 'summary.json').exists())
            before = snapshot(self.root)
            with self.assertRaises(FileExistsError):
                grasp.trial(args)
        self.assertEqual(init.call_count, 1)
        self.assertEqual(snapshot(self.root), before)

    def test_concurrent_claims_have_exactly_one_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        barrier = Barrier(2)
        def claim():
            args = grasp.parse_args(['--output', str(self.root)])
            barrier.wait(timeout=5)
            try:
                coroutine = grasp.episode(args)
            except FileExistsError:
                return False
            coroutine.close()  # reservation only, no native initialization
            return True
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(set(snapshot(self.root)), {'attempt.json'})
        self.assertTrue(json.loads((self.root / 'attempt.json').read_text())['attempt_id'])

    def test_symlink_and_unrelated_files_are_not_consumed(self):
        link = self.root / 'alias'
        dest = self.root / 'actual'
        dest.mkdir()
        link.symlink_to(dest, target_is_directory=True)
        for output in (link, self.root):
            before = snapshot(self.root)
            with self.assertRaises(FileExistsError):
                grasp.episode(grasp.parse_args(['--output', str(output)]))
            self.assertEqual(snapshot(self.root), before)

    def test_default_reset_isolates_success_and_interrupted_evidence(self):
        import numpy as np
        from dexlab.episode import GraspFrame
        from dexlab.tasks.apple_stem import AppleStemCfg, AppleStemEnv
        def inner(args):
            (args.output / 'source-sha256.json').write_text('new source')
            yield GraspFrame(0, ('a',), np.zeros(1), np.r_[np.zeros(6), 1], np.zeros(1))
            (args.output / 'summary.json').write_text('{"passed": true}')
            yield GraspFrame(0.002, ('a',), np.zeros(1), np.r_[np.zeros(6), 1],
                             np.zeros(1), {'passed': True})
        for backend in ('mujoco', 'superdex'):
            with self.subTest(backend=backend), patch.object(grasp, '_episode', inner), \
                 patch.object(grasp, 'OUT', self.root / backend / 'src'):
                env = AppleStemEnv(AppleStemCfg(), backend_type=backend)
                try:
                    env.reset()
                    first = env.output_directory
                    env.step([[0]])  # completed success
                    before = snapshot(first)
                    env.reset()
                    second = env.output_directory
                    interrupted = snapshot(second)
                    env.reset()  # abandon the second episode before success
                    self.assertEqual(len({first, second, env.output_directory}), 3)
                    self.assertEqual(snapshot(first), before)
                    self.assertEqual(snapshot(second), interrupted)
                    self.assertFalse((second / 'summary.json').exists())
                finally:
                    env.close()

    def test_explicit_reset_rejected_and_scene_lock_released(self):
        import numpy as np
        from dexlab.episode import GraspFrame
        from dexlab.tasks.apple_stem import AppleStemCfg, AppleStemEnv
        def inner(args):
            yield GraspFrame(0, ('a',), np.zeros(1), np.r_[np.zeros(6), 1], np.zeros(1))
        with patch.object(grasp, '_episode', inner):
            env = AppleStemEnv(AppleStemCfg(output=str(self.root / 'first')))
            other = AppleStemEnv(AppleStemCfg(output=str(self.root / 'second')))
            try:
                env.reset()
                before = snapshot(env.output_directory)
                with self.assertRaises(FileExistsError):
                    env.reset()
                self.assertIsNone(env.output_directory)
                self.assertIsNone(env.state)
                self.assertEqual(snapshot(self.root / 'first'), before)
                other.reset()  # failed reservation did not leak the scene lock
            finally:
                env.close()
                other.close()

    def test_cli_rejected_directory_cannot_be_written_by_finally(self):
        from dexlab.tasks.apple_stem import main
        for name in ('summary.json', 'runtime-timing.json', 'qualification-observation.json'):
            (self.root / name).write_bytes(b'old record\n')
        before = snapshot(self.root)
        args = grasp.parse_args(['--output', str(self.root)])
        with patch.object(grasp, 'parse_args', return_value=args), \
             patch.dict('os.environ', {'DEXLAB_MUJOCO_PROFILE': 'historical-3.11.0'}), \
             patch.object(grasp.physics, 'initialize') as init:
            with self.assertRaises(FileExistsError):
                main()
        init.assert_not_called()
        self.assertEqual(snapshot(self.root), before)

    def test_cli_startup_failure_only_records_its_own_timing(self):
        from dexlab.tasks.apple_stem import main
        args = grasp.parse_args(['--output', str(self.root)])
        with patch.object(grasp, 'parse_args', return_value=args), \
             patch.dict('os.environ', {'DEXLAB_MUJOCO_PROFILE': 'historical-3.11.0'}), \
             patch.object(grasp.physics, 'uses_double_precision', return_value=True), \
             patch.object(grasp.physics, 'initialize', side_effect=RuntimeError('native sentinel')):
            with self.assertRaisesRegex(RuntimeError, 'native sentinel'):
                main()
        timing = json.loads((self.root / 'runtime-timing.json').read_text())
        self.assertIsNone(timing['preparation_seconds'])
        self.assertFalse((self.root / 'summary.json').exists())
