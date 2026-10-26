"""Exercise real Git input preparation without downloading or executing a policy."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "amp_inputs", Path(__file__).resolve().parents[1] / "demos/amp-box-lift/fetch_source.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class AmpInputTests(unittest.TestCase):
    def test_changed_bytes_are_rejected_even_when_the_size_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weight.pt"
            path.write_bytes(b"abcd")
            expected = hashlib.sha1(b"blob 4\0abcd").hexdigest()
            accepted = entry.inspect_input(path, 4, expected)
            self.assertEqual(accepted["sha256"], hashlib.sha256(b"abcd").hexdigest())
            path.write_bytes(b"abce")
            with self.assertRaisesRegex(ValueError, "Git identity"):
                entry.inspect_input(path, 4, expected)

    def test_fresh_sparse_checkout_preserves_the_exact_commit_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "upstream"
            repo.mkdir()

            def git(*arguments):
                return subprocess.check_output(["git", "-C", str(repo), *arguments], text=True).strip()

            git("init", "--quiet")
            git("config", "user.name", "Input fixture")
            git("config", "user.email", "fixture@example.invalid")
            for name, payload in {"uv.lock": "version=1", "models/dualarm.pt": "fixture", "excluded.txt": "exclude"}.items():
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(payload)
            git("add", ".")
            git("commit", "--quiet", "-m", "fixture")
            commit = git("rev-parse", "HEAD")
            blob = git("rev-parse", "HEAD:models/dualarm.pt")
            output = root / "prepared"
            with patch.object(entry, "REPOSITORY", str(repo)), patch.object(entry, "COMMIT", commit), \
                    patch.object(entry, "INPUTS", {"models/dualarm.pt": (7, blob)}), \
                    patch.object(entry.shutil, "disk_usage", return_value=SimpleNamespace(free=60 * 1024**3)), \
                    patch.object(sys, "argv", ["fetch_source", str(output)]):
                entry.main()
                with self.assertRaises(FileExistsError):
                    entry.main()
            manifest = json.loads((output / "inputs.json").read_text())
            self.assertEqual(manifest["commit"], commit)
            self.assertEqual(manifest["inputs"]["models/dualarm.pt"]["git_blob"], blob)
            self.assertFalse((output / "source/excluded.txt").exists())
            self.assertEqual(manifest["native_qualification"], "not run")


if __name__ == "__main__":
    unittest.main()
