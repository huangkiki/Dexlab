"""Plot archived table/robot diagnostics and separately labeled injected controls."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def render(robot_path, table_path, controls_path, output):
    robot, table, controls = [json.loads(p.read_text()) for p in (robot_path, table_path, controls_path)]
    for other in (table, controls):
        if any(other['input_sha256'].get(key) != robot['input_sha256'][key]
               for key in ('model.mjb', 'states.npz')):
            raise ValueError('Diagnostics refer to different source recordings')
    times = np.array([r['time_s'] for r in robot['rows']])
    table_rows = table['table_surface_diagnostic']['rows']
    if not np.array_equal(times, [r['time_s'] for r in table_rows]):
        raise ValueError('Saved-frame time grids differ')
    output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family': ['Noto Sans CJK SC', 'DejaVu Sans'],
                         'axes.unicode_minus': False, 'svg.fonttype': 'none'})
    files = []
    for lang in ('en', 'zh'):
        zh = lang == 'zh'
        fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.5), layout='constrained')
        fig.suptitle('布料几何检查：桌体相交与机器人检查分开报告' if zh else
                     'Cloth geometry: table intrusion and robot coverage', fontsize=17)
        axes[0].plot(times, [r['triangle_max_interior_depth_m'] * 1000 for r in table_rows],
                     color='#b64f30', label='桌体（已有独立诊断）' if zh else 'Table (existing independent diagnostic)')
        axes[0].plot(times, [r['maximum_interior_depth_m'] * 1000 for r in robot['rows']],
                     color='#007c91', linewidth=2, label='79 个机器人碰撞凸包' if zh else '79 robot collision hulls')
        axes[0].set(xlabel='记录时间（s）' if zh else 'Recorded time (s)',
                    ylabel='最大内部侵入（mm）' if zh else 'Maximum interior intrusion (mm)', ylim=(-.15, 3.35))
        axes[0].set_title('同一历史轨迹 · 225 帧 · 25 Hz · 布料中面' if zh else
                          'Same historical trajectory · 225 frames · 25 Hz · cloth midsurface', fontsize=11)
        axes[0].legend(loc='upper right', fontsize=10)
        axes[0].grid(alpha=.2)
        labels = ['原始姿态', '人工移入拇指', '人工平移远离'] if zh else ['Original pose', 'Injected into thumb', 'Translated clear']
        values = [controls['controls'][key]['report']['maximum_interior_depth_m'] * 1000
                  for key in ('original', 'into_thumb', 'translated_clear')]
        axes[1].bar(labels, values, color=['#007c91', '#b64f30', '#007c91'], width=.5)
        axes[1].set(ylabel='最大内部侵入（mm）' if zh else 'Maximum interior intrusion (mm)', ylim=(0, max(values) * 1.28))
        axes[1].set_title('独立反例验证 · 人工修改几何 · 零动力学步进（不是抓取结果）' if zh else
                          'Injected geometry controls · zero integration · not grasp outcomes', fontsize=11)
        for i, value in enumerate(values):
            axes[1].text(i, value + .12, f'{value:.3f}', ha='center', fontsize=11)
        fig.supxlabel('未检查帧间运动或有限厚度；小接触重叠不直接等于物理失效。' if zh else
                       'No inter-frame or finite-thickness claim; small contact overlap alone is not physical failure.', fontsize=10)
        stem = 'coverage.zh-CN' if zh else 'coverage'
        for extension in ('svg', 'png'):
            path = output / f'{stem}.{extension}'
            fig.savefig(path, dpi=150)
            if extension == 'svg':
                path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
            files.append(path)
        plt.close(fig)
    provenance = {
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (robot_path, table_path, controls_path)},
        'outputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'physics_steps_executed': 0,
    }
    (output / 'figure-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('robot', type=Path)
    parser.add_argument('table', type=Path)
    parser.add_argument('controls', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.robot, args.table, args.controls, args.output)
