"""Compare complete measured baseline/candidate traces, including release impact."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('baseline', type=Path)
parser.add_argument('candidate', type=Path)
parser.add_argument('output', type=Path)
a = parser.parse_args()
if a.output.exists():
    parser.error('Choose a new output path')
fig, axes = plt.subplots(2, 1, figsize=(9, 6), layout='constrained', sharex=True)
for path, label, color in [(a.baseline, 'Baseline: 2 ms step, default contact', '#bd4937'),
                           (a.candidate, 'Candidate: 0.5 ms step, contact-only change', '#226d9b')]:
    rows = json.loads(path.read_text())['samples']
    t = [r['time'] for r in rows]
    axes[0].plot(t, [r['object_pos'][2]*1000 for r in rows], label=label, color=color)
    axes[1].plot(t, [1000*max(r['contacts']['penetration'], default=0) for r in rows], color=color)
axes[0].set(ylabel='Object center height (mm)')
axes[0].legend(fontsize=9)
axes[1].set(ylabel='Native penetration (mm)', xlabel='Simulation time (s)', xlim=(0, 4))
axes[1].axhline(1, color='#555555', linestyle='--', label='1 mm engineering criterion')
axes[1].legend()
for ax in axes:
    ax.axvline(3.2, color='#888888', linestyle=':', linewidth=1)
    ax.grid(alpha=.2)
fig.suptitle('Primitive pinch and release | every recorded physics step; no smoothing')
fig.savefig(a.output, dpi=150)
plt.close(fig)
