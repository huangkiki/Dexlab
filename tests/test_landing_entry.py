"""Native admission must not launch an unpinned substitute environment."""

import importlib.metadata
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "landing_entry", Path(__file__).resolve().parents[1] / "demos/landing-contact/run.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class LandingEntryTests(unittest.TestCase):
    def test_generated_assets_are_frozen_and_changed_source_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "third_party/supermimic_vibed/data"
            files = {"g1_description/robot.urdf": b"robot", "backflip/backflip.csv": b"motion",
                     "g1_description/g1_29dof.xml": b"generated XML",
                     "g1_usd/g1_29dof/g1_29dof.usda": b"generated USD"}
            for name, payload in files.items():
                path = data / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            (root / "environment").mkdir()
            (root / "environment/asset-manifest.json").write_text(json.dumps({
                "assets": [{"relative_file": "robot.urdf", "sha256": hashlib.sha256(b"robot").hexdigest()}],
                "motion_csv_sha256": hashlib.sha256(b"motion").hexdigest()}))
            frozen = entry.asset_identity(root)
            generated = data / "g1_usd/g1_29dof/g1_29dof.usda"
            generated.write_bytes(b"changed geometry")
            self.assertNotEqual(frozen, entry.asset_identity(root))
            (data / "backflip/backflip.csv").write_bytes(b"changed motion")
            with self.assertRaisesRegex(ValueError, "published manifest"):
                entry.asset_identity(root)

    def test_newer_engine_does_not_silently_replace_the_reference(self):
        versions = dict(entry.RUNTIME, mujoco="3.17.0")
        with patch.object(entry.importlib.metadata, "version", side_effect=versions.__getitem__), \
                patch.object(entry.importlib.util, "find_spec") as source:
            with self.assertRaisesRegex(ValueError, "Native versions differ"):
                entry.runtime_identity()
            source.assert_not_called()

    def test_missing_packages_have_an_explicit_admission_error(self):
        with patch.object(entry.importlib.metadata, "version", side_effect=importlib.metadata.PackageNotFoundError):
            with self.assertRaisesRegex(ValueError, "unavailable"):
                entry.runtime_identity()


if __name__ == "__main__":
    unittest.main()
