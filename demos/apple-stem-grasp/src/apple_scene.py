"""Apple scene, native arm IK and display geometry."""
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from robot import ASSET, display_xml, physics, robotics

OUT = Path(__file__).resolve().parent
APPLE = OUT.parent / "assets/apple"
TABLE_TOP = 0.2995
TABLE_CENTER = np.array([0.30, 0.46, TABLE_TOP - 0.02])
TABLE_SIZE = np.array([0.6, 0.48, 0.04])
OPEN = np.array([0.05, 0, 0.05, 0.05] * 4 + [0.05, -0.39, 0.05, 0.05])
CLOSED = np.array([0.9, 0, 1.1, 0.8] * 4 + [0.8, -0.6, 1, 1])
PALM_ROTATION = Rotation.from_matrix([[-1, 0, 0], [0, 0, -1], [0, -1, 0]])

def solve_arm(
    actor, wrist, reference, arm_ids, bounds, position, palm_rotation=PALM_ROTATION
):
    """Solve native unloaded FK before dynamic actors are created."""

    def residual(angles):
        pose = reference.copy()
        pose[arm_ids] = angles
        actor.set_articulated_pose_from_joints(pose=pose)
        transform = wrist.get_root_transform()
        r = Rotation.from_quat(np.array(transform.rotation))
        return np.r_[
            np.array(transform.translation) - position,
            0.2 * (r * palm_rotation.inv()).as_rotvec(),
        ]

    def jacobian(angles):
        return np.column_stack(
            [
                (residual(angles + 0.001 * e) - residual(angles - 0.001 * e)) / 0.002
                for e in np.eye(len(arm_ids))
            ]
        )

    rng = np.random.default_rng(8)
    best = None
    for attempt in range(16):
        seed = (
            reference[arm_ids].astype(float) if attempt == 0 else rng.uniform(*bounds)
        )
        result = least_squares(
            residual,
            np.clip(seed, bounds[0] + 1e-5, bounds[1] - 1e-5),
            jac=jacobian,
            bounds=bounds,
            max_nfev=200,
        )
        if best is None or np.linalg.norm(result.fun) < np.linalg.norm(best.fun):
            best = result
        if np.linalg.norm(best.fun) < 2e-5:
            break
    if np.linalg.norm(best.fun) > 0.0002:
        raise RuntimeError(f"Unreachable wrist pose {position}: residual {best.fun}")
    pose = reference.copy()
    pose[arm_ids] = best.x
    return pose

def make_display(
    prefab, destination, *, title="OpenArm + Wuji | SuperDex"
):
    root = display_xml(prefab)
    root.set("model", title)
    assets = root.find("asset")
    world = root.find("worldbody")
    ET.SubElement(
        assets,
        "texture",
        type="skybox",
        builtin="gradient",
        rgb1=".26 .33 .42",
        rgb2=".05 .07 .10",
        width="512",
        height="3072",
    )
    ET.SubElement(
        assets,
        "texture",
        name="apple_color",
        type="2d",
        file=str(APPLE / "Textures/apple_albedo.png"),
    )
    ET.SubElement(
        assets,
        "material",
        name="apple_material",
        texture="apple_color",
        specular=".25",
        shininess=".35",
        texuniform="false",
    )
    ET.SubElement(
        assets, "mesh", name="apple_mesh", file=str(APPLE / "apple-render.obj")
    )
    apple_body = ET.SubElement(world, "body", name="native_apple", mocap="true")
    ET.SubElement(
        apple_body,
        "geom",
        type="mesh",
        mesh="apple_mesh",
        material="apple_material",
        contype="0",
        conaffinity="0",
    )
    ET.SubElement(
        world,
        "geom",
        name="table",
        type="box",
        size=" ".join(map(str, TABLE_SIZE / 2)),
        pos=" ".join(map(str, TABLE_CENTER)),
        rgba=".52 .35 .21 1",
    )
    for dx in [-0.25, 0.25]:
        for dy in [-0.19, 0.19]:
            ET.SubElement(
                world,
                "geom",
                type="box",
                size=f".02 .02 {(TABLE_TOP - 0.04) / 2}",
                pos=f"{TABLE_CENTER[0] + dx} {TABLE_CENTER[1] + dy} {(TABLE_TOP - 0.04) / 2}",
                rgba=".23 .26 .3 1",
            )
    xml = ET.tostring(root, encoding="unicode")
    (destination / "display.xml").write_text(xml)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.10, 0.22, 0.5]
    camera.distance = 2.4
    camera.azimuth = 225
    camera.elevation = -23
    return model, data, camera
