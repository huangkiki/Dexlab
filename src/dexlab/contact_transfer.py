"""Independent checks for the declared prospective cube/plane transfer cohort.

Input geometry checks do not observe SuperDex's internal cooked representation.
Numerical comparison tolerances below cover serialized floating-point coordinates,
not contact penetration or material accuracy.
"""
from collections import Counter
import hashlib

import numpy as np

PROFILES = ('mujoco-imp09-500us', 'mujoco-imp0001-500us', 'superdex-load-damping-500us')
SEEDS = tuple(range(2026100500, 2026100510))
# Frozen development mappings; seed-specific mass/area compensation is forbidden.
PROFILE_PARAMETERS = {
    'mujoco-imp09-500us': {'solref': [-2500, -5], 'solimp': [.9, .9, .001, .5, 2]},
    'mujoco-imp0001-500us': {'solref': [-24975, -49.95], 'solimp': [.001, .001, .001, .5, 2]},
    'superdex-load-damping-500us': {
        'penalty_coefficient': 12500000.0, 'penalty_threshold_default': 1e-6,
        'penalty_smoothing_half_distance': 5e-7, 'normal_viscous_damping_coefficient': 10.0,
    },
}


def sampled_case(seed):
    raw = hashlib.sha256(str(seed).encode('ascii')).digest()
    u = int.from_bytes(raw[:8], 'big') / 2**64
    v = int.from_bytes(raw[8:16], 'big') / 2**64
    return round(.12 + .16*u, 6), round(.015 + .010*v, 6)


def validate_plan(plan):
    jobs = plan['jobs']
    if len(jobs) != 30 or len({j['id'] for j in jobs}) != 30:
        raise ValueError('Require all 30 unique paired jobs')
    expected = [(seed, profile) for i, seed in enumerate(SEEDS)
                for profile in PROFILES[i % 3:] + PROFILES[:i % 3]]
    if [(j['seed'], j['profile_id']) for j in jobs] != expected:
        raise ValueError('Changed cohort, missing pair or reordered jobs')
    for job in jobs:
        profile = job['profile_id']
        case = job['case']
        mass, half_size = sampled_case(job['seed'])
        if (case['mass'], case['half_size']) != (mass, half_size):
            raise ValueError('Case differs from declared sampling')
        if job['engine'] != profile.split('-')[0]:
            raise ValueError('Profile assigned to wrong engine')
        if (case['gravity'], case['timestep'], case['settle'], case['duration'], case['max_force']) != (9.81, .0005, 0, .8, 40):
            raise ValueError('Changed fixed protocol settings')
        if job['normal_parameters'] != PROFILE_PARAMETERS[profile]:
            raise ValueError('Native profile retuned within transfer cohort')
    return True


def initial_state_matches(case, time, pose, velocity):
    """Check the actually recorded initial state, with quaternion sign symmetry."""
    pose = np.asarray(pose, dtype=float)
    velocity = np.asarray(velocity, dtype=float)
    if pose.shape != (7,) or velocity.shape != (6,):
        return False
    if not np.isfinite(np.r_[time, pose, velocity]).all():
        return False
    return bool(
        time == 0
        and np.allclose(pose[:3], [0, 0, case['half_size']], rtol=0, atol=1e-12)
        and np.allclose(np.abs(pose[3:]), [1, 0, 0, 0], rtol=0, atol=1e-12)
        and np.allclose(velocity, 0, rtol=0, atol=1e-12)
    )


def box_mesh_matches(vertices, faces, half_size):
    """Validate a closed outward-oriented 8-corner box input, not cooked geometry."""
    vertices, faces = np.asarray(vertices), np.asarray(faces)
    if (vertices.shape != (8, 3) or faces.shape != (12, 3)
            or not np.issubdtype(faces.dtype, np.integer)
            or not np.isfinite(vertices).all() or not np.isfinite(half_size)
            or half_size <= 0 or faces.min() < 0 or faces.max() >= 8):
        return False
    if len(np.unique(vertices, axis=0)) != 8 or not np.allclose(np.abs(vertices), half_size, rtol=0, atol=1e-12):
        return False
    edges = Counter()
    volume = 0.0
    for face in faces:
        if len(set(face.tolist())) != 3:
            return False
        a, b, c = vertices[face]
        normal = np.cross(b-a, c-a)
        # Each triangle must lie on one cube face and point away from the COM.
        if not np.any((a == b) & (b == c)) or np.dot(normal, (a+b+c)/3) <= 0:
            return False
        volume += np.dot(a, np.cross(b, c)) / 6
        for u, v in zip(face, np.roll(face, -1)):
            edges[(int(u), int(v))] += 1
    if any(count != 1 or edges[(v, u)] != 1 for (u, v), count in edges.items()):
        return False
    return bool(np.isclose(volume, (2*half_size)**3, rtol=1e-12, atol=0))


def geometry_observation(engine, case, native, mesh=None):
    if engine == 'mujoco':
        observed = native.get('geometry_readback', {})
        sizes = np.asarray(observed.get('size', []))
        passed = (observed.get('type') == [0, 6] and sizes.shape == (2, 3)
                  and np.isfinite(sizes).all()
                  and np.allclose(sizes[1], case['half_size'], rtol=0, atol=1e-12))
        return {'checked_representation': 'compiled analytic plane and box dimensions',
                'representation_matches': bool(passed), 'cooked_mesh_equivalence': None}
    if engine == 'superdex':
        passed = mesh is not None and box_mesh_matches(mesh['vertices'], mesh['faces'], case['half_size'])
        return {'checked_representation': 'submitted triangle mesh only',
                'representation_matches': bool(passed), 'cooked_mesh_equivalence': None,
                'combined_contact_law_readback': None}
    raise ValueError('Unsupported native representation')
