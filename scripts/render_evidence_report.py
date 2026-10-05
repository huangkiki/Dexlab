#!/usr/bin/env python3
"""Generate bilingual tables and plots from a completed offline evidence report."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    'apple-regression': ('Apple grasp regression', '苹果抓梗回归'),
    'cloth-heldout': ('Nominal cloth held-out', '基础布料留出'),
    'physx-cloth-heldout': ('PhysX cloth held-out', 'PhysX 布料留出'),
    'contact-development': ('Contact development', '基础接触开发'),
    'normal-response': ('Static response development', '静态响应开发'),
    'transient-response': ('Transient response development', '瞬态响应开发'),
    'robot-cloth': ('Robot cloth diagnostic', '机器人夹布诊断'),
}
OUTCOMES = (
    ('protocol_pass', '#009E73', 'Protocol pass', '协议通过'),
    ('protocol_fail', '#D55E00', 'Protocol failure', '协议失败'),
    ('geometry_review_required', '#CC79A7', 'Geometry review', '几何复核'),
    ('unsupported', '#999999', 'Unsupported', '不支持'),
    ('timeout', '#E69F00', 'Timeout', '超时'),
    ('runtime_failure', '#0072B2', 'Runtime failure', '运行失败'),
)


def save(fig, path):
    svg = path.parent / (path.name + '.svg')
    fig.savefig(svg, bbox_inches='tight', metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    fig.savefig(path.parent / (path.name + '.png'), dpi=160, bbox_inches='tight')
    plt.close(fig)


def figures(report, output, zh):
    suffix = '.zh-CN' if zh else ''
    if zh:
        font_manager.findfont('Noto Sans CJK SC', fallback_to_default=False)
    plt.rcParams.update({'font.family': 'Noto Sans CJK SC' if zh else 'DejaVu Sans',
                         'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.hashsalt': 'dexlab-d03',
                         'axes.unicode_minus': False})
    cohorts = report['cohorts']
    fig, ax = plt.subplots(figsize=(10, 5.6), layout='constrained')
    left = np.zeros(len(cohorts))
    for key, color, en, cn in OUTCOMES:
        counts = np.array([c['counts'].get(key, 0) for c in cohorts])
        if not counts.any():
            continue
        widths = counts / np.array([c['count'] for c in cohorts]) * 100
        ax.barh(range(len(cohorts)), widths, left=left, color=color, label=cn if zh else en)
        for i, (width, count) in enumerate(zip(widths, counts, strict=True)):
            if count and width > 6:
                ax.text(left[i] + width / 2, i, str(count), ha='center', va='center', color='white', fontweight='bold')
        left += widths
    ax.set_yticks(range(len(cohorts)), [f"{LABELS[c['id']][int(zh)]}  (N={c['count']})" for c in cohorts])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('各固定批次内占比 (%)；块内数字为记录数' if zh else 'Share within each frozen cohort (%); labels are record counts')
    ax.set_title('历史重评：协议结果分开报告，不作引擎精度排名' if zh else 'Historical rescoring: separate protocols, no engine accuracy ranking', pad=38)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1), ncols=2, frameon=False, fontsize=9)
    save(fig, output / ('outcomes' + suffix))

    rows = [r for r in report['records'] if r['cohort'] == 'apple-regression']
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), layout='constrained')
    for ax, metric, title, limit in zip(axes, ('apple.native_depth', 'apple.wrist_translation'),
                                       (('原生接触重叠', 'Native contact overlap'), ('相对腕部位移', 'Wrist-relative displacement')), (1, 2), strict=True):
        failure_label_used = False
        for profile, color, marker in (('mujoco', '#0072B2', 'o'), ('superdex', '#D55E00', 's')):
            selected = [r for r in rows if r['profile'] == profile]
            values = [r['metrics'][metric]['value'] * 1000 for r in selected]
            ax.plot(range(len(values)), values, marker=marker, color=color, linewidth=1, label=profile)
            failed = [i for i, row in enumerate(selected) if row['outcome'] != 'protocol_pass']
            if failed:
                label = None if failure_label_used else ('完整协议失败' if zh else 'Full protocol failed')
                ax.scatter(failed, [values[i] for i in failed], marker='x', color='#222222', s=85, linewidth=1.6, zorder=5, label=label)
                failure_label_used = True
        ax.axhline(limit, color='#555555', linestyle='--', linewidth=1)
        ax.set_yscale('log')
        ax.set_xticks(range(10), [f'{i:03d}' for i in range(10)], fontsize=9)
        ax.set_xlabel('冻结场景编号' if zh else 'Frozen scenario index')
        ax.set_ylabel('mm（对数坐标）' if zh else 'mm (log scale)')
        ax.set_title(title[0] if zh else title[1])
        ax.legend(frameon=False, fontsize=9)
        ax.grid(axis='y', alpha=.2)
    fig.suptitle('参数各自固定；虚线为原协议阈值；位移不是材料滑移' if zh else 'Separately fixed profiles; dashed = existing limits; displacement is not material slip', fontsize=11)
    save(fig, output / ('apple-metrics' + suffix))


def markdown(report, output, zh):
    suffix = '.zh-CN' if zh else ''
    defs = json.loads((ROOT / 'docs/evidence/metrics.json').read_text())
    selection = json.loads((ROOT / 'docs/evidence/cohorts.json').read_text())
    total = len(report['records'])
    robot = next(r for r in report['records'] if r['cohort'] == 'robot-cloth')
    frames = robot['coverage']['samples']
    intrusion = int(robot['metrics']['robot_cloth.intrusion_frames']['value'])
    depth = robot['metrics']['robot_cloth.table_depth']['value'] * 1000
    text = [
        '# 历史重评：统一指标与证据边界（D03）' if zh else '# Historical rescoring: metrics and evidence boundaries (D03)',
        '', '[English](README.md) | [简体中文](README.zh-CN.md)', '',
        f'**结论：七个固定批次共 {total} 条记录按当前评分器重新读取；旧夹布“通过”应列为几何复核，其余批次的协议结果见下表。没有实测精度或等预算引擎排名。**' if zh else
        f'**Conclusion: {total} records from seven frozen cohorts are read again with current scorers. The old robot-cloth pass requires geometry review. Other cohort outcomes are below. This is neither measured accuracy nor an equal-budget engine ranking.**', '',
        '此报告为历史离线重评，不是新一轮动力学实验；发布验收见 [GitHub Releases](https://github.com/huangkiki/Dexlab/releases)。保持原控制器、引擎与物理阈值，原始输入逐文件校验，分析前后哈希必须一致。' if zh else
        'This is offline historical rescoring, not a new dynamics experiment; release validation is recorded in [GitHub Releases](https://github.com/huangkiki/Dexlab/releases). Controllers, engines and physical limits are unchanged. Every declared raw input is hash-checked before and after analysis.', '',
        '## 结果与结论' if zh else '## Results and conclusions', '',
        f'![{"各批次结果" if zh else "Cohort outcomes"}](outcomes{suffix}.svg)', '',
        '| 批次 | N | 历史通过 | 当前协议通过 | 协议失败 | 几何复核 | 不支持 | 超时 / 运行失败 |' if zh else
        '| Cohort | N | Historical passes | Current protocol passes | Protocol failures | Geometry review | Unsupported | Timeout / runtime failure |',
        '|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for c in report['cohorts']:
        count=c['counts']
        text.append(f"| {LABELS[c['id']][int(zh)]} | {c['count']} | {c['historical_counts'].get('protocol_pass',0)} | {count.get('protocol_pass',0)} | {count.get('protocol_fail',0)} | {count.get('geometry_review_required',0)} | {count.get('unsupported',0)} | {count.get('timeout',0)} / {count.get('runtime_failure',0)} |")
    text += ['',
        '分母属于不同任务和开发阶段，不能相加形成总成功率。基本接触、静态和瞬态批次是开发配置，不是随机成功率测试。PhysX 外力拉伸的 4 个“不支持”保留在全部场景分母中，不计作通过。未完成的苹果 100 场景测试没有并入这 20 次回归。' if zh else
        'Denominators belong to different tasks and development stages: do not pool them into an overall success rate. Contact/static/transient cohorts are development configurations, not random trials. Four unsupported PhysX force-driven cloth cases remain in the full denominator. The unfinished 100-scenario apple evaluation is not merged into this 20-run regression.', '',
        '选取的是预先列明的完整发布批次，不是仓库全部历史运行。基础接触原始发布包还保留 3 次初始化失败；其它早期开发、资格检查和细化记录仍在各原报告中，本表没有重新评分这些记录。' if zh else
        'The selection comprises complete, predeclared published cohorts, not every historical run. The contact release also retains three initialization failures; other early development, qualification and refinement records remain in their original reports and are not rescored in this table.', '',
        f'![{"逐场景抓梗指标" if zh else "Per-scenario grasp metrics"}](apple-metrics{suffix}.svg)', '',
        '苹果图表中的两条曲线对应各自固定参数。原生重叠与相对腕部位移分面显示；1 mm / 2 mm 虚线沿用旧验收阈值，× 表示整体验收失败。位移很小也可能是根本没有提起苹果，必须结合离桌、支撑等完整检查。两条原生重叠曲线依赖不同接触算法，不能据此宣称同一表面的物理精度排名。材料点累计滑移所有记录均为未知。' if zh else
        'Apple curves use separately fixed parameters. Native overlap and wrist-relative translation have separate panels; 1 mm / 2 mm dashed lines are unchanged limits and crosses mark full-protocol failures. Very small displacement can occur when the apple was never lifted: clearance and support checks still apply. Native overlap depends on each contact algorithm and is not a common-surface accuracy ranking. Accumulated material-point slip is unavailable for every record.', '',
        f'机器人夹布：{frames} 个 25 Hz 保存帧中 {intrusion} 帧进入桌体，最大内部深度 {depth:.2f} mm；旧协议通过并不消除几何问题。该深度按零厚度三角面与厚 6 mm 的桌体计算，不能与 SDF 原生距离或竖直穿透合并比较。物理修复由 [#32](https://github.com/huangkiki/Dexlab/issues/32) 跟进。' if zh else
        f'Robot cloth: {intrusion} of {frames} saved 25 Hz frames intersect the table, with {depth:.2f} mm maximum interior depth. Passing the old protocol does not remove this geometry problem. This zero-thickness-triangle diagnostic against a 6 mm table is distinct from native SDF distance and vertical penetration. Physical repair is tracked in [#32](https://github.com/huangkiki/Dexlab/issues/32).', '',
        '## 测量契约' if zh else '## Measurement contract', '',
        '每条结果包含固定批次与场景 ID、历史/当前状态、失败检查、原始文件 SHA-256、当前评分器 SHA-256 和采样覆盖。数值统一为 SI；图中仅将米显式换算为毫米。定义与近似见下表及 [metrics.json](metrics.json)。未观测量为 `null`，不填零、不跨缺测帧插值。场景没有球体、地面或固定边界时，对应指标为 `not_applicable`，不是测得零。' if zh else
        'Each row contains frozen cohort/record IDs, historical/current outcomes, failed checks, raw-file SHA-256 hashes, current scorer SHA-256 hashes and sampling coverage. Values use SI; plots explicitly convert metres to millimetres. Definitions and approximations are below and in [metrics.json](metrics.json). Unobserved quantities are null, never zero-filled or interpolated across gaps. Absent obstacles or pinned boundaries are not_applicable, not observed zero.', '',
        '| 指标 ID | 单位 | 定义与边界 |' if zh else '| Metric ID | Unit | Definition and boundary |', '|---|---|---|',
    ]
    for key, value in defs.items():
        description = value['description_zh'] if zh else value['definition']+'. '+value['approximation']
        text.append(f"| `{key}` | {value['unit']} | {description} |")
    text += ['',
        '时间覆盖：抓梗为全程逐物理步记录，保持窗口 `[11,14)` 秒；基础布料与接触包括未步进初始帧；夹布表面诊断只有 25 Hz，夹持检查使用 100 Hz trace 的 `[2,hold_end)` 秒。布料自交另按 `surface_coverage` 的实际抽样间隔报告，不宣称帧间连续无碰撞。力使用被测物体世界系原生合力，并与对应步的速度增量对齐；不把驱动目标作为测得的力。' if zh else
        'Coverage: apple states are recorded every physics step, with hold [11,14) s; basic cloth/contact include the unstepped initial state. Robot-cloth surface diagnostics cover 25 Hz only; hold checks use the 100 Hz trace in [2,hold_end) s. Cloth self-crossings retain their actual sampled surface_coverage, without continuous-time collision claims. Forces are native world-frame resultants on the tested body aligned with the corresponding velocity increment; drive targets are not measured force.', '',
        '数值损坏与物理失败分开：缺文件、哈希改变、重复/截断时间戳、矛盾检查会让报告生成失败，不会缩小分母或改记为物理失败。原生警告、稳定性/保留失败等完整运行结果保留为协议失败。不支持、超时、运行错误保持独立状态。' if zh else
        'Evidence errors are separate from physical failures: missing files, hash changes, duplicate/truncated times and contradictory checks abort report generation rather than shrink the denominator or become physical failures. Complete runs with native warnings or retention/stability failures remain protocol failures. Unsupported operations, timeouts and runtime errors retain separate states.', '',
        '## 两条评估轨道' if zh else '## Two evaluation tracks', '',
        '| 轨道 | 本次状态 |' if zh else '| Track | Current status |', '|---|---|',
        '| 对实测物理参考的误差 | 未提供实测力、材料响应或真机轨迹，未知；20 kN/m + 40 N·s/m 是合成工程目标。 |' if zh else '| Error against measured physical references | Unavailable: no measured forces, material responses or hardware trajectories. 20 kN/m + 40 N·s/m is a synthetic engineering target. |',
        '| 等预算调参后的任务性能 | 历史调参预算不等，不能称等预算 benchmark；仅报告各固定配置及协议结果。 |' if zh else '| Task performance after equal-budget tuning | Historical tuning budgets are unmatched. Only fixed-profile protocol outcomes are reported. |', '',
        '当前不输出速度排行：准备、物理步进、控制/记录、渲染、归档应分别计时，旧记录未满足统一隔离条件。完整能量收支、材料滑移、真实摩擦和驱动辨识仍缺证据。' if zh else
        'No speed ranking is exported. Preparation, physics stepping, control/recording, rendering and archival require separate timing; historical runs lack uniform isolation. Full energy accounting, material slip, real friction and drive identification remain unsupported by these records.', '',
        '## 数据、代码与复算' if zh else '## Data, code and reproduction', '',
        '[全部结果与逐文件哈希](historical-v1.json) · [逐指标 CSV](metrics.csv) · [冻结批次选择](cohorts.json) · [离线评分代码](../../src/dexlab/evidence_report.py) · [图表生成代码](../../scripts/render_evidence_report.py)' if zh else
        '[All rows and per-file hashes](historical-v1.json) · [Tidy metric CSV](metrics.csv) · [Frozen cohort selection](cohorts.json) · [Offline scorer](../../src/dexlab/evidence_report.py) · [Plot generator](../../scripts/render_evidence_report.py)', '',
        '补齐的两组公开包使用显式脱敏副本及冻结历史评分器；106 条记录完整复算一致。下载目录、变换及限制见 [独立复算说明](PUBLIC-ARCHIVE.zh-CN.md)。原历史报告保留当时的可用性记录，当前下载位置以本表为准。' if zh else
        'The two completed public cohorts use explicit metadata projections and the frozen historical scorer; all 106 records reproduce exactly. See [portable reproduction](PUBLIC-ARCHIVE.md) for layout, transformations and limits. The immutable historical report retains its original availability snapshot; this table gives current download locations.', '',
        '| 批次 | 完整原始记录 |' if zh else '| Cohort | Complete raw records |', '|---|---|',
    ]
    for c in selection['cohorts']:
        url=c['raw_source']['url']
        label=('[发布包]('+url+')' if zh else '[Release archive]('+url+')') if url else ('本地保留；当前没有公开的完整原始包，JSON 不能替代原始轨迹' if zh else 'Preserved locally; no public complete raw archive. JSON does not replace raw trajectories.')
        text.append(f"| {LABELS[c['id']][int(zh)]} | {label} |")
    text += ['',
        '两组公开脱敏批次请使用上方包内独立复算脚本。包内复制的批次记录绑定公开哈希；仓库原记录刻意保留私有原件哈希，不能用于混合校验脱敏副本和原件。其余五组发布包仍沿用各自的原始记录与评分来源。以下命令只从不可变的 208 条记录报告重新生成图表，不重新评分原始数据。' if zh else
        'For the two public projected cohorts, use the bundled standalone reproducer above. Its copied receipts bind public hashes; the original tracked receipts deliberately retain private-original hashes and cannot validate a mixture of projected and original files. The other five archives retain their original receipt/scorer provenance. The following command regenerates plots from the immutable 208-record report; it does not rescore raw data.', '',
        '```bash', '.venv/bin/python scripts/render_evidence_report.py docs/evidence/historical-v1.json --output /tmp/evidence-report', '```', '',
        '开发者工具 `dexlab.evidence_report` 面向未脱敏原始输入及兼容的历史模型运行时。当前评分器可能要求旧录制不存在的证据；复现已发表历史值应使用包内固定源码，不能补造缺失证据。绘图另需安装 `matplotlib`。' if zh else
        'The developer-facing `dexlab.evidence_report` tool requires unredacted original inputs and a compatible recorded-model runtime. Current scorers may require evidence absent from old recordings; use the pinned bundled sources to reproduce published historical values. Missing evidence remains missing. Plotting additionally requires matplotlib.', '',
        '复算会载入保存的 MuJoCo 模型作几何/FK 分析；不会调用动力学积分。评分版本由源文件哈希集合精确绑定，而不只依赖包版本号。图表生成成功不代表新代码已通过发布门禁。' if zh else
        'Rescoring loads saved MuJoCo models for geometry/FK analysis but never integrates dynamics. Scorer identity is bound to source-file hashes, not just a package version. Generating plots does not establish release-gate completion.', '',
        '[任务与参数来源](../inventory/README.zh-CN.md) · [研究方法](../research-focus.zh-CN.md) · [首页](../../README.md)' if zh else
        '[Task and parameter provenance](../inventory/README.md) · [Research methods](../research-focus.md) · [Homepage](../../README.en.md)', '',
    ]
    (output / ('README'+suffix+'.md')).write_text('\n'.join(text))


def render(report_path, output):
    report=json.loads(report_path.read_text())
    if report['schema'] != 'historical-evidence-v1':
        raise ValueError('Unknown report schema')
    output.mkdir(parents=True, exist_ok=True)
    definitions = json.loads((ROOT / 'docs/evidence/metrics.json').read_text())
    with (output / 'metrics.csv').open('w') as stream:
        writer=csv.writer(stream, lineterminator='\n')
        writer.writerow(('cohort','record','profile','historical_outcome','outcome','metric','unit','value','status'))
        for row in report['records']:
            for key, value in row['metrics'].items():
                writer.writerow((row['cohort'],row['id'],row['profile'],row['historical_outcome'],row['outcome'],key,definitions[key]['unit'],value['value'],value['status']))
    for zh in (False, True):
        figures(report, output, zh)
        markdown(report, output, zh)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.suffix in ('.svg', '.png', '.csv', '.md')}
    receipt = {'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(), 'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'matplotlib_version': matplotlib.__version__, 'files': hashes}
    (output/'plot-provenance.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    render(args.report, args.output)
