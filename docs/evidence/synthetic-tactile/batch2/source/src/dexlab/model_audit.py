"""Read-only source/runtime audits; findings never repair a simulation model."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

UNITS = {
    "length": "m",
    "mass": "kg",
    "time": "s",
    "angle": "rad",
    "inertia": "kg m^2",
    "force": "N",
    "torque": "N m",
    "joint_stiffness": "N m / rad",
    "joint_damping": "N m s / rad",
    "basis": "Declared SI interpretation of the assets and task; not hardware calibration.",
}
CONTACT_FIELDS = (
    "coulomb_friction_coefficient",
    "friction_falloff_vel",
    "penalty_coefficient",
    "penalty_threshold_default",
    "penalty_smoothing_half_distance",
    "normal_viscous_damping_coefficient",
    "viscous_friction_coefficient",
)


def inertia_matrix(value):
    """SuperDex packed order is xx, xy, xz, yy, yz, zz."""
    if value is None:
        return None
    xx, xy, xz, yy, yz, zz = np.asarray(value)
    return np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])


def check_inertial(mass, com, inertia, *, static=False, massless_frame=False):
    """Return defects without normalizing, symmetrizing, or clamping input."""
    defects = []
    try:
        mass = float(mass)
        com, inertia = np.asarray(com, float), np.asarray(inertia, float)
    except (TypeError, ValueError):
        return ["non_numeric_inertial"]
    if (
        not np.isfinite(mass)
        or not np.isfinite(com).all()
        or not np.isfinite(inertia).all()
    ):
        return ["non_finite_inertial"]
    if com.shape != (3,) or inertia.shape != (3, 3):
        return ["invalid_inertial_shape"]
    if mass < 0 or (mass == 0 and not static and not massless_frame):
        defects.append("non_positive_dynamic_mass")
    tolerance = max(1e-15, np.linalg.norm(inertia) * 1e-9)
    if not np.allclose(inertia, inertia.T, rtol=0, atol=tolerance):
        return defects + ["asymmetric_inertia"]
    moments = np.linalg.eigvalsh(inertia)
    if moments[0] < -tolerance:
        defects.append("negative_inertia_eigenvalue")
    if mass > 0 and moments[0] <= 0:
        defects.append("non_positive_inertia")
    if moments[2] > moments[0] + moments[1] + tolerance:
        defects.append("inertia_triangle_inequality")
    if mass == 0 and not static and massless_frame and np.any(inertia != 0):
        defects.append("massless_frame_has_inertia")
    return defects


def check_joint(axis, limits):
    try:
        axis, limits = np.asarray(axis, float), np.asarray(limits, float)
    except (TypeError, ValueError):
        return ["non_numeric_joint"]
    if axis.shape != (3,) or limits.shape != (2,):
        return ["invalid_joint_shape"]
    if not np.isfinite(axis).all() or not np.isfinite(limits).all():
        return ["non_finite_joint"]
    defects = []
    if not np.isclose(np.linalg.norm(axis), 1, rtol=0, atol=1e-6):
        defects.append("non_unit_joint_axis")
    if limits[0] > limits[1]:
        defects.append("reversed_joint_limits")
    return defects


def json_value(value):
    """Keep invalid numeric evidence as text in standards-compliant JSON."""
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_value(v) for v in value]
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


def findings(report):
    rows = []

    def check_numbers(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key not in ("findings", "errors", "warnings"):
                    check_numbers(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple, np.ndarray)):
            for i, item in enumerate(value):
                check_numbers(item, f"{path}[{i}]")
        elif (isinstance(value, (float, np.floating)) and not np.isfinite(value)) or (
            isinstance(value, str) and value in ("nan", "inf", "-inf")
        ):
            rows.append(
                {"severity": "error", "object": path, "code": "non_finite_parameter"}
            )

    check_numbers(report, "report")
    for body in report["bodies"]:
        for stage in ("source", "effective"):
            props = body[stage]
            if any(props.get(k) is None for k in ("mass", "com", "inertia")):
                rows.append(
                    {
                        "severity": "info",
                        "object": body["name"],
                        "stage": stage,
                        "code": "unspecified_source_properties",
                    }
                )
                if stage == "effective" and not body["static"]:
                    rows.append(
                        {
                            "severity": "error",
                            "object": body["name"],
                            "stage": stage,
                            "code": "missing_effective_inertial",
                        }
                    )
                mass = props.get("mass")
                if mass is not None and (
                    float(mass) < 0
                    or (
                        float(mass) == 0
                        and not body["static"]
                        and not body["massless_reason"]
                    )
                ):
                    rows.append(
                        {
                            "severity": "error",
                            "object": body["name"],
                            "stage": stage,
                            "code": "non_positive_dynamic_mass",
                        }
                    )
                com, inertia = props.get("com"), props.get("inertia")
                if com is not None and np.asarray(com).shape != (3,):
                    rows.append(
                        {
                            "severity": "error",
                            "object": body["name"],
                            "stage": stage,
                            "code": "invalid_inertial_shape",
                        }
                    )
                if inertia is not None:
                    # Validate provided inertia even when other source fields
                    # are omitted. Temporary check inputs never enter the report.
                    for defect in check_inertial(
                        0 if mass is None else mass, [0, 0, 0], inertia, static=True
                    ):
                        rows.append(
                            {
                                "severity": "error",
                                "object": body["name"],
                                "stage": stage,
                                "code": defect,
                            }
                        )
                continue
            for defect in check_inertial(
                props["mass"],
                props["com"],
                props["inertia"],
                static=body["static"],
                massless_frame=bool(body["massless_reason"]),
            ):
                rows.append(
                    {
                        "severity": "error",
                        "object": body["name"],
                        "stage": stage,
                        "code": defect,
                    }
                )
        if body["massless_reason"]:
            rows.append(
                {
                    "severity": "info",
                    "object": body["name"],
                    "code": "intentional_massless_frame",
                }
            )
    for joint in report["joints"]:
        if joint["type"] != "REVOLUTE":
            continue
        for defect in check_joint(joint["axis"], joint["limits"]):
            rows.append({"severity": "error", "object": joint["name"], "code": defect})
    for drive in report["drives"]:
        values = np.asarray([drive["stiffness"], drive["damping"]], float)
        if not np.isfinite(values).all() or np.any(values < 0):
            rows.append(
                {
                    "severity": "error",
                    "object": drive["joint"],
                    "code": "invalid_drive_gains",
                }
            )
    for overlap in report["initial_overlaps"]["pairs"]:
        if overlap["minimum_distance_m"] < 0:
            rows.append(
                {
                    "severity": "warning",
                    "object": overlap["pair"],
                    "code": "initial_overlap",
                    "minimum_distance_m": overlap["minimum_distance_m"],
                    "filter": overlap.get("filter", "engine_contact"),
                }
            )
    return rows


def write_report(report, path):
    report = json_value(report)
    report["findings"] = findings(report)
    report["errors"] = sum(row["severity"] == "error" for row in report["findings"])
    report["warnings"] = sum(row["severity"] == "warning" for row in report["findings"])
    Path(path).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        f"Model audit {Path(path).name}: {report['errors']} errors, {report['warnings']} warnings",
        flush=True,
    )
    return report


def _properties(actor):
    # The native API rejects get_mass() for static actors. Zero below denotes
    # excluded dynamic mass, not a measurement of their physical mass.
    if actor.is_static() and not actor.is_nested_link_actor():
        return {"mass": 0.0, "com": None, "inertia": None}
    return {
        "mass": 0.0 if actor.is_static() else actor.get_mass(),
        "com": np.asarray(actor.get_rigid_center_of_mass_local()),
        "inertia": inertia_matrix(actor.get_rigid_moment_of_inertia_local()),
    }


def _contact(actor):
    if actor.get_collider_type().name == "NONE":
        return None
    params = actor.get_contact_params()
    return {name: getattr(params, name) for name in CONTACT_FIELDS}


def _transform(transform):
    return {
        "translation_m": np.asarray(transform.translation),
        "rotation_xyzw": np.asarray(transform.rotation),
    }


def sample_initial_overlaps(actors, scene, inferred_disabled, *, max_vertices=256):
    """Bidirectional vertex probes of AABB-overlapping surfaces, without stepping."""
    surfaces = []
    for name, actor in actors:
        mesh = actor.get_surface_mesh()
        if mesh.is_empty():
            continue
        transform = actor.get_root_transform()
        vertices = Rotation.from_quat(transform.rotation).apply(
            np.asarray(mesh.coordinates).reshape(-1, 3)
        ) + np.asarray(transform.translation)
        chosen = np.linspace(
            0, len(vertices) - 1, min(len(vertices), max_vertices), dtype=int
        )
        surfaces.append(
            (name, actor, vertices.min(0), vertices.max(0), vertices[chosen])
        )
    pairs, candidates = [], 0
    for i, (name, actor, lower, upper, points) in enumerate(surfaces):
        for other_name, other, other_lower, other_upper, other_points in surfaces[
            i + 1 :
        ]:
            if np.any(upper < other_lower) or np.any(other_upper < lower):
                continue
            candidates += 1
            minimum = float("inf")
            for target, query in ((other, points), (actor, other_points)):
                distances = np.empty(len(query), dtype=np.float64)
                target.get_points_distance_to_surface(
                    np.ascontiguousarray(query), distances
                )
                if not np.isfinite(distances).all():
                    raise ValueError(
                        f"Non-finite surface distances: {name}, {other_name}"
                    )
                minimum = min(minimum, float(distances.min()))
            if minimum < 0:
                layers = [
                    scene.is_layer_contact_enabled(
                        actor.get_contact_layer(), other.get_contact_layer()
                    ),
                    scene.is_layer_contact_enabled(
                        other.get_contact_layer(), actor.get_contact_layer()
                    ),
                ]
                pairs.append(
                    {
                        "pair": [name, other_name],
                        "minimum_distance_m": minimum,
                        "layer_directions_enabled": layers,
                        "filter": "inferred_disabled"
                        if tuple(sorted((name, other_name))) in inferred_disabled
                        else "actor_filter_not_observable",
                    }
                )
    return {
        "method": "bidirectional native signed surface-distance queries at initial world pose",
        "phase": "after apple settling and pre-grasp robot placement; before grasp stepping",
        "maximum_vertices_per_surface": max_vertices,
        "aabb_candidates": candidates,
        "pairs": pairs,
        "limitation": "Finite vertex probes may miss small or edge-only intersections. Layer directions are read back; actor filters are inferred from prefab rules, not queried. Negative samples are geometry warnings, including filtered adjacent links. No global collision-free certificate.",
    }


def record_superdex(prefab, links, scene, apple, table, actor, directory):
    """Snapshot loaded source and native runtime without setters or scene steps."""
    from mujoco_model import excluded_pairs
    from physics_utils import physics, robotics
    from robot import ASSET

    raw = robotics.load_bot_prefab_from_file(
        str(ASSET / "openarm_v20_wuji_trimmed.superdex_bot")
    )
    bodies, joints, drives = [], [], []
    controller = physics.PoseControllerParams(len(links))
    actor.get_articulated_pose_controller_params(controller)
    for i, (source, joint, link) in enumerate(
        zip(raw.links, raw.joints, links, strict=True)
    ):
        marker = (
            joint.type.name == "HARD"
            and not source.shape_file
            and source.mass in (None, 0)
            and source.moment_of_inertia is None
        )
        bodies.append(
            {
                "name": source.name,
                "static": link.is_static(),
                "massless_reason": "fixed coordinate frame without source geometry or inertial properties"
                if marker
                else None,
                "source": {
                    "mass": source.mass,
                    "com": None
                    if source.center_of_mass is None
                    else np.asarray(source.center_of_mass),
                    "inertia": inertia_matrix(source.moment_of_inertia),
                    "density": source.density,
                    "collider": source.collider_type.name,
                    "shape_scale": np.asarray(source.shape_scale),
                    "shape_file": str(Path(source.shape_file).relative_to(ASSET))
                    if source.shape_file
                    else None,
                    "contact": {
                        name: getattr(source.contact, name) for name in CONTACT_FIELDS
                    },
                },
                "effective": _properties(link),
                "collision": {
                    "type": link.get_collider_type().name,
                    "layer": link.get_contact_layer(),
                    "contact": _contact(link),
                },
            }
        )
        axis = np.asarray(joint.axis)
        joints.append(
            {
                "name": joint.name,
                "type": joint.type.name,
                "axis": axis,
                "limits": None
                if joint.min_limit is None
                else [np.dot(joint.min_limit, axis), np.dot(joint.max_limit, axis)],
                "parent_link": source.parent_link,
                "child_link": source.name,
                "parent_link_from_joint": _transform(joint.parent_link_from_joint),
                "parent_joint_from_link": _transform(source.parent_joint_from_link),
                "effort_limit": joint.effort_limit,
                "limit_stiffness": joint.limit_stiffness,
                "limit_damping": joint.limit_damping,
                "viscous_friction": joint.friction.viscous,
                "coulomb_friction": joint.friction.coulomb,
            }
        )
        if joint.type.name == "REVOLUTE":
            tracking = controller.joint_tracking[i]
            drives.append(
                {
                    "joint": joint.name,
                    "stiffness": tracking.stiffness,
                    "damping": tracking.damping,
                    "saturation": tracking.saturation,
                    "source_effort_limit": joint.effort_limit,
                    "origin": "task pose controller; -1 saturation means unbounded; source effort limit is not a verified motor limit",
                }
            )
    for name, link in (("apple", apple), ("table", table)):
        bodies.append(
            {
                "name": name,
                "static": link.is_static(),
                "massless_reason": None,
                "source": {
                    "mass": 0.2 if name == "apple" else None,
                    "com": None,
                    "inertia": None,
                    "origin": "task mass 0.2 kg; native geometry-derived COM/inertia"
                    if name == "apple"
                    else "static task box; density 250 kg/m^3",
                },
                "effective": _properties(link),
                "collision": {
                    "type": link.get_collider_type().name,
                    "layer": link.get_contact_layer(),
                    "contact": _contact(link),
                },
            }
        )
    disabled = {
        tuple(sorted((prefab.links[i].name, prefab.links[j].name)))
        for i, j in excluded_pairs(prefab, links, scene)
    }
    actors = [
        (info.name, link) for info, link in zip(prefab.links, links, strict=True)
    ] + [("apple", apple), ("table", table)]
    layers = sorted({link.get_contact_layer() for _, link in actors})
    report = {
        "schema_version": 1,
        "backend": "superdex",
        "units": UNITS,
        "bodies": bodies,
        "joints": joints,
        "drives": drives,
        "sources": {
            str(p.relative_to(ASSET)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ASSET.rglob("*.superdex_bot"))
        },
        "source_record": json.loads((ASSET / "source.json").read_text()),
        "collision_filters": {
            "layer_directions": [
                {
                    "first": a,
                    "second": b,
                    "enabled": scene.is_layer_contact_enabled(a, b),
                }
                for a in layers
                for b in layers
            ],
            "explicit_overrides": [
                {"first": o.link_a, "second": o.link_b, "enabled": o.enable}
                for o in raw.contact_overrides
            ],
            "inferred_disabled_robot_pairs": sorted(disabled),
            "limitation": "Actor filters have no public readback; inferred using the existing transfer's adjacency and override rules. No native bitmask representation.",
        },
        "initial_overlaps": sample_initial_overlaps(actors, scene, disabled),
        "assumptions": [
            "SI units are inherited, not measured.",
            "Source properties are from the unmodified loaded prefab; omitted values are null, not zero.",
            "Static mass is reported as zero dynamic mass because the native mass getter rejects static actors; source mass is preserved separately.",
            "Standalone static geometry does not expose rigid COM/inertia; those fields remain null.",
            "Missing properties on fixed geometry-free frames are treated as intentional massless coordinate frames.",
            "Apple COM/inertia are geometry estimates. No finger tissue, stem bending or hardware calibration.",
        ],
    }
    return write_report(report, Path(directory) / "model-audit.superdex.json")


def record_mujoco(model, data, directory):
    """Read compiled parameters and detect initial contacts in isolated MjData."""
    import mujoco

    directory = Path(directory)
    native = json.loads((directory / "model-audit.superdex.json").read_text())
    bodies, joints, drives = [], [], []
    for original in native["bodies"]:
        name = original["name"]
        body_id = model.body("robot_world" if name == "world" else name).id
        rotation = Rotation.from_quat(
            model.body_iquat[body_id][[1, 2, 3, 0]]
        ).as_matrix()
        bodies.append(
            {
                "name": name,
                "static": bool(model.body_weldid[body_id] == 0),
                "massless_reason": original["massless_reason"],
                "source": original["effective"],
                "prefab_source": original["source"],
                "effective": {
                    "mass": model.body_mass[body_id],
                    "com": model.body_ipos[body_id],
                    "inertia": rotation
                    @ np.diag(model.body_inertia[body_id])
                    @ rotation.T,
                },
            }
        )
    for i in range(model.njnt):
        joint = model.joint(i)
        if model.jnt_type[i] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        dof = model.jnt_dofadr[i]
        joints.append(
            {
                "name": joint.name,
                "type": "REVOLUTE",
                "axis": model.jnt_axis[i],
                "limits": model.jnt_range[i],
                "limited": bool(model.jnt_limited[i]),
                "damping": model.dof_damping[dof],
                "armature": model.dof_armature[dof],
                "frictionloss": model.dof_frictionloss[dof],
            }
        )
    for i in range(model.nu):
        drives.append(
            {
                "joint": model.joint(int(model.actuator_trnid[i, 0])).name,
                "stiffness": model.actuator_gainprm[i, 0],
                "damping": -model.actuator_biasprm[i, 2],
                "gainprm": model.actuator_gainprm[i],
                "biasprm": model.actuator_biasprm[i],
                "forcelimited": bool(model.actuator_forcelimited[i]),
                "forcerange": model.actuator_forcerange[i],
                "ctrllimited": bool(model.actuator_ctrllimited[i]),
                "ctrlrange": model.actuator_ctrlrange[i],
                "origin": "task gain override; effective damping includes dt*kp",
            }
        )
    probe = mujoco.MjData(model)
    probe.qpos[:] = data.qpos
    mujoco.mj_forward(model, probe)
    pairs = {}
    for contact in probe.contact[: probe.ncon]:
        if contact.dist < 0:
            pair = tuple(
                sorted(
                    (
                        model.geom(int(contact.geom1)).name,
                        model.geom(int(contact.geom2)).name,
                    )
                )
            )
            pairs[pair] = min(pairs.get(pair, 0), float(contact.dist))
    excluded = [
        [model.body(int(signature) >> 16).name, model.body(int(signature) & 65535).name]
        for signature in model.exclude_signature
    ]
    geometries = [
        {
            "name": model.geom(i).name,
            "body": model.body(int(model.geom_bodyid[i])).name,
            "type": mujoco.mjtGeom(int(model.geom_type[i])).name,
            "contype": int(model.geom_contype[i]),
            "conaffinity": int(model.geom_conaffinity[i]),
            "condim": int(model.geom_condim[i]),
            "friction": model.geom_friction[i],
            "solref": model.geom_solref[i],
            "solimp": model.geom_solimp[i],
            "margin": model.geom_margin[i],
        }
        for i in range(model.ngeom)
    ]
    report = {
        "schema_version": 1,
        "backend": "mujoco",
        "units": UNITS,
        "bodies": bodies,
        "joints": joints,
        "drives": drives,
        "sources": native["sources"],
        "collision_filters": {
            "geometries": geometries,
            "excluded_body_pairs": excluded,
            "parent_filter_enabled": not bool(
                model.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_FILTERPARENT
            ),
        },
        "initial_overlaps": {
            "method": "mj_forward on fresh MjData with copied initial qpos; effective collision filters apply",
            "phase": "after apple settling and pre-grasp placement, before dynamics steps",
            "pairs": [
                {"pair": list(pair), "minimum_distance_m": distance}
                for pair, distance in sorted(pairs.items())
            ],
            "limitation": "Engine-generated contacts, not exhaustive surface intersection. Filtered pairs are absent. Negative distances are reported, not repaired.",
        },
        "assumptions": [
            "Source here means the native SuperDex runtime; prefab_source retains loaded asset values.",
            "Inertia is reconstructed in the body frame from compiled principal axes/moments.",
            "Compiler placeholder masses/inertias are restored to zero by the existing adapter; this audit does not repair them.",
            "MuJoCo uses convex hulls for non-SDF mesh collisions, including extra wrist/ABAD exclusions.",
            "Drive and friction values are task overrides, not identified hardware parameters.",
        ],
        "timestep_s": float(model.opt.timestep),
    }
    return write_report(report, directory / "model-audit.mujoco.json")


def main():
    parser = argparse.ArgumentParser(
        description="Recheck a saved model audit; errors exit 1, warnings remain visible."
    )
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if report.get("schema_version") != 1:
        raise SystemExit("Unsupported model audit schema")
    rows = findings(report)
    print(json.dumps(rows, indent=2, allow_nan=False))
    raise SystemExit(1 if any(row["severity"] == "error" for row in rows) else 0)


if __name__ == "__main__":
    main()
