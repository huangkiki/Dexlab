"""Offline SDF grasp acceptance; recorded forces never feed the controller."""

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

APPLE = Path(__file__).resolve().parent.parent / "assets/apple"


def relative_motion(apple, wrist):
    positions = (
        Rotation.from_quat(wrist[:, 3:]).inv().apply(apple[:, :3] - wrist[:, :3])
    )
    rotations = Rotation.from_quat(wrist[:, 3:]).inv() * Rotation.from_quat(
        apple[:, 3:]
    )
    return {
        "maximum_wrist_relative_displacement_mm": float(
            np.linalg.norm(positions - positions[0], axis=1).max() * 1000
        ),
        "maximum_wrist_relative_rotation_deg": float(
            np.rad2deg((rotations[0].inv() * rotations).magnitude()).max()
        ),
    }


def verify_grasp(directory, *, expected_mass=0.2):
    if not np.isfinite(expected_mass) or expected_mass <= 0:
        raise ValueError("Expected mass must be finite and positive")
    weight = expected_mass * 9.81
    directory = Path(directory)
    engine = json.loads((directory / "engine.json").read_text())
    with np.load(directory / "sdf-dynamics.npz") as archive:
        log = dict(archive)
    with np.load(directory / "sdf-contacts.npz") as archive:
        contacts = archive["contacts"]
    if engine["backend"] == "mujoco":
        from dexlab.mujoco_artifacts import load_model

        model = load_model(directory)
        identities = {
            "official_wheel": engine.get("wheel_record_matches") is True
            and engine.get("engine_patch") is None,
            "native_sdf_apple_and_pads": all(
                model.geom("collision_" + n).type[0] == mujoco.mjtGeom.mjGEOM_SDF
                and model.geom_plugin[model.geom("collision_" + n).id] == -1
                for n in ("apple", "r_thumb_pad", "r_index_finger_pad")
            ),
            "free_apple_no_attachment": bool(
                model.joint("apple_free").type[0] == mujoco.mjtJoint.mjJNT_FREE
                and model.neq == 0
                and model.nmocap == 0
            ),
            "original_apple_mass": bool(
                np.isclose(model.body("apple").mass[0], expected_mass)
            ),
            "no_apple_actuation": bool(
                all(
                    int(j) != model.joint("apple_free").id
                    for j in model.actuator_trnid[:, 0]
                )
            ),
        }
        body_lookup = {i: model.body(i).name for i in range(model.nbody)}
    else:
        identities = {
            "fp64": engine.get("fp64") is True,
            "native_sdf_apple_and_pads": engine.get("grasp_collider_types")
            == {n: "SDF" for n in ("apple", "r_thumb_pad", "r_index_finger_pad")},
            "free_apple_no_attachment": engine.get("apple_dynamic") is True,
            "original_apple_mass": bool(np.isclose(engine["mass_kg"], expected_mass)),
        }
        body_lookup = dict(enumerate(engine["body_names"]))
    dt = float(engine["dt"])
    count = len(log["time"])
    hold = (log["time"] >= 11) & (log["time"] < 14)
    checks = {
        "completed": bool(engine["completed"] and count == round(14 / dt)),
        "uniform_step_coverage": bool(
            np.allclose(log["time"], np.arange(count) * dt, atol=1e-10)
        ),
        "finite_records": all(np.isfinite(x).all() for x in log.values())
        and bool(np.isfinite(contacts).all()),
        **identities,
        "fixed_base": bool(
            np.max(np.abs(log["base_pose"] - log["base_pose"][0])) < 1e-12
        ),
        "no_solver_warnings": bool(np.max(log["warnings"]) == 0),
        "bounded_penetration": bool(np.max(log["penetration"]) < 0.001),
        "full_hold": int(hold.sum()) == round(3 / dt),
    }
    stats = {"maximum_penetration_mm": float(np.max(log["penetration"]) * 1000)}
    if not all(
        checks[k]
        for k in ("completed", "uniform_step_coverage", "finite_records", "full_hold")
    ):
        return {
            "passed": False,
            "backend": engine["backend"],
            "scope": "14 s stem grasp; 11-14 s hold",
            "checks": checks,
            "metrics": stats,
            "error": "Incomplete or invalid physics-step archive",
        }
    if hold.any():
        stats.update(relative_motion(log["apple_pose"][hold], log["wrist_pose"][hold]))
        stats["minimum_clearance_mm"] = float(log["clearance"][hold].min() * 1000)
        stats["mean_hand_support_weight_ratio"] = float(
            log["hand"][hold, 2].mean() / weight
        )
        checks.update(
            lifted=stats["minimum_clearance_mm"] > 70,
            hand_supports_weight=abs(stats["mean_hand_support_weight_ratio"] - 1)
            < 0.05,
            no_table_support=bool(
                np.linalg.norm(log["table"][hold], axis=1).max() < 0.05
            ),
            no_other_support=bool(
                np.linalg.norm(log["other"][hold], axis=1).max() < 0.05
            ),
            retained=stats["maximum_wrist_relative_displacement_mm"] < 2
            and stats["maximum_wrist_relative_rotation_deg"] < 5,
        )
    hold_contacts = contacts[(contacts[:, 0] >= 11) & (contacts[:, 0] < 14)]
    contact_steps = np.rint(contacts[:, 0] / dt).astype(int)
    checks["contact_step_times_valid"] = bool(
        np.allclose(contacts[:, 0], contact_steps * dt, atol=1e-10, rtol=0)
        and np.all((contact_steps >= 0) & (contact_steps < count))
    )
    sums = {
        key: np.zeros(count) for key in ("thumb", "index", "off_stem", "other_hand")
    }
    reconciled = np.zeros((count, 3))
    if len(hold_contacts):
        points = hold_contacts[:, 2:5]
        fruit = trimesh.load_mesh(APPLE / "apple-collision.obj", process=False)
        stem = trimesh.load_mesh(APPLE / "stem-collision.obj", process=False)
        # Match against original source surfaces, not rendering or geom IDs.
        distances = []
        for mesh in (fruit, stem):
            distances.append(
                np.concatenate(
                    [
                        trimesh.proximity.closest_point(mesh, batch)[1]
                        for batch in np.array_split(points, max(1, len(points) // 2048))
                    ]
                )
            )
        off_stem = (distances[0] <= distances[1] + 0.0002) | (
            distances[1] > 0.0022 + 2 * np.abs(hold_contacts[:, 5])
        )
        indices = np.rint(hold_contacts[:, 0] / dt).astype(int)
        norms = np.linalg.norm(hold_contacts[:, 7:10], axis=1)
        body_names = np.array([body_lookup[int(i)] for i in hold_contacts[:, 1]])
        for key, mask in (
            ("thumb", body_names == "r_thumb_pad"),
            ("index", body_names == "r_index_finger_pad"),
            ("other_hand", ~np.isin(body_names, ["r_thumb_pad", "r_index_finger_pad"])),
            ("off_stem", off_stem),
        ):
            np.add.at(sums[key], indices[mask], norms[mask])
        np.add.at(reconciled, indices, hold_contacts[:, 7:10])
    checks["contact_ledger_matches_hand_force"] = bool(
        np.allclose(reconciled[hold], log["hand"][hold], atol=1e-8)
    )
    if hold.any():
        checks["two_sdf_pads_throughout_hold"] = bool(
            np.min(sums["thumb"][hold]) > 0.1 and np.min(sums["index"][hold]) > 0.1
        )
        checks["no_fruit_support_during_hold"] = bool(
            np.max(sums["off_stem"][hold]) < 0.05
        )
        checks["only_two_pads_support"] = bool(np.max(sums["other_hand"][hold]) < 0.05)
        stats["maximum_off_stem_contact_n"] = float(np.max(sums["off_stem"][hold]))
    residual = (
        log["total"]
        - [0, 0, weight]
        - expected_mass * (log["velocity"] - log["velocity_before"]) / dt
    )
    stats["maximum_momentum_residual_weight_ratio"] = float(
        np.linalg.norm(residual, axis=1).max() / weight
    )
    checks["momentum_balance"] = stats["maximum_momentum_residual_weight_ratio"] < 0.05
    checks = {k: bool(v) for k, v in checks.items()}
    return {
        "passed": all(checks.values()),
        "backend": engine["backend"],
        "scope": "14 s stem grasp; 11-14 s hold",
        "checks": checks,
        "metrics": stats,
        "limits": "Known-pose scripted control. Rigid stem; no fracture or hardware validation. SDF discretization and contact-point classification are approximate.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--expected-mass-kg", type=float, default=0.2)
    args = parser.parse_args()
    result = verify_grasp(args.run, expected_mass=args.expected_mass_kg)
    (args.run / "summary.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
