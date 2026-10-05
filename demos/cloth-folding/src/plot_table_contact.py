"""Plot the recorded table-edge witness; this is a projection, not a depth map."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


def render(report, output):
    data = json.loads(report.read_text())
    points = np.array(data['triangle_vertices_m'])
    lower, upper = np.array(data['table_bounds_m'])
    projected = (points[:, 1:] - [lower[1], upper[2]]) * 1000
    midpoints = (projected + projected[[1, 2, 0]]) / 2
    files = {}
    for zh in [False, True]:
        if zh:
            font_manager.findfont('Noto Sans CJK SC', fallback_to_default=False)
        plt.rcParams.update({'font.family': 'Noto Sans CJK SC' if zh else 'DejaVu Sans',
                             'font.size': 11, 'axes.unicode_minus': False,
                             'svg.hashsalt': 'dexlab-table-contact-v1'})
        fig, ax = plt.subplots(figsize=(8.7, 5.0), layout='constrained')
        ax.add_patch(Rectangle((0, (lower[2]-upper[2])*1000), 17, 6,
                              color='#BBC4CE', alpha=.6, label='桌体投影' if zh else 'Table projection'))
        ax.plot(*projected[[0, 1, 2, 0]].T, color='#0072B2', linewidth=2,
                label='原始三角形边界' if zh else 'Original triangle boundary')
        ax.scatter(*projected.T, color='#0072B2', s=55, zorder=5,
                   label='原始顶点：均在桌体外' if zh else 'Original vertices: all outside table')
        ax.scatter(*midpoints.T, color='#D55E00', marker='x', s=80, zorder=6,
                   label='细分增加的边中点' if zh else 'Edge midpoints added by subdivision')
        for i, offset in enumerate([(-42, 12), (-42, -18), (8, 2)]):
            ax.annotate(f'v{i}', projected[i], xytext=offset, textcoords='offset points', fontsize=11)
        ax.set(xlim=(-4, 17), ylim=(-7, 6),
               xlabel='Y：相对桌前缘 (mm)' if zh else 'Y relative to front edge (mm)',
               ylabel='Z：相对桌面 (mm)' if zh else 'Z relative to tabletop (mm)')
        ax.axhline(0, color='#687080', linewidth=.7); ax.axvline(0, color='#687080', linewidth=.7)
        ax.set_title('历史第 0 帧，三角形 42：布面跨过桌边' if zh else 'Historical frame 0, triangle 42: surface crosses the table edge')
        ax.legend(loc='lower right', fontsize=9, framealpha=.95)
        ax.text(.01, .99, 'Y–Z 投影；不是三维穿透深度图\n静态查询，未执行动力学步进' if zh else
                'Y–Z projection, not a 3D penetration-depth map\nStatic query; zero dynamics integration steps',
                transform=ax.transAxes, va='top', fontsize=10)
        suffix='.zh-CN' if zh else ''
        for extension in ['svg', 'png']:
            p=output/f'witness{suffix}.{extension}'
            fig.savefig(p, dpi=160, metadata={'Date': None} if extension=='svg' else None)
            if extension=='svg':
                p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
            files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        plt.close(fig)
    receipt={'input_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
             'plot_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'artifacts':files,'scope':'Y-Z projection of recorded geometry; not a dynamics replay'}
    (output/'figure-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    render(args.report,args.output)
