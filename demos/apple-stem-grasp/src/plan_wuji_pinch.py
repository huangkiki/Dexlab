"""Native FK for a Wuji thumb/index pinch, with the other fingers folded away."""

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

MIDPOINT = np.array([0.007220762637925224, 0.04766233634419183, -0.10329213992842383])
PINCH_AXIS = np.array([0.3907896639367602, -0.00021523124219297515, 0.9204799792693519])
# Native IK opposition of measured distal surfaces on the current Beta 1 pads.
PAD_CONTACT_POINTS = {
    "index_finger": np.array([0.0004635374880864237, 0.00342909332255811, -0.022]),
    "thumb": np.array([-0.0005446435071906924, 0.004403587628418048, -0.026]),
}
PAD_CONTACT_NORMALS = {
    "index_finger": np.array(
        [0.05059817682549827, 0.7464876577935838, -0.6634726831330623]
    ),
    "thumb": np.array([-0.06805676636206305, 0.7540358824666177, -0.6532979140523324]),
}
PINCH_SEED = np.array(
    [
        0.2773231275960221,
        0.4929599999416662,
        1.2039319909469213,
        0.9286209939225749,
        1.0745031684903399,
        -0.15277445624527874,
        0.9198764317912855,
        -1.0469962940130848,
    ]
)


def pinch_pose(actor, links, joints, reference, gap):
    pose = reference.copy()
    wrist = links["r_wrist"]

    for finger, side in [("index_finger", -1), ("thumb", 1)]:
        ids = np.array(
            [i for i, j in enumerate(joints) if j.name.startswith("r_" + finger)]
        )
        bounds = np.array(
            [
                [
                    np.dot(np.array(getattr(joints[i], k)), np.array(joints[i].axis))
                    for i in ids
                ]
                for k in ["min_limit", "max_limit"]
            ]
        )
        target = MIDPOINT + side * gap / 2 * PINCH_AXIS
        seed = reference[ids].astype(float)

        def residual(x, ids=ids, finger=finger, target=target, seed=seed, side=side):
            pose[ids] = x
            actor.set_articulated_pose_from_joints(pose=pose)
            transform = wrist.get_root_transform()
            r = Rotation.from_quat(np.array(transform.rotation))
            pad = links[f"r_{finger}_pad"].get_root_transform()
            pad_rotation = Rotation.from_quat(np.array(pad.rotation))
            contact = pad_rotation.apply(PAD_CONTACT_POINTS[finger]) + np.array(
                pad.translation
            )
            local = r.inv().apply(contact - np.array(transform.translation))
            normal = (r.inv() * pad_rotation).apply(PAD_CONTACT_NORMALS[finger])
            return np.r_[
                10 * (local - target),
                0.003 * (normal + side * PINCH_AXIS),
                0.00005 * (x - seed),
            ]

        def jac(x):
            return np.column_stack(
                [
                    (residual(x + 0.001 * e) - residual(x - 0.001 * e)) / 0.002
                    for e in np.eye(4)
                ]
            )

        result = least_squares(
            residual,
            np.clip(seed, bounds[0] + 1e-5, bounds[1] - 1e-5),
            jac=jac,
            bounds=bounds,
            max_nfev=200,
        )
        if np.linalg.norm(result.fun[:3]) / 10 > 0.0001:
            raise RuntimeError(f"{finger} pinch IK residual: {result.fun}")
        pose[ids] = result.x
    return pose


def gravity_offset(actor, prefab, links, pose, ids, gains):
    """Feed forward dU/dq as a PD target offset; only evaluate unloaded FK."""

    def potential(q):
        actor.set_articulated_pose_from_joints(pose=q)
        value = 0.0
        for info, link in zip(prefab.links, links):
            if info.mass is None or info.center_of_mass is None:
                continue
            t = link.get_root_transform()
            com = Rotation.from_quat(np.array(t.rotation)).apply(
                np.array(info.center_of_mass)
            ) + np.array(t.translation)
            value += info.mass * 9.81 * com[2]
        return value

    offset = np.zeros_like(pose)
    for i in ids:
        plus, minus = pose.copy(), pose.copy()
        plus[i] += 0.001
        minus[i] -= 0.001
        offset[i] = (potential(plus) - potential(minus)) / 0.002 / gains[i]
    return offset
