"""Analytical checks over measured free-box traces; no physics engine imports."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


class ImpulseConsistencyError(ValueError):
    """Observed state and force disagree; retain the case as invalid evidence."""
    def __init__(self, residual):
        super().__init__('State/force impulse inconsistency or possible state injection')
        self.residual = residual


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
        raise ImpulseConsistencyError(impulse_error)
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


def require_close(actual, expected, label, tolerance=1e-12):
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.shape != expected.shape or not np.isfinite(actual).all() or not np.allclose(
            actual, expected, atol=tolerance, rtol=0):
        raise ValueError(f'Incorrect {label}')


def validate_admission(protocol, case, readback):
    """Check native geometry and frame readbacks without importing MuJoCo."""
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    quat = [np.cos(angle / 2), 0., np.sin(angle / 2), 0.]
    rotation = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0],
                         [-np.sin(angle), 0, np.cos(angle)]]).ravel()
    half = protocol['side_m'] / 2
    expected = dict(state=np.r_[0, half * normal, quat, np.zeros(6)],
                    body_ipos=np.zeros((2, 3)), body_iquat=[[1, 0, 0, 0]] * 2,
                    body_gravcomp=[0, 0], geom_type=[0, 6], geom_bodyid=[0, 1],
                    geom_size=[[2, 2, .1], [half] * 3], geom_pos=np.zeros((2, 3)),
                    geom_quat=[quat, [1, 0, 0, 0]], geom_xpos=[np.zeros(3), half * normal],
                    geom_xmat=[rotation, rotation], geom_priority=[0, 0], geom_solmix=[1, 1],
                    geom_margin=[0, 0], geom_gap=[0, 0], dof_damping=np.zeros(6),
                    dof_armature=np.zeros(6), dof_frictionloss=np.zeros(6))
    mask = [0, 1] if case.get('negative_no_floor', False) else [1, 1]
    expected.update(geom_contype=mask, geom_conaffinity=mask)
    for name, value in expected.items():
        require_close(readback[name], value, name)
    for name, value in protocol['native_options'].items():
        require_close(readback[name], value, name)


def export_precision(readback, exported):
    """Report observed export loss; the campaign integrates the original model."""
    differences = {}
    if set(readback) != set(exported):
        raise ValueError('Incomplete compiled export readback')
    for name in readback:
        before, after = np.asarray(readback[name]), np.asarray(exported[name])
        if before.shape != after.shape or not np.isfinite(after).all():
            raise ValueError('Malformed compiled export readback')
        error = float(np.max(np.abs(after - before))) if before.size else 0.
        if error > 1e-12:
            differences[name] = error
    return dict(within_tolerance=not differences, absolute_tolerance=1e-12, absolute_max_errors=differences,
                integrated_asset='model.xml', compiled_xml_used_for_physics=False)


def validate_contacts(protocol, case, trace, contacts):
    """Reconstruct every per-contact force and compare independent native channels."""
    # NpzFile lazily decompresses on every access; materialize each channel once.
    trace, contacts = dict(trace), dict(contacts)
    steps = round(protocol['duration_s'] / case['timestep'])
    offsets = np.asarray(contacts['offsets'])
    if (offsets.shape != (steps + 1,) or not np.isfinite(offsets).all()
            or np.any(offsets % 1) or offsets[0] != 0 or np.any(np.diff(offsets) < 0)):
        raise ValueError('Malformed contact offsets')
    offsets = offsets.astype(int)
    require_close(np.diff(offsets), trace['contact_count'], 'per-step contact count', 0.)
    count = int(offsets[-1])
    widths = dict(geom=2, frame=9, pos=3, force_local=6, friction=5, solref=2, solimp=5)
    for name in (*widths, 'distance'):
        values = np.asarray(contacts[name])
        shape = (count, widths[name]) if name in widths else (count,)
        if values.shape != shape or not np.isfinite(values).all():
            raise ValueError(f'Lost or nonfinite contact {name}')
    geom = np.asarray(contacts['geom'])
    if not np.all(np.sort(geom, axis=1) == [0, 1]):
        raise ValueError('Unexpected native contact pair')
    frames = contacts['frame'].reshape((-1, 3, 3))
    require_close(frames @ frames.transpose(0, 2, 1), np.tile(np.eye(3), (count, 1, 1)), 'contact frame', 1e-10)
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    signs = np.where(geom[:, 1] == 1, 1., -1.)
    require_close(signs[:, None] * frames[:, 0], np.tile(normal, (count, 1)), 'incline contact normal', 1e-10)
    require_close(contacts['friction'][:, :2], np.full((count, 2), case['friction']), 'contact friction', 1e-5)
    require_close(contacts['solref'], np.tile(protocol['solref'], (count, 1)), 'effective solref')
    d = case['impedance']
    require_close(contacts['solimp'], np.tile([d, d, .001, .5, 2], (count, 1)), 'effective solimp')
    forces = signs[:, None] * np.einsum('nji,nj->ni', frames, contacts['force_local'][:, :3])
    contact_torques = signs[:, None] * np.einsum('nji,nj->ni', frames, contacts['force_local'][:, 3:])
    step_ids = np.repeat(np.arange(steps), np.diff(offsets))
    sums, torques = np.zeros((steps, 3)), np.zeros((steps, 3))
    lever = contacts['pos'] - trace['states'][step_ids, 1:4]
    np.add.at(sums, step_ids, forces)
    np.add.at(torques, step_ids, np.cross(lever, forces) + contact_torques)
    distances = np.zeros(steps)
    np.minimum.at(distances, step_ids, contacts['distance'])
    require_close(trace['contact_distance'], distances, 'contact distance minimum')
    require_close(sums, trace['forces'], 'per-contact force sum', 1e-10)
    generalized = np.asarray(trace['generalized_contact_forces'])
    accelerations = np.asarray(trace['accelerations'])
    if (generalized.shape != (steps, 6) or accelerations.shape != (steps, 6)
            or not np.isfinite(generalized).all() or not np.isfinite(accelerations).all()):
        raise ValueError('Malformed independent native force/acceleration channel')
    require_close(generalized[:, :3], trace['forces'], 'generalized force sum', 1e-10)
    w, vector = trace['states'][:-1, 4:5], trace['states'][:-1, 5:8]
    torque_local = torques + 2 * np.cross(vector, np.cross(vector, torques) - w * torques)
    require_close(generalized[:, 3:], torque_local, 'generalized torque frame', 1e-10)
    require_close(np.diff(trace['states'][:, 8:11], axis=0),
                  accelerations[:, :3] * case['timestep'], 'native acceleration epoch', 1e-10)
    iterations = np.asarray(trace['solver_iterations'])
    if iterations.shape != (steps,) or not np.isfinite(iterations).all() or np.any(iterations % 1) or np.any(iterations < 0):
        raise ValueError('Malformed observed solver iterations')
    if case.get('negative_no_floor', False) and count:
        raise ValueError('Disabled support produced native contacts')


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
    prospective = protocol.get('schema_version') == 2
    if prospective:
        if campaign['admission_only'] or campaign['error'] is not None:
            raise ValueError('Incomplete physical campaign')
        if file_hash(root / 'official-proof.json') != campaign['proof_sha256']:
            raise ValueError('Official proof binding mismatch')
        proof = json.loads((root / 'official-proof.json').read_text())
        runtime = campaign['runtime']
        if (runtime['native_version'] != protocol['version'] or proof['version'] != protocol['version']
                or runtime['code_sha256'] != proof['wheel']['package_code_sha256']
                or runtime['native_core_sha256'] != proof['native_core_sha256']
                or runtime['precision'] != 'float64' or runtime['device'] != 'cpu'
                or runtime['engine_patches'] is not False):
            raise ValueError('Unqualified native runtime')
        for name, digest in campaign['source_hashes'].items():
            if Path(name).name != name or file_hash(root / 'source' / name) != digest:
                raise ValueError('Frozen source changed')
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
                    'impratio': case.get('impratio', 1.), 'integrator': 0,
                    'solver': {'PGS': 0, 'CG': 1, 'Newton': 2}[protocol.get('solver', 'Newton')],
                    'cone': {'pyramidal': 0, 'elliptic': 1}[protocol.get('cone', 'elliptic')]}
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
        export = None
        if prospective:
            if meta['completed_steps'] != round(protocol['duration_s'] / case['timestep']) or meta['error'] is not None:
                raise ValueError('Interrupted or incomplete native case')
            for name in ('admission.json', 'compiled.xml', 'export-readback.json', 'contacts.npz'):
                if file_hash(directory / name) != meta['hashes'][name]:
                    raise ValueError('Prospective artifact changed')
            if readback != json.loads((directory / 'admission.json').read_text()):
                raise ValueError('Conflicting admission readbacks')
            validate_admission(protocol, case, readback)
            export = export_precision(readback, json.loads((directory / 'export-readback.json').read_text()))
        with np.load(directory / 'trace.npz', allow_pickle=False) as trace:
            if prospective:
                with np.load(directory / 'contacts.npz', allow_pickle=False) as contacts:
                    validate_contacts(protocol, case, trace, contacts)
            try:
                result = score(protocol, case, trace)
            except ImpulseConsistencyError as error:
                if not prospective:
                    raise  # Historical reader behavior stays fail-closed.
                result = dict(record_valid=False, passed=False, checks={'impulse_consistency': False},
                              failure=str(error), impulse_residual_max_ns=error.residual,
                              metrics=None)
            active = trace['contact_count'] > 0
            result['contact_loss_fraction'] = float(np.mean(~active))
            result['native_friction_range'] = ([float(np.min(trace['friction'][active])), float(np.max(trace['friction'][active]))] if np.any(active) else None)
            if prospective:
                result.setdefault('record_valid', True)
                result.update(expected_negative=case.get('negative_no_floor', False),
                              compiled_export=export, solver_iterations_max=int(np.max(trace['solver_iterations'])))
                if result['expected_negative'] and result['passed']:
                    raise ValueError('Scoring accepted disabled support')
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
