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


def validate_readback(protocol, case, readback):
    """Check compiled configuration against the declared physical specification."""
    p = protocol
    size = p['jaw_half_size_m']; half = p['side_m']/2
    jaw_inertia = [p['jaw_mass_kg']*(size[(i+1)%3]**2+size[(i+2)%3]**2)/3 for i in range(3)]
    cube_inertia = p['cube_mass_kg']*p['side_m']**2/6
    expected = dict(
        nq=9, nv=8, nu=2, timestep=case['timestep'], gravity=[0,0,0],
        integrator=0, solver=2, cone=1, impratio=1,
        iterations=p['solver_iterations'], tolerance=p['solver_tolerance'],
        body_mass=[0,p['jaw_mass_kg'],p['jaw_mass_kg'],p['cube_mass_kg']],
        body_inertia=[[0,0,0],jaw_inertia,jaw_inertia,[cube_inertia]*3],
        body_pos=[[0,0,0],[-half-size[0],0,0],[half+size[0],0,0],[0,0,0]],
        jnt_type=[2,2,0], jnt_axis=[[1,0,0],[-1,0,0],[0,0,1]],
        jnt_qposadr=[0,1,2], jnt_dofadr=[0,1,2],
        dof_damping=[0]*8, dof_frictionloss=[0]*8, dof_armature=[0]*8,
        geom_type=[6]*3, geom_size=[size,size,[half]*3], geom_bodyid=[1,2,3],
        geom_friction=[[p['friction'],0,0]]*3, geom_condim=[3]*3,
        geom_solref=[p['solref']]*3,
        geom_solimp=[[case['impedance']]*2+[.001,.5,2]]*3,
        actuator_gear=[[1,0,0,0,0,0]]*2, actuator_gainprm=[[1]+[0]*9]*2,
        actuator_biasprm=[[0]*10]*2, actuator_trnid=[[0,-1],[1,-1]])
    if set(readback) != set(expected):
        raise ValueError('Compiled configuration fields differ')
    for name, value in expected.items():
        if np.shape(readback[name]) != np.shape(value):
            raise ValueError(f'Compiled shape mismatch: {name}')
        _close(readback[name], value, 1e-14, f'Compiled configuration mismatch: {name}')


def score_campaign(root, evidence):
    """Bind immutable inputs to a trusted protocol before numerical scoring.

    Local hashes detect inconsistency, not malicious fabrication or hardware truth.
    """
    import hashlib
    import json
    from pathlib import Path
    from dexlab.pinch_run import model_xml

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    protocol = json.loads((root/'manifest.json').read_text())
    frozen = json.loads((evidence/'manifest.json').read_text())
    if protocol != frozen:
        raise ValueError('Manifest differs from frozen protocol')
    campaign = json.loads((root/'campaign.json').read_text())
    if campaign['manifest_sha256'] != digest(root/'manifest.json'):
        raise ValueError('Manifest hash mismatch')
    if campaign['runner_sha256'] != digest(Path(__file__).with_name('pinch_run.py')):
        raise ValueError('Runner source mismatch')
    cases = protocol['cases']
    if len(cases) != 18 or len({c['id'] for c in cases}) != 18 or campaign['completed_cases'] != 18:
        raise ValueError('Incomplete/duplicate case matrix')
    runtime = campaign['runtime']
    if runtime.get('version') != protocol['version'] or runtime.get('record_verified') is not True:
        raise ValueError('Runtime record/version mismatch')
    rows = []
    for case in cases:
        directory = root/case['id']
        meta = json.loads((directory/'metadata.json').read_text())
        if meta['case'] != case or meta['state_writes_after_initialization'] != 0:
            raise ValueError('Case identity or state injection declaration')
        if (meta['cube_body'],meta['cube_geom'],meta['jaw_geoms']) != (3,2,[0,1]):
            raise ValueError('Native geometry/body identity mismatch')
        if meta['force_epoch'] != 'states[i].time; states[i+1] postintegration':
            raise ValueError('Force epoch declaration mismatch')
        for name, key in (('trace.npz','trace_sha256'),('model.xml','xml_sha256')):
            if digest(directory/name) != meta[key]:
                raise ValueError(f'Artifact hash mismatch: {case["id"]}/{name}')
        if (directory/'model.xml').read_text() != model_xml(protocol,case):
            raise ValueError('XML differs from declared scene')
        validate_readback(protocol,case,meta['readback'])
        timing = {k:meta[k] for k in ('setup_s','control_s','native_step_s','observation_s','serialization_s','total_case_wall_s')}
        if not all(np.isfinite(v) and v >= 0 for v in timing.values()):
            raise ValueError('Invalid cost record')
        with np.load(directory/'trace.npz',allow_pickle=False) as trace:
            try:
                result = score_trace(protocol,case,trace)
            except ValueError as error:
                # A rejected numerical trace must not hide the remaining matrix.
                result = dict(passed=False, status='invalid evidence', error=str(error))
        rows.append(dict(id=case['id'],**result,timing=timing,
                         trace_sha256=meta['trace_sha256'],xml_sha256=meta['xml_sha256']))
    return dict(protocol=protocol,campaign=campaign,results=rows,
                scorer_sha256=digest(Path(__file__)),
                passed_cases=sum(row['passed'] is True for row in rows),
                failed_cases=sum(row['passed'] is False and row['status'] != 'invalid evidence' for row in rows),
                invalid_cases=sum(row['status'] == 'invalid evidence' for row in rows),
                diagnostic_cases=sum(row['passed'] is None for row in rows))


def main():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = score_campaign(args.input,args.evidence)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
