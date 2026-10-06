"""Independent plane geometry/freefall checks; no synthetic force-as-truth claim."""

import argparse
import json
from pathlib import Path

import numpy as np


def score(record):
    try:
        if not isinstance(record, dict):
            raise ValueError("Native record must be an object")
        if record.get("completed") is not True or "error" in record:
            raise ValueError("Native record incomplete")
        expected = {
            "dt_s": 0.002,
            "steps": 150,
            "repeats": 2,
            "diameter_m": 0.008,
            "area_density_kg_m2": 0.2,
            "initial_height_m": 0.02,
            "initial_vx_m_s": 0.2,
            "gravity_m_s2": [0, 0, -9.81],
        }
        if (
            record["protocol"] != expected
            or record["versions"]["genesis-world"] != "1.4.3"
        ):
            raise ValueError("Frozen protocol/runtime mismatch")
        scenes = record["scenes"]
        if [s["name"] for s in scenes] != ["low", "high", "disabled"]:
            raise ValueError("Missing/duplicate conditions")
        results = {}
        states = {}
        for scene, mu, coupled in zip(scenes, [0.01, 0.5, 0.01], [True, True, False]):
            if scene["mu"] != mu or scene["coupled"] is not coupled:
                raise ValueError("Condition mismatch")
            n = scene["native"]["particle_count"]
            mass = np.asarray(scene["native"]["particle_mass_kg"], dtype=float)
            faces = np.asarray(scene["native"]["mesh_faces"])
            if (
                type(n) is not int
                or n < 3
                or mass.shape != (n,)
                or not np.isfinite(mass).all()
                or (mass <= 0).any()
                or abs(mass.sum() - 0.00032) > 1e-8
            ):
                raise ValueError("Native mass/readback mismatch")
            if (
                faces.ndim != 2
                or faces.shape[1] != 3
                or not np.issubdtype(faces.dtype, np.integer)
                or (faces < 0).any()
                or (faces >= n).any()
            ):
                raise ValueError("Invalid native surface topology")
            vertices = np.asarray(scene["native"]["mesh_vertices"], dtype=float)
            if vertices.shape != (n, 3) or not np.isfinite(vertices).all():
                raise ValueError("Invalid native vertices")
            triangles = vertices[faces]
            area = (
                np.linalg.norm(
                    np.cross(
                        triangles[:, 1] - triangles[:, 0],
                        triangles[:, 2] - triangles[:, 0],
                    ),
                    axis=1,
                ).sum()
                / 2
            )
            if abs(area - 0.0016) > 1e-8:
                raise ValueError("Native surface area mismatch")
            if scene["native"]["particle_diameter_m"] != 0.008:
                raise ValueError("Native particle diameter mismatch")
            episodes = scene["episodes"]
            if [e["repeat"] for e in episodes] != [0, 1]:
                raise ValueError("Missing reset repeat")
            trajectories = []
            case_results = []
            for episode in episodes:
                rows = episode["rows"]
                if [r["step"] for r in rows] != list(range(151)):
                    raise ValueError("Incomplete every-step coverage")
                p = np.asarray([r["pos"] for r in rows], dtype=float)
                v = np.asarray([r["vel"] for r in rows], dtype=float)
                if (
                    p.shape != (151, n, 3)
                    or v.shape != p.shape
                    or not np.isfinite(p).all()
                    or not np.isfinite(v).all()
                ):
                    raise ValueError("Missing or nonfinite particle observations")
                if (
                    np.max(abs(p[0, :, 2] - 0.02)) > 1e-8
                    or np.max(abs(v[0] - [0.2, 0, 0])) > 1e-8
                ):
                    raise ValueError("Initial state mismatch")
                steps = np.arange(151)
                zref = (
                    p[0, :, 2][None, :]
                    - 9.81 * 0.002**2 * (steps * (steps + 1) / 2)[:, None]
                )
                vzref = -9.81 * 0.002 * steps[:, None]
                center_z = p[:, :, 2] @ mass / mass.sum()
                minimum = float(p[:, :, 2].min())
                hold_error = float(np.max(abs(center_z[-50:] - 0.004)))
                support = minimum >= -0.0005 and hold_error <= 0.0005
                pos_error = float(np.max(abs(p[:, :, 2] - zref)))
                vel_error = float(np.max(abs(v[:, :, 2] - vzref)))
                case_results.append(
                    {
                        "support_passed": support,
                        "minimum_surface_z_m": minimum,
                        "hold_center_height_error_m": hold_error,
                        "freefall_z_error_m": pos_error,
                        "freefall_vz_error_m_s": vel_error,
                        "negative_verified": not support
                        and pos_error <= 0.0001
                        and vel_error <= 0.001,
                        "mean_final_x_travel_m": float(
                            np.mean(p[-1, :, 0] - p[0, :, 0])
                        ),
                        "mean_final_vx_m_s": float(np.mean(v[-1, :, 0])),
                    }
                )
                trajectories.append((p, v))
            dp = float(np.max(abs(trajectories[0][0] - trajectories[1][0])))
            dv = float(np.max(abs(trajectories[0][1] - trajectories[1][1])))
            results[scene["name"]] = {
                "episodes": case_results,
                "reset_max_position_difference_m": dp,
                "reset_max_velocity_difference_m_s": dv,
                "reset_passed": dp <= 1e-9 and dv <= 1e-8,
            }
            states[scene["name"]] = trajectories[0]
        passed = all(r["reset_passed"] for r in results.values())
        passed &= all(
            e["support_passed"]
            for name in ("low", "high")
            for e in results[name]["episodes"]
        )
        passed &= all(e["negative_verified"] for e in results["disabled"]["episodes"])
        return {
            "valid": True,
            "passed": bool(passed),
            "cases": results,
            "high_low_max_position_difference_m": float(
                np.max(abs(states["high"][0] - states["low"][0]))
            ),
            "high_low_max_velocity_difference_m_s": float(
                np.max(abs(states["high"][1] - states["low"][1]))
            ),
            "limits": "Plane geometry only. Linear triangle-plane penetration is bounded by minimum vertex z; no general swept-surface/obstacle/self-contact proof. Native PBD coupling forces unqualified.",
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
