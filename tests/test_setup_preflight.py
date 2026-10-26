"""Run both real shell entries against disposable venvs and a non-installing uv spy."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv

ROOT = Path(__file__).resolve().parents[1]


class SetupAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "checkout"
        self.repo.mkdir()
        for name in ("scripts/setup.sh", "scripts/setup_source.sh", "scripts/setup_preflight.py",
                     "scripts/python-constraints.txt", "scripts/runtime-requirements.txt",
                     "scripts/source-build-requirements.txt",
                     "demos/apple-stem-grasp/requirements.txt"):
            source = ROOT / name
            if source.exists():
                target = self.repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        self.env = self.repo / ".venv"
        venv.EnvBuilder(with_pip=False, symlinks=True).create(self.env)
        self.site = self.env / "lib/python3.12/site-packages"
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.calls = self.base / "uv-calls.jsonl"
        spy = self.bin / "uv"
        spy.write_text(f"#!{sys.executable}\n" + '''import json, os, subprocess, sys
with open(os.environ["SETUP_SPY_LOG"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1] == "venv":
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", sys.argv[-1]], check=True)
else:
    sys.exit(73)  # Admission reached installation, but no packages are modified.
''')
        spy.chmod(0o755)

    def package(self, name, version, *, site=None, editable=None):
        target = (site or self.site) / f"{name}-{version}.dist-info"
        target.mkdir(parents=True)
        (target / "METADATA").write_text(f"Name: {name}\nVersion: {version}\n")
        entries = [f"{target.name}/METADATA,,"]
        if editable is not None:
            (target / "direct_url.json").write_text(json.dumps({
                "url": Path(editable).as_uri(), "dir_info": {"editable": True},
            }))
            entries.append(f"{target.name}/direct_url.json,,")
        (target / "RECORD").write_text("\n".join(entries) + "\n")

    def run_setup(self, script, *args, profile="historical-3.11.0"):
        if self.calls.exists():
            self.calls.unlink()
        return subprocess.run(["bash", str(self.repo / "scripts" / script), *args],
            env={**os.environ, "PATH": str(self.bin) + os.pathsep + os.defpath,
                 "CC": "true", "CXX": "true", "SETUP_SPY_LOG": str(self.calls),
                 "DEXLAB_MUJOCO_PROFILE": profile}, text=True, capture_output=True)

    def assert_rejected(self, *args, message, **kwargs):
        result = self.run_setup(*args, **kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists(), result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        return result

    def test_existing_316_rejected_without_installation_or_metadata_changes(self):
        self.package("mujoco", "3.16.0")
        metadata = self.site / "mujoco-3.16.0.dist-info/METADATA"
        before = metadata.read_bytes()
        for script in ("setup.sh", "setup_source.sh"):
            with self.subTest(script=script):
                self.assert_rejected(script, message="mujoco 3.16.0")
                self.assertEqual(metadata.read_bytes(), before)

    def test_selected_candidate_profile_rejected_before_even_creating_venv(self):
        shutil.rmtree(self.env)
        for script in ("setup.sh", "setup_source.sh"):
            with self.subTest(script=script):
                self.assert_rejected(script, profile="qualification-3.17.0", message="historical-3.11.0")
                self.assertFalse(self.env.exists())

    def test_unknown_shared_link_is_rejected(self):
        target = self.base / "shared-environment"
        self.env.rename(target)
        self.env.symlink_to(target, target_is_directory=True)
        for script in ("setup.sh", "setup_source.sh"):
            with self.subTest(script=script):
                self.assert_rejected(script, message="--claim-environment")

    def test_clean_environment_and_compatible_reentry_reach_installation(self):
        for script in ("setup.sh", "setup_source.sh"):
            with self.subTest(script=script):
                result = self.run_setup(script)
                self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
                self.assertEqual(json.loads(self.calls.read_text().splitlines()[0])[0], "pip")
        self.package("mujoco", "3.11.0")
        self.package("dexlab", "0.66.1", editable=self.repo)
        for script in ("setup.sh", "setup_source.sh"):
            result = self.run_setup(script)
            self.assertEqual(result.returncode, 73, result.stdout + result.stderr)

    def test_fresh_install_creates_only_its_own_environment_before_admission(self):
        shutil.rmtree(self.env)
        result = self.run_setup("setup.sh")
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        self.assertEqual([call[0] for call in calls], ["venv", "pip"])
        self.assertTrue((self.env / "dexlab-environment.json").is_file())

    def test_owned_mounted_link_can_be_claimed_then_reentered(self):
        target = self.base / "mounted-environment"
        self.env.rename(target)
        self.env.symlink_to(target, target_is_directory=True)
        result = self.run_setup("setup.sh", "--claim-environment")
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        marker = target / "dexlab-environment.json"
        before = marker.read_bytes()
        owner = json.loads(before)
        self.assertEqual(owner["checkout"], str(self.repo))
        self.assertEqual(owner["profile"], "historical-3.11.0")
        result = self.run_setup("setup_source.sh")
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertEqual(marker.read_bytes(), before)

    def test_claim_does_not_bypass_profile_or_existing_ownership(self):
        marker = self.env / "dexlab-environment.json"
        marker.write_text(json.dumps({"schema_version": 1, "checkout": "/another/checkout",
                                      "profile": "historical-3.11.0"}))
        before = marker.read_bytes()
        for script in ("setup.sh", "setup_source.sh"):
            self.assert_rejected(script, "--claim-environment", message="ownership/profile differs")
            self.assertEqual(marker.read_bytes(), before)
        marker.unlink()
        self.package("mujoco", "3.17.0")
        self.assert_rejected("setup.sh", "--claim-environment", message="mujoco 3.17.0")
        self.assertFalse(marker.exists())

    def test_other_editable_checkout_is_rejected(self):
        self.package("dexlab", "0.66.1", editable=self.base / "another-checkout")
        for script in ("setup.sh", "setup_source.sh"):
            self.assert_rejected(script, message="another checkout")

    def test_matching_packages_from_external_site_path_are_rejected(self):
        shared = self.base / "shared-site"
        self.package("mujoco", "3.11.0", site=shared)
        (self.site / "inherited.pth").write_text(str(shared) + "\n")
        for script in ("setup.sh", "setup_source.sh"):
            self.assert_rejected(script, message="outside this environment")

    def test_populated_unknown_link_cannot_be_claimed(self):
        self.package("mujoco", "3.11.0")
        target = self.base / "shared-environment"
        self.env.rename(target)
        self.env.symlink_to(target, target_is_directory=True)
        self.assert_rejected("setup.sh", "--claim-environment", message="populated shared environment")
        self.assertFalse((target / "dexlab-environment.json").exists())

    def test_invalid_marker_and_broken_environment_fail_closed(self):
        marker = self.env / "dexlab-environment.json"
        marker.write_text("invalid json")
        self.assert_rejected("setup.sh", message="Setup refused")
        self.assertEqual(marker.read_text(), "invalid json")
        marker.unlink()
        shutil.rmtree(self.env)
        self.env.symlink_to(self.base / "missing")
        self.assert_rejected("setup_source.sh", message="broken link")
        self.assertFalse((self.base / "missing").exists())

    def test_explicit_profile_overrides_inherited_candidate_and_source_routes_arguments(self):
        result = self.run_setup("setup.sh", "--source", "--mujoco-profile", "historical-3.11.0",
                                profile="qualification-3.17.0")
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertIn("source-build-requirements.txt", self.calls.read_text())

    def test_source_option_after_profile_still_selects_source_installer(self):
        result = self.run_setup("setup.sh", "--mujoco-profile", "historical-3.11.0", "--source")
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertIn("source-build-requirements.txt", self.calls.read_text())

    def test_unknown_inspection_flag_cannot_bypass_installer_admission(self):
        for script in ("setup.sh", "setup_source.sh"):
            self.assert_rejected(script, "--inspect", message="unrecognized arguments")

    def test_help_does_not_create_or_install_an_environment(self):
        shutil.rmtree(self.env)
        for script in ("setup.sh", "setup_source.sh"):
            result = self.run_setup(script, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--claim-environment", result.stdout)
            self.assertFalse(self.calls.exists())
            self.assertFalse(self.env.exists())

    def test_source_build_pin_conflict_is_rejected_before_pip_or_build(self):
        self.package("cmake", "4.3.0")
        self.assert_rejected("setup_source.sh", message="cmake 4.3.0")
        result = self.run_setup("setup.sh")  # wheel installation does not use CMake
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)

    def test_package_payload_linked_outside_prefix_is_not_modified(self):
        self.package("mujoco", "3.11.0")
        external = self.base / "shared.py"
        external.write_text("original payload\n")
        (self.site / "mujoco.py").symlink_to(external)
        with (self.site / "mujoco-3.11.0.dist-info/RECORD").open("a") as stream:
            stream.write("mujoco.py,,\n")
        self.assert_rejected("setup.sh", message="outside this environment")
        self.assertEqual(external.read_text(), "original payload\n")


if __name__ == "__main__":
    unittest.main()
