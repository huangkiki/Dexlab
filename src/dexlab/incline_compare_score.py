"""Validate native evidence separately, then apply common incline metrics."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash, measure_response, score_campaign


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
    parser.add_argument('--superdex', type=Path, required=True)
    parser.add_argument('--mujoco', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.superdex, args.mujoco)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
