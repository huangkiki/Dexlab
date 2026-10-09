"""Independent Newton incline validation and analytic scoring; NumPy only."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import ImpulseConsistencyError, file_hash, measure_response, require_close


PROFILES = ('xpbd', 'semiimplicit', 'featherstone', 'vbd-legacy', 'vbd-compliant',
            'kamino-padmm', 'kamino-dvi')
EPS32 = np.finfo(np.float32).eps
LIMITS = dict(static_displacement_m=.001, static_speed_m_s=.001,
              sliding_velocity_rmse_m_s=.01, sliding_position_rmse_m=.01,
              acceleration_error_m_s2=.05, rotation_rad=.01,
              penetration_m=.001, force_balance_rmse_n=.01)


def require_float32(actual, expected, label):
    """Bound representation error, never the physical acceptance limits."""
    actual, expected = np.asarray(actual), np.asarray(expected)
    tolerance = 8 * EPS32 * np.maximum(np.abs(expected), 1e-8)
    if (actual.shape != expected.shape or not np.isfinite(actual).all()
            or np.any(np.abs(actual - expected) > tolerance)):
        raise ValueError(f'Incorrect {label}')


def initial_state(protocol, case):
    angle = np.deg2rad(case['angle_deg'])
    return np.r_[0, protocol['side_m'] / 2 * np.array([np.sin(angle), 0, np.cos(angle)]),
                 np.cos(angle / 2), 0, np.sin(angle / 2), 0, np.zeros(6)]


def validate_protocol(protocol):
    if protocol['profile'] not in PROFILES:
        raise ValueError('Unqualified solver profile')
    if (protocol['limits'] != LIMITS
            or protocol['source_commit'] != '713fecdc41caf0c9d726f5c016939f36e66e3dff'):
        raise ValueError('Changed physical limits or source identity')
    for name, value in dict(schema_version=1, engine='Newton Physics', version='1.6.1',
                            warp_version='1.18.0', duration_s=2, score_start_s=.5,
                            side_m=.04, mass_kg=.064, density_kg_m3=1000,
                            gravity_m_s2=9.81).items():
        if protocol[name] != value:
            raise ValueError(f'Unqualified protocol: {name}')
    positive = [c for c in protocol['cases'] if not c.get('negative_no_floor', False)]
    negative = [c for c in protocol['cases'] if c.get('negative_no_floor', False)]
    expected = {(regime, angle, mu, h) for regime, angle, mu in
                [('static', 15, .5), ('sliding', 35, .5), ('frictionless', 15, 0)]
                for h in (.002, .001, .0005)}
    observed = {(c['regime'], c['angle_deg'], c['friction'], c['timestep']) for c in positive}
    if len(positive) != 9 or observed != expected or len(negative) != 1:
        raise ValueError('Expected nine distinct positive cases and one negative')
    if any(negative[0][k] != v for k, v in
           dict(regime='static', angle_deg=15, friction=.5, timestep=.001).items()):
        raise ValueError('Incorrect negative condition')
    ids = [c['id'] for c in protocol['cases']]
    if len(set(ids)) != 10 or any(Path(x).name != x or x in ('', '.', '..') for x in ids):
        raise ValueError('Unsafe or duplicate case ID')


def validate_admission(protocol, case, admission):
    model, counts = admission['model'], admission['counts']
    jointed = protocol['profile'] != 'semiimplicit'
    expected_counts = dict(body_count=1, joint_count=int(jointed),
                           joint_dof_count=6 * jointed, joint_coord_count=7 * jointed,
                           articulation_count=int(jointed), world_count=1,
                           shape_count=2, particle_count=0)
    if counts != expected_counts or admission['contact_capacity'] < 4:
        raise ValueError('Wrong native model topology or contact capacity')
    half = protocol['side_m'] / 2
    inertia = protocol['mass_kg'] * protocol['side_m'] ** 2 / 6
    expected = dict(body_mass=[protocol['mass_kg']], body_inertia=[np.eye(3) * inertia],
                    body_com=[[0, 0, 0]], body_flags=[1], body_world=[0],
                    shape_body=[-1, 0], shape_type=[1, 7],
                    shape_scale=[[0, 0, 0], [half] * 3], shape_material_mu=[case['friction']] * 2,
                    shape_material_ke=[2500] * 2, shape_material_kd=[100] * 2,
                    shape_material_kf=[1000] * 2, shape_material_ka=[0] * 2,
                    shape_material_restitution=[0] * 2, shape_material_mu_torsional=[0] * 2,
                    shape_material_mu_rolling=[0] * 2, shape_gap=[.01] * 2,
                    shape_margin=[0] * 2,
                    shape_collision_group=[1, 0 if case.get('negative_no_floor', False) else 1])
    for key, value in expected.items():
        require_float32(model[key], value, key)
    require_float32(admission['initial_state'], initial_state(protocol, case), 'initial state')
    initial = initial_state(protocol, case)
    require_float32(model['body_q'], [np.r_[initial[1:4], initial[5:8], initial[4]]], 'body pose')
    require_float32(model['shape_transform'],
                    [[0, 0, 0, *initial[5:8], initial[4]], [0, 0, 0, 0, 0, 0, 1]], 'shape frames')
    for name in ('joint_target_ke', 'joint_target_kd', 'joint_damping'):
        if model[name] is not None and np.any(model[name]):
            raise ValueError('Unrequested joint drive or damping')
    if admission['control_joint_f'] is not None and np.any(admission['control_joint_f']):
        raise ValueError('Nonzero control force')
    # Newton keeps one additional gravity row for the global world.
    require_float32(model['gravity'], [[0, 0, -protocol['gravity_m_s2']]] * 2, 'gravity')


def rotate(quat, vector):
    return vector + 2 * np.cross(quat[1:], np.cross(quat[1:], vector) + quat[0] * vector)


def validate_rows(protocol, case, admission, rows):
    dt = case['timestep']
    steps = round(protocol['duration_s'] / dt)
    if len(rows) != steps:
        raise ValueError('Incomplete physical observations')
    states = np.array([admission['initial_state']] + [r['state'] for r in rows])
    forces = np.array([r['net_force'] for r in rows])
    if (states.shape != (steps + 1, 14) or forces.shape != (steps, 3)
            or not np.isfinite(states).all() or not np.isfinite(forces).all()):
        raise ValueError('Malformed or nonfinite state/force observations')
    require_close(states[:, 0], np.arange(steps + 1) * dt, 'state interval schedule', 1e-12)
    require_close(np.linalg.norm(states[:, 4:8], axis=1), np.ones(steps + 1), 'unit quaternions', 8 * EPS32)
    tolerance = 8 * EPS32 * (np.abs(states[:-1, 1:4]) + np.abs(states[1:, 8:11] * dt) + protocol['side_m'])
    if np.any(np.abs(np.diff(states[:, 1:4], axis=0) - states[1:, 8:11] * dt) > tolerance):
        raise ValueError('Position/velocity mismatch beyond representation bound')
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0, np.cos(angle)])
    counts, distances = [], []
    expected_convention = ('force_on_body1' if protocol['profile'].startswith('vbd') else
                           'negative_solve_wrench' if protocol['profile'] == 'featherstone' else
                           'com_wrench' if protocol['profile'] == 'semiimplicit' else 'wrench_on_shape0')
    for index, row in enumerate(rows):
        require_close(row['pre_state'], states[index], 'state continuity')
        require_close([row['interval_start_s'], row['interval_end_s']],
                      states[index:index + 2, 0], 'force epoch')
        contacts, readback = row['contacts'], row['force_readback']
        if readback['convention'] != expected_convention:
            raise ValueError('Force convention differs from native solver')
        count = len(contacts['shape0'])
        counts.append(count)
        if count > admission['contact_capacity']:
            raise ValueError('Overflowing contact count')
        for name, width in [('shape0', None), ('shape1', None), ('normal', 3), ('point0', 3),
                            ('point1', 3), ('offset0', 3), ('offset1', 3), ('margin0', None), ('margin1', None)]:
            values = np.asarray(contacts[name])
            shape = (count, width) if count and width else (count,)
            if values.shape != shape or not np.isfinite(values).all():
                raise ValueError(f'Malformed contact {name}')
        if not count:
            require_close(forces[index], np.zeros(3), 'force without contact')
            distances.append(0.)
            continue
        s0, s1 = np.asarray(contacts['shape0']), np.asarray(contacts['shape1'])
        if np.any(np.sort(np.stack([s0, s1]), axis=0) != np.array([[0], [1]])):
            raise ValueError('Unexpected contact identity')
        require_float32(contacts['normal'], np.where(s0[:, None] == 0, normal, -normal), 'contact normal')
        separations = []
        for i in range(count):
            points = []
            for side, shape in [('0', s0[i]), ('1', s1[i])]:
                point = np.asarray(contacts['point' + side][i])
                if shape == 1:
                    point = states[index, 1:4] + rotate(states[index, 4:8], point)
                points.append(point)
            separations.append(float(np.dot(points[1] - points[0], contacts['normal'][i])
                                     - contacts['margin0'][i] - contacts['margin1'][i]))
        distances.append(min(0., min(separations)))
        convention = readback['convention']
        if convention == 'wrench_on_shape0':
            f = np.asarray(readback['force'])
            if f.shape != (count, 6):
                raise ValueError('Lost native per-contact wrench')
            total = np.sum(np.where(s0[:, None] == 1, 1, -1) * f[:, :3], axis=0)
        elif convention == 'force_on_body1':
            f = np.asarray(readback['force'])
            b0, b1 = np.asarray(readback['body0']), np.asarray(readback['body1'])
            require_close(b0, np.where(s0 == 1, 0, -1), 'VBD body0')
            require_close(b1, np.where(s1 == 1, 0, -1), 'VBD body1')
            if f.shape != (count, 3):
                raise ValueError('Lost VBD force')
            total = np.sum(np.where(b1[:, None] == 0, 1, -1) * f, axis=0)
        elif convention in ('com_wrench', 'negative_solve_wrench'):
            f = np.asarray(readback['wrench'])
            if f.shape != (6,):
                raise ValueError('Lost native aggregate wrench')
            total = f[:3] * (-1 if convention == 'negative_solve_wrench' else 1)
        else:
            raise ValueError('Unknown native force convention')
        require_close(forces[index], total, 'native force sum', 1e-12)
    if case.get('negative_no_floor', False) and any(counts):
        raise ValueError('Disabled collision generated contacts')
    return dict(states=states, forces=forces, contact_count=np.array(counts),
                contact_distance=np.array(distances), force_times=states[:-1, 0])


def score_campaign(root):
    protocol = json.loads((root / 'manifest.json').read_text())
    validate_protocol(protocol)
    campaign = json.loads((root / 'campaign.json').read_text())
    if (campaign['admission_only'] or campaign['state'] != 'completed'
            or campaign['protocol_sha256'] != file_hash(root / 'manifest.json')):
        raise ValueError('Not a completed, bound physical campaign')
    if campaign['proof_sha256'] != file_hash(root / 'official-proof.json'):
        raise ValueError('Changed official identity proof')
    if campaign['recorder_sha256'] != file_hash(root / 'recorder.py'):
        raise ValueError('Changed recorder')
    if campaign['recorder_sha256'] != protocol['recorder_sha256']:
        raise ValueError('Recorder differs from preregistered source')
    proof = json.loads((root / 'official-proof.json').read_text())
    if (campaign['device'] != 'cpu' or campaign['precision'] != 'float32'
            or campaign['engine_patches'] is not False or proof['source_commit'] != protocol['source_commit']):
        raise ValueError('Unqualified runtime or source')
    for name, version in [('newton', '1.6.1'), ('warp-lang', '1.18.0')]:
        identity = campaign['packages'][name]
        if identity != proof['packages'][name]['identity'] or identity['version'] != version or not identity['record_verified']:
            raise ValueError('Wrong official runtime identity')
    if len(campaign['cases']) != len(protocol['cases']):
        raise ValueError('Incomplete campaign')
    recovery = None
    if 'continuation' in campaign:
        from dexlab.newton_incline_recovery import validate_recovery
        recovery = validate_recovery(root, campaign, protocol)
    results = []
    for case, logged in zip(protocol['cases'], campaign['cases'], strict=True):
        directory = root / case['id']
        meta = json.loads((directory / 'metadata.json').read_text())
        if logged != meta or meta['case'] != case or meta['state_writes_after_initialization'] != 0:
            raise ValueError('Inconsistent case identity or state writes')
        if not {'admission.json', 'steps.jsonl.gz'}.issubset(meta['hashes']):
            raise ValueError('Missing admission or observation binding')
        for name, digest in meta['hashes'].items():
            if Path(name).name != name or file_hash(directory / name) != digest:
                raise ValueError('Changed observation artifact')
        result = dict(case=case['id'], negative=case.get('negative_no_floor', False),
                      valid=False, passed=False)
        try:
            if meta['error'] or meta['completed_steps'] != round(protocol['duration_s'] / case['timestep']):
                raise ValueError(meta['error'] or 'Incomplete physical observations')
            admission = json.loads((directory / 'admission.json').read_text())
            if file_hash(directory / 'admission.json') != protocol['admission_sha256'][case['id']]:
                raise ValueError('Effective model or solver parameters changed after admission')
            validate_admission(protocol, case, admission)
            with gzip.open(directory / 'steps.jsonl.gz', 'rt') as stream:
                rows = [json.loads(line) for line in stream]
            trace = validate_rows(protocol, case, admission, rows)
            result.update(measure_response(protocol, case, trace), valid=True)
            if result['negative']:
                result['negative_rejected'] = not result['passed']
        except (ValueError, KeyError) as error:
            result['error'] = f'{type(error).__name__}: {error}'
            if isinstance(error, ImpulseConsistencyError):
                result['impulse_residual_max_ns'] = error.residual
        results.append(result)
    report = dict(profile=protocol['profile'], results=results,
                  positives_passed=sum(r['passed'] and not r['negative'] for r in results),
                  positives_total=9, reliable_coverage_v1=False)
    if recovery is not None:
        report['continuation'] = recovery
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(score_campaign(args.input), stream, indent=2, allow_nan=False)
        stream.write('\n')
