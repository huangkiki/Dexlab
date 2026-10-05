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
