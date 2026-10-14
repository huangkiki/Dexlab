"""Engine-free validation of native PhysX observations and analytical scoring."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import ImpulseConsistencyError, file_hash, measure_response, require_close


SOURCE_COMMIT = '517a0073715120e114ee055b63b26c95e00d9039'
PROFILES = {'pgs': (0, 16448), 'pgs-friction': (0, 49216),
            'tgs': (1, 16448), 'tgs-external': (1, 81984)}
LIMITS = dict(static_displacement_m=.001, static_speed_m_s=.001,
              sliding_velocity_rmse_m_s=.01, sliding_position_rmse_m=.01,
              acceleration_error_m_s2=.05, rotation_rad=.01,
              penetration_m=.001, force_balance_rmse_n=.01)
EPS32 = np.finfo(np.float32).eps


def require_float32(actual, expected, label):
    """Check finite model parameters, allowing their FP32 representation error."""
    actual, expected = np.asarray(actual), np.asarray(expected)
    tolerance = 8 * EPS32 * np.maximum(abs(expected), 1e-8)
    if (actual.shape != expected.shape or not np.isfinite(actual).all()
            or np.any(abs(actual - expected) > tolerance)):
        raise ValueError(f'Incorrect {label}')


def vector(value, label):
    result = np.asarray(value)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ValueError(f'Invalid {label}')
    return result


def validate_protocol(protocol):
    if protocol['profile'] not in PROFILES or protocol['source_commit'] != SOURCE_COMMIT:
        raise ValueError('Unqualified source or profile')
    for key, value in dict(schema_version=1, version='5.9.0', duration_s=2, score_start_s=.5,
                           side_m=.04, mass_kg=.064, gravity_m_s2=9.81, limits=LIMITS).items():
        if protocol[key] != value:
            raise ValueError(f'Changed protocol: {key}')
    positive = [c for c in protocol['cases'] if not c.get('negative_no_floor', False)]
    negative = [c for c in protocol['cases'] if c.get('negative_no_floor', False)]
    expected = {(regime, angle, mu, h) for regime, angle, mu in
                [('static', 15, .5), ('sliding', 35, .5), ('frictionless', 15, 0)]
                for h in (.002, .001, .0005)}
    if (len(positive) != 9 or len(negative) != 1 or
            {(c['regime'], c['angle_deg'], c['friction'], c['timestep']) for c in positive} != expected):
        raise ValueError('Expected nine positives and one negative')
    if any(negative[0][k] != v for k, v in dict(regime='static', angle_deg=15, friction=.5, timestep=.001).items()):
        raise ValueError('Incorrect negative')
    ids = [c['id'] for c in protocol['cases']]
    if len(set(ids)) != 10 or any(Path(x).name != x or x in ('', '.', '..') for x in ids):
        raise ValueError('Unsafe or duplicate case ID')


def validate_admission(protocol, case, a):
    solver, flags = PROFILES[protocol['profile']]
    expected = dict(kind='admission', sdk_version='5.9.0', sdk_version_integer=84475904,
                    real_bytes=4, profile=protocol['profile'], requested_timestep=case['timestep'],
                    effective_timestep=float(np.float32(case['timestep'])), solver_type=solver,
                    scene_flags=flags, friction_type=0, position_iterations=8, velocity_iterations=2,
                    dynamic_actors=1, static_actors=1, cpu_worker_count=1, contact_capacity=256,
                    linear_damping=0, angular_damping=0, sleep_threshold=0, stabilization_threshold=0,
                    body_flags=0, actor_flags=1, restitution=0, friction_combine_mode=0, material_flags=0,
                    scene_timestamp=1, errors=[])
    for key, value in expected.items():
        if a[key] != value:
            raise ValueError(f'Incorrect native {key}')
    if a['contact_report_bytes'] < 8192:
        raise ValueError('Insufficient contact stream capacity')
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    quat = [np.cos(angle / 2), 0, np.sin(angle / 2), 0]
    require_float32(a['initial_state'], np.r_[0, protocol['side_m'] / 2 * normal, quat, np.zeros(6)], 'initial state')
    require_float32(a['mass'], protocol['mass_kg'], 'mass')
    require_float32(a['inertia'], [protocol['mass_kg'] * protocol['side_m']**2 / 6] * 3, 'inertia')
    require_float32(a['gravity'], [0, 0, -protocol['gravity_m_s2']], 'gravity')
    require_float32(a['mass_frame'], [0, 0, 0, 1, 0, 0, 0], 'mass frame')
    plane_angle = angle - np.pi / 2
    require_float32(a['plane_pose'], [0, 0, 0, np.cos(plane_angle / 2), 0, np.sin(plane_angle / 2), 0], 'plane frame')
    require_float32([a['static_friction'], a['dynamic_friction']], [case['friction']] * 2, 'friction')
    for name, geometry in [('cube_shape', 3), ('plane_shape', 1)]:
        shape = a[name]
        expected_flags = 10 if name == 'cube_shape' and case.get('negative_no_floor', False) else 11
        if shape['geometry_type'] != geometry or shape['flags'] != expected_flags:
            raise ValueError('Wrong geometry or collision flags')
        require_float32([shape['contact_offset'], shape['rest_offset']], [.0001, 0], 'contact offsets')
        require_float32(shape['local_pose'], [0, 0, 0, 1, 0, 0, 0], 'shape frame')
    require_float32(a['cube_shape']['half_extents'], [protocol['side_m'] / 2] * 3, 'box size')


def validate_rows(protocol, case, admission, records):
    steps = round(protocol['duration_s'] / case['timestep'])
    if len(records) != steps + 2 or records[0] != admission:
        raise ValueError('Incomplete or changed native stream')
    completion = records[-1]
    if (completion['kind'] != 'completion' or completion['completed_steps'] != steps
            or completion['state_writes_after_initialization'] != 0 or completion['errors']):
        raise ValueError('Incomplete native case or post-initialization writes')
    rows = records[1:-1]
    states = np.array([admission['initial_state']] + [r['state'] for r in rows])
    if states.shape != (steps + 1, 14) or not np.isfinite(states).all():
        raise ValueError('Malformed native states')
    h = admission['effective_timestep']
    require_close(states[:, 0], np.arange(steps + 1) * h, 'native FP32 step clock', 1e-12)
    require_close(np.linalg.norm(states[:, 4:8], axis=1), np.ones(steps + 1), 'unit orientations', 8 * EPS32)
    # TGS external-force substeps are not one semi-implicit Euler update.
    # Enforce actual pre/post continuity, not an inapplicable final-velocity identity.
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    forces, counts, distances = [], [], []
    for i, row in enumerate(rows):
        if (row['kind'] != 'step' or row['step'] != i or row['scene_timestamp'] != admission['scene_timestamp'] + i + 1
                or row['errors'] or row['overflow'] or row['sleeping']):
            raise ValueError('Invalid step counter, contacts, awake state or native errors')
        require_close(row['pre_state'], states[i], 'state continuity')
        require_close([row['interval_start_s'], row['interval_end_s']], states[i:i+2, 0], 'impulse interval', 1e-12)
        impulse, count, minimum = np.zeros(3), 0, 0.
        if len(row['pairs']) > 1:
            raise ValueError('Unexpected contact pair count')
        for pair in row['pairs']:
            if type(pair['cube_first']) is not bool:
                raise ValueError('Unknown native body order')
            sign = 1 if pair['cube_first'] else -1
            contacts, anchors = pair['contacts'], pair['friction_anchors']
            if (len(contacts) != pair['declared_contacts'] or len(contacts) >= admission['contact_capacity']
                    or len(anchors) >= admission['contact_capacity']):
                raise ValueError('Truncated contacts or friction anchors')
            if contacts and (not pair['normal_impulses_available'] or
                             (case['friction'] > 0 and not pair['friction_impulses_available'])):
                raise ValueError('Missing native impulse channel')
            if (pair['patch_count'] < 0 or pair['patch_count'] > len(contacts)
                    or (anchors and not pair['friction_impulses_available'])):
                raise ValueError('Invalid native patch or friction stream')
            for contact in contacts:
                require_float32(sign * np.asarray(contact['normal']), normal, 'world contact normal')
                vector(contact['position'], 'world contact point')
                raw = vector(contact['impulse'], 'normal impulse')
                if not np.isfinite(contact['separation']):
                    raise ValueError('Invalid separation')
                # extractContacts reports only normal impulse, not total impulse.
                magnitude = float(sign * raw @ normal)
                require_close(sign * raw, magnitude * normal, 'normal impulse direction', 1e-10)
                if magnitude < -1e-10:
                    raise ValueError('Attractive normal impulse')
                impulse += sign * raw
                minimum = min(minimum, contact['separation'])
            for anchor in anchors:
                vector(anchor['position'], 'world friction anchor')
                raw = vector(anchor['impulse'], 'friction impulse')
                require_close(raw @ normal, 0., 'tangential friction impulse', 1e-10)
                impulse += sign * raw
            count += len(contacts)
        forces.append(impulse / h)
        counts.append(count)
        distances.append(minimum)
    if case.get('negative_no_floor', False) and any(counts):
        raise ValueError('Disabled collision generated contacts')
    return dict(states=states, forces=np.array(forces), force_times=states[:-1, 0],
                contact_count=np.array(counts), contact_distance=np.array(distances))


def score_campaign(root):
    protocol = json.loads((root / 'manifest.json').read_text())
    validate_protocol(protocol)
    campaign = json.loads((root / 'campaign.json').read_text())
    if campaign['state'] != 'completed' or campaign['admission_only']:
        raise ValueError('Not a completed physical campaign')
    for name, key in [('manifest.json', 'protocol_sha256'), ('official-proof.json', 'proof_sha256'), ('runner.py', 'runner_sha256')]:
        if file_hash(root / name) != campaign[key]:
            raise ValueError('Changed campaign provenance')
    proof = json.loads((root / 'official-proof.json').read_text())
    if (proof['source_commit'] != SOURCE_COMMIT or proof['binary_sha256'] != protocol['binary_sha256']
            or campaign['binary_sha256'] != protocol['binary_sha256']
            or proof['recorder_sha256'] != protocol['recorder_sha256']
            or campaign['runner_sha256'] != protocol['runner_sha256']):
        raise ValueError('Changed frozen source or binary')
    if len(campaign['cases']) != len(protocol['cases']):
        raise ValueError('Incomplete campaign cases')
    results = []
    for case, meta in zip(protocol['cases'], campaign['cases'], strict=True):
        directory = root / case['id']
        if meta != json.loads((directory / 'metadata.json').read_text()) or meta['case'] != case:
            raise ValueError('Changed case binding')
        if not {'admission.json', 'native.jsonl.gz', 'stderr.txt'}.issubset(meta['hashes']):
            raise ValueError('Missing evidence binding')
        for name, digest in meta['hashes'].items():
            if Path(name).name != name or file_hash(directory / name) != digest:
                raise ValueError('Changed raw artifact')
        result = dict(case=case['id'], negative=case.get('negative_no_floor', False), valid=False, passed=False)
        try:
            if meta['error'] or meta['returncode']:
                raise ValueError(meta['error'] or 'Native process failed')
            admission = json.loads((directory / 'admission.json').read_text())
            if file_hash(directory / 'admission.json') != protocol['admission_sha256'][case['id']]:
                raise ValueError('Model or solver options changed after freeze')
            validate_admission(protocol, case, admission)
            with gzip.open(directory / 'native.jsonl.gz', 'rt') as stream:
                records = [json.loads(line) for line in stream]
            trace = validate_rows(protocol, case, admission, records)
            native_case = case | {'timestep': admission['effective_timestep']}
            result.update(measure_response(protocol, native_case, trace), valid=True)
            if result['negative']:
                result['negative_rejected'] = not result['passed']
        except (ValueError, KeyError) as error:
            result['error'] = f'{type(error).__name__}: {error}'
            if isinstance(error, ImpulseConsistencyError):
                result['impulse_residual_max_ns'] = error.residual
        results.append(result)
    return dict(profile=protocol['profile'], results=results, positives_passed=sum(r['passed'] and not r['negative'] for r in results),
                positives_total=9, reliable_coverage_v1=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(score_campaign(args.input), stream, indent=2, allow_nan=False)
        stream.write('\n')
