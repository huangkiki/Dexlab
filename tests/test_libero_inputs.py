"""Task identity must come from pinned declarations, including non-body targets."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dexlab.libero_inputs import (
    DATASET_INDEX, SUITE_COUNTS, UPSTREAM, _source_file, _source_identity,
    bddl_identity, benchmark_language, dataset_index, task_map,
)


BDDL = b"""; A deliberately different filename is not the instruction.
(define (problem LIBERO_Tabletop_Manipulation)
  (:domain robosuite)
  (:language Open the middle layer of the drawer)
  (:fixtures table - table cabinet - wooden_cabinet)
  (:objects soup tomato - can basket - basket)
  (:regions (middle_region (:target cabinet))
            (middle_region (:target table) (:ranges ((0 0 1 1)))))
  (:obj_of_interest cabinet_middle_region)
  (:init (Close cabinet_middle_region))
  (:goal (And (Open cabinet_middle_region))))
"""


class LiberoInputTests(unittest.TestCase):
    def test_benchmark_language_is_a_separate_pinned_api_declaration(self):
        self.assertEqual(benchmark_language("pick_up_the_cream_cheese_and_place_it_in_the_basket"),
                         "pick up the cream cheese and place it in the basket")
        self.assertEqual(benchmark_language("KITCHEN_SCENE10_close_the_drawer"), "close the drawer")
        self.assertEqual(benchmark_language("LIVING_ROOM_SCENE2_put_the_bowl_on_the_table"),
                         "put the bowl on the table")
        self.assertNotEqual(benchmark_language("open_the_middle_drawer_of_the_cabinet"),
                            bddl_identity(BDDL)["language"])

    def source(self):
        suites = {suite: [f"task_{n}" for n in range(count)]
                  for suite, count in SUITE_COUNTS.items()}
        return suites, ("unrelated = {'do_not_use': []}\nlibero_task_map = "
                        + repr(suites)).encode()

    def test_reads_named_literal_not_first_assignment_or_executable_code(self):
        expected, raw = self.source()
        self.assertEqual(task_map(raw), expected)
        with self.assertRaises(ValueError):
            task_map(b"libero_task_map = __import__('os').system('exit 1')")
        with self.assertRaisesRegex(ValueError, "one literal"):
            task_map(raw + b"\nlibero_task_map = {}")

    def test_extra_missing_duplicate_and_unsafe_tasks_are_rejected(self):
        original, _ = self.source()
        mutations = []
        extra = copy.deepcopy(original); extra["libero_100"] = ["extra"]; mutations.append(extra)
        missing = copy.deepcopy(original); missing["libero_90"].pop(); mutations.append(missing)
        duplicate = copy.deepcopy(original); duplicate["libero_goal"][1] = "task_0"; mutations.append(duplicate)
        unsafe = copy.deepcopy(original); unsafe["libero_goal"][0] = "../escape"; mutations.append(unsafe)
        for suites in mutations:
            with self.subTest(suites=suites.keys()), self.assertRaises(ValueError):
                task_map(("libero_task_map = " + repr(suites)).encode())

    def test_articulated_interest_resolves_to_region_without_becoming_a_body(self):
        identity = bddl_identity(BDDL)
        self.assertEqual(identity["problem"], "libero_tabletop_manipulation")
        self.assertEqual(identity["language"], "open the middle layer of the drawer")
        self.assertEqual(identity["objects_of_interest"], ["cabinet_middle_region"])
        self.assertNotIn("cabinet_middle_region", identity["objects"])
        self.assertEqual(identity["regions"]["cabinet_middle_region"]["target"], "cabinet")
        self.assertEqual(identity["regions"]["table_middle_region"]["target"], "table")
        self.assertEqual(identity["goal"], ["and", ["open", "cabinet_middle_region"]])

    def test_multiple_objects_and_goal_predicates_are_all_preserved(self):
        raw = BDDL.replace(b"(:obj_of_interest cabinet_middle_region)",
                           b"(:obj_of_interest soup tomato basket)")
        raw = raw.replace(b"(And (Open cabinet_middle_region))",
                          b"(And (In soup basket) (In tomato basket))")
        identity = bddl_identity(raw)
        self.assertEqual(identity["objects"], {"soup": "can", "tomato": "can", "basket": "basket"})
        self.assertEqual(identity["objects_of_interest"], ["soup", "tomato", "basket"])
        self.assertEqual(identity["goal"], ["and", ["in", "soup", "basket"], ["in", "tomato", "basket"]])

    def test_unused_undeclared_region_is_retained_and_flagged_like_official_goal_files(self):
        raw = BDDL.replace(b"(:regions", b"(:regions (unused (:target absent_body))")
        identity = bddl_identity(raw)
        self.assertEqual(identity["unresolved_region_targets"], ["absent_body_unused"])
        self.assertFalse(identity["regions"]["absent_body_unused"]["target_declared"])
        self.assertNotIn("absent_body", identity["objects"])
        with self.assertRaisesRegex(ValueError, "undeclared entity"):
            bddl_identity(raw.replace(b"(Open cabinet_middle_region)", b"(Open absent_body_unused)"))

    def test_malformed_declarations_do_not_become_partial_valid_identities(self):
        cases = [BDDL[:-3], BDDL + b")", BDDL + BDDL,
                 BDDL.replace(b"(:domain robosuite)", b"(:domain other)"),
                 BDDL.replace(b"(:target cabinet)", b"(:target missing)"),
                 BDDL.replace(b"(:target cabinet)", b"(:target cabinet) (:target cabinet)"),
                 BDDL.replace(b"(:obj_of_interest cabinet_middle_region)", b"(:obj_of_interest absent)"),
                 BDDL.replace(b"soup tomato - can", b"soup soup - can"),
                 BDDL.replace(b"(:goal", b"(:domain robosuite) (:goal"),
                 BDDL.replace(b"(Open cabinet_middle_region)", b"(Open missing)"),
                 BDDL.replace(b"(Open cabinet_middle_region)", b"Open"),
                 BDDL.replace(b"(Open cabinet_middle_region)", b"()")]
        for raw in cases:
            with self.subTest(raw=raw[-60:]), self.assertRaises(ValueError):
                bddl_identity(raw)

    def test_pinned_metadata_keeps_all_130_files_and_real_byte_denominator(self):
        files = dataset_index()
        self.assertEqual(len(files), 130)
        self.assertEqual(sum(row["bytes"] for row in files.values()), 100442942572)
        self.assertEqual({suite: sum(path.startswith(suite + "/") for path in files)
                          for suite in SUITE_COUNTS}, SUITE_COUNTS)

    def test_even_plausible_metadata_mutations_fail_frozen_digest(self):
        data = json.loads(DATASET_INDEX.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.json"
            for field, value in (("revision", "0" * 40), ("schema_version", 2)):
                changed = copy.deepcopy(data); changed[field] = value
                path.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, "metadata changed"):
                    dataset_index(path)
            data["files"][0]["sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "metadata changed"):
                dataset_index(path)

    def test_source_requires_exact_revision_and_no_tracked_modifications(self):
        with patch("dexlab.libero_inputs.subprocess.check_output", side_effect=[UPSTREAM, ""]):
            _source_identity(Path("not-executed"))
        for output in (["0" * 40], [UPSTREAM, " M task.bddl"]):
            with patch("dexlab.libero_inputs.subprocess.check_output", side_effect=output):
                with self.assertRaises(ValueError):
                    _source_identity(Path("not-executed"))

    def test_source_path_cannot_escape_through_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"; root.mkdir()
            outside = Path(temporary) / "outside"; outside.write_bytes(b"outside")
            (root / "aliased").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes"):
                _source_file(root, "aliased")


if __name__ == "__main__":
    unittest.main()
