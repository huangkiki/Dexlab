from copy import deepcopy
from unittest.mock import patch
from datetime import datetime, timezone
import unittest

from dexlab.engine_versions import (validate_versions, mujoco_profile_identity,
                                    validate_runtime_qualification, verify_frozen_runtime,
                                    require_formal_batch_qualification)


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


class RuntimeQualificationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 5, tzinfo=timezone.utc)
        self.profiles = {"mujoco": {"solver": "Newton", "dt": 0.0005,
                                    "precision": "float64", "device": "cpu"}}
        self.source = {"task.py": "1" * 64}
        self.runtime = {"installed": {"mujoco": "3.14.0"},
                        "native": {"mujoco": "3.14.0"},
                        "artifact_sha256": {"libmujoco": "2" * 64}}
        self.evidence = {"mujoco": {"raw_record_sha256": "3" * 64,
                         "checks": {"complete": True, "contact": True},
                         "profile": deepcopy(self.profiles["mujoco"])}}
        self.receipt = {"schema_version": 1, "task": "fixture",
                        "profiles": deepcopy(self.profiles),
                        "source_sha256": self.source.copy(),
                        "runtime": deepcopy(self.runtime),
                        "evidence_sha256": {"mujoco": "3" * 64},
                        "audit": [dict(package="mujoco", version="3.14.0",
                            checked_at=self.now.isoformat(), yanked=False,
                            classifiers=[], requires_dist=[],
                            source="https://pypi.org/pypi/mujoco/json")]}

    def admit(self):
        return require_formal_batch_qualification("fixture", self.profiles,
            receipt=self.receipt, source_hashes=self.source, runtime=self.runtime,
            evidence=self.evidence, required_checks={"mujoco": {"complete", "contact"}},
            now=self.now)

    def test_exact_positive_freeze_is_detached_from_mutable_receipt(self):
        frozen = self.admit()
        self.receipt["runtime"]["native"]["mujoco"] = "changed"
        verify_frozen_runtime(frozen, task="fixture", profiles=self.profiles,
                              source_hashes=self.source, runtime=self.runtime)
        self.assertEqual(frozen["runtime"]["native"]["mujoco"], "3.14.0")

    def test_evidence_pass_boolean_cannot_replace_complete_independent_checks(self):
        for checks in ({}, {"complete": True}, {"complete": True, "contact": False},
                       {"complete": True, "contact": 1},
                       {"complete": True, "contact": True, "unexpected": True}):
            with self.subTest(checks=checks):
                self.evidence["mujoco"]["passed"] = True
                self.evidence["mujoco"]["checks"] = checks
                with self.assertRaises(ValueError):
                    self.admit()

    def test_task_settings_source_runtime_and_raw_record_substitutions_fail(self):
        changes = [lambda: self.receipt.update(task="another-task"),
                   lambda: self.profiles["mujoco"].update(dt=0.001),
                   lambda: self.source.update({"task.py": "9" * 64}),
                   lambda: self.runtime["native"].update(mujoco="3.11.0"),
                   lambda: self.runtime["artifact_sha256"].update(libmujoco="8" * 64),
                   lambda: self.evidence["mujoco"].update(raw_record_sha256="7" * 64)]
        for change in changes:
            self.setUp()
            change()
            with self.assertRaises(ValueError):
                self.admit()

    def test_matching_inputs_cannot_resume_a_different_task(self):
        frozen = self.admit()
        with self.assertRaises(ValueError):
            verify_frozen_runtime(frozen, task="different", profiles=self.profiles,
                                  source_hashes=self.source, runtime=self.runtime)

    def test_apple_resume_requires_official_archive_to_observed_code_link(self):
        self.receipt["task"] = "apple-stem"
        self.runtime["package_code_sha256"] = {"mujoco": "5" * 64}
        self.receipt["runtime"] = deepcopy(self.runtime)
        self.receipt["audit"][0]["distribution_sha256"] = {"mujoco.whl": "6" * 64}
        frozen = validate_runtime_qualification(self.receipt, task="apple-stem",
            profiles=self.profiles, source_hashes=self.source, runtime=self.runtime,
            evidence=self.evidence, required_checks={"mujoco": {"complete", "contact"}}, now=self.now)
        def check():
            verify_frozen_runtime(frozen, task="apple-stem", profiles=self.profiles,
                                  source_hashes=self.source, runtime=self.runtime)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            check()
        frozen["official_wheels"] = {"mujoco": {"filename": "mujoco.whl",
            "sha256": "6" * 64, "package_code_sha256": "5" * 64}}
        check()
        frozen["official_wheels"]["mujoco"]["sha256"] = "7" * 64
        with self.assertRaisesRegex(ValueError, "differ"):
            check()

    def test_missing_freeze_cannot_resume(self):
        with self.assertRaises(ValueError):
            verify_frozen_runtime({}, task="fixture", profiles={}, source_hashes={}, runtime={})

    def test_frozen_resume_keeps_dated_release_but_rejects_artifact_changes(self):
        frozen = self.admit()
        # Freshness applies at freeze, not to the exact unchanged resume.
        frozen["audit"][0]["checked_at"] = "2020-01-01T00:00:00+00:00"
        verify_frozen_runtime(frozen, task="fixture", profiles=self.profiles,
                              source_hashes=self.source, runtime=self.runtime)
        self.runtime["artifact_sha256"]["libmujoco"] = "4" * 64
        with self.assertRaises(ValueError):
            verify_frozen_runtime(frozen, task="fixture", profiles=self.profiles,
                                  source_hashes=self.source, runtime=self.runtime)


if __name__ == "__main__":
    unittest.main()
