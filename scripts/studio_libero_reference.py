"""Freeze LIBERO display geometry with its native MuJoCo 2.3.7 kinematics.

Run this file in the original LIBERO environment, then pass the NPZ to
prepare_studio_replays.py libero. No integration, controller or scorer is run.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if mujoco.__version__ != '2.3.7':
        raise ValueError('Reference requires the original MuJoCo 2.3.7')
    if args.output.exists():
        raise FileExistsError(args.output)
    model_path, trajectory = args.raw / 'effective-model.xml', args.raw / 'trajectory.npz'
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    with np.load(trajectory, allow_pickle=False) as record:
        states = np.vstack((record['initial'], record['state']))
    positions, rotations = [], []
    normalization_error = 0.
    for row in states:
        data.qpos[:] = row[1:1 + model.nq]
        mujoco.mj_fwdPosition(model, data)
        error = float(np.max(abs(data.qpos - row[1:1 + model.nq])))
        if error > 1e-14:
            raise ValueError('Kinematics changed more than quaternion roundoff')
        normalization_error = max(normalization_error, error)
        positions.append(data.geom_xpos.copy())
        rotations.append(data.geom_xmat.copy())
    fields = ('mesh_vert', 'mesh_vertadr', 'mesh_vertnum', 'geom_type', 'geom_dataid', 'geom_size')
    with args.output.open('xb') as stream:
        np.savez_compressed(stream, positions=positions, rotations=rotations, times=states[:, 0],
                            **{key: np.asarray(getattr(model, key)) for key in fields})
    info = {'native_version': mujoco.__version__, 'quaternion_roundoff_max': normalization_error, 'physics_steps': 0, 'frames': len(states),
            'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (model_path, trajectory)},
            'reference_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    args.output.with_suffix('.json').write_text(json.dumps(info, indent=2) + '\n')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
