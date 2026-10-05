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
    def test_failed_verification_prevents_commit_and_push(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".autoresearch/worktrees/issue-1").mkdir(parents=True)
            summary = root / "review.md"
            summary.write_text("Concrete change and validation evidence")
            with (
                patch.object(module, "ROOT", root),
                patch.object(module, "source_tree", return_value="a" * 40),
                patch.object(module, "authorized_issue", return_value=issue(1)),
                patch.object(
                    module, "run", return_value="autoresearch/issue-1"
                ) as runner,
                patch.object(
                    module,
                    "check",
                    side_effect=subprocess.CalledProcessError(1, "physics"),
                ),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    module.submit(1, summary)
                self.assertEqual(runner.call_count, 1)
                self.assertEqual(
                    runner.call_args.args[:3], ("git", "branch", "--show-current")
                )

    def test_failed_remote_verification_prevents_commit_and_push(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".autoresearch/worktrees/issue-1").mkdir(parents=True)
            summary = root / "review.md"
            summary.write_text("Concrete change and validation evidence")
            with (
                patch.object(module, "ROOT", root),
                patch.object(module, "source_tree", return_value="a" * 40),
                patch.object(module, "authorized_issue", return_value=issue(1)),
                patch.object(
                    module, "run", return_value="autoresearch/issue-1"
                ) as runner,
                patch.object(
                    module,
                    "check_remote",
                    side_effect=subprocess.CalledProcessError(1, "physics"),
                ),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    module.submit(1, summary, "worker:/checkout")
                self.assertEqual(runner.call_count, 1)
                self.assertEqual(
                    runner.call_args.args[:3], ("git", "branch", "--show-current")
                )

    def test_revoked_authorization_during_remote_gate_prevents_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".autoresearch/worktrees/issue-1").mkdir(parents=True)
            summary = root / "review.md"
            summary.write_text("Concrete change")
            with (patch.object(module, "ROOT", root),
                  patch.object(module, "source_tree", return_value="a" * 40),
                  patch.object(module, "run", return_value="autoresearch/issue-1") as runner,
                  patch.object(module, "check_remote"),
                  patch.object(module, "authorized_issue",
                               side_effect=[issue(1), SystemExit("approval revoked")])):
                with self.assertRaisesRegex(SystemExit, "approval revoked"):
                    module.submit(1, summary, "worker:/checkout")
                self.assertEqual(runner.call_count, 1)


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
