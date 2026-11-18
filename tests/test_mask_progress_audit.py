import unittest

import numpy as np

from dexlab.mask_progress_audit import (
    MaskRecord,
    first_lost_stage,
    mask_area_fraction,
    perturb,
    roi_overlap_fraction,
    stage_for_time,
    summarize,
)


def record(frame, time, mask, roi=(2, 2, 4, 4)):
    return MaskRecord(frame=frame, native_time_s=time, mask=mask, roi=roi)


class MaskProgressAuditTest(unittest.TestCase):
    def test_area_and_roi_overlap_count_the_named_pixels(self):
        mask = np.zeros((10, 10), dtype=bool)
        mask[2:4, 2:4] = True
        mask[6, 6] = True
        self.assertEqual(mask_area_fraction(mask), 0.05)
        self.assertEqual(roi_overlap_fraction(mask, (0, 0, 4, 4)), 0.8)
        self.assertEqual(roi_overlap_fraction(np.zeros_like(mask), (0, 0, 4, 4)), 0.0)

    def test_stage_boundaries_are_half_open(self):
        events = dict(first_contact_s=2.0, first_lift_s=3.0, first_success_s=5.0)
        self.assertEqual(stage_for_time(1.999, **events), "pre-contact")
        self.assertEqual(stage_for_time(2.0, **events), "contact-to-lift")
        self.assertEqual(stage_for_time(3.0, **events), "lift-to-success")
        self.assertEqual(stage_for_time(5.0, **events), "post-success")

    def test_perturbations_change_only_the_selected_mask_contract(self):
        mask = np.zeros((20, 20), dtype=bool)
        mask[6:14, 6:14] = True
        records = [record(index, index / 10, mask.copy()) for index in range(20)]
        dropout = perturb(records, "dropout")
        self.assertFalse(dropout[15].mask.any())
        self.assertEqual(dropout[14].mask.sum(), mask.sum())
        false_box = perturb(records, "false-box")
        self.assertGreater(false_box[0].mask.sum(), mask.sum())
        delay = perturb(records, "delay", delay_frames=3)
        self.assertEqual(delay[2].mask.sum(), 0)
        self.assertTrue(np.array_equal(delay[3].mask, records[0].mask))
        occluded = perturb(records, "occlusion", occlusion_fraction=0.5)
        self.assertLess(occluded[0].mask.sum(), mask.sum())

    def test_summary_keeps_events_out_of_the_signal_and_reports_stage_order(self):
        records = []
        for frame in range(0, 60, 5):
            mask = np.zeros((20, 20), dtype=bool)
            if frame >= 20:
                mask[5:9, 5:9] = True
            records.append(record(frame, 1.0 + frame / 10, mask, roi=(4, 4, 10, 10)))
        summary = summarize(
            records,
            first_contact_s=3.0,
            first_lift_s=4.0,
            first_success_s=5.5,
            sample_stride=5,
            source_perturbation="baseline",
        )
        self.assertEqual(summary["sample_count"], 12)
        self.assertEqual(summary["stages"]["pre-contact"]["median_roi_overlap"], 0.0)
        self.assertEqual(summary["stages"]["post-success"]["median_roi_overlap"], 1.0)
        self.assertEqual(summary["precontact_vs_postcontact_auc"], 1.0)

    def test_first_lost_stage_uses_stage_medians(self):
        baseline = {
            "stages": {
                "pre-contact": {"median_roi_overlap": 0.0},
                "contact-to-lift": {"median_roi_overlap": 0.5},
                "lift-to-success": {"median_roi_overlap": 0.9},
                "post-success": {"median_roi_overlap": 1.0},
            }
        }
        changed = {
            "stages": {
                "pre-contact": {"median_roi_overlap": 0.0},
                "contact-to-lift": {"median_roi_overlap": 0.3},
                "lift-to-success": {"median_roi_overlap": 0.8},
                "post-success": {"median_roi_overlap": 0.9},
            }
        }
        self.assertEqual(first_lost_stage(baseline, changed), "contact-to-lift")
