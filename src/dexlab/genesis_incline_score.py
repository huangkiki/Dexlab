"""Independent Genesis evidence and analytic scoring; imports no physics engine."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import ImpulseConsistencyError, file_hash, measure_response, require_close


ENUMS = {'constraint_solver': {'CG': 0, 'Newton': 1}, 'friction_cone': {'pyramidal': 0, 'elliptic': 1},
         'contact_resolution': {'convex': 0, 'signorini': 1}, 'integrator': {'approximate_implicitfast': 2}}


def initial_state(protocol, case):
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    return np.r_[0, normal * protocol['side_m'] / 2, np.cos(angle / 2), 0, np.sin(angle / 2), 0, np.zeros(6)]


def validate_protocol(protocol):
    cases = protocol['cases']
    positives = [case for case in cases if not case.get('negative_no_floor', False)]
    negatives = [case for case in cases if case.get('negative_no_floor', False)]
    expected = {(regime, angle, friction, timestep) for regime, angle, friction in
                [('static', 15, .5), ('sliding', 35, .5), ('frictionless', 15, 0)]
                for timestep in (.002, .001, .0005)}
    observed = {(c['regime'], c['angle_deg'], c['friction'], c['timestep']) for c in positives}
    if len(positives) != 9 or observed != expected or len(negatives) != 1:
        raise ValueError('Expected nine unique positive conditions and one disabled-support control')
    if (len({c['id'] for c in cases}) != len(cases)
            or any(Path(c['id']).name != c['id'] or c['id'] in ('.', '..', '') for c in cases)
            or any(negatives[0][key] != value for key, value in
                   dict(regime='static', angle_deg=15, friction=.5, timestep=.001).items())):
        raise ValueError('Duplicate/unsafe case identity or incorrect negative control')
    if any(protocol[key] != value for key, value in dict(
            schema_version=1, engine='Genesis', version='1.4.3', quadrants_version='1.3.3',
            threads=1, duration_s=2, score_start_s=.5, mass_kg=.064, side_m=.04,
            density_kg_m3=1000, gravity_m_s2=9.81).items()):
        raise ValueError('Unqualified acquisition protocol')
    options = protocol['genesis']['options']
    if options['contact_resolution'] == 'signorini' and (
            options['constraint_solver'] != 'Newton' or options['friction_cone'] != 'elliptic'):
        raise ValueError('Unsupported Signorini solver/cone combination')
    for key, values in ENUMS.items():
        if options[key] not in values:
            raise ValueError(f'Unqualified {key}')


def validate_runtime(protocol, proof, runtime):
    if proof['source_commit'] != protocol['source_commit']:
        raise ValueError('Genesis source identity differs from the frozen protocol')
    for name, version in (('genesis-world', protocol['version']), ('quadrants', protocol['quadrants_version'])):
        record = proof['packages'][name]
        identity = runtime['packages'][name]
        if (identity != record['identity'] or not identity['record_verified'] or identity['version'] != version
                or protocol['official_wheel_sha256'][name] != record['wheel_sha256']):
            raise ValueError('Unqualified package identity')
    if (runtime['mapped_native'] != proof['packages']['quadrants']['native_files'] or not runtime['mapped_native']
            or runtime['backend'] != 'cpu' or runtime['precision'] != 'float64'
            or runtime['deterministic'] is not True or runtime['seed'] != 0 or runtime['engine_patches'] is not False
            or runtime['compiler_default_fp'] != 'f64'
            or runtime['compiler'] != dict(cpu_max_num_threads=1, num_compile_threads=1, fast_math=True, random_seed=0)):
        raise ValueError('Unqualified compiler, native core or execution settings')


def validate_admission(protocol, case, admission):
    config = protocol['genesis']
    options = admission['options']
    expected = dict(config['options'])
    expected.update({key: ENUMS[key][value] for key, value in config['options'].items() if key in ENUMS})
    expected['dt'] = case['timestep']
    if any(options.get(key) != value for key, value in expected.items()):
        raise ValueError('Native solver/contact/clock settings differ')
    if 'expected_options' in config:
        resolved = dict(config['expected_options'], dt=case['timestep'])
        if case.get('negative_no_floor', False):
            resolved['max_contacts'] = 0  # No eligible pair, but both geoms are retained.
        if options != resolved:
            raise ValueError('Resolved native options changed')
        if admission['static_config'] != config['expected_static_config']:
            raise ValueError('Resolved native kernel configuration changed')
    sim = admission['sim_options']
    if sim['dt'] != case['timestep'] or sim['substeps'] != 1 or sim['requires_grad']:
        raise ValueError('Incorrect native simulation clock')
    require_close(sim['gravity'], [0, 0, -protocol['gravity_m_s2']], 'gravity')
    require_close(admission['state'], initial_state(protocol, case), 'initial state')
    require_close(admission['mass'], [protocol['mass_kg']], 'mass')
    require_close(admission['com'], [[0, 0, 0]], 'COM frame')
    require_close(admission['inertia'], [np.eye(3) * protocol['mass_kg'] * protocol['side_m']**2 / 6], 'inertia')
    if (admission['n_envs'] != 0 or admission['n_dofs'] != 6 or admission['n_geoms'] != 2
            or admission['initial_contact_count'] != 0 or admission['initial_errors'] != [0]):
        raise ValueError('Incorrect single-world model or reset contamination')
    require_close(admission['friction_ratio'], [1, 1], 'friction multiplier')
    geoms = admission['geom_parameters']
    if len(geoms) != 2 or [g['id'] for g in geoms] != [0, 1] or [g['type'] for g in geoms] != [0, 5]:
        raise ValueError('Incorrect plane/cube geometry identities')
    require_close(geoms[0]['data'], [0, 0, 1, 0, 0, 0, 0], 'local plane normal')
    require_close(geoms[1]['data'], [protocol['side_m']] * 3 + [0] * 4, 'cube dimensions')
    require_close(geoms[0]['pos'], [0, 0, 0], 'plane origin')
    require_close(geoms[1]['pos'], admission['state'][1:4], 'cube geometry frame')
    for index, geom in enumerate(geoms):
        require_close(geom['quat'], admission['state'][4:8], 'geometry orientation')
        require_close(geom['friction'], case['friction'], 'authored geom friction')
        require_close(geom['sol_params'], config['sol_params'], 'geom sol_params')
        mask = (1 << index) if case.get('negative_no_floor', False) else 65535
        if geom['contype'] != mask or geom['conaffinity'] != mask:
            raise ValueError('Incorrect collision filter')
    if admission['contact_capacity'] < 1:
        raise ValueError('Missing native contact capacity')


def validate_trace(protocol, case, trace, rows):
    steps = round(protocol['duration_s'] / case['timestep'])
    shapes = dict(states=(steps + 1, 14), forces=(steps, 3), contact_count=(steps,),
                  force_times=(steps,), native_errors=(steps, 1))
    for key, shape in shapes.items():
        values = np.asarray(trace[key])
        if values.shape != shape or not np.isfinite(values).all():
            raise ValueError(f'Truncated, malformed or nonfinite {key}')
    if np.any(trace['native_errors']):
        raise ValueError('Native collision/solver error flags')
    counts = np.asarray(trace['contact_count'])
    if np.any(counts < 0) or np.any(counts % 1):
        raise ValueError('Malformed contact count')
    states, h = np.asarray(trace['states']), case['timestep']
    require_close(states[0], initial_state(protocol, case), 'initial trace state')
    require_close(states[:, 0], np.arange(steps + 1) * h, 'native state clock', 1e-10)
    require_close(trace['force_times'], states[:-1, 0], 'force epoch', 1e-10)
    require_close(np.linalg.norm(states[:, 4:8], axis=1), np.ones(steps + 1), 'quaternion norm', 1e-8)
    require_close(np.diff(states[:, 1:4], axis=0), states[1:, 8:11] * h, 'position/velocity consistency', 1e-10)
    if len(rows) != steps:
        raise ValueError('Missing native contact ledger rows')
    expected_sol = np.array(protocol['genesis']['sol_params'])
    expected_sol[0] = max(expected_sol[0], 2 * h)
    for index, row in enumerate(rows):
        require_close([row['interval_start_s'], row['interval_end_s']], states[index:index + 2, 0], 'contact interval', 1e-10)
        data, count = row['contacts'], int(counts[index])
        for key, width in [('geom_a', None), ('geom_b', None), ('link_a', None), ('link_b', None),
                           ('penetration', None), ('position', 3), ('normal', 3), ('force', 3),
                           ('friction', None), ('sol_params', 7)]:
            value = np.asarray(data[key])
            shape = (count, width) if width and count else (count,)
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError(f'Lost or malformed native contact: {key}')
        if not count:
            require_close(trace['forces'][index], np.zeros(3), 'force without contacts', 1e-10)
            continue
        a, b = np.asarray(data['geom_a']), np.asarray(data['geom_b'])
        if np.any(np.sort(np.stack([a, b]), axis=0) != np.array([[0], [1]])):
            raise ValueError('Unexpected native contact pair')
        require_close(data['link_a'], a, 'contact body A')
        require_close(data['link_b'], b, 'contact body B')
        angle = np.deg2rad(case['angle_deg'])
        normal = np.array([np.sin(angle), 0., np.cos(angle)])
        require_close(data['normal'], np.where(a[:, None] == 1, normal, -normal), 'B-to-A contact normal', 1e-9)
        require_close(data['friction'], np.full(count, max(case['friction'], .01)), 'effective pair friction')
        require_close(data['sol_params'], np.tile(expected_sol, (count, 1)), 'effective pair sol_params')
        forces = np.where(b[:, None] == 1, 1, -1) * np.asarray(data['force'])
        require_close(forces.sum(axis=0), trace['forces'][index], 'contact/net-force ledger', 1e-10)
    if case.get('negative_no_floor', False) and counts.any():
        raise ValueError('Disabled support produced contacts')


def score_record(protocol, case, directory):
    meta = json.loads((directory / 'metadata.json').read_text())
    if (meta['case'] != case or meta['completed_steps'] != round(protocol['duration_s'] / case['timestep'])
            or meta['attempted_steps'] != meta['completed_steps']
            or meta['error'] is not None or meta['state_writes_after_initialization'] != 0):
        raise ValueError('Incomplete case or declared state injection')
    for name in ('admission.json', 'contacts.jsonl.gz', 'trace.npz'):
        if file_hash(directory / name) != meta['hashes'][name]:
            raise ValueError(f'Artifact changed: {name}')
    admission = json.loads((directory / 'admission.json').read_text())
    validate_admission(protocol, case, admission)
    with gzip.open(directory / 'contacts.jsonl.gz', 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    with np.load(directory / 'trace.npz', allow_pickle=False) as data:
        trace = dict(data)
    validate_trace(protocol, case, trace, rows)
    if max(trace['contact_count']) > admission['contact_capacity']:
        raise ValueError('Recorded contacts exceed native capacity')
    states = trace['states']
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    w, vector = states[:, 4:5], states[:, 5:8]
    local_normal = normal + 2 * np.cross(vector, np.cross(vector, normal) - w * normal)
    gaps = states[:, 1:4] @ normal - protocol['side_m'] / 2 * np.sum(np.abs(local_normal), axis=1)
    trace['contact_distance'] = gaps[1:]
    try:
        result = measure_response(protocol, case, trace)
        result['record_valid'] = True
        result['checks']['requested_contact_model'] = case['friction'] >= .01
        result['passed'] = all(result['checks'].values())
        if case['friction'] == 0:
            result['effective_friction_diagnostic'] = measure_response(protocol, dict(case, friction=.01), trace)
    except ImpulseConsistencyError as error:
        result = dict(record_valid=False, passed=False, checks={'impulse_consistency': False},
                      failure=str(error), impulse_residual_max_ns=error.residual, metrics=None)
    result.update(id=case['id'], expected_negative=case.get('negative_no_floor', False),
                  requested_friction=case['friction'], effective_pair_friction=max(case['friction'], .01),
                  contact_loss_fraction=float(np.mean(trace['contact_count'] == 0)),
                  native_error_max=int(np.max(trace['native_errors'])),
                  timing={key: meta[key] for key in ('setup_s', 'native_step_s', 'observation_s', 'total_case_wall_s')})
    if result['expected_negative'] and result['passed']:
        raise ValueError('Independent physics accepted disabled support')
    return result


def score_campaign(root):
    protocol = json.loads((root / 'protocol.json').read_text())
    validate_protocol(protocol)
    campaign = json.loads((root / 'campaign.json').read_text())
    for name, key in [('protocol.json', 'protocol_sha256'), ('official-proof.json', 'official_proof_sha256'),
                      ('runtime.json', 'runtime_sha256')]:
        if file_hash(root / name) != campaign[key]:
            raise ValueError(f'Campaign binding changed: {name}')
    if (campaign['admission_only'] or campaign['error'] is not None
            or campaign['completed_cases'] != [case['id'] for case in protocol['cases']]):
        raise ValueError('Incomplete physical campaign')
    required = {'genesis_incline.py', 'genesis_incline_score.py', 'incline_score.py'}
    if set(campaign['source_hashes']) != required:
        raise ValueError('Missing frozen source')
    for name, digest in campaign['source_hashes'].items():
        if file_hash(root / 'source' / name) != digest:
            raise ValueError('Frozen source changed')
    validate_runtime(protocol, json.loads((root / 'official-proof.json').read_text()),
                     json.loads((root / 'runtime.json').read_text()))
    results = [score_record(protocol, case, root / case['id']) for case in protocol['cases']]
    positives = [r for r in results if not r['expected_negative']]
    return dict(results=results, positive_passed=sum(r['passed'] for r in positives), positive_total=len(positives),
                negative_controls=sum(r['expected_negative'] for r in results),
                scorer_sha256=file_hash(Path(__file__)),
                scope='Native CPU qualification; not hardware calibration or coverage-v1 admission')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(score_campaign(args.input), stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
