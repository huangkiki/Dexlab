"""Known-state fingertip planning on isolated FK data, followed by joint control."""

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

# Measured contact frames from the existing Wuji apple-stem experiment.
MIDPOINT = np.array([0.007220762638, 0.047662336344, -0.103292139928])
PINCH_AXIS = np.array([0.390789663937, -0.000215231242, 0.920479979269])
CONTACT_POINTS = {
    "index_finger": np.array([0.000463537488, 0.003429093323, -0.022]),
    "thumb": np.array([-0.000544643507, 0.004403587628, -0.026]),
}
CONTACT_NORMALS = {
    "index_finger": np.array([0.0505981768, 0.7464876578, -0.6634726831]),
    "thumb": np.array([-0.0680567664, 0.7540358825, -0.6532979141]),
}
PINCH_SEED = np.array(
    [
        0.2773231276,
        0.4929599999,
        1.2039319909,
        0.9286209939,
        1.0745031685,
        -0.1527744562,
        0.9198764318,
        -1.0469962940,
    ]
)


def smooth(time, start, end):
    fraction = np.clip((time - start) / (end - start), 0, 1)
    return fraction * fraction * (3 - 2 * fraction)


def joint_ids(model, prefix):
    return np.array(
        [
            joint
            for joint in range(model.njnt)
            if model.joint(joint).name.startswith(prefix)
        ],
        dtype=int,
    )


def mirror(side):
    return np.array([1, -1 if side == "l" else 1, 1])


def initial_pose(model, sides):
    pose = model.qpos0.copy()
    for joint in range(model.njnt):
        if model.jnt_limited[joint]:
            address = model.jnt_qposadr[joint]
            pose[address] = np.clip(pose[address], *model.jnt_range[joint])
    for side in sides:
        joints = np.r_[
            joint_ids(model, side + "_index_finger"), joint_ids(model, side + "_thumb")
        ]
        pose[model.jnt_qposadr[joints]] = PINCH_SEED
        pose = finger_pose(model, pose, side, 0.026)
    return pose


def finger_pose(model, reference, side, gap):
    """Solve the two opposing pad surfaces; other fingers keep their targets."""
    data = mujoco.MjData(model)
    data.qpos[:] = reference
    reflection = mirror(side)
    midpoint, axis = MIDPOINT * reflection, PINCH_AXIS * reflection
    wrist = model.body(side + "_wrist").id
    for finger, sign in (("index_finger", -1), ("thumb", 1)):
        joints = joint_ids(model, side + "_" + finger)
        positions = model.jnt_qposadr[joints]
        bounds = model.jnt_range[joints].T
        seed = reference[positions].copy()
        target = midpoint + sign * gap / 2 * axis
        pad = model.body(side + "_" + finger + "_pad").id

        def residual(angles):
            data.qpos[positions] = angles
            mujoco.mj_kinematics(model, data)
            wrist_rotation = data.xmat[wrist].reshape(3, 3)
            pad_rotation = data.xmat[pad].reshape(3, 3)
            point = wrist_rotation.T @ (
                data.xpos[pad]
                + pad_rotation @ (CONTACT_POINTS[finger] * reflection)
                - data.xpos[wrist]
            )
            normal = (
                wrist_rotation.T @ pad_rotation @ (CONTACT_NORMALS[finger] * reflection)
            )
            return np.r_[
                10 * (point - target),
                0.003 * (normal + sign * axis),
                0.00005 * (angles - seed),
            ]

        result = least_squares(
            residual,
            np.clip(seed, bounds[0] + 1e-5, bounds[1] - 1e-5),
            bounds=bounds,
            max_nfev=200,
        )
        if np.linalg.norm(result.fun[:3]) > 0.002:
            raise ValueError(f"{side} {finger} contact-frame IK failed: {result.fun}")
        data.qpos[positions] = result.x
    return data.qpos.copy()


def robot_penetration(model, data):
    """Largest reported robot self- or environment penetration, excluding cloth."""
    return max(
        (
            -float(contact.dist)
            for contact in data.contact
            if np.all(contact.geom >= 0)
            and any(
                model.geom(int(geom)).name.startswith("collision_")
                for geom in contact.geom
            )
        ),
        default=0,
    )


def arm_pose(model, reference, side, point, rotation, *, relax_orientation=False):
    """Find an arm solution and reject rigid collisions in the FK model."""
    data = mujoco.MjData(model)
    data.qpos[:] = reference
    arm = "left" if side == "l" else "right"
    joints = joint_ids(model, f"arm_openarm_{arm}_joint")
    positions = model.jnt_qposadr[joints]
    bounds = model.jnt_range[joints].T
    wrist = model.body(side + "_wrist").id
    target = point - rotation @ (MIDPOINT * mirror(side))

    def residual(angles):
        data.qpos[positions] = angles
        mujoco.mj_kinematics(model, data)
        error = Rotation.from_matrix(
            rotation @ data.xmat[wrist].reshape(3, 3).T
        ).as_rotvec()
        if relax_orientation:
            grip = data.xpos[wrist] + data.xmat[wrist].reshape(3, 3) @ (
                MIDPOINT * mirror(side)
            )
            mujoco.mj_fwdPosition(model, data)
            clearance = 10 * max(robot_penetration(model, data) - 0.00001, 0)
            return np.r_[
                grip - point,
                0.002 * error,
                0.0001 * (angles - reference[positions]),
                clearance,
            ]
        return np.r_[data.xpos[wrist] - target, 0.2 * error]

    rng = np.random.default_rng(8)
    best, best_score, best_depth = None, np.inf, np.inf
    for attempt in range(12):
        seed = reference[positions] if attempt == 0 else rng.uniform(*bounds)
        result = least_squares(
            residual,
            np.clip(seed, bounds[0] + 1e-5, bounds[1] - 1e-5),
            bounds=bounds,
            max_nfev=150,
        )
        data.qpos[positions] = result.x
        mujoco.mj_fwdPosition(model, data)
        depth = robot_penetration(model, data)
        score = np.linalg.norm(result.fun) + 100 * max(depth - 0.0001, 0)
        if score < best_score:
            best, best_score, best_depth = result, score, depth
        tolerance = 0.003 if relax_orientation else 1e-5
        if np.linalg.norm(best.fun) < tolerance and best_depth < 0.0001:
            break
    position_error = np.linalg.norm(best.fun[:3])
    acceptable_error = position_error < 0.001 and (
        relax_orientation or np.linalg.norm(best.fun) < 0.001
    )
    if not acceptable_error or best_depth > 0.0003:
        raise ValueError(
            f"{side} arm cannot reach {point}: residual {best.fun}; penetration {best_depth}"
        )
    data.qpos[positions] = best.x
    return data.qpos.copy()


def hand_environment_contacts(model, data, side):
    """Include every static scene geom, not just named tabletop boxes."""
    contacts = []
    prefix = "collision_" + side + "_"
    for contact in data.contact:
        names = [model.geom(int(geom)).name for geom in contact.geom if geom >= 0]
        hand = [name for name in names if name.startswith(prefix)]
        if not hand:
            continue
        if np.any(contact.flex >= 0) or any(
            not name.startswith("collision_") for name in names
        ):
            contacts.append(
                (hand, float(contact.dist), bool(np.any(contact.flex >= 0)))
            )
    return contacts


def grasp_candidates(model, state, side, material_ids, weights):
    """Use local cloth geometry, then verify that the actual pad meshes straddle it."""
    data = mujoco.MjData(model)
    data.qpos[:] = state
    mujoco.mj_fwdPosition(model, data)
    vertices = data.flexvert_xpos[material_ids]
    point = weights @ vertices
    normal = np.cross(vertices[0] - vertices[1], vertices[2] - vertices[1])
    normal /= np.linalg.norm(normal)
    closed = finger_pose(model, state, side, 0.0005)
    hand = model.jnt_qposadr[joint_ids(model, side + "_")]
    expected = {f"collision_{side}_{finger}_pad" for finger in CONTACT_POINTS}
    pinch_surfaces = expected | {
        f"collision_{side}_{finger}_nail" for finger in CONTACT_POINTS
    }
    # A nominal hanging-hem frame complements the noisy local triangle normal.
    nominal = np.array([0.15, -1.0, 0.2])
    angles = (60, 45, 75, 30, 90, 0, 120, 150, 180, 210, 240, 270, 300, 330)
    orientations = []
    for direction, nominal_frame in ((nominal, True), (normal, False)):
        direction = direction / np.linalg.norm(direction)
        for sign in (1, -1):
            axis = PINCH_AXIS if nominal_frame else PINCH_AXIS * mirror(side)
            aligned = Rotation.align_vectors([sign * direction], [axis])[0]
            for angle in angles:
                rotation = (
                    Rotation.from_rotvec(direction * np.deg2rad(angle)) * aligned
                ).as_matrix()
                if nominal_frame and side == "l":
                    rotation = np.diag([-1, 1, 1]) @ rotation @ np.diag([1, -1, 1])
                orientations.append((rotation, sign, angle))
    for rotation, sign, angle in orientations:
        try:
            opened = arm_pose(model, state, side, point, rotation)
        except ValueError:
            continue
        data.qpos[:] = opened
        mujoco.mj_fwdPosition(model, data)
        if any(
            distance < -0.0001
            for _, distance, _ in hand_environment_contacts(model, data, side)
        ):
            continue
        data.qpos[hand] = closed[hand]
        mujoco.mj_fwdPosition(model, data)
        contacts = hand_environment_contacts(model, data, side)
        pads = {
            name
            for names, _, cloth in contacts
            if cloth
            for name in names
            if name in expected
        }
        other_depth = min(
            (
                distance
                for names, distance, cloth in contacts
                if not cloth or any(name not in pinch_surfaces for name in names)
            ),
            default=0,
        )
        if pads == expected and other_depth >= -0.0003:
            yield {
                "opened": opened,
                "closed": closed[hand],
                "hand": hand,
                "point": point,
                "rotation": rotation,
                "material_ids": np.asarray(material_ids),
                "material_weights": np.asarray(weights),
                "side": side,
                "angle": angle,
                "normal_sign": sign,
            }
