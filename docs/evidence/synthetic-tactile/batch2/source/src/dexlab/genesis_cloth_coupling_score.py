"""Independent linear momentum audit for the frozen free-plate diagnostic."""

import argparse
import json
from pathlib import Path

import numpy as np


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or record.get("completed") is not True
            or "error" in record
        ):
            raise ValueError("Incomplete native record")
        expected = {
            "dt_s": 0.002,
            "steps": 150,
            "repeats": 2,
            "diameter_m": 0.008,
            "area_density_kg_m2": 0.2,
            "initial_height_m": 0.02,
            "initial_vz_m_s": -0.1,
            "gravity_m_s2": [0, 0, 0],
            "plate_size_m": [0.08, 0.08, 0.01],
            "plate_mass_kg": 0.001,
        }
        if (
            record["protocol"] != expected
            or record["versions"]["genesis-world"] != "1.4.3"
        ):
            raise ValueError("Frozen protocol/runtime mismatch")
        scenes = record["scenes"]
        if [s["name"] for s in scenes] != ["coupled", "disabled"]:
            raise ValueError("Missing conditions")
        results = {}
        for scene, coupled in zip(scenes, [True, False]):
            if scene["coupled"] is not coupled:
                raise ValueError("Coupling condition mismatch")
            native = scene["native"]
            mass = np.asarray(native["particle_mass_kg"], dtype=float)
            plate_mass = float(native["plate_mass_kg"])
            n = native["particle_count"]
            if (
                type(n) is not int
                or n < 3
                or mass.shape != (n,)
                or not np.isfinite(mass).all()
                or (mass <= 0).any()
                or abs(mass.sum() - 0.00032) > 1e-8
                or not np.isfinite(plate_mass)
                or abs(plate_mass - 0.001) > 1e-12
                or native["plate_dofs"] != 6
            ):
                raise ValueError("Invalid native masses/free-body readback")
            episodes = scene["episodes"]
            if [e["repeat"] for e in episodes] != [0, 1]:
                raise ValueError("Missing reset repeat")
            trajectories = []
            episode_results = []
            for episode in episodes:
                rows = episode["rows"]
                if [r["step"] for r in rows] != list(range(151)):
                    raise ValueError("Missing every-step observation")
                p, v, rp, rv = [
                    np.asarray([r[key] for r in rows], dtype=float)
                    for key in ("pos", "vel", "plate_pos", "plate_vel")
                ]
                if (
                    p.shape != (151, n, 3)
                    or v.shape != p.shape
                    or rp.shape != (151, 3)
                    or rv.shape != rp.shape
                    or any(not np.isfinite(a).all() for a in (p, v, rp, rv))
                ):
                    raise ValueError("Invalid state arrays")
                if (
                    np.max(abs(v[0] - [0, 0, -0.1])) > 1e-8
                    or np.max(abs(rv[0])) > 1e-8
                    or np.max(abs(p[0, :, 2] - 0.02)) > 1e-8
                    or np.max(abs(rp[0])) > 1e-8
                ):
                    raise ValueError("Initial state mismatch")
                cloth_momentum = np.einsum("tnk,n->tk", v, mass)
                rigid_momentum = plate_mass * rv
                total = cloth_momentum + rigid_momentum
                residual = float(np.max(np.linalg.norm(total - total[0], axis=1)))
                tolerance = 0.01 * float(np.linalg.norm(total[0])) + 1e-8
                cloth_gain = float(cloth_momentum[-1, 2] - cloth_momentum[0, 2])
                plate_gain = float(rigid_momentum[-1, 2] - rigid_momentum[0, 2])
                transfer = cloth_gain >= 0.1 * abs(
                    total[0, 2]
                ) and plate_gain <= -0.1 * abs(total[0, 2])
                negative = (
                    np.max(abs(rp - rp[0])) <= 1e-9
                    and np.max(abs(rv)) <= 1e-8
                    and np.max(abs(v - [0, 0, -0.1])) <= 1e-8
                )
                episode_results.append(
                    {
                        "max_momentum_residual_kg_m_s": residual,
                        "momentum_tolerance_kg_m_s": tolerance,
                        "momentum_passed": residual <= tolerance,
                        "cloth_z_momentum_change_kg_m_s": cloth_gain,
                        "plate_z_momentum_change_kg_m_s": plate_gain,
                        "transfer_verified": bool(transfer),
                        "negative_verified": bool(negative),
                    }
                )
                trajectories.append((p, v, rp, rv))
            differences = [float(np.max(abs(a - b))) for a, b in zip(*trajectories)]
            repeat_ok = all(
                d <= tol for d, tol in zip(differences, [1e-9, 1e-8, 1e-9, 1e-8])
            )
            passed = repeat_ok and all(
                e["momentum_passed"]
                and e["transfer_verified" if coupled else "negative_verified"]
                for e in episode_results
            )
            results[scene["name"]] = {
                "passed": passed,
                "repeat_max_differences": differences,
                "episodes": episode_results,
            }
        return {
            "valid": True,
            "passed": all(r["passed"] for r in results.values()),
            "cases": results,
            "limits": "Linear momentum only; native PBD force readback, angular momentum and frictional grasp remain unqualified.",
        }
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
