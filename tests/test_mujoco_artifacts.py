"""Compressed evidence must reconstruct the exact original MuJoCo binary."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import mujoco
import numpy as np

from dexlab.mujoco_artifacts import load_model, model_inputs, pack_model


class ModelArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.model = mujoco.MjModel.from_xml_string(
            '<mujoco><worldbody><body pos="0 0 1"><freejoint/>'
            '<geom type="sphere" size="0.03" mass="0.3"/>'
            "</body></worldbody></mujoco>"
        )
        self.binary = self.path / "model.mjb"
        mujoco.mj_saveModel(self.model, str(self.binary))

    def test_raw_and_lossless_compressed_models_agree(self):
        before = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        np.testing.assert_array_equal(
            load_model(self.path).body_mass, self.model.body_mass
        )
        pack_model(self.path)
        self.assertFalse(self.binary.exists())
        manifest = json.loads((self.path / "model-artifact.json").read_text())
        self.assertEqual(manifest["uncompressed_sha256"], before)
        restored = load_model(self.path)
        np.testing.assert_array_equal(restored.body_mass, self.model.body_mass)
        np.testing.assert_array_equal(restored.qpos0, self.model.qpos0)
        self.assertEqual(len(model_inputs(self.path)), 2)

    def test_wrong_original_hash_is_rejected(self):
        pack_model(self.path)
        path = self.path / "model-artifact.json"
        manifest = json.loads(path.read_text())
        manifest["uncompressed_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "original binary hash"):
            load_model(self.path)

    def test_expansion_larger_than_manifest_is_rejected(self):
        pack_model(self.path)
        path = self.path / "model-artifact.json"
        manifest = json.loads(path.read_text())
        manifest["uncompressed_bytes"] = 1
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "declared size"):
            load_model(self.path)

    def test_backend_without_mujoco_binary_is_unchanged(self):
        self.binary.unlink()
        pack_model(self.path)
        self.assertEqual(list(self.path.iterdir()), [])

    def test_chunked_records_share_storage_and_remain_standalone(self):
        second = self.path / "second"
        second.mkdir()
        shutil.copy2(self.binary, second / "model.mjb")
        shared = self.path / "shared"
        pack_model(self.path, shared_store=shared)
        pack_model(second, shared_store=shared)
        chunks = list((self.path / "model-chunks").glob("*.gz"))
        for chunk in chunks:
            self.assertEqual(chunk.stat().st_ino, (second / "model-chunks" / chunk.name).stat().st_ino)
        shutil.rmtree(shared)
        np.testing.assert_array_equal(load_model(second).body_mass, self.model.body_mass)
        self.assertEqual(len(model_inputs(second)), len(chunks) + 1)

    def test_corrupt_chunk_is_rejected(self):
        pack_model(self.path, shared_store=self.path / "shared")
        chunk = next((self.path / "model-chunks").glob("*.gz"))
        import gzip
        chunk.write_bytes(gzip.compress(b"corrupted"))
        with self.assertRaisesRegex(ValueError, "Model chunk"):
            load_model(self.path)

    def test_manifest_cannot_reference_an_arbitrary_path(self):
        pack_model(self.path, shared_store=self.path / "shared")
        path = self.path / "model-artifact.json"
        manifest = json.loads(path.read_text())
        manifest["chunks"][0]["sha256"] = "../outside"
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Invalid model chunk"):
            load_model(self.path)


if __name__ == "__main__":
    unittest.main()
