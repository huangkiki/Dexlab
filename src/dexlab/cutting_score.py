"""Independent validation of saved cutting states; does not import the solver."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


# Frozen before the first run: numerical accounting (FP64), complete topology,
# 2 percentage points half-mass tolerance, and mm-scale motion probe. The
# overlap limit is one contact-proxy radius, not real-food accuracy.
ACCEPTANCE = {
    'fraction_error': .02, 'momentum_error_ns': 1e-9, 'minimum_det_f': .05,
    'maximum_overlap_radii': 1., 'relative_motion_m': .001,
    'passive_motion_m': .003, 'minimum_reaction_n': .001,
}

def grid_components(nodes, weights, sides):
    """Connectivity of nonzero reference stencils and single-cut compatibility.

    Checks the mechanical transfer graph, including unassigned bridges. A
    rendered gap or merely two different labels cannot establish separation.
    """
    count = len(sides)
    parent = np.arange(count)

    def root(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    def join(p, q):
        parent[root(q)] = root(p)

    representatives = {}
    for p in range(count):
        for node, weight in zip(nodes[p], weights[p], strict=True):
            if weight <= 0:
                continue
            groups = representatives.setdefault(int(node), {})
            side = int(sides[p])
            if side in groups:
                join(p, groups[side])
            else:
                groups[side] = p
    for groups in representatives.values():
        if 0 in groups:
            for side in (1, 2):
                if side in groups:
                    join(groups[0], groups[side])
    roots = np.array([root(p) for p in range(count)])
    _, labels, sizes = np.unique(roots, return_inverse=True, return_counts=True)
    return labels, sizes


def score_run(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest.get('status') != 'complete':
        raise ValueError('Incomplete simulation record')
    if set(manifest['artifacts']) != {'states.npz', 'trace.npz'}:
        raise ValueError('Both physical artifacts must be hashed')
    for name, digest in manifest['artifacts'].items():
        if Path(name).name != name:
            raise ValueError('Artifact must be inside the run directory')
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Artifact digest mismatch: {name}')
    with np.load(directory / 'states.npz', allow_pickle=False) as archive:
        states = {key: archive[key] for key in archive.files}
    with np.load(directory / 'trace.npz', allow_pickle=False) as archive:
        trace = {key: archive[key] for key in archive.files}
    needed = {'position', 'velocity', 'sides', 'damage', 'time', 'reference', 'nodes', 'weights'}
    if not needed.issubset(states):
        raise ValueError('Required physical state is missing')
    needed_trace = {'momentum_ns', 'external_impulse_ns', 'material_reaction_n',
                    'maximum_proxy_overlap_m', 'minimum_det_f', 'maximum_det_f',
                    'blade_position_m', 'blade_velocity_m_s', 'time_s', 'drive_force_n',
                    'board_impulse_ns', 'blade_board_impulse_ns'}
    if not needed_trace.issubset(trace):
        raise ValueError('Required native observation is missing')
    if not all(np.isfinite(a).all() for a in (*states.values(), *trace.values())):
        raise ValueError('Non-finite observation')
    x, reference, sides = states['position'], states['reference'], states['sides']
    if x.ndim != 3 or len(x) < 2:
        raise ValueError('Invalid position dimensions')
    frames, particles, axes = x.shape
    config = manifest['config']
    if manifest['acceptance'] != ACCEPTANCE or manifest['probe_time_s'] != 2.4:
        raise ValueError('Altered frozen acceptance or probe protocol')
    dt = config['dt']
    expected_count = int(np.prod(np.rint(np.array(config['size']) / config['grid_spacing']).astype(int) * 2))
    expected_steps = round(manifest['duration_s'] / dt)
    if (axes != 3 or reference.shape != (particles, 3) or particles != expected_count
            or sides.shape != (frames, particles) or states['velocity'].shape != x.shape
            or states['damage'].shape != sides.shape or states['time'].shape != (frames,)
            or states['nodes'].shape != (particles, 8) or states['weights'].shape != (particles, 8)):
        raise ValueError('Invalid state dimensions or particle inventory')
    vector_fields = ('momentum_ns', 'external_impulse_ns', 'material_reaction_n',
                     'blade_position_m', 'blade_velocity_m_s', 'drive_force_n',
                     'board_impulse_ns', 'blade_board_impulse_ns')
    if any(trace[key].shape != (expected_steps, 3) for key in vector_fields):
        raise ValueError('Invalid observation vector dimensions')
    if any(a.ndim == 0 or len(a) != expected_steps for a in trace.values()):
        raise ValueError('Missing or extra integration steps')
    if (not np.allclose(trace['time_s'], (np.arange(expected_steps) + 1) * dt, rtol=0, atol=1e-12)
            or not np.all(np.diff(states['time']) > 0)
            or abs(states['time'][0]) > 1e-12
            or abs(states['time'][-1] - manifest['duration_s']) > 1e-12):
        raise ValueError('Invalid physical clock')
    if (not np.isin(sides, (0, 1, 2)).all() or sides[0].any()
            or ((states['damage'] < 0) | (states['damage'] > 1)).any()
            or not np.allclose(x[0], reference, rtol=0, atol=1e-12)):
        raise ValueError('Invalid initial state or cut state')
    if not np.allclose(states['weights'].sum(axis=1), 1, rtol=0, atol=1e-12):
        raise ValueError('Invalid transfer weights')
    if ((states['weights'] <= 0).any() or (states['nodes'] < 0).any()
            or not np.issubdtype(states['nodes'].dtype, np.integer)):
        raise ValueError('Invalid transfer stencil')
    if states['velocity'][0].any():
        raise ValueError('This protocol starts from rest')
    persistent = bool(np.all((sides[:-1] == 0) | (sides[:-1] == sides[1:])))
    _, initial_sizes = grid_components(states['nodes'], states['weights'], sides[0])
    _, final_sizes = grid_components(states['nodes'], states['weights'], sides[-1])
    fractions = sorted((final_sizes / particles).tolist(), reverse=True)
    initial_momentum = np.zeros(3)
    # Recompute balance from raw momentum and external impulse, not the
    # solver's precomputed residual column.
    residual = np.diff(np.vstack((initial_momentum, trace['momentum_ns'])), axis=0) - trace['external_impulse_ns']
    momentum_error = float(np.abs(residual).max())
    # Independently reconcile frame velocity with raw whole-system momentum.
    mass = config['density'] * (config['grid_spacing'] / 2)**3
    indices = np.rint(states['time'][1:] / dt).astype(int) - 1
    frame_momentum = mass * states['velocity'][1:].sum(axis=1) + config['blade_mass'] * trace['blade_velocity_m_s'][indices]
    frame_error = float(np.abs(frame_momentum - trace['momentum_ns'][indices]).max())
    external = trace['board_impulse_ns'] + trace['blade_board_impulse_ns'] + dt * trace['drive_force_n']
    external[:, 2] -= mass * particles * 9.81 * dt
    probe_step = round(manifest['probe_time_s'] / dt)
    if probe_step < expected_steps:
        external[probe_step] += mass * (reference[:, 0] > 0).sum() * np.array([.12, 0., .1])
    external_error = float(np.abs(external - trace['external_impulse_ns']).max())
    blade_impulse = config['blade_mass'] * np.diff(
        np.vstack((np.zeros(3), trace['blade_velocity_m_s'])), axis=0)
    blade_error = float(np.abs(blade_impulse - dt * (trace['drive_force_n'] + trace['material_reaction_n'])
                               - trace['blade_board_impulse_ns']).max())
    probe_frame = int(np.searchsorted(states['time'], manifest['probe_time_s'], side='right') - 1)
    right = reference[:, 0] > 0
    displacements = [x[-1, mask].mean(axis=0) - x[probe_frame, mask].mean(axis=0)
                     for mask in (~right, right)]
    relative_motion = float(displacements[1][0] - displacements[0][0])
    limits = manifest['acceptance']
    checks = {
        'complete_duration': abs(manifest['duration_s'] - 3.) < 1e-12,
        'initially_connected': len(initial_sizes) == 1,
        'persistent_cut_labels': persistent,
        'two_mechanical_components': len(final_sizes) == 2,
        'half_mass': len(fractions) == 2 and max(abs(f - .5) for f in fractions) <= limits['fraction_error'],
        'momentum_balance': momentum_error <= limits['momentum_error_ns'],
        'frame_momentum_matches': frame_error <= limits['momentum_error_ns'],
        'external_impulse_matches': external_error <= limits['momentum_error_ns'],
        'blade_reaction_feedback': blade_error <= limits['momentum_error_ns'],
        'positive_jacobian': float(trace['minimum_det_f'].min()) >= limits['minimum_det_f'],
        'bounded_overlap': float(trace['maximum_proxy_overlap_m'].max()) <= limits['maximum_overlap_radii'] * config['grid_spacing'] / 4,
        'blade_withdrawn': float(trace['blade_position_m'][-1, 2] - config['blade_half_size'][2]) > float(x[-1, :, 2].max()) + config['grid_spacing'] / 4,
        'independent_motion': relative_motion >= limits['relative_motion_m'] and abs(displacements[0][0]) <= limits['passive_motion_m'],
        'nonzero_material_reaction': float(np.linalg.norm(trace['material_reaction_n'], axis=1).max()) > limits['minimum_reaction_n'],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    return {
        'schema_version': 1, 'mode': manifest['mode'], 'passed': all(checks.values()),
        'checks': checks, 'component_mass_fractions': fractions,
        'initial_components': len(initial_sizes), 'final_components': len(final_sizes),
        'mass_kg': mass * particles, 'particle_count': particles,
        'momentum_error_ns': momentum_error, 'frame_momentum_error_ns': frame_error,
        'external_impulse_error_ns': external_error, 'blade_impulse_error_ns': blade_error,
        'relative_motion_m': relative_motion,
        'left_displacement_m': displacements[0].tolist(), 'right_displacement_m': displacements[1].tolist(),
        'peak_material_reaction_n': float(np.linalg.norm(trace['material_reaction_n'], axis=1).max()),
        'maximum_proxy_overlap_m': float(trace['maximum_proxy_overlap_m'].max()),
        'det_f_range': [float(trace['minimum_det_f'].min()), float(trace['maximum_det_f'].max())],
        'evidence_scope': 'synthetic CPU reference task; not measured tofu or authors implementation',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = score_run(args.directory)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
