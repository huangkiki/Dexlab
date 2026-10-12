import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "autoresearch", Path(__file__).parents[1] / "scripts/autoresearch.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def issue(number, state="OPEN", labels=("auto:approved", "priority:P1"),
          dependencies="none", created_at=None):
    return {
        "number": number,
        "state": state,
        "labels": [{"name": label} for label in labels],
        "body": f"Depends on: {dependencies}\n",
        "createdAt": created_at or f"2026-09-30T00:00:{number:02d}Z",
        "title": f"Task {number}",
    }


class QueueTest(unittest.TestCase):
    def test_pythonpath_cannot_disguise_an_editable_install_in_another_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'dexlab').mkdir()
            (root / 'dexlab/__init__.py').write_text('')

            def preflight(*command, **kwargs):
                if command[0] != sys.executable:
                    self.fail('Wrong installed checkout reached the expensive gate')
                return subprocess.run(command, cwd=kwargs['cwd'], check=True, capture_output=True)

            environment = {'SUPERDEX_PYTHON': sys.executable, 'PYTHONPATH': directory,
                           'DEXLAB_MUJOCO_PROFILE': 'historical-3.11.0'}
            with patch.dict('os.environ', environment, clear=True), \
                    patch.object(module, 'run', side_effect=preflight), \
                    self.assertRaises(subprocess.CalledProcessError):
                module.check(root)

    def test_only_opted_in_and_unclaimed_issues(self):
        issues = [
            issue(1, labels=()),
            issue(2, labels=("auto:approved", "priority:P1", "needs-input")),
            issue(3, state="CLOSED"),
            issue(4),
            issue(5),
            issue(6),
        ]
        self.assertEqual(
            module.select_issue(issues, [{"headRefName": "autoresearch/issue-4"}])[
                "number"
            ],
            5,
        )

    def test_empty_queue(self):
        self.assertIsNone(module.select_issue([], []))
        self.assertIsNone(
            module.select_issue([issue(1)], [{"headRefName": "autoresearch/issue-1"}])
        )

    def test_research_and_legacy_labels_do_not_grant_authorization(self):
        for label in ("research", "autoresearch", "experiment"):
            with self.subTest(label=label):
                self.assertIsNone(module.select_issue(
                    [issue(1, labels=(label, "priority:P0"))], []))

    def test_priority_precedes_creation_order(self):
        low = issue(1, labels=("auto:approved", "priority:P2"))
        high = issue(9, labels=("auto:approved", "priority:P0"))
        self.assertEqual(module.select_issue([low, high], [])["number"], 9)

    def test_creation_order_not_number_breaks_priority_tie(self):
        self.assertEqual(module.select_issue([
            issue(1, created_at="2026-09-30T00:00:02Z"),
            issue(2, created_at="2026-09-30T00:00:01Z"),
        ], [])["number"], 2)

    def test_missing_or_conflicting_priorities_fail_closed(self):
        for labels in [("auto:approved",), ("auto:approved", "priority:P0", "priority:P1")]:
            with self.subTest(labels=labels):
                self.assertIsNone(module.select_issue([issue(1, labels=labels)], []))

    def test_both_blocker_classes_exclude_work(self):
        for blocker in ("blocked", "needs-input"):
            with self.subTest(blocker=blocker):
                self.assertIsNone(module.select_issue([issue(
                    1, labels=("auto:approved", "priority:P0", blocker))], []))

    def test_closed_dependency_requires_verified_integration(self):
        items = [issue(1, state="CLOSED"), issue(2, dependencies="#1")]
        self.assertIsNone(module.select_issue(items, []))
        self.assertEqual(module.select_issue(items, [], integrated={1})["number"], 2)

    def test_open_dependency_is_not_delivered_even_with_partial_merged_pr(self):
        report = module.queue_report([issue(1), issue(2, dependencies="#1")], [], integrated={1})
        self.assertNotIn(2, [item["number"] for item in report["eligible"]])

    def test_unknown_and_cyclic_dependencies_are_explained(self):
        for items, expected in [
            ([issue(1, dependencies="#8")], "unknown dependency #8"),
            ([issue(1, dependencies="#2"), issue(2, dependencies="#1")], "dependency cycle"),
            ([issue(1, dependencies="#1")], "dependency cycle"),
        ]:
            with self.subTest(expected=expected):
                report = module.queue_report(items, [])
                self.assertIsNone(report["selected"])
                self.assertIn(expected, " ".join(report["excluded"][0]["reasons"]))

    def test_transitive_dependencies_are_checked(self):
        items = [issue(1), issue(2, state="CLOSED", dependencies="#1"),
                 issue(3, dependencies="#2")]
        report = module.queue_report(items, [], integrated={2})
        self.assertNotIn(3, [item["number"] for item in report["eligible"]])

    def test_missing_duplicate_and_malformed_dependency_fields(self):
        for body in ("", "Depends on: #1; #2", "Depends on: #1, #1",
                     "Depends on: none\nDepends on: #2", "Depends on: #0"):
            with self.subTest(body=body):
                item = issue(3)
                item["body"] = body
                self.assertIsNone(module.select_issue([item], []))

    def test_linked_pr_on_arbitrary_branch_prevents_duplicate_claim(self):
        for association in ({"body": "Refs #12"}, {"closingIssuesReferences": [{"number": 12}]}):
            with self.subTest(association=association):
                pull = {"headRefName": "fix/cloth-audit", "state": "OPEN", **association}
                self.assertIsNone(module.select_issue([issue(12)], [pull]))

    def test_multiple_explicit_refs_are_all_claimed(self):
        self.assertEqual(module.linked_issues({"body": "Refs #12, #27"}), {12, 27})

    def test_dependency_mention_in_pr_does_not_claim_it(self):
        pull = {"headRefName": "fix/another", "body": "Depends on: #12"}
        self.assertEqual(module.select_issue([issue(12)], [pull])["number"], 12)

    def test_existing_worktree_and_closed_pr_are_distinguished(self):
        pull = {"headRefName": "autoresearch/issue-12", "state": "MERGED"}
        self.assertIsNone(module.select_issue([issue(12)], [pull], claimed={12}))
        self.assertEqual(module.select_issue([issue(12)], [pull])["number"], 12)

    def test_pause_keeps_dry_run_candidates_but_selects_no_job(self):
        report = module.queue_report([issue(12)], [], paused=True)
        self.assertIsNone(report["selected"])
        self.assertEqual(report["eligible"][0]["number"], 12)

    def test_start_preserves_existing_worktree_during_dispatch_pause(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worktree = root / ".autoresearch/worktrees/issue-12"
            worktree.mkdir(parents=True)
            marker = worktree / "uncommitted.py"
            marker.write_text("preserve me")
            with (patch.object(module, "ROOT", root),
                  patch.object(module, "authorized_issue", return_value=issue(12)),
                  patch.object(module, "run", return_value="autoresearch/issue-12"),
                  patch.object(module, "queue_context", side_effect=AssertionError("no new dispatch"))):
                result = module.start(12)
            self.assertEqual(result["worktree"], str(worktree))
            self.assertEqual(marker.read_text(), "preserve me")

    def test_start_refuses_new_worktree_during_dispatch_pause(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch.object(module, "ROOT", root),
                  patch.object(module, "authorized_issue", return_value=issue(12)),
                  patch.object(module, "queue_context", return_value=([issue(12)], [], {"paused": True})),
                  patch.object(module, "run") as runner):
                with self.assertRaises(SystemExit):
                    module.start(12)
                runner.assert_not_called()

    def test_unknown_creation_time_fails_closed(self):
        item = issue(12)
        del item["createdAt"]
        self.assertIsNone(module.select_issue([item], []))


class SubmissionTest(unittest.TestCase):
    """Exercise real branch/index/commit behavior while keeping publication offline."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.worktree = self.root / ".autoresearch/worktrees/issue-1"
        self.worktree.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Submission Test")
        self.git("config", "user.email", "submission@example.invalid")
        self.source = self.worktree / "source.py"
        self.source.write_text("initial\n")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.git("remote", "add", "origin", "git@github.com:huangkiki/Dexlab.git")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-qb", "autoresearch/issue-1")
        self.source.write_text("implementation\n")
        self.summary = self.root / "review.md"
        self.summary.write_text("Concrete change and validation evidence")
        self.pulls = []
        self.publications = []
        self.real_run = module.run
        patcher = patch.object(module, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name, kwargs in (
            ("authorized_issue", {"return_value": issue(1)}),
            ("run", {"side_effect": self.run_command}),
            ("gh_json", {"side_effect": self.github}),
            ("check", {}), ("check_remote", {}),
        ):
            patcher = patch.object(module, name, **kwargs)
            setattr(self, name + "_mock", patcher.start())
            self.addCleanup(patcher.stop)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.worktree,
                                       text=True, stderr=subprocess.PIPE).strip()

    def recover(self):
        self.git("branch", "-m", "fix/existing")
        self.git("commit", "-qam", "existing implementation")
        pull = dict(number=7, url="https://github.com/huangkiki/Dexlab/pull/7",
                    state="OPEN", body="Refs #1", closingIssuesReferences=[],
                    baseRefName="main", headRefName="fix/existing",
                    headRefOid=self.git("rev-parse", "HEAD"), isCrossRepository=False,
                    headRepository={"name": "Dexlab"}, headRepositoryOwner={"login": "huangkiki"})
        self.pulls = [pull]
        return pull

    def github(self, *args):
        if args[:2] == ("pr", "list"):
            return json.loads(json.dumps(self.pulls))
        if args[:2] == ("pr", "view"):
            return dict(self.pulls[0])
        self.fail(f"Unexpected GitHub command: {args}")

    def run_command(self, *args, **kwargs):
        if args[:2] == ("git", "push"):
            self.publications.append(args)
            if self.pulls:
                self.pulls[0]["headRefOid"] = self.git("rev-parse", "HEAD")
            return None
        if args[:2] == ("gh", "api"):
            self.assertEqual(args[2:], ("repos/huangkiki/Dexlab/pulls", "--input", "-"))
            payload = json.loads(kwargs["input"])
            self.assertEqual(payload["base"], "main")
            self.assertEqual(payload["head"], "autoresearch/issue-1")
            self.assertIn("Refs #1", payload["body"])
            self.publications.append(args)
            self.pulls = [dict(number=8, url="https://github.com/huangkiki/Dexlab/pull/8",
                               state="OPEN", baseRefName="main", headRefName=payload["head"],
                               headRefOid=self.git("rev-parse", "HEAD"))]
            return json.dumps({"html_url": self.pulls[0]["url"]})
        if args[:3] == ("gh", "pr", "edit"):
            self.assertEqual(args[3], "7")
            self.publications.append(args)
            return None
        if args[0] == "gh":
            self.fail(f"Unexpected publication command: {args}")
        return self.real_run(*args, **kwargs)

    def test_standard_submission_validates_commits_pushes_and_creates_without_git_discovery(self):
        result = module.submit(1, self.summary)
        self.check_mock.assert_called_once_with(self.worktree)
        self.assertEqual(result["headRefOid"], self.git("rev-parse", "HEAD"))
        self.assertFalse(self.git("status", "--porcelain"))
        self.assertEqual([p[:2] for p in self.publications], [("git", "push"), ("gh", "api")])

    def test_explicit_recovery_updates_same_pr_after_new_reviewed_commit(self):
        self.recover()
        self.source.write_text("review correction\n")
        self.git("commit", "-qam", "review correction")
        result = module.submit(1, self.summary, existing_pr=7)
        self.assertEqual(result["number"], 7)
        self.check_mock.assert_called_once_with(self.worktree)
        self.assertEqual([p[:2] for p in self.publications], [("git", "push"), ("gh", "pr")])

    def test_standard_existing_pr_still_commits_reviewed_changes_after_gate(self):
        pull = self.recover()
        self.git("branch", "-m", "autoresearch/issue-1")
        pull["headRefName"] = "autoresearch/issue-1"
        self.source.write_text("reviewed standard-branch correction\n")
        result = module.submit(1, self.summary)
        self.assertEqual(result["number"], 7)
        self.assertFalse(self.git("status", "--porcelain"))
        self.check_mock.assert_called_once_with(self.worktree)
        self.assertFalse(any(p[:2] == ("gh", "api") for p in self.publications))

    def test_recovery_requires_explicit_pr(self):
        self.recover()
        with self.assertRaises(SystemExit):
            module.submit(1, self.summary)
        self.check_mock.assert_not_called()
        self.assertFalse(self.publications)

    def test_recovery_rejects_wrong_remote_pr_identity_and_ambiguity_before_gate(self):
        pull = self.recover()
        for field, value in (("state", "CLOSED"), ("baseRefName", "other"),
                             ("headRefName", "another"), ("body", "Depends on: #1"),
                             ("isCrossRepository", True), ("headRepositoryOwner", {"login": "other"}),
                             ("headRepository", {"name": "other"})):
            with self.subTest(field=field):
                self.pulls = [{**pull, field: value}]
                with self.assertRaises(SystemExit):
                    module.submit(1, self.summary, existing_pr=7)
        self.pulls = [pull, {**pull, "number": 8}]
        with self.assertRaisesRegex(SystemExit, "Multiple PRs"):
            module.submit(1, self.summary, existing_pr=7)
        self.pulls = [pull]
        with self.assertRaises(SystemExit):
            module.submit(1, self.summary, existing_pr=99)
        self.check_mock.assert_not_called()
        self.assertFalse(self.publications)

    def test_wrong_fetch_or_push_destination_is_rejected(self):
        for option in ((), ("--push",)):
            with self.subTest(option=option):
                self.git("remote", "set-url", *option, "origin", "https://github.com/other/repo.git")
                with self.assertRaisesRegex(SystemExit, "Origin"):
                    module.submit(1, self.summary)
                self.git("remote", "set-url", *option, "origin", "git@github.com:huangkiki/Dexlab.git")
        self.check_mock.assert_not_called()
        self.assertFalse(self.publications)

    def test_recovery_preserves_unrelated_dirty_files_and_index(self):
        self.recover()
        other = self.worktree / "unrelated.py"
        other.write_text("preserve me\n")
        before = self.git("write-tree")
        with self.assertRaisesRegex(SystemExit, "clean, reviewed"):
            module.submit(1, self.summary, existing_pr=7)
        self.assertEqual(other.read_text(), "preserve me\n")
        self.assertEqual(self.git("write-tree"), before)
        self.check_mock.assert_not_called()
        self.assertFalse(self.publications)

    def test_recovery_requires_ancestor_of_remote_head(self):
        pull = self.recover()
        self.git("checkout", "-qb", "unrelated", "origin/main")
        self.source.write_text("different history\n")
        self.git("commit", "-qam", "different history")
        remote = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "fix/existing")
        self.pulls = [{**pull, "headRefOid": remote}]
        with self.assertRaisesRegex(SystemExit, "does not contain"):
            module.submit(1, self.summary, existing_pr=7)
        self.check_mock.assert_not_called()
        self.assertFalse(self.publications)

    def test_failed_local_and_remote_gates_prevent_commit_and_publication(self):
        initial = self.git("rev-parse", "HEAD")
        for destination, gate in ((None, self.check_mock), ("worker:/checkout", self.check_remote_mock)):
            gate.side_effect = subprocess.CalledProcessError(1, "physics")
            with self.subTest(destination=destination), self.assertRaises(subprocess.CalledProcessError):
                module.submit(1, self.summary, destination)
            self.assertEqual(self.git("rev-parse", "HEAD"), initial)
            self.assertFalse(self.publications)

    def test_failed_recovery_gate_cannot_update_existing_pr(self):
        self.recover()
        self.check_mock.side_effect = subprocess.CalledProcessError(1, "physics")
        with self.assertRaises(subprocess.CalledProcessError):
            module.submit(1, self.summary, existing_pr=7)
        self.assertFalse(self.publications)

    def test_revoked_authorization_prevents_commit_and_publication(self):
        self.authorized_issue_mock.side_effect = [issue(1), SystemExit("approval revoked")]
        initial = self.git("rev-parse", "HEAD")
        with self.assertRaisesRegex(SystemExit, "approval revoked"):
            module.submit(1, self.summary, "worker:/checkout")
        self.assertEqual(self.git("rev-parse", "HEAD"), initial)
        self.assertFalse(self.publications)

    def test_changed_source_during_gate_prevents_publication(self):
        self.check_mock.side_effect = lambda _: self.source.write_text("changed during gate\n")
        with self.assertRaisesRegex(SystemExit, "Source changed"):
            module.submit(1, self.summary)
        self.assertFalse(self.publications)

    def test_changed_branch_during_gate_prevents_publication(self):
        self.check_mock.side_effect = lambda _: self.git("checkout", "-qb", "other")
        with self.assertRaisesRegex(SystemExit, "different branch"):
            module.submit(1, self.summary)
        self.assertFalse(self.publications)

    def test_changed_pr_head_during_gate_prevents_publication(self):
        self.recover()
        self.check_mock.side_effect = lambda _: self.pulls[0].update(headRefOid="f" * 40)
        with self.assertRaisesRegex(SystemExit, "PR changed"):
            module.submit(1, self.summary, existing_pr=7)
        self.assertFalse(self.publications)

    def test_changed_commit_with_identical_tree_during_gate_is_rejected(self):
        self.recover()
        self.check_mock.side_effect = lambda _: self.git("commit", "--allow-empty", "-qm", "concurrent")
        with self.assertRaisesRegex(SystemExit, "Local commit changed"):
            module.submit(1, self.summary, existing_pr=7)
        self.assertFalse(self.publications)

    def test_wrong_pr_readback_is_rejected(self):
        original = self.github
        def wrong(*args):
            result = original(*args)
            return {**result, "baseRefName": "other"} if args[:2] == ("pr", "view") else result
        self.gh_json_mock.side_effect = wrong
        with self.assertRaisesRegex(SystemExit, "PR readback"):
            module.submit(1, self.summary)

    def test_cli_forwards_explicit_recovery_without_changing_defaults(self):
        with patch.object(module, "submit", return_value={}) as submitter:
            with patch.object(sys, "argv", ["autoresearch", "submit", "1", "--summary-file", str(self.summary),
                                             "--existing-pr", "7"]):
                module.main()
            self.assertEqual(submitter.call_args.kwargs, {"existing_pr": 7})


class VerifiedCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Queue Test")
        self.git("config", "user.email", "queue@example.invalid")
        (self.root / ".gitignore").write_text("ignored/\n")
        (self.root / "source.py").write_text("original\n")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def test_snapshot_includes_changes_and_untracked_but_preserves_index(self):
        before = self.git("write-tree")
        (self.root / "source.py").write_text("changed\n")
        (self.root / "new.py").write_text("new\n")
        ignored = self.root / "ignored"
        ignored.mkdir()
        (ignored / "runtime.py").write_text("runtime\n")
        expected = module.source_tree(self.root)
        self.assertNotEqual(expected, before)
        self.assertEqual(self.git("write-tree"), before)
        self.git("add", "-A")
        self.assertEqual(self.git("write-tree"), expected)
        (ignored / "runtime.py").write_text("runtime changed\n")
        self.assertEqual(module.source_tree(self.root), expected)

    def test_remote_gate_passes_exact_tree_and_disables_agent_forwarding(self):
        with patch.object(module, "run") as runner:
            result = module.check_remote(self.root, "worker:/checkout with space")
        self.assertEqual(result["source_tree"], module.source_tree(self.root))
        command = runner.call_args.args
        self.assertIn("ForwardAgent=no", command)
        self.assertIn("--expected-tree " + result["source_tree"], command[-1])
        self.assertIn("cd '/checkout with space'", command[-1])

    def test_remote_gate_propagates_failure(self):
        with patch.object(module, "run", side_effect=subprocess.CalledProcessError(1, "ssh")):
            with self.assertRaises(subprocess.CalledProcessError):
                module.check_remote(self.root, "worker:/checkout")

    def test_remote_gate_refuses_changed_local_tree(self):
        def change(*args, **kwargs):
            (self.root / "source.py").write_text("changed during check\n")
        with patch.object(module, "run", side_effect=change):
            with self.assertRaisesRegex(SystemExit, "Local source changed"):
                module.check_remote(self.root, "worker:/checkout")

    def test_invalid_remote_destination_fails_before_execution(self):
        with patch.object(module, "run") as runner:
            for destination in ("-oProxyCommand=bad:/tmp", "worker:relative", "worker", "worker:/a\nb"):
                with self.subTest(destination=destination), self.assertRaises(SystemExit):
                    module.check_remote(self.root, destination)
            runner.assert_not_called()

    def test_remote_entrypoint_rejects_wrong_tree_before_physics(self):
        with (patch.object(sys, "argv", ["autoresearch", "check", str(self.root),
                                        "--expected-tree", "0" * 40]),
              patch.object(module, "check") as gate):
            with self.assertRaisesRegex(SystemExit, "does not match"):
                module.main()
            gate.assert_not_called()

    def test_dependency_integration_requires_actual_base_ancestry(self):
        integrated = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", integrated)
        (self.root / "source.py").write_text("unmerged\n")
        self.git("commit", "-qam", "not integrated")
        unmerged = self.git("rev-parse", "HEAD")
        def pull(number, state="MERGED", base="main", commit=integrated):
            return {"state": state, "baseRefName": base, "mergeCommit": {"oid": commit},
                    "closingIssuesReferences": [{"number": number}]}
        pulls = [pull(1), pull(2, commit=unmerged), pull(3, base="staging"),
                 pull(4, state="OPEN"), pull(5, commit="0" * 40)]
        real_run = module.run
        def offline_run(*args, **kwargs):
            if args[:3] == ("git", "fetch", "origin"):
                return None
            return real_run(*args, **kwargs)
        with (patch.object(module, "ROOT", self.root),
              patch.object(module, "gh_json", side_effect=[[], pulls]),
              patch.object(module, "run", side_effect=offline_run)):
            _, _, context = module.queue_context()
        self.assertEqual(context["integrated"], {1})

    def manual_fixture(self):
        commit = self.git("rev-parse", "HEAD")
        entries = [{"issue": 42, "pr": 76, "merge_commit": commit,
                    "audit_url": "https://github.com/huangkiki/Dexlab/issues/42#issuecomment-123"}]
        pulls = [{"number": 76, "state": "MERGED", "baseRefName": "main",
                  "mergeCommit": {"oid": commit}, "closingIssuesReferences": []}]
        return entries, [{"number": 42, "state": "CLOSED"}], pulls

    def commit_ledger(self, entries):
        path = self.root / "docs/issue-deliveries.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(entries))
        self.git("add", "docs/issue-deliveries.json")
        self.git("commit", "-qm", "reviewed ledger", "--allow-empty")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def test_manual_delivery_restores_dependency_without_closing_keywords(self):
        entries, issues, pulls = self.manual_fixture()
        self.commit_ledger(entries)
        with patch.object(module, "ROOT", self.root):
            integrated = module.manual_integrations(issues, pulls)
        self.assertEqual(integrated, {42})
        self.assertEqual(module.select_issue(
            [issue(42, state="CLOSED"), issue(77, dependencies="#42")], [],
            integrated=integrated)["number"], 77)

    def test_manual_delivery_ignores_unmerged_working_ledger(self):
        entries, issues, pulls = self.manual_fixture()
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        (self.root / "docs").mkdir()
        (self.root / "docs/issue-deliveries.json").write_text(json.dumps(entries))
        with patch.object(module, "ROOT", self.root):
            self.assertEqual(module.manual_integrations(issues, pulls), set())
        self.commit_ledger(entries)
        (self.root / "docs/issue-deliveries.json").write_text("corrupt working copy")
        with patch.object(module, "ROOT", self.root):
            self.assertEqual(module.manual_integrations(issues, pulls), {42})

    def test_manual_delivery_rejects_stale_or_unmerged_pr_evidence(self):
        entries, issues, pulls = self.manual_fixture()
        self.commit_ledger(entries)
        for field, value in (("state", "OPEN"), ("baseRefName", "other"),
                             ("mergeCommit", {"oid": "0" * 40}), ("number", 999)):
            with self.subTest(field=field), patch.object(module, "ROOT", self.root):
                with self.assertRaisesRegex(SystemExit, "does not match"):
                    module.manual_integrations(issues, [{**pulls[0], field: value}])
        with patch.object(module, "ROOT", self.root):
            with self.assertRaisesRegex(SystemExit, "reopened"):
                module.manual_integrations([{"number": 42, "state": "OPEN"}], pulls)
            with self.assertRaisesRegex(SystemExit, "missing"):
                module.manual_integrations([], pulls)

    def test_manual_delivery_rejects_nonancestor_even_with_matching_api(self):
        entries, issues, pulls = self.manual_fixture()
        self.commit_ledger(entries)
        base = self.git("rev-parse", "HEAD")
        (self.root / "source.py").write_text("unmerged")
        self.git("commit", "-qam", "unmerged")
        other = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "--detach", base)
        entries[0]["merge_commit"] = other
        pulls[0]["mergeCommit"] = {"oid": other}
        self.commit_ledger(entries)
        with patch.object(module, "ROOT", self.root):
            with self.assertRaisesRegex(SystemExit, "not in origin/main"):
                module.manual_integrations(issues, pulls)

    def test_manual_delivery_rejects_malformed_ledger(self):
        entries, issues, pulls = self.manual_fixture()
        bad = [None, {}, [None], entries * 2,
               [{**entries[0], "issue": True}],
               [{**entries[0], "merge_commit": "not a hash"}],
               [{**entries[0], "audit_url": "https://example.com"}],
               [{**entries[0], "extra": "ignored?"}]]
        for value in bad:
            with self.subTest(value=value):
                self.commit_ledger(value)
                with patch.object(module, "ROOT", self.root):
                    with self.assertRaises(SystemExit):
                        module.manual_integrations(issues, pulls)



class ResourceGateTests(unittest.TestCase):
    def test_remote_guard_wraps_full_gate_with_private_resource_receipts(self):
        with (patch.object(module, "source_tree", return_value="a" * 40),
              patch.object(module, "run") as runner):
            module.check_remote(Path("/source"), "worker:/checkout", Path("/state"))
        command = runner.call_args.args[-1]
        self.assertIn("scripts/research_guard.py run --lock /state/window.lock", command)
        self.assertIn("--kind qualification", command)
        self.assertIn("--resource-dir /state/receipts", command)
        with patch.object(module, "run") as runner, patch.object(module, "source_tree"):
            with self.assertRaises(SystemExit):
                module.check_remote(Path("/source"), "worker:/checkout", Path("relative"))
            runner.assert_not_called()

    def test_gate_uses_explicit_interpreter_and_data_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            python = str(root / "candidate/bin/python")
            output = root / "data-output"
            with patch.dict("os.environ", {"SUPERDEX_PYTHON": python,
                                             "DEXLAB_RUN_ROOT": str(output),
                                             "DEXLAB_MUJOCO_PROFILE": "historical-3.11.0"}), \
                 patch.object(module, "run") as runner:
                result = module.check(root)
            self.assertTrue(all(Path(path).parent == output for path in result["outputs"].values()))
            self.assertTrue(any(call.args[0] == python for call in runner.call_args_list))

    def test_each_gate_preserves_old_outputs_and_measures_episode_and_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(module, "run") as runner, \
                 patch.dict("os.environ", {"DEXLAB_MUJOCO_PROFILE": "historical-3.11.0"}):
                first = module.check(root, root / "receipts")
                second = module.check(root, root / "receipts")
            self.assertNotEqual(first["run_id"], second["run_id"])
            self.assertTrue(set(first["outputs"].values()).isdisjoint(second["outputs"].values()))
            commands = [call.args for call in runner.call_args_list if "/usr/bin/time" in call.args]
            self.assertEqual(len(commands), 8)
            for run in (first, second):
                for backend in ("mujoco", "superdex"):
                    for phase in ("episode", "verify"):
                        receipt = str(root / "receipts" / f"{run['run_id']}-{backend}-{phase}.json")
                        self.assertEqual(sum(receipt in command for command in commands), 1)
                self.assertTrue((root / "receipts" / (run["run_id"] + "-outputs.json")).is_file())

    def test_candidate_gate_requires_provenance_before_running_and_checks_it_after_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict("os.environ", {"DEXLAB_MUJOCO_PROFILE": "qualification-3.14.0"}, clear=True), \
                 patch.object(module, "run") as runner:
                with self.assertRaisesRegex(ValueError, "DEXLAB_QUALIFICATION_WHEELS"):
                    module.check(root)
                runner.assert_not_called()
                with patch.dict("os.environ", {"DEXLAB_QUALIFICATION_WHEELS": str(root / "wheels")}):
                    result = module.check(root)
                self.assertEqual(runner.call_args.args[1:3], ("-m", "dexlab.apple_admission"))
                self.assertIn(result["outputs"]["mujoco"], runner.call_args.args)
                self.assertIn(result["admission"], runner.call_args.args)
