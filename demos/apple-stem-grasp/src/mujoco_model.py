"""Translate the downloaded OpenArm/Wuji prefab into native MuJoCo dynamics.

The two grasp pads and apple use native SDFs. Robot inertias and joint frames
come from the loaded asset; the model is generated locally, not redistributed.
"""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np
import trimesh
from apple_scene import APPLE, TABLE_CENTER, TABLE_SIZE
from scipy.spatial.transform import Rotation

PADS = ("r_index_finger_pad", "r_thumb_pad")


def numbers(values):
    return " ".join(format(float(value), ".17g") for value in values)


def pose(transform):
    return {
        "pos": numbers(transform.translation),
        "quat": numbers(np.asarray(transform.rotation)[[3, 0, 1, 2]]),
    }


def inertia_matrix(value):
    xx, xy, xz, yy, yz, zz = value
    return np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])


def add_inertial(body, native, massless):
    mass = 0.0 if native.is_static() else native.get_mass()
    inertia = inertia_matrix(native.get_rigid_moment_of_inertia_local())
    if mass == 0:
        # The XML compiler rejects massless moving links. Restore the asset's
        # exact values after compilation and check the full mass matrix.
        massless.append(body.get("name"))
        mass, inertia = 1e-8, np.eye(3) * 1e-8
    moments, axes = np.linalg.eigh(inertia)
    if np.linalg.det(axes) < 0:
        axes[:, -1] *= -1
    ET.SubElement(
        body,
        "inertial",
        mass=str(mass),
        pos=numbers(native.get_rigid_center_of_mass_local()),
        diaginertia=numbers(moments),
        quat=numbers(Rotation.from_matrix(axes).as_quat()[[3, 0, 1, 2]]),
    )


def excluded_pairs(prefab, links, scene):
    """Mirror native adjacent-link filtering and the prefab's explicit overrides."""
    neighbors = [[] for _ in links]
    shapes = [not link.get_surface_mesh().is_empty() for link in links]
    for i, (info, joint) in enumerate(zip(prefab.links, prefab.joints)):
        if info.parent_link >= 0:
            hard = joint.type.name == "HARD"
            neighbors[i].append((info.parent_link, hard))
            neighbors[info.parent_link].append((i, hard))
    disabled = set()
    for i in range(len(links)):
        if not shapes[i]:
            continue
        visited, stack = {i}, [i]
        while stack:
            for j, hard in neighbors[stack.pop()]:
                if j in visited:
                    continue
                visited.add(j)
                if shapes[j] and j > i:
                    disabled.add((i, j))
                if hard or not shapes[j]:
                    stack.append(j)
    by_name = {info.name: i for i, info in enumerate(prefab.links)}
    for override in prefab.contact_overrides:
        pair = tuple(sorted((by_name[override.link_a], by_name[override.link_b])))
        if override.enable:
            disabled.discard(pair)
        else:
            disabled.add(pair)
    for i, link in enumerate(links):
        for j in range(i + 1, len(links)):
            if not scene.is_layer_contact_enabled(
                link.get_contact_layer(), links[j].get_contact_layer()
            ):
                disabled.add((i, j))
    return disabled


def load_model(path):
    path = Path(path)
    if path.suffix == ".mjb":
        return mujoco.MjModel.from_binary_path(str(path))
    root = ET.parse(path).getroot()
    spec = mujoco.MjSpec.from_file(str(path))
    for geom in spec.geoms:
        if geom.type == mujoco.mjtGeom.mjGEOM_SDF:
            spec.mesh(geom.meshname).octree_maxdepth = 9
    model = spec.compile()
    for name in root.find('./custom/text[@name="massless_bodies"]').get("data").split():
        model.body(name).mass[:] = 0
        model.body(name).inertia[:] = 0
    data = mujoco.MjData(model)
    mujoco.mj_setConst(model, data)
    mujoco.mj_forward(model, data)
    matrix = np.empty((model.nv, model.nv))
    mujoco.mj_fullM(model, data, matrix)
    np.linalg.cholesky(matrix)
    return model


def build_model(prefab, links, scene, apple, directory):
    """Use native link-local surfaces and the display meshes already generated."""
    directory = Path(directory)
    assets_dir = directory / "model-assets"
    assets_dir.mkdir(exist_ok=True)
    root = ET.Element("mujoco", model="OpenArm + Wuji | MuJoCo SDF-SDF")
    ET.SubElement(
        root, "compiler", angle="radian", inertiafromgeom="false", fusestatic="false"
    )
    ET.SubElement(
        root,
        "option",
        timestep=".0005",
        integrator="implicitfast",
        solver="Newton",
        iterations="100",
        tolerance="1e-10",
        cone="elliptic",
        gravity="0 0 -9.81",
        impratio="3000",
        sdf_initpoints="40",
        sdf_iterations="100",
    )
    ET.SubElement(root, "size", memory="256M")
    default = ET.SubElement(root, "default")
    ET.SubElement(
        default,
        "geom",
        density="0",
        friction="1 .001 .0001",
        condim="4",
        solref=".005 1",
        solimp=".95 .99 .001",
        margin="0",
    )
    ET.SubElement(default, "joint", damping="0", armature="0", solreflimit=".005 1")
    asset = ET.SubElement(root, "asset")
    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "geom", name="floor", type="plane", size="3 3 .1")
    table = ET.SubElement(world, "body", name="table", pos=numbers(TABLE_CENTER))

    def mesh_asset(name, mesh):
        filename = assets_dir / (name + ".obj")
        mesh.export(filename)
        ET.SubElement(
            asset, "mesh", name=name, file=str(filename.resolve()), inertia="shell"
        )

    # Small triangles avoid sparse mesh-SDF seeds across a large tabletop.
    table_mesh = trimesh.creation.box(extents=TABLE_SIZE)
    vertices, faces = trimesh.remesh.subdivide_to_size(
        table_mesh.vertices, table_mesh.faces, max_edge=0.04
    )
    mesh_asset(
        "table_mesh", trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    )
    ET.SubElement(table, "geom", name="table_collision", type="mesh", mesh="table_mesh")
    bodies, massless = {}, []
    actuator = ET.SubElement(root, "actuator")
    names = [
        info.name if info.name != "world" else "robot_world" for info in prefab.links
    ]
    for i, (info, joint, link) in enumerate(zip(prefab.links, prefab.joints, links)):
        if not np.allclose(
            info.parent_joint_from_link.translation, 0
        ) or not np.allclose(info.parent_joint_from_link.rotation, [0, 0, 0, 1]):
            raise ValueError(f"Unsupported nonidentity child joint frame: {info.name}")
        parent = world if info.parent_link < 0 else bodies[info.parent_link]
        attrs = pose(joint.parent_link_from_joint)
        if info.parent_link < 0:
            rotation = Rotation.from_quat(prefab.world_from_root.rotation)
            attrs = {
                "pos": numbers(
                    np.asarray(prefab.world_from_root.translation)
                    + rotation.apply(joint.parent_link_from_joint.translation)
                ),
                "quat": numbers(
                    (
                        rotation
                        * Rotation.from_quat(joint.parent_link_from_joint.rotation)
                    ).as_quat()[[3, 0, 1, 2]]
                ),
            }
        body = ET.SubElement(parent, "body", name=names[i], **attrs)
        bodies[i] = body
        add_inertial(body, link, massless)
        if joint.type.name == "REVOLUTE":
            axis = np.asarray(joint.axis)
            ET.SubElement(
                body,
                "joint",
                name=joint.name,
                type="hinge",
                axis=numbers(axis),
                limited="true",
                range=numbers(
                    [np.dot(joint.min_limit, axis), np.dot(joint.max_limit, axis)]
                ),
                damping=str(joint.friction.viscous),
                frictionloss=str(joint.friction.coulomb),
            )
            ET.SubElement(
                actuator,
                "position",
                name="pos_" + joint.name,
                joint=joint.name,
                kp="1000",
                kv="40",
            )
        elif joint.type.name != "HARD":
            raise ValueError(f"Unsupported joint: {joint.name}")
        surface = link.get_surface_mesh()
        if not surface.is_empty():
            mesh = trimesh.Trimesh(
                vertices=np.asarray(surface.coordinates).reshape(-1, 3),
                faces=np.asarray(surface.connectivity).reshape(-1, 3),
                process=False,
            )
            mesh_asset("collision_" + info.name, mesh)
            ET.SubElement(
                body,
                "geom",
                name="collision_" + info.name,
                type="sdf" if info.name in PADS else "mesh",
                mesh="collision_" + info.name,
                group="3",
                rgba=".5 .5 .5 0",
            )
    apple_body = ET.SubElement(
        world, "body", name="apple", **pose(apple.get_root_transform())
    )
    ET.SubElement(apple_body, "freejoint", name="apple_free")
    add_inertial(apple_body, apple, massless)
    ET.SubElement(
        asset,
        "mesh",
        name="apple_union",
        file=str(APPLE / "apple-stem-union.obj"),
        inertia="shell",
    )
    ET.SubElement(
        apple_body,
        "geom",
        name="collision_apple",
        type="sdf",
        mesh="apple_union",
        group="3",
        rgba="1 0 0 0",
    )
    contact = ET.SubElement(root, "contact")
    disabled = excluded_pairs(prefab, links, scene)
    # The wrist mesh's convex hull fills the installed ABAD mounting recess.
    for i, info in enumerate(prefab.links):
        if info.name.endswith("_proximal_abd"):
            parent = prefab.links[info.parent_link]
            wrist = prefab.links[parent.parent_link]
            if wrist.name in ("l_wrist", "r_wrist"):
                disabled.add(tuple(sorted((i, parent.parent_link))))
    for first, second in sorted(disabled):
        ET.SubElement(contact, "exclude", body1=names[first], body2=names[second])
    custom = ET.SubElement(root, "custom")
    ET.SubElement(custom, "text", name="massless_bodies", data=" ".join(massless))
    ET.indent(root)
    path = directory / "model.xml"
    ET.ElementTree(root).write(path, encoding="unicode")
    model = load_model(path)
    # Check loaded contact types rather than claiming SDF from an XML string.
    for name in (*PADS, "apple"):
        if model.geom("collision_" + name).type[0] != mujoco.mjtGeom.mjGEOM_SDF:
            raise RuntimeError(f"Expected native SDF for {name}")
    mujoco.mj_saveModel(model, str(directory / "model.mjb"))
    manifest = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(assets_dir.glob("*.obj"))
    }
    (directory / "model-assets.json").write_text(json.dumps(manifest, indent=2))
    return model
