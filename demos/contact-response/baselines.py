"""Descriptive, per-episode hold and constant-velocity forecasts; no fitting."""

import argparse
import json
from pathlib import Path

import numpy as np

from data import load_cohort, sha256


def quaternion_product(a, b):
    return np.concatenate((a[..., :1] * b[..., :1] - np.sum(a[..., 1:] * b[..., 1:], axis=-1, keepdims=True),
                           a[..., :1] * b[..., 1:] + b[..., :1] * a[..., 1:] + np.cross(a[..., 1:], b[..., 1:])), axis=-1)


def orientation_error(a, b):
    """Shortest rotation angle in radians; quaternion signs are immaterial."""
    relative = quaternion_product(np.concatenate((a[..., :1], -a[..., 1:]), axis=-1), b)
    return 2 * np.arctan2(np.linalg.norm(relative[..., 1:], axis=-1), np.abs(relative[..., 0]))


def predict(position, quaternion, velocity, local_omega, horizon, method):
    """Only origin state enters the forecast, with local angular rate on the right."""
    if method == "hold":
        return position.copy(), quaternion.copy()
    if method != "constant-velocity":
        raise ValueError("Unknown baseline")
    angle = np.linalg.norm(local_omega, axis=-1, keepdims=True) * horizon
    # sin(theta/2)/theta is well-defined at zero.
    vector = local_omega * horizon * .5 * np.sinc(angle / (2 * np.pi))
    delta = np.concatenate((np.cos(angle / 2), vector), axis=-1)
    return position + velocity * horizon, quaternion_product(quaternion, delta)


def confusion(predicted, actual):
    tp = int(np.sum(predicted & actual))
    fp = int(np.sum(predicted & ~actual))
    fn = int(np.sum(~predicted & actual))
    tn = int(np.sum(~predicted & ~actual))
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None)


def phase_labels(labels, origins, steps):
    phases = []
    for origin in origins:
        series = labels[origin - 1:origin + steps + 1]
        changes = np.diff(series.astype(int))
        gained, lost = np.any(changes > 0), np.any(changes < 0)
        phases.append("switching" if gained and lost else "establishment" if gained else
                      "loss" if lost else "sustained" if series[0] else "absent")
    return np.array(phases)


def evaluate_episode(episode, protocol):
    raw, manifest = episode["raw"], episode["manifest"]
    dt = manifest["effective"]["timestep"]
    stride = round(protocol["origin_stride_s"] / dt)
    if stride < 1 or not np.isclose(stride * dt, protocol["origin_stride_s"], rtol=0, atol=1e-12):
        raise ValueError("Origin stride must contain whole native steps")
    qpos, qvel = raw["qpos_before"], raw["qvel_before"]
    labels = episode["loads"] >= protocol["contact_normal_threshold_n"]
    rows = []
    for horizon in protocol["horizons_s"]:
        steps = round(horizon / dt)
        if steps < 1 or not np.isclose(steps * dt, horizon, rtol=0, atol=1e-12):
            raise ValueError("Horizon must contain whole native steps")
        origins = np.arange(stride, len(qpos) - steps, stride)
        if not len(origins):
            raise ValueError("No complete forecast windows")
        ends = origins + steps
        # Contact at solve i is not available before solve i.
        known, actual = labels[origins - 1], labels[ends]
        phases = [phase_labels(labels[:, pad], origins, steps) for pad in range(2)]
        boundaries = manifest["config"]
        time_s = raw["time_s"]
        context = np.where(time_s[origins] < boundaries["support_end_s"], "assisted-preparation",
                           np.where(time_s[origins] < boundaries["hold_start_s"], "settling",
                                    np.where(time_s[origins] < boundaries["action_start_s"], "hold", "commanded-release-or-unload")))
        for method in protocol["baselines"]:
            position, quaternion = predict(qpos[origins, 20:23], qpos[origins, 23:27],
                                            qvel[origins, 20:23], qvel[origins, 23:26], horizon, method)
            position_error = np.linalg.norm(position - qpos[ends, 20:23], axis=1)
            angle_error = orientation_error(quaternion, qpos[ends, 23:27])
            for pad, name in enumerate(("index_finger", "thumb")):
                for stage in np.unique(context):
                    for phase in ("establishment", "sustained", "loss", "absent", "switching"):
                        selected = (context == stage) & (phases[pad] == phase)
                        count = int(selected.sum())
                        if not count:
                            continue
                        rows.append(dict(method=method, horizon_s=horizon, pad=name, origin_stage=str(stage),
                                         contact_phase=phase, windows=count,
                                         position_rmse_m=float(np.sqrt(np.mean(position_error[selected] ** 2))),
                                         position_max_m=float(position_error[selected].max()),
                                         orientation_rmse_rad=float(np.sqrt(np.mean(angle_error[selected] ** 2))),
                                         endpoint_contact=confusion(known[selected, pad], actual[selected, pad]),
                                         event_forecast="no change",
                                         establishment_event=confusion(np.zeros(count, dtype=bool),
                                                                       np.full(count, phase in ("establishment", "switching"))),
                                         loss_event=confusion(np.zeros(count, dtype=bool),
                                                              np.full(count, phase in ("loss", "switching")))))
    return dict(episode=episode.get("relative_path", str(episode["directory"])),
                case=manifest["case"], partition=protocol["partition"],
                physical_sha256=episode["physical_sha256"], manifest_sha256=episode["manifest_sha256"],
                observations_sha256=manifest["observations_sha256"],
                original_qualification=episode["qualification"], metrics=rows,
                contact_scope="Pad-normal pair loads, not net force. Missing geometric contact distance is unobserved.",
                response_identification="NOT_EVALUATED", candidate_model="NOT_AVAILABLE", control_benefit="NOT_EVALUATED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=Path(__file__).with_name("protocol.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    protocol = json.loads(args.protocol.read_text())
    episodes, duplicates = load_cohort(args.bundle, protocol)
    report = dict(schema_version=1, protocol_sha256=sha256(args.protocol), protocol=protocol,
                  source_sha256={p.name: sha256(p) for p in (Path(__file__), Path(__file__).with_name("data.py"))},
                  independent_repeat_count=0, episodes=[evaluate_episode(e, protocol) for e in episodes],
                  duplicate_copies=duplicates,
                  inference="Descriptive overlapping windows; no confidence interval or held-out/model/causal claim.")
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=str(args.output), unique_episodes=len(episodes), duplicates=len(duplicates))))


if __name__ == "__main__":
    main()
