"""Audit whether a visual target mask acts as a task-progress signal.

This module is deliberately offline. It transforms recorded masks and ROIs; it
does not read physical state, score task success, or feed a policy.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Any, Iterable, Literal

import numpy as np

Perturbation = Literal["baseline", "dropout", "false-box", "delay", "occlusion"]
STAGES = ("pre-contact", "contact-to-lift", "lift-to-success", "post-success")


@dataclass(frozen=True)
class MaskRecord:
    frame: int
    native_time_s: float
    mask: np.ndarray
    roi: tuple[int, int, int, int]


def _mask(mask: np.ndarray) -> np.ndarray:
    values = np.asarray(mask)
    if values.ndim != 2:
        raise ValueError("mask must be a 2D array")
    return values != 0


def _roi_slice(roi: tuple[int, int, int, int], shape: tuple[int, int]) -> tuple[slice, slice]:
    x1, y1, x2, y2 = roi
    height, width = shape
    x1, x2 = max(0, min(x1, width)), max(0, min(x2, width))
    y1, y2 = max(0, min(y1, height)), max(0, min(y2, height))
    if x1 >= x2 or y1 >= y2:
        raise ValueError(f"empty ROI after clipping: {roi}")
    return slice(y1, y2), slice(x1, x2)


def mask_area_fraction(mask: np.ndarray) -> float:
    return float(_mask(mask).sum() / mask.size)


def roi_overlap_fraction(mask: np.ndarray, roi: tuple[int, int, int, int]) -> float:
    values = _mask(mask)
    count = int(values.sum())
    if count == 0:
        return 0.0
    return float(values[_roi_slice(roi, values.shape)].sum() / count)


def _occupy_right_fraction(mask: np.ndarray, fraction: float) -> np.ndarray:
    if not 0 < fraction < 1:
        raise ValueError("occlusion fraction must be between 0 and 1")
    occupied = _mask(mask)
    rows, columns = np.nonzero(occupied)
    if len(columns) == 0:
        return occupied
    width = int(columns.max() - columns.min() + 1)
    boundary = int(columns.min() + round(width * (1.0 - fraction)))
    result = occupied.copy()
    result[:, boundary:] = False
    return result


def _false_box(mask: np.ndarray, roi: tuple[int, int, int, int]) -> np.ndarray:
    values = _mask(mask).copy()
    view = values[_roi_slice(roi, values.shape)]
    height, width = view.shape
    box_height = max(4, height // 2)
    box_width = max(6, width // 2)
    y1 = max(0, (height - box_height) // 2)
    x1 = max(0, (width - box_width) // 2)
    view[y1 : y1 + box_height, x1 : x1 + box_width] = True
    return values


def perturb(
    records: list[MaskRecord],
    kind: Perturbation,
    *,
    dropout_period: int = 20,
    dropout_offset: int = 15,
    delay_frames: int = 3,
    occlusion_fraction: float = 0.4,
) -> list[MaskRecord]:
    if dropout_period <= 0:
        raise ValueError("dropout_period must be positive")
    if delay_frames < 0:
        raise ValueError("delay_frames cannot be negative")
    by_frame = {record.frame: record for record in records}
    output: list[MaskRecord] = []
    for record in records:
        mask = _mask(record.mask).copy()
        if kind == "baseline":
            pass
        elif kind == "dropout":
            if record.frame % dropout_period == dropout_offset:
                mask[:] = False
        elif kind == "false-box":
            mask = _false_box(mask, record.roi)
        elif kind == "delay":
            source = by_frame.get(record.frame - delay_frames)
            mask = _mask(source.mask).copy() if source is not None else np.zeros_like(mask)
        elif kind == "occlusion":
            mask = _occupy_right_fraction(mask, occlusion_fraction)
        else:
            raise ValueError(f"unknown perturbation: {kind}")
        output.append(
            MaskRecord(
                frame=record.frame,
                native_time_s=record.native_time_s,
                mask=mask,
                roi=record.roi,
            )
        )
    return output


def stage_for_time(
    native_time_s: float,
    *,
    first_contact_s: float,
    first_lift_s: float,
    first_success_s: float,
) -> str:
    if not first_contact_s <= first_lift_s <= first_success_s:
        raise ValueError("event times must satisfy contact <= lift <= success")
    if native_time_s < first_contact_s:
        return "pre-contact"
    if native_time_s < first_lift_s:
        return "contact-to-lift"
    if native_time_s < first_success_s:
        return "lift-to-success"
    return "post-success"


def _rank_auc(negative: Iterable[float], positive: Iterable[float]) -> float | None:
    neg = list(negative)
    pos = list(positive)
    if not neg or not pos:
        return None
    wins = sum(
        1.0 if p > n else 0.5 if p == n else 0.0
        for n in neg
        for p in pos
    )
    return float(wins / (len(neg) * len(pos)))


def summarize(
    records: list[MaskRecord],
    *,
    first_contact_s: float,
    first_lift_s: float,
    first_success_s: float,
    sample_stride: int,
    source_perturbation: Perturbation,
) -> dict[str, Any]:
    if sample_stride <= 0:
        raise ValueError("sample_stride must be positive")
    sampled = [record for record in records if record.frame % sample_stride == 0]
    stage_values: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"area": [], "roi_overlap": []}
    )
    samples = []
    previously_present = False
    missed = absent = false_boxes = delayed = 0
    for record in sampled:
        area = mask_area_fraction(record.mask)
        overlap = roi_overlap_fraction(record.mask, record.roi)
        stage = stage_for_time(
            record.native_time_s,
            first_contact_s=first_contact_s,
            first_lift_s=first_lift_s,
            first_success_s=first_success_s,
        )
        stage_values[stage]["area"].append(area)
        stage_values[stage]["roi_overlap"].append(overlap)
        present = bool(_mask(record.mask).any())
        if not present:
            absent += 1
        if source_perturbation == "dropout" and previously_present and not present:
            missed += 1
        if source_perturbation == "false-box":
            false_boxes += 1
        if source_perturbation == "delay":
            delayed += 1
        previously_present = present
        samples.append(
            {
                "frame": record.frame,
                "native_time_s": round(record.native_time_s, 6),
                "stage": stage,
                "mask_area_fraction": round(area, 6),
                "roi_overlap_fraction": round(overlap, 6),
                "target_mask_present": present,
            }
        )
    stages = {}
    for stage in STAGES:
        areas = stage_values[stage]["area"]
        overlaps = stage_values[stage]["roi_overlap"]
        stages[stage] = {
            "samples": len(areas),
            "median_area_fraction": round(float(median(areas)), 6) if areas else None,
            "median_roi_overlap": round(float(median(overlaps)), 6) if overlaps else None,
        }
    pre = stage_values["pre-contact"]["roi_overlap"]
    post = [
        value
        for stage in STAGES[1:]
        for value in stage_values[stage]["roi_overlap"]
    ]
    auc = _rank_auc(pre, post)
    areas = [sample["mask_area_fraction"] for sample in samples]
    return {
        "perturbation": source_perturbation,
        "sample_count": len(samples),
        "missed_detections": missed,
        "mask_absent_samples": absent,
        "false_boxes": false_boxes,
        "delay_frames": 3 if source_perturbation == "delay" else 0,
        "delayed_samples": delayed,
        "mean_mask_area_fraction": round(float(np.mean(areas)), 6),
        "precontact_vs_postcontact_auc": round(auc, 6) if auc is not None else None,
        "stages": stages,
        "samples": samples,
    }


def first_lost_stage(
    baseline: dict[str, Any],
    perturbed: dict[str, Any],
    *,
    tolerance: float = 0.05,
) -> str:
    for stage in STAGES:
        base = baseline["stages"][stage]["median_roi_overlap"]
        changed = perturbed["stages"][stage]["median_roi_overlap"]
        if base is None or changed is None:
            continue
        if abs(base - changed) > tolerance:
            return stage
    return "none"
