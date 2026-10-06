"""Frozen local normal-response identification; scoring imports no engine.

Coefficients describe the sampled fixture, not a measured hardware material.
Pre/post state epochs are reported separately; neither is selected by fit quality.
"""

import numpy as np

LOADS = (2.0, 4.0, 6.0)
TIMESTEPS = (0.0005, 0.00025, 0.000125)
DURATION = 1.2
SETTLE = 0.4
WINDOW = 0.4
DAMPING = 10.0
LIMITS = {
    "condition": 20.0,
    "fit_fraction": 0.05,
    "prediction_fraction": 0.05,
    "tangent_relative_error": 0.1,
    "amplitude_relative_change": 0.1,
    "preload_relative_error": 0.01,
    "settle_speed_m_s": 1e-5,
    "settle_std_m": 1e-6,
    "momentum_n": 1e-5,
    "ledger_n": 1e-7,
    "off_axis_m": 1e-7,
    "off_axis_rad_s": 1e-6,
}


def commands(load, dt):
    """Two integer-cycle frequencies; 2% fitting then 1% held-out amplitude.

    The amplitude is a fraction of preload per tone; commands act at step start.
    """
    if load not in LOADS or dt not in TIMESTEPS:
        raise ValueError("Outside frozen development protocol")
    t = np.arange(round(DURATION / dt)) * dt
    amplitude = np.where(t < SETTLE, 0.0, np.where(t < SETTLE + WINDOW, 0.02, 0.01))
    wave = np.sin(2 * np.pi * 20 * (t - SETTLE)) + np.sin(2 * np.pi * 35 * (t - SETTLE))
    return load * (1 + amplitude * wave)


def fit_response(depth, inward_speed, force, *, applied_load=None):
    """Fit force versus state, optionally separating applied-load feedthrough."""
    x = np.column_stack((depth, inward_speed)).astype(float)
    if applied_load is not None:
        x = np.column_stack((x, applied_load))
    width = 2 if applied_load is None else 3
    y = np.asarray(force, dtype=float)
    if (
        y.ndim != 1
        or x.shape != (len(y), width)
        or len(y) < 10
        or not np.isfinite(x).all()
        or not np.isfinite(y).all()
    ):
        raise ValueError("Need finite, aligned response samples")
    center = x.mean(axis=0)
    scale = x.std(axis=0)
    if np.any(scale <= 1e-15):
        raise ValueError("Unexcited response coordinate")
    design = np.column_stack((np.ones(len(y)), (x - center) / scale))
    condition = float(np.linalg.cond(design))
    if condition > LIMITS["condition"]:
        raise ValueError("Response coordinates are not independently identifiable")
    coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != width + 1:
        raise ValueError("Rank-deficient response")
    slopes = coefficients[1:] / scale
    intercept = float(coefficients[0] - slopes @ center)
    predicted = intercept + x @ slopes
    result = {
        "stiffness_n_m": float(slopes[0]),
        "damping_ns_m": float(slopes[1]),
        "intercept_n": intercept,
        "condition": condition,
        "residual_rms_n": float(np.sqrt(np.mean((y - predicted) ** 2))),
    }
    if applied_load is not None:
        result["load_gain"] = float(slopes[2])
    return result


def score(load, dt, data):
    """Fail closed on absent epochs/force ledger; report every model outcome."""
    command = commands(load, dt)
    n = len(command)
    shapes = {
        "time": (n + 1,),
        "pose": (n + 1, 7),
        "velocity": (n + 1, 6),
        "force": (n, 3),
        "ledger": (n, 3),
        "load": (n,),
        "completed": (n,),
        "contacts": (n,),
    }
    checks = {
        "complete_finite_arrays": all(
            k in data and np.shape(data[k]) == shape and np.isfinite(data[k]).all()
            for k, shape in shapes.items()
        )
    }
    result = {
        "valid": False,
        "checks": checks,
        "epochs": {},
        "scope": "Synthetic local response; not hardware calibration",
    }
    if not checks["complete_finite_arrays"]:
        return result
    time, pose, velocity = (data[k] for k in ("time", "pose", "velocity"))
    force = data["force"]
    expected_force = force.copy()
    expected_force[:, 2] -= command
    momentum = 0.2 * np.diff(velocity[:, :3], axis=0) / dt - expected_force
    settled = slice(round(0.3 / dt), round(0.4 / dt))
    checks.update(
        declared_clock=bool(
            np.allclose(time, np.arange(n + 1) * dt, atol=1e-9, rtol=0)
        ),
        declared_commands=bool(np.array_equal(data["load"], command)),
        native_steps_completed=bool(
            data["completed"].dtype == bool and data["completed"].all()
        ),
        contact_retained=bool(np.all(data["contacts"][round(SETTLE / dt) :] > 0)),
        stable_contact_count=bool(
            np.all(
                data["contacts"][round(SETTLE / dt) :]
                == data["contacts"][round(SETTLE / dt)]
            )
        ),
        force_ledger=bool(np.max(abs(force - data["ledger"])) <= LIMITS["ledger_n"]),
        momentum=bool(np.max(abs(momentum)) <= LIMITS["momentum_n"]),
        normal_translation=bool(
            np.max(abs(pose[:, :2])) <= LIMITS["off_axis_m"]
            and np.max(abs(pose[:, 3:] - [1, 0, 0, 0])) <= LIMITS["off_axis_m"]
            and np.max(abs(velocity[:, 3:])) <= LIMITS["off_axis_rad_s"]
        ),
        settled_speed=bool(
            np.max(abs(velocity[settled, 2])) <= LIMITS["settle_speed_m_s"]
        ),
        settled_depth=bool(np.std(pose[settled, 2]) <= LIMITS["settle_std_m"]),
        preload_balance=bool(
            abs(np.mean(force[settled, 2]) / load - 1)
            <= LIMITS["preload_relative_error"]
        ),
    )
    result["momentum_peak_n"] = float(np.max(abs(momentum)))
    result["ledger_peak_n"] = float(np.max(abs(force - data["ledger"])))
    fit_slice = slice(round(0.4 / dt), round(0.8 / dt))
    test_slice = slice(round(0.8 / dt), n)
    for name, offset in [("pre_step", 0), ("post_step", 1)]:
        depth = 0.02 - pose[offset : n + offset, 2]
        inward = -velocity[offset : n + offset, 2]
        try:
            fitted = fit_response(
                depth[fit_slice], inward[fit_slice], force[fit_slice, 2]
            )
            held = fit_response(
                depth[test_slice], inward[test_slice], force[test_slice, 2]
            )
        except ValueError as exc:
            result["epochs"][name] = {"identifiable": False, "reason": str(exc)}
            continue
        prediction = (
            fitted["intercept_n"]
            + fitted["stiffness_n_m"] * depth[test_slice]
            + fitted["damping_ns_m"] * inward[test_slice]
        )
        error = float(np.sqrt(np.mean((prediction - force[test_slice, 2]) ** 2)))
        target = DAMPING * load
        result["epochs"][name] = {
            "identifiable": True,
            "fit": fitted,
            "smaller_amplitude_fit": held,
            "held_out_prediction_rms_n": error,
            "fit_ok": fitted["residual_rms_n"] <= LIMITS["fit_fraction"] * 0.02 * load,
            "prediction_ok": error <= LIMITS["prediction_fraction"] * 0.01 * load,
            "conditional_cL_ok": abs(fitted["damping_ns_m"] / target - 1)
            <= LIMITS["tangent_relative_error"],
            "amplitude_stability_ok": abs(held["damping_ns_m"] - fitted["damping_ns_m"])
            <= LIMITS["amplitude_relative_change"] * target,
        }
    result["valid"] = all(checks.values())
    return result
