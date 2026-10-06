"""Independent transient diagnostic against a declared linear contact target.

This synthetic Kelvin--Voigt response is not a measured fingertip material.
Only the positive-load interval is compared: a bilateral linear spring must
not be used as a reference for detachment. No time/offset alignment is fitted.
"""

import numpy as np


TARGET = {
    "stiffness_n_m": 20000.0,
    "damping_n_s_m": 40.0,
    "window_s": 0.05,
    "rms_fraction_of_step": 0.10,
    "peak_fraction_of_step": 0.25,
}


def reference(time, mass, *, stiffness=20000.0, damping=40.0):
    """Exact underdamped response to 2 N increments at 0, 0.2 and 0.4 s.

    Indentation is positive downwards; m*x'' + D*x' + K*x = load.
    The fixture starts at zero indentation and zero velocity.
    """
    time = np.asarray(time, dtype=float)
    if (
        not np.isfinite([mass, stiffness, damping]).all()
        or mass <= 0
        or stiffness <= 0
        or damping < 0
        or damping**2 >= 4 * mass * stiffness
        or not np.isfinite(time).all()
    ):
        raise ValueError("Expected a finite underdamped reference")
    alpha = damping / (2 * mass)
    omega = np.sqrt(stiffness / mass - alpha**2)
    displacement = np.zeros_like(time)
    for onset in (0.0, 0.2, 0.4):
        t = np.maximum(time - onset, 0)
        displacement += (
            2
            / stiffness
            * (
                1
                - np.exp(-alpha * t)
                * (np.cos(omega * t) + alpha / omega * np.sin(omega * t))
            )
        )
    return displacement


def score(case, data):
    """Score early response per load, without letting long plateaus hide error.

    This diagnostic must accompany the full native/static/momentum checks from
    contact_indent_run.verify; it is not a standalone physical acceptance.
    """
    checks = {
        "complete_shapes": all(
            key in data and np.shape(data[key]) == shape
            for key, shape in {
                "time": (case.steps + 1,),
                "pose": (case.steps + 1, 7),
            }.items()
        )
    }
    result = {"passed": False, "checks": checks, "metrics": {}}
    if not checks["complete_shapes"]:
        return result
    checks["finite_samples"] = bool(
        np.isfinite(data["time"]).all() and np.isfinite(data["pose"]).all()
    )
    checks["uniform_time_grid"] = bool(
        np.allclose(
            data["time"],
            np.arange(case.steps + 1) * case.timestep,
            atol=1e-10,
            rtol=0,
        )
    )
    if not all(checks.values()):
        return result
    # COM displacement, rather than deepest corner: tipping is independently
    # rejected by the full fixture scorer and cannot improve this diagnostic.
    depth = case.half_size - data["pose"][:, 2]
    ideal = reference(
        data["time"],
        case.mass,
        stiffness=TARGET["stiffness_n_m"],
        damping=TARGET["damping_n_s_m"],
    )
    scale = 2 / TARGET["stiffness_n_m"]
    width = round(TARGET["window_s"] / case.timestep)
    rows = []
    for index, load in enumerate((2, 4, 6)):
        start = round(index * 0.2 / case.timestep)
        error = (
            depth[start + 1 : start + width + 1] - ideal[start + 1 : start + width + 1]
        )
        rows.append(
            {
                "load_n": load,
                "rms_error_m": float(np.sqrt(np.mean(error**2))),
                "peak_error_m": float(np.abs(error).max()),
            }
        )
    checks["transient_rms_matches"] = all(
        row["rms_error_m"] / scale < TARGET["rms_fraction_of_step"] for row in rows
    )
    checks["transient_peak_matches"] = all(
        row["peak_error_m"] / scale < TARGET["peak_fraction_of_step"] for row in rows
    )
    result["metrics"] = {"windows": rows, "step_indentation_scale_m": scale}
    result["passed"] = all(checks.values())
    return result
