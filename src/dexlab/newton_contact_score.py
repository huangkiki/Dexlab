"""Independent, fail-closed scoring of the frozen XPBD contact protocol."""

import argparse
import json
import math
from pathlib import Path


def _vector(value, size):
    if (
        not isinstance(value, list)
        or len(value) != size
        or any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            for x in value
        )
    ):
        raise ValueError("Missing, nonfinite or malformed observation")
    return value


def _episode(episode):
    rows = episode["rows"]
    if len(rows) != 1000 or [r["step"] for r in rows] != list(range(1, 1001)):
        raise ValueError("Incomplete step coverage")
    body = episode["body_index"]
    mapping = episode["shape_body"]
    if (
        type(body) is not int
        or body != 0
        or any(type(index) is not int for index in mapping)
        or sorted(mapping) != [-1, 0]
    ):
        raise ValueError("Unexpected scene topology")
    mass = episode["observed_mass_kg"]
    if (
        isinstance(mass, bool)
        or not isinstance(mass, (int, float))
        or not math.isfinite(mass)
        or abs(mass - 0.1) > 1e-7
    ):
        raise ValueError("Unexpected observed mass")
    if episode["shape_type"] != [1, 3]:
        raise ValueError("Expected analytical plane and sphere")
    scales = episode["shape_scale"]
    transforms = episode["shape_transform"]
    if len(scales) != 2 or len(transforms) != 2:
        raise ValueError("Missing geometry readback")
    for actual, expected in zip(scales, ([0.0, 0.0, 0.0], [0.05, 0.0, 0.0])):
        if max(abs(a - b) for a, b in zip(_vector(actual, 3), expected)) > 1e-7:
            raise ValueError("Unexpected shape dimensions")
    for actual in transforms:
        if (
            max(
                abs(a - b)
                for a, b in zip(_vector(actual, 7), [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
            )
            > 1e-7
        ):
            raise ValueError("Unexpected local collision transform")
    if episode["shape_mu"] != [0.0, 0.0] or episode["shape_margin"] != [0.0, 0.0]:
        raise ValueError("Unexpected contact material or offset")
    initial = _vector(episode["initial_q"], 7)
    velocity = _vector(episode["initial_qd"], 6)
    if (
        max(abs(a - b) for a, b in zip(initial, [0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 1.0]))
        > 1e-7
        or max(map(abs, velocity)) > 1e-7
    ):
        raise ValueError("Unexpected initial state")
    heights, speeds, forces, zvel = [], [], [], []
    for row in rows:
        q, qd = _vector(row["q"], 7), _vector(row["qd"], 6)
        if abs(sum(v * v for v in q[3:]) - 1.0) > 1e-4:
            raise ValueError("Invalid quaternion")
        a, b, contact_forces = row["shape0"], row["shape1"], row["force"]
        if not len(a) == len(b) == len(contact_forces):
            raise ValueError("Missing force observations")
        fz = 0.0
        for s0, s1, force in zip(a, b, contact_forces):
            _vector(force, 6)
            if (
                any(type(s) is not int or not 0 <= s < len(mapping) for s in (s0, s1))
                or s0 == s1
            ):
                raise ValueError("Invalid contact pair")
            fz += force[2] * (1 if mapping[s0] == body else -1)
        heights.append(q[2])
        speeds.append(math.sqrt(sum(v * v for v in qd[:3])))
        forces.append(fz)
        zvel.append(qd[2])
    max_pen = max(0.0, 0.05 - min([initial[2]] + heights))
    height_err = max(abs(z - 0.05) for z in heights[-250:])
    speed = max(speeds[-250:])
    force_err = max(abs(f - 0.981) / 0.981 for f in forces[-250:])
    impulse_residual = 0.1 * (zvel[-1] - velocity[2]) - (sum(forces) * 0.001 - 0.981)
    free_position_err = max(
        abs(z - (0.1 - 9.81 * 0.001**2 * n * (n + 1) / 2))
        for n, z in enumerate(heights, 1)
    )
    free_velocity_err = max(abs(v + 9.81 * 0.001 * n) for n, v in enumerate(zvel, 1))
    return {
        "support_passed": max_pen <= 0.001
        and height_err <= 0.001
        and speed <= 0.01
        and force_err <= 0.05,
        "max_intrusion_m": max_pen,
        "hold_height_error_m": height_err,
        "hold_speed_m_s": speed,
        "hold_force_relative_error": force_err,
        "momentum_residual_N_s": impulse_residual,
        "freefall_position_error_m": free_position_err,
        "freefall_velocity_error_m_s": free_velocity_err,
        "max_abs_contact_force_N": max(map(abs, forces)),
    }


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("completed") is not True
            or "error" in record
        ):
            raise ValueError("Native execution incomplete")
        expected = {
            "dt_s": 0.001,
            "steps": 1000,
            "mass_kg": 0.1,
            "radius_m": 0.05,
            "initial_height_m": 0.1,
            "gravity_m_s2": -9.81,
            "device": "cpu",
            "precision": "float32",
        }
        if any(record.get(k) != v for k, v in expected.items()):
            raise ValueError("Protocol differs from frozen settings")
        if record.get("solver") != {
            "name": "SolverXPBD",
            "iterations": 4,
            "rigid_contact_relaxation": 0.8,
            "rigid_contact_con_weighting": True,
            "enable_restitution": False,
        }:
            raise ValueError("Unexpected solver settings")
        if (
            record["versions"]["newton"] != "1.6.1"
            or record["versions"]["warp-lang"] != "1.18.0"
        ):
            raise ValueError("Unexpected runtime versions")
        episodes = record["episodes"]
        if [e["case"] for e in episodes] != [
            "support",
            "support-repeat",
            "collision-disabled",
        ]:
            raise ValueError("Missing or duplicate cases")
        results = [_episode(e) for e in episodes]
        repeat_identical = episodes[0]["rows"] == episodes[1]["rows"]
        negative = results[2]
        negative_verified = (
            not negative["support_passed"]
            and negative["freefall_position_error_m"] <= 0.0001
            and negative["freefall_velocity_error_m_s"] <= 0.001
            and negative["max_abs_contact_force_N"] == 0
        )
        return {
            "valid": True,
            "passed": all(r["support_passed"] for r in results[:2])
            and repeat_identical
            and negative_verified,
            "repeat_identical": repeat_identical,
            "negative_control_verified": negative_verified,
            "cases": dict(zip([e["case"] for e in episodes], results)),
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
