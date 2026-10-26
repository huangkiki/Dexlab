"""Exercise admission and persistent pause with no real issue or worktree dispatch."""

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
    "autoresearch", Path(__file__).resolve().parents[1] / "scripts/autoresearch.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def metadata(number, *, state="OPEN", login="huangkiki", approved=True):
    return {"number": number, "state": state, "author": {"login": login},
            "labels": [{"name": s} for s in (("auto:approved", "priority:P1") if approved else ())],
            "url": f"https://github.com/huangkiki/Dexlab/issues/{number}",
            "createdAt": "2026-10-26T00:00:00Z"}


def decision(number):
    return {"allowed": True, "repository": "huangkiki/Dexlab", "issue": number,
            "author": "huangkiki", "author_id": 45757984, "reason": "author_allowlisted"}


class InstalledAuthorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "home"
        self.gate = self.home / ".codex/skills/autodev/scripts/check_issue_author.py"
        self.gate.parent.mkdir(parents=True)
        self.gate.write_text("# installed gate fixture; subprocess is mocked\n")
        for target, name, value in ((module.Path, "home", self.home), (module, "ROOT", self.base / "checkout")):
            patcher = patch.object(target, name, return_value=value) if name == "home" else patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def invoke(self, payload, returncode=0):
        result = SimpleNamespace(stdout=json.dumps(payload), returncode=returncode)
        with patch.object(module.subprocess, "run", return_value=result) as runner:
            value = module.author_admission(12)
        return value, runner

    def test_trusted_installation_is_used_in_isolated_python_not_repo_config(self):
        value, runner = self.invoke(decision(12))
        self.assertTrue(value["allowed"])
        self.assertEqual(runner.call_args.args[0], [sys.executable, "-I", str(self.gate),
                         "--repo", module.REPO, "--issue", "12"])
        self.assertEqual(runner.call_args.kwargs["cwd"], self.gate.parent)

    def test_exit_status_and_complete_numeric_identity_are_required(self):
        for payload, code in [(decision(12), 1), ({**decision(12), "allowed": False}, 0),
                              ({**decision(12), "author_id": None}, 0),
                              ({**decision(12), "author_id": "45757984"}, 0),
                              ({**decision(12), "author_id": True}, 0),
                              ({**decision(12), "repository": "other/repo"}, 0),
                              ({**decision(12), "repository": None}, 0),
                              ({**decision(12), "issue": 13}, 0), ([], 0)]:
            with self.subTest(payload=payload, code=code):
                self.assertFalse(self.invoke(payload, code)[0]["allowed"])

    def test_missing_installation_api_errors_and_invalid_output_fail_closed(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("gate", 45)):
            with patch.object(module.subprocess, "run", side_effect=error):
                self.assertFalse(module.author_admission(12)["allowed"])
        with patch.object(module.subprocess, "run", return_value=SimpleNamespace(stdout="invalid", returncode=0)):
            self.assertFalse(module.author_admission(12)["allowed"])
        self.gate.unlink()
        with patch.object(module.subprocess, "run") as runner:
            self.assertFalse(module.author_admission(12)["allowed"])
            runner.assert_not_called()

    def test_live_decision_is_not_cached(self):
        results = [SimpleNamespace(stdout=json.dumps(decision(12)), returncode=0),
                   SimpleNamespace(stdout=json.dumps({"allowed": False}), returncode=1)]
        with patch.object(module.subprocess, "run", side_effect=results) as runner:
            self.assertTrue(module.author_admission(12)["allowed"])
            self.assertFalse(module.author_admission(12)["allowed"])
        self.assertEqual(runner.call_count, 2)

    def test_repository_cannot_replace_the_installed_gate(self):
        with patch.object(module, "ROOT", self.home), patch.object(module.subprocess, "run") as runner:
            self.assertFalse(module.author_admission(12)["allowed"])
            runner.assert_not_called()


class QueueReadTests(unittest.TestCase):
    def test_approved_external_author_without_admission_cannot_be_selected(self):
        outsider = {**metadata(12, login="outside"), "body": "Depends on: none\n"}
        report = module.queue_report([outsider], [])
        self.assertIsNone(report["selected"])
        self.assertIn("author admission", str(report["excluded"]))

    def test_only_admitted_candidate_and_dependency_bodies_are_read(self):
        events = []
        rows = [metadata(12), metadata(13, login="outside"), metadata(14, state="CLOSED", approved=False),
                metadata(15, approved=False)]
        def gate(number):
            events.append(("gate", number))
            return {"allowed": False, "reason": "outside"} if number == 13 else decision(number)
        def github(*args):
            if args[:2] == ("issue", "list"):
                self.assertNotIn("body", args[-1].split(","))
                events.append(("metadata", None))
                return rows
            self.assertEqual(args[:2], ("issue", "view"))
            number = int(args[2])
            self.assertIn(("gate", number), events)
            self.assertNotIn(number, (13, 15))
            events.append(("body", number))
            return {**next(row for row in rows if row["number"] == number), "title": "trusted task",
                    "body": "Depends on: #14\n" if number == 12 else "Depends on: none\n"}
        with patch.object(module, "gh_json", side_effect=github), patch.object(module, "author_admission", side_effect=gate):
            issues = module.queue_issues()
        self.assertEqual(events, [("metadata", None), ("gate", 12), ("body", 12),
                                  ("gate", 13), ("gate", 14), ("body", 14)])
        report = module.queue_report(issues, [], integrated={14})
        self.assertEqual(report["selected"]["number"], 12)
        self.assertNotIn("body", next(item for item in issues if item["number"] == 13))

    def test_explicit_recovery_rechecks_author_before_reading_body(self):
        row = metadata(12, approved=False)
        def github(*args):
            if args[:2] == ("issue", "list"):
                return [row]
            self.fail("Rejected recovery author must not reach issue body")
        with patch.object(module, "gh_json", side_effect=github), \
                patch.object(module, "author_admission", return_value={"allowed": False}) as gate:
            module.queue_issues(target=12)
            module.queue_issues(target=12)
        self.assertEqual(gate.call_count, 2)

    def test_untrusted_dependency_cannot_be_unlocked_by_closed_or_integrated_state(self):
        rows = [{**metadata(12), "body": "Depends on: #14\n", "author_admission": decision(12)},
                metadata(14, state="CLOSED", login="outside", approved=False)]
        report = module.queue_report(rows, [], integrated={14})
        self.assertIsNone(report["selected"])
        self.assertIn("#14: author admission", str(report["excluded"]))

    def test_metadata_identity_mismatch_stops_before_body_read(self):
        with patch.object(module, "gh_json", return_value=[metadata(12, login="outside")]) as github, \
                patch.object(module, "author_admission", return_value=decision(12)):
            rows = module.queue_issues()
        self.assertEqual(github.call_count, 1)
        self.assertFalse(rows[0]["author_admission"]["allowed"])

    def test_recovery_and_submission_cannot_bypass_rejected_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".autoresearch/worktrees/issue-12").mkdir(parents=True)
            summary = root / "review.md"
            summary.write_text("Concrete change and validation plan")
            rows = [{**metadata(12), "author_admission": {"allowed": False}}]
            with patch.object(module, "ROOT", root), \
                    patch.object(module, "queue_context", return_value=(rows, [], {"integrated": set()})), \
                    patch.object(module, "check") as gate, patch.object(module, "run") as mutation:
                with self.assertRaisesRegex(SystemExit, "author admission"):
                    module.start(12)
                with self.assertRaisesRegex(SystemExit, "author admission"):
                    module.submit(12, summary)
                gate.assert_not_called()
                mutation.assert_not_called()


class PersistentPauseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / ".git").mkdir()
        for name, kwargs in (("ROOT", {"new": self.root}), ("run", {"return_value": ".git"})):
            patcher = patch.object(module, name, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_missing_state_and_legacy_marker_default_to_paused(self):
        self.assertTrue(module.dispatch_state()["paused"])
        (self.root / ".git/dexlab-dispatch-paused").touch()
        self.assertTrue(module.dispatch_state()["paused"])

    def test_explicit_state_survives_new_reader_and_is_shared_across_worktrees(self):
        self.assertFalse(module.set_dispatch(False)["paused"])
        path = self.root / ".git/dexlab-dispatch-state.json"
        self.assertEqual(json.loads(path.read_text()), {"schema_version": 1, "paused": False})
        with patch.object(module, "ROOT", self.root / "another-worktree"), \
                patch.object(module, "run", return_value=str(self.root / ".git")):
            self.assertFalse(module.dispatch_state()["paused"])
            self.assertTrue(module.set_dispatch(True)["paused"])
        self.assertTrue(module.dispatch_state()["paused"])

    def test_corrupted_or_symlinked_state_cannot_enable_dispatch_or_be_overwritten(self):
        path = self.root / ".git/dexlab-dispatch-state.json"
        for text in ('invalid', '{"schema_version":1,"paused":"false"}', '{"schema_version":1,"paused":false,"extra":1}'):
            path.write_text(text)
            self.assertTrue(module.dispatch_state()["paused"])
            with self.assertRaises(SystemExit):
                module.set_dispatch(False)
            self.assertEqual(path.read_text(), text)
        path.unlink()
        other = self.root / "other.json"
        other.write_text('{"schema_version":1,"paused":false}')
        path.symlink_to(other)
        self.assertTrue(module.dispatch_state()["paused"])
        with self.assertRaises(SystemExit):
            module.set_dispatch(False)

    def test_interactive_start_does_not_resume_automatic_dispatch(self):
        row = {**metadata(12), "body": "Depends on: none\n", "author_admission": decision(12)}
        calls = []
        def command(*args, **kwargs):
            calls.append(args)
            return "autoresearch/issue-12" if args[:2] == ("git", "branch") else None
        with patch.object(module, "authorized_issue", return_value=row), \
                patch.object(module, "queue_context", return_value=([row], [], {"paused": True})), \
                patch.object(module, "run", side_effect=command), \
                patch.object(module.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(SystemExit):
                module.start(12)
            self.assertFalse(calls)
            module.start(12, interactive=True)
        self.assertTrue(any(call[:3] == ("git", "worktree", "add") for call in calls))
        self.assertTrue(module.dispatch_state()["paused"])
        self.assertFalse((self.root / ".git/dexlab-dispatch-state.json").exists())

    def test_existing_authorized_worktree_can_recover_while_paused(self):
        row = {**metadata(12), "body": "Depends on: none\n", "author_admission": decision(12)}
        (self.root / ".autoresearch/worktrees/issue-12").mkdir(parents=True)
        with patch.object(module, "authorized_issue", return_value=row) as admission, \
                patch.object(module, "run", return_value="autoresearch/issue-12") as command:
            result = module.start(12)
        admission.assert_called_once_with(12)
        self.assertEqual(result["branch"], "autoresearch/issue-12")
        self.assertEqual(command.call_count, 1)
        self.assertEqual(command.call_args.args[:3], ("git", "branch", "--show-current"))
        self.assertTrue(module.dispatch_state()["paused"])


if __name__ == "__main__":
    unittest.main()
