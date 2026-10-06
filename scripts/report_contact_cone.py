"""Re-score a frozen contact-onset study and export its complete table and figure."""
import argparse
import csv
import json
from pathlib import Path

from dexlab.contact_cone import verify_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = verify_matrix(args.study)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'cone-results.json').write_text(json.dumps(result, indent=2) + '\n')
    rows = [dict(row['job'], valid=row['result']['valid'],
                 engineering_pass=row['result']['engineering']['passed'],
                 **row['result']['metrics']) for row in result['cases']]
    with (args.output / 'cone-results.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), layout='constrained')
    for column, mu in enumerate((0.3, 0.0)):
        for cone, color in (('elliptic', '#0072B2'), ('pyramidal', '#D55E00')):
            for tc, style in ((0.005, '-'), (0.02, '--')):
                points = sorted((r for r in rows[:24] if r['friction'] == mu
                                 and r['cone'] == cone and r['timeconst'] == tc),
                                key=lambda r: r['timestep'])
                for axis, key in zip(axes[:, column], (
                    'maximum_abs_vertical_speed_m_s', 'first50ms_vx_reference_max_m_s')):
                    axis.plot([r['timestep'] * 1000 for r in points],
                              [r[key] * 1000 if r['valid'] else float('nan') for r in points],
                              style, color=color, marker='o', label=f'{cone}, tc={tc*1000:g} ms')
                    axis.set_xticks([0.25, 0.5, 1])
                    axis.grid(alpha=0.2)
                    axis.set_ylim(bottom=0)
        axes[0, column].set_title(f'Authored friction = {mu:g}')
        axes[1, column].set_xlabel('Timestep (ms)')
    axes[0, 0].set_ylabel('Peak |vertical speed| (mm/s)')
    axes[1, 0].set_ylabel('First 50 ms max vx discrepancy (mm/s)')
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('MuJoCo 3.15.0: geometric-touch onset, no settling\n24 fixed conditions; scales differ by panel; lines are visual guides')
    fig.savefig(args.output / 'cone-results.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
