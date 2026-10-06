"""Force/COM-speed diagnostics for the non-tipping planar fixture.

This does not estimate static friction or material-point slip. Native force is
from the completed solve; velocity uses its bracketing actual states. Missing
coverage cannot become a zero-friction measurement. Existing physics acceptance
remains separate and unchanged.
"""

import numpy as np

from dexlab.contact_plane import score


SPEED_EDGES_M_S = (0.0001, 0.001, 0.01, 0.05, 0.1, 0.3)
MIN_NORMAL_WEIGHT_FRACTION = 0.01


def diagnose(case, data):
    """Bin signed resisting force / positive normal force by midpoint COM speed.

    Exclude low-load, near-rest and direction-crossing intervals from the ratio,
    retaining their counts. A negative ratio means force assists translation.
    The translational work proxy excludes rotation and is not contact energy.
    """
    physical = score(case, data)
    result = {
        "status": "incomplete",
        "physical_acceptance": physical,
        "scope": "Planar resultant force versus COM speed; not static friction or material slip",
        "force_epoch": "Completed solve with bracketing pre/post-step actual COM velocities",
        "speed_edges_m_s": list(SPEED_EDGES_M_S),
        "minimum_normal_weight_fraction": MIN_NORMAL_WEIGHT_FRACTION,
        "bins": [],
    }
    checks = physical["checks"]
    required = (
        "complete_shapes", "finite_states_and_forces", "complete_contact_coverage",
        "native_steps_completed", "uniform_time_grid", "unit_quaternions",
    )
    if not all(checks.get(name, False) for name in required):
        return result

    before = data["velocity"][:-1, :2]
    after = data["velocity"][1:, :2]
    midpoint = (before + after) / 2
    speed = np.linalg.norm(midpoint, axis=1)
    force = data["contact_force"]
    loaded = force[:, 2] > MIN_NORMAL_WEIGHT_FRACTION * case.mass * case.gravity
    crossing = np.einsum("ij,ij->i", before, after) < 0
    moving = speed >= SPEED_EDGES_M_S[0]
    selected = loaded & moving & ~crossing
    power = np.einsum("ij,ij->i", force[:, :2], midpoint)
    ratio = np.full(case.steps, np.nan)
    ratio[selected] = -power[selected] / speed[selected] / force[selected, 2]
    result.update(
        status="available",
        reference_applicable=all(checks.get(k, False) for k in (
            "initially_level_reference_applicable", "no_tipping_reference_applicable",
            "no_transverse_drift", "surface_contact_geometry",
        )),
        interval_counts={
            "total": case.steps,
            "selected": int(selected.sum()),
            "not_loaded": int((~loaded).sum()),
            "below_speed_floor": int((loaded & ~moving).sum()),
            "direction_crossing": int((loaded & moving & crossing).sum()),
        },
        # These are disjoint categories: selected + the three exclusions = total.
        translational_contact_work_proxy_j=float(power.sum() * case.timestep),
        sampled_contact_assisting_translation_duration_s=float(
            np.count_nonzero(selected & (power > 0)) * case.timestep
        ),
    )
    for i, low in enumerate(SPEED_EDGES_M_S):
        high = SPEED_EDGES_M_S[i + 1] if i + 1 < len(SPEED_EDGES_M_S) else None
        mask = selected & (speed >= low)
        if high is not None:
            mask &= speed < high
        values = ratio[mask]
        result["bins"].append({
            "speed_lower_m_s": low,
            "speed_upper_m_s": high,
            "count": int(mask.sum()),
            "sample_duration_s": float(mask.sum() * case.timestep),
            "resisting_force_ratio_median": float(np.median(values)) if len(values) else None,
            "resisting_force_ratio_range": [float(values.min()), float(values.max())]
            if len(values) else None,
        })
    return result


def main():
    """Read an existing archive; do not launch physics or rewrite its verdict."""
    import argparse
    import json
    from pathlib import Path

    from dexlab.contact_plane import PlaneCase
    from dexlab.contact_plane_native import verify

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    receipt = json.loads((args.directory / "run.json").read_text())
    with np.load(args.directory / "states.npz", allow_pickle=False) as saved:
        report = diagnose(PlaneCase(**receipt["case"]), dict(saved))
    report["archive_acceptance"] = verify(args.directory)
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report["archive_acceptance"]["passed"] else 1)


if __name__ == "__main__":
    main()
