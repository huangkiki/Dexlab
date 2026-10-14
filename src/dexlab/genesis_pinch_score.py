"""Engine-independent checks for the frozen primitive pinch development fixture."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def table_depth(position, quaternion):
    """Exact oriented-box support against the horizontal reference plane."""
    w, x, y, z = quaternion
    half_height = .02 * (abs(2 * (x*z-w*y)) + abs(2 * (y*z+w*x)) + abs(1-2*(x*x+y*y)))
    return max(half_height - position[2], 0)


def score_trial(record, dt, *, force_limit=10., initial_x=0., include_timeline=False):
    rows = record['samples']
    if len(rows) != round(4 / dt):
        raise ValueError('Incomplete trajectory')
    if record.get('condition') not in ('pinch', 'open_negative'):
        raise ValueError('Unknown trial condition')
    initial = record['initial']
    cube = initial['cube_link']
    pads = set(initial['pad_links'])
    if len(pads) != 2 or cube in pads or initial['plane_link'] in pads:
        raise ValueError('Invalid body identity map')
    initial_ok = (
        math.isclose(initial['cube_mass'][0], .064, abs_tol=1e-12)
        and initial['gripper_mass'] == [0., 1., .1, .1]
        and initial['armature'] == [0., 0., 0.]
        and initial['kp'] == [1000., 500., 500.]
        and initial['kv'] == [50., 20., 20.]
        and initial['force_range'] == [[-50., -force_limit, -force_limit], [50., force_limit, force_limit]]
        and initial['q'] == [0., 0., 0.]
        and initial['object_pos'] == [initial_x, 0., .02]
        and initial['object_vel'] == [0., 0., 0.]
        and [v[0] for v in initial['geom_sol_params']] == [.002, .002]
        and [v[0] for v in initial['joint_sol_params']] == [.01, .01, .01]
    )
    native_depth = reference_depth = ledger_error = impulse_error = 0.
    hold_heights, release_heights, hold_pad_counts, hold_other, released_pad_force = [], [], [], [], []
    first_failure = {} if initial_ok else {'declared_import': 0.}
    timeline = []
    positive = record['condition'] == 'pinch'
    previous_velocity = initial['object_vel']
    for index, row in enumerate(rows):
        if not math.isclose(row['time'], (index+1)*dt, abs_tol=1e-12):
            raise ValueError('Nonuniform or missing sample')
        values = row['q'] + row['object_pos'] + row['object_vel'] + row['object_quat']
        if not all(math.isfinite(v) for v in values) or not math.isclose(sum(v*v for v in row['object_quat']), 1., abs_tol=1e-6):
            raise ValueError('Nonfinite state or invalid orientation')
        contact = row['contacts']
        count = len(contact['link_a'])
        if any(len(contact[k]) != count for k in ('link_b', 'force_a', 'force_b', 'penetration')):
            raise ValueError('Inconsistent contact ledger')
        force = [0., 0., 0.]
        active_pads = set()
        pad_vectors = {pad: [0., 0., 0.] for pad in pads}
        other_vertical = pad_force = 0.
        for i in range(count):
            a, b = contact['link_a'][i], contact['link_b'][i]
            if (a == cube) == (b == cube):
                raise ValueError('Contact does not identify one object side')
            f = contact['force_a'][i] if a == cube else contact['force_b'][i]
            partner = b if a == cube else a
            if not all(math.isfinite(v) for v in f + [contact['penetration'][i]]):
                raise ValueError('Nonfinite contact')
            for k in range(3):
                force[k] += f[k]
            magnitude = math.sqrt(sum(v*v for v in f))
            if partner in pads:
                pad_force += magnitude
                for axis in range(3):
                    pad_vectors[partner][axis] += f[axis]
                if magnitude > 1e-8:
                    active_pads.add(partner)
            else:
                other_vertical += abs(f[2])
            native_depth = max(native_depth, contact['penetration'][i])
        reference_depth = max(reference_depth, table_depth(row['object_pos'], row['object_quat']))
        net = row['object_contact_force'][0]
        if not all(math.isfinite(v) for v in net):
            raise ValueError('Nonfinite net force')
        ledger_error = max(ledger_error, max(abs(force[k]-net[k]) for k in range(3)))
        residual = math.sqrt(sum((.064*(row['object_vel'][k]-previous_velocity[k])-dt*(force[k]-(.064*9.81 if k == 2 else 0)))**2 for k in range(3)))
        impulse_error = max(impulse_error, residual/(.064*9.81*dt))
        previous_velocity = row['object_vel']
        if 2 <= row['time'] <= 3:
            hold_heights.append(row['object_pos'][2])
            hold_pad_counts.append(len(active_pads))
            hold_other.append(other_vertical)
        if 3.8 <= row['time'] <= 4:
            release_heights.append(row['object_pos'][2])
            released_pad_force.append(pad_force)
        sample_checks = {
            'native_penetration_1mm': native_depth <= .001,
            'reference_table_penetration_1mm': reference_depth <= .001,
            'force_ledger': ledger_error <= 1e-8,
            'momentum_balance_5percent_weight': impulse_error <= .05,
        }
        if 2 <= row['time'] <= 3:
            sample_checks['hold_or_negative'] = (
                row['object_pos'][2] >= .06 and len(active_pads) == 2 and other_vertical <= .01
            ) if positive else not active_pads
        if not positive and row['object_pos'][2] > .03:
            sample_checks['hold_or_negative'] = False
        if 3.8 <= row['time'] <= 4:
            sample_checks['released'] = row['object_pos'][2] <= .03 and pad_force <= .01
        for name, passed in sample_checks.items():
            if not passed:
                first_failure.setdefault(name, row['time'])
        if include_timeline:
            ordered_forces = [pad_vectors[pad] for pad in initial['pad_links']]
            timeline.append({
                'time_s': row['time'], 'center_z_m': row['object_pos'][2],
                'velocity_z_m_s': row['object_vel'][2],
                'pad_forces_on_cube_N': ordered_forces,
                'pad_abs_x_force_proxy_N': [abs(f[0]) for f in ordered_forces],
                'other_absolute_vertical_support_N': other_vertical,
            })
    checks = {
        'declared_import': initial_ok,
        'native_penetration_1mm': native_depth <= .001,
        'reference_table_penetration_1mm': reference_depth <= .001,
        'force_ledger': ledger_error <= 1e-8,
        'momentum_balance_5percent_weight': impulse_error <= .05,
        'released': max(release_heights) <= .03 and max(released_pad_force) <= .01,
        'hold_or_negative': (min(hold_heights) >= .06 and min(hold_pad_counts) == 2 and max(hold_other) <= .01)
            if positive else (max(r['object_pos'][2] for r in rows) <= .03 and max(hold_pad_counts) == 0),
    }
    result = {'passed': all(checks.values()), 'checks': checks,
              'first_failure_time_s': first_failure, 'metrics': {
        'native_max_penetration_m': native_depth, 'reference_table_max_penetration_m': reference_depth,
        'maximum_force_ledger_error_N': ledger_error, 'maximum_momentum_residual_weight_ratio': impulse_error,
        'minimum_hold_center_z_m': min(hold_heights), 'maximum_release_center_z_m': max(release_heights)}}
    if include_timeline:
        result['timeline'] = timeline
    return result


def score(directory):
    protocol = json.loads((directory/'protocol.json').read_text())
    if protocol.get('schema') == 2:
        return score_force_case(directory, protocol)
    dt = protocol['dt_s']
    if dt not in (.001, .0005, .00025):
        raise ValueError('Unsupported timestep')
    for key, expected in {'schema': 1, 'engine': '1.4.3', 'steps': round(4/dt), 'duration_s': 4,
                          'mass_kg': .064, 'cube_size_m': .04, 'mu': .5, 'gravity_m_s2': 9.81,
                          'backend': 'cpu', 'precision': '64', 'seed': 0, 'repeats': 2,
                          'conditions': ['pinch', 'open_negative'], 'plane_cube_geom_timeconst_s': .002}.items():
        if protocol.get(key) != expected:
            raise ValueError(f'Unsupported protocol: {key}')
    results = {}
    reset_equal = {}
    for condition in ('pinch', 'open_negative'):
        previous = None
        for repeat in range(2):
            key = f'{condition}-{repeat}'
            record = json.loads((directory/f'{key}.json').read_text())
            if record['condition'] != condition or record['repeat'] != repeat:
                raise ValueError('Mislabeled trial')
            results[key] = score_trial(record, dt)
            if previous is not None:
                reset_equal[condition] = previous == record['samples']
            previous = record['samples']
    return {'passed': all(r['passed'] for r in results.values()) and all(reset_equal.values()),
            'results': results, 'exact_reset_replay': reset_equal,
            'scope': 'Development fixture only; no convergence, hardware, GPU or SDF qualification'}


def score_force_case(directory, protocol):
    """Bind observed initial parameters to a frozen case, retaining all thresholds."""
    manifest_path = Path(__file__).resolve().parents[2] / 'demos/contact-benchmark/force-limit-v1.json'
    manifest = json.loads(manifest_path.read_text())
    case = protocol.get('case')
    if case not in manifest['cases']:
        raise ValueError('Case is not in the preregistered manifest')
    expected = {'schema': 2, 'engine': manifest['engine_version'], 'dt_s': .0005,
                'steps': 8000, 'duration_s': 4, 'mass_kg': .064, 'cube_size_m': .04,
                'mu': .5, 'gravity_m_s2': 9.81, 'backend': 'cpu', 'precision': '64',
                'seed': 0, 'repeats': 1, 'conditions': [case['condition']],
                'plane_cube_geom_timeconst_s': .002}
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise ValueError(f'Unsupported force-limit protocol: {key}')
    runner = directory / 'runner.py'
    expected_source = Path(__file__).with_name('genesis_pinch_probe.py').read_bytes()
    recorded_source = runner.read_bytes()
    if recorded_source != expected_source or hashlib.sha256(recorded_source).hexdigest() != protocol.get('source_sha256'):
        raise ValueError('Unreviewed or corrupted runner source')
    if (directory / 'force-limit-v1.json').read_bytes() != manifest_path.read_bytes():
        raise ValueError('Manifest snapshot mismatch')
    record = json.loads((directory / f"{case['condition']}-0.json").read_text())
    if (record.get('condition') != case['condition'] or record.get('repeat') != 0
            or record.get('case_id') != case['id']):
        raise ValueError('Mislabeled force-limit trajectory')
    return score_force_record(record, case, include_timeline=True)


def score_force_record(record, case, *, include_timeline=False):
    """Score a case whose manifest and acquisition identity the caller verified."""
    result = score_trial(record, .0005, force_limit=case['force_limit_N'],
                         initial_x=case['initial_x_m'], include_timeline=include_timeline)
    checks = result['checks']
    observed = record['initial']
    checks['initial_rest_orientation'] = (
        observed.get('object_quat') == [1., 0., 0., 0.]
        and observed.get('object_ang') == [0., 0., 0.]
        and observed.get('qvel') == [0., 0., 0.]
    )
    expected_inertia = .064 * .04**2 / 6
    inertia = observed.get('cube_inertia', [])
    checks['box_inertia_and_friction'] = (
        len(inertia) == 1 and len(inertia[0]) == 3
        and all(len(row) == 3 for row in inertia[0])
        and all(math.isclose(inertia[0][i][j], expected_inertia if i == j else 0., abs_tol=1e-12)
                for i in range(3) for j in range(3))
        and observed.get('geom_friction') == [.5] * 4
    )
    if not checks['box_inertia_and_friction']:
        result['first_failure_time_s']['box_inertia_and_friction'] = 0.
    if not checks['initial_rest_orientation']:
        result['first_failure_time_s']['initial_rest_orientation'] = 0.
    result['passed'] = all(checks.values())
    validity_keys = ('declared_import', 'native_penetration_1mm',
                     'reference_table_penetration_1mm', 'force_ledger',
                     'momentum_balance_5percent_weight', 'initial_rest_orientation', 'box_inertia_and_friction')
    result['case'] = case
    result['numerically_valid'] = all(checks[key] for key in validity_keys)
    result['task_passed'] = checks['hold_or_negative'] and checks['released']
    result['scope'] = 'Fixed simulation challenges; no hardware or population success claim'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2))
