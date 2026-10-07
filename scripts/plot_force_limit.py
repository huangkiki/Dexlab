"""Plot full-rate scored observations; missing cases remain explicitly incomplete."""
import argparse
import json
from pathlib import Path


def plot(campaign, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    manifest = json.loads((Path(__file__).resolve().parents[1] /
                           'demos/contact-benchmark/force-limit-v1.json').read_text())
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for path in sorted(campaign.glob('attempt-*/score.json')):
        result = json.loads(path.read_text())
        case_id = result['case']['id']
        if case_id in results:
            raise ValueError(f'Multiple scores for {case_id}; reconcile attempts explicitly')
        results[case_id] = result
    declared = {case['id'] for case in manifest['cases']}
    if set(results) - declared:
        raise ValueError('Unregistered scored case')
    colors = {.2: '#0072B2', .4: '#D55E00', .8: '#009E73', 10.: '#CC79A7'}
    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    for row, offset in enumerate([0., -.002, .002]):
        for case in manifest['cases']:
            if case['initial_x_m'] != offset or case['id'] not in results:
                continue
            result = results[case['id']]
            samples = result['timeline']
            times = [sample['time_s'] for sample in samples]
            label = case['id'].replace('dev-', '').replace('eval-', '')
            negative = case['condition'] == 'open_negative'
            style = '--' if negative or 'repeat' in case['id'] else '-'
            color = '#555555' if negative else colors[case['force_limit_N']]
            axes[row, 0].plot(times, [sample['center_z_m']*1000 for sample in samples],
                              label=label, color=color, linestyle=style, linewidth=1.1)
            # Sum absolute x projections: a flat-pad diagnostic, not a measured friction capacity.
            axes[row, 1].plot(times, [sum(sample['pad_abs_x_force_proxy_N']) for sample in samples],
                              label=label, color=color, linestyle=style, linewidth=1.1)
        axes[row, 0].plot([2, 3], [60, 60], color='black', linestyle=':', label='hold threshold')
        axes[row, 1].axhline(.064*9.81/.5, color='black', linestyle=':', label='ideal static sum reference')
        axes[row, 0].set_ylabel(f'x = {offset*1000:g} mm\nCube center z (mm)')
        axes[row, 1].set_ylabel('Sum |pad force x| (N)')
        for ax in axes[row]:
            ax.axvspan(2, 3, color='#999999', alpha=.08)
            ax.axvline(3.2, color='#777777', linewidth=.6)
            ax.grid(alpha=.2)
            ax.legend(fontsize=7, ncol=2)
            ax.set_xlim(0, 4)
    for ax in axes[-1]:
        ax.set_xlabel('Simulation time (s)')
    fig.suptitle(f'Frozen standard-block cases: {len(results)}/{len(declared)} scored\n'
                 'Genesis native dynamics; force projection is not actuator force or hardware truth', fontsize=12)
    fig.tight_layout()
    fig.savefig(output / 'force-height.png', dpi=180)
    plt.close(fig)
    rows = []
    for case in manifest['cases']:
        result = results.get(case['id'])
        rows.append({'case': case, 'status': 'scored' if result else 'incomplete',
                     'result': {key: value for key, value in result.items() if key != 'timeline'}
                     if result else None})
    (output / 'summary.json').write_text(json.dumps({
        'intended': len(declared), 'scored': len(results), 'cases': rows,
        'scope': 'Fixed cases, no population success probability or hardware qualification',
    }, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    plot(args.campaign, args.output)
