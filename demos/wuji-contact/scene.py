"""A fixed-wrist Wuji scene from the published native prefab, without dynamics."""

import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import h5py
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from plan_wuji_pinch import MIDPOINT, PAD_CONTACT_NORMALS, PAD_CONTACT_POINTS, PINCH_AXIS, PINCH_SEED

PREFAB = Path("upstream/hands/wuji_hand2_beta1/right/wuji_hand2_beta1_right.superdex_bot")
FINGERS = ("index_finger", "thumb")


def numbers(values):
    return " ".join(format(float(x), ".17g") for x in values)


def transform(value):
    return (np.asarray(value.get("translation", [0, 0, 0]), dtype=float),
            Rotation.from_quat(value.get("rotation", [0, 0, 0, 1])))


def kinematics(prefab, q):
    """Prefab FK in the wrist frame; no simulation or state-reset rollout."""
    poses, joint_index = [], 0
    for link, joint in zip(prefab["links"], prefab["joints"], strict=True):
        child_pos, child_rot = transform(link.get("parentJointFromLink", {}))
        if np.linalg.norm(child_pos) > 1e-12 or child_rot.magnitude() > 1e-12:
            raise ValueError("This Wuji fixture requires identity child joint frames")
        if "parentLink" not in link:
            poses.append((np.zeros(3), Rotation.identity()))
            continue
        pos, rot = transform(joint.get("parentLinkFromJoint", {}))
        parent_pos, parent_rot = poses[link["parentLink"]]
        if joint["type"] == "Revolute":
            rot = rot * Rotation.from_rotvec(np.asarray(joint["axis"]) * q[joint_index])
            joint_index += 1
        elif joint["type"] != "Hard":
            raise ValueError(f"Unexpected child joint type: {joint['type']}")
        poses.append((parent_pos + parent_rot.apply(pos), parent_rot * rot))
    if joint_index != len(q):
        raise ValueError("Joint count mismatch")
    return dict(zip((x["name"] for x in prefab["links"]), poses, strict=True))


def pinch_plan(prefab, gap):
    joints = [j for j in prefab["joints"] if j["type"] == "Revolute"]
    q = np.zeros(len(joints))
    residuals = {}
    for finger_index, (finger, side) in enumerate(zip(FINGERS, (-1, 1), strict=True)):
        ids = [i for i, j in enumerate(joints) if j["name"].startswith("r_" + finger)]
        bounds = np.array([[np.dot(joints[i][key], joints[i]["axis"]) for i in ids]
                           for key in ("minLimit", "maxLimit")])
        seed = PINCH_SEED[finger_index * 4:(finger_index + 1) * 4]
        target = MIDPOINT + side * gap / 2 * PINCH_AXIS

        def residual(x):
            q[ids] = x
            pos, rot = kinematics(prefab, q)[f"r_{finger}_pad"]
            point = pos + rot.apply(PAD_CONTACT_POINTS[finger])
            normal = rot.apply(PAD_CONTACT_NORMALS[finger])
            return np.r_[10 * (point - target), .003 * (normal + side * PINCH_AXIS),
                         .00005 * (x - seed)]

        result = least_squares(residual, np.clip(seed, bounds[0] + 1e-5, bounds[1] - 1e-5),
                               bounds=bounds, max_nfev=300, diff_step=1e-4)
        error = np.linalg.norm(residual(result.x)[:3]) / 10
        if error > .0001:
            raise ValueError(f"{finger} pad target unreachable: {error} m")
        q[ids] = result.x
        residuals[finger] = float(error)
    return q, residuals


def verify_assets(robot_root, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    paths = manifest["archives"][0]["files"]
    for relative, expected in paths.items():
        path = Path(robot_root).parent / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing regular asset: {relative}")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Asset hash mismatch: {relative}")
    return hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()


def build(robot_root, output, config):
    """Export the exact source inertias and meshes; native mesh contact is convex."""
    robot_root, output = Path(robot_root), Path(output)
    output.mkdir(exist_ok=False)
    mesh_dir = output / "meshes"
    mesh_dir.mkdir()
    prefab = json.loads((robot_root / PREFAB).read_text())
    joints = [j for j in prefab["joints"] if j["type"] == "Revolute"]
    opened, open_errors = pinch_plan(prefab, config["open_gap_m"])
    closed, close_errors = pinch_plan(prefab, config["closed_gap_m"])
    x_axis = PINCH_AXIS / np.linalg.norm(PINCH_AXIS)
    z_axis = np.cross(x_axis, [0, 1, 0]); z_axis /= np.linalg.norm(z_axis)
    wrist_rotation = Rotation.from_matrix(np.array([x_axis, np.cross(z_axis, x_axis), z_axis]))
    wrist_position = np.array([0., 0., .6])
    object_position = wrist_position + wrist_rotation.apply(MIDPOINT)
    root = ET.Element("mujoco", model="Wuji fixed wrist contact qualification")
    ET.SubElement(root, "compiler", angle="radian", inertiafromgeom="false", fusestatic="false")
    ET.SubElement(root, "option", timestep=str(config["dt_s"]), gravity="0 0 -9.81",
                  integrator="implicitfast", solver="Newton", cone="elliptic",
                  iterations="100", tolerance="1e-10", impratio="1")
    ET.SubElement(root, "size", memory="128M")
    default = ET.SubElement(root, "default")
    ET.SubElement(default, "geom", density="0", condim="3", friction="1 0 0",
                  solref=".002 1", solimp=".95 .99 .001", margin="0")
    ET.SubElement(default, "joint", damping="0", armature="0", frictionloss="0")
    asset, world = ET.SubElement(root, "asset"), ET.SubElement(root, "worldbody")
    contact, actuator = ET.SubElement(root, "contact"), ET.SubElement(root, "actuator")
    ET.SubElement(world, "light", pos=".1 -.3 1.2", dir="0 0 -1", diffuse=".8 .8 .8")
    ET.SubElement(world, "light", pos="-.5 .2 .8", dir="1 -1 -.5", diffuse=".4 .4 .4")
    bodies, names, neighbors = [], [], [[] for _ in prefab["links"]]
    for index, (link, joint) in enumerate(zip(prefab["links"], prefab["joints"], strict=True)):
        name = link["name"]; names.append(name)
        if "parentLink" not in link:
            pos, rot, parent = wrist_position, wrist_rotation, world
            if joint["type"] != "Free":
                raise ValueError("Unexpected source wrist joint")
        else:
            pos, rot = transform(joint.get("parentLinkFromJoint", {}))
            parent = bodies[link["parentLink"]]
            hard = joint["type"] == "Hard"
            neighbors[index].append((link["parentLink"], hard))
            neighbors[link["parentLink"]].append((index, hard))
        body = ET.SubElement(parent, "body", name=name, pos=numbers(pos),
                             quat=numbers(rot.as_quat()[[3, 0, 1, 2]]))
        bodies.append(body)
        mass = link.get("mass", 0.)
        if mass > 0:
            xx, xy, xz, yy, yz, zz = link["momentOfInertia"]
            ET.SubElement(body, "inertial", pos=numbers(link["centerOfMass"]), mass=str(mass),
                          fullinertia=numbers([xx, yy, zz, xy, xz, yz]))
        if joint["type"] == "Revolute":
            axis = joint["axis"]
            bounds = [np.dot(joint[key], axis) for key in ("minLimit", "maxLimit")]
            ET.SubElement(body, "joint", name=joint["name"], axis=numbers(axis), type="hinge",
                          limited="true", range=numbers(bounds))
            limit = joint["effortLimit"]
            ET.SubElement(actuator, "motor", name=joint["name"], joint=joint["name"],
                          ctrllimited="true", ctrlrange=numbers([-limit, limit]),
                          forcelimited="true", forcerange=numbers([-limit, limit]))
        if link.get("shape"):
            source = robot_root / PREFAB.parent / link["shape"]
            with h5py.File(source) as mesh:
                vertices = np.asarray(mesh["mesh/coordinates"]).reshape(-1, 3)
                faces = np.asarray(mesh["mesh/connectivity"]).reshape(-1, 3)
            path = mesh_dir / (name + "_collision.obj")
            with path.open("w") as stream:
                for v in vertices:
                    stream.write("v " + numbers(v) + "\n")
                for f in faces:
                    stream.write("f " + " ".join(str(int(i) + 1) for i in f) + "\n")
            ET.SubElement(asset, "mesh", name=name, file="meshes/" + path.name, inertia="shell")
            ET.SubElement(body, "geom", name=name + "_collision", type="mesh", mesh=name,
                          group="3", rgba=".4 .4 .4 0")
            render_path = mesh_dir / (name + "_render.obj")
            shutil.copyfile(robot_root / render_path.name, render_path)
            ET.SubElement(asset, "mesh", name=name + "_render", file="meshes/" + render_path.name)
            color = ".22 .26 .30 1" if "pad" in name else ".85 .87 .89 1"
            ET.SubElement(body, "geom", name=name + "_visual", type="mesh", mesh=name + "_render",
                          contype="0", conaffinity="0", group="2", rgba=color)
    # Preserve the source's adjacent/fixed-link filtering and explicit overrides.
    shaped = [bool(link.get("shape")) for link in prefab["links"]]
    excluded = set()
    for i in range(len(bodies)):
        if not shaped[i]:
            continue
        visited, stack = {i}, [i]
        while stack:
            for j, hard in neighbors[stack.pop()]:
                if j in visited:
                    continue
                visited.add(j)
                if shaped[j] and j > i:
                    excluded.add((i, j))
                if hard or not shaped[j]:
                    stack.append(j)
    for entry in prefab["contactOverrides"]:
        pair = tuple(sorted([names.index(entry["linkA"]), names.index(entry["linkB"])]))
        if entry["enable"]:
            excluded.discard(pair)
        else:
            excluded.add(pair)
    for i, j in sorted(excluded):
        ET.SubElement(contact, "exclude", body1=names[i], body2=names[j])
    obj = ET.SubElement(world, "body", name="object", pos=numbers(object_position))
    ET.SubElement(obj, "freejoint", name="object_free")
    radius, mass = config["radius_m"], config["mass_kg"]
    ET.SubElement(obj, "inertial", pos="0 0 0", mass=str(mass),
                  diaginertia=numbers([.4 * mass * radius**2] * 3))
    ET.SubElement(obj, "geom", name="object", type="sphere", size=str(radius), rgba=".92 .33 .12 1")
    ET.indent(root)
    ET.ElementTree(root).write(output / "scene.xml", encoding="unicode")
    plan = dict(joint_names=[j["name"] for j in joints], open=opened.tolist(), closed=closed.tolist(),
                open_errors_m=open_errors, closed_errors_m=close_errors,
                wrist_position=wrist_position.tolist(), wrist_quaternion=wrist_rotation.as_quat().tolist(),
                object_position=object_position.tolist(),
                collision="MuJoCo convex hull of each source collision mesh; analytic object sphere",
                fixed_wrist="Source free root replaced by declared world-fixed wrist",
                source_prefab_sha256=hashlib.sha256((robot_root / PREFAB).read_bytes()).hexdigest())
    (output / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    return plan
