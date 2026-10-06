"""Independent signed-distance audit of cloth vertices against a fixed plane."""

import mujoco
import numpy as np

from .cloth_table_audit import NUMERICAL_EPS_M


def audit_floor(model, times, vertices):
    """Linear triangle/plane distance reaches its minimum at a vertex.

    Report midsurface crossing separately from the declared collision-radius
    envelope; neither requires native collision detection or a physics step.
    """
    floor = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'floor')
    if (floor < 0 or model.geom_type[floor] != mujoco.mjtGeom.mjGEOM_PLANE
            or model.geom_bodyid[floor] != 0 or model.nflex != 1):
        return {'status': 'unsupported_geometry', 'reason': 'Require one cloth and a world-fixed floor plane'}
    times, vertices = np.asarray(times), np.asarray(vertices)
    if (times.ndim != 1 or not len(times)
            or vertices.shape != (len(times), model.nflexvert, 3)
            or not np.isfinite(vertices).all() or not np.isfinite(times).all()
            or np.any(np.diff(times) <= 0)):
        return {'status': 'insufficient_evidence', 'reason': 'Invalid saved state grid'}
    data = mujoco.MjData(model)
    mujoco.mj_kinematics(model, data)
    normal = data.geom_xmat[floor].reshape(3, 3)[:, 2]
    distances = (vertices - data.geom_xpos[floor]) @ normal
    minimum = distances.min(axis=1)
    depths = np.maximum(0, -minimum)
    envelopes = np.maximum(0, model.flex_radius[0] - minimum)
    frame, vertex = np.unravel_index(np.argmin(distances), distances.shape)
    count = int(np.count_nonzero(depths > NUMERICAL_EPS_M))
    return {
        'status': 'sampled_intrusion' if count else 'no_sampled_intrusion',
        'method': 'Independent vertex signed distance to fixed plane; triangle minimum is at a vertex',
        'evaluated_frames': len(times), 'frames_with_intrusion': count,
        'maximum_midsurface_depth_m': float(depths.max()),
        'maximum_radius_envelope_depth_m': float(envelopes.max()),
        'collision_radius_m': float(model.flex_radius[0]),
        'numerical_zero_tolerance_m': NUMERICAL_EPS_M,
        'witness': {'frame': int(frame), 'time_s': float(times[frame]),
                    'vertex': int(vertex), 'position_m': vertices[frame, vertex].tolist()},
        'scope': 'Saved-frame midsurface geometry and nominal radius envelope; no inter-step certification',
    }
