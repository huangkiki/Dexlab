"""Substep storage and action integration without starting a native simulator."""

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.libero_execute import execute_actions, run
from dexlab.libero_substeps import SubstepArchive, read_chunk, write_chunk
from dexlab.libero_workflow import file_hash
import test_libero_execute as action_fixtures
import test_libero_execute_failure as run_fixtures


class LiberoSubstepsTests(unittest.TestCase):
    def test_packed_roundtrip_preserves_numeric_bits_layout_and_ownership(self):
        rows = [{"bits": np.array([0x7ff8000000000042, 0x8000000000000000,
                                    0xfff0000000000000], dtype=np.uint64).view(np.float64),
                 "integers": np.array([2**63 + 7, 2**64 - 1], dtype=np.uint64),
                 "big_endian": np.array([1.5, -0.0], dtype='>f8'),
                 "strided": np.arange(24, dtype=np.int16).reshape(4, 6)[:, ::2],
                 "scalar": np.asarray(-0.0, dtype=np.float32),
                 "empty": np.empty((2, 0, 3), dtype=np.int32),
                 "bool": np.array([True, False])}]
        with tempfile.TemporaryDirectory() as root:
            first, second = Path(root) / 'first.npz', Path(root) / 'second.npz'
            write_chunk(first, rows)
            write_chunk(second, rows)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with np.load(first, allow_pickle=False) as archive:
                self.assertEqual(len(archive.files), 2)
            restored = read_chunk(first)[0]
            for key, original in rows[0].items():
                with self.subTest(key=key):
                    self.assertEqual(restored[key].dtype.str, original.dtype.str)
                    self.assertEqual(restored[key].shape, original.shape)
                    self.assertEqual(restored[key].tobytes(), original.tobytes())
                    self.assertTrue(restored[key].flags.writeable)
                    self.assertTrue(restored[key].flags.owndata)

    def test_legacy_chunk_is_readable_without_rewriting(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'legacy.npz'
            metadata = {"schema_version": 1, "rows": [{"value": {"__ndarray__": "array_0"}}]}
            np.savez_compressed(path, metadata=np.frombuffer(json.dumps(metadata).encode(), np.uint8),
                                array_0=np.array([1, 2**60 + 1], dtype=np.int64))
            original = path.read_bytes()
            np.testing.assert_array_equal(read_chunk(path)[0]['value'], np.array([1, 2**60 + 1]))
            self.assertEqual(path.read_bytes(), original)

    def test_corrupted_packed_metadata_and_extents_are_rejected(self):
        base = {"schema_version": 2, "rows": [{"__ndarray__": 0}],
                "arrays": [{"dtype": '<i8', "shape": [1]}]}
        modes = ('alias', 'missing', 'extra', 'boolean_ref', 'extra_ref_key', 'negative_shape',
                 'fractional_shape', 'boolean_shape', 'huge_shape', 'object_dtype', 'invalid_dtype',
                 'missing_descriptor', 'short_payload', 'trailing_payload', 'payload_dtype',
                 'payload_shape', 'extra_member')
        with tempfile.TemporaryDirectory() as root:
            for mode in modes:
                metadata = deepcopy(base)
                arrays = {'payload': np.zeros(8, dtype=np.uint8)}
                if mode == 'alias': metadata['rows'].append({'__ndarray__': 0})
                elif mode == 'missing': metadata['rows'][0]['__ndarray__'] = 1
                elif mode == 'extra': metadata['rows'] = []
                elif mode == 'boolean_ref': metadata['rows'][0]['__ndarray__'] = False
                elif mode == 'extra_ref_key': metadata['rows'][0]['extra'] = 1
                elif mode == 'negative_shape': metadata['arrays'][0]['shape'] = [-1]
                elif mode == 'fractional_shape': metadata['arrays'][0]['shape'] = [1.0]
                elif mode == 'boolean_shape': metadata['arrays'][0]['shape'] = [True]
                elif mode == 'huge_shape': metadata['arrays'][0]['shape'] = [2**64, 2**64]
                elif mode == 'object_dtype': metadata['arrays'][0]['dtype'] = '|O'
                elif mode == 'invalid_dtype': metadata['arrays'][0]['dtype'] = 'not-a-dtype'
                elif mode == 'missing_descriptor': del metadata['arrays'][0]['shape']
                elif mode == 'short_payload': arrays['payload'] = np.zeros(7, dtype=np.uint8)
                elif mode == 'trailing_payload': arrays['payload'] = np.zeros(9, dtype=np.uint8)
                elif mode == 'payload_dtype': arrays['payload'] = np.zeros(8, dtype=np.int8)
                elif mode == 'payload_shape': arrays['payload'] = np.zeros((2, 4), dtype=np.uint8)
                elif mode == 'extra_member': arrays['unused'] = np.zeros(1)
                arrays['metadata'] = np.frombuffer(json.dumps(metadata).encode(), np.uint8)
                path = Path(root) / (mode + '.npz')
                np.savez_compressed(path, **arrays)
                with self.subTest(mode=mode), self.assertRaises(ValueError):
                    read_chunk(path)

    def test_roundtrip_preserves_ragged_arrays_dtypes_and_invalid_evidence(self):
        rows = [{"sequence": 0, "force_time": float('nan'),
                 "qpos": np.array([1., float('inf')]), "empty_jacobian": np.empty((0, 3)),
                 "contacts": [{"ids": np.array([1, 2], dtype=np.int32)}]},
                {"sequence": 1, "contacts": [], "empty_ids": np.empty(0, dtype=np.int64)}]
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'chunk.npz'
            write_chunk(path, rows)
            restored = read_chunk(path)
            self.assertTrue(np.isnan(restored[0]['force_time']))
            np.testing.assert_array_equal(restored[0]['qpos'], rows[0]['qpos'])
            self.assertEqual(restored[0]['empty_jacobian'].shape, (0, 3))
            self.assertEqual(restored[0]['contacts'][0]['ids'].dtype, np.int32)
            self.assertEqual(restored[1]['empty_ids'].dtype, np.int64)
            with self.assertRaises(FileExistsError):
                write_chunk(path, [])

    def test_alias_missing_extra_and_object_arrays_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            with self.assertRaisesRegex(ValueError, 'pickle-free'):
                write_chunk(root / 'object.npz', [np.array([object()])])
            self.assertFalse((root / 'object.npz').exists())
            for mode in ('alias', 'missing', 'extra'):
                rows = [{'__ndarray__': 'a'}]
                arrays = {'a': np.ones(2)}
                if mode == 'alias':
                    rows.append({'__ndarray__': 'a'})
                elif mode == 'missing':
                    arrays = {}
                else:
                    arrays['unused'] = np.zeros(1)
                arrays['metadata'] = np.frombuffer(json.dumps({'schema_version': 1, 'rows': rows}).encode(), np.uint8)
                path = root / (mode + '.npz'); np.savez_compressed(path, **arrays)
                with self.subTest(mode=mode), self.assertRaises(ValueError):
                    read_chunk(path)

    def test_action_and_substep_sequence_cannot_skip_or_alias(self):
        with tempfile.TemporaryDirectory() as root:
            archive = SubstepArchive(Path(root) / 'steps')
            with self.assertRaises(ValueError):
                archive.append({'sequence': 0})
            with self.assertRaises(ValueError):
                archive.start_action(1)
            archive.start_action(0)
            archive.append({'sequence': 0})
            with self.assertRaises(ValueError):
                archive.append({'sequence': 0})
            with self.assertRaises(ValueError):
                archive.start_action(1)
            archive.flush()
            self.assertFalse(archive.rows)
            self.assertEqual(read_chunk(archive.directory / archive.chunks[0]['name'])[0]['action_index'], 0)

    def test_failed_action_prefix_is_saved_before_original_error_propagates(self):
        env = action_fixtures.NativeFixture()
        with tempfile.TemporaryDirectory() as root:
            archive = SubstepArchive(Path(root) / 'steps')
            original = env.step
            def step(action):
                archive.append({'sequence': archive.substeps, 'status': 'recorded', 'qpos': np.ones(3)})
                if env.count == 1:
                    raise RuntimeError('second action failed')
                return original(action)
            env.step = step
            rows = {}
            with self.assertRaisesRegex(RuntimeError, 'second action failed'):
                execute_actions(env, np.ones((3, 7)), action_fixtures.goal_fixtures.DEFINITION,
                                recording=True, rows=rows, events=[], markers=[], substeps=archive)
            self.assertEqual(len(rows['actions']), 1)
            self.assertEqual(len(archive.chunks), 2)
            self.assertEqual(archive.substeps, 2)
            self.assertFalse(archive.rows)
            self.assertEqual(read_chunk(archive.directory / 'action-000001.npz')[0]['action_index'], 1)

    def test_archive_write_failure_does_not_replace_native_error(self):
        env = action_fixtures.NativeFixture()
        env.step = lambda action: (_ for _ in ()).throw(RuntimeError('native failed'))
        with tempfile.TemporaryDirectory() as root:
            archive = SubstepArchive(Path(root) / 'steps')
            with patch.object(archive, 'flush', side_effect=OSError('disk failed')):
                with self.assertRaisesRegex(RuntimeError, 'native failed') as caught:
                    execute_actions(env, np.ones((3, 7)), action_fixtures.goal_fixtures.DEFINITION,
                                    recording=True, rows={}, events=[], markers=[], substeps=archive)
            self.assertIsInstance(caught.exception.__cause__, OSError)

    def test_run_binds_recursive_archive_hashes_and_complete_action_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); env = action_fixtures.NativeFixture()
            payload, stack = run_fixtures.LiberoExecuteFailureTests().prepare(root, env)
            payload['substep_recording'] = True
            @contextmanager
            def fake_capture(sim, sink):
                original = env.step
                sequence = 0
                def step(action):
                    nonlocal sequence
                    for _ in range(2):
                        sink({'sequence': sequence, 'status': 'recorded', 'data': np.ones(2)})
                        sequence += 1
                    return original(action)
                env.step = step
                try:
                    yield {'schema_version': 1, 'fixture': True}
                finally:
                    env.step = original
            with stack, patch('dexlab.libero_execute.record_substeps', fake_capture):
                result = run(payload, root / 'output')
            self.assertEqual(result['status'], 'completed')
            self.assertTrue(result['substep_recording'])
            index = json.loads((root / 'output/substeps.json').read_text())
            self.assertEqual(index['substeps'], 6)
            self.assertEqual([chunk['substeps'] for chunk in index['chunks']], [2, 2, 2])
            self.assertEqual(sum(name.startswith('substeps/') for name in result['files']), 3)
            for name, digest in result['files'].items():
                self.assertEqual(file_hash(root / 'output' / name), digest)
            self.assertTrue(env.closed)

    def test_empty_substeps_cannot_be_a_completed_instrumented_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); env = action_fixtures.NativeFixture()
            payload, stack = run_fixtures.LiberoExecuteFailureTests().prepare(root, env)
            payload['substep_recording'] = True
            @contextmanager
            def empty_capture(sim, sink):
                yield {'fixture': True}
            with stack, patch('dexlab.libero_execute.record_substeps', empty_capture):
                with self.assertRaisesRegex(ValueError, 'Missing substep'):
                    run(payload, root / 'output')
            result = json.loads((root / 'output/run.json').read_text())
            self.assertEqual(result['status'], 'failed')
            self.assertIsNone(result['native_success_final'])
            self.assertTrue(env.closed)


if __name__ == '__main__':
    unittest.main()
