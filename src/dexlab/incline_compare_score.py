"""Validate native evidence separately, then apply common incline metrics."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash, measure_response, score_campaign, require_close


def validate_admission(protocol, case, record):
    """Check saved native configuration independently of the running engine."""
    meta, config = record['metadata'], protocol['comparison']
    for key in ('identity', 'api_identity'):
        identity = meta[key]
        if identity['version'] != config['superdex_version'] or not identity['record_verified']:
            raise ValueError('Unverified official runtime')
    if record['double_precision'] is not True or record['time_s'] != 0:
        raise ValueError('Precision or initial clock mismatch')
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    initial = np.r_[protocol['side_m']/2*normal, np.cos(angle/2), 0, np.sin(angle/2), 0]
    if not np.allclose(record['pose'], initial, atol=1e-12, rtol=0) or np.any(record['velocity']):
        raise ValueError('Initial native state mismatch')
    if not np.allclose(record['gravity'], [0, 0, -protocol['gravity_m_s2']], atol=1e-12, rtol=0):
        raise ValueError('Native gravity mismatch')
    if not np.isclose(meta['mass_readback'], protocol['mass_kg'], atol=1e-12, rtol=0):
        raise ValueError('Native mass mismatch')
    inertia = protocol['mass_kg']*protocol['side_m']**2/6
    actual = np.asarray(meta['inertia_readback'])
    if actual.shape != (6,) or not np.allclose(actual, [inertia, 0, 0, inertia, 0, inertia], atol=1e-12, rtol=0):
        raise ValueError('Native inertia mismatch')
    solver = dict(integrator=config['integration_method'], iterations=config['solver_iterations'],
                  absolute_tolerance=config['absolute_tolerance'], relative_tolerance=config['relative_tolerance'])
    if meta['solver'] != solver:
        raise ValueError('Native solver mismatch')
    contact = config['normal_parameters'] | dict(coulomb_friction_coefficient=case['friction'],
        friction_falloff_vel=config['friction_falloff_vel'], viscous_friction_coefficient=config['viscous_friction_coefficient'])
    if meta['actor_contact_parameters'] != {'box': contact, 'plane': contact}:
        raise ValueError('Actor contact setting mismatch')
    geometry = record['geometry']
    vertices = np.asarray(geometry['vertices'])
    if geometry['box_collider'] != 'BOX' or geometry['plane_collider'] != 'PLANE':
        raise ValueError('Collider mismatch')
    if vertices.shape != (8, 3) or not np.allclose(np.abs(vertices), protocol['side_m']/2, atol=1e-12, rtol=0) or len(np.unique(vertices, axis=0)) != 8:
        raise ValueError('Native cube geometry mismatch')
    points = np.asarray(record['plane_query_points'])
    if points.shape != (3, 3) or not np.allclose(points, np.array([-.03, 0., .03])[:, None]*normal, atol=1e-12, rtol=0):
        raise ValueError('Plane query coordinates mismatch')
    if not np.allclose(record['plane_distances'], [-.03, 0, .03], atol=1e-12, rtol=0):
        raise ValueError('Native plane orientation mismatch')
    if 'solver_profile' in protocol:
        if record['effective_solver'] != protocol['effective_solver_expected']:
            raise ValueError('Effective solver parameters differ from frozen readback')
        require_close(record['box_com_local'], [0, 0, 0], 'box center of mass')
        if record['box_dofs'] != 6 or record['plane_dofs'] != 0:
            raise ValueError('Unexpected native degrees of freedom')
        if record['contact_pair_disabled_command'] is not bool(case.get('negative_no_floor', False)):
            raise ValueError('Incorrect contact-disable command')


def score_superdex(protocol, case, trace):
    """No fabricated per-contact friction or warning arrays for this backend."""
    h = case['timestep']
    steps = round(protocol['duration_s']/h)
    states, forces = np.asarray(trace['states']), np.asarray(trace['forces'])
    if states.shape != (steps+1, 14) or forces.shape != (steps, 3):
        raise ValueError('Truncated state or force record')
    for name in ('contact_distance', 'contact_count', 'force_times', 'contact_force_errors', 'statuses'):
        if np.asarray(trace[name]).shape != (steps,):
            raise ValueError(f'Malformed {name}')
    for name in ('states', 'forces', 'contact_distance', 'contact_count', 'force_times', 'contact_force_errors'):
        if not np.isfinite(trace[name]).all():
            raise ValueError(f'Nonfinite {name}')
    if not np.allclose(states[:, 0], np.arange(steps+1)*h, atol=1e-10, rtol=0):
        raise ValueError('Incorrect native clock')
    if not np.allclose(trace['force_times'], states[1:, 0], atol=1e-10, rtol=0):
        raise ValueError('Incorrect postsolve force epoch')
    if np.any(np.asarray(trace['contact_count']) < 0) or np.any(np.asarray(trace['contact_count']) % 1):
        raise ValueError('Invalid contact count')
    if not np.isin(trace['statuses'], ['CONVERGED', 'STOPPED']).all():
        raise ValueError('Diverged or unrecognized native solver status')
    if np.max(trace['contact_force_errors']) > 1e-7:
        raise ValueError('Contact force sum disagrees with total native force')
    if not np.allclose(np.diff(states[:, 1:4], axis=0), states[1:, 8:11]*h, atol=1e-10, rtol=0):
        raise ValueError('Position/velocity inconsistency or state injection')
    angle = np.deg2rad(case['angle_deg'])
    initial = np.r_[protocol['side_m']/2*np.array([np.sin(angle), 0, np.cos(angle)]),
                    np.cos(angle/2), 0, np.sin(angle/2), 0]
    if not np.allclose(states[0, 1:8], initial, atol=1e-12, rtol=0) or np.any(states[0, 8:]):
        raise ValueError('Incorrect initial pose or velocity')
    if not np.allclose(np.linalg.norm(states[:, 4:8], axis=1), 1, atol=1e-8, rtol=0):
        raise ValueError('Nonunit quaternion')
    # Normalize only the interval label after validating the native postsolve epoch.
    common = dict(trace) | {'force_times': states[:-1, 0]}
    result = measure_response(protocol, case, common)
    result['contact_loss_fraction'] = float(np.mean(np.asarray(trace['contact_count']) == 0))
    result['solver_status_counts'] = {str(k): int(v) for k, v in zip(*np.unique(trace['statuses'], return_counts=True))}
    result['combined_friction_readback'] = None
    return result


def geometric_penetration(protocol, case, states):
    """Supplement native contact distances with the same cube/plane geometry."""
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    states = np.asarray(states)
    w, vector = states[:, 4:5], states[:, 5:8]
    local_normal = normal + 2*np.cross(vector, np.cross(vector, normal)-w*normal)
    support_radius = protocol['side_m']/2*np.sum(np.abs(local_normal), axis=1)
    clearance = states[:, 1:4] @ normal - support_radius
    return float(max(0., -np.min(clearance)))


def validate_contact_ledger(trace, ledger, stats):
    """Check saved contact queries against independent native total force/torque."""
    steps = len(trace['forces'])
    if len(ledger) != steps or len(stats) != steps:
        raise ValueError('Truncated contact or solver ledger')
    for index, (contacts, stat) in enumerate(zip(ledger, stats)):
        if len(contacts) != trace['contact_count'][index]:
            raise ValueError('Lost contacts')
        force_sum, torque_sum = np.zeros(3), np.zeros(3)
        for point in contacts:
            if type(point['box_is_actor_a']) is not bool:
                raise ValueError('Invalid contact ownership')
            for name in ('force_on_box', 'normal_native', 'point_a', 'point_b', 'velocity_a', 'velocity_b'):
                vector = np.asarray(point[name])
                if vector.shape != (3,) or not np.isfinite(vector).all():
                    raise ValueError('Malformed contact vector')
            if not np.isfinite(point['distance']):
                raise ValueError('Nonfinite contact distance')
            force = np.asarray(point['force_on_box'])
            position = np.asarray(point['point_a' if point['box_is_actor_a'] else 'point_b'])
            force_sum += force
            torque_sum += np.cross(position-trace['states'][index+1, 1:4], force)
        require_close(force_sum, trace['forces'][index], 'contact force sum', 1e-10)
        require_close(torque_sum, trace['contact_torques'][index], 'contact torque sum', 1e-10)
        require_close(trace['contact_distance'][index], min([0.]+[p['distance'] for p in contacts]),
                      'contact distance minimum')
        if any(not isinstance(stat[name], int) or stat[name] < 0
               for name in ('max_non_linear_iters', 'max_line_search_iters')):
            raise ValueError('Invalid solver iteration observation')
        if not np.isfinite(stat['residual_norm']) or stat['residual_norm'] < 0:
            raise ValueError('Invalid native residual observation')


def score_profile(root):
    """Score a prospective profile, preserving physical and invalid-record failures."""
    protocol = json.loads((root/'manifest.json').read_text())
    campaign = json.loads((root/'campaign.json').read_text())
    if campaign['admission_only'] or campaign['manifest_sha256'] != file_hash(root/'manifest.json'):
        raise ValueError('Not a bound physical campaign')
    if campaign['completed_cases'] != len(protocol['cases']):
        raise ValueError('Incomplete physical campaign')
    results, negatives = [], []
    for case in protocol['cases']:
        folder = root/case['id']
        metadata = json.loads((folder/'metadata.json').read_text())
        if metadata['case'] != case or metadata['state_writes_after_initialization'] != 0:
            raise ValueError('Case mismatch or state writes')
        hashes = metadata['ledger_sha256'] | {
            'trace.npz': metadata['trace_sha256'], 'admission.json': metadata['admission_sha256'],
            'geometry.npz': metadata['geometry_sha256']}
        for name, expected in hashes.items():
            if file_hash(folder/name) != expected:
                raise ValueError('Artifact hash mismatch')
        validate_admission(protocol, case, json.loads((folder/'admission.json').read_text()))
        complete = json.loads((folder/'completion.json').read_text())
        if complete['error'] is not None or complete['completed_steps'] != round(protocol['duration_s']/case['timestep']):
            raise ValueError('Interrupted native record')
        with np.load(folder/'trace.npz', allow_pickle=False) as saved:
            trace = dict(saved)
        try:
            validate_contact_ledger(trace, json.loads((folder/'contacts.json').read_text()),
                                    json.loads((folder/'solver-stats.json').read_text()))
            measured = score_superdex(protocol, case, trace)
            measured.update(record_valid=True, geometric_penetration_m=geometric_penetration(protocol, case, trace['states']))
            if case.get('negative_no_floor', False):
                require_close(trace['forces'], np.zeros_like(trace['forces']), 'negative contact force', 1e-12)
                require_close(trace['contact_count'], np.zeros_like(trace['contact_count']), 'negative contacts', 0)
                target = -protocol['gravity_m_s2'] * trace['states'][:, 0]
                require_close(trace['states'][:, 10], target, 'negative freefall speed', 1e-9)
                if measured['passed']:
                    raise ValueError('Negative control incorrectly passes physical acceptance')
                measured['negative_control_validated'] = True
        except ValueError as error:
            measured = dict(record_valid=False, passed=False, failure=str(error),
                            checks={'native_evidence': False}, metrics=None)
        row = dict(id=case['id'], **measured)
        (negatives if case.get('negative_no_floor', False) else results).append(row)
    return dict(protocol=protocol, results=results, negative_controls=negatives,
                positive_count=len(results), positive_passed=sum(r['passed'] for r in results),
                scope='Frozen native profile; initial analytic qualification, no coverage-v1 credit')


def compare(superdex_root, mujoco_root):
    protocol = json.loads((superdex_root/'manifest.json').read_text())
    campaign = json.loads((superdex_root/'campaign.json').read_text())
    if len(protocol['cases']) != 9 or len({case['id'] for case in protocol['cases']}) != 9:
        raise ValueError('Incorrect paired case set')
    if campaign['admission_only'] or campaign['completed_cases'] != len(protocol['cases']):
        raise ValueError('Incomplete physical campaign')
    if campaign['manifest_sha256'] != file_hash(superdex_root/'manifest.json'):
        raise ValueError('Manifest hash mismatch')
    # Original strict MuJoCo artifact/readback checks remain unchanged.
    historical = score_campaign(mujoco_root)
    originals = {case['id']: case for case in historical['protocol']['cases']}
    for key in ('duration_s', 'score_start_s', 'mass_kg', 'side_m', 'gravity_m_s2', 'limits'):
        if protocol[key] != historical['protocol'][key]:
            raise ValueError(f'Nonpaired protocol field: {key}')
    results = []
    for case in protocol['cases']:
        if case != originals[case['id']]:
            raise ValueError('Nonpaired case')
        directory = superdex_root/case['id']
        meta = json.loads((directory/'metadata.json').read_text())
        if meta['case'] != case or meta['state_writes_after_initialization'] != 0:
            raise ValueError('Case mismatch or state writes')
        for name, key in [('trace.npz', 'trace_sha256'), ('admission.json', 'admission_sha256'), ('geometry.npz', 'geometry_sha256')]:
            if file_hash(directory/name) != meta[key]:
                raise ValueError('Artifact hash mismatch')
        validate_admission(protocol, case, json.loads((directory/'admission.json').read_text()))
        with np.load(directory/'trace.npz', allow_pickle=False) as trace:
            try:
                measured = score_superdex(protocol, case, trace)
                measured['record_valid'] = True
                measured['geometric_penetration_m'] = geometric_penetration(protocol, case, trace['states'])
            except ValueError as error:
                measured = dict(record_valid=False, passed=False, failure=str(error))
        old = next(row for row in historical['results'] if row['id'] == case['id'])
        with np.load(mujoco_root/case['id']/'trace.npz', allow_pickle=False) as trace:
            old['geometric_penetration_m'] = geometric_penetration(protocol, case, trace['states'])
        results.append(dict(id=case['id'], mujoco=old, superdex=measured,
                            superdex_metadata=meta))
    return dict(results=results, protocol=protocol,
                scope='Fixed native profiles, not calibrated materials or general engine ranking')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--superdex', type=Path)
    parser.add_argument('--mujoco', type=Path)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.profile is not None:
        if args.superdex is not None or args.mujoco is not None:
            parser.error('--profile cannot be combined with paired scoring')
        result = score_profile(args.profile)
    else:
        if args.superdex is None or args.mujoco is None:
            parser.error('Provide --profile or both --superdex and --mujoco')
        result = compare(args.superdex, args.mujoco)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
