"""Engine-independent checks for the frozen primitive pinch development fixture."""
import argparse
import json
import math
from pathlib import Path


def table_depth(position, quaternion):
    """Exact oriented-box support against the horizontal reference plane."""
    w, x, y, z = quaternion
    half_height = .02 * (abs(2 * (x*z-w*y)) + abs(2 * (y*z+w*x)) + abs(1-2*(x*x+y*y)))
    return max(half_height - position[2], 0)


def score_trial(record, dt):
    rows = record['samples']
    if len(rows) != round(4 / dt):
        raise ValueError('Incomplete trajectory')
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
        and initial['force_range'] == [[-50., -10., -10.], [50., 10., 10.]]
        and initial['q'] == [0., 0., 0.]
        and initial['object_pos'] == [0., 0., .02]
        and initial['object_vel'] == [0., 0., 0.]
        and [v[0] for v in initial['geom_sol_params']] == [.002, .002]
        and [v[0] for v in initial['joint_sol_params']] == [.01, .01, .01]
    )
    native_depth = reference_depth = ledger_error = impulse_error = 0.
    hold_heights, release_heights, hold_pad_counts, hold_other, released_pad_force = [], [], [], [], []
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
    positive = record['condition'] == 'pinch'
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
    return {'passed': all(checks.values()), 'checks': checks, 'metrics': {
        'native_max_penetration_m': native_depth, 'reference_table_max_penetration_m': reference_depth,
        'maximum_force_ledger_error_N': ledger_error, 'maximum_momentum_residual_weight_ratio': impulse_error,
        'minimum_hold_center_z_m': min(hold_heights), 'maximum_release_center_z_m': max(release_heights)}}


def score(directory):
    protocol = json.loads((directory/'protocol.json').read_text())
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2))
