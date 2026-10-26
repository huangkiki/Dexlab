"""Audit a complete visible prefix; this alone never identifies a causal effect."""

import argparse
import json
from pathlib import Path

import numpy as np

from baselines import orientation_error
from data import SCORE, load_episode, sha256

# Every tolerance has a unit and is explicitly supplied by a future frozen protocol.
UNITS = dict(joint_position_rad="rad", object_position_m="m", object_orientation_rad="rad",
             joint_velocity_rad_s="rad/s", object_velocity_m_s="m/s", object_omega_rad_s="rad/s",
             target_rad="rad", requested_torque_nm="N m", actuator_force_nm="N m",
             support_force_n="N", external_force_n="N", external_torque_nm="N m",
             applied_joint_torque_nm="N m", applied_object_force_n="N", applied_object_torque_nm="N m",
             object_contact_force_n="N", pad_normal_n="N", contact_position_m="m",
             contact_frame="1", contact_distance_m="m", contact_force_n="N", contact_torque_nm="N m")


def maximum_difference(a, b):
    if a.shape != b.shape:
        raise ValueError("Observable shape mismatch")
    return float(np.max(np.abs(a - b), initial=0))


def prefix_differences(a, b, onset):
    """States include the onset; solved observations/actions stop strictly before it."""
    x, y = a["raw"], b["raw"]
    states, solved = slice(0, onset + 1), slice(0, onset)
    differences = {}
    fields = {
        "joint_position_rad": ("qpos_before", slice(0, 20), states),
        "object_position_m": ("qpos_before", slice(20, 23), states),
        "joint_velocity_rad_s": ("qvel_before", slice(0, 20), states),
        "object_velocity_m_s": ("qvel_before", slice(20, 23), states),
        "target_rad": ("target", slice(None), solved),
        "requested_torque_nm": ("requested_torque", slice(None), solved),
        "actuator_force_nm": ("actuator_force", slice(None), solved),
        "support_force_n": ("support_force", slice(None), solved),
        "object_contact_force_n": ("object_contact_force", slice(None), solved),
        "external_force_n": ("external_wrenches", slice(0, 3), solved),
        "external_torque_nm": ("external_wrenches", slice(3, 6), solved),
        "applied_joint_torque_nm": ("qfrc_applied", slice(0, 20), solved),
        "applied_object_force_n": ("qfrc_applied", slice(20, 23), solved),
        "applied_object_torque_nm": ("qfrc_applied", slice(23, 26), solved),
    }
    for name, (field, columns, rows) in fields.items():
        differences[name] = maximum_difference(x[field][rows, ..., columns], y[field][rows, ..., columns])
    differences["object_orientation_rad"] = float(orientation_error(x["qpos_before"][states, 23:27], y["qpos_before"][states, 23:27]).max())
    differences["object_omega_rad_s"] = maximum_difference(
        SCORE.world_angular_velocity(x["qpos_before"][states], x["qvel_before"][states]),
        SCORE.world_angular_velocity(y["qpos_before"][states], y["qvel_before"][states]))
    differences["pad_normal_n"] = maximum_difference(a["loads"][solved], b["loads"][solved])
    contact_identity_matches = True
    for field in ("contact_position_m", "contact_frame", "contact_distance_m", "contact_force_n", "contact_torque_nm"):
        differences[field] = 0.
    # Conservative native-order comparison. A changed ordering/count is unqualified,
    # never silently paired by proximity and interpreted as identical solver state.
    for i in range(onset):
        ca = x["contacts"][x["contact_offsets"][i]:x["contact_offsets"][i + 1]]
        cb = y["contacts"][y["contact_offsets"][i]:y["contact_offsets"][i + 1]]
        if ca.shape != cb.shape or not np.array_equal(ca[:, :3], cb[:, :3]):
            contact_identity_matches = False
            continue
        for name, cols in (("contact_position_m", slice(3, 6)), ("contact_frame", slice(6, 15)),
                           ("contact_distance_m", slice(15, 16)), ("contact_force_n", slice(16, 19)),
                           ("contact_torque_nm", slice(19, 22))):
            differences[name] = max(differences[name], maximum_difference(ca[:, cols], cb[:, cols]))
    return differences, contact_identity_matches


def compare(baseline, repeat, intervention, protocol):
    tolerances = protocol["prefix_tolerances"]
    if set(tolerances) != set(UNITS):
        raise ValueError("Require an explicit unit-specific tolerance for every observable group")
    if any(not np.isfinite(v) or v < 0 for v in tolerances.values()):
        raise ValueError("Tolerances must be finite and nonnegative")
    if not isinstance(protocol.get("tolerance_basis"), str) or not protocol["tolerance_basis"].strip():
        raise ValueError("Record a reviewed tolerance basis; no source-specific defaults are assumed")
    time = baseline["raw"]["time_s"]
    onset_time, horizon = protocol["intervention_start_s"], protocol["horizon_s"]
    if not np.isfinite([onset_time, horizon]).all() or onset_time <= 0 or horizon <= 0:
        raise ValueError("Require positive finite onset and horizon")
    dt = baseline["manifest"]["effective"]["timestep"]
    onset = round(onset_time / dt)
    end = round((onset_time + horizon) / dt)
    if end >= len(time) or onset >= end or not np.allclose([time[onset], time[end]], [onset_time, onset_time + horizon], atol=1e-12, rtol=0):
        raise ValueError("Onset/horizon must match available native ticks")
    reasons, comparisons = [], {}
    for role, episode in (("repeat", repeat), ("intervention", intervention)):
        if not np.array_equal(time, episode["raw"]["time_s"]):
            raise ValueError("All branches require identical complete native time grids")
        for field in ("source_sha256", "asset_manifest_sha256", "runtime", "config", "force_epoch"):
            if baseline["manifest"][field] != episode["manifest"][field]:
                reasons.append(f"{role}: {field} differs")
        # This is only the saved subset, not a complete compiled-model identity.
        for key in set(baseline["manifest"]["effective"]) | set(episode["manifest"]["effective"]):
            if key == "object_contact_friction_readbacks":
                continue  # Observed over the entire episode, including the intervention.
            if baseline["manifest"]["effective"].get(key) != episode["manifest"]["effective"].get(key):
                reasons.append(f"{role}: effective {key} differs")
        maxima, contacts_match = prefix_differences(baseline, episode, onset)
        exceeded = [key for key, value in maxima.items() if value > tolerances[key]]
        comparisons[role] = dict(maximum_absolute_difference=maxima, exceeded=exceeded,
                                 native_contact_identity_matches=contacts_match)
        reasons.extend(f"{role}: prefix {key}" for key in exceeded)
        if not contacts_match:
            reasons.append(f"{role}: native contact identity/order/count differs")
    window = slice(onset, end + 1)
    x, r, z = (e["raw"] for e in (baseline, repeat, intervention))
    if not np.array_equal(x["target"], r["target"]):
        reasons.append("repeat: target command differs")
    if np.array_equal(x["target"][window], z["target"][window]):
        reasons.append("intervention: no target command change in the declared horizon")
    for field in ("support_force", "external_wrenches", "qfrc_applied"):
        if not np.array_equal(x[field][window], z[field][window]) or not np.array_equal(x[field][window], r[field][window]):
            reasons.append(f"post-onset exogenous input differs: {field}")
    noise = r["qpos_before"][window, 20:23] - x["qpos_before"][window, 20:23]
    effect = z["qpos_before"][window, 20:23] - x["qpos_before"][window, 20:23]
    return dict(schema_version=1, visible_prefix_compatible=not reasons, reasons=reasons,
                protocol=protocol, units=UNITS, comparisons=comparisons,
                repeat_max_position_difference_m=float(np.linalg.norm(noise, axis=1).max()),
                intervention_max_position_difference_m=float(np.linalg.norm(effect, axis=1).max()),
                identity={role: dict(manifest_sha256=e["manifest_sha256"], physical_sha256=e["physical_sha256"])
                          for role, e in (("baseline", baseline), ("repeat", repeat), ("intervention", intervention))},
                response_identification="UNIDENTIFIED",
                unresolved=["Fresh-process repetition and complete compiled-model identity are not established by this record format.",
                            "A calibrated repeat envelope and predeclared effect/direction thresholds are still required.",
                            "Compatible visible prefixes do not establish identical hidden solver caches."],
                candidate_model_prediction=None, control_benefit=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "repeat", "intervention", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = compare(*(load_episode(getattr(args, role)) for role in ("baseline", "repeat", "intervention")),
                     json.loads(args.protocol.read_text()))
    report["source_sha256"] = {name: sha256(Path(__file__).with_name(name)) for name in ("prefix.py", "data.py", "baselines.py")}
    report["protocol_sha256"] = sha256(args.protocol)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(visible_prefix_compatible=report["visible_prefix_compatible"], response_identification="UNIDENTIFIED")))


if __name__ == "__main__":
    main()
