"""Engine-free applied-load response identification for the frozen MuJoCo fixture."""

import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.contact_tangent import LIMITS, fit_response
from dexlab.contact_tangent import score as validity_score
from dexlab.physx_baseline import digest

PROFILES = {
    "high": {"solref": [-2500, -5], "solimp": [0.9, 0.9, 0.001, 0.5, 2]},
    "low": {"solref": [-24975, -49.95], "solimp": [0.001, 0.001, 0.001, 0.5, 2]},
}


def score(load, dt, data):
    """Keep generic validity separate from model fit; never accept unsettled fits.

    Pre-step is the declared MuJoCo solve epoch. Post-step is a diagnostic,
    never an alternative selected by regression quality. The target stays
    K=20000 N/m, D=40 Ns/m and zero direct applied-load dependence.
    """
    original = validity_score(load, dt, data)
    result = {key: original[key] for key in ("valid", "checks")}
    result["models"] = {}
    if not original["checks"]["complete_finite_arrays"]:
        return result
    result["momentum_peak_n"] = original["momentum_peak_n"]
    n = len(data["load"])
    train = slice(round(0.4 / dt), round(0.8 / dt))
    held = slice(round(0.8 / dt), n)
    for epoch, offset in (("pre", 0), ("post", 1)):
        depth = 0.02 - data["pose"][offset : n + offset, 2]
        speed = -data["velocity"][offset : n + offset, 2]
        for augmented in (False, True):
            name = epoch + ("-load" if augmented else "-basic")
            try:
                fitted = fit_response(
                    depth[train],
                    speed[train],
                    data["force"][train, 2],
                    applied_load=data["load"][train] if augmented else None,
                )
                smaller = fit_response(
                    depth[held],
                    speed[held],
                    data["force"][held, 2],
                    applied_load=data["load"][held] if augmented else None,
                )
            except ValueError as exc:
                result["models"][name] = {"identifiable": False, "reason": str(exc)}
                continue
            predicted = (
                fitted["intercept_n"]
                + fitted["stiffness_n_m"] * depth[held]
                + fitted["damping_ns_m"] * speed[held]
                + fitted.get("load_gain", 0.0) * data["load"][held]
            )
            error = float(np.sqrt(np.mean((data["force"][held, 2] - predicted) ** 2)))
            result["models"][name] = {
                "identifiable": True,
                "fit": fitted,
                "smaller_amplitude_fit": smaller,
                "prediction_rms_n": error,
                "prediction_ok": error <= LIMITS["prediction_fraction"] * 0.01 * load,
                "fit_ok": fitted["residual_rms_n"]
                <= LIMITS["fit_fraction"] * 0.02 * load,
                "data_valid": original["valid"],
                "target_difference": {
                    "stiffness_n_m": fitted["stiffness_n_m"] - 20000,
                    "damping_ns_m": fitted["damping_ns_m"] - 40,
                    "load_gain": fitted.get("load_gain", 0.0),
                },
            }
    return result


def verify(directory):
    """Rebuild validity and fits from raw arrays/contacts, not saved scores."""
    directory = Path(directory)
    receipt = json.loads((directory / "receipt.json").read_text())
    required = {"states.npz", "contacts.jsonl.gz", "native.json", "model.xml"}
    if set(receipt["hashes"]) != required or any(
        digest(directory / name) != receipt["hashes"][name] for name in required
    ):
        raise ValueError("Incomplete or mismatched raw archive hashes")
    if receipt["normal"] not in PROFILES.values():
        raise ValueError("Outside frozen normal profiles")
    native = json.loads((directory / "native.json").read_text())
    if (
        native["normal_parameters_readback"] != receipt["normal"]
        or native["mass_readback"] != 0.2
    ):
        raise ValueError("Native fixture differs from declared protocol")
    expected_solver = {
        "integrator": 0,
        "algorithm": 2,
        "cone": 1,
        "iterations": 100,
        "tolerance": 1e-10,
        "impratio": 1.0,
        "disableflags": 0,
        "enableflags": 0,
    }
    geometry = native.get("geometry_readback", {})
    if (
        native.get("solver") != expected_solver
        or geometry.get("type") != [0, 6]
        or geometry.get("size") != [[2.0, 2.0, 0.1], [0.02, 0.02, 0.02]]
        or native.get("friction_readback") != [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        or not np.allclose(
            native.get("inertia_readback", []),
            [0.2 * 0.04**2 / 6] * 3,
            rtol=1e-12,
            atol=0,
        )
    ):
        raise ValueError("Native geometry or solver differs from frozen fixture")
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        data = {key: saved[key] for key in saved.files}
    forces, counts, completed = [], [], []
    with gzip.open(directory / "contacts.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            points = row["contacts"]
            for point in points:
                if any(
                    point["parameters"][key] != receipt["normal"][key]
                    for key in ("solref", "solimp")
                ):
                    raise ValueError(
                        "Native pair parameters differ from declared profile"
                    )
            forces.append(
                np.sum([point["force_on_box"] for point in points], axis=0)
                if points
                else np.zeros(3)
            )
            counts.append(len(points))
            completed.append(not any(row["warnings"]))
    reconstructed = {
        "ledger": np.asarray(forces),
        "contacts": np.asarray(counts),
        "completed": np.asarray(completed, dtype=bool),
    }
    if any(
        key not in data or not np.array_equal(data[key], value)
        for key, value in reconstructed.items()
    ):
        raise ValueError("Raw contacts/warnings disagree with saved arrays")
    return score(receipt["load_n"], receipt["timestep_s"], data)
