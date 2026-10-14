"""Compressed evidence must reconstruct the exact original MuJoCo binary."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import mujoco
import numpy as np

from dexlab.mujoco_artifacts import (
    conversion_parameters, load_model, model_inputs, pack_model,
    parameter_differences, save_conversion_evidence, warp_model_parameters,
    cpu_contact_address_valid,
)


class GpuReadbackTests(unittest.TestCase):
    def test_cpu_contact_bounds_cover_inactive_pyramid_and_elliptic_contacts(self):
        self.assertTrue(cpu_contact_address_valid(-1, 3, True, 0))
        self.assertFalse(cpu_contact_address_valid(0, 3, True, 0))
        self.assertTrue(cpu_contact_address_valid(4, 3, True, 8))
        self.assertFalse(cpu_contact_address_valid(8, 3, True, 8))
        self.assertFalse(cpu_contact_address_valid(12, 3, True, 8))
        self.assertTrue(cpu_contact_address_valid(5, 3, False, 8))
        self.assertFalse(cpu_contact_address_valid(6, 3, False, 8))
        self.assertTrue(cpu_contact_address_valid(7, 1, True, 8))
        self.assertFalse(cpu_contact_address_valid(-2, 3, True, 8))

    def test_gpu_overrides_and_float32_precision_are_observed(self):
        class Parameters:
            def __getattr__(self, name):
                return 0

        class Array:
            def __init__(self, values):
                self.values = np.asarray(values, dtype=np.float32)

            def numpy(self):
                return self.values.copy()

        model = Parameters()
        model.opt = Parameters()
        model.stat = Parameters()
        model.block_dim = Parameters()
        model.body_mass = Array([[0., .064]])
        model.opt.timestep = Array([.001])
        first = warp_model_parameters(model)
        self.assertEqual(first['dtypes']['body_mass'], 'float32')
        self.assertNotEqual(first['values']['body_mass'][0][1], .064)
        model.body_mass.values[0, 1] = .128
        second = warp_model_parameters(model)
        self.assertFalse(parameter_differences(first['values'], second['values'])['body_mass']['equal'])
        model.body_mass.values[0, 1] = np.nan
        with self.assertRaisesRegex(ValueError, 'Non-finite GPU parameter: body_mass'):
            warp_model_parameters(model)

    def test_missing_gpu_field_is_not_an_inferred_default(self):
        with self.assertRaises(AttributeError):
            warp_model_parameters(SimpleNamespace())


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


class ConversionEvidenceTests(unittest.TestCase):
    def test_mjspec_export_loss_preserves_exact_binary_and_source_arrays(self):
        spec = mujoco.MjSpec.from_string(
            '<mujoco><worldbody><body pos="0.123456789123 0 1"><freejoint/>'
            '<geom type="box" size=".02 .02 .02" mass=".06400000303983688"/>'
            '</body></worldbody></mujoco>')
        model = spec.compile()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            intermediate = root / 'framework.xml'
            intermediate.write_text(spec.to_xml())
            saved = save_conversion_evidence(model, root, intermediate=intermediate)
            self.assertTrue(saved['binary_readback_exact'])
            self.assertGreater(saved['intermediate_differences']['body_mass']['max_abs'], 0.)
            self.assertGreater(saved['intermediate_differences']['body_pos']['max_abs'], 0.)
            np.testing.assert_array_equal(load_model(root).body_mass, model.body_mass)
            original = (root / 'model.mjb').read_bytes()
            with self.assertRaises(FileExistsError):
                save_conversion_evidence(model, root, intermediate=intermediate)
            self.assertEqual((root / 'model.mjb').read_bytes(), original)

    def test_drive_and_frame_changes_are_observable(self):
        model = mujoco.MjModel.from_xml_string(
            '<mujoco><worldbody><body><joint name="j" axis="0 1 0"/>'
            '<geom type="box" size=".02 .03 .04"/></body></worldbody>'
            '<actuator><position joint="j" kp="10"/></actuator></mujoco>')
        before = conversion_parameters(model)
        model.actuator_gainprm[0, 0] = 20
        model.body_ipos[1, 0] = .001
        changes = parameter_differences(before, conversion_parameters(model))
        self.assertEqual(changes['actuator_gainprm']['max_abs'], 10.)
        self.assertEqual(changes['body_ipos']['max_abs'], .001)
        self.assertFalse(changes['actuator_gainprm']['equal'])

    def test_missing_nonfinite_and_shape_changes_cannot_look_equal(self):
        with self.assertRaisesRegex(ValueError, 'fields differ'):
            parameter_differences({'mass': [1.]}, {})
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            parameter_differences({'mass': [1.]}, {'mass': [float('nan')]})
        changed = parameter_differences({'mass': [1.]}, {'mass': [1., 1.]})
        self.assertIsNone(changed['mass']['max_abs'])
        self.assertFalse(changed['mass']['equal'])


if __name__ == "__main__":
    unittest.main()
