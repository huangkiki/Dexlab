"""Recompute Newtonian dissipation from saved states without importing the solver."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.cutting_score import histories_compatible


def verify(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    config = manifest['config']
    eta = config.get('dynamic_viscosity', 0.)
    if (not np.isfinite(eta) or eta <= 0
            or manifest.get('motion_protocol') not in ('cut-push', 'cut-no-push')):
        raise ValueError('Expected positive viscosity and a continuous record without velocity injection')
    for name in ('states.npz', 'trace.npz'):
        with (directory / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['artifacts'][name]:
                raise ValueError(f'Changed raw record: {name}')
    with np.load(directory / 'states.npz', allow_pickle=False) as archive:
        state = {key: archive[key] for key in
                 ('reference', 'time', 'nodes', 'weights', 'velocity', 'deformation', 'sides')}
    with np.load(directory / 'trace.npz', allow_pickle=False) as archive:
        recorded = archive['viscous_dissipation_j']
    h, dt = config['grid_spacing'], config['dt']
    cells = np.rint(np.asarray(config['size']) / h).astype(int)
    origin = -np.array([config['size'][0] / 2, config['size'][1] / 2, 0.])
    nodes, weights = state['nodes'], state['weights']
    coordinates = np.stack(np.unravel_index(nodes, cells + 1), axis=-1) * h + origin
    relative = coordinates - state['reference'][:, None, :]
    factors = 1 - abs(relative) / h
    np.testing.assert_allclose(factors.prod(axis=2), weights, rtol=0, atol=1e-12)
    gradients = np.empty_like(relative)
    for axis in range(3):
        others = [other for other in range(3) if other != axis]
        gradients[:, :, axis] = np.sign(relative[:, :, axis]) * factors[:, :, others].prod(axis=2) / h
    volume = (h / 2)**3
    particle_mass = config['density'] * volume
    count = int(np.prod(cells + 1))
    expected, observed = [], []
    for time, velocity, deformation, codes in zip(
            state['time'], state['velocity'], state['deformation'], state['sides'], strict=True):
        step = round(time / dt)
        if step == len(recorded):
            continue  # The final state has no following substep.
        if not 0 <= step < len(recorded) or abs(step * dt - time) > 1e-12:
            raise ValueError('Saved state does not match an integration boundary')
        mass = np.zeros((int(codes.max()) + 1, count))
        momentum = np.zeros((*mass.shape, 3))
        np.add.at(mass, (codes[:, None], nodes), particle_mass * weights)
        np.add.at(momentum, (codes[:, None], nodes),
                  particle_mass * weights[:, :, None] * velocity[:, None, :])
        total_mass = mass.sum(axis=0)
        coupled = momentum.copy()
        occupied = total_mass > 0
        for a in range(len(mass)):
            for b in range(a + 1, len(mass)):
                if not histories_compatible(a, b):
                    continue
                exchange = (mass[a, occupied, None] * momentum[b, occupied]
                            - mass[b, occupied, None] * momentum[a, occupied]) / total_mass[occupied, None]
                coupled[a, occupied] += exchange
                coupled[b, occupied] -= exchange
        grid_velocity = np.zeros_like(momentum)
        np.divide(coupled, mass[:, :, None], out=grid_velocity, where=mass[:, :, None] > 0)
        reference_rate = np.einsum('paj,pak->pjk', grid_velocity[codes[:, None], nodes], gradients)
        spatial_rate = reference_rate @ np.linalg.inv(deformation)
        symmetric = (spatial_rate + spatial_rate.transpose(0, 2, 1)) / 2
        jacobian = np.linalg.det(deformation)
        if (jacobian <= 0).any():
            raise ValueError('Inverted saved material point')
        expected.append(2 * eta * dt * volume * np.sum(jacobian * np.sum(symmetric**2, axis=(1, 2))))
        observed.append(recorded[step])
    np.testing.assert_allclose(observed, expected, rtol=1e-10, atol=1e-13)
    if not expected or not np.isfinite(recorded).all() or recorded.min() < -1e-14:
        raise ValueError('Missing, nonfinite or negative constitutive dissipation')
    return {
        'state': 'passed', 'dynamic_viscosity_pa_s': eta, 'dt_s': dt,
        'source_artifacts': manifest['artifacts'], 'samples_checked': len(expected),
        'maximum_sample_error_j': float(np.max(np.abs(np.asarray(expected) - observed))),
        'native_total_constitutive_dissipation_j': float(recorded.sum()),
        'definition': 'At each saved state with a following substep: dt * sum(2 eta V0 J D:D), using the current compatibility-filtered P2G velocity. This is constitutive dissipation, not the total mechanical energy change.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.run)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
