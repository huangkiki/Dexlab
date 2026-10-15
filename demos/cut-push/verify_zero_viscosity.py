"""Compare old/new zero-viscosity material steps on frozen native event states."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

from dexlab import cutting, cutting_geometry


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(run, baseline_source):
    manifest = json.loads((run / 'manifest.json').read_text())
    if (manifest['task'] != 'tofu-sequential' or manifest['motion_protocol'] != 'cut-push'
            or manifest['config'].get('dynamic_viscosity', 0.) != 0.):
        raise ValueError('Expected the frozen pure-elastic continuous tofu record')
    if digest(baseline_source) != manifest['source_sha256']['cutting.py']:
        raise ValueError('Baseline source does not match the frozen native record')
    if digest(Path(cutting_geometry.__file__)) != manifest['source_sha256']['cutting_geometry.py']:
        raise ValueError('Geometry differs from the frozen native record')
    if digest(run / 'states.npz') != manifest['artifacts']['states.npz']:
        raise ValueError('Changed saved states')
    spec = importlib.util.spec_from_file_location('dexlab_frozen_cutting', baseline_source)
    baseline = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = baseline
    spec.loader.exec_module(baseline)
    config_values = dict(manifest['config'])
    for name in ('size', 'blade_half_size'):
        config_values[name] = tuple(config_values[name])
    config = cutting.CutConfig(**config_values)
    sim = cutting.CuttingSimulation(config)
    with np.load(run / 'states.npz', allow_pickle=False) as archive:
        for key, actual in [('reference', sim.reference), ('nodes', sim.nodes), ('weights', sim.weights)]:
            np.testing.assert_array_equal(archive[key], actual)
        states = {key: archive[key] for key in ('time', 'position', 'velocity', 'deformation', 'sides')}
    mu = config.young_modulus / (2 * (1 + config.poisson_ratio))
    lam = config.young_modulus * config.poisson_ratio / ((1 + config.poisson_ratio) * (1 - 2 * config.poisson_ratio))
    random = np.random.default_rng(217)
    impulse = random.normal(0., 1e-8, sim.x.shape)
    impulse -= impulse.mean(axis=0)
    checks = []
    for time in (0., .5, 1., 2., 3., 3.3, 4.2, 5.5, 6.):
        frame = int(np.argmin(abs(states['time'] - time)))
        if abs(states['time'][frame] - time) > 1e-12:
            raise ValueError('Missing declared event frame')
        for label, applied in [('zero', np.zeros_like(impulse)), ('balanced-random', impulse)]:
            outputs = []
            for kernel in (baseline.material_step, cutting.material_step):
                arrays = [states[key][frame].copy() for key in ('position', 'velocity', 'deformation')]
                kernel(*arrays, states['sides'][frame].copy(), sim.nodes, sim.weights, sim.gradients,
                       applied.copy(), sim.mass, sim.volume, mu, lam, config.dt, config.flip_fraction,
                       sim.node_count)
                outputs.append(arrays)
            for old, new in zip(*outputs, strict=True):
                if old.dtype != new.dtype or old.shape != new.shape:
                    raise ValueError('Changed material state representation')
                np.testing.assert_array_equal(old.view(np.uint8), new.view(np.uint8))
            checks.append({'time_s': time, 'impulse_pattern': label, 'x_velocity_F_bitwise_equal': True})
    return {'state': 'passed', 'checks': checks, 'source_artifacts': manifest['artifacts'],
            'baseline_source_sha256': digest(baseline_source),
            'new_source_sha256': digest(Path(cutting.__file__)),
            'scope': 'Isolated material-step regression at nine saved event states, each with two impulse patterns. This is not a new full trajectory or a physical input applied to the showcase.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--baseline-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.run, args.baseline_source)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'state': report['state'], 'checks': len(report['checks'])}))


if __name__ == '__main__':
    main()
