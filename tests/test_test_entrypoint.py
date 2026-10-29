"""Test selection must fail before discovery, not inside native fixtures."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_tests", ROOT / "scripts/run_tests.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class TestEntryPointTests(unittest.TestCase):
    def invoke(self, arguments=(), *, package="3.16.0", native="3.16.0", environment=None):
        output = io.StringIO()
        engine = SimpleNamespace(mj_versionString=lambda: native)
        with patch.dict(os.environ, environment or {}, clear=True), \
                patch.object(sys, "path", sys.path.copy()), \
                patch.dict(sys.modules, {"mujoco": engine}), \
                patch.object(entry, "version", return_value=package), \
                patch.object(entry.subprocess, "run", return_value=SimpleNamespace(returncode=7)) as run, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                code = entry.main(list(arguments))
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), run

    def test_missing_profile_never_starts_suite(self):
        code, message, run = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn("--mujoco-profile", message)
        run.assert_not_called()

    def test_incompatible_identity_never_starts_suite(self):
        for profile, package, native in (
            ("historical-3.11.0", "3.16.0", "3.16.0"),
            ("qualification-3.16.0", "3.16.0", "3.11.0"),
            ("qualification-3.16.0", "3.15.0", "3.16.0"),
            ("unknown", "3.16.0", "3.16.0"),
        ):
            with self.subTest(profile=profile, package=package, native=native):
                code, message, run = self.invoke(
                    ["--mujoco-profile", profile], package=package, native=native)
                self.assertEqual(code, 2)
                for value in (profile, package, native, sys.executable):
                    self.assertIn(value, message)
                run.assert_not_called()

    def test_cli_profile_binds_child_environment_and_preserves_failure(self):
        code, message, run = self.invoke(
            ["--mujoco-profile", "qualification-3.16.0", "--pattern", "test_contact_load.py"],
            environment={"DEXLAB_MUJOCO_PROFILE": "historical-3.11.0", "PYTHONPATH": "/old/source"},
        )
        self.assertEqual(code, 7)
        command = run.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[1:4], ["-m", "unittest", "discover"])
        self.assertEqual(command[-1], "test_contact_load.py")
        self.assertEqual(run.call_args.kwargs["cwd"], ROOT)
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["DEXLAB_MUJOCO_PROFILE"], "qualification-3.16.0")
        self.assertEqual(environment["PYTHONPATH"].split(os.pathsep)[:2],
                         [str(ROOT / "src"), str(ROOT / "demos/apple-stem-grasp/src")])
        self.assertIn(str(ROOT / "src/dexlab"), message)

    def test_inherited_profile_and_historical_runtime_remain_supported(self):
        for profile, version in (("historical-3.11.0", "3.11.0"),
                                 ("qualification-3.16.0", "3.16.0")):
            with self.subTest(profile=profile):
                code, _, run = self.invoke(package=version, native=version,
                                          environment={"DEXLAB_MUJOCO_PROFILE": profile})
                self.assertEqual(code, 7)
                run.assert_called_once()

    def test_check_only_does_not_run_tests(self):
        code, _, run = self.invoke(["--mujoco-profile", "qualification-3.16.0", "--check-only"])
        self.assertEqual(code, 0)
        run.assert_not_called()

    def test_missing_native_module_is_reported_before_discovery(self):
        output = io.StringIO()
        with patch.dict(sys.modules, {"mujoco": None}), \
                patch.object(sys, "path", sys.path.copy()), \
                patch.object(entry, "version", return_value="3.16.0"), \
                patch.object(entry.subprocess, "run") as run, \
                contextlib.redirect_stderr(output):
            code = entry.main(["--mujoco-profile", "qualification-3.16.0"])
        self.assertEqual(code, 2)
        self.assertIn("mujoco", output.getvalue())
        self.assertIn("test suite was not started", output.getvalue())
        run.assert_not_called()

    def test_cli_from_another_directory_fails_early_with_actual_runtime(self):
        environment = {**os.environ, "DEXLAB_MUJOCO_PROFILE": "unknown", "PYTHONPATH": "/old/source"}
        result = subprocess.run([sys.executable, str(ROOT / "scripts/run_tests.py")],
                                cwd="/tmp", env=environment, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown MuJoCo compatibility profile", result.stderr)
        self.assertIn(str(ROOT / "src/dexlab"), result.stdout)
        self.assertNotIn("Ran ", result.stderr)
