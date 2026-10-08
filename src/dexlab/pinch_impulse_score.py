"""Engine-free decomposition; diagnostic consistency is not physical validity."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.pinch_run import model_xml
from dexlab.pinch_score import validate_readback, _advance_quaternion


FORCES = ('qfrc_smooth', 'qfrc_constraint', 'qfrc_bias', 'qfrc_passive',
          'qfrc_actuator', 'qfrc_applied')


def require_close(actual, expected, limit, message):
    if not np.allclose(actual, expected, rtol=0, atol=limit):
        raise ValueError(message)


def score_trace(protocol, case, trace):
    h = case['timestep']
    n = round(protocol['duration_s'] / h)
    limits = protocol['diagnostic_limits']
    shapes = dict(states=(n + 1, 18), qacc=(n, 8), mass=(n, 8, 8), commands=(n, 2),
                  external=(n, 3), body_load=(n, 4, 6), force_times=(n,), nefc=(n,), solver_offsets=(n + 1,))
    shapes.update({name: (n, 8) for name in FORCES})
    for name, shape in shapes.items():
        if name not in trace or trace[name].shape != shape or not np.isfinite(trace[name]).all():
            raise ValueError(f'Missing/malformed {name}')
    for name in ('warnings', 'solver_niter'):
        if name not in trace or trace[name].ndim != 2 or trace[name].shape[0] != n or not trace[name].shape[1]:
            raise ValueError(f'Missing/malformed {name}')
        if not np.isfinite(trace[name]).all():
            raise ValueError(f'Nonfinite {name}')
    if np.any(trace['warnings']):
        raise ValueError('Native warning')
    state = trace['states']
    require_close(state[:, 0], np.arange(n + 1) * h, 1e-10, 'State epoch mismatch')
    require_close(trace['force_times'], state[:-1, 0], 1e-10, 'Force epoch mismatch')
    require_close(np.diff(state[:, 1:6], axis=0), h * state[1:, 10:15], 1e-10, 'Position integration mismatch')
    predicted_q = _advance_quaternion(state[:-1, 6:10], state[1:, 15:18], h)
    sign = np.where(np.sum(predicted_q * state[1:, 6:10], axis=1) < 0, -1., 1.)
    require_close(predicted_q * sign[:, None], state[1:, 6:10], 1e-10, 'Quaternion integration mismatch')
    initial = np.zeros(18); initial[6] = 1
    require_close(state[0], initial, 1e-12, 'Initial state mismatch')
    require_close(np.linalg.norm(state[:, 6:10], axis=1), 1, 1e-10, 'Quaternion mismatch')
    normal = case['capacity_ratio'] * protocol['cube_mass_kg'] * protocol['gravity_m_s2'] / (2 * protocol['friction'])
    command = normal * np.minimum(np.arange(n) / round(protocol['ramp_s'] / h), 1)
    require_close(trace['commands'], np.repeat(command[:, None], 2, axis=1), 1e-12, 'Command mismatch')
    onset = round(protocol['preload_s'] / h)
    external = np.zeros((n, 3)); external[onset:, 2] = -protocol['cube_mass_kg'] * protocol['gravity_m_s2']
    require_close(trace['external'], external, 1e-12, 'External load mismatch')
    body_load = np.zeros((n, 4, 6)); body_load[:, 3, :3] = external
    require_close(trace['body_load'], body_load, 1e-12, 'Body load mismatch')
    actuator = np.zeros((n, 8)); actuator[:, :2] = command[:, None]
    require_close(trace['qfrc_actuator'], actuator, 1e-12, 'Actuation mismatch')
    require_close(trace['qfrc_applied'], 0, 1e-12, 'Unexpected generalized applied force')
    require_close(trace['qfrc_passive'], 0, 1e-12, 'Unexpected passive force')
    mass = protocol['cube_mass_kg']; inertia = mass * protocol['side_m']**2 / 6
    diagonal = np.array([protocol['jaw_mass_kg']] * 2 + [mass] * 3 + [inertia] * 3)
    require_close(trace['mass'], np.diag(diagonal), limits['mass_matrix_absolute'], 'Mass matrix mismatch')
    smooth = actuator + trace['qfrc_passive'] + trace['qfrc_applied'] - trace['qfrc_bias']
    smooth[:, 2:5] += external
    require_close(trace['qfrc_smooth'][:, :5], smooth[:, :5], limits['smooth_force_n'], 'Smooth linear force mismatch')
    require_close(trace['qfrc_smooth'][:, 5:], smooth[:, 5:], limits['smooth_torque_n_m'], 'Smooth torque mismatch')
    if np.any(trace['nefc'] < 0) or np.any(trace['nefc'] != np.floor(trace['nefc'])):
        raise ValueError('Invalid constraint count')
    counts = trace['solver_niter']
    if np.any(counts != np.floor(counts)) or np.any(counts < 0) or np.any(counts > protocol['solver_iterations']):
        raise ValueError('Invalid solver iteration count')
    stats = trace.get('solver_stats')
    if stats is None or stats.ndim != 2 or stats.shape[1] != 9 or not np.isfinite(stats).all():
        raise ValueError('Missing/malformed solver statistics')
    offsets = np.r_[0, np.cumsum(counts.sum(axis=1))]
    if not np.array_equal(trace['solver_offsets'], offsets) or offsets[-1] != len(stats):
        raise ValueError('Solver statistics truncated')
    for step in range(n):
        expected = [(island, iteration) for island, count in enumerate(counts[step])
                    for iteration in range(int(count))]
        if not np.array_equal(stats[int(offsets[step]):int(offsets[step + 1]), :2], np.asarray(expected).reshape(-1, 2)):
            raise ValueError('Solver statistic epoch/index mismatch')
    dv = np.diff(state[:, 10:18], axis=0)
    acceleration = trace['qacc']
    integration_velocity = dv - h * acceleration
    require_close(integration_velocity[:, :5], 0, limits['linear_integration_m_s'], 'Linear acceleration integration mismatch')
    require_close(integration_velocity[:, 5:], 0, limits['angular_integration_rad_s'], 'Angular acceleration integration mismatch')
    multiply = lambda v: np.einsum('nij,nj->ni', trace['mass'], v)
    force = trace['qfrc_smooth'] + trace['qfrc_constraint']
    total = multiply(dv) - h * force
    integration = multiply(integration_velocity)
    force_term = h * (multiply(acceleration) - force)
    closure = total - integration - force_term
    require_close(closure[:, :5], 0, limits['linear_closure_n_s'], 'Linear decomposition mismatch')
    require_close(closure[:, 5:], 0, limits['angular_closure_n_m_s'], 'Angular decomposition mismatch')
    metrics = {}
    for name, values in (('total', total), ('integration', integration), ('force', force_term), ('closure', closure)):
        for unit, group in (('n_s', values[:, :5]), ('n_m_s', values[:, 5:])):
            metrics[f'{name}_peak_{unit}'] = float(np.abs(group).max())
            metrics[f'{name}_rms_{unit}'] = float(np.sqrt(np.mean(group**2)))
    metrics.update(max_iterations=int(counts.max()), cap_hit_steps=int(np.any(counts == protocol['solver_iterations'], axis=1).sum()),
                   max_scaled_gradient=float(stats[:, 3].max(initial=0)),
                   loaded_travel_m=float(state[onset, 5] - state[-1, 5]),
                   loaded_peak_speed_m_s=float(np.abs(state[onset:, 14]).max()))
    return dict(status='diagnostic consistent', metrics=metrics,
                scope='Numerical decomposition only; no physical acceptance or accuracy claim')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def score_campaign(root, evidence, baseline):
    protocol = json.loads((root / 'manifest.json').read_text())
    if protocol != json.loads((evidence / 'manifest.json').read_text()):
        raise ValueError('Protocol differs from trusted manifest')
    campaign = json.loads((root / 'campaign.json').read_text())
    for key, path in (('manifest_sha256', root / 'manifest.json'),
                      ('runner_sha256', Path(__file__).with_name('pinch_impulse_run.py')),
                      ('fixture_source_sha256', Path(__file__).with_name('pinch_run.py'))):
        if campaign[key] != digest(path):
            raise ValueError(f'Source/protocol hash mismatch: {key}')
    if campaign['completed_cases'] != 6 or len(protocol['cases']) != 6 or len({c['id'] for c in protocol['cases']}) != 6:
        raise ValueError('Case matrix mismatch')
    if campaign['runtime']['version'] != protocol['version'] or campaign['runtime'].get('record_verified') is not True:
        raise ValueError('Native runtime mismatch')
    rows = []
    for case in protocol['cases']:
        directory = root / case['id']
        meta = json.loads((directory / 'metadata.json').read_text())
        if meta['case'] != case or meta['state_writes_after_initialization'] != 0 or meta['cube_body'] != 3:
            raise ValueError('Case identity/state-write mismatch')
        if meta['force_epoch'] != 'states[i].time; states[i+1] postintegration':
            raise ValueError('Force epoch declaration mismatch')
        fields = ['island', 'iteration', 'improvement', 'gradient', 'lineslope', 'nactive', 'nchange', 'neval', 'nupdate']
        if meta['statistic_fields'] != fields or meta['solver_iteration_capacity'] < protocol['solver_iterations']:
            raise ValueError('Solver statistic schema mismatch')
        spec = dict(protocol, solver_tolerance=case['solver_tolerance'])
        validate_readback(spec, case, meta['readback'])
        if (directory / 'model.xml').read_text() != model_xml(spec, case):
            raise ValueError('Native model mismatch')
        for name, key in (('model.xml', 'xml_sha256'), ('trace.npz', 'trace_sha256')):
            if digest(directory / name) != meta[key]:
                raise ValueError('Artifact hash mismatch')
        with np.load(directory / 'trace.npz', allow_pickle=False) as trace:
            try:
                if trace['solver_niter'].shape[1] != meta['solver_island_capacity']:
                    raise ValueError('Solver island capacity mismatch')
                result = score_trace(protocol, case, trace)
                if case['solver_tolerance'] == 1e-10:
                    ref = protocol['baseline'][str(case['capacity_ratio'])]
                    path = baseline / ref['id'] / 'trace.npz'
                    if digest(path) != ref['trace_sha256']:
                        raise ValueError('Baseline artifact hash mismatch')
                    with np.load(path, allow_pickle=False) as previous:
                        require_close(trace['states'], previous['states'], protocol['diagnostic_limits']['baseline_state_absolute'], 'Baseline trajectory mismatch')
                    result['baseline_matched'] = True
            except ValueError as error:
                result = dict(status='invalid diagnostic', error=str(error))
        timing = {key: meta[key] for key in ('setup_s', 'control_s', 'native_step_s', 'observation_s', 'serialization_s', 'total_case_wall_s')}
        if any(not np.isfinite(v) or v < 0 for v in timing.values()):
            raise ValueError('Invalid timing record')
        rows.append(dict(id=case['id'], **result, trace_sha256=meta['trace_sha256'], timing=timing))
    return dict(protocol=protocol, campaign=campaign, results=rows, scorer_sha256=digest(__file__))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'evidence', 'baseline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = score_campaign(args.input, args.evidence, args.baseline)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
