"""Paired normal-damping diagnosis; no material fit or physical threshold change."""
from copy import deepcopy

import numpy as np

from dexlab.contact_load import LIMITS, LoadCase

DAMPING = 'normal_viscous_damping_coefficient'
STEPS = (.0005, .00025, .000125)
PARAMETERS = {
    'penalty_coefficient': 12500000.0,
    'penalty_threshold_default': 1e-6,
    'penalty_smoothing_half_distance': 5e-7,
}


def validate_plan(plan):
    """Reject missing/reordered pairs and changes beyond the declared ablation."""
    jobs = plan['jobs']
    expected = [(dt, damping) for i, dt in enumerate(STEPS)
                for damping in ((0., 10.) if i % 2 == 0 else (10., 0.))]
    if len(jobs) != 6 or len({job['id'] for job in jobs}) != 6:
        raise ValueError('Require six unique paired runs')
    if plan.get('protocol') != 'normal-load' or plan.get('target') != LIMITS:
        raise ValueError('Changed physical protocol or thresholds')
    for job, (dt, damping) in zip(jobs, expected, strict=True):
        case = dict(job['case'])
        case.pop('name', None)
        if case != dict(mass=.2, half_size=.02, gravity=9.81, timestep=dt,
                        settle=0., duration=.8, max_force=40.):
            raise ValueError('Changed physical case or pair order')
        if (job['engine'] != 'superdex'
                or job['normal_parameters'] != PARAMETERS | {DAMPING: damping}):
            raise ValueError('Changed native parameters outside the frozen ablation')
    return True


def pair_native_matches(left, right):
    """Compare complete recorded actor/solver/native metadata, not hidden laws."""
    def normalize(native, expected):
        result = deepcopy(native)
        containers = [result['normal_parameters_readback'], result['contact'],
                      result['actor_contact_parameters']['box'],
                      result['actor_contact_parameters']['plane']]
        for values in containers:
            if values.pop(DAMPING) != expected:
                raise ValueError('Native damping differs from its pair member')
        return result

    # Caller supplies zero-damping first, independently of execution order.
    return normalize(left, 0.) == normalize(right, 10.)


def force_windows(case, data):
    """Count solved-step vertical tensile force separately for load and unload.

    Event boundaries denote entire step intervals, not substep contact times.
    This diagnostic requires the archive's separate force-ledger/momentum checks.
    """
    n = case.steps
    shapes = {'time': (n+1,), 'contact_force': (n, 3), 'downward_load': (n,)}
    if any(key not in data or np.shape(data[key]) != shape
           or not np.isfinite(data[key]).all() for key, shape in shapes.items()):
        raise ValueError('Incomplete or nonfinite force/time/load arrays')
    time = np.asarray(data['time'])
    if not np.allclose(time, np.arange(n+1)*case.timestep, atol=1e-10, rtol=0):
        raise ValueError('Changed solved-step clock')
    if not np.array_equal(data['downward_load'], case.loads()):
        raise ValueError('Changed loading schedule')
    force = np.asarray(data['contact_force'])[:, 2]
    rows = {}
    for name, mask in [('loading', data['downward_load'] > 0),
                       ('unloading', data['downward_load'] < 0)]:
        negative = np.flatnonzero(mask & (force < -LIMITS['normal_tension_n']))
        rows[name] = {
            'minimum_force_n': float(force[mask].min()),
            'negative_steps': len(negative),
            'negative_duration_s': float(len(negative)*case.timestep),
            'negative_step_intervals_s': [[float(time[i]), float(time[i+1])]
                                          for i in negative],
        }
    return rows


def point_force_windows(case, data, contacts):
    """Diagnose solved-step point forces on the qualified horizontal plane.

    This adds observations, not a replacement historical acceptance verdict.
    Point samples have no persistent IDs; counts are not unique contacts.
    """
    force_windows(case, data)  # Preserve existing clock/load/array qualification.
    if not isinstance(contacts, list) or len(contacts) != case.steps:
        raise ValueError('Incomplete point-contact coverage')
    per_step = []
    for index, points in enumerate(contacts):
        if not isinstance(points, list):
            raise ValueError('Contact step must contain a point list')
        forces = []
        for point in points:
            vectors = {}
            for key in ('force_on_box', 'normal_native', 'point_b'):
                value = np.asarray(point.get(key), dtype=float)
                if value.shape != (3,) or not np.isfinite(value).all():
                    raise ValueError('Missing or nonfinite point observation')
                vectors[key] = value
            if (not np.allclose(vectors['normal_native'], [0, 0, 1], rtol=0, atol=1e-12)
                    or abs(vectors['point_b'][2]) > 1e-12):
                raise ValueError('Point is outside the qualified horizontal-plane frame')
            forces.append(vectors['force_on_box'])
        force = np.asarray(forces).reshape(-1, 3)
        if not np.allclose(force.sum(axis=0), data['contact_force'][index],
                           rtol=1e-6, atol=1e-7):
            raise ValueError('Point-force ledger differs from the archived total')
        per_step.append(force[:, 2])
    result = {}
    tolerance = LIMITS['normal_tension_n']
    for name, mask in (('loading', data['downward_load'] > 0),
                       ('unloading', data['downward_load'] < 0)):
        indices = np.flatnonzero(mask)
        observed = np.concatenate([per_step[i] for i in indices])
        negative_steps = [int(i) for i in indices if np.any(per_step[i] < -tolerance)]
        hidden = [i for i in negative_steps if data['contact_force'][i, 2] >= -tolerance]
        result[name] = {
            'point_samples': int(observed.size),
            'minimum_point_force_n': float(observed.min()) if observed.size else None,
            'negative_point_samples': int(np.count_nonzero(observed < -tolerance)),
            'steps_with_negative_point': len(negative_steps),
            'negative_step_duration_s': len(negative_steps)*case.timestep,
            'negative_step_intervals_s': [[float(data['time'][i]), float(data['time'][i+1])]
                                          for i in negative_steps],
            'hidden_by_aggregate_steps': hidden,
        }
    return result
