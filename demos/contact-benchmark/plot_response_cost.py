"""Plot synthetic-target discrepancy and measured cost, not engine accuracy."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if report['verification']['outcomes_reproduced'] != 27:
        parser.error('Expected all 27 independently reproduced outcomes')
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), layout='constrained')
    profiles = [('mujoco-imp09-', 'MuJoCo impedance 0.9', '#0072B2'),
                ('mujoco-imp0001-', 'MuJoCo impedance 0.001', '#009E73'),
                ('superdex-load-damping-', 'SuperDex load damping', '#D55E00')]
    for prefix, label, color in profiles:
        rows = sorted((r for r in report['groups'] if r['candidate'].startswith(prefix)), key=lambda r:-r['timestep_s'])
        if len(rows) != 3 or any(r['runs'] != 3 for r in rows):
            parser.error('Expected three timesteps with three repeats each')
        x = [r['timestep_s'] * 1000 for r in rows]
        axes[0].plot(x, [r['worst_window_rms_m']*1e6 for r in rows], 'o-', label=label, color=color)
        for ax, key, scale in [(axes[1], 'native_call_seconds', 1000), (axes[2], 'episode_wall_seconds', 1)]:
            costs = [r['cost'][key] for r in rows]
            med = [c['median']*scale for c in costs]
            ax.errorbar(x, med, yerr=[[m-c['minimum']*scale for m,c in zip(med,costs)], [c['maximum']*scale-m for m,c in zip(med,costs)]], fmt='o-', capsize=4, color=color)
    for ax in axes:
        ax.set_xscale('log');ax.set_yscale('log');ax.set_xlim(.57,.11)
        ax.set_xticks([.5,.25,.125], ['0.5','0.25','0.125']);ax.set_xticks([],minor=True)
        ax.set_xlabel('Timestep (ms), finer →');ax.grid(alpha=.2)
    axes[0].set_ylabel('Worst positive-load window RMS (µm)')
    axes[1].set_ylabel('Native API call time / episode (ms)')
    axes[2].set_ylabel('Complete run() call / episode (s)')
    axes[0].set_title('Discrepancy from synthetic target')
    axes[1].set_title('Collision + integration + solver')
    axes[2].set_title('Includes recording and scoring')
    fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=3)
    fig.suptitle('Fixed contact profiles: response and cost\n27 serial runs; 9 combined passes, 18 failures retained. Cost: median and min–max.', fontsize=12)
    fig.savefig(args.output, dpi=170, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
