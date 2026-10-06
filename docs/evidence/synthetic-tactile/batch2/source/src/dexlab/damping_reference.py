"""Conditional tangent-law comparison, not native simulation or material fitting."""

import argparse
import json
import math


def compare_reference(loads_n, target_damping_ns_m):
    """Minimax match of c*L to a constant D over positive static preloads.

    Assumes aligned normals, pure translation, common fixed c, and elastic
    resultant L at equilibrium. It does not bound trajectory or solver error.
    """
    loads = tuple(float(load) for load in loads_n)
    target = float(target_damping_ns_m)
    if not loads or any(not math.isfinite(x) or x <= 0 for x in loads):
        raise ValueError("Require nonempty, finite, strictly positive preloads")
    if not math.isfinite(target) or target <= 0:
        raise ValueError("Require finite, strictly positive target damping")
    low, high = min(loads), max(loads)
    ratio = low / high
    coefficient = (target / high) * (2 / (1 + ratio))
    effective = [coefficient * load for load in loads]
    if not math.isfinite(coefficient) or coefficient <= 0 or any(
        not math.isfinite(value) or value <= 0 for value in effective
    ):
        raise ValueError("Inputs exceed representable positive floating-point range")
    return {
        "scope": "Conditional analytic tangent model; not a native measurement",
        "assumptions": [
            "Pure normal translation and aligned contact normals",
            "A common fixed effective coefficient at all contacts",
            "Elastic normal resultant equals positive static preload",
            "Documented damping law interpreted as F_d = c F_el v_n",
        ],
        "loads_n": list(loads),
        "target_damping_ns_m": target,
        "minimax_coefficient_s_m": coefficient,
        "effective_tangent_damping_ns_m": effective,
        "relative_tangent_errors": [value / target - 1 for value in effective],
        "minimum_worst_relative_tangent_error": (1 - ratio) / (1 + ratio),
        "limits": [
            "Not a trajectory RMS error bound or a physics-accuracy score",
            "No native per-contact law, clamping or tangent measurement verified",
            "No real-material calibration or engine ranking",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loads-n", type=float, nargs="+", default=[2, 4, 6])
    parser.add_argument("--target-damping-ns-m", type=float, default=40)
    args = parser.parse_args()
    try:
        result = compare_reference(args.loads_n, args.target_damping_ns_m)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
