"""Task preparation must preserve every admitted demo and its frozen identity."""

import copy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.libero_demo import load_demo, prepare_task
from dexlab.libero_workflow import UPSTREAM, file_hash
from dexlab.migration_budget import json_bytes
import test_libero_dataset as fixtures
from test_libero_inputs import BDDL


class LiberoDemoTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.LiberoDatasetTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        self.task = fixture.task
        self.task['bddl_path'] = 'libero/libero/bddl_files/task.bddl'
        bddl = self.root / self.task['bddl_path']
        bddl.parent.mkdir(parents=True)
        bddl.write_bytes(BDDL)
        self.receipt = fixture.admit()
        (self.root / 'admission.json').write_bytes(json_bytes(self.receipt))
        self.dataset = self.root / 'datasets' / self.task['dataset']['path']
        self.dataset.parent.mkdir(parents=True)
        shutil.copy2(fixture.path, self.dataset)
        self.inputs = {'upstream_commit': UPSTREAM, 'tasks': [self.task]}
        self.output = self.root / 'prepared'

    def prepare(self):
        with patch('dexlab.libero_demo.frozen_inputs', return_value=(self.inputs, 'f' * 64)):
            return prepare_task(self.root, self.root / 'frozen', self.task['task_id'],
                                self.root / 'datasets', self.root / 'admission.json', self.output)

    def load(self, demo='demo_0'):
        return load_demo(self.output, file_hash(self.output / 'manifest.json'), demo)

    def update_file_hash(self, name):
        manifest = json.loads((self.output / 'manifest.json').read_text())
        manifest['files'][name] = file_hash(self.output / name)
        (self.output / 'manifest.json').write_bytes(json_bytes(manifest))

    def test_complete_denominator_and_all_actions_survive_roundtrip(self):
        manifest = self.prepare()
        self.assertEqual(manifest['demonstrations'], self.receipt['demonstrations'])
        self.assertEqual(manifest['demonstration_count'], 5)
        self.assertEqual(manifest['action_count'], 15)
        for declaration in self.receipt['demonstrations']:
            data = self.load(declaration['demo_id'])
            self.assertEqual(data['demonstration'], declaration)
            self.assertEqual(data['task']['definition']['goal'], self.task['definition']['goal'])
            self.assertEqual(data['initial'].shape, (declaration['state_width'],))
            np.testing.assert_array_equal(data['actions'], np.ones((3, 7), dtype=np.float32))
            self.assertFalse({'rewards', 'dones', 'dataset_states'} & data.keys())
        self.assertEqual(self.load()['metadata']['bddl_file'], 'chiliocosm/bddl_files/old_task_name.bddl')
        self.assertEqual(self.load()['bddl'], BDDL)

    def test_partial_or_changed_file_never_publishes_completion(self):
        self.dataset.write_bytes(self.dataset.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, 'byte count'):
            self.prepare()
        self.assertFalse((self.output / 'manifest.json').exists())
        self.assertEqual(json.loads((self.output / 'failure.json').read_text())['phase'], 'file-identity')
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_admitted_dataset_can_use_existing_external_cache_symlink(self):
        cache = self.root / 'existing-cache.hdf5'
        self.dataset.rename(cache)
        self.dataset.symlink_to(cache)
        self.prepare()
        self.assertEqual(self.load()['manifest']['demonstration_count'], 5)

    def test_unknown_task_or_demo_cannot_be_silently_substituted(self):
        self.inputs['tasks'] = []
        with self.assertRaisesRegex(ValueError, 'absent'):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.inputs['tasks'] = [self.task]
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'denominator'):
            self.load('demo_1')

    def test_snapshot_requires_external_hash_and_all_declared_files(self):
        self.prepare()
        pinned = file_hash(self.output / 'manifest.json')
        manifest = json.loads((self.output / 'manifest.json').read_text())
        del manifest['files']['demo_23.xml']
        (self.output / 'manifest.json').write_bytes(json_bytes(manifest))
        with self.assertRaisesRegex(ValueError, 'frozen case'):
            load_demo(self.output, pinned, 'demo_0')
        with self.assertRaisesRegex(ValueError, 'omits'):
            self.load()

    def test_rehashed_truncated_or_nonfinite_actions_are_semantically_rejected(self):
        self.prepare()
        path = self.output / 'demo_0.npz'
        with np.load(path) as archive:
            initial, actions = archive['initial'], archive['actions']
        for corrupted in (actions[:-1], np.full_like(actions, np.nan)):
            np.savez(path, actions=corrupted, initial=initial)
            self.update_file_hash(path.name)
            with self.assertRaisesRegex(ValueError, 'admitted'):
                self.load()

    def test_rehashed_model_metadata_and_task_changes_cannot_override_admission(self):
        self.prepare()
        for name in ('demo_0.xml', 'metadata.json', 'task.bddl'):
            path = self.output / name; original = path.read_bytes()
            path.write_bytes(original + b'\n')
            self.update_file_hash(name)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'admission'):
                self.load()
            path.write_bytes(original); self.update_file_hash(name)

    def test_demo_split_and_count_cannot_be_rewritten(self):
        manifest = self.prepare()
        for field in ('demonstrations', 'action_count'):
            bad = copy.deepcopy(manifest)
            if field == 'demonstrations':
                original = bad[field][0]['split']
                bad[field][0]['split'] = 'development' if original == 'validation' else 'validation'
            else:
                bad[field] -= 1
            (self.output / 'manifest.json').write_bytes(json_bytes(bad))
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'denominator'):
                self.load()

    def test_read_cannot_follow_a_snapshot_symlink_outside_its_root(self):
        self.prepare()
        original = self.output / 'demo_0.xml'
        external = self.root / 'external.xml'
        original.rename(external)
        original.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.load()


if __name__ == '__main__':
    unittest.main()
