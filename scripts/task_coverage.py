#!/usr/bin/env python3
"""Validate the versioned task inventory and render the four public tables."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKERS = ('<!-- task-coverage:start -->', '<!-- task-coverage:end -->')
ENGINES = ('MuJoCo', 'SuperDex', 'Genesis', 'Newton Physics', 'PhysX', 'Drake')
STATES = {
    'passed': ('完整通过', 'Passed'),
    'partial': ('部分通过', 'Partial'),
    'failed': ('失败', 'Failed'),
    'not-run': ('未运行', 'Not run'),
    'blocked': ('接入受阻', 'Blocked'),
    'unsupported': ('不支持', 'Unsupported'),
}
RELIABILITY_CHECKS = (
    'positive_cases', 'negative_controls', 'independent_physics',
    'frozen_holdout', 'equal_tuning_budget', 'provenance',
)


def evidence(root, reference):
    """Read only an in-repository, content-addressed evidence file."""
    path = (root / reference['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Evidence must be an existing repository file')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError(f'Evidence hash changed: {reference["path"]}')
    return data


def cloth_counts(bundle, expected_cases):
    """Recount frozen per-case summaries, not a trajectory revalidation."""
    expected = {(solver, case) for solver in bundle['profiles'] for case in expected_cases}
    seen = set()
    counts = {}
    for record in bundle['records']:
        job = record['job']
        key = job['solver'], job['case']
        if key not in expected or key in seen:
            raise ValueError(f'Unexpected or duplicate cloth case: {key}')
        seen.add(key)
        task = expected_cases[job['case']]
        passed, total = counts.get((job['solver'], task), (0, 0))
        verdict = record['summary']['protocol_checks_passed']
        if type(verdict) is not bool or verdict != job['protocol_checks_passed']:
            raise ValueError('Contradictory cloth summary verdict')
        if verdict and (job['status'] != 'completed' or job['exit_code'] != 0):
            raise ValueError('Incomplete execution cannot count as a pass')
        counts[job['solver'], task] = passed + int(verdict), total + 1
    if seen != expected:
        raise ValueError('Missing frozen cloth cases; omissions must not improve coverage')
    return counts


def incline_counts(bundle, protocol):
    """Recount the frozen qualification, including the required negative."""
    cases = {case['id']: case for case in protocol['cases']}
    seen, passed, total, negatives = set(), 0, 0, []
    for result in bundle['results']:
        name = result['id']
        if name not in cases or name in seen or type(result['record_valid']) is not bool:
            raise ValueError('Missing, duplicate or invalid incline evidence')
        seen.add(name)
        negative = cases[name].get('negative_no_floor', False)
        if not result['checks'] or any(type(value) is not bool for value in result['checks'].values()):
            raise ValueError('Malformed incline checks')
        if (result['expected_negative'] != negative or type(result['passed']) is not bool
                or result['passed'] != all(result['checks'].values())):
            raise ValueError('Contradictory incline verdict')
        if not result['record_valid']:
            if result['passed'] or not result.get('failure'):
                raise ValueError('Invalid evidence cannot qualify a positive or a negative')
        if negative:
            if result['passed']:
                raise ValueError('Negative control was accepted')
            negatives.append(result['record_valid'])
        else:
            passed += int(result['passed'])
            total += 1
    if seen != set(cases) or not negatives or not total:
        raise ValueError('Incomplete incline qualification')
    return passed, total, all(negatives)


def reliable_tasks(manifest, root):
    """Union task types across qualified configs; never add repeats or paths."""
    result = {engine: set() for engine in ENGINES}
    for row in manifest['rows']:
        if row['cohort'] != manifest['current_protocol']:
            continue
        for task, cell in row['cells'].items():
            if 'acceptance' not in cell:
                continue
            report = json.loads(evidence(root, cell['acceptance']))
            identity = {key: row[key] for key in ('engine', 'solver', 'runtime_path', 'version')}
            identity.update(protocol_id=row['cohort'], task_type=task)
            if any(report.get(key) != value for key, value in identity.items()):
                raise ValueError('Acceptance identity does not match the coverage cell')
            if cell['state'] != 'passed' or any(
                report.get('checks', {}).get(key) is not True for key in RELIABILITY_CHECKS
            ):
                raise ValueError('Reliable coverage requires every preregistered acceptance check')
            result[row['engine']].add(task)
    return result


def load_inventory(root=ROOT):
    manifest = json.loads((root / 'docs/task-coverage.json').read_text())
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported task coverage schema')
    tasks = manifest['tasks']
    if len({task['id'] for task in tasks}) != len(tasks):
        raise ValueError('Duplicate task type')
    task_ids = {task['id'] for task in tasks}
    task_groups = {task['id']: task['group'] for task in tasks}
    group_ids = {group['id'] for group in manifest['groups']}
    if set(task_groups.values()) != group_ids:
        raise ValueError('Every task group must have a rendered table')
    cohorts = manifest['cohorts']
    counts = {}
    for name, cohort in cohorts.items():
        if 'cloth_summaries' in cohort:
            bundle = json.loads(evidence(root, cohort['cloth_summaries']))
            counts[name] = cloth_counts(bundle, cohort['expected_cases'])
        if 'incline_score' in cohort:
            bundle = json.loads(evidence(root, cohort['incline_score']))
            protocol = json.loads(evidence(root, cohort['protocol']))
            if bundle['protocol_sha256'] != cohort['protocol']['sha256']:
                raise ValueError('Incline protocol binding changed')
            counts[name] = {(cohort['profile'], 'incline'): incline_counts(bundle, protocol)}
    rows_seen = set()
    for row in manifest['rows']:
        identity = tuple(row[key] for key in ('engine', 'solver', 'runtime_path', 'version', 'cohort'))
        if identity in rows_seen or row['engine'] not in ENGINES or row['cohort'] not in cohorts:
            raise ValueError('Duplicate or unknown configuration/cohort')
        rows_seen.add(identity)
        if not row['groups'] or not set(row['groups']) <= group_ids:
            raise ValueError('Configuration references an unknown table')
        if set(row['cells']) != task_ids:
            raise ValueError('Every configuration must account for every fixed task type')
        for task, cell in row['cells'].items():
            if cell['state'] not in STATES:
                raise ValueError('Unknown coverage state')
            if cell['state'] != 'not-run' and task_groups[task] not in row['groups']:
                raise ValueError('An observed or blocked cell must not be hidden from public tables')
            if not cell.get('reference'):
                raise ValueError('Every state needs evidence or a recovery issue')
            if not cell['reference'].startswith('https://github.com/huangkiki/Dexlab/'):
                raise ValueError('Coverage references must identify repository evidence or issues')
            if 'counts_from' in cell:
                count = counts[row['cohort']][row['profile'], cell['counts_from']]
                passed, total = count[:2]
                negative_valid = count[2] if len(count) == 3 else True
                state = 'passed' if passed == total and negative_valid else 'partial' if passed else 'failed'
                if cell['state'] != state:
                    raise ValueError('Declared state disagrees with frozen records')
                cell['count'] = f'{passed}/{total}'
                if not negative_valid:
                    cell['negative_valid'] = False
            if cell['state'] in ('passed', 'partial', 'failed', 'unsupported'):
                if 'evidence' not in cell:
                    raise ValueError('Observed and unsupported claims require hashed evidence')
                evidence(root, cell['evidence'])
    reliable_tasks(manifest, root)
    return manifest


def render(manifest, language, root=ROOT):
    zh = language == 'zh'
    index = 0 if zh else 1
    lines = [MARKERS[0], '']
    lines += [
        '状态：完整通过 / 部分通过 / 失败 / 未运行 / 接入受阻 / 不支持。点击单元格查看证据或恢复条件。'
        if zh else 'States: passed / partial / failed / not run / blocked / unsupported. Cells link to evidence or recovery conditions.',
        '',
        '**历史协议分别展示；通过只表示该协议的验收。** 新协议可靠覆盖须完成正例、负例、独立物理评分和冻结留出验证，并保持相同调优预算。'
        if zh else '**Historical protocols remain separate; a pass applies only to its protocol.** Reliable coverage under the new protocol requires positive and negative cases, independent physics scoring, frozen holdouts and equal tuning budgets.',
        '',
    ]
    for group in manifest['groups']:
        tasks = [task for task in manifest['tasks'] if task['group'] == group['id']]
        lines += ['### ' + group[language], '']
        headers = ['引擎核心 / solver / 路径 / 版本 / 批次' if zh else 'Core / solver / path / version / cohort']
        headers += [task[language] for task in tasks]
        lines += ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        for row in manifest['rows']:
            if group['id'] not in row['groups']:
                continue
            values = [f'**{row["engine"]} · {row["solver"]}**<br>'
                      f'{row["runtime_path"]} · {row["version"]}<br>{row["cohort"]}']
            for task in tasks:
                cell = row['cells'][task['id']]
                label = STATES[cell['state']][index]
                if 'count' in cell:
                    label += ' ' + cell['count']
                if cell.get('negative_valid') is False:
                    label += '；负例无效' if zh else '; invalid negative'
                values.append(f'[{label}]({cell["reference"]})')
            lines.append('| ' + ' | '.join(values) + ' |')
        lines.append('')
    qualified = reliable_tasks(manifest, root)
    if not any(qualified.values()):
        lines += ['**新协议可靠覆盖：尚未验收。** 这不表示已有引擎不能完成任务；历史结果不自动追认为新协议结果。'
                  if zh else '**Reliable coverage under the new protocol: not yet qualified.** Existing capabilities remain valid within their original protocols; historical runs are not retroactively admitted.', '']
    else:
        lines += [('可靠任务类型并集：' if zh else 'Union of qualified task types: ') +
                  '; '.join(f'{engine}: {len(tasks)}' for engine, tasks in qualified.items()), '']
    lines += [
        '布料数字从 105 份历史摘要逐例重算，不等于重新评分完整轨迹。Featherstone 布料使用半隐式粒子核；预折叠下落不是主动折布。缺少实验不等于不支持。'
        if zh else 'Cloth counts are recomputed from 105 historical summaries, not rescored trajectories. Featherstone cloth uses semi-implicit particle kernels; folded drop is not active folding. Missing runs do not establish lack of support.',
        '',
        '[清单与生成规则](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.zh-CN.md)' if zh else
        '[Inventory and generation rules](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.md)',
        '', MARKERS[1],
    ]
    return '\n'.join(lines)


def update(root=ROOT, check=False):
    manifest = load_inventory(root)
    stale = []
    for filename, language in (('README.md', 'zh'), ('README.en.md', 'en'),
                               ('docs/site/zh/index.md', 'zh'), ('docs/site/en/index.md', 'en')):
        path = root / filename
        source = path.read_text()
        if any(source.count(marker) != 1 for marker in MARKERS):
            raise ValueError(f'Expected exactly one generated block: {filename}')
        before, rest = source.split(MARKERS[0])
        _, after = rest.split(MARKERS[1])
        updated = before + render(manifest, language, root) + after
        if updated != source:
            stale.append(filename)
            if not check:
                path.write_text(updated)
    if check and stale:
        raise ValueError('Stale coverage tables: ' + ', '.join(stale))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    update(check=parser.parse_args().check)
