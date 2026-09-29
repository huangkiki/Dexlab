"""Preserve the compiled OpenArm/Wuji dynamics while folding massless fixed frames."""

import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from dexlab.mujoco_artifacts import load_model
from dexlab.physx_baseline import digest, write_json

DT = 0.001


def numbers(values):
    return " ".join(format(float(value), ".17g") for value in values)


def rotation(element: ET.Element) -> Rotation:
    return Rotation.from_quat(
        np.fromstring(element.get("quat", "1 0 0 0"), sep=" ")[[1, 2, 3, 0]]
    )


def move_into_parent(element: ET.Element, frame: ET.Element) -> None:
    """Compose a fixed frame into an explicitly positioned body, geom or site."""
    if any(
        name in element.attrib
        for name in ("euler", "axisangle", "xyaxes", "zaxis", "fromto")
    ):
        raise ValueError("Only explicit pos/wxyz frame authoring is supported")
    parent_rotation = rotation(frame)
    position = np.fromstring(element.get("pos", "0 0 0"), sep=" ")
    offset = np.fromstring(frame.get("pos", "0 0 0"), sep=" ")
    element.set("pos", numbers(offset + parent_rotation.apply(position)))
    element.set(
        "quat", numbers((parent_rotation * rotation(element)).as_quat()[[3, 0, 1, 2]])
    )


def collapse_massless_frames(root: ET.Element, massless: set[str]) -> dict[str, str]:
    """Remove zero-inertia fixed frames, retaining their named sites for FK.

    The fixed root remains an explicitly nonphysical anchor. Its unit mass and
    inertia do not enter any moving joint's mass matrix; that is checked below.
    """
    remapped = {}

    def visit(parent):
        for body in list(parent.findall("body")):
            if body.get("name") in massless:
                if body.find("joint") is not None or body.find("freejoint") is not None:
                    raise ValueError("Cannot collapse a massless moving joint")
                if any(
                    child.tag not in ("inertial", "body", "geom", "site")
                    for child in body
                ):
                    raise ValueError(
                        "Unsupported contents in a massless coordinate frame"
                    )
                remapped[body.get("name")] = parent.get("name")
                site = ET.SubElement(
                    body, "site", name="frame_" + body.get("name"), size="0.0001"
                )
                site.set("rgba", "0 0 0 0")
                offset = list(parent).index(body)
                for child in list(body):
                    if child.tag != "inertial":
                        move_into_parent(child, body)
                        parent.insert(offset, child)
                        offset += 1
                parent.remove(body)
                # Children moved into this parent may themselves be massless.
                visit(parent)
                return
            visit(body)

    visit(root)
    for name, owner in remapped.items():
        while owner in remapped:
            owner = remapped[owner]
        remapped[name] = owner
    return remapped


def implicit_body_exclusions(
    model: mujoco.MjModel, names: list[str]
) -> set[tuple[str, str]]:
    """Make MuJoCo's weld-group/parent filtering explicit for native importers.

    Fixed links can remain separate PhysX bodies even though MuJoCo treats
    them as one weld group. Disabling all articulation self-collision is not
    equivalent. Explicit geom pairs override MuJoCo's body filters; reject
    conflicting overrides rather than disabling a requested contact.
    """
    ids = {name: model.body(name).id for name in names}
    if len(ids) != len(names):
        raise ValueError("Collision body names must be unique")
    filter_parent = not (
        model.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_FILTERPARENT
    )
    excluded = set()
    for index, first in enumerate(names):
        weld_first = int(model.body_weldid[ids[first]])
        parent_first = int(model.body_weldid[model.body_parentid[weld_first]])
        for second in names[index + 1 :]:
            weld_second = int(model.body_weldid[ids[second]])
            parent_second = int(model.body_weldid[model.body_parentid[weld_second]])
            if weld_first == weld_second or (
                filter_parent
                and weld_first != 0
                and weld_second != 0
                and (weld_first == parent_second or weld_second == parent_first)
            ):
                excluded.add(tuple(sorted((first, second))))
    for first_geom, second_geom in zip(model.pair_geom1, model.pair_geom2):
        pair = tuple(
            sorted(
                (
                    model.body(model.geom_bodyid[first_geom]).name,
                    model.body(model.geom_bodyid[second_geom]).name,
                )
            )
        )
        if pair in excluded:
            raise ValueError(
                "Explicit geom-pair override cannot be represented by a body exclusion"
            )
    return excluded


def preserve_implicit_filters(
    root: ET.Element, model: mujoco.MjModel
) -> list[list[str]]:
    """Add only source-implied exclusions and return the newly authored pairs."""
    robot = root.find("./worldbody/body[@name='robot_world']")
    if robot is None:
        raise ValueError("Expected robot_world body")
    contact = root.find("contact")
    if contact is None:
        contact = ET.SubElement(root, "contact")
    existing = {
        tuple(sorted((p.attrib["body1"], p.attrib["body2"])))
        for p in contact.findall("exclude")
    }
    names = [b.attrib["name"] for b in robot.iter("body")]
    added = sorted(implicit_body_exclusions(model, names) - existing)
    for first, second in added:
        ET.SubElement(contact, "exclude", body1=first, body2=second)
    return [list(pair) for pair in added]


def prepare(source_run: Path, output: Path) -> dict:
    """Transfer compiled physical parameters, never XML placeholder inertias."""
    output.mkdir(parents=True, exist_ok=False)
    source_xml = source_run / "model.xml"
    original = load_model(source_run)
    binary = source_run / "model.mjb"
    source_model_sha256 = (
        digest(binary)
        if binary.is_file()
        else json.loads((source_run / "model-artifact.json").read_text())[
            "uncompressed_sha256"
        ]
    )
    tree = ET.parse(source_xml).getroot()
    world = tree.find("worldbody")
    robot = world.find("body[@name='robot_world']")
    if robot is None:
        raise ValueError("Expected the existing OpenArm/Wuji robot_world subtree")
    robot_names = [b.get("name") for b in robot.iter("body")]
    with np.load(source_run / "command-plan.npz", allow_pickle=False) as plan:
        q_by_name = dict(
            zip(plan["joint_names"].tolist(), plan["pre"].tolist(), strict=True)
        )
    joint_names = [j.get("name") for j in robot.iter("joint")]
    if len(joint_names) != 54 or set(joint_names) != set(q_by_name):
        raise ValueError("Expected exactly the actual 54 OpenArm/Wuji joints")
    for child in list(world):
        if child is not robot:
            world.remove(child)
    for tag in ("custom", "keyframe", "size"):
        for child in tree.findall(tag):
            tree.remove(child)
    tree.find("compiler").attrib.pop("inertiafromgeom", None)
    tree.find("compiler").attrib.pop("fusestatic", None)
    tree.find("option").set("timestep", str(DT))
    tree.find("option").set("gravity", "0 0 0")
    massless = []
    for body in robot.iter("body"):
        source = original.body(body.get("name"))
        inertia = body.find("inertial")
        if inertia is None:
            raise ValueError("Every source body must declare its inertial frame")
        if float(source.mass[0]) == 0:
            if np.any(source.inertia != 0):
                raise ValueError("Zero-mass frame has nonzero effective inertia")
            massless.append(body.get("name"))
        inertia.attrib = {
            "mass": str(float(source.mass[0])),
            "pos": numbers(source.ipos),
            "quat": numbers(source.iquat),
            "diaginertia": numbers(source.inertia),
        }
    for actuator in tree.find("actuator"):
        aid = original.actuator(actuator.get("name")).id
        gain, bias = original.actuator_gainprm[aid], original.actuator_biasprm[aid]
        if gain[0] <= 0 or bias[1] != -gain[0] or bias[2] > 0:
            raise ValueError("Expected a position actuator")
        actuator.set("kp", str(gain[0]))
        actuator.set("kv", str(-bias[2]))
        actuator.set(
            "forcelimited", str(bool(original.actuator_forcelimited[aid])).lower()
        )
        if original.actuator_forcelimited[aid]:
            actuator.set("forcerange", numbers(original.actuator_forcerange[aid]))
    remapped = collapse_massless_frames(robot, set(massless) - {robot.get("name")})
    anchor = robot.find("inertial")
    anchor.attrib = {"mass": "1", "pos": "0 0 0", "diaginertia": "1 1 1"}
    retained = {b.get("name") for b in robot.iter("body")}
    contact = tree.find("contact")
    for pair in list(contact):
        for name in ("body1", "body2"):
            pair.set(name, remapped.get(pair.get(name), pair.get(name)))
        if (
            pair.get("body1") not in retained
            or pair.get("body2") not in retained
            or pair.get("body1") == pair.get("body2")
        ):
            contact.remove(pair)
    implicit_exclusions = preserve_implicit_filters(tree, original)
    # No contacts in this qualification. Preserve surfaces for later explicit
    # native SDF authoring; MJCF importer ignores the original type="sdf".
    sdf_geoms = []
    for geom in robot.iter("geom"):
        if geom.get("type") == "sdf":
            sdf_geoms.append(geom.get("name"))
            geom.set("type", "mesh")
    used = {g.get("mesh") for g in robot.iter("geom")}
    mesh_hashes = {}
    assets = output / "meshes"
    assets.mkdir()
    for mesh in list(tree.find("asset")):
        if mesh.tag != "mesh" or mesh.get("name") not in used:
            tree.find("asset").remove(mesh)
            continue
        path = Path(mesh.get("file"))
        if not path.is_absolute():
            path = source_xml.parent / path
        destination = assets / (mesh.get("name") + path.suffix)
        shutil.copyfile(path, destination)
        mesh.set("file", str(destination.resolve()))
        mesh_hashes[destination.name] = digest(destination)
    q = np.array([q_by_name[name] for name in joint_names])
    ET.SubElement(
        ET.SubElement(tree, "keyframe"),
        "key",
        name="home",
        qpos=numbers(q),
        ctrl=numbers(q),
    )
    ET.indent(tree)
    filename = output / "robot.xml"
    ET.ElementTree(tree).write(filename, encoding="unicode")
    candidate = mujoco.MjModel.from_xml_path(str(filename))
    checks = compare_reduction(original, candidate, joint_names, q)
    # Self-contained FK/dynamics model for offline scoring; contacts are not
    # part of this qualification. No external meshes are needed to rescore.
    for parent in tree.iter():
        for child in list(parent):
            if child.tag in ("geom", "asset", "contact"):
                parent.remove(child)
    ET.ElementTree(tree).write(output / "kinematics.xml", encoding="unicode")
    scoring_model = mujoco.MjModel.from_xml_path(str(output / "kinematics.xml"))
    scoring_check = compare_reduction(original, scoring_model, joint_names, q)
    if not scoring_check["passed"]:
        raise RuntimeError("Self-contained scoring model changes physical parameters")
    report = {
        "source_run": str(source_run),
        "source_xml_sha256": digest(source_xml),
        "source_compiled_model_sha256": source_model_sha256,
        "command_plan_sha256": digest(source_run / "command-plan.npz"),
        "candidate_sha256": digest(filename),
        "mesh_sha256": mesh_hashes,
        "source_robot_body_count": len(robot_names),
        "candidate_body_count": len(retained),
        "scoring_model_checks": scoring_check,
        "joint_names": joint_names,
        "home": q.tolist(),
        "collapsed_frames": remapped,
        "original_sdf_geoms": sdf_geoms,
        "implicit_collision_exclusions": implicit_exclusions,
        "reduction_checks": checks,
        "scope": "contacts and gravity disabled; mesh conversion is not SDF equivalence",
        "anchor": "unit mass/inertia on fixed root; excluded from moving-joint dynamics",
        "drive_parameters": "compiled MuJoCo run; effective damping includes its dt*kp term; task parameters, not hardware calibration",
        "effort_limit": "unbounded source drives become UniSim 1e9 Nm; not hardware limits",
    }
    write_json(output / "model-transfer.json", report)
    if not checks["passed"]:
        raise RuntimeError(
            "Robot reduction differs from compiled source dynamics/kinematics"
        )
    return report


def compare_reduction(original, candidate, joint_names, home):
    """Check dynamics and FK against the original compiled model at 17 poses."""
    old_ids = [original.joint(name).id for name in joint_names]
    old_q = original.jnt_qposadr[old_ids]
    old_v = original.jnt_dofadr[old_ids]
    new_q = [candidate.joint(name).qposadr[0] for name in joint_names]
    old_body = [
        original.body(candidate.body(i).name).id for i in range(1, candidate.nbody)
    ]
    original.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
    candidate.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
    od, nd = mujoco.MjData(original), mujoco.MjData(candidate)
    old_m = np.empty((original.nv, original.nv))
    new_m = np.empty((candidate.nv, candidate.nv))
    rng = np.random.default_rng(54321)
    position_error = rotation_error = matrix_error = 0.0
    for sample in range(17):
        q = (
            home
            if sample == 0
            else rng.uniform(candidate.jnt_range[:, 0], candidate.jnt_range[:, 1])
        )
        od.qpos[:] = original.qpos0
        od.qpos[old_q], nd.qpos[new_q] = q, q
        mujoco.mj_forward(original, od)
        mujoco.mj_forward(candidate, nd)
        mujoco.mj_fullM(original, od, old_m)
        mujoco.mj_fullM(candidate, nd, new_m)
        matrix_error = max(
            matrix_error, float(np.max(np.abs(old_m[np.ix_(old_v, old_v)] - new_m)))
        )
        position_error = max(
            position_error,
            float(np.max(np.linalg.norm(od.xpos[old_body] - nd.xpos[1:], axis=1))),
        )
        rotation_error = max(
            rotation_error, float(np.max(np.abs(od.xmat[old_body] - nd.xmat[1:])))
        )
    return {
        "poses": 17,
        "position_error_m": position_error,
        "rotation_matrix_error": rotation_error,
        "joint_mass_matrix_error": matrix_error,
        "passed": position_error < 1e-10
        and rotation_error < 1e-10
        and matrix_error < 1e-10,
    }
