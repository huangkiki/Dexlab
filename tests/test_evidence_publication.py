"""Public metadata must not conceal changes to scientific inputs."""
import hashlib
import json
import unittest

from dexlab.evidence_publication import project_json, public_metadata


class PublicMetadataTest(unittest.TestCase):
    def test_redaction_is_explicit_and_preserves_scientific_values(self):
        original = {"command": ["/home/example/run.py", "--dt", "0.001"],
                    "engine": {"version": "1.0", "package_identity": {
                        "installation_origin": {"url": "file:///home/example/build"}}},
                    "case": {"mass": 0.15, "friction": 0.8},
                    "trajectory_sha256": "untouched", "status": "failed"}
        raw = json.dumps(original).encode()
        public, lineage = project_json(raw)
        parsed = json.loads(public)
        self.assertEqual(parsed["case"], original["case"])
        self.assertEqual(parsed["status"], "failed")
        self.assertEqual(parsed["trajectory_sha256"], "untouched")
        self.assertEqual(parsed["engine"]["version"], "1.0")
        self.assertNotIn("command", parsed)
        self.assertEqual(lineage["removed_json_pointers"],
                         ["/command", "/engine/package_identity/installation_origin"])
        self.assertEqual(lineage["original_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(lineage["original_sha256"], lineage["public_sha256"])
        self.assertIn("command", original)

    def test_unreviewed_path_is_rejected_without_mutating_original(self):
        original = {"case": {"material": "/mnt/private/material.json"}}
        with self.assertRaisesRegex(ValueError, "/case/material"):
            public_metadata(original)
        self.assertEqual(original["case"]["material"], "/mnt/private/material.json")

    def test_unchanged_json_keeps_exact_bytes(self):
        raw = b'{  "failed": true, "value": null }\n'
        public, lineage = project_json(raw)
        self.assertEqual(public, raw)
        self.assertEqual(lineage["transformation"], "byte-identical")

    def test_nested_receipt_metadata_is_projected_consistently(self):
        run = {"command": ["/tmp/work/run.py"], "dt": 0.001}
        report = {"records": [{"metadata": run}]}
        result, pointers = public_metadata(report)
        self.assertEqual(result["records"][0]["metadata"], public_metadata(run)[0])
        self.assertEqual(pointers, ["/records/0/metadata/command"])


class BundleIntegrityTest(unittest.TestCase):
    def setUp(self):
        import importlib.util
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.payload = self.bundle / "payload.bin"
        self.payload.write_bytes(b"immutable")
        manifest = {"schema": "public-historical-bundle-v1", "environment": {},
                    "files": {"payload.bin": hashlib.sha256(b"immutable").hexdigest()}}
        (self.bundle / "manifest.json").write_text(json.dumps(manifest))
        script = Path(__file__).resolve().parents[1] / "scripts/reproduce_historical_bundle.py"
        spec = importlib.util.spec_from_file_location("bundle_reproduction", script)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_missing_file_rejected_before_scoring(self):
        self.payload.unlink()
        with self.assertRaisesRegex(ValueError, "missing or undeclared"):
            self.module.reproduce(self.bundle, self.root / "result")
        self.assertFalse((self.root / "result").exists())

    def test_corrupt_file_rejected_before_scoring(self):
        self.payload.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.module.reproduce(self.bundle, self.root / "result")

    def test_extra_python_file_rejected(self):
        (self.bundle / "injected.py").write_text("raise RuntimeError")
        with self.assertRaisesRegex(ValueError, "missing or undeclared"):
            self.module.reproduce(self.bundle, self.root / "result")

    def test_symlink_rejected_even_if_target_bytes_match(self):
        target = self.root / "external"
        target.write_bytes(self.payload.read_bytes())
        self.payload.unlink()
        self.payload.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.module.reproduce(self.bundle, self.root / "result")

    def test_output_cannot_mutate_input_bundle(self):
        with self.assertRaisesRegex(ValueError, "outside the bundle"):
            self.module.reproduce(self.bundle, self.bundle / "result")

    def test_scientific_command_path_is_not_silently_removed(self):
        with self.assertRaisesRegex(ValueError, "Unreviewed"):
            public_metadata({"controller": {"command": ["/home/private/policy"]}})


class BundleInstructionTest(unittest.TestCase):
    def test_archive_identity_is_external_to_the_archive(self):
        from dexlab.evidence_publication import bundle_readme
        data = (b"Header\n<!-- repository-only:start -->\narchive hash\n"
                b"<!-- repository-only:end -->\n[English](PUBLIC-ARCHIVE.md)\n")
        self.assertEqual(bundle_readme(data), b"Header\n[English](README.md)\n")
