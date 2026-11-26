import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "research_intake", Path(__file__).parents[1] / "scripts/research_intake.py"
)
intake = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(intake)


def payload(discussion=388, decision="pilot"):
    return {
        "schema_version": 1,
        "discussion": discussion,
        "slug": "robodojo-simulator-audit",
        "title": "RoboDojo simulator-integrity audit",
        "decision": decision,
        "summary": "Audit one existing record before changing policy or backend.",
        "current_work_impact": "Adds a candidate preflight; no mainline replacement.",
        "candidates": [] if decision in {"watch", "reject"} else [{
            "slug": "bread-slip-integrity-preflight",
            "kind": "experiment",
            "goal": "Audit one existing RoboDojo bread-slip record.",
            "entrypoints": [
                "docs/evidence/robodojo-bread-slip/layout-011-root-cause.json",
                "docs/evidence/robodojo-bread-slip/contact-escape-v67.json",
            ],
            "first_slice": "Produce four evidence tables without fabricating missing values.",
            "acceptance": [
                "Unavailable runtime fields are marked not_recorded.",
                "Positive and negative evaluator controls are reported separately.",
            ],
            "depends_on": [243],
            "non_goals": ["Do not rerun Isaac Sim.", "Do not change scorer thresholds."],
        }],
    }


def discussion(body, number=388):
    return {
        "id": "D_kwDOExample",
        "number": number,
        "title": "Research decision",
        "body": body,
        "url": f"https://github.com/huangkiki/Dexlab/discussions/{number}",
        "comments": {"totalCount": 0, "nodes": []},
    }


def body(value):
    return (
        f"{intake.INTAKE_START}\n```json\n"
        + json.dumps(value, ensure_ascii=False, indent=2)
        + f"\n```\n{intake.INTAKE_END}"
    )


class ParseTests(unittest.TestCase):
    def test_valid_block_is_normalized(self):
        result = intake.parse_discussion_body(body(payload()), 388)
        self.assertEqual(result["slug"], "robodojo-simulator-audit")
        self.assertEqual(result["candidates"][0]["depends_on"], [243])

    def test_missing_or_duplicate_block_fails_closed(self):
        for source in ("no machine data", body(payload()) + "\n" + body(payload())):
            with self.subTest(source=source[:20]), self.assertRaises(intake.IntakeError):
                intake.parse_discussion_body(source, 388)

    def test_discussion_number_and_actionable_candidates_are_checked(self):
        mismatch = payload()
        mismatch["discussion"] = 387
        with self.assertRaisesRegex(intake.IntakeError, "must match"):
            intake.validate_payload(mismatch, 388)
        no_candidates = payload(decision="pilot")
        no_candidates["candidates"] = []
        with self.assertRaisesRegex(intake.IntakeError, "require at least one"):
            intake.validate_payload(no_candidates, 388)

    def test_watch_reject_cannot_create_execution_work(self):
        watch = payload(decision="watch")
        self.assertEqual(intake.validate_payload(watch, 388)["candidates"], [])
        invalid = copy.deepcopy(watch)
        invalid["candidates"] = payload()["candidates"]
        with self.assertRaisesRegex(intake.IntakeError, "must not contain"):
            intake.validate_payload(invalid, 388)

    def test_entrypoints_must_be_repository_relative(self):
        invalid = payload()
        invalid["candidates"][0]["entrypoints"] = ["../private/data.json"]
        with self.assertRaisesRegex(intake.IntakeError, "repository-relative"):
            intake.validate_payload(invalid, 388)


class RenderTests(unittest.TestCase):
    def test_umbrella_and_child_keep_authorization_separate(self):
        value = intake.validate_payload(payload(), 388)
        umbrella = intake.render_umbrella(
            value, "https://github.com/huangkiki/Dexlab/discussions/388"
        )
        child = intake.render_child(
            value,
            value["candidates"][0],
            42,
            "https://github.com/huangkiki/Dexlab/discussions/388",
        )
        self.assertIn(intake._umbrella_marker(value), umbrella)
        self.assertIn(intake.NON_EXECUTABLE_MARKER, umbrella)
        self.assertIn("not authorized for execution", umbrella)
        self.assertIn(intake._child_marker(42, value, value["candidates"][0]), child)
        self.assertIn("Depends on: #243", child)
        self.assertIn("scripts/autoresearch.py check", child)
        self.assertNotIn("auto:approved", child)


class SyncTests(unittest.TestCase):
    def test_issue_creation_uses_stdin_for_the_body(self):
        seen = {}

        def fake_run(*args, input=None):
            seen["body_file_arg"] = args[args.index("--body-file") + 1]
            seen["body"] = input
            return "https://github.com/huangkiki/Dexlab/issues/42"

        with patch.object(intake, "run", side_effect=fake_run):
            url = intake._create_issue("Title", "Body", ("experiment",))
        self.assertEqual(url, "https://github.com/huangkiki/Dexlab/issues/42")
        self.assertEqual(seen["body_file_arg"], "-")
        self.assertEqual(seen["body"], "Body")

    def test_watch_decision_has_no_github_side_effect(self):
        source = discussion(body(payload(decision="watch")))
        with patch.object(intake, "load_discussion", return_value=source), \
             patch.object(intake, "_project_context") as project, \
             patch.object(intake, "_find_issue") as find:
            result = intake.sync(388)
        self.assertEqual(result["action"], "none")
        project.assert_not_called()
        find.assert_not_called()

    def test_dry_run_reports_creation_without_writes(self):
        source = discussion(body(payload()))
        context = {"project_id": "P", "field_id": "F", "option_id": "T"}
        with patch.object(intake, "load_discussion", return_value=source), \
             patch.object(intake, "_project_context", return_value=context), \
             patch.object(intake, "_find_issue", return_value=None), \
             patch.object(intake, "_create_issue") as create, \
             patch.object(intake, "ensure_project_status") as project:
            result = intake.sync(388, dry_run=True)
        self.assertEqual(result["action"], "create")
        self.assertEqual(result["project_status"], "Triage")
        self.assertIn(intake._umbrella_marker(result["payload"]), result["body"])
        create.assert_not_called()
        project.assert_not_called()

    def test_closed_umbrella_is_not_silently_reopened_or_reused(self):
        source = discussion(body(payload()))
        context = {"project_id": "P", "field_id": "F", "option_id": "T"}
        existing = {
            "number": 42,
            "state": "CLOSED",
            "url": "https://github.com/huangkiki/Dexlab/issues/42",
        }
        with patch.object(intake, "load_discussion", return_value=source), \
             patch.object(intake, "_project_context", return_value=context), \
             patch.object(intake, "_find_issue", return_value=existing):
            with self.assertRaisesRegex(intake.IntakeError, "closed"):
                intake.sync(388)

    def test_promote_dry_run_does_not_add_authorization(self):
        value = intake.validate_payload(payload(), 388)
        umbrella_body = intake.render_umbrella(
            value, "https://github.com/huangkiki/Dexlab/discussions/388"
        )
        umbrella = {
            "number": 42,
            "state": "OPEN",
            "title": "[Research intake] RoboDojo simulator-integrity audit",
            "body": umbrella_body,
            "url": "https://github.com/huangkiki/Dexlab/issues/42",
            "id": "I_parent",
            "labels": [],
        }
        context = {"project_id": "P", "field_id": "F", "option_id": "TODO"}
        with patch.object(intake, "gh_json", return_value=umbrella), \
             patch.object(intake, "load_discussion", return_value=discussion(body(payload()))), \
             patch.object(intake, "_project_context", return_value=context), \
             patch.object(intake, "_find_issue", return_value=None), \
             patch.object(intake, "_create_issue") as create:
            result = intake.promote(
                umbrella=42,
                slice_slug="bread-slip-integrity-preflight",
                priority="P2",
                dry_run=True,
            )
        self.assertEqual(result["action"], "create")
        self.assertEqual(result["labels"], ["experiment", "priority:P2"])
        self.assertEqual(result["project_status"], "Todo")
        self.assertNotIn("auto:approved", result["labels"])
        create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
