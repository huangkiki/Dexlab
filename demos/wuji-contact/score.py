"""Independently score saved Wuji contact states; never execute the simulator."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def world_angular_velocity(qpos, qvel):
    """Rotate free-joint local angular velocity by its saved wxyz quaternion."""
    quaternion = qpos[:, 23:27]
    if not np.allclose(np.linalg.norm(quaternion, axis=1), 1., atol=1e-10, rtol=0):
        raise ValueError("Non-unit object quaternion")
    vector, scalar = quaternion[:, 1:], quaternion[:, :1]
    local = qvel[:, 23:26]
    cross = np.cross(vector, local)
    return local + 2 * (scalar * cross + np.cross(vector, cross))


def evaluate(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["state"] != "recorded":
        raise ValueError("An incomplete attempt is not a valid record")
    path = directory / "observations.npz"
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["observations_sha256"]:
        raise ValueError("Raw observations hash mismatch")
    with np.load(path, allow_pickle=False) as archive:
        raw = dict(archive)
    p, effective = manifest["config"], manifest["effective"]
    t, dt = raw["time_s"], effective["timestep"]
    n = round(p["duration_s"] / dt)
    if len(t) != n or not np.allclose(t, np.arange(n) * dt, atol=1e-12, rtol=0):
        raise ValueError("Incomplete or inconsistent physics clock")
    for name, values in raw.items():
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite field: {name}")
        if name not in ("contacts", "contact_offsets") and len(values) != n:
            raise ValueError(f"Record epoch mismatch: {name}")
    for name in ("qpos", "qvel"):
        if not np.allclose(raw[name + "_after"][:-1], raw[name + "_before"][1:], atol=1e-12, rtol=0):
            raise ValueError("State discontinuity or injection")
    contacts, offsets = raw["contacts"], raw["contact_offsets"]
    if (offsets.shape != (n + 1,) or offsets[0] != 0 or offsets[-1] != len(contacts)
            or np.any(np.diff(offsets) < 0) or offsets.dtype.kind not in "iu"):
        raise ValueError("Incomplete contact record")
    obj = effective["object_geom_id"]
    reconstructed = np.zeros((n, 3))
    largest_contact_force = np.zeros(n)
    contact_torque = np.zeros((n, 3))
    normals = np.zeros((n, 2))
    other_support = np.zeros(n)
    pads = [effective["body_names"].index("r_" + finger + "_pad")
            for finger in ("index_finger", "thumb")]
    for i in range(n):
        for c in contacts[offsets[i]:offsets[i + 1]]:
            geom1, geom2, body = map(int, c[:3])
            if obj not in (geom1, geom2) or geom1 == geom2:
                raise ValueError("Contact identity mismatch")
            frame, local = c[6:15].reshape(3, 3), c[16:22]
            if not np.allclose(frame @ frame.T, np.eye(3), atol=1e-6, rtol=0):
                raise ValueError("Non-orthonormal contact frame")
            force = (1 if geom2 == obj else -1) * frame.T @ local[:3]
            reconstructed[i] += force
            largest_contact_force[i] = max(largest_contact_force[i], np.linalg.norm(force))
            moment = (1 if geom2 == obj else -1) * frame.T @ local[3:]
            contact_torque[i] += np.cross(c[3:6] - raw["qpos_before"][i, 20:23], force) + moment
            if body in pads:
                normals[i, pads.index(body)] += local[0]
            else:
                other_support[i] += np.linalg.norm(force)
    if not np.allclose(reconstructed, raw["object_contact_force"], atol=1e-10, rtol=0):
        raise ValueError("Recorded total force disagrees with native contact reconstruction")
    mass, gravity = effective["object_mass"], np.asarray(effective["gravity"])
    dv = raw["qvel_after"][:, 20:23] - raw["qvel_before"][:, 20:23]
    impulse_residual = mass * dv - dt * (reconstructed + mass * gravity + raw["support_force"])
    hold = (t >= p["hold_start_s"]) & (t < p["action_start_s"])
    tail = (t >= p["action_start_s"] + p["action_ramp_s"] + .2)
    no_support = t >= p["support_end_s"]
    anchor = raw["qpos_before"][round(p["support_end_s"] / dt), 20:23]
    displacement = np.linalg.norm(raw["qpos_after"][:, 20:23] - anchor, axis=1)
    speed = np.linalg.norm(raw["qvel_after"][:, 20:23], axis=1)
    bilateral = np.mean(np.all(normals[hold] >= p["min_pad_normal_n"], axis=1))
    limits = np.array(effective["actuator_force_limits"])
    integrity = (effective["eq_count"] == 0
                 and np.all(raw["support_force"][no_support] == 0)
                 and np.all(raw["external_wrenches"][no_support] == 0)
                 and np.all(raw["qfrc_applied"] == 0)
                 and np.all(np.abs(raw["actuator_force"]) <= limits + 1e-10)
                 and not np.any(raw["warnings"]))
    numeric = np.max(np.linalg.norm(impulse_residual, axis=1)) <= p["impulse_error_ns"]
    angular_error = None
    if "angular_impulse_error_nms" in p:
        inertia = np.asarray(effective["object_inertia"])
        if not np.allclose(inertia, inertia[0], atol=1e-16, rtol=0):
            raise ValueError("Angular audit requires the frozen isotropic sphere")
        omega_before = world_angular_velocity(raw["qpos_before"], raw["qvel_before"])
        omega_after = world_angular_velocity(raw["qpos_after"], raw["qvel_after"])
        external_torque = raw["external_wrenches"][:, effective["object_body_id"], 3:]
        angular_residual = inertia[0] * (omega_after - omega_before) - dt * (contact_torque + external_torque)
        angular_error = float(np.linalg.norm(angular_residual, axis=1).max())
        numeric = numeric and angular_error <= p["angular_impulse_error_nms"]
    geometric = np.max(other_support[hold]) <= p["max_other_contact_n"]
    hold_pass = bool(integrity and numeric and geometric
                     and np.max(displacement[hold]) <= p["hold_max_displacement_m"]
                     and np.max(speed[hold]) <= p["hold_max_speed_m_s"]
                     and bilateral >= p["min_bilateral_fraction"]
                     and np.max(raw["max_penetration_m"][hold]) <= p["max_penetration_m"])
    release_drop = anchor[2] - raw["qpos_after"][-1, 22]
    # Opposing pad forces can cancel without releasing the object.
    release_peak_contact = float(np.max(largest_contact_force[tail]))
    free_tail = release_peak_contact <= p["release_max_contact_n"]
    release_conditions = bool(release_drop >= p["release_min_drop_m"] and free_tail)
    # Falling after failed acquisition is not evidence of commanded release.
    release_pass = bool(hold_pass and release_conditions)
    unload = None
    if manifest["case"].startswith("unload-"):
        finger = 0 if manifest["case"] == "unload-index_finger" else 1
        baseline = float(np.mean(normals[hold, finger]))
        measured = float(np.max(normals[tail, finger]))
        unload = dict(baseline_normal_n=baseline, tail_max_normal_n=measured,
                      pass_unload=bool(measured <= max(p["min_pad_normal_n"], .05 * baseline)),
                      drop_m=float(release_drop))
    return dict(case=manifest["case"],
                observations_sha256=manifest["observations_sha256"],
                manifest_sha256=hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
                scorer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                record_integrity_pass=bool(integrity),
                numerical_balance_pass=bool(numeric), hold_pass=hold_pass, release_pass=release_pass,
                qualification_pass=bool(hold_pass and release_pass), unload=unload,
                metrics=dict(hold_max_displacement_m=float(np.max(displacement[hold])),
                             hold_max_speed_m_s=float(np.max(speed[hold])),
                             bilateral_fraction=float(bilateral), hold_mean_pad_normals_n=np.mean(normals[hold],axis=0).tolist(),
                             other_support_max_n=float(np.max(other_support[hold])),
                             impulse_error_max_ns=float(np.max(np.linalg.norm(impulse_residual, axis=1))),
                             impulse_error_total_ns=np.sum(impulse_residual, axis=0).tolist(),
                             angular_impulse_error_max_nms=angular_error,
                             release_drop_m=float(release_drop), release_no_contact=free_tail,
                             release_max_single_contact_n=release_peak_contact,
                             release_conditions_met=release_conditions,
                             max_penetration_m=float(np.max(raw["max_penetration_m"])),
                             saturation_fraction=float(np.mean(np.abs(raw["requested_torque"]) >= limits)),
                             solver_iterations_max=int(np.max(raw["solver_niter"])),
                             solver_last_gradient_max=float(np.max(raw["solver_last_gradient"])),
                             physics_wall_s=float(np.sum(raw["step_wall_s"]))),
                scope="Synthetic fixed-wrist native contact qualification. Task failure alone is not solver failure or hardware validation.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.directory)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
