"""Audit post-withdrawal tofu jitter without filtering positions or changing scores."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def measure(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['task'] != 'tofu-sequential' or manifest['motion_protocol'] != 'cut-push':
        raise ValueError('This diagnostic is defined for the continuous tofu push')
    for name in ('states.npz', 'trace.npz'):
        with (directory / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['artifacts'][name]:
                raise ValueError(f'Changed raw recording: {name}')
    with np.load(directory / 'states.npz', allow_pickle=False) as archive:
        time = archive['time']
        reference = archive['reference']
        positions = archive['position']
    with np.load(directory / 'trace.npz', allow_pickle=False) as archive:
        clock = archive['time_s']
        reaction = archive['material_reaction_n']
    native = (time >= 5.4 - 1e-9) & (time <= 6. + 1e-9)
    displayed = native & np.isclose(time / .05, np.rint(time / .05), atol=1e-9, rtol=0)
    if not np.allclose(time[displayed], np.arange(5.4, 6.01, .05), atol=1e-12, rtol=0):
        raise ValueError('Missing exact 20 Hz display samples in the diagnostic window')
    left = reference[:, 0] < -.015
    sample = positions[displayed][:, left]
    x = sample[:, :, 0].mean(axis=1) * 1000
    reverse = np.abs(np.diff(x)).sum() - abs(x[-1] - x[0])
    contact_window = (clock > 5.4) & (clock <= 6. + 1e-12)
    return {
        'source_artifacts': manifest['artifacts'], 'config': manifest['config'],
        'native_centroid_x_peak_to_peak_mm': float(np.ptp(positions[native][:, left, 0].mean(axis=1)) * 1000),
        'display_centroid_x_peak_to_peak_mm': float(np.ptp(x)),
        'display_centroid_x_excess_reversing_travel_mm': float(reverse),
        'display_particle_second_difference_rms_mm': float(np.sqrt(np.mean(np.diff(sample, n=2, axis=0)**2)) * 1000),
        'maximum_knife_contact_n': float(np.linalg.norm(reaction[contact_window], axis=1).max()),
        'visual_alarm': bool(reverse > .3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--vary', choices=('timestep', 'viscosity'), default='timestep')
    args = parser.parse_args()
    baseline, candidate = measure(args.baseline), measure(args.candidate)
    before = dict(baseline['config'], dynamic_viscosity=baseline['config'].get('dynamic_viscosity', 0.))
    after = dict(candidate['config'], dynamic_viscosity=candidate['config'].get('dynamic_viscosity', 0.))
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = {'dt'} if args.vary == 'timestep' else {'dynamic_viscosity'}
    if changed != expected:
        raise ValueError(f'The comparison must change only {args.vary}')
    report = {
        'schema_version': 1, 'varied_parameter': args.vary,
        'window_s': [5.4, 6.0], 'display_sample_interval_s': .05,
        'definitions': {
            'excess_reversing_travel': 'Sum of absolute successive centroid x increments minus absolute net x displacement; mm.',
            'particle_second_difference_rms': 'RMS of successive second differences of native left-piece xyz positions sampled at display times; mm. No filtering.',
            'visual_alarm': 'More than 0.3 mm excess reversing travel in this display window flags the reported symptom; this is a diagnostic, not food-fidelity acceptance.',
            'scope': ('Timestep changes also alter this contact penalty and per-second transfer dissipation; sensitivity is not proof of convergence or real-food calibration.'
                      if args.vary == 'timestep' else
                      'Only dynamic viscosity changes; this is a synthetic material comparison, not calibrated tofu. Rigid rocking need not dissipate through material viscosity.'),
        },
        'baseline': baseline, 'selected': candidate,
    }
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: {name: value for name, value in row.items() if name not in ('config', 'source_artifacts')}
                      for key, row in [('baseline', baseline), ('selected', candidate)]}, indent=2))


if __name__ == '__main__':
    main()
