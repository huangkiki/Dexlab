#!/usr/bin/env python3
"""Plot measured overlap and energy-error sensitivity without rerunning physics."""
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
    report = json.loads(args.input.read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.labelsize': 10, 'axes.titlesize': 12,
                         'legend.fontsize': 10, 'xtick.labelsize': 9,
                         'ytick.labelsize': 9, 'figure.facecolor': 'white'})
    figure, axes = plt.subplots(2, 3, figsize=(11, 6), layout='constrained')
    styles = [(.001, '#0072B2', 'o', '-'),
              (.0005, '#E69F00', 's', '-'),
              (.00025, '#009E73', '^', '-')]
    for col, speed in enumerate((.5, 1., 2.)):
        for step, color, marker, line in styles:
            rows = sorted((row for row in report['results']
                           if row['speed_m_s'] == speed and row['timestep_s'] == step),
                          key=lambda row: row['arrival_phase'])
            x = [row['arrival_phase'] for row in rows]
            for axis, values in [(axes[0,col], [row['penetration_m']*1000 for row in rows]),
                                 (axes[1,col], [row['metrics']['relative_energy_error']*100 for row in rows])]:
                axis.plot(x, values, color=color, marker=marker, linestyle=line,
                          label=f'h = {step*1000:g} ms', linewidth=1.7, markersize=5)
        axes[0,col].set_title(f'Incident speed {speed:g} m/s')
        axes[0,col].set_yscale('log')
        axes[0,col].set_ylim(.35, 3)
        axes[1,col].set_ylim(-.08, 2.6)
        for row in (0,1):
            axes[row,col].axhline(1, color='#666666', linestyle=':', linewidth=1.4)
            axes[row,col].set_xticks([0,.25,.5,.75])
            axes[row,col].set_xlabel('Arrival phase (step fraction)')
            axes[row,col].grid(alpha=.18)
    axes[0,0].set_ylabel('Sampled overlap (mm)')
    axes[1,0].set_ylabel('Relative energy error (%)')
    figure.suptitle('Arrival phase changes finer-step errors; 1 ms endpoints remain near exact', fontsize=14)
    handles, labels = axes[0,0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='outside lower center', ncol=3, frameon=False)
    figure.savefig(args.output, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(figure)


if __name__ == '__main__':
    main()
