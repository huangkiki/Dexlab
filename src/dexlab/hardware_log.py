"""Read-only intake checks for D06 hardware logs; never controls a robot."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


# signal -> (unit, width, provenance kind). Device-specific conversions stay explicit.
SIGNALS = {
    "joint_position_actual": ("rad", 6, "feedback"),
    "joint_position_target": ("rad", 6, "command"),
    "joint_velocity_actual": ("rad/s", 6, "feedback"),
    "tcp_pose_actual": ("m,rad_rotvec", 6, "feedback"),
    "tcp_wrench_actual": ("N,Nm", 6, "feedback"),
    "gripper_aperture_actual": ("m", 1, "feedback"),
    "gripper_aperture_target": ("m", 1, "command"),
    "gripper_setting_target": ("device_code", 1, "command"),
    "gripper_force_reported": ("N", 1, "feedback"),
    "gripper_current_actual": ("A", 1, "feedback"),
    "normal_force_reference": ("N", 1, "reference"),
    "displacement_reference": ("m", 1, "reference"),
    "video_frame_index": ("count", 1, "reference"),
    "device_status": ("device_code", 1, "feedback"),
}
UR_FIELDS = {
    "joint_position_actual": "actual_q", "joint_position_target": "target_q",
    "joint_velocity_actual": "actual_qd", "tcp_pose_actual": "actual_TCP_pose",
    "tcp_wrench_actual": "actual_TCP_force",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(content):
    return json.loads(content, object_pairs_hook=unique_object)


def validate(directory: Path) -> dict:
    """Validate an explicit manifest and asynchronous samples, without rewriting input.

    Missing metadata is reported separately from corrupt data. A format-valid file
    is not scientific acceptance, a calibrated sensor, or permission to move hardware.
    """
    directory = directory.resolve()
    manifest = read_json((directory / "manifest.json").read_text())
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1, "unsupported schema_version")
    require(manifest["kind"] in {"preparation", "synthetic", "measured"}, "invalid kind")
    require(manifest["protocol"] == "ctag-contact-v1", "unknown protocol")
    missing, blockers = [], []
    needed_channels = {name for trial in manifest["trials"] for name in trial["required_channels"]}
    require(needed_channels <= manifest["channels"].keys(), "unknown required channel")
    needed_devices = {manifest["channels"][name]["device"] for name in needed_channels}
    needed_clocks = {manifest["channels"][name]["clock"] for name in needed_channels} | {"host"}
    needed_frames = {manifest["channels"][name]["frame"] for name in needed_channels}

    def mark(message, blocking=True):
        missing.append(message)
        if blocking:
            blockers.append(message)

    devices = manifest["devices"]
    for name, model in (("arm_left", "UR7e"), ("arm_right", "UR7e"),
                        ("gripper_left", "CTAG2F90D"), ("gripper_right", "CTAG2F90D")):
        require(devices[name]["model"] == model, f"{name}: wrong device model")
    for name, device in devices.items():
        for field in ("firmware", "interface"):
            require(device[field] is None or text(device[field]), f"{name}: invalid {field}")
            if device[field] is None:
                mark(f"device:{name}:{field}", name in needed_devices)
    artifacts = manifest["artifacts"]
    for name, expected in artifacts.items():
        path = (directory / name).resolve()
        require(not Path(name).is_absolute() and path.is_relative_to(directory), "artifact escapes bundle")
        require(path.is_file(), f"missing artifact: {name}")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        require(actual == expected, f"artifact hash mismatch: {name}")

    def evidence(value):
        return text(value) and value in artifacts

    clocks = manifest["clocks"]
    frames = manifest["frames"]
    require("host" in clocks, "host clock is required")
    for name, clock in clocks.items():
        require(text(clock["description"]), f"{name}: missing clock description")
        for key in ("offset_to_host_s", "scale_to_host", "uncertainty_s"):
            value = clock[key]
            require(value is None or finite(value), f"{name}: invalid {key}")
            if value is None:
                mark(f"clock:{name}:{key}", name in needed_clocks)
        require(clock["scale_to_host"] is None or clock["scale_to_host"] > 0, "invalid clock scale")
        require(clock["uncertainty_s"] is None or clock["uncertainty_s"] >= 0, "negative clock uncertainty")
        if not evidence(clock["evidence"]):
            mark(f"clock:{name}:evidence", name in needed_clocks)
    for name, frame in frames.items():
        require(text(frame["description"]), f"{name}: missing frame convention")
        if not evidence(frame["evidence"]):
            mark(f"frame:{name}:evidence", name in needed_frames)
    channels = manifest["channels"]
    require(bool(channels), "no channels declared")
    for name, channel in channels.items():
        unit, width, kind = SIGNALS[channel["signal"]]
        require(channel["unit"] == unit and channel["kind"] == kind, f"{name}: unit or provenance mismatch")
        require(channel["device"] in devices, f"{name}: unknown device")
        require(channel["frame"] in frames and channel["clock"] in clocks, f"{name}: unknown frame/clock")
        require(channel["status"] in {"unverified", "unavailable", "verified"}, f"{name}: invalid status")
        require(text(channel["source_field"]) or channel["source_field"] is None, f"{name}: invalid source field")
        if devices[channel["device"]]["model"] == "UR7e" and channel["signal"] in UR_FIELDS:
            require(channel["source_field"] in (None, UR_FIELDS[channel["signal"]]), f"{name}: wrong UR source field")
        if channel["status"] == "verified":
            require(text(channel["source_field"]) and evidence(channel["evidence"]), f"{name}: verification evidence missing")
        else:
            mark(f"channel:{name}:{channel['status']}", name in needed_channels)
        uncertainty = channel["uncertainty"]
        if uncertainty is None:
            mark(f"channel:{name}:uncertainty", name in needed_channels)
        else:
            values = uncertainty["absolute_bounds"]
            require(isinstance(values, list) and len(values) == width
                    and all(finite(x) and x >= 0 for x in values), f"{name}: invalid uncertainty bounds")
            require(text(uncertainty["basis"]) and evidence(uncertainty["evidence"]), f"{name}: uncertainty evidence missing")

    trials, groups = {}, {}
    for trial in manifest["trials"]:
        name = trial["id"]
        require(text(name) and name not in trials, "duplicate or empty trial id")
        require(trial["split"] in {"development", "calibration", "test"}, f"{name}: invalid split")
        require(trial["status"] in {"planned", "complete", "aborted"}, f"{name}: invalid status")
        require(type(trial["repeat"]) is int and trial["repeat"] >= 1, f"{name}: invalid repeat")
        require(text(trial["conditions"]), f"{name}: missing conditions")
        for field in ("specimen_id", "condition_id"):
            require(text(trial[field]), f"{name}: missing {field}")
            key = (field, trial[field])
            require(key not in groups or groups[key] == trial["split"], f"{name}: {field} leaks across splits")
            groups[key] = trial["split"]
        needed = trial["required_channels"]
        require(isinstance(needed, list) and needed and len(set(needed)) == len(needed)
                and all(x in channels for x in needed), f"{name}: invalid required channels")
        require({"normal_force_reference", "displacement_reference"}
                <= {channels[x]["signal"] for x in needed}, f"{name}: independent force/displacement required")
        require(trial["status"] != "aborted" or text(trial["failure_reason"]), f"{name}: failure reason missing")
        if trial["status"] != "complete":
            mark(f"trial:{name}:{trial['status']}")
        trials[name] = trial
    require(bool(trials), "no trials declared")

    previous, counts, gaps = {}, Counter(), Counter()
    sample_count = 0
    with (directory / "samples.jsonl").open() as stream:
        for line_number, line in enumerate(stream, 1):
            row = read_json(line)
            prefix = f"line {line_number}"
            require(set(row) == {"trial_id", "channel", "sequence", "host_time_s",
                                 "device_time_s", "value", "quality", "reason"}, f"{prefix}: wrong sample fields")
            name, trial = row["channel"], row["trial_id"]
            require(name in channels and trial in trials, f"{prefix}: unknown channel/trial")
            require(trials[trial]["status"] != "planned", f"{prefix}: planned trial has samples")
            channel = channels[name]
            sequence, host, device = row["sequence"], row["host_time_s"], row["device_time_s"]
            require(type(sequence) is int and sequence >= 0, f"{prefix}: invalid sequence")
            require(finite(host) and host >= 0, f"{prefix}: invalid host time")
            require(device is None or (finite(device) and device >= 0), f"{prefix}: invalid device time")
            value = row["value"]
            require(row["quality"] in {"valid", "missing", "invalid"}, f"{prefix}: invalid quality")
            if row["quality"] == "valid":
                require(channel["status"] == "verified", f"{prefix}: unverified channel has valid measurement")
                width = SIGNALS[channel["signal"]][1]
                require(isinstance(value, list) and len(value) == width
                        and all(finite(x) for x in value), f"{prefix}: invalid value shape/number")
                require(row["reason"] is None, f"{prefix}: valid sample must have null reason")
                counts[(trial, name)] += 1
            else:
                require(value is None and text(row["reason"]), f"{prefix}: missing/invalid value needs null and reason")
                gaps[name] += 1
            key = (trial, name)
            if key in previous:
                old_sequence, old_host, old_device = previous[key]
                require(sequence > old_sequence and host >= old_host, f"{prefix}: reordered or duplicate sample")
                require(device is None or old_device is None or device > old_device, f"{prefix}: device clock repeated/reset")
                gaps[name] += sequence - old_sequence - 1
            # Retain last known device time across missing timestamp records.
            previous[key] = (sequence, host, device if device is not None else previous.get(key, (0, 0, None))[2])
            if device is None:
                mark(f"channel:{name}:device_time", name in needed_channels)
            sample_count += 1
    for name, trial in trials.items():
        for channel in trial["required_channels"]:
            if not counts[(name, channel)]:
                mark(f"trial:{name}:no_valid_samples:{channel}")
    if not artifacts:
        mark("artifacts:raw_sources_and_verification")
    return {
        "format_valid": True, "kind": manifest["kind"], "sample_count": sample_count,
        "trial_status_counts": dict(Counter(t["status"] for t in trials.values())),
        "missing_metadata_or_data": sorted(set(missing)), "observed_gap_counts": dict(gaps),
        "intake_blockers": sorted(set(blockers)),
        "measured_intake_ready": manifest["kind"] == "measured" and not blockers
        and not any(gaps[name] for name in needed_channels),
        "scientific_acceptance": "not_assessed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--require-measured", action="store_true",
                        help="also require measured kind and complete intake metadata; not scientific acceptance")
    args = parser.parse_args()
    try:
        report = validate(args.directory)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        print(json.dumps({"format_valid": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 2 if args.require_measured and not report["measured_intake_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
