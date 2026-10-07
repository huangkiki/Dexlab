"""Independent scalar contact predictions; no physics-engine dependency.

Only isolated collinear, frictionless, undamped spheres are represented.
Agreement with this discrete model is not validation of a real material.
"""
import numpy as np


LIMITS = dict(position_m=1e-10, velocity_m_s=1e-9, force_n=1e-6)


def _inputs(x, velocity, masses, radius, stiffness):
    x, velocity, masses = (np.asarray(a, dtype=float) for a in (x, velocity, masses))
    if any(a.shape != (2,) or not np.isfinite(a).all() for a in (x, velocity, masses)):
        raise ValueError('Require finite two-body vectors')
    if (np.any(masses <= 0) or not np.isfinite([radius, stiffness]).all()
            or radius <= 0 or stiffness <= 0 or x[1] <= x[0]):
        raise ValueError('Unsupported mass, geometry or stiffness')
    return x, velocity, masses


def step(x, velocity, masses, radius, stiffness, timestep):
    """Velocity-first Euler update with unilateral force at the input epoch."""
    x, velocity, masses = _inputs(x, velocity, masses, radius, stiffness)
    if not np.isfinite(timestep) or timestep <= 0:
        raise ValueError('Require a positive finite timestep')
    compression = max(0., 2*radius - (x[1]-x[0]))
    reduced_mass = 1 / np.sum(1/masses)
    force = reduced_mass * stiffness * compression * np.array([-1., 1.])
    next_velocity = velocity + timestep * force/masses
    return x + timestep * next_velocity, next_velocity, force


def rollout(x, velocity, masses, radius, stiffness, timestep, steps):
    """Open-loop prediction initialized once; never reads measured later states."""
    if not isinstance(steps, int) or not 1 <= steps <= 100000:
        raise ValueError('Require a bounded positive step count')
    x, velocity, masses = _inputs(x, velocity, masses, radius, stiffness)
    positions = np.empty((steps+1, 2)); velocities = np.empty_like(positions)
    forces = np.empty((steps, 2))
    positions[0], velocities[0] = x, velocity
    for i in range(steps):
        positions[i+1], velocities[i+1], forces[i] = step(
            positions[i], velocities[i], masses, radius, stiffness, timestep)
    return positions, velocities, forces


def continuous(x, velocity, masses, radius, stiffness, times):
    """Continuous undamped unilateral spring reference, one approaching impact."""
    x, velocity, masses = _inputs(x, velocity, masses, radius, stiffness)
    times = np.asarray(times, dtype=float)
    gap = x[1]-x[0]-2*radius
    closing = velocity[0]-velocity[1]
    if (gap < 0 or closing <= 0 or times.ndim != 1 or not np.isfinite(times).all()
            or np.any(times < 0)):
        raise ValueError('Require separated approaching initial data and nonnegative times')
    omega = np.sqrt(stiffness)
    arrival, duration = gap/closing, np.pi/omega
    tau = times-arrival
    active = (tau >= 0) & (tau <= duration)
    separation = np.where(tau < 0, 2*radius-closing*tau,
                          2*radius+closing*(tau-duration))
    relative_velocity = np.where(tau < 0, -closing, closing)
    separation[active] = 2*radius-closing/omega*np.sin(omega*tau[active])
    relative_velocity[active] = -closing*np.cos(omega*tau[active])
    total = masses.sum(); reduced = 1/np.sum(1/masses)
    center_velocity = np.dot(masses, velocity)/total
    center = np.dot(masses, x)/total + center_velocity*times
    weights = np.array([-masses[1], masses[0]])/total
    positions = center[:, None] + separation[:, None]*weights
    velocities = center_velocity + relative_velocity[:, None]*weights
    magnitude = np.zeros_like(times)
    magnitude[active] = reduced*omega*closing*np.sin(omega*tau[active])
    return positions, velocities, magnitude[:, None]*np.array([-1., 1.])


def residuals(observed, predicted):
    """Absolute maxima, with fail-closed shape and finite-value checks."""
    errors = {}
    if len(observed) != 3 or len(predicted) != 3:
        raise ValueError('Require positions, velocities and forces')
    for name, actual, expected in zip(LIMITS, observed, predicted):
        actual, expected = np.asarray(actual), np.asarray(expected)
        if (actual.shape != expected.shape or actual.size == 0
                or not np.isfinite(actual).all() or not np.isfinite(expected).all()):
            raise ValueError('Malformed or nonfinite prediction arrays')
        errors[name] = float(np.max(np.abs(actual-expected)))
    return dict(errors=errors, passed=all(errors[k] <= limit for k, limit in LIMITS.items()))


def audit_trace(protocol, case, trace):
    """Compare both autonomous prediction and measured-input local updates."""
    from dexlab.impact_score import score
    historical = score(protocol, case, trace)
    states = np.asarray(trace['states'])
    if (not np.allclose(states[:, :, 1:3], 0, atol=1e-12, rtol=0)
            or not np.allclose(states[:, :, 8:13], 0, atol=1e-12, rtol=0)
            or not np.allclose(states[:, :, 3:7], [1., 0., 0., 0.], atol=1e-12, rtol=0)):
        raise ValueError('Unsupported noncentral motion or rotation')
    x = case.get('initial_x_m', protocol['initial_x_m'])
    velocity = case['initial_vx_m_s']
    masses, radius = case['masses_kg'], protocol['radius_m']
    stiffness = case.get('stiffness_s2', protocol['stiffness_s2'])
    h = case['timestep']; steps = len(states)-1
    observed = (states[:, :, 0], states[:, :, 7], np.asarray(trace['forces'])[:, :, 0])
    predicted = rollout(x, velocity, masses, radius, stiffness, h, steps)
    local = [step(states[i, :, 0], states[i, :, 7], masses, radius, stiffness, h)
             for i in range(steps)]
    local = tuple(np.asarray(values) for values in zip(*local))
    local_observed = (observed[0][1:], observed[1][1:], observed[2])
    reference = continuous(x, velocity, masses, radius, stiffness, trace['times'])
    continuous_errors = residuals(observed, (reference[0], reference[1], reference[2][:-1]))['errors']
    compression = np.maximum(0., 2*radius-(observed[0][:, 1]-observed[0][:, 0]))
    reduced = 1/np.sum(1/np.asarray(masses))
    energy = .5*np.sum(np.asarray(masses)*observed[1]**2, axis=1)+.5*reduced*stiffness*compression**2
    return dict(id=case['id'], stiffness_s2=stiffness, timestep_s=h,
                speed_m_s=velocity[0]-velocity[1], arrival_phase=case.get('arrival_phase', 0.),
                z=stiffness*h*h, full_rollout=residuals(observed, predicted),
                one_step=residuals(local_observed, local), continuous_errors=continuous_errors,
                continuous_contact_duration_s=float(np.pi/np.sqrt(stiffness)),
                sampled_contact_duration_s=float(np.count_nonzero(trace['contact_count'])*h),
                max_total_energy_deviation_j=float(np.max(np.abs(energy-energy[0]))),
                historical_final_state_passed=historical['passed'])


def bind_records(campaign, published, selected_ids):
    """Published hashes are independent of mutable local metadata."""
    actual = {r['id']: r for r in campaign['results']}
    expected = {r['id']: r for r in published['results']}
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError('Duplicate selected records')
    for name in selected_ids:
        if name not in actual or name not in expected:
            raise ValueError('Missing published record')
        for key in ('trace_sha256', 'xml_sha256'):
            if actual[name][key] != expected[name][key]:
                raise ValueError('Published artifact binding mismatch')


def audit(roots, evidence):
    import json
    import time
    from pathlib import Path
    from dexlab.impact_score import score_campaign, file_hash
    from dexlab.impact_stiffness import validate_pair as validate_stiffness
    from dexlab.impact_phase import validate_pair as validate_phase
    start = time.perf_counter()
    campaigns = [score_campaign(root) for root in roots]
    selected = validate_stiffness(campaigns[0], campaigns[1])
    validate_phase(campaigns[1], campaigns[2])
    reports = [json.loads((evidence/name/'results.json').read_text())
               for name in ('impact-stiffness', 'impact-phase')]
    expected_campaigns = [reports[0]['baseline_campaign'], reports[0]['new_campaign'],
                          reports[1]['new_campaign']]
    if any(c['campaign'] != expected for c, expected in zip(campaigns, expected_campaigns)):
        raise ValueError('Published campaign identity mismatch')
    groups = [[c['id'] for c, _ in selected],
              [c['id'] for c in campaigns[1]['protocol']['cases']],
              [c['id'] for c in campaigns[2]['protocol']['cases']]]
    rows = []; seen = set()
    for root, campaign, ids, published in zip(roots, campaigns, groups, [reports[0], reports[0], reports[1]]):
        bind_records(campaign, published, ids)
        p = campaign['protocol']
        if p['version'] != '3.15.0' or p['impedance'] != .9:
            raise ValueError('Unsupported runtime or impedance')
        cases = {c['id']: c for c in p['cases']}
        for name in ids:
            if name in seen:
                raise ValueError('Repeated case')
            seen.add(name)
            with np.load(root/name/'trace.npz', allow_pickle=False) as trace:
                row = audit_trace(p, cases[name], trace)
            binding = next(r for r in published['results'] if r['id'] == name)
            row.update(trace_sha256=binding['trace_sha256'], xml_sha256=binding['xml_sha256'])
            rows.append(row)
    if len(rows) != 54:
        raise ValueError('Require all 54 records')
    return dict(results=rows, cases=54, new_native_runs=0, limits=LIMITS,
                full_rollout_passes=sum(r['full_rollout']['passed'] for r in rows),
                one_step_passes=sum(r['one_step']['passed'] for r in rows),
                campaigns=[c['campaign'] for c in campaigns],
                scorer_sha256=file_hash(Path(__file__)), scoring_wall_s=time.perf_counter()-start)


def main():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--stiffness', type=Path, required=True)
    parser.add_argument('--phase', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit([args.baseline, args.stiffness, args.phase], args.evidence)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
