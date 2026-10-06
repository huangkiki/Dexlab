"""Rigid-body relative velocities at archived native contact locations.

Both twists and COM poses are the actual post-step states. MuJoCo contact
locations/normals come from the preceding solve, so the spatial sampling may
lag by one timestep. No contact IDs are tracked between steps and these metrics
are not accumulated material-point slip or a solver-independent contact mesh.
"""

import numpy as np


def cylinder_contact_motion(data, contacts, engine, body_ids=()):
    """Return per-step loaded-contact speeds; missing data stays unknown/NaN."""
    steps = len(data["time"]) - 1
    known = np.zeros(steps, dtype=bool)
    peak = np.full(steps, np.nan)
    rms = np.full(steps, np.nan)
    normal_load = np.full((steps, 2), np.nan)
    lookup = {int(body): index for index, body in enumerate(body_ids)}
    for step, row in enumerate(contacts[:steps]):
        try:
            if engine == "physx":
                pads = np.array(
                    [lookup[body] for body in row["normal_body_ids"]], dtype=int
                )
                points = np.asarray(row["normal_point"], dtype=float).reshape(-1, 3)
                directions = np.asarray(row["normal_direction"], dtype=float).reshape(
                    -1, 3
                )
                forces = np.asarray(row["normal_force"], dtype=float).reshape(-1, 3)
            else:
                pads = np.array([point["pad"] for point in row], dtype=int)
                points = np.array(
                    [point["point"] for point in row], dtype=float
                ).reshape(-1, 3)
                directions = np.array(
                    [point["normal_direction"] for point in row], dtype=float
                ).reshape(-1, 3)
                forces = np.array(
                    [point["normal_force"] for point in row], dtype=float
                ).reshape(-1, 3)
            count = len(pads)
            if (
                points.shape != (count, 3)
                or directions.shape != (count, 3)
                or forces.shape != (count, 3)
                or not np.isin(pads, [0, 1]).all()
                or not np.isfinite([points, directions, forces]).all()
                or not np.allclose(
                    np.linalg.norm(directions, axis=1), 1, atol=1e-5, rtol=0
                )
            ):
                continue
            pose, twist = data["pose"][step + 1], data["velocity"][step + 1]
            object_velocity = twist[2, :3] + np.cross(
                twist[2, 3:], points - pose[2, :3]
            )
            pad_velocity = twist[pads, :3] + np.cross(
                twist[pads, 3:], points - pose[pads, :3]
            )
            relative = object_velocity - pad_velocity
            tangent = (
                relative - np.sum(relative * directions, axis=1)[:, None] * directions
            )
            speed = np.linalg.norm(tangent, axis=1)
            weights = np.linalg.norm(forces, axis=1)
            loaded = weights > 1e-12
            if not np.isfinite(speed).all():
                continue
            normal_load[step] = [weights[pads == pad].sum() for pad in (0, 1)]
            known[step] = True
            if loaded.any():
                peak[step] = speed[loaded].max()
                rms[step] = np.sqrt(
                    np.average(speed[loaded] ** 2, weights=weights[loaded])
                )
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return {
        "known": known,
        "peak_speed": peak,
        "rms_speed": rms,
        "normal_load": normal_load,
    }


def summarize_cylinder_motion(data, contacts, engine, body_ids=()):
    motion = cylinder_contact_motion(data, contacts, engine, body_ids)
    times = data["time"][1:]
    hold = (times > 0.5) & (times <= 1.5)
    loaded = np.isfinite(motion["rms_speed"])
    selected = hold & loaded
    return {
        "complete_observation_coverage": bool(motion["known"].all()),
        "known_steps": int(motion["known"].sum()),
        "expected_steps": len(times),
        "loaded_steps": int(loaded.sum()),
        "hold_loaded_contact_peak_tangent_speed_m_s": float(
            motion["peak_speed"][selected].max()
        )
        if selected.any()
        else None,
        "hold_loaded_contact_rms_tangent_speed_m_s": float(
            np.sqrt(np.mean(motion["rms_speed"][selected] ** 2))
        )
        if selected.any()
        else None,
        "scope": "Actual post-step COM twists evaluated at native normal-contact locations; MuJoCo locations may lag one step; not tracked material slip. RMS is normal-load weighted within each step, then time weighted on the fixed grid; unloaded steps excluded and coverage reported.",
    }
