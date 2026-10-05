"""Plot solved-step unloading forces, preserving both damping settings."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from report_damping_ablation import summarize


def plot(root, output):
    report = summarize(root)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5), sharey=True)
    sources = {}
    for ax, dt in zip(axes, (.0005, .00025, .000125), strict=True):
        for damping, color in [(0., '#0072B2'), (10., '#D55E00')]:
            row = next(r for r in report['results'] if r['timestep_s'] == dt and r['damping_s_m'] == damping)
            source = root/'raw'/row['id']/'states.npz'
            sources[row['id']] = hashlib.sha256(source.read_bytes()).hexdigest()
            with np.load(source, allow_pickle=False) as data:
                time = data['time'][1:]
                window = (time >= .6-1e-10) & (time <= .615+1e-10)
                ax.plot((time[window]-.6)*1000, data['contact_force'][window, 2],
                        '.-', markersize=3, linewidth=1, color=color, label=f'{damping:g} s/m')
            ax.axhline(0, color='#555555', linewidth=.6)
        ax.set(title=f'dt = {dt*1e6:g} µs', xlabel='Time after unloading (ms)')
        ax.grid(alpha=.2)
    axes[0].set_ylabel('Vertical contact force (N)')
    axes[-1].legend(title='Normal damping')
    fig.suptitle('Matched damping ablation: tensile force during unloading', fontsize=12)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170)
    plt.close(fig)
    output.with_suffix('.provenance.json').write_text(json.dumps({
        'state_sha256': sources, 'plot_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'image_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'scope': 'Six complete deterministic episodes; 0-15 ms unloading detail only. Lines join solved-step samples, not continuous force reconstruction.'
    }, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plot(args.directory, args.output)
