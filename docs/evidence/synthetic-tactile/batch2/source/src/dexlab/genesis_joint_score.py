"""Independently separate imported-model checks from a frozen limit criterion."""
import argparse
import json
import math
from pathlib import Path


def score_trial(record):
    rows = record["samples"]
    if len(rows) != 500:
        raise ValueError("Expected 500 samples")
    for index, row in enumerate(rows):
        if row["step"] != index + 1 or not all(
            math.isfinite(row[key]) for key in ("q_m", "v_m_s", "generalized_force_N")
        ):
            raise ValueError("Invalid or missing sample")
    initial = record["initial_readback"]
    expected_armature = 0.0 if record["armature_profile"] == "zero" else 0.1
    expected_time = 0.004 if record["response"] == "explicit004" else 0.01
    checks = {
        "mass": initial["get_links_mass"] == [0.0, 0.1],
        "armature": initial["get_dofs_armature"] == [expected_armature],
        "effective_mass": math.isclose(initial["get_mass_mat"][0][0], 0.1 + expected_armature, abs_tol=1e-12),
        "passive_damping": initial["get_dofs_damping"] == [0.0],
        "gains": initial["get_dofs_kp"] == [100.0] and initial["get_dofs_kv"] == [10.0],
        "limit_range": initial["get_dofs_limit"] == [[0.0], [0.05]],
        "effort_range": initial["get_dofs_force_range"] == [[-5.0], [5.0]],
        "initial_q": math.isclose(initial["get_dofs_position"][0], 0.025, abs_tol=1e-12),
        "solver_parameters": initial["joint_sol_params"] == [expected_time, 1.0, 0.9, 0.95, 0.001, 0.5, 2.0],
    }
    violations = [max(-r["q_m"], r["q_m"] - 0.05, 0) for r in rows]
    return {"import_checks": checks, "import_passed": all(checks.values()),
            "max_violation_m": max(violations), "final_violation_m": violations[-1],
            "limit_criterion_passed": max(violations) <= 0.001 if record["limits_enabled"] else violations[-1] >= 0.01}


def score(directory):
    protocol = json.loads((directory / "protocol.json").read_text())
    for key, expected in {"schema": 1, "engine": "1.4.3", "precision": "64", "backend": "cpu",
                          "gravity": [0, 0, 0], "mass_kg": 0.1, "initial_q_m": 0.025,
                          "kp": 100, "kv": 10, "effort_range_N": [-5, 5],
                          "targets_m": [-0.05, 0.1],
                          "dt_s": 0.002, "steps": 500, "range_m": [0, 0.05],
                          "max_violation_m": 0.001, "negative_min_exceedance_m": 0.01}.items():
        if protocol.get(key) != expected:
            raise ValueError(f"Unsupported protocol: {key}")
    results = {}
    for armature in ("as_imported", "zero"):
        for response in ("default", "explicit004"):
            for enabled in (True, False):
                for target in (-0.05, 0.1):
                    key = f"{armature}-{response}-{enabled}-{target}"
                    record = json.loads((directory / f"{key}.json").read_text())
                    if (record["armature_profile"], record["response"], record["limits_enabled"], record["target_m"]) != (armature, response, enabled, target):
                        raise ValueError("Mislabeled record")
                    results[key] = score_trial(record)
    return {"scope": "Engineering criterion only; physical accuracy unmeasured", "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2))
