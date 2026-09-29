"""Offline hold-window diagnostics, separate from physical grasp acceptance."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

PADS = ("r_thumb_pad", "r_index_finger_pad")


def intervals(mask, start, dt):
    """Contiguous sampled bins; no interpolation or bridging across unknowns."""
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return [
        {
            "start_s": float(start + first * dt),
            "end_s": float(start + last * dt),
            "duration_s": float((last - first) * dt),
            "samples": int(last - first),
        }
        for first, last in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))
    ]


def vector_stats(values, unit):
    """Equal-weight statistics over finite observed samples, never zero-filled."""
    valid = np.isfinite(values).all(axis=1)
    observed = values[valid]
    result = {
        "unit": unit,
        "valid_samples": int(valid.sum()),
        "unknown_samples": int((~valid).sum()),
        "mean_components": None,
        "rms_norm": None,
        "peak_norm": None,
        "centered_rms_norm": None,
        "centered_peak_norm": None,
    }
    if len(observed):
        mean = observed.mean(axis=0)
        norms = np.linalg.norm(observed, axis=1)
        centered = np.linalg.norm(observed - mean, axis=1)
        result.update(
            mean_components=mean.tolist(),
            rms_norm=float(np.sqrt(np.mean(norms**2))),
            peak_norm=float(norms.max()),
            centered_rms_norm=float(np.sqrt(np.mean(centered**2))),
            centered_peak_norm=float(centered.max()),
        )
    return result


def analyze(log, contacts, dt, body_names, window=(11.0, 14.0)):
    """Analyze existing arrays; body_names maps native body IDs to names."""
    start, end = window
    if not np.isfinite([dt, start, end]).all() or dt <= 0 or not 0 <= start < end:
        raise ValueError("Require finite positive dt and an ordered nonnegative window")
    if not np.allclose(
        np.array(window) / dt, np.rint(np.array(window) / dt), atol=1e-7, rtol=0
    ):
        raise ValueError("Window boundaries must align with the physics-step grid")
    count = round((end - start) / dt)
    times = np.asarray(log["time"], dtype=float)
    if times.ndim != 1:
        raise ValueError("time must be a one-dimensional array")

    def locate(t):
        # Only cast bounded hold-window timestamps, including invalid grid points.
        inside = np.isfinite(t) & (t >= start - dt * 1e-7) & (t < end - dt * 1e-7)
        rows = np.flatnonzero(inside)
        scaled = (t[rows] - start) / dt
        steps = np.rint(scaled).astype(int)
        aligned = (np.abs(scaled - steps) <= 1e-7) & (steps >= 0) & (steps < count)
        return (
            rows[aligned],
            steps[aligned],
            int((~aligned).sum()),
            int((~np.isfinite(t)).sum()),
        )

    rows, steps, off_grid, invalid_times = locate(times)
    multiplicity = np.bincount(steps, minlength=count)
    unique = multiplicity == 1
    usable = unique[steps]
    fields = {}
    unavailable = []
    for name, width in (
        ("apple_pose", 7),
        ("wrist_pose", 7),
        ("velocity", 3),
        ("hand", 3),
    ):
        values = np.full((count, width), np.nan)
        source = np.asarray(log.get(name, []), dtype=float)
        if source.shape == (len(times), width):
            values[steps[usable]] = source[rows[usable]]
        else:
            unavailable.append(name)
        fields[name] = values

    apple, wrist = fields["apple_pose"], fields["wrist_pose"]
    relative = np.full((count, 3), np.nan)
    pose_valid = (
        np.isfinite(apple[:, :3]).all(axis=1)
        & np.isfinite(wrist).all(axis=1)
        & (np.linalg.norm(wrist[:, 3:], axis=1) > 0)
    )
    if pose_valid.any():
        relative[pose_valid] = (
            Rotation.from_quat(wrist[pose_valid, 3:])
            .inv()
            .apply(apple[pose_valid, :3] - wrist[pose_valid, :3])
        )

    ledger = None if contacts is None else np.asarray(contacts, dtype=float)
    summed = np.zeros((count, 3))
    bad_steps = np.zeros(count, dtype=bool)
    loads = {name: np.zeros(count) for name in PADS}
    entries = {name: np.zeros(count, dtype=int) for name in PADS}
    contact_off_grid = contact_invalid_times = invalid_rows = 0
    if ledger is not None:
        if ledger.ndim != 2 or ledger.shape[1] != 10:
            raise ValueError("contacts must have shape (N, 10)")
        crows, csteps, contact_off_grid, contact_invalid_times = locate(ledger[:, 0])
        for row, step in zip(ledger[crows], csteps):
            if not np.isfinite(row).all() or row[1] != np.trunc(row[1]):
                bad_steps[step] = True
                invalid_rows += 1
                continue
            name = body_names.get(int(row[1]))
            if name is None or not name.startswith("r_"):
                bad_steps[step] = True
                invalid_rows += 1
                continue
            summed[step] += row[7:10]
            if name in PADS:
                entries[name][step] += 1
                loads[name][step] += np.linalg.norm(row[7:10])
    # Same reconciliation tolerances as verify_sdf_grasp; no acceptance change.
    reconciles = np.isclose(summed, fields["hand"], atol=1e-8, rtol=1e-5).all(axis=1)
    trusted = unique & reconciles & ~bad_steps
    if ledger is None or contact_off_grid or contact_invalid_times:
        trusted[:] = False  # Cannot safely assign these ledger records to bins.
    fingers = {}
    for name in PADS:
        known = trusted & (entries[name] > 0)
        low = known & (loads[name] <= 0.1)
        episodes = intervals(low, start, dt)
        for episode in episodes:
            first = round((episode["start_s"] - start) / dt)
            last = first + episode["samples"]
            episode["left_censored"] = bool(first == 0 or not known[first - 1])
            episode["right_censored"] = bool(last == count or not known[last])
        fingers[name] = {
            "load_definition": "sum of world-force magnitudes over this pad's recorded points; not normal force",
            "load": vector_stats(np.where(known, loads[name], np.nan)[:, None], "N"),
            "threshold_n": 0.1,
            "observed_zero_force_samples": int((known & (loads[name] == 0)).sum()),
            "no_ledger_row_samples": int((entries[name] == 0).sum()),
            "unknown_intervals": intervals(~known, start, dt),
            "observed_low_force_intervals": episodes,
            "observed_low_force_duration_s": float(low.sum() * dt),
            "low_force_duration_bounds_s": [
                float(low.sum() * dt),
                float((low | ~known).sum() * dt),
            ],
            "longest_observed_low_force_duration_s": max(
                (x["duration_s"] for x in episodes), default=0.0
            ),
        }
    observed_times = start + np.flatnonzero(unique) * dt
    gaps = np.diff(observed_times)
    return {
        "schema_version": 1,
        "window_s": [start, end],
        "sampling": {
            "dt_s": dt,
            "nominal_rate_hz": 1 / dt,
            "expected_samples": count,
            "unique_samples": int(unique.sum()),
            "missing_samples": int((multiplicity == 0).sum()),
            "duplicate_bins": int((multiplicity > 1).sum()),
            "off_grid_rows_in_window": off_grid,
            "nonfinite_timestamps_in_archive": invalid_times,
            "observed_interval_min_s": float(gaps.min()) if len(gaps) else None,
            "observed_interval_max_s": float(gaps.max()) if len(gaps) else None,
            "unknown_intervals": intervals(~unique, start, dt),
        },
        "signals": {
            "apple_origin_world_position": vector_stats(apple[:, :3], "m"),
            "apple_origin_wrist_relative_position": vector_stats(relative, "m"),
            "apple_com_world_velocity": vector_stats(fields["velocity"], "m/s"),
            "hand_force_on_apple_world": vector_stats(fields["hand"], "N"),
        },
        "unavailable_or_malformed_fields": unavailable,
        "contact_ledger": {
            "available": ledger is not None,
            "off_grid_rows_in_window": contact_off_grid,
            "nonfinite_timestamps_in_archive": contact_invalid_times,
            "invalid_rows_in_window": invalid_rows,
            "force_mismatch_samples": int(
                (unique & np.isfinite(fields["hand"]).all(axis=1) & ~reconciles).sum()
            ),
            "reconciliation_atol_n": 1e-8,
            "reconciliation_rtol": 1e-5,
            "fingers": fingers,
        },
        "energy": {
            "available": False,
            "reason": "Logs lack full-system velocities, inertias, actuator work and dissipated/contact energy. No total-energy or conservation diagnostic is inferred from momentum balance.",
        },
        "limits": [
            "Diagnostics only: no grasp verdict or new acceptance thresholds.",
            "RMS and peaks use vector norms; centered values subtract the observed mean, not a trend or frequency band. Drift and oscillation both contribute.",
            "Finite observed samples only; missing, duplicate and invalid samples are not interpolated or zero-filled. Incomplete statistics may be biased.",
            "The sparse ledger has no per-finger completeness marker. An absent row is unknown, not zero force. Force reconciliation cannot detect all balanced omissions.",
            "Low load means <=0.1 N, matching the existing two-pad acceptance boundary; it is not proof of geometric separation. Durations are observed sample-bin durations, not exact event times.",
            "Times are step-start labels: poses and velocities are recorded after integration, forces belong to that solved step. Different backend rates limit comparisons.",
        ],
    }


def diagnose_run(directory):
    directory = Path(directory)
    inputs = [directory / name for name in ("engine.json", "sdf-dynamics.npz")]
    engine = json.loads(inputs[0].read_text())
    with np.load(inputs[1], allow_pickle=False) as archive:
        log = dict(archive)
    contacts_path = directory / "sdf-contacts.npz"
    contacts = None
    if contacts_path.exists():
        inputs.append(contacts_path)
        with np.load(contacts_path, allow_pickle=False) as archive:
            contacts = archive["contacts"]
    if engine["backend"] == "mujoco":
        from dexlab.mujoco_artifacts import load_model, model_inputs

        inputs.extend(model_inputs(directory))
        model = load_model(directory)
        names = {i: model.body(i).name for i in range(model.nbody)}
    elif engine["backend"] == "superdex":
        names = dict(enumerate(engine["body_names"]))
    else:
        raise ValueError(f"Unsupported backend: {engine['backend']}")
    result = analyze(log, contacts, float(engine["dt"]), names)
    result["backend"] = engine["backend"]
    result["engine_version"] = engine.get("version")
    result["input_sha256"] = {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in inputs
    }
    result["analyzer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = diagnose_run(args.run)
    output = args.output or args.run / "jitter-diagnostics.json"
    if output.resolve() in {
        (args.run / name).resolve()
        for name in result["input_sha256"]
    }:
        parser.error("Output must not overwrite an input archive")
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
