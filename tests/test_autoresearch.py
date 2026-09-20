import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "autoresearch", Path(__file__).parents[1] / "scripts/autoresearch.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def issue(number, state="OPEN", labels=("autoresearch",)):
    return {
        "number": number,
        "state": state,
        "labels": [{"name": label} for label in labels],
    }


class QueueTest(unittest.TestCase):
    def test_only_opted_in_and_unclaimed_issues(self):
        issues = [
            issue(1, labels=()),
            issue(2, labels=("autoresearch", "needs-input")),
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


class SubmissionTest(unittest.TestCase):
    def test_failed_verification_prevents_commit_and_push(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".autoresearch/worktrees/issue-1").mkdir(parents=True)
            summary = root / "review.md"
            summary.write_text("Concrete change and validation evidence")
            with (
                patch.object(module, "ROOT", root),
                patch.object(module, "gh_json", return_value=issue(1)),
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
