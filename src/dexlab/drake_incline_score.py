"""Offline admission, contact ledger and physics checks; no Drake imports."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash, measure_response


def require_close(actual, expected, label, tolerance=1e-12):
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.allclose(
            actual, expected, atol=tolerance, rtol=0):
        raise ValueError(f'Incorrect {label}')


def initial_state(protocol, case):
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    return np.r_[0, normal * (protocol['side_m'] / 2 + protocol.get('initial_clearance_m', 0.)),
                 np.cos(angle / 2), 0, np.sin(angle / 2), 0, np.zeros(6)]


def validate_runtime(protocol, proof, runtime):
    expected_version = protocol['version'] + ' ' + protocol['source_commit']
    if (proof['version'] != protocol['version']
            or proof['native_version_file'] != expected_version
            or proof['wheel']['digests']['sha256'] != protocol['official_wheel_sha256']
            or runtime['native_version_file'] != expected_version
            or runtime['package']['version'] != protocol['version']
            or runtime['package']['code_sha256'] != proof['package_code_sha256']
            or runtime['package']['record_verified'] is not True
            or runtime['precision'] != 'float64' or runtime['engine_patches'] is not False):
        raise ValueError('Unqualified native runtime identity')
    files = runtime['loaded_files']
    if not files or not any(Path(name).name == 'libdrake.so' for name in files):
        raise ValueError('Missing loaded native core identity')
    if any(proof['native_files'].get(name) != digest for name, digest in files.items()):
        raise ValueError('Loaded payload is outside the official qualification')


def validate_admission(protocol, case, admission):
    config = protocol['drake']
    expected = dict(timestep=case['timestep'], solver='kSap', approximation=config['approximation'],
                    contact_model='kHydroelastic', sampled_output=True,
                    near_rigid_threshold=config['near_rigid_threshold'], num_positions=7, num_velocities=6)
    if any(admission.get(key) != value for key, value in expected.items()):
        raise ValueError('Native solver/contact/clock configuration mismatch')
    require_close(admission['state'], initial_state(protocol, case), 'initial state')
    require_close(admission['gravity'], [0, 0, -protocol['gravity_m_s2']], 'gravity')
    require_close(admission['mass'], protocol['mass_kg'], 'mass')
    require_close(admission['com'], np.zeros(3), 'COM frame')
    require_close(admission['inertia'], np.eye(3) * protocol['mass_kg'] * protocol['side_m']**2 / 6, 'inertia')
    require_close(admission['cube_dimensions'], np.full(3, protocol['side_m']), 'cube geometry')
    require_close(admission['cube_pose_in_body'], np.eye(4), 'collision geometry frame')
    angle = np.deg2rad(case['angle_deg'])
    plane = np.array([[np.cos(angle), 0, np.sin(angle), 0], [0, 1, 0, 0],
                      [-np.sin(angle), 0, np.cos(angle), 0], [0, 0, 0, 1]])
    if case.get('negative_no_floor', False):
        if admission['plane_pose_in_world'] is not None or admission['plane_properties'] is not None:
            raise ValueError('Negative control unexpectedly contains a floor')
    else:
        require_close(admission['plane_pose_in_world'], plane, 'incline frame')
    friction = dict(static=case['friction'], dynamic=case['friction'])
    if admission['combined_friction_api'] != friction:
        raise ValueError('Native pair combination differs from declared friction')
    for name in ('cube_properties', 'plane_properties'):
        props = admission[name]
        if props is None:
            continue
        if props['material']['coulomb_friction'] != friction:
            raise ValueError('Native material friction overwritten')
        require_close(props['material']['hunt_crossley_dissipation'], config['dissipation_s_m'], 'dissipation')
    plane_props = admission['plane_properties']
    if plane_props is not None:
        require_close(plane_props['hydroelastic']['hydroelastic_modulus'], config['hydroelastic_modulus_pa'], 'modulus')
        require_close(plane_props['hydroelastic']['slab_thickness'], config['slab_thickness_m'], 'slab thickness')
    require_close(admission['cube_properties']['hydroelastic']['resolution_hint'], config['resolution_hint_m'], 'surface resolution')
    require_close(admission['stiction_tolerance']['authored'], config['stiction_tolerance_m_s'], 'authored stiction tolerance')


def validate_trace(protocol, case, trace, contact_rows):
    steps = round(protocol['duration_s'] / case['timestep'])
    shapes = dict(states=(steps + 1, 14), forces=(steps, 3), generalized_contact_forces=(steps, 6),
                  contact_count=(steps,), force_times=(steps,))
    for name, shape in shapes.items():
        values = np.asarray(trace[name])
        if values.shape != shape or not np.isfinite(values).all():
            raise ValueError(f'Truncated, malformed or nonfinite {name}')
    states = np.asarray(trace['states'])
    h = case['timestep']
    require_close(states[:, 0], np.arange(steps + 1) * h, 'native state clock', 1e-10)
    require_close(trace['force_times'], states[:-1, 0], 'sampled force epoch', 1e-10)
    require_close(states[0], initial_state(protocol, case), 'initial trace state')
    require_close(np.linalg.norm(states[:, 4:8], axis=1), np.ones(steps + 1), 'quaternion norm', 1e-8)
    require_close(np.diff(states[:, 1:4], axis=0), states[1:, 8:11] * h, 'native position/velocity consistency', 1e-10)
    require_close(trace['generalized_contact_forces'][:, 3:], trace['forces'], 'contact/generalized-force ledger', 1e-7)
    if len(contact_rows) != steps:
        raise ValueError('Missing contact ledger rows')
    for index, row in enumerate(contact_rows):
        require_close([row['interval_start_s'], row['interval_end_s']], states[index:index + 2, 0], 'contact interval', 1e-10)
        contacts = row['contacts']
        if len(contacts) != trace['contact_count'][index]:
            raise ValueError('Lost contact patch')
        total = np.zeros(3)
        for contact in contacts:
            for key in ('force_on_cube_world', 'torque_on_cube_at_centroid_world', 'centroid_world'):
                value = np.asarray(contact[key])
                if value.shape != (3,) or not np.isfinite(value).all():
                    raise ValueError('Malformed contact observation')
            if not np.isfinite(contact['area_m2']) or contact['area_m2'] <= 0:
                raise ValueError('Invalid native surface area')
            total += contact['force_on_cube_world']
        require_close(total, trace['forces'][index], 'surface-force sum', 1e-7)
    if case.get('negative_no_floor', False) and np.any(trace['contact_count']):
        raise ValueError('Unexpected support in the no-floor control')


def score_record(protocol, case, directory):
    meta = json.loads((directory / 'metadata.json').read_text())
    steps = round(protocol['duration_s'] / case['timestep'])
    if meta['case'] != case or meta['completed_steps'] != steps or meta['error'] is not None:
        raise ValueError('Incomplete native case')
    if meta['state_writes_after_initialization'] != 0:
        raise ValueError('Declared post-initialization state injection')
    for name in ('admission.json', 'trace.npz', 'contacts.jsonl.gz'):
        if file_hash(directory / name) != meta['hashes'][name]:
            raise ValueError(f'Artifact changed: {name}')
    validate_admission(protocol, case, json.loads((directory / 'admission.json').read_text()))
    with gzip.open(directory / 'contacts.jsonl.gz', 'rt') as stream:
        contact_rows = [json.loads(line) for line in stream]
    with np.load(directory / 'trace.npz', allow_pickle=False) as data:
        trace = dict(data)
    validate_trace(protocol, case, trace, contact_rows)
    states = trace['states']
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    w, vector = states[:, 4:5], states[:, 5:8]
    local_normal = normal + 2 * np.cross(vector, np.cross(vector, normal) - w * normal)
    gaps = states[:, 1:4] @ normal - protocol['side_m'] / 2 * np.sum(np.abs(local_normal), axis=1)
    # Same independent physical limits as the original protocol. Clearance is
    # reconstructed from native end poses, not called native quadrature depth.
    trace['contact_distance'] = gaps[1:]
    result = measure_response(protocol, case, trace)
    result.update(id=case['id'], record_valid=True,
                  expected_negative=case.get('negative_no_floor', False),
                  contact_loss_fraction=float(np.mean(trace['contact_count'] == 0)),
                  timing={key: meta[key] for key in ('setup_s', 'native_step_s', 'observation_s', 'total_case_wall_s')})
    if result['expected_negative'] and result['passed']:
        raise ValueError('Independent physics falsely accepted the no-floor control')
    return result


def score_campaign(root):
    protocol = json.loads((root / 'protocol.json').read_text())
    campaign = json.loads((root / 'campaign.json').read_text())
    for name, key in [('protocol.json', 'protocol_sha256'), ('official-proof.json', 'official_proof_sha256'),
                      ('runtime.json', 'runtime_sha256')]:
        if file_hash(root / name) != campaign[key]:
            raise ValueError(f'Campaign binding changed: {name}')
    cases = protocol['cases']
    if len({c['id'] for c in cases}) != len(cases) or campaign['completed_cases'] != len(cases):
        raise ValueError('Missing or duplicate cases')
    if campaign['admission_only'] or campaign['error'] is not None:
        raise ValueError('No complete physical campaign')
    for name, digest in campaign['source_hashes'].items():
        if Path(name).name != name or file_hash(root / 'source' / name) != digest:
            raise ValueError('Frozen source archive changed')
    validate_runtime(protocol, json.loads((root / 'official-proof.json').read_text()),
                     json.loads((root / 'runtime.json').read_text()))
    results = [score_record(protocol, case, root / case['id']) for case in cases]
    positives = [r for r in results if not r['expected_negative']]
    return dict(results=results, positive_passed=sum(r['passed'] for r in positives),
                positive_total=len(positives), negative_controls=sum(r['expected_negative'] for r in results),
                scorer_sha256=file_hash(Path(__file__)),
                scope='Initial native qualification; no hardware calibration, full-engine ranking or coverage-v1 admission')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = score_campaign(args.input)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
