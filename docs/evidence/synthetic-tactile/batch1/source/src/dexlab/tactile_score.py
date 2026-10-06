"""Independent separation of native fixture results and synthetic observations."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.physx_baseline import box_plane_clearance


PATHS = ("direct", "slide-return", "detach-recontact", "reset-direct")


def evaluate(record, arrays):
    try:
        expected = [f'{r}-{p}' for r in (32, 64) for p in PATHS]
        if record.get('completed') is not True or 'error' in record or [r['name'] for r in record['runs']] != expected or set(arrays) != set(expected):
            raise ValueError('Incomplete frozen eight-trajectory batch')
        case = record['case']
        if any(case[k] != v for k, v in dict(mass=.2, half_size=.02, friction=.3, gravity=9.81, timestep=.0005, initial_speed=0., duration=3., settle=0.).items()):
            raise ValueError('Native protocol mismatch')
        results = []
        for row in record['runs']:
            a = arrays[row['name']]
            shapes = {'pose': (6001, 7), 'velocity': (6001, 6), 'force': (6000, 3), 'command': (6000, 6), 'maps': (150, row['resolution'], row['resolution']), 'map_stats': (6000, 3)}
            if any(a[k].shape != v or not np.isfinite(a[k]).all() for k, v in shapes.items()):
                raise ValueError('Incomplete or nonfinite arrays')
            if a['warnings'].shape[0] != 6000 or len(row['contact_distances_m']) != 6000:
                raise ValueError('Missing native coverage')
            dist = np.array([d for values in row['contact_distances_m'] for d in values], float)
            if not np.isfinite(dist).all():
                raise ValueError('Nonfinite native contact distance')
            if np.max(abs(np.linalg.norm(a['pose'][:, 3:], axis=1) - 1)) > 1e-10:
                raise ValueError('Nonunit native orientation')
            clearance = box_plane_clearance(a['pose'], .02)
            support_error = float(abs(a['force'][-1000:, 2].mean() / (.2 * 9.81) - 1))
            rotation_error = float(np.rad2deg(2 * np.arccos(np.clip(abs(a['pose'][-1, 3]), 0, 1))))
            detached = clearance[1:] > .001
            sensor_ok = bool(a['map_stats'][:, 0].min() >= 0 and a['map_stats'][:, 1].max() <= .001 + 1e-12 and (a['map_stats'][detached, 1] <= 1e-12).all())
            penetration = float(max(0., -clearance.min(), -dist.min() if len(dist) else 0.))
            results.append({'name': row['name'], 'native_passed': bool(not a['warnings'].any() and penetration <= .001 and support_error <= .05), 'sensor_bounds_and_detachment_passed': sensor_ok,
                            'maximum_penetration_m': penetration, 'terminal_support_relative_error': support_error,
                            'terminal_position_m': a['pose'][-1, :3].tolist(), 'terminal_rotation_deg': rotation_error,
                            'detached_steps': int(detached.sum()),
                            'path_exercised': bool((row['path'] != 'detach-recontact' or detached.any()) and (row['path'] != 'slide-return' or np.max(a['pose'][:, 0]) >= .01))})
        invariance = []
        for path in PATHS:
            left, right = (arrays[f'{r}-{path}'] for r in (32, 64))
            differences = {k: float(np.max(abs(left[k] - right[k]))) for k in ('pose', 'velocity', 'force', 'command')}
            invariance.append({'path': path, 'differences': differences, 'bitwise_equal': all(np.array_equal(left[k], right[k]) for k in differences), 'passed': all(v <= 1e-12 for v in differences.values())})
        resets = []
        endpoints = []
        for r in (32, 64):
            direct = arrays[f'{r}-direct']
            reset = arrays[f'{r}-reset-direct']
            resets.append(all(np.max(abs(direct[k] - reset[k])) <= 1e-12 for k in ('pose', 'velocity', 'force', 'command')))
            for path in PATHS:
                pose = arrays[f'{r}-{path}']['pose'][-1]
                reference = direct['pose'][-1]
                position = float(np.linalg.norm(pose[:3] - reference[:3]))
                angle = float(np.rad2deg(2 * np.arccos(np.clip(abs(pose[3:] @ reference[3:]), 0, 1))))
                endpoints.append({'name': f'{r}-{path}', 'position_difference_m': position, 'rotation_difference_deg': angle, 'passed': position <= .0001 and angle <= .1})
        return {'valid': True, 'passed': all(x['native_passed'] and x['sensor_bounds_and_detachment_passed'] and x['path_exercised'] for x in results) and all(x['passed'] for x in invariance + endpoints) and all(resets), 'runs': results, 'observation_invariance': invariance, 'resets': [bool(v) for v in resets], 'endpoints': endpoints,
                'limits': 'Synthetic occupancy only. Native force is solve epoch; map is post-step. No real tactile accuracy, shear history or material calibration.'}
    except (KeyError, ValueError, TypeError, IndexError) as error:
        return {'valid': False, 'passed': False, 'reason': str(error)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    record = json.loads((args.directory / 'record.json').read_text())
    arrays = {r['name']: dict(np.load(args.directory / (r['name'] + '.npz'), allow_pickle=False)) for r in record['runs']}
    result = evaluate(record, arrays)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
