"""Check the recorded rope and palm geometry without importing libuipc."""

import argparse
import json
from pathlib import Path

import numpy as np

HOLD_START = 1.6
HOLD_END = 2.0
SAMPLE_X = np.linspace(-0.17, 0.17, 9)


def is_single_loop(edges, count):
    if count < 3 or edges.shape != (count, 2) or not np.issubdtype(edges.dtype, np.integer):
        return False
    if int(edges.min()) < 0 or int(edges.max()) >= count:
        return False
    neighbors = [[] for _ in range(count)]
    for a, b in edges:
        if a == b or b in neighbors[a]:
            return False
        neighbors[a].append(b)
        neighbors[b].append(a)
    if any(len(adjacent) != 2 for adjacent in neighbors):
        return False
    visited, pending = {0}, [0]
    while pending:
        for node in neighbors[pending.pop()]:
            if node not in visited:
                visited.add(node)
                pending.append(node)
    return len(visited) == count


def strand_sections(points, edges):
    left, right = (points[edges[:, end]] for end in (0, 1))
    sections = []
    for x in SAMPLE_X:
        crossing = (left[:, 0] < x) != (right[:, 0] < x)
        if np.count_nonzero(crossing) != 2:
            return None
        a, b = left[crossing], right[crossing]
        fraction = (x - a[:, 0]) / (b[:, 0] - a[:, 0])
        intersections = a[:, 1:] + fraction[:, None] * (b[:, 1:] - a[:, 1:])
        sections.append(intersections[intersections[:, 0].argsort()])
    return np.asarray(sections)


def evaluate(record):
    positions, transforms = record["positions"], record["transforms"]
    edges, times = record["edges"], record["times"]
    complete = (
        positions.ndim == 3 and positions.shape[2] == 3 and len(positions) == 241
        and transforms.shape == (241, 2, 4, 4)
        and times.shape == (241,) and np.allclose(times, np.arange(241) / 120)
        and np.isfinite(positions).all() and np.isfinite(transforms).all()
    )
    if not complete or not is_single_loop(edges, positions.shape[1]):
        return {"passed": False, "reason": "incomplete native record or invalid closed-loop topology"}

    edge_lengths = np.linalg.norm(positions[:, edges[:, 1]] - positions[:, edges[:, 0]], axis=-1)
    if np.any(edge_lengths[0] <= 0):
        return {"passed": False, "reason": "zero-length rest edge"}
    max_strain = float(np.max(np.abs(edge_lengths / edge_lengths[0] - 1)))
    hold = (HOLD_START <= times) & (times <= HOLD_END)
    palm_x = transforms[:, :, 0, 3]
    span = palm_x[hold, 1] - palm_x[hold, 0]
    min_wrap = float(np.min(np.column_stack((
        palm_x[hold, 0] - positions[hold, :, 0].min(axis=1),
        positions[hold, :, 0].max(axis=1) - palm_x[hold, 1],
    ))))
    sections = [strand_sections(frame, edges) for frame in positions[hold]]
    double_strands = all(section is not None for section in sections)
    separation_min = separation_max = chord_error = None
    if double_strands:
        sections = np.stack(sections)
        gap = sections[:, :, 1, 0] - sections[:, :, 0, 0]
        separation_min, separation_max = float(gap.min()), float(gap.max())
        ratio = np.linspace(0.0, 1.0, len(SAMPLE_X))[None, :, None, None]
        chord = sections[:, :1] + ratio * (sections[:, -1:] - sections[:, :1])
        chord_error = float(np.linalg.norm(sections - chord, axis=-1).max())
    checks = {
        "guide_span": bool(np.min(span) >= 0.44),
        "rope_extends_past_both_guide_centers": min_wrap >= 0.018,
        "two_strands": double_strands,
        "strand_separation": double_strands and 0.045 <= separation_min <= separation_max <= 0.100,
        "strand_straightness": double_strands and chord_error <= 0.006,
        "max_edge_strain": max_strain <= 0.10,
    }
    return {
        "passed": all(checks.values()), "checks": checks, "frames": len(times),
        "hold_frames": int(hold.sum()), "guide_contact": bool(record["guide_contact"]),
        "min_guide_span_m": float(span.min()), "min_outside_guide_centers_m": min_wrap,
        "strand_separation_range_m": [separation_min, separation_max],
        "max_strand_chord_error_m": chord_error, "max_abs_edge_strain": max_strain,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trajectory", type=Path)
    args = parser.parse_args()
    with np.load(args.trajectory) as record:
        result = evaluate(record)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
