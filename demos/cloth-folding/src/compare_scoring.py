"""Read-only historical scoring comparison and independent geometry controls.

Controls are evaluator tests, not new simulated grasps or tuned trajectories.
"""

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import mujoco
import numpy as np

from verify_cloth import input_hashes, verify_episode, verify_saved


def clipped_depth(face, lower, upper):
    """Independent polygon clipping + bisection reference; no LP solver."""
    def intersects(inset):
        polygon = list(np.asarray(face, dtype=float))
        for axis in range(3):
            for sign, bound in ((1, lower[axis] + inset), (-1, upper[axis] - inset)):
                if not polygon:
                    return False
                output = []
                for previous, current in zip(polygon[-1:] + polygon[:-1], polygon):
                    a = sign * (previous[axis] - bound)
                    b = sign * (current[axis] - bound)
                    if (a >= 0) != (b >= 0):
                        output.append(previous + a / (a - b) * (current - previous))
                    if b >= 0:
                        output.append(current)
                polygon = output
        return bool(polygon)

    if not intersects(0):
        return 0.0
    lo, hi = 0.0, float(np.min(upper - lower) / 2)
    for _ in range(36):
        midpoint = (lo + hi) / 2
        if intersects(midpoint):
            lo = midpoint
        else:
            hi = midpoint
    return lo


def compare(directory):
    """Keep source evidence immutable and compare identical protocol inputs."""
    directory = Path(directory)
    original = input_hashes(directory)
    legacy_path = Path(__file__).parents[1] / 'evidence/legacy/verify_cloth_v0_14_2.py'
    provenance = json.loads((legacy_path.parent / 'source.json').read_text())
    assert hashlib.sha256(legacy_path.read_bytes()).hexdigest() == provenance['sha256']
    spec = importlib.util.spec_from_file_location('frozen_cloth_verifier', legacy_path)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    metadata = json.loads((directory / 'summary.json').read_text())
    records = json.loads((directory / 'trace.json').read_text())
    plans = []
    for path in sorted(directory.glob('plan-*.npz')):
        with np.load(path, allow_pickle=False) as archive:
            plan = dict(archive)
            plan['side'] = str(plan['side'])
            plans.append(plan)
    options = dict(task=metadata['task'], hold_end=metadata['schedule_s']['hold_end'],
                   duration=metadata['schedule_s']['duration'], failure=metadata['failure'],
                   sample_dt=metadata['sample_dt_s'])
    variants = {'original': (records, metadata['maximums'])}
    injected = copy.deepcopy(records)
    injected[48]['table_penetration_m'] = 0.02
    variants['injected_trace_20mm'] = (injected, metadata['maximums'])
    consistent = dict(metadata['maximums'], table_penetration_m=0.02)
    variants['consistent_trace_and_summary_20mm'] = (injected, consistent)
    compared = {}
    for name, (trace, maxima) in variants.items():
        old = legacy.verify_episode(trace, maxima, plans, **options)
        new = verify_episode(trace, maxima, plans, **options)
        compared[name] = {
            'old_protocol_passed': old['passed'], 'new_protocol_passed': new['passed'],
            'new_failed_checks': [key for key, passed in new['checks'].items() if not passed],
        }
    current = verify_saved(directory)
    diagnostic = current['table_surface_diagnostic']
    if 'table_bounds_m' not in diagnostic:
        raise ValueError('Historical reference requires supported table geometry')
    lower, upper = np.asarray(diagnostic['table_bounds_m'])
    model = mujoco.MjModel.from_binary_path(str(directory / 'model.mjb'))
    data = mujoco.MjData(model)
    reference = []
    with np.load(directory / 'states.npz', allow_pickle=False) as states:
        # Fixed quartile checkpoints; not selected for agreement or task success.
        indices = np.linspace(0, len(states['qpos']) - 1, 5, dtype=int)
        for index in indices:
            data.qpos[:] = states['qpos'][index]
            mujoco.mj_fwdPosition(model, data)
            depth = max(clipped_depth(face, lower, upper)
                        for face in data.flexvert_xpos[states['triangles']])
            measured = diagnostic['rows'][index]['triangle_max_interior_depth_m']
            reference.append({'frame': int(index), 'clipping_depth_m': depth,
                              'lp_depth_m': measured, 'absolute_difference_m': abs(depth - measured)})
    if input_hashes(directory) != original:
        raise ValueError('Source recording changed during comparison')
    return {
        'comparison_version': 'cloth-score-comparison-v1', 'input_sha256': original,
        'legacy_source': provenance, 'current_report': current, 'protocol_controls': compared,
        'historical_reference': reference,
        'reference_agrees_within_1e_8_m': all(row['absolute_difference_m'] <= 1e-8 for row in reference),
        'reference_scope': 'Independent intersection algorithm at five fixed saved frames; shared recorded geometry/FK; no independent physics or inter-frame claim',
        'injection_scope': 'Synthetic trace-only inconsistency and matched high-penetration control; no trajectory or original evidence edited',
        'comparison_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error('Comparison output must be outside the original recording')
    result = compare(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    controls = result['protocol_controls']
    valid = (controls['original']['old_protocol_passed']
             and controls['original']['new_protocol_passed']
             and controls['injected_trace_20mm']['old_protocol_passed']
             and not controls['injected_trace_20mm']['new_protocol_passed']
             and not controls['consistent_trace_and_summary_20mm']['new_protocol_passed']
             and result['current_report']['assessment'] == 'geometry_review_required'
             and result['reference_agrees_within_1e_8_m'])
    print(json.dumps({'comparison_checks_passed': valid, 'assessment': result['current_report']['assessment']}))
    raise SystemExit(0 if valid else 1)
