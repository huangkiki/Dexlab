from copy import deepcopy
from unittest.mock import patch
from datetime import datetime, timezone
import unittest

from dexlab.engine_versions import validate_versions, mujoco_profile_identity


class VersionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 5, tzinfo=timezone.utc)
        self.row = dict(package="mujoco", version="3.14.0", checked_at=self.now.isoformat(),
                        yanked=False, classifiers=[], requires_dist=[],
                        source="https://pypi.org/pypi/mujoco/json")

    def check(self, rows, installed=None, native=None, **kwargs):
        return validate_versions(rows, installed or {"mujoco": "3.14.0"},
                                 native or {"mujoco": "3.14.0"}, now=self.now, **kwargs)

    def test_metadata_pass_is_not_runtime_qualification(self):
        self.assertEqual(self.check([self.row]),
                         {"metadata_compatible": True, "runtime_qualified": False})

    def test_stale_missing_yanked_and_immature_evidence_rejected(self):
        for change in ({"checked_at": "2026-10-01T00:00:00+00:00"},
                       {"checked_at": "2026-10-06T00:00:00+00:00"},
                       {"yanked": True}, {"yanked": None},
                       {"classifiers": ["Development Status :: 3 - Alpha"]},
                       {"version": "3.15.0"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check([self.row | change])
        with self.assertRaises(ValueError):
            self.check([])

    def test_previews_and_native_mismatch_rejected(self):
        for version in ("3.14.0rc1", "3.15.0.dev1", "3.14.0+patched"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.check([self.row | {"version": version}], {"mujoco": version})
        with self.assertRaises(ValueError):
            self.check([self.row], native={"mujoco": "3.11.0"})

    def test_newton_sim_extra_cannot_silently_downgrade_mujoco(self):
        newton = deepcopy(self.row)
        newton.update(package="newton", version="1.6.0",
                      source="https://pypi.org/pypi/newton/json",
                      requires_dist=['mujoco~=3.12.0; extra == "sim"'])
        versions = {"mujoco": "3.14.0", "newton": "1.6.0"}
        self.check([self.row, newton], versions)
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            self.check([self.row, newton], versions, extras={"newton": ["sim"]})


class MuJoCoCompatibilityProfileTests(unittest.TestCase):
    def test_historical_default_does_not_silently_upgrade(self):
        with patch.dict("os.environ", {}, clear=True):
            old = mujoco_profile_identity({"version": "3.11.0"}, "3.11.0")
            self.assertEqual(old["profile_status"], "historical")
            with self.assertRaises(ValueError):
                mujoco_profile_identity({"version": "3.14.0"}, "3.14.0")

    def test_candidate_requires_explicit_selection_and_native_match(self):
        identity = {"version": "3.14.0", "code_sha256": "example"}
        with patch.dict("os.environ", {"DEXLAB_MUJOCO_PROFILE": "qualification-3.14.0"}):
            result = mujoco_profile_identity(identity, "3.14.0")
            self.assertEqual(result["profile_status"], "candidate")
            self.assertFalse(result["formal_batch_qualified"])
            self.assertEqual(identity, {"version": "3.14.0", "code_sha256": "example"})
            with self.assertRaises(ValueError):
                mujoco_profile_identity(identity, "3.11.0")
        with self.assertRaises(ValueError):
            mujoco_profile_identity(identity, "3.14.0", profile="latest")


if __name__ == "__main__":
    unittest.main()
