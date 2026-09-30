"""Plot the saved geometric diagnostic; does not run physics or rescore it."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(report_path, output, language):
    report = json.loads(report_path.read_text())
    diagnostic = report['current_report']['table_surface_diagnostic']
    rows = diagnostic['rows']
    chinese = language == 'zh'
    plt.rcParams.update({'font.family': 'Noto Sans CJK SC' if chinese else 'DejaVu Sans',
                         'font.size': 11, 'svg.hashsalt': 'dexlab-cloth-evidence-v2'})
    fig, ax = plt.subplots(figsize=(9, 3.8), layout='constrained')
    time = [row['time_s'] for row in rows]
    depth = [1000 * row['triangle_max_interior_depth_m'] for row in rows]
    vertex = [1000 * row['vertex_max_interior_depth_m'] for row in rows]
    ax.fill_between(time, depth, color='#bb4b24', alpha=.15)
    ax.plot(time, depth, color='#bb4b24', lw=2,
            label='三角面内部' if chinese else 'Triangle interiors')
    ax.plot(time, vertex, color='#24697c', lw=1.7, linestyle='--',
            label='仅检查顶点' if chinese else 'Vertices only')
    ax.set(xlim=(0, 9), ylim=(-.12, 3.45),
           xlabel='记录时间 / s' if chinese else 'Recorded time / s',
           ylabel='桌体内部深度 / mm' if chinese else 'Table interior depth / mm',
           title=('历史夹布记录：176 / 225 帧存在桌体相交' if chinese else
                  'Historical cloth record: table intrusion in 176 / 225 frames'))
    ax.text(.98, .77, '25 Hz 保存帧；非原生接触距离' if chinese else
            '25 Hz saved states; not native contact distance',
            transform=ax.transAxes, ha='right', fontsize=10)
    ax.legend(loc='upper right', frameon=False, ncols=2)
    ax.grid(alpha=.2)
    ax.spines[['top', 'right']].set_visible(False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={'Date': None})
    plt.close(fig)
    if output.suffix.lower() == '.svg':
        output.write_text('\n'.join(line.rstrip() for line in output.read_text().splitlines()) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--language', choices=('zh', 'en'), default='en')
    args = parser.parse_args()
    plot(args.report, args.output, args.language)
