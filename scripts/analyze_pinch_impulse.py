#!/usr/bin/env python3
"""Plot all six diagnostic records without rerunning physics."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--scores', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = json.loads(args.scores.read_text())
    cases = results['protocol']['cases']
    rows = results['results']
    if len(rows) != 6 or [row['id'] for row in rows] != [case['id'] for case in cases]:
        raise ValueError('Incomplete or reordered plot matrix')
    args.output.mkdir(parents=True, exist_ok=False)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    colors = ['#0072B2', '#D55E00', '#009E73']
    styles = ['-', '--', ':']
    for column, ratio in enumerate((1, 2)):
        selected = [(case, row) for case, row in zip(cases, rows) if case['capacity_ratio'] == ratio]
        tolerance = [c['solver_tolerance'] for c, _ in selected]
        top = axes[0, column]
        for label, key, style in [('Total', 'total_peak_n_s', 'o-'),
                                  ('Force term', 'force_peak_n_s', 'x--'),
                                  ('Integration term', 'integration_peak_n_s', '^:')]:
            top.loglog(tolerance, [row['metrics'][key] for _, row in selected], style, label=label)
        top.set(xlim=(3e-6, 3e-15), ylim=(1e-22, 1e-5), title=f'R = {ratio}: peak linear impulse residual',
                xlabel='Newton stopping tolerance (dimensionless)', ylabel='Absolute residual (N s)')
        top.grid(alpha=.25); top.legend(fontsize=9)
        bottom = axes[1, column]
        for index, (case, row) in enumerate(selected):
            path = args.input / case['id'] / 'trace.npz'
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['trace_sha256']:
                raise ValueError('Plot trace hash mismatch')
            with np.load(path, allow_pickle=False) as trace:
                states = trace['states']
            onset = round(results['protocol']['preload_s'] / case['timestep'])
            bottom.plot(states[onset:, 0] - states[onset, 0],
                        1000 * (states[onset, 5] - states[onset:, 5]),
                        color=colors[index], linestyle=styles[index], linewidth=2,
                        label=f"tol = {case['solver_tolerance']:.0e}")
        bottom.axhline(1, color='gray', linestyle='--', linewidth=1, label='Original 1 mm limit')
        bottom.set(xlim=(0, 1), ylim=(0, 2.15), title=f'R = {ratio}: loaded motion (curves overlap)',
                   xlabel='Time since load onset (s)', ylabel='Downward travel (mm)')
        bottom.grid(alpha=.25); bottom.legend(fontsize=9)
    fig.savefig(args.output / 'residual-motion.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
