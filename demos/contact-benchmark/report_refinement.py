"""Offline shared-grid differences; preserve physical failures and missing pairs."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from dexlab.contact_refinement import compare_archives


def run_details(directory, scores):
    """Expose measured inputs and costs without exporting deployment paths."""
    metadata = json.loads((directory / 'run.json').read_text())
    statuses = json.loads((directory / 'native-status.json').read_text())
    with np.load(directory / 'states.npz', allow_pickle=False) as states:
        initial = {key: states[key][0].tolist() for key in ('pose', 'velocity')}
    return {
        'id': directory.name,
        'case': metadata['case'],
        'initial_state': initial,
        'native': metadata['native'],
        'artifact_sha256': metadata['artifact_sha256'],
        'native_status': (
            {'kind': 'convergence_status', 'counts': dict(Counter(statuses))}
            if metadata['engine'] == 'superdex' else
            {'kind': 'warning_counters', 'maximum_by_type': np.max(statuses, axis=0).tolist()}
        ),
        'cost_seconds': {key: metadata[key] for key in (
            'preparation_seconds', 'step_and_observation_seconds', 'total_seconds')},
        'physical_score': scores,
    }


def report(directory):
    rows = []
    for engine in ('mujoco', 'superdex'):
        for control in ('forward', 'frictionless'):
            for coarse, fine in (('h', 'h2'), ('h2', 'h4'), ('h4', 'h8')):
                left = f'{engine}-dev-onset-{control}-{coarse}'
                right = f'{engine}-dev-onset-{control}-{fine}'
                result = compare_archives(directory / left, directory / right)
                rows.append({'engine': engine, 'control': control,
                             'coarse': left, 'fine': right, **result})
    scores = {}
    for row in rows:
        for name, score in zip((row['coarse'], row['fine']), row['physical_scores']):
            scores[name] = score
    runs = []
    for name, score in sorted(scores.items()):
        try:
            runs.append(run_details(directory / name, score))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            runs.append({'id': name, 'physical_score': score,
                         'details_error': type(exc).__name__})
    return {'complete_run_details': len(runs) == 16 and all('details_error' not in row for row in runs), 'runs': runs, 'scope': 'Contact-onset development self-consistency; no exact numerical-error or physical-accuracy claim',
            'expected_pairs': 12, 'comparable_pairs': sum(row['comparable'] for row in rows),
            'pairs': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error('Report must be outside the original evidence directory')
    result = report(args.directory)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    # Comparability is not physical acceptance; per-record failures stay explicit.
    raise SystemExit(0 if result['complete_run_details'] and result['comparable_pairs'] == result['expected_pairs'] else 1)


if __name__ == '__main__':
    main()
