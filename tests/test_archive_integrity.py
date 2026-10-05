import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from dexlab.archive_integrity import content_manifest, finalize, snapshot, verify_copy


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'model.bin').write_bytes(b'complete model')
        (self.source / 'trace.json').write_text('[1,2,3]')
        self.before = snapshot(self.source)
        self.stage = self.root / '.incoming'
        shutil.copytree(self.source, self.stage)
        self.destination = self.root / 'archive'
        self.receipt = self.root / 'receipts' / 'run.json'

    def reader(self, path):
        self.assertEqual(json.loads((path / 'trace.json').read_text()), [1, 2, 3])
        return {'readable': True, 'scientific_acceptance': False}

    def finish(self, reader=None, after=None):
        return finalize(self.stage, self.destination, self.before,
                        snapshot(self.source) if after is None else after,
                        self.reader if reader is None else reader, receipt_path=self.receipt)

    def test_complete_failed_experiment_is_archived_without_deleting_source(self):
        receipt = self.finish()
        self.assertTrue(receipt['archived'])
        self.assertFalse(receipt['offline_read']['scientific_acceptance'])
        self.assertFalse(receipt['source_deleted'])
        self.assertEqual(self.before, snapshot(self.source))
        verify_copy(self.destination, self.before)
        self.assertFalse(self.stage.exists())
        self.assertEqual(receipt, json.loads(self.receipt.read_text()))

    def test_missing_extra_corrupted_and_linked_files_are_rejected(self):
        for mutation in ('missing', 'extra', 'corrupt', 'link'):
            with self.subTest(mutation=mutation):
                shutil.rmtree(self.stage)
                shutil.copytree(self.source, self.stage)
                if mutation == 'missing': (self.stage / 'model.bin').unlink()
                elif mutation == 'extra': (self.stage / 'extra').touch()
                elif mutation == 'corrupt': (self.stage / 'model.bin').write_bytes(b'bad')
                else: (self.stage / 'external').symlink_to(self.source / 'model.bin')
                with self.assertRaises(ValueError): self.finish()
                self.assertTrue(self.stage.exists())
                self.assertFalse(self.destination.exists())

    def test_source_mutation_during_transfer_is_rejected(self):
        (self.source / 'model.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Source changed'): self.finish()
        self.assertTrue(self.stage.exists())
        self.assertFalse(self.receipt.exists())

    def test_reader_failure_or_mutation_never_promotes(self):
        with self.assertRaises(ValueError): self.finish(reader=lambda p: {'readable': False})
        def mutate(path):
            (path / 'trace.json').write_text('[]')
            return {'readable': True}
        with self.assertRaises(ValueError): self.finish(reader=mutate)
        self.assertFalse(self.destination.exists())

    def test_manifest_totals_and_unsafe_paths_are_rejected(self):
        for change in ({'path': '../escape'}, {'path': '/absolute'}, {'sha256': 'not a hash'}, {'bytes': -1}):
            value = json.loads(json.dumps(self.before));value['files'][0].update(change)
            with self.assertRaises(ValueError): content_manifest(value)
        value = json.loads(json.dumps(self.before));value['total_bytes'] += 1
        with self.assertRaises(ValueError): content_manifest(value)

    def test_existing_unrelated_archive_is_never_replaced(self):
        self.destination.mkdir()
        with self.assertRaises(FileExistsError): self.finish()

    def test_crash_between_promotion_and_receipt_can_resume_without_copy(self):
        import dexlab.archive_integrity as module
        write = module.write_receipt
        calls = 0
        def crash(path, value):
            nonlocal calls
            calls += 1
            if calls == 2: raise OSError('simulated receipt failure')
            write(path, value)
        with patch.object(module, 'write_receipt', side_effect=crash):
            with self.assertRaises(OSError): self.finish()
        self.assertTrue(self.destination.exists())
        self.assertFalse(json.loads(self.receipt.read_text())['archived'])
        self.assertTrue(self.finish()['archived'])

    def test_crash_before_promotion_can_resume_the_staging_copy(self):
        with patch.object(Path, 'rename', side_effect=OSError('simulated rename failure')):
            with self.assertRaises(OSError): self.finish()
        self.assertTrue(self.stage.exists())
        self.assertFalse(json.loads(self.receipt.read_text())['archived'])
        self.assertTrue(self.finish()['archived'])
