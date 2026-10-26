#!/usr/bin/env python3
"""Compare the two frozen native probes offline before full AMP evaluations."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.amp_lift_audit import check_step_clock, compare_contact_decoding, compare_probe_values
from dexlab.libero_substeps import read_chunk
from dexlab.migration_budget import MigrationBudget


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_gpu_resources(telemetry, expected):
    """Keep sampled GPU limits explicit; missing observations never mean zero."""
    budget = telemetry.get("gpu_budget") or {}
    if budget.get("limit_mib") != expected["limit_mib"] or \
            budget.get("sampling_interval_s") != expected["sampling_interval_s"] or \
            not budget.get("uuid", "").startswith("GPU-") or telemetry.get("gpu_budget_stop_reason"):
        raise ValueError("Missing or failed sampled GPU resource budget")
    observations = [telemetry.get("initial_gpu_memory_mib")]
    observations += [sample.get("devices") for sample in telemetry.get("gpu_memory_samples_mib", [])]
    if telemetry.get("state") == "completed":
        observations.append(telemetry.get("final_gpu_memory_mib"))
        if not telemetry.get("gpu_memory_samples_mib"):
            raise ValueError("Missing GPU samples during native execution")
    for rows in observations:
        selected = [row.split(",") for row in rows or [] if row.split(",")[0].strip() == budget["uuid"]]
        if len(selected) != 1 or len(selected[0]) != 3:
            raise ValueError("Selected GPU telemetry is missing or ambiguous")
        used, total = map(int, selected[0][1:])
        if not 0 <= used <= expected["limit_mib"] or total - expected["limit_mib"] < expected["minimum_device_reserve_mib"]:
            raise ValueError("Sampled GPU resource envelope or reserve was exceeded")
    return budget


def completed_resources(invocation, gpu_budget):
    """Require the enclosing service's final observation, not a process start."""
    path = Path(invocation["resources_receipt"])
    receipt = json.loads(path.read_text())
    telemetry = receipt.get("telemetry") or {}
    final = telemetry.get("final") or {}
    limits = telemetry.get("effective_limits") or {}
    service = receipt.get("service", "")
    if receipt.get("state") != "completed" or receipt.get("returncode") != 0 or \
            telemetry.get("state") != "completed" or telemetry.get("returncode") != 0 or \
            not final or not service.startswith("dexlab-bounded-") or \
            f"/{service}.service" not in invocation["cgroup"]:
        raise ValueError("Probe has no matching successful final resource telemetry")
    events = dict(line.split() for line in final["memory.events"].splitlines())
    if any(int(events.get(name, 0)) for name in ("oom", "oom_kill", "oom_group_kill")) or \
            limits.get("memory.swap.max") != "0" or limits.get("memory.max") in (None, "max"):
        raise ValueError("Probe resource admission failed")
    plan = receipt.get("resource_plan") or {}
    measurement = plan.get("measurement") or {}
    if not plan.get("profile", "").startswith("adaptive-") or \
            plan.get("profile") != telemetry.get("profile") or \
            len(measurement.get("sha256", "")) != 64 or \
            not np.isfinite(measurement.get("peak_mib", float("nan"))) or \
            measurement.get("peak_mib", 0) <= 0:
        raise ValueError("Probe requires a frozen measured adaptive resource plan")
    gpu = check_gpu_resources(telemetry, gpu_budget)
    return {"sha256": sha256(path), "effective_limits": limits,
            "resource_plan": plan, "gpu_budget": gpu, "wall_s": receipt["wall_s"]}


def qualify(budget, protocol, protocol_sha):
    attempts = budget.status()["attempts"]
    frozen_resources = json.loads((budget.root / "manifest.json").read_text())["resource_plan"]
    probes, identities, invocations, resources = {}, {}, {}, {}
    for case in ("probe-native", "probe-recorded"):
        matches = [a for a in attempts if a["case_id"] == case]
        if len(matches) != 1 or not matches[0]["terminal"] or \
                matches[0]["terminal"]["outcome"] != "recorded":
            raise ValueError("Both named fresh-process probes must have completed")
        directory = Path(matches[0]["handle"]["output"])
        invocation = directory / "invocation.json"
        identity = sha256(invocation)
        if matches[0]["terminal"]["evidence_sha256"] != identity:
            raise ValueError("Probe invocation differs from the durable ledger")
        data = json.loads(invocation.read_text())
        expected = next(c for c in protocol["cases"] if c["id"] == case)
        if data["status"] != "completed" or data["completed_actions"] != expected["actions"] or \
                data["case"] != expected or data["protocol_sha256"] != protocol_sha:
            raise ValueError("Probe is incomplete or belongs to another protocol")
        probes[case], identities[case], invocations[case] = directory, identity, data
        resources[case] = completed_resources(data, protocol["gpu_budget"])
        if resources[case]["resource_plan"] != frozen_resources:
            raise ValueError("Probe resource plan differs from the frozen native budget")
    left, right = (invocations[case] for case in ("probe-native", "probe-recorded"))
    for key in ("source", "runtime", "native_payload", "runner_sha256", "recorder_sha256", "effective_conditions"):
        if left[key] != right[key]:
            raise ValueError(f"Native probe identity differs: {key}")
    for key in ("effective_limits", "resource_plan", "gpu_budget"):
        if resources["probe-native"][key] != resources["probe-recorded"][key]:
            raise ValueError(f"Probe resource envelope changed: {key}")
    checks = protocol["checks"]
    tolerance = {"atol": checks["state_parity_atol"], "rtol": checks["state_parity_rtol"]}
    reference, recorded = (probes[case] for case in ("probe-native", "probe-recorded"))
    max_error = 0.
    evidence = {}

    def compare_chunks(relative):
        nonlocal max_error
        first, second = reference / relative, recorded / relative
        a, b = read_chunk(first), read_chunk(second)
        if len(a) != 1 or len(b) != 1:
            raise ValueError("Expected one complete control record per action")
        max_error = max(max_error, compare_probe_values(a[0], b[0], **tolerance, path=relative))
        evidence[relative] = {"reference": sha256(first), "recorded": sha256(second)}
        return b[0]

    previous = compare_chunks("initial-state.npz")
    with np.load(reference / "native/effective-model.npz", allow_pickle=False) as a, \
            np.load(recorded / "native/effective-model.npz", allow_pickle=False) as b:
        compare_probe_values(dict(a), dict(b), atol=0., rtol=0., path="effective-model")
    for case, directory in probes.items():
        evidence[case] = {name: sha256(directory / "native" / name)
                          for name in ("effective-model.npz", "compiled-template.mjb", "recording.json")}
    native_meta = json.loads((reference / "native/recording.json").read_text())
    metadata = json.loads((recorded / "native/recording.json").read_text())
    for key in ("options", "time_dtype", "use_cuda_graph", "force_decoder_sha256", "body_names", "geom_names",
                "joint_names", "site_names", "actuator_names", "epochs", "force_order"):
        if native_meta[key] != metadata[key]:
            raise ValueError(f"Probe compiled metadata differs: {key}")
    if metadata["status"] != "completed" or not metadata["use_cuda_graph"]:
        raise ValueError("The original CUDA graph and complete archive are required")
    count = left["case"]["actions"]
    decimation = protocol["conditions"]["decimation"]
    if len(metadata["chunks"]) != count or metadata["substeps"] != count * decimation:
        raise ValueError("Native probe substeps are missing")
    if {path.name for path in (recorded / "native/substeps").glob("*.npz")} != \
            {f"action-{index:06d}.npz" for index in range(count)}:
        raise ValueError("Unexpected native-record extent")
    if len(list((reference / "actions").glob("*.npz"))) != count or \
            len(list((recorded / "actions").glob("*.npz"))) != count:
        raise ValueError("Unexpected control-record extent")
    maximum_force_error = 0.
    contacts = 0
    loaded_contacts = 0
    for index, chunk in enumerate(metadata["chunks"]):
        action = compare_chunks(f"actions/action-{index:06d}.npz")
        name = f"action-{index:06d}.npz"
        if chunk != {"name": name, "action_index": index, "substeps": decimation}:
            raise ValueError("Broken native chunk sequence")
        path = recorded / "native/substeps" / name
        rows = read_chunk(path)
        evidence[f"native/substeps/{name}"] = sha256(path)
        if len(rows) != decimation:
            raise ValueError("Truncated native action")
        for substep, row in enumerate(rows):
            if row["sequence"] != index * decimation + substep or row["action_index"] != index:
                raise ValueError("Broken native substep sequence")
            before, after = row["before"], row["after"]
            if row["nefc"] != len(row["efc_force"]) or np.any(row["contacts"]["worldid"] != 0):
                raise ValueError("Constraint extent or contact world differs")
            for phase in (before, after):
                if any(not np.isfinite(value).all() for value in phase.values()):
                    raise ValueError("Nonfinite native observation")
            check_step_clock(before["time"], after["time"], dt=protocol["conditions"]["physics_dt_s"],
                             dtype=metadata["time_dtype"])
            for field in ("qpos", "qvel", "time"):
                compare_probe_values(previous[field], before[field], atol=0., rtol=0., path=f"native continuity.{field}")
            previous = after
            decoded = compare_contact_decoding(row["contacts"], row["efc_force"],
                cone=metadata["options"]["cone"], atol=checks["force_decode_atol"],
                rtol=checks["force_decode_rtol"])
            if not decoded["passed"]:
                raise ValueError("Independent native contact-force decoding failed")
            maximum_force_error = max(maximum_force_error, decoded["maximum_component_error"])
            contacts += decoded["contacts"]
            loaded_contacts += int(np.count_nonzero(np.linalg.norm(row["contacts"]["local_force"][:, :3], axis=1)
                                                   > checks["loaded_contact_threshold_n"]))
        for field in ("qpos", "qvel"):
            compare_probe_values(rows[-1]["after"][field], action["feedback"][field],
                                 atol=0., rtol=0., path=f"control-boundary.{field}")
    if loaded_contacts == 0:
        raise ValueError("No loaded contact exercised the recorder in this probe")
    return {
        "passed": True, "protocol_sha256": protocol_sha, "probe_invocation_sha256": identities,
        "native_payload": left["native_payload"], "evidence_sha256": evidence,
        "resources": resources,
        "maximum_control_component_error": max_error,
        "maximum_contact_force_component_error": maximum_force_error, "contacts": contacts,
        "loaded_contacts": loaded_contacts,
        "scope": "Short native recorder parity and force representation only; no lift or physical qualification",
        "task_success": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=Path, required=True)
    args = parser.parse_args()
    budget = MigrationBudget(args.budget)
    raw = Path(__file__).with_name("protocol.json").read_bytes()
    protocol_sha = hashlib.sha256(raw).hexdigest()
    if json.loads((budget.root / "manifest.json").read_text())["protocol_sha256"] != protocol_sha:
        parser.error("Budget and protocol differ")
    target = budget.root / "qualification.json"
    if target.exists():
        parser.error("Preserve the previous qualification; do not overwrite a campaign")
    try:
        result = qualify(budget, json.loads(raw), protocol_sha)
    except Exception as error:
        result = {"passed": False, "protocol_sha256": protocol_sha,
                  "error": f"{type(error).__name__}: {error}", "task_success": None}
        with target.open("x") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
        raise
    with target.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(target)


if __name__ == "__main__":
    main()
