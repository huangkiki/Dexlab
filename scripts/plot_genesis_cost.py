"""Plot measured quality and instrumented CPU costs without engine ranking."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(source, output):
    data = json.loads(source.read_text())
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    for case in data['cases']:
        trials = case['timings']['trials']
        positives = [t for t in trials if t['condition'] == 'pinch']
        dt = case['dt_s'] * 1000
        for trial in positives:
            metrics = case['score']['results'][f"pinch-{trial['repeat']}"]['metrics']
            cost = trial['step_s']
            axes[0].scatter(cost, metrics['native_max_penetration_m']*1000, label=f'{dt:g} ms / reset {trial["repeat"]}')
        means = {k: sum(t[k] for t in positives)/len(positives) for k in ('control_s','step_s','observations_s','serialize_write_s')}
        bottom = 0
        for k, color in zip(means, ('#687c95','#227c9d','#e9c46a','#cf6652')):
            axes[1].bar(str(dt), means[k], bottom=bottom, color=color, label=k if case is data['cases'][0] else None)
            bottom += means[k]
    axes[0].axhline(1, linestyle='--', color='#777', label='Frozen 1 mm criterion')
    axes[0].set(xlabel='Instrumented stepping wall time / 4 s episode (s)', ylabel='Full-episode native peak penetration (mm)', title='Development quality / cost; both resets shown')
    axes[1].set(xlabel='Timestep (ms)', ylabel='Mean wall time / positive episode (s)', title='Separate costs; reset-pair mean')
    for ax in axes:
        ax.grid(axis='y', alpha=.2)
        ax.legend(fontsize=7)
    fig.suptitle('Genesis 1.4.3 CPU FP64 | warm cache | no convergence or engine-ranking claim',fontsize=11)
    fig.savefig(output,dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    a=parser.parse_args()
    if a.output.exists():
        parser.error('Choose a fresh output path')
    plot(a.source,a.output)
