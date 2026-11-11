"""Exercise the workflow's actual change filter against real Git histories."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


class FrontendSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        workflow = Path(__file__).resolve().parents[1] / ".github/workflows/docs.yml"
        steps = yaml.safe_load(workflow.read_text())["jobs"]["build"]["steps"]
        self.script = next(step["run"] for step in steps if step.get("id") == "frontend")
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.root / "README.md").write_text("initial\n")
        (self.root / "web").mkdir()
        (self.root / "web/app.ts").write_text("initial\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def selected(self, *, event="pull_request", base=None):
        output = self.root / "output"
        output.write_text("")
        subprocess.run(["bash", "-e", "-o", "pipefail", "-c", self.script], cwd=self.root,
                       env={**os.environ, "EVENT": event, "BASE": self.base if base is None else base,
                            "GITHUB_OUTPUT": str(output)}, check=True)
        return output.read_text().strip() == "test=true"

    def test_docs_only_pr_and_main_push_skip_frontend_regressions(self):
        (self.root / "README.md").write_text("revised\n")
        self.git("commit", "-qam", "docs")
        self.assertFalse(self.selected())
        self.assertFalse(self.selected(event="push"))

    def test_frontend_change_and_rename_out_of_web_run_regressions(self):
        self.git("mv", "web/app.ts", "archived.ts")
        self.git("commit", "-qm", "rename")
        self.assertTrue(self.selected())

    def test_workflow_change_runs_regressions(self):
        path = self.root / ".github/workflows/docs.yml"
        path.parent.mkdir(parents=True)
        path.write_text("changed workflow\n")
        self.git("add", ".github")
        self.git("commit", "-qm", "workflow")
        self.assertTrue(self.selected())

    def test_manual_unknown_and_initial_base_run_regressions(self):
        self.assertTrue(self.selected(event="workflow_dispatch"))
        self.assertTrue(self.selected(base="0" * 40))
        self.assertTrue(self.selected(base=""))
