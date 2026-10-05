"""Small isolated provenance tests; no native imports or experiments."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import warnings
import zipfile

from dexlab.official_wheels import verify_official_wheel


class WheelIdentityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.wheel = Path(temp.name) / 'fixture-1.0-py3-none-any.whl'
        with zipfile.ZipFile(self.wheel, 'w') as archive:
            archive.writestr('fixture/__init__.py', b'original')
            archive.writestr('fixture-1.0.dist-info/METADATA', 'Name: fixture\nVersion: 1.0\n')
        hashes = {'fixture/__init__.py': hashlib.sha256(b'original').hexdigest()}
        self.arguments = dict(package='fixture', version='1.0',
                              official_sha256=self.digest(),
                              installed_code_sha256=hashlib.sha256(
                                  json.dumps(hashes, sort_keys=True).encode()).hexdigest())

    def digest(self):
        return hashlib.sha256(self.wheel.read_bytes()).hexdigest()

    def test_official_code_match_and_no_private_path_in_evidence(self):
        evidence = verify_official_wheel(self.wheel, **self.arguments)
        self.assertEqual(evidence['code_files'], 1)
        self.assertNotIn(str(self.wheel.parent), json.dumps(evidence))

    def test_task_admission_binds_real_archive_and_rejects_modified_install(self):
        from dexlab.apple_admission import admit_records, COMMON_CHECKS
        from dexlab.engine_versions import verify_frozen_runtime

        runtime = {"installed": {"fixture": "1.0"}, "native": {"fixture": "1.0"},
                   "artifact_sha256": {"fixture": "2" * 64},
                   "package_code_sha256": {"fixture": self.arguments["installed_code_sha256"]}}
        row = {"package": "fixture", "version": "1.0",
               "checked_at": datetime.now(timezone.utc).isoformat(),
               "source": "https://pypi.org/pypi/fixture/json", "yanked": False,
               "classifiers": [], "requires_dist": [],
               "distribution_sha256": {self.wheel.name: self.digest()}}
        profiles = {"fixture-profile": {"backend": "superdex"}}
        evidence = {"raw_record_sha256": "3" * 64,
                    "profile": profiles["fixture-profile"],
                    "checks": {name: True for name in COMMON_CHECKS | {"fp64"}}}
        with patch("dexlab.apple_admission.observe_runtime", return_value=runtime), \
             patch("dexlab.apple_admission.refresh_inventory", return_value=[row]), \
             patch("dexlab.apple_admission.rescore_record", return_value=evidence) as scorer:
            frozen = admit_records({"fixture-profile": "raw-record"}, profiles,
                                   {"task.py": "4" * 64}, wheel_dir=self.wheel.parent)
            verify_frozen_runtime(frozen, task="apple-stem", profiles=profiles,
                                  source_hashes={"task.py": "4" * 64}, runtime=runtime)
            scorer.assert_called_once()
            scorer.reset_mock()
            runtime["package_code_sha256"]["fixture"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "Installed code differs"):
                admit_records({"fixture-profile": "raw-record"}, profiles,
                              {"task.py": "4" * 64}, wheel_dir=self.wheel.parent)
            scorer.assert_not_called()

    def test_altered_distribution_rejected(self):
        with self.assertRaisesRegex(ValueError, 'official distribution'):
            verify_official_wheel(self.wheel, **(self.arguments | {'official_sha256': '0' * 64}))

    def test_self_consistent_rebuilt_install_not_enough(self):
        with self.assertRaisesRegex(ValueError, 'Installed code differs'):
            verify_official_wheel(self.wheel, **(self.arguments | {'installed_code_sha256': '0' * 64}))

    def test_other_version_or_package_rejected(self):
        for replacement in ({'version': '2.0'}, {'package': 'other'}):
            with self.subTest(replacement=replacement), self.assertRaisesRegex(ValueError, 'identity mismatch'):
                verify_official_wheel(self.wheel, **(self.arguments | replacement))

    def test_duplicate_members_rejected_even_with_matching_archive_hash(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.wheel, 'a') as archive:
                archive.writestr('fixture/__init__.py', b'replacement')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify_official_wheel(self.wheel, **(self.arguments | {'official_sha256': self.digest()}))

    def test_unsupported_code_relocation_fails_closed(self):
        with zipfile.ZipFile(self.wheel, 'a') as archive:
            archive.writestr('fixture-1.0.data/purelib/other.py', b'other')
        with self.assertRaisesRegex(ValueError, 'relocation'):
            verify_official_wheel(self.wheel, **(self.arguments | {'official_sha256': self.digest()}))


if __name__ == '__main__':
    unittest.main()
