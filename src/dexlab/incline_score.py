"""Analytical checks over measured free-box traces; no physics engine imports."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def rmse(values):
    return float(np.sqrt(np.mean(np.square(values))))


def score(protocol, case, trace):
    """Raise for invalid evidence; report physical failures without hiding them."""
    h = case['timestep']
    steps = round(protocol['duration_s'] / h)
    required = {'states', 'forces', 'force_times', 'contact_distance', 'contact_count', 'friction', 'warnings'}
    if not required.issubset(trace.keys()):
        raise ValueError('Missing trace fields')
    for name in ['force_times', 'contact_distance', 'contact_count']:
        if np.asarray(trace[name]).shape != (steps,):
            raise ValueError(f'Malformed {name}')
    if np.asarray(trace['warnings']).ndim != 2 or np.asarray(trace['warnings']).shape[0] != steps or np.asarray(trace['warnings']).shape[1] == 0:
        raise ValueError('Malformed warnings')
    states = np.asarray(trace['states'])
    forces = np.asarray(trace['forces'])
    if states.shape != (steps + 1, 14) or forces.shape != (steps, 3):
        raise ValueError('Truncated or malformed state/force trace')
    for name in ['states', 'forces', 'force_times', 'contact_distance', 'contact_count', 'warnings']:
        if not np.isfinite(trace[name]).all():
            raise ValueError(f'Nonfinite {name}')
    if not np.allclose(states[:, 0], np.arange(steps + 1) * h, atol=1e-10, rtol=0):
        raise ValueError('Incorrect sample times')
    if not np.allclose(trace['force_times'], states[:-1, 0], atol=1e-10, rtol=0):
        raise ValueError('Incorrect force epoch')
    if np.any(trace['warnings']):
        raise ValueError('Native solver warnings')
    if not np.allclose(np.diff(states[:, 1:4], axis=0), states[1:, 8:11] * h, atol=1e-10, rtol=0):
        raise ValueError('Position/velocity inconsistency or state injection')
    angle = np.deg2rad(case['angle_deg'])
    tangent = np.array([np.cos(angle), 0., -np.sin(angle)])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    initial_quat = np.array([np.cos(angle / 2), 0., np.sin(angle / 2), 0.])
    if not np.allclose(states[0, 1:4], protocol['side_m'] / 2 * normal, atol=1e-12):
        raise ValueError('Incorrect initial position or coordinate convention')
    if not np.allclose(states[0, 4:8], initial_quat, atol=1e-12) or np.any(states[0, 8:]):
        raise ValueError('Incorrect initial orientation/velocity')
    if not np.allclose(np.linalg.norm(states[:, 4:8], axis=1), 1, atol=1e-8):
        raise ValueError('Nonunit quaternion')
    active = np.asarray(trace['contact_count']) > 0
    mu = np.asarray(trace['friction'])
    if mu.shape != (steps, 2) or not np.isfinite(mu[active]).all():
        raise ValueError('Missing native friction')
    # Native engines can clamp exactly-zero friction to a tiny positive value.
    if not np.allclose(mu[active], case['friction'], atol=1e-5, rtol=0):
        raise ValueError('Native friction differs from declared model')
    return measure_response(protocol, case, trace)


def measure_response(protocol, case, trace):
    """Common numerical metrics; callers must first validate native evidence."""
    states, forces = np.asarray(trace['states']), np.asarray(trace['forces'])
    active = np.asarray(trace['contact_count']) > 0
    h = case['timestep']
    angle = np.deg2rad(case['angle_deg'])
    tangent = np.array([np.cos(angle), 0., -np.sin(angle)])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    initial_quat = np.array([np.cos(angle / 2), 0., np.sin(angle / 2), 0.])
    time = states[:, 0]
    position = states[:, 1:4] @ tangent
    speed = states[:, 8:11] @ tangent
    mask = time >= protocol['score_start_s'] - 1e-10
    force_mask = np.asarray(trace['force_times']) >= protocol['score_start_s'] - 1e-10
    tau = time[mask] - time[mask][0]
    g, mass = protocol['gravity_m_s2'], protocol['mass_kg']
    static = case['regime'] == 'static'
    acceleration = 0. if static else g * (np.sin(angle) - case['friction'] * np.cos(angle))
    fitted = float(np.polyfit(tau, speed[mask], 1)[0])
    predicted_v = speed[mask][0] + acceleration * tau
    predicted_s = position[mask][0] + speed[mask][0] * tau + .5 * acceleration * tau**2
    target_force = mass * g * np.cos(angle) * normal
    target_force -= (mass * g * np.sin(angle) if static else case['friction'] * mass * g * np.cos(angle)) * tangent
    residual = mass * np.diff(states[:, 8:11], axis=0) - (forces + [0, 0, -mass * g]) * h
    impulse_error = float(np.max(np.linalg.norm(residual, axis=1)))
    # A conservative numerical-consistency check, not an ideal-reference accuracy tolerance.
    if impulse_error > 1e-7:
        raise ValueError('State/force impulse inconsistency or possible state injection')
    rotation = 2 * np.arccos(np.clip(np.abs(states[:, 4:8] @ initial_quat), 0, 1))
    metrics = dict(static_displacement_m=float(np.max(np.abs(position - position[0]))),
                   static_speed_m_s=float(np.max(np.abs(speed[mask]))),
                   sliding_velocity_rmse_m_s=rmse(speed[mask] - predicted_v),
                   sliding_position_rmse_m=rmse(position[mask] - predicted_s),
                   acceleration_error_m_s2=float(abs(fitted - acceleration)),
                   rotation_rad=float(np.max(rotation)),
                   penetration_m=float(max(0, -np.min(trace['contact_distance']))),
                   force_balance_rmse_n=rmse(np.linalg.norm(forces[force_mask] - target_force, axis=1)))
    used = ['rotation_rad', 'penetration_m', 'force_balance_rmse_n']
    used += ['static_displacement_m', 'static_speed_m_s'] if static else [
        'sliding_velocity_rmse_m_s', 'sliding_position_rmse_m', 'acceleration_error_m_s2']
    checks = {name: metrics[name] <= protocol['limits'][name] for name in used}
    checks['continuous_support'] = bool(active[force_mask].all())
    return dict(metrics=metrics, checks=checks, passed=all(checks.values()),
                acceleration_reference_m_s2=float(acceleration), acceleration_fitted_m_s2=fitted,
                full_velocity_rmse_m_s=rmse(speed - acceleration * time),
                full_position_rmse_m=rmse(position - position[0] - .5 * acceleration * time**2),
                impulse_residual_max_ns=impulse_error)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_campaign(root):
    """Verify artifact bindings before scoring; never discard a failed case."""
    protocol = json.loads((root / 'manifest.json').read_text())
    campaign = json.loads((root / 'campaign.json').read_text())
    cases = protocol['cases']
    if campaign['manifest_sha256'] != file_hash(root / 'manifest.json'):
        raise ValueError('Manifest hash mismatch')
    if campaign['completed_cases'] != len(cases) or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Incomplete or duplicate cases')
    if campaign['runtime']['version'] != protocol['version'] or not campaign['runtime']['record_verified']:
        raise ValueError('Runtime identity mismatch')
    results = []
    for case in cases:
        directory = root / case['id']
        meta = json.loads((directory / 'metadata.json').read_text())
        if meta['case'] != case or meta['state_writes_after_initialization'] != 0:
            raise ValueError('Case mismatch or declared state injection')
        for name, key in [('trace.npz', 'trace_sha256'), ('model.xml', 'xml_sha256')]:
            if file_hash(directory / name) != meta[key]:
                raise ValueError(f'Artifact hash mismatch: {case["id"]}/{name}')
        readback = meta['readback']
        expected = {'nq': 7, 'nv': 6, 'nu': 0, 'timestep': case['timestep'],
                    'iterations': protocol['solver_iterations'], 'tolerance': protocol['solver_tolerance'],
                    'impratio': case.get('impratio', 1.), 'integrator': 0, 'solver': 2, 'cone': 1}
        if any(readback[k] != v for k, v in expected.items()):
            raise ValueError('Compiled solver/DOF mismatch')
        if not np.allclose(readback['gravity'], [0, 0, -protocol['gravity_m_s2']], atol=1e-12):
            raise ValueError('Gravity mismatch')
        if not np.isclose(readback['mass'][1], protocol['mass_kg'], atol=1e-12):
            raise ValueError('Mass mismatch')
        inertia = protocol['mass_kg'] * protocol['side_m']**2 / 6
        if not np.allclose(readback['inertia'][1], inertia, atol=1e-12):
            raise ValueError('Inertia mismatch')
        if readback['condim'] != [3, 3] or not np.allclose(readback['geom_friction'], [[case['friction'], 0, 0]] * 2, atol=1e-12):
            raise ValueError('Geometry friction mismatch')
        if not np.allclose(readback['solref'], [protocol['solref']] * 2, atol=1e-12) or not np.allclose(readback['solimp'], [[case['impedance'], case['impedance'], .001, .5, 2]] * 2, atol=1e-12):
            raise ValueError('Contact setting mismatch')
        with np.load(directory / 'trace.npz', allow_pickle=False) as trace:
            result = score(protocol, case, trace)
            active = trace['contact_count'] > 0
            result['contact_loss_fraction'] = float(np.mean(~active))
            result['native_friction_range'] = [float(np.min(trace['friction'][active])), float(np.max(trace['friction'][active]))]
        results.append(dict(id=case['id'], **result, timing={k: meta[k] for k in
            ['setup_s', 'native_step_s', 'observation_s', 'loop_wall_s', 'total_case_wall_s']},
            trace_sha256=meta['trace_sha256'], xml_sha256=meta['xml_sha256']))
    return dict(protocol=protocol, campaign=campaign, scorer_sha256=file_hash(Path(__file__)),
                results=results, passed_cases=sum(r['passed'] for r in results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = score_campaign(args.input)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
