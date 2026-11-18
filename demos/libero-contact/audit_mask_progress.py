#!/usr/bin/env python3
"""Audit mask-progress signals on the published LIBERO demo-0 replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from dexlab.mask_progress_audit import (
    MaskRecord,
    first_lost_stage,
    perturb,
    summarize,
)

TARGET_COLOR_LOW = (60, 15, 80)
TARGET_COLOR_HIGH = (140, 110, 170)
TARGET_SEED = np.array([304.7, 308.8])
GRIPPER_SEED_BOX = (242, 131, 39, 44)
ROI_PADDING = 14
FPS = 20
NATIVE_TIME_ORIGIN_S = 0.25


def _target_component(
    frame: np.ndarray,
    previous: np.ndarray,
    velocity: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color = cv2.inRange(hsv, np.array(TARGET_COLOR_LOW), np.array(TARGET_COLOR_HIGH))
    color[:70] = 0
    color[:, :120] = 0
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(color)
    prediction = previous + velocity
    candidates = []
    for component in range(1, count):
        x, y, width, height, area = stats[component]
        if not (60 <= area <= 2000 and 10 <= width <= 70 and 8 <= height <= 60):
            continue
        center = centroids[component]
        distance = float(np.linalg.norm(center - prediction))
        if distance < 45:
            candidates.append((distance, component, center))
    if not candidates:
        return np.zeros(frame.shape[:2], dtype=bool), prediction, np.zeros(2)
    _, component, center = min(candidates)
    velocity = np.clip(0.5 * velocity + 0.5 * (center - previous), -15, 15)
    return labels == component, center, velocity


def _roi_from_gripper(box: tuple[float, float, float, float], shape: tuple[int, int]) -> tuple[int, int, int, int]:
    height, width = shape
    x, y, box_width, box_height = box
    return (
        max(0, round(x) - ROI_PADDING),
        max(0, round(y) - ROI_PADDING),
        min(width, round(x + box_width) + ROI_PADDING),
        min(height, round(y + box_height) + ROI_PADDING),
    )


def track_video(video: Path) -> tuple[list[MaskRecord], dict]:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {video}")
    if capture.get(cv2.CAP_PROP_FPS) != FPS:
        raise ValueError("the audit expects the published 20 fps replay")
    ok, first = capture.read()
    if not ok:
        raise ValueError("video contains no frames")
    tracker = cv2.TrackerMIL_create()
    tracker.init(first, GRIPPER_SEED_BOX)
    previous = TARGET_SEED.copy()
    velocity = np.zeros(2)
    records = []
    frame = first
    index = 0
    while ok:
        if index:
            ok, frame = capture.read()
            if not ok:
                break
        tracked, gripper_box = tracker.update(frame)
        if not tracked:
            raise ValueError(f"gripper tracker failed at frame {index}")
        mask, previous, velocity = _target_component(frame, previous, velocity)
        roi = _roi_from_gripper(gripper_box, frame.shape[:2])
        records.append(
            MaskRecord(
                frame=index,
                native_time_s=NATIVE_TIME_ORIGIN_S + index / FPS,
                mask=mask,
                roi=roi,
            )
        )
        index += 1
    capture.release()
    return records, {
        "fps": FPS,
        "native_time_origin_s": NATIVE_TIME_ORIGIN_S,
        "target_color_hsv_low": TARGET_COLOR_LOW,
        "target_color_hsv_high": TARGET_COLOR_HIGH,
        "target_seed_center_px": TARGET_SEED.tolist(),
        "gripper_seed_box_px": GRIPPER_SEED_BOX,
        "roi_padding_px": ROI_PADDING,
    }


def _events(summary: Path, demo: str) -> dict:
    data = json.loads(summary.read_text())
    matches = [
        case
        for case in data["cases"]
        if case["demo"] == demo
        and case["candidate"]["id"] == "baseline"
        and case["candidate"]["mode"] == "actions"
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one baseline record for {demo}, found {len(matches)}")
    events = matches[0]["events"]
    return {
        "first_finger_contact_s": events["first_finger_contact_s"],
        "first_lift_s": events["first_lift_s"],
        "first_native_success_s": events["first_native_success_s"],
        "first_basket_contact_s": events["first_basket_contact_s"],
        "last_finger_contact_s": events["last_finger_contact_s"],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(video: Path, summary: Path, demo: str, sample_stride: int) -> dict:
    records, tracking = track_video(video)
    events = _events(summary, demo)
    kwargs = dict(
        first_contact_s=events["first_finger_contact_s"],
        first_lift_s=events["first_lift_s"],
        first_success_s=events["first_native_success_s"],
        sample_stride=sample_stride,
    )
    reports = {}
    for kind in ("baseline", "dropout", "false-box", "delay", "occlusion"):
        perturbed = perturb(records, kind)
        reports[kind] = summarize(
            perturbed,
            source_perturbation=kind,
            **kwargs,
        )
    baseline = reports["baseline"]
    for kind, report in reports.items():
        report["first_lost_stage"] = (
            "none" if kind == "baseline" else first_lost_stage(baseline, report)
        )
        report.pop("samples")
    return {
        "schema_version": 1,
        "experiment": "mask-progress-signal-audit",
        "source": {
            "video": str(video),
            "video_sha256": _sha256(video),
            "summary": str(summary),
            "summary_sha256": _sha256(summary),
            "demo": demo,
            "published_record_only": True,
            "new_physics_run": False,
            "new_policy_run": False,
        },
        "tracking": tracking,
        "events_used_only_as_stage_labels": events,
        "signal_contract": {
            "mask_area": "target-mask pixels / image pixels",
            "roi_overlap": "target-mask pixels in gripper ROI / target-mask pixels",
            "first_lost_stage": "first stage with median ROI-overlap change greater than 0.05",
        },
        "perturbation_contract": {
            "dropout": "blank mask when frame % 20 == 15",
            "false-box": "fill the centre half of the gripper ROI",
            "delay": "use the mask from three frames earlier",
            "occlusion": "remove the right 40% of the target-mask bounding box",
        },
        "reports": reports,
        "acceptance": {
            "physical_task_success_computed": False,
            "events_are_separate_from_signal_score": True,
            "actor_input_and_acceptance_truth_separated": True,
            "new_physics_backend": False,
            "policy_training": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--demo", default="demo_0")
    parser.add_argument("--sample-stride", default=5, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.video, args.summary, args.demo, args.sample_stride)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value["first_lost_stage"] for key, value in result["reports"].items()}, indent=2))
