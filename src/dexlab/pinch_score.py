"""Engine-free pinch trace validation and bounded Coulomb-reference diagnostics.

Trace checks are not archive provenance or a claim of real-material accuracy.
"""

import numpy as np


def _close(actual, expected, tolerance, message):
    if not np.allclose(actual, expected, atol=tolerance, rtol=0):
        raise ValueError(message)


def _rotate(quaternion, vector):
    """Rotate vectors by unit wxyz quaternions, with NumPy broadcasting."""
    q = quaternion[..., 1:]
    cross = np.cross(q, vector)
    return vector + 2 * (quaternion[..., :1] * cross + np.cross(q, cross))


def _advance_quaternion(q, omega, h):
    angle = np.linalg.norm(omega, axis=-1, keepdims=True) * h
    xyz = omega * (h / 2) * np.sinc(angle / (2 * np.pi))
    w = np.cos(angle / 2)
    return np.concatenate((q[:, :1] * w - np.sum(q[:, 1:] * xyz, axis=1, keepdims=True),
                           q[:, :1] * xyz + w * q[:, 1:] + np.cross(q[:, 1:], xyz)), axis=1)


def _rmse(values):
    return float(np.sqrt(np.mean(np.square(values))))


def score_trace(protocol, case, trace):
    """Reject invalid observations; preserve valid evidence of physical failure."""
    p, c = protocol, case
    h = c['timestep']; n = round(p['duration_s'] / h); limits = p['limits']
    shapes = dict(states=(n+1, 18), commands=(n, 2), external=(n, 3),
                  forces=(n, 2, 3), moments=(n, 2, 3), contacts=(n, 16, 13),
                  counts=(n, 2), actuator=(n, 8), constraint=(n, 8), force_times=(n,))
    for name, shape in shapes.items():
        if name not in trace or np.shape(trace[name]) != shape:
            raise ValueError(f'Missing/malformed {name}')
        if name != 'contacts' and not np.isfinite(trace[name]).all():
            raise ValueError(f'Nonfinite {name}')
    warnings = np.asarray(trace.get('warnings', []))
    if warnings.ndim != 2 or warnings.shape[0] != n or warnings.shape[1] == 0 or np.any(warnings):
        raise ValueError('Missing/malformed/native warnings')
    state = np.asarray(trace['states']); q = state[:, 6:10]
    _close(state[:, 0], np.arange(n+1)*h, 1e-10, 'Incorrect state times')
    _close(trace['force_times'], state[:-1, 0], 1e-10, 'Incorrect force epoch')
    initial = np.zeros(18); initial[6] = 1
    _close(state[0], initial, 1e-12, 'Incorrect initial state')
    _close(np.linalg.norm(q, axis=1), 1, 1e-10, 'Nonunit quaternion')
    onset = round(p['preload_s']/h)
    normal_command = c['capacity_ratio'] * p['cube_mass_kg'] * p['gravity_m_s2'] / (2*p['friction'])
    expected_command = normal_command * np.minimum(np.arange(n)/round(p['ramp_s']/h), 1)
    _close(trace['commands'], np.repeat(expected_command[:, None], 2, axis=1), 1e-12, 'Wrong force command')
    expected_external = np.zeros((n, 3)); expected_external[onset:, 2] = -p['cube_mass_kg']*p['gravity_m_s2']
    _close(trace['external'], expected_external, 1e-12, 'Wrong external load')
    expected_actuator = np.zeros((n, 8)); expected_actuator[:, :2] = trace['commands']
    _close(trace['actuator'], expected_actuator, 1e-12, 'Motor/command mismatch')

    # Independently sum individual contacts, preserving the signed force on cube.
    contacts = np.asarray(trace['contacts']); active = np.isfinite(contacts[:, :, 0])
    if not np.isfinite(contacts[active]).all() or not np.isnan(contacts[~active]).all():
        raise ValueError('Incomplete contact slot')
    flat = contacts[active]
    if np.any(~np.isin(flat[:, 0], [0, 1])):
        raise ValueError('Unknown contact side')
    _close(np.linalg.norm(flat[:, 4:7], axis=1), 1, 1e-10, 'Nonunit contact normal')
    _close(flat[:, 11:13], p['friction'], 1e-12, 'Native friction mismatch')
    sums = np.zeros((n, 2, 3)); moments = np.zeros_like(sums)
    counts = np.zeros((n, 2), dtype=int); normals = np.zeros((n, 2))
    contact_normal = np.sum(flat[:, 4:7]*flat[:, 7:10], axis=1)
    tangent = flat[:, 7:10]-contact_normal[:, None]*flat[:, 4:7]
    cone_excess = float(np.max(np.linalg.norm(tangent, axis=1)-p['friction']*contact_normal, initial=0))
    tensile = float(-np.min(contact_normal, initial=0))
    epochs, slots = np.nonzero(active); side = flat[:, 0].astype(int)
    np.add.at(sums, (epochs, side), flat[:, 7:10])
    np.add.at(moments, (epochs, side), np.cross(flat[:, 1:4]-state[epochs, 3:6], flat[:, 7:10]))
    np.add.at(counts, (epochs, side), 1)
    np.add.at(normals, (epochs, side), contact_normal)
    if not np.array_equal(trace['counts'], counts):
        raise ValueError('Contact count mismatch')
    _close(trace['forces'], sums, 1e-10, 'Summed contact force mismatch')
    _close(trace['moments'], moments, 1e-10, 'Summed contact moment mismatch')
    constraint = np.zeros((n, 8))
    constraint[:, 0] = -sums[:, 0, 0]; constraint[:, 1] = sums[:, 1, 0]
    constraint[:, 2:5] = sums.sum(axis=1)
    inverse_q = q[:-1].copy(); inverse_q[:, 1:] *= -1
    constraint[:, 5:8] = _rotate(inverse_q, moments.sum(axis=1))
    _close(trace['constraint'], constraint, 1e-9, 'Generalized/contact force mismatch')
    mass = p['cube_mass_kg']; inertia = mass*p['side_m']**2/6
    masses = np.array([p['jaw_mass_kg']]*2 + [mass]*3 + [inertia]*3)
    net = constraint + expected_actuator; net[:, 2:5] += expected_external
    impulse = np.diff(state[:, 10:18], axis=0)*masses-net*h
    impulse_peak = float(np.abs(impulse[:, :5]).max())
    angular_impulse_peak = float(np.abs(impulse[:, 5:]).max())
    if impulse_peak > limits['impulse_residual_n_s'] or angular_impulse_peak > limits['angular_impulse_residual_n_m_s']:
        raise ValueError('Impulse mismatch/state injection')
    _close(np.diff(state[:, 1:6], axis=0), h*state[1:, 10:15], limits['position_update_residual_m'], 'Euler position mismatch/state injection')
    predicted_q = _advance_quaternion(q[:-1], state[1:, 15:18], h)
    # Quaternion sign is a representation choice, not an orientation difference.
    alignment = np.where(np.sum(predicted_q*q[1:], axis=1) < 0, -1., 1.)
    _close(predicted_q*alignment[:, None], q[1:], 1e-10, 'Angular state integration mismatch')

    time = state[:, 0]; window = time >= p['score_start_s']-1e-10
    fw = time[:-1] >= p['score_start_s']-1e-10
    tau = time[window]-time[onset]; down = -state[:, 5]; speed = -state[:, 14]
    acceleration = max(0., p['gravity_m_s2']*(1-c['capacity_ratio']))
    predicted_v = speed[onset]+acceleration*tau
    predicted_x = down[onset]+speed[onset]*tau+.5*acceleration*tau**2
    rotation = 2*np.arccos(np.clip(np.abs(q[:, 0]), 0, 1))
    ideal_support = mass*(p['gravity_m_s2']-acceleration)
    metrics = dict(
        static_displacement_m=float(np.max(np.abs(down[onset:]-down[onset]))),
        static_speed_m_s=float(np.max(np.abs(speed[onset:]))),
        sliding_velocity_rmse_m_s=_rmse(speed[window]-predicted_v),
        sliding_position_rmse_m=_rmse(down[window]-predicted_x),
        acceleration_error_m_s2=float(abs(np.polyfit(tau, speed[window], 1)[0]-acceleration)),
        rotation_rad=float(rotation.max()),
        penetration_m=float(-np.min(flat[:, 10], initial=0)),
        lateral_drift_m=float(np.linalg.norm(state[:, 3:5], axis=1).max()),
        normal_command_relative_rmse=float(max(_rmse(normals[fw, i]/normal_command-1) for i in (0, 1))),
        contact_loss_fraction=float(np.mean(np.any(counts[onset:] == 0, axis=1))),
        force_balance_rmse_n=_rmse(sums[fw].sum(axis=1)-[0, 0, ideal_support]),
        friction_bound_slack_n=max(cone_excess, tensile),
        preload_speed_m_s=float(np.linalg.norm(state[onset, 12:15])))
    common = ('rotation_rad','penetration_m','lateral_drift_m','normal_command_relative_rmse',
              'contact_loss_fraction','force_balance_rmse_n','friction_bound_slack_n','preload_speed_m_s')
    motion = ('static_displacement_m','static_speed_m_s') if c['capacity_ratio'] >= 1 else (
        'sliding_velocity_rmse_m_s','sliding_position_rmse_m','acceleration_error_m_s2')
    checks = {name: metrics[name] <= limits[name] for name in common+motion}
    return dict(metrics=metrics, checks=checks, passed=None if c['capacity_ratio'] == 1 else all(checks.values()),
                status='marginal diagnostic' if c['capacity_ratio'] == 1 else 'evaluated',
                impulse_peak_ns=impulse_peak, angular_impulse_peak_nms=angular_impulse_peak,
                onset_state=state[onset].tolist(),
                initial_rest_velocity_rmse_m_s=_rmse(speed[window]-acceleration*tau),
                initial_rest_position_rmse_m=_rmse(down[window]-.5*acceleration*tau**2),
                measured_normal_capacity_mean_n=float(np.mean(p['friction']*normals[fw].sum(axis=1))),
                full_stage_normal_command_relative_rmse=[_rmse(normals[onset:, i]/normal_command-1) for i in (0, 1)],
                scope='Specified Coulomb fixture; measured-force capacity is diagnostic, not an independent prediction')
