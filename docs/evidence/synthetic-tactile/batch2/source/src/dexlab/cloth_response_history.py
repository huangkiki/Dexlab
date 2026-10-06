"""Equal-time cloth response curves; not a constitutive calibration certificate."""

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from dexlab.genesis_cloth_response import score as first_step_score, surface_error


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("duration_s") != 0.02
            or record.get("repeats") != 2
        ):
            raise ValueError("Require frozen 20 ms/two-repeat protocol")
        one_step = copy.deepcopy(record)
        for case in one_step["cases"]:
            case["final"] = case["episodes"][0]["rows"][1]
        first = first_step_score(one_step)
        if not first["valid"]:
            raise ValueError(
                "First-step native protocol invalid: " + first.get("reason", "")
            )
        results = []
        for case in record["cases"]:
            mass = np.asarray(case["mass"], float)
            steps = round(0.02 / case["dt"])
            if [e["repeat"] for e in case["episodes"]] != [0, 1]:
                raise ValueError("Missing repeat")
            traces, states = [], []
            for episode in case["episodes"]:
                rows = episode["rows"]
                if [r["step"] for r in rows] != list(range(steps + 1)):
                    raise ValueError("Incomplete equal-time observations")
                p = np.asarray([r["pos"] for r in rows], float)
                v = np.asarray([r["vel"] for r in rows], float)
                if (
                    p.shape != (steps + 1, len(mass), 3)
                    or v.shape != p.shape
                    or not np.isfinite(p).all()
                    or not np.isfinite(v).all()
                ):
                    raise ValueError("Invalid response states")
                if (
                    np.max(abs(p[0] - case["initial"]["pos"])) > 1e-9
                    or np.max(abs(v[0])) > 1e-8
                ):
                    raise ValueError("Reset initial state mismatch")
                center = np.einsum("tnk,n->tk", p, mass) / mass.sum()
                curve = [
                    {
                        "time_s": i * case["dt"],
                        **surface_error(pos, case["rest"], case["faces"]),
                        "kinetic_energy_J": float(
                            0.5 * np.sum(mass[:, None] * v[i] ** 2)
                        ),
                    }
                    for i, pos in enumerate(p)
                ]
                negative_ok = bool(
                    np.max(abs(p - p[0])) <= 1e-9 and np.max(abs(v)) <= 1e-8
                )
                traces.append(
                    {
                        "repeat": episode["repeat"],
                        "curve": curve,
                        "max_center_shift_m": float(
                            np.linalg.norm(center - center[0], axis=1).max()
                        ),
                        "disabled_unchanged": negative_ok,
                    }
                )
                states.append((p, v))
            difference = [float(np.max(abs(a - b))) for a, b in zip(*states)]
            repeat_ok = difference[0] <= 1e-9 and difference[1] <= 1e-8
            passed = repeat_ok and all(
                t["max_center_shift_m"] <= 1e-8
                and (case["enabled"] or t["disabled_unchanged"])
                for t in traces
            )
            results.append(
                {k: case[k] for k in ("diameter", "dt", "mode", "enabled")}
                | {
                    "passed": passed,
                    "repeat_max_differences": difference,
                    "episodes": traces,
                }
            )
        return {
            "valid": True,
            "passed": first["passed"] and all(c["passed"] for c in results),
            "first_step": first,
            "cases": results,
            "limits": "20 ms synthetic free response. No monotonic decay required for undamped dynamics; curves are not calibrated material error or proof of convergence. Particle diameter also changes the contact envelope.",
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
