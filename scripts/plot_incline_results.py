"""Plot all frozen incline cases; no selection by pass/fail."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    results = {r['id']: r for r in data['results']}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout='constrained')
    for impedance, color in [(0.9, '#0072B2'), (0.99, '#D55E00')]:
        for regime, style in [('static', '-'), ('sliding', '--'), ('frictionless', ':')]:
            cases = sorted((c for c in data['protocol']['cases'] if c['impedance'] == impedance and c['regime'] == regime), key=lambda c: c['timestep'])
            rows = [results[c['id']] for c in cases]
            h = [c['timestep'] * 1000 for c in cases]
            label = f'{regime}, d={impedance}'
            axes[1, 1].plot(h, [r['timing']['native_step_s'] * 1000 for r in rows], style, marker='o', color=color, label=label)
            if regime == 'static':
                axes[0, 0].plot(h, [r['metrics']['static_displacement_m'] * 1000 for r in rows], '-o', color=color, label=f'd={impedance}')
            if regime == 'sliding':
                axes[0, 1].plot(h, [r['contact_loss_fraction'] * 100 for r in rows], '-o', color=color, label=f'd={impedance}')
            if regime == 'frictionless':
                axes[1, 0].plot(h, [r['full_position_rmse_m'] * 1000 for r in rows], '-o', color=color, label=f'd={impedance}')
    axes[0, 0].axhline(1, color='black', linestyle=':', label='frozen limit')
    labels = [('Static: two-second drift', 'Displacement (mm)'),
              ('Sliding: reference assumptions fail', 'Contact-free solve epochs (%)'),
              ('Requested-zero friction: full-reference error', 'Position RMSE (mm)'),
              ('Single short CPU run; timing is noisy', 'Native step time per case (ms)')]
    for ax, (title, ylabel) in zip(axes.flat, labels):
        ax.set(title=title, xlabel='Time step (ms)', ylabel=ylabel)
        ax.set_xticks([.5, 1, 2])
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('MuJoCo 3.15.0 • 18 preregistered incline cases', fontsize=14)
    fig.savefig(args.output, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
