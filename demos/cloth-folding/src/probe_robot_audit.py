"""Injected geometry controls on historical robot meshes, without simulation."""

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from dexlab import cloth_robot_audit
from dexlab.cloth_robot_audit import audit_robot, robot_hulls


def translated_cloth_pose(model, pose, delta):
    """Translate the archived three-slide-joint cloth; leave the robot intact."""
    data = mujoco.MjData(model)
    data.qpos[:] = pose
    mujoco.mj_kinematics(model, data)
    mujoco.mj_flex(model, data)
    before, robot_before = data.flexvert_xpos.copy(), data.geom_xpos.copy()
    result = pose.copy()
    for body in np.unique(model.flex_vertbodyid):
        start, count = int(model.body_jntadr[body]), int(model.body_jntnum[body])
        joints = np.arange(start, start + count)
        if count != 3 or np.any(model.jnt_type[joints] != mujoco.mjtJoint.mjJNT_SLIDE):
            raise ValueError("Control requires three slide joints per cloth vertex")
        result[model.jnt_qposadr[joints]] += np.linalg.solve(data.xaxis[joints].T, delta)
    data.qpos[:] = result
    mujoco.mj_kinematics(model, data)
    mujoco.mj_flex(model, data)
    if (not np.allclose(data.flexvert_xpos, before + delta, rtol=0, atol=1e-10)
            or not np.array_equal(robot_before, data.geom_xpos)):
        raise ValueError("Injected control did not preserve the specified geometry")
    return result


def run(directory, frame):
    paths = [directory / name for name in ("model.mjb", "states.npz")]
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    model = mujoco.MjModel.from_binary_path(str(paths[0]))
    with np.load(paths[1], allow_pickle=False) as archive:
        pose, time, triangles = archive['qpos'][frame], archive['time_s'][frame], archive['triangles']
    data = mujoco.MjData(model)
    data.qpos[:] = pose
    mujoco.mj_kinematics(model, data)
    mujoco.mj_flex(model, data)
    pad = next(h for h in robot_hulls(model) if h.name == 'collision_r_thumb_pad')
    center = pad.vertices.mean(axis=0) @ data.geom_xmat[pad.geom_id].reshape(3, 3).T + data.geom_xpos[pad.geom_id]
    centroids = data.flexvert_xpos[triangles].mean(axis=1)
    index = int(np.argmin(np.linalg.norm(centroids - center, axis=1)))
    shifts = {'original': np.zeros(3), 'into_thumb': center - centroids[index],
              'translated_clear': np.array([0., 0., 2.])}
    reports = {}
    for name, delta in shifts.items():
        moved = translated_cloth_pose(model, pose, delta)
        reports[name] = {'cloth_translation_m': delta.tolist(),
                         'report': audit_robot(model, [time], [moved], triangles)}
    if reports['into_thumb']['report']['per_geom_maximum_interior_depth_m'][pad.name] <= 1e-4:
        raise ValueError('Injected 0.1 mm-plus thumb intrusion was not detected')
    if reports['translated_clear']['report']['status'] != 'no_sampled_intrusion':
        raise ValueError('Translated clear control is not separated')
    if before != {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}:
        raise ValueError('Input recording changed')
    return {'classification': 'synthetically_translated_geometry_not_a_physics_episode',
            'frame_index': frame, 'time_s': float(time), 'target_triangle': index,
            'target_geom': pad.name, 'input_sha256': before, 'physics_steps_executed': 0,
            'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'auditor_sha256': hashlib.sha256(Path(cloth_robot_audit.__file__).read_bytes()).hexdigest(),
            'controls': reports}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--frame', type=int, default=112)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.frame < 0 or args.output.exists() or args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error('Use a nonnegative frame and new output outside the record')
    result = run(args.directory, args.frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: value['report']['maximum_interior_depth_m']
                      for key, value in result['controls'].items()}))
