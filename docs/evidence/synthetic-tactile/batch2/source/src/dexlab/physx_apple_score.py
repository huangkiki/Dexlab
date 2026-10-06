"""Offline PhysX grasp diagnostics, with explicit native-geometry limitations.

Native contact separation is not independent reference-surface penetration.
Full single-scene acceptance additionally requires the separate surface audit
and complete worker diagnostics. It is not cross-engine material calibration.
"""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from dexlab.physx_baseline import digest, write_json

PADS = ("robot/r_thumb_pad", "robot/r_index_finger_pad")
LIMITS = {
    "clearance_m": 0.07,
    "native_hand_penetration_m": 0.001,
    "drift_m": 0.002,
    "rotation_deg": 5.0,
    "support_relative": 0.05,
    "other_force_n": 0.05,
    "pad_load_n": 0.1,
    "momentum_residual_weight_ratio": 0.05,
}

BENCHMARK_INTERFACE_WARNING = (
    "[Warning] [carb] Acquiring non optional plugin interface which is not listed as dependency: "
    "[omni::physx::IPhysxBenchmarks v1.0] (plugin: <default plugin>), by client: "
    "omni.physics.physx.plugin. Add it to CARB_PLUGIN_IMPL_DEPS() macro of a client."
)


def physics_diagnostics(text):
    """Keep the pinned SDK's plugin-dependency warning separate from physics errors."""
    startup, physics = [], []
    for line in text.splitlines():
        if line.endswith(BENCHMARK_INTERFACE_WARNING):
            startup.append(line)
        elif any(
            level in line for level in ("[Warning]", "[Error]", "[Fatal]")
        ) and any(
            word in line.lower()
            for word in ("physx", "physics", "articulation", "solver")
        ):
            physics.append(line)
    return startup, physics


def classify_stem(points, fruit, stem):
    """Classify native anchors against source surfaces, never segmentation IDs.

    The historical 0.2 mm ambiguity band and 2.2 mm stem-distance tolerance
    are retained. Friction anchors have no penetration field; no depth-based
    tolerance expansion is applied. Classification is approximate.
    """
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
    return (distances[0] > distances[1] + 0.0002) & (distances[1] <= 0.0022)


def score(receipt, states, contacts, native, fruit, stem, table_mesh):
    """Use actual body states and all force records; missing data cannot pass."""
    checks = {}
    result = {
        "native_hold_passed": False,
        "strict_stem_observations_passed": False,
        "qualified": False,
        "checks": checks,
        "metrics": {},
        "limits": LIMITS,
        "scope": __doc__.strip(),
        "unavailable": [
            "independent whole-surface penetration",
            "full solver-warning coverage",
        ],
    }
    names = receipt.get("body_names", [])
    dt = receipt.get("dt", 0)
    if not isinstance(dt, (float, int)) or not np.isfinite(dt) or dt <= 0:
        checks["valid_timestep"] = False
        return result
    count = round(14 / dt)
    if count < 2 or not np.isclose(count * dt, 14, rtol=0, atol=1e-10):
        checks["valid_timestep"] = False
        return result
    shapes = {
        "time": (count,),
        "q": (count, 54),
        "dq": (count, 54),
        "position": (count, len(names), 3),
        "quaternion": (count, len(names), 4),
        "velocity": (count, len(names), 3),
        "angular_velocity": (count, len(names), 3),
    }
    checks["complete_finite_states"] = all(
        key in states and states[key].shape == shape and np.isfinite(states[key]).all()
        for key, shape in shapes.items()
    )
    checks["required_bodies"] = len(names) == len(set(names)) and all(
        name in names
        for name in (
            "apple/apple",
            "robot/r_wrist",
            "robot/robot_world",
            "table/table",
            *PADS,
        )
    )
    if not all(checks.values()):
        return result
    checks["post_step_time_grid"] = bool(
        np.allclose(states["time"], np.arange(1, count + 1) * dt, rtol=0, atol=1e-10)
    )
    checks["unit_quaternions"] = bool(
        np.allclose(np.linalg.norm(states["quaternion"], axis=2), 1, rtol=0, atol=1e-5)
    )
    if not all(checks.values()):
        return result
    apple, wrist, base, table = [
        names.index(name)
        for name in ("apple/apple", "robot/r_wrist", "robot/robot_world", "table/table")
    ]
    rotation = Rotation.from_quat(states["quaternion"][:, apple][:, [1, 2, 3, 0]])
    wrist_rotation = Rotation.from_quat(states["quaternion"][:, wrist][:, [1, 2, 3, 0]])
    groups = {name: np.zeros((count, 3)) for name in ("hand", "table", "other")}
    loads = {name: np.zeros(count) for name in (*PADS, "other_hand", "off_stem")}
    id_names = receipt.get("contact_details", {}).get("body_names", {})
    hold = (states["time"] >= 11) & (states["time"] < 14)
    checks["full_hold_window"] = int(hold.sum()) == round(3 / dt)
    if not checks["full_hold_window"] or not hold.any():
        return result
    checks["complete_contact_polls"] = receipt.get("contact_polls") == count
    checks["valid_contacts"] = True
    max_penetration = 0.0
    for kind in ("normal", "friction"):
        try:
            steps, ids, forces, points = [
                contacts[kind + "_" + field]
                for field in ("step", "body_ids", "force", "point")
            ]
            valid = (
                steps.ndim == ids.ndim == 1
                and ids.shape == steps.shape
                and steps.dtype.kind in "iu"
                and ids.dtype.kind in "iu"
                and forces.shape == points.shape == (len(steps), 3)
                and np.isfinite(forces).all()
                and np.isfinite(points).all()
                and np.all((steps >= 0) & (steps < count))
                and all(str(int(i)) in id_names for i in np.unique(ids))
            )
            if not valid:
                raise ValueError("Malformed contact records")
            owners = np.array([id_names[str(int(i))] for i in ids])
            hand = np.array([name.startswith("robot/") for name in owners])
            for group, mask in (
                ("hand", hand),
                ("table", owners == "table/table"),
                ("other", ~hand & (owners != "table/table")),
            ):
                np.add.at(groups[group], steps[mask], forces[mask])
            if kind == "normal":
                separation = contacts["separation"]
                if separation.shape != steps.shape or not np.isfinite(separation).all():
                    raise ValueError("Invalid native contact separation")
                max_penetration = (
                    max(0.0, float(-separation[hand].min())) if hand.any() else 0.0
                )
            active = hold[steps] & hand
            if active.any():
                local = (
                    rotation[steps[active]]
                    .inv()
                    .apply(points[active] - states["position"][steps[active], apple])
                )
                on_stem = classify_stem(local, fruit, stem)
                magnitudes = np.linalg.norm(forces[active], axis=1)
                for name, mask in (
                    (PADS[0], owners[active] == PADS[0]),
                    (PADS[1], owners[active] == PADS[1]),
                    ("other_hand", ~np.isin(owners[active], PADS)),
                    ("off_stem", ~on_stem),
                ):
                    np.add.at(loads[name], steps[active][mask], magnitudes[mask])
        except (KeyError, TypeError, ValueError, IndexError):
            checks["valid_contacts"] = False
            return result
    mass = float(np.asarray(native["apple"]["body_mass"])[0, 0])
    checks["expected_mass"] = bool(np.isclose(mass, 0.2, rtol=0, atol=1e-7))
    com = np.asarray(native["apple"]["body_com"])[0, 0]
    velocity = states["velocity"][:, apple] + np.cross(
        states["angular_velocity"][:, apple],
        rotation.apply(np.broadcast_to(com, (count, 3))),
    )
    initial = np.asarray(receipt.get("initial_apple_com_velocity", []))
    checks["initial_velocity_recorded"] = initial.shape == (3,) and bool(
        np.isfinite(initial).all()
    )
    residual = float("inf")
    if checks["initial_velocity_recorded"]:
        previous = np.vstack((initial, velocity[:-1]))
        total = sum(groups.values())
        residual = float(
            np.linalg.norm(
                mass * (velocity - previous) / dt - total - [0, 0, -mass * 9.81], axis=1
            ).max()
            / (mass * 9.81)
        )
    relative = wrist_rotation.inv().apply(
        states["position"][:, apple] - states["position"][:, wrist]
    )
    relative_rotation = wrist_rotation.inv() * rotation
    drift = float(np.linalg.norm(relative[hold] - relative[hold][0], axis=1).max())
    angle = float(
        np.rad2deg(
            (relative_rotation[hold][0].inv() * relative_rotation[hold]).magnitude()
        ).max()
    )
    table_rotation = Rotation.from_quat(states["quaternion"][:, table][:, [1, 2, 3, 0]])
    table_tops = np.array(
        [
            np.max(table_mesh.vertices @ matrix[2]) + position[2]
            for matrix, position in zip(
                table_rotation[hold].as_matrix(), states["position"][hold, table]
            )
        ]
    )
    clearance = (
        np.array(
            [
                np.min(fruit.vertices @ matrix[2]) + position[2]
                for matrix, position in zip(
                    rotation[hold].as_matrix(), states["position"][hold, apple]
                )
            ]
        )
        - table_tops
    )
    support = float(groups["hand"][hold, 2].mean() / (mass * 9.81))
    checks.update(
        lifted=float(clearance.min()) > LIMITS["clearance_m"],
        retained=drift < LIMITS["drift_m"] and angle < LIMITS["rotation_deg"],
        hand_supports_weight=abs(support - 1) < LIMITS["support_relative"],
        no_table_support=bool(
            np.linalg.norm(groups["table"][hold], axis=1).max()
            < LIMITS["other_force_n"]
        ),
        no_other_support=bool(
            np.linalg.norm(groups["other"][hold], axis=1).max()
            < LIMITS["other_force_n"]
        ),
        bounded_native_hand_penetration=max_penetration
        < LIMITS["native_hand_penetration_m"],
        momentum_balance=residual < LIMITS["momentum_residual_weight_ratio"],
        fixed_base=bool(
            np.max(np.abs(states["position"][:, base] - states["position"][0, base]))
            < 1e-7
        ),
        fixed_table=bool(
            np.max(np.abs(states["position"][:, table] - states["position"][0, table]))
            < 1e-7
        ),
        fixed_base_rotation=bool(
            np.max(
                np.abs(
                    np.abs(
                        states["quaternion"][:, base] @ states["quaternion"][0, base]
                    )
                    - 1
                )
            )
            < 1e-6
        ),
        fixed_table_rotation=bool(
            np.max((table_rotation[0].inv() * table_rotation).magnitude()) < 1e-6
        ),
    )
    result["native_hold_passed"] = bool(all(checks.values()))
    checks.update(
        two_pads_throughout_hold=bool(
            all(loads[name][hold].min() > LIMITS["pad_load_n"] for name in PADS)
        ),
        only_two_pads_support=bool(
            loads["other_hand"][hold].max() < LIMITS["other_force_n"]
        ),
        stem_support_only=bool(loads["off_stem"][hold].max() < LIMITS["other_force_n"]),
    )
    result["strict_stem_observations_passed"] = bool(all(checks.values()))
    result["metrics"] = {
        "minimum_hold_clearance_m": float(clearance.min()),
        "hold_drift_m": drift,
        "hold_rotation_deg": angle,
        "mean_hand_support_weight_ratio": support,
        "maximum_native_hand_penetration_m": max_penetration,
        "maximum_momentum_residual_weight_ratio": residual
        if np.isfinite(residual)
        else None,
        "maximum_other_hand_load_n": float(loads["other_hand"][hold].max()),
        "maximum_off_stem_load_n": float(loads["off_stem"][hold].max()),
    }
    return result


def reference_checks(directory: Path, report: dict) -> dict:
    """Bind the separate geometry audit to the actual states and all source geoms."""
    tree = ET.parse(directory / "robot-model/robot.xml")
    assets = {item.get("name"): item for item in tree.findall("./asset/mesh")}
    expected = {}
    for body in tree.findall(".//body"):
        for geom in body.findall("geom"):
            path = Path(assets[geom.get("mesh")].get("file"))
            if not path.is_absolute():
                path = directory / "robot-model" / path
            expected[("robot/" + body.get("name"), geom.get("name"))] = digest(path)
    rows = report.get("results", [])
    actual = {
        (row.get("body"), row.get("geom")): row.get("source_sha256") for row in rows
    }
    checks = {
        "reference_states_match": report.get("states_sha256")
        == digest(directory / "states.npz"),
        "reference_verifier_matches": report.get("source_sha256")
        == digest(Path(__file__).with_name("physx_geometry.py")),
        "reference_all_source_geometries": actual == expected
        and len(rows) == len(expected),
        "reference_analytic_query": report.get("analytic_query_check", {}).get(
            "maximum_box_error_m", float("inf")
        )
        < 1e-6,
    }
    bounds = []
    valid = bool(rows)
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        count = len(saved["time"])
    for row in rows:
        valid &= row.get("total_steps") == count
        if row.get("bounding_spheres_disjoint") is True:
            valid &= row.get("near_steps") == 0
            continue
        values = [
            row.get(key, float("nan"))
            for key in (
                "sampled_max_penetration_m",
                "spatial_bound_m",
                "temporal_bound_m",
            )
        ]
        bound = sum(values)
        indices = row.get("sampled_step_indices", [])
        valid &= (
            bool(indices)
            and indices == sorted(set(indices))
            and all(type(i) is int and 0 <= i < count for i in indices)
            and row.get("sampled_steps") == len(indices)
            and np.isfinite(values).all()
            and min(values) >= 0
            and np.isclose(
                bound,
                row.get("covered_penetration_bound_m", float("nan")),
                rtol=0,
                atol=1e-12,
            )
        )
        bounds.append(bound)
    checks["reference_coverage_accounting"] = bool(valid and bounds)
    checks["bounded_reference_penetration"] = bool(
        bounds and max(bounds) < LIMITS["native_hand_penetration_m"]
    )
    return checks


def verify(directory: Path, geometry: Path | None = None):
    receipt = json.loads((directory / "run.json").read_text())
    artifacts = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        "contacts.npz",
        "native-records.json",
        "layout.json",
        "import-report.json",
        "reference-fruit.obj",
        "reference-stem.obj",
        "table.obj",
        "source.py",
        "robot-model/kinematics.xml",
    }
    intact = required <= artifacts.keys() and all(
        not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and (directory / name).is_file()
        and digest(directory / name) == expected
        for name, expected in artifacts.items()
    )
    if not intact:
        raise ValueError("Incomplete or modified grasp evidence")
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        states = dict(saved)
    with np.load(directory / "contacts.npz", allow_pickle=False) as saved:
        contacts = dict(saved)
    native = json.loads((directory / "native-records.json").read_text())
    fruit, stem = [
        trimesh.load_mesh(directory / f"reference-{name}.obj", process=False)
        for name in ("fruit", "stem")
    ]
    table_mesh = trimesh.load_mesh(directory / "table.obj", process=False)
    result = score(receipt, states, contacts, native, fruit, stem, table_mesh)
    layout = json.loads((directory / "layout.json").read_text())
    entities = {entity["name"]: entity for entity in layout["entities"]}
    apple = entities.get("apple", {})
    sdf = {
        name: value
        for name, value in zip(
            native["robot"]["geom_names"][0], native["robot"]["geom_sdf"][0]
        )
    }
    native_sdf = native["apple"]["geom_sdf"][0][0] is not None and all(
        sdf.get("collision_" + name.removeprefix("robot/")) is not None for name in PADS
    )
    report = json.loads((directory / "import-report.json").read_text())
    fields = {item["field"]: item for item in report.get("fields", [])}
    parameters = {
        "contact_offset": 0.0001,
        "rest_offset": 0.0,
        "solver_position_iteration_count": 8,
        "solver_velocity_iteration_count": 2,
        "external_forces_every_iteration": True,
        "min_torsional_patch_radius": receipt.get("min_torsional_patch_radius_m"),
    }
    contact_settings = all(
        name in fields
        and expected is not None
        and isinstance(fields[name].get("effective"), (int, float, bool))
        and np.isclose(fields[name]["effective"], expected, rtol=1e-6, atol=1e-9)
        and any(
            item.get("kind") == "engine_readback"
            for item in fields[name].get("provenance", [])
        )
        for name, expected in parameters.items()
    )
    result["checks"].update(
        archive_hashes_match=True,
        native_completed=receipt.get("status") == "completed"
        and "cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True,
        robot_self_collision=receipt.get("robot_self_collision") is True,
        native_sdf_apple_and_pads=native_sdf,
        native_contact_settings=bool(contact_settings),
        free_unactuated_apple=apple.get("root_mode") == "floating"
        and not apple.get("actuator_names")
        and len(apple.get("root_qvel_indices", [])) == 6,
    )
    receipt_ok = all(
        result["checks"][key]
        for key in (
            "archive_hashes_match",
            "native_completed",
            "source_unchanged",
            "robot_self_collision",
            "native_sdf_apple_and_pads",
            "native_contact_settings",
            "free_unactuated_apple",
        )
    )
    result["native_hold_passed"] &= receipt_ok
    result["strict_stem_observations_passed"] &= receipt_ok
    stderr_complete = (
        receipt.get("complete_worker_stderr") is True
        and receipt.get("worker_exit_code") == 0
        and "worker-stderr.log" in artifacts
    )
    diagnostics = []
    startup = []
    if stderr_complete:
        startup, diagnostics = physics_diagnostics(
            (directory / "worker-stderr.log").read_text(errors="replace")
        )
    result["checks"].update(
        complete_worker_diagnostics=stderr_complete,
        no_physics_diagnostics_in_stderr=stderr_complete and not diagnostics,
    )
    result["worker_physics_diagnostics"] = diagnostics
    result["worker_startup_diagnostics"] = startup
    result["unavailable"] = [] if stderr_complete else ["complete worker diagnostics"]
    if geometry is None:
        result["unavailable"].append("independent whole-surface penetration")
    else:
        reference = json.loads(geometry.read_text())
        result["checks"].update(reference_checks(directory, reference))
        result["reference_report_sha256"] = digest(geometry)
        result["reference_limits"] = reference.get("bounds_exclude", [])
        result["qualified"] = bool(all(result["checks"].values()))
    result["verifier_sha256"] = digest(Path(__file__))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--geometry",
        type=Path,
        help="Independent physx_geometry.py report for this record",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; preserve prior diagnostics")
    result = verify(args.run, args.geometry)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["qualified"] else 1)
