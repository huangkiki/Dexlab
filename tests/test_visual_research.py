"""Prevent publication of misaligned or misattributed visual evidence."""

import copy
import shutil
import subprocess
import unittest

from scripts.build_docs import preserve_homepage_anchors
from scripts.visual_research import (
    ROOT,
    check,
    nearest_indices,
    read_bundle,
    validate_bundle,
)


class VisualEvidenceTests(unittest.TestCase):
    def test_homepage_legacy_anchors_do_not_move_to_new_sections(self):
        html = '<section id="id1"><h2>New catalogue</h2></section>'
        targets = (
            "research-findings",
            "research-diagnosis",
            "research-selection",
            "research-scope",
        )
        html += "".join(
            f'<section id="{target}"><h2>{target}</h2></section>' for target in targets
        )
        result = preserve_homepage_anchors(html)
        self.assertEqual(preserve_homepage_anchors(result), result)
        self.assertIn('id="visual-id1"', result)
        for i, target in enumerate(targets, 1):
            self.assertIn(f'<section id="{target}"><span id="id{i}"></span>', result)
            self.assertEqual(result.count(f'id="id{i}"'), 1)

    @classmethod
    def setUpClass(cls):
        cls.bundle = read_bundle(ROOT / "docs/evidence/visual/pinch-retention.json.gz")

    def test_all_published_sources_and_media_match(self):
        index = check()
        self.assertEqual(
            {c["id"] for c in index["cases"]}, {"incline", "normal", "pinch"}
        )
        self.assertEqual(len(index["cases"][0]["variants"]), 9)

    def test_replay_must_not_hide_clock_shift(self):
        data = copy.deepcopy(self.bundle)
        data["videos"][0]["frames"][50]["samples"]["dev-cap-0.4"]["time_s"] += 0.1
        with self.assertRaisesRegex(ValueError, "outside the display frame"):
            validate_bundle(data)

    def test_missing_frame_mapping_is_rejected(self):
        data = copy.deepcopy(self.bundle)
        data["videos"][0]["frames"][5]["samples"].clear()
        with self.assertRaisesRegex(ValueError, "Incomplete frame map"):
            validate_bundle(data)

    def test_wrong_source_index_and_truncated_episode_are_rejected(self):
        data = copy.deepcopy(self.bundle)
        data["videos"][0]["frames"][5]["samples"]["dev-cap-0.4"]["index"] += 4
        with self.assertRaisesRegex(ValueError, "wrong source state"):
            validate_bundle(data)
        data = copy.deepcopy(self.bundle)
        data["videos"][0]["frames"] = data["videos"][0]["frames"][:60]
        with self.assertRaisesRegex(ValueError, "complete episode"):
            validate_bundle(data)

    def test_missing_channel_or_configuration_cannot_disappear(self):
        data = copy.deepcopy(self.bundle)
        data["series"][0]["channels"].pop()
        with self.assertRaisesRegex(ValueError, "measured channel"):
            validate_bundle(data)
        data = copy.deepcopy(self.bundle)
        data["videos"].pop()
        with self.assertRaisesRegex(ValueError, "every configuration"):
            validate_bundle(data)

    def test_missing_force_units_or_epoch_is_not_a_zero_force(self):
        for field in ("unit", "epoch"):
            data = copy.deepcopy(self.bundle)
            data["series"][0]["channels"][0][field] = ""
            with self.assertRaisesRegex(ValueError, "metadata"):
                validate_bundle(data)

    def test_nonfinite_or_reversed_samples_are_rejected(self):
        for value in (float("nan"), float("inf")):
            data = copy.deepcopy(self.bundle)
            data["series"][0]["channels"][0]["points"][0][1] = value
            with self.assertRaisesRegex(ValueError, "Nonfinite"):
                validate_bundle(data)
        data = copy.deepcopy(self.bundle)
        data["series"][0]["channels"][0]["points"].reverse()
        with self.assertRaisesRegex(ValueError, "clock"):
            validate_bundle(data)

    def test_failed_pinch_remains_failed(self):
        states = {s["id"]: s["verdict"] for s in self.bundle["series"]}
        self.assertEqual(states, {"dev-cap-0.4": "fail", "dev-cap-0.8": "pass"})

    def test_nearest_source_step_without_interpolation(self):
        result = nearest_indices([0, 0.002, 0.004, 0.006], [0, 0.0031, 0.1])
        self.assertEqual(result.tolist(), [0, 2, 3])
        with self.assertRaises(ValueError):
            nearest_indices([0, 0.01, 0.01], [0.005])

    def test_scientific_failures_are_not_removed_by_display_export(self):
        data = read_bundle(ROOT / "docs/evidence/visual/incline-sliding-0.001.json.gz")
        self.assertEqual(len(data["series"]), 6)
        self.assertTrue(
            any(not s["valid"] and s["verdict"] == "invalid" for s in data["series"])
        )
        self.assertTrue(any(s["verdict"] == "fail" for s in data["series"]))

    def test_parameter_comparison_keeps_original_effective_values(self):
        data = read_bundle(ROOT / "docs/evidence/visual/normal-calibration.json.gz")
        self.assertNotEqual(
            data["series"][0]["effective_parameters"],
            data["series"][1]["effective_parameters"],
        )
        self.assertEqual([s["verdict"] for s in data["series"]], ["fail", "pass"])

    @unittest.skipUnless(
        shutil.which("node"), "Node required for browser-clock unit checks"
    )
    def test_browser_clock_and_peak_preservation(self):
        subprocess.run(
            ["node", str(ROOT / "tests/visual_replay_clock.cjs")],
            check=True,
            capture_output=True,
            text=True,
        )
