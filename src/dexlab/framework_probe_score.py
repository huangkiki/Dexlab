"""Engine-free checks of the frozen framework clock/contact diagnostic.

This small diagnostic admits recorder development, never reliable task coverage.
"""

import argparse
import json
from pathlib import Path

import numpy as np


def decode_pyramidal_contact(forces, addresses, friction, dim):
    """Independent decoding for this fixture's frictionless/3D pyramid contacts."""
    if dim not in (1, 3):
        raise ValueError('This diagnostic only audits contact dimensions 1 and 3')
    if not np.isfinite(forces).all() or not np.isfinite(friction).all():
        raise ValueError('Non-finite native force or friction')
    size = 1 if dim == 1 else 4
    addresses = np.asarray(addresses[:size], dtype=int)
    if len(addresses) != size:
        raise ValueError('Missing native constraint addresses')
    if np.all(addresses == -1):
        return np.zeros(6)
    if np.any(addresses < 0) or np.any(addresses >= len(forces)):
        raise ValueError('Native constraint address outside the recorded solve')
    values = np.asarray(forces)[addresses]
    result = np.zeros(6)
    result[0] = values.sum()
    if dim == 3:
        result[1] = friction[0] * (values[0] - values[1])
        result[2] = friction[1] * (values[2] - values[3])
    return result


def audit_export(directory):
    """Compare saved native and CPU-converted forces without loading either engine."""
    from dexlab.mujoco_artifacts import cpu_contact_address_valid

    rows = [json.loads(line) for line in (Path(directory) / 'steps.jsonl').read_text().splitlines()]
    gpu_error = cpu_error = 0.
    affected_steps = []
    invalid_steps = []
    contacts = compared_cpu_contacts = invalid_cpu_contacts = 0
    for row in rows:
        changed = invalid = False
        for contact in row['contacts']:
            if not np.isfinite(contact['force_local']).all():
                raise ValueError('Non-finite contact-force readback')
            reconstructed = decode_pyramidal_contact(
                row['native_efc_force'], contact['native_efc_address'], contact['friction'], contact['dim'])
            error = float(np.max(np.abs(reconstructed - contact['force_local'])))
            gpu_error = max(gpu_error, error)
            cpu_valid = cpu_contact_address_valid(
                contact['cpu_efc_address'], contact['dim'], True, row['nefc'])
            if contact.get('cpu_address_in_bounds', cpu_valid) != cpu_valid:
                raise ValueError('CPU address-validity flag contradicts raw bounds')
            if cpu_valid:
                cpu_force = contact['cpu_converted_force_local']
                if cpu_force is None or not np.isfinite(cpu_force).all():
                    raise ValueError('Missing or non-finite in-bounds CPU readback')
                difference = float(np.max(np.abs(reconstructed - cpu_force)))
                cpu_error = max(cpu_error, difference)
                changed |= difference > 1e-5
                compared_cpu_contacts += 1
            else:
                invalid = True
                invalid_cpu_contacts += 1
            contacts += 1
        if changed:
            affected_steps.append(row['step'])
        if invalid:
            invalid_steps.append(row['step'])
    return {'steps': len(rows), 'contacts': contacts, 'native_decode_max_abs_N': gpu_error,
            'cpu_in_bounds_max_abs_N': cpu_error if compared_cpu_contacts else None,
            'cpu_compared_contacts': compared_cpu_contacts,
            'cpu_invalid_contacts': invalid_cpu_contacts, 'cpu_invalid_steps': invalid_steps,
            'cpu_mismatch_steps': affected_steps,
            'native_decode_within_1e_5_N': gpu_error <= 1e-5,
            'scope': 'Pyramidal fixture address audit. Out-of-bounds CPU force values, including historical values, are not physical observations.'}


def score(directory):
    directory = Path(directory)
    protocol = json.loads((directory / 'protocol.json').read_text())
    invocation = json.loads((directory / 'invocation.json').read_text())
    import hashlib
    if hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest() != invocation['protocol_sha256']:
        raise ValueError('Frozen protocol hash changed')
    case = next(row for row in protocol['cases'] if row['id'] == invocation['case'])
    admission = json.loads((directory / 'admission.json').read_text())
    completion = json.loads((directory / 'completion.json').read_text())
    model = json.loads((directory / 'conversion-readback.json').read_text())['compiled']
    rows = [json.loads(line) for line in (directory / 'steps.jsonl').read_text().splitlines()]
    if not rows:
        raise ValueError('No positive-duration observations')
    dt, limits = protocol['dt_s'], protocol['limits']
    bodies = np.flatnonzero(np.asarray(model['body_mass']) > 0)
    if len(bodies) != 1 or model['nq'] != 7 or model['nv'] != 6:
        raise ValueError('Diagnostic requires one free rigid body')
    body = int(bodies[0])
    mass = model['body_mass'][body]
    geom_body = np.asarray(model['geom_bodyid'])
    qvel = np.asarray([row['qvel'] for row in rows])
    qpos = np.asarray([row['qpos'] for row in rows])
    expected_times = np.arange(1, len(rows) + 1) * dt
    gpu_times = np.asarray([row['gpu_time_s'] for row in rows])
    framework_times = np.asarray([row['framework_time_s'] for row in rows])
    constraints = np.asarray([row['qfrc_constraint'][:3] for row in rows])
    acceleration = np.asarray([row['qacc'][:3] for row in rows])
    previous = np.vstack((np.asarray(model['state'][8:11]), qvel[:-1, :3]))
    delta = qvel[:, :3] - previous
    gravity = np.array([0., 0., -protocol['gravity_m_s2']])
    total = np.zeros((len(rows), 3))
    for index, row in enumerate(rows):
        for contact in row['contacts']:
            g0, g1 = contact['geom']
            sign = int(geom_body[g1] == body) - int(geom_body[g0] == body)
            total[index] += sign * np.asarray(contact['frame']).reshape(3, 3).T @ np.asarray(contact['force_local'])[:3]
    metrics = {
        'gpu_clock_error_s': float(np.max(np.abs(gpu_times - expected_times))),
        'framework_clock_error_s': float(np.max(np.abs(framework_times - expected_times))),
        'momentum_residual_Ns': float(np.max(np.linalg.norm(mass * delta - (constraints + mass * gravity) * dt, axis=1))),
        'contact_force_residual_N': float(np.max(np.linalg.norm(total - constraints, axis=1))),
        'acceleration_step_residual_m_s': float(np.max(np.linalg.norm(delta - acceleration * dt, axis=1))),
        'maximum_contacts': max(row['nacon'] for row in rows),
        'maximum_constraints': max(row['nefc'] for row in rows),
    }
    counts = [row['step'] for row in rows]
    checks = {
        'complete': (len(rows) == protocol['steps'] and counts == list(range(1, protocol['steps'] + 1))
                     and completion['completed_steps'] == completion['requested_steps'] == protocol['steps']),
        'finite': bool(np.isfinite(qvel).all() and np.isfinite(qpos).all()
                       and all(np.isfinite(x) for x in metrics.values())),
        'framework_counters': all(row['framework_step_count'] == row['step'] for row in rows),
        'clocks': max(metrics['gpu_clock_error_s'], metrics['framework_clock_error_s']) <= limits['clock_s'],
        'effective_dt': all(np.allclose(row['gpu_dt_s'], dt, rtol=0, atol=limits['dt_s']) for row in rows),
        'capacity': all(0 <= row['nacon'] <= admission['naconmax_shared'] and
                        0 <= row['nefc'] <= admission['njmax_per_world'] for row in rows),
        'contact_readback_complete': all(row['nacon'] == len(row['contacts']) for row in rows),
        'momentum': metrics['momentum_residual_Ns'] <= limits['momentum_Ns'],
        'contact_force': metrics['contact_force_residual_N'] <= limits['force_N'],
        'acceleration_epoch': metrics['acceleration_step_residual_m_s'] <= limits['velocity_m_s'],
        'selected_contact_path': admission['use_mujoco_contacts'] == case['mujoco_contacts'],
    }
    initial_position = np.asarray(model['state'][1:4])
    if case['no_floor']:
        freefall = initial_position + .5 * expected_times[:, None] ** 2 * gravity
        metrics['freefall_position_error_m'] = float(np.max(np.linalg.norm(qpos[:, :3] - freefall, axis=1)))
        checks['negative_freefall'] = metrics['freefall_position_error_m'] <= limits['freefall_m']
        checks['negative_has_no_contacts'] = metrics['maximum_contacts'] == 0
    else:
        metrics['displacement_m'] = float(np.max(np.linalg.norm(qpos[:, :3] - initial_position, axis=1)))
        checks['positive_support'] = metrics['maximum_contacts'] > 0 and metrics['displacement_m'] <= limits['support_m']
    return {'case': case['id'], 'passed': all(checks.values()), 'checks': checks, 'metrics': metrics,
            'scope': 'Development clock/contact diagnostic; task qualification and reliable coverage remain pending.'}


def score_native_state(directory):
    """Apply the same state/impulse bounds without inventing a framework clock.

    Native diagnostic records do not include per-contact forces, so this check
    intentionally makes no contact-force-sum or complete task acceptance claim.
    """
    import hashlib

    directory = Path(directory)
    raw = (directory / 'protocol.json').read_bytes()
    protocol = json.loads(raw)
    invocation = json.loads((directory / 'invocation.json').read_text())
    if hashlib.sha256(raw).hexdigest() != invocation['protocol_sha256']:
        raise ValueError('Frozen protocol hash changed')
    case = next(row for row in protocol['cases'] if row['id'] == invocation['case'])
    model = json.loads((directory / 'conversion-readback.json').read_text())['compiled']
    admission = json.loads((directory / 'admission.json').read_text())
    completion = json.loads((directory / 'completion.json').read_text())
    rows = [json.loads(line) for line in (directory / 'steps.jsonl').read_text().splitlines()]
    if not rows:
        raise ValueError('No positive-duration observations')
    bodies = np.flatnonzero(np.asarray(model['body_mass']) > 0)
    if len(bodies) != 1 or model['nq'] != 7 or model['nv'] != 6:
        raise ValueError('Diagnostic requires one free rigid body')
    mass, dt, limits = model['body_mass'][int(bodies[0])], protocol['dt_s'], protocol['limits']
    velocity = np.asarray([row['qvel'][:3] for row in rows])
    position = np.asarray([row['qpos'][:3] for row in rows])
    acceleration = np.asarray([row['qacc'][:3] for row in rows])
    constraint = np.asarray([row['qfrc_constraint'][:3] for row in rows])
    smooth = np.asarray([row['qfrc_smooth'][:3] for row in rows])
    previous = np.vstack((np.asarray(model['state'][8:11]), velocity[:-1]))
    delta = velocity - previous
    gravity = np.array([0., 0., -protocol['gravity_m_s2']])
    times = np.arange(1, len(rows) + 1) * dt
    initial_position = np.asarray(model['state'][1:4])
    metrics = {
        'gpu_clock_error_s': float(np.max(np.abs([row['gpu_time_s'] for row in rows] - times))),
        'momentum_residual_Ns': float(np.max(np.linalg.norm(mass * delta - (constraint + mass * gravity) * dt, axis=1))),
        'acceleration_step_residual_m_s': float(np.max(np.linalg.norm(delta - acceleration * dt, axis=1))),
        'native_equation_residual_N': float(np.max(np.linalg.norm(mass * acceleration - smooth - constraint, axis=1))),
        'maximum_contacts': max(row['nacon'] for row in rows),
        'maximum_constraints': max(row['nefc'] for row in rows),
    }
    checks = {
        'complete': (len(rows) == protocol['steps'] == completion['completed_steps']
                     and [row['step'] for row in rows] == list(range(1, protocol['steps'] + 1))),
        'finite': bool(all(np.isfinite(x) for x in metrics.values())
                       and all(np.isfinite(row[name]).all() for row in rows for name in
                               ('qpos', 'qvel', 'qacc', 'qfrc_constraint', 'qfrc_smooth'))),
        'clock': metrics['gpu_clock_error_s'] <= limits['clock_s'],
        'effective_dt': all(np.allclose(row['gpu_dt_s'], dt, rtol=0, atol=limits['dt_s']) for row in rows),
        'capacity': all(0 <= row['nacon'] <= admission['naconmax_shared']
                        and 0 <= row['nefc'] <= admission['njmax_per_world'] for row in rows),
        'contact_address_count': all(len(row['native_efc_address']) == row['nacon'] for row in rows),
        'momentum': metrics['momentum_residual_Ns'] <= limits['momentum_Ns'],
        'acceleration_epoch': metrics['acceleration_step_residual_m_s'] <= limits['velocity_m_s'],
    }
    if case['no_floor']:
        expected = initial_position + .5 * times[:, None] ** 2 * gravity
        metrics['freefall_position_error_m'] = float(np.max(np.linalg.norm(position - expected, axis=1)))
        checks['negative_freefall'] = metrics['freefall_position_error_m'] <= limits['freefall_m']
        checks['negative_has_no_contacts'] = metrics['maximum_contacts'] == 0
    else:
        metrics['displacement_m'] = float(np.max(np.linalg.norm(position - initial_position, axis=1)))
        checks['positive_support'] = metrics['maximum_contacts'] > 0 and metrics['displacement_m'] <= limits['support_m']
    return {'case': case['id'], 'passed': all(checks.values()), 'checks': checks, 'metrics': metrics,
            'scope': 'Native state-only development diagnostic; per-contact force and full task qualification not evaluated.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--native-state', action='store_true')
    args = parser.parse_args()
    result = score_native_state(args.directory) if args.native_state else score(args.directory)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
