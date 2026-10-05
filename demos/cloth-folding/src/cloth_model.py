"""Passive MuJoCo cloth and the robot exported by the apple-stem demo.

The only equality constraints belong to the cloth's internal edges. There are
no hand/cloth attachments, mocap bodies, or actuators on cloth vertices.
"""

from pathlib import Path
from itertools import product
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from dexlab.engine_versions import mujoco_profile_identity

TABLE_HEIGHT = 0.5
CLOTH_RADIUS = 0.0012


def numbers(values):
    return " ".join(
        format(float(value), ".17g") for value in np.asarray(values).ravel()
    )


def cloth_mesh(garment):
    """Return an original single-layer panel; the T shape is not a sewn shirt."""
    if garment:
        xs = np.arange(-9, 10) * 0.05
        ys = 0.36 + np.arange(13) * 0.025
    else:
        xs = np.linspace(0.08, 0.28, 13)
        ys = np.linspace(0.38, 0.58, 13)

    points, indices, triangles = [], {}, []

    def vertex(i, j):
        key = (i, j)
        if key not in indices:
            indices[key] = len(points)
            points.append((xs[i], ys[j], TABLE_HEIGHT + 0.002))
        return indices[key]

    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            center_x = (xs[i] + xs[i + 1]) / 2
            if garment:
                if abs(center_x) > 0.30 and not 7 <= j < 10:
                    continue
                if j >= 11 and abs(center_x) < 0.10:
                    continue
            a, b = vertex(i, j), vertex(i + 1, j)
            c, d = vertex(i + 1, j + 1), vertex(i, j + 1)
            triangles.extend(((a, b, c), (a, c, d)))

    return np.asarray(points), np.asarray(triangles), indices


def add_table(world, *, mesh_name=None):
    # MuJoCo 3.11 caps flex contacts per body pair. Separate fixed support
    # bodies preserve distributed support without changing the engine.
    for row, y in enumerate(np.linspace(0.4275, 0.8125, 8)):
        for column, x in enumerate(np.linspace(-0.495, 0.495, 12)):
            body = ET.SubElement(world, "body", name=f"table_{column}_{row}")
            ET.SubElement(
                body,
                "geom",
                name=f"table_{column}_{row}",
                **({"type": "box", "size": ".045 .0275 .003"} if mesh_name is None
                   else {"type": "mesh", "mesh": mesh_name}),
                pos=numbers((x, y, TABLE_HEIGHT - 0.003)),
                rgba=".34 .39 .43 1",
                condim="3",
                friction=".6 .005 .0001",
                solref=".002 1",
                solimp=".99 .999 .001",
            )


def load_model(path):
    """Restore zero-mass fixed links recorded by the original robot exporter."""
    root = ET.parse(path).getroot()
    model = mujoco.MjModel.from_xml_path(str(path))
    massless = root.find('./custom/text[@name="massless_bodies"]')
    if massless is not None:
        for name in massless.get("data", "").split():
            model.body(name).mass[:] = 0
            model.body(name).inertia[:] = 0
    mujoco.mj_setConst(model, mujoco.MjData(model))
    return model


def build_model(
    robot_model, destination, *, garment=False, hand_friction=1.0, timestep=0.00025,
    table_contact="box", floor_time_constant=0.002, edge_time_constant=0.002,
):
    """Keep native robot frames, inertia, meshes, joints and collision filters."""
    identity = mujoco_profile_identity({"version": mujoco.__version__}, mujoco.mj_versionString())
    integrator = ("discrete" if identity["profile_status"] == "candidate" else "implicitfast")
    robot_model = Path(robot_model).resolve()
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root = ET.parse(robot_model).getroot()
    root.set("model", "OpenArm + Wuji | frictional cloth manipulation")
    root.find("compiler").set("fusestatic", "false")
    world, assets = root.find("worldbody"), root.find("asset")
    for element in list(world):
        if element.tag == "geom" or element.get("name") in ("apple", "table"):
            world.remove(element)
    for asset in list(assets):
        if asset.get("name") in ("apple_union", "table_mesh"):
            assets.remove(asset)
        elif asset.get("file"):
            asset.set("file", str((robot_model.parent / asset.get("file")).resolve()))

    # The flex/rigid path uses the original surface meshes as convex colliders.
    # This demo does not claim the apple task's SDF/SDF contact representation.
    for geom in world.iter("geom"):
        geom.set("type", "mesh")
        geom.set("group", "0")
        geom.set(
            "rgba", ".15 .17 .2 1" if "pad" in geom.get("name", "") else ".65 .7 .76 1"
        )
        geom.set("contype", "2")
        geom.set("conaffinity", "3")
        if hand_friction != 1.0 and geom.get("name", "").startswith(
            ("collision_r_", "collision_l_")
        ):
            geom.set("priority", "1")
            geom.set("friction", f"{hand_friction} .005 .0001")

    option = root.find("option")
    option.attrib.clear()
    option.attrib.update(
        timestep=str(timestep),
        integrator=integrator,
        solver="Newton",
        iterations="100",
        tolerance="1e-8",
        jacobian="sparse",
        cone="pyramidal",
        impratio="100",
    )
    default = root.find("default/geom")
    default.set("condim", "3")
    default.set("friction", "1 .005 .0001")
    default.set("solref", ".002 1")
    default.set("solimp", ".99 .999 .001")
    for actuator in root.find("actuator"):
        finger = actuator.get("joint").startswith(("r_", "l_"))
        actuator.set("kp", "15" if finger else "1000")
        actuator.set("kv", ".15" if finger else "40")
        actuator.set("forcelimited", "true")
        actuator.set("forcerange", "-1 1" if finger else "-60 60")

    visual = ET.SubElement(root, "visual")
    ET.SubElement(visual, "global", offwidth="1280", offheight="960")
    ET.SubElement(visual, "headlight", ambient=".4 .4 .4", diffuse=".7 .7 .7")
    ET.SubElement(world, "light", pos="0 -.5 2", diffuse=".8 .8 .8")
    floor = ET.SubElement(
        world, "geom", name="floor", type="plane", size="3 3 .1", rgba=".10 .14 .20 1"
    )
    if floor_time_constant != 0.002:
        # Override pair mixing only for the explicitly selected floor response.
        floor.set("priority", "1")
        floor.set("solref", numbers((floor_time_constant, 1)))
    if table_contact not in ("box", "convex-mesh"):
        raise ValueError("Unknown table contact representation")
    mesh_name = None
    if table_contact == "convex-mesh":
        # Same cuboid surfaces, using the general convex/flex collision path.
        # This changes contact representation, not table dimensions or material.
        mesh_name = "cloth_table_cuboid"
        corners = np.array(list(product((-1, 1), repeat=3))) * (.045, .0275, .003)
        ET.SubElement(assets, "mesh", name=mesh_name, vertex=numbers(corners))
    add_table(world, mesh_name=mesh_name)

    vertices, triangles, indices = cloth_mesh(garment)
    flex = ET.SubElement(
        world,
        "flexcomp",
        name="cloth",
        type="direct",
        dim="2",
        mass=".025" if garment else ".015",
        radius=str(CLOTH_RADIUS),
        point=numbers(vertices),
        element=numbers(triangles),
        rgba=".02 .68 .63 1",
    )
    ET.SubElement(flex, "edge", equality="true", damping=".002",
                  solref=numbers((edge_time_constant, 1)))
    ET.SubElement(
        flex,
        "elasticity",
        young="1e5",
        poisson="0",
        thickness=".0005",
        elastic2d="bend",
        damping=".0001",
    )
    ET.SubElement(
        flex,
        "contact",
        selfcollide="auto",
        internal="false",
        contype="1",
        conaffinity="3",
        condim="3",
        friction="1 .005 .0001",
        solref=".002 1",
        solimp=".99 .999 .001",
    )
    ET.indent(root)
    path = destination / "model.xml"
    ET.ElementTree(root).write(path, encoding="unicode")
    model = load_model(path)
    if model.nmocap or any(kind != mujoco.mjtEq.mjEQ_FLEX for kind in model.eq_type):
        raise ValueError("Only internal cloth-edge equality constraints are allowed")
    cloth_bodies = set(model.flex_vertbodyid)
    if any(
        model.jnt_bodyid[joint] in cloth_bodies for joint in model.actuator_trnid[:, 0]
    ):
        raise ValueError("Cloth vertices must not be actuated")
    return model, vertices, triangles, indices
