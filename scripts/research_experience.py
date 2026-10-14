"""Validate historical evidence links and render the bilingual research guide."""
import argparse
import json
from pathlib import Path

try:
    from scripts.task_coverage import ROOT, evidence, load_inventory
except ModuleNotFoundError:
    from task_coverage import ROOT, evidence, load_inventory

MARKERS = ('<!-- research-experience:start -->', '<!-- research-experience:end -->')
FIELDS = ('title', 'condition', 'observation', 'explanation', 'advice', 'boundary',
          'first_check', 'starting_point', 'cost')
LABELS = {
    'zh': ('条件', '观察', '解释与证据等级', '建议', '边界', '新场景首先验证', '候选起点', '成本'),
    'en': ('Conditions', 'Observation', 'Explanation and evidence level', 'Advice',
           'Limits', 'First check in a new scene', 'Starting candidate', 'Cost'),
}


def load_experiences(root=ROOT):
    manifest = json.loads((root / 'docs/research-experiences.json').read_text())
    if manifest.get('schema_version') != 1 or not manifest.get('experiences'):
        raise ValueError('Expected versioned, nonempty experience index')
    tasks = {t['id'] for t in load_inventory(root)['tasks']}
    seen = set()
    for row in manifest['experiences']:
        identity = row['id']
        if (not isinstance(identity, str) or not identity or identity in seen
                or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in identity)):
            raise ValueError('Invalid or duplicate experience id')
        seen.add(identity)
        if not row['task_ids'] or not set(row['task_ids']) <= tasks:
            raise ValueError('Experience must reference existing coverage tasks')
        for language in LABELS:
            if set(row[language]) != set(FIELDS) or any(
                not isinstance(v, str) or not v.strip() for v in row[language].values()
            ):
                raise ValueError('Every experience needs complete bilingual research fields')
        if not row['evidence']:
            raise ValueError('Experience needs source evidence')
        for reference in row['evidence']:
            evidence(root, reference)
    return manifest['experiences']


def render(rows, language):
    lines = [MARKERS[0], '']
    for row in rows:
        text = row[language]
        lines += [f'({row["id"]})=', f'## {text["title"]}', '']
        for key, label in zip(FIELDS[1:], LABELS[language]):
            lines += [f'**{label}：** {text[key]}' if language == 'zh'
                      else f'**{label}:** {text[key]}', '']
        links = [f'[{r["path"]}](https://github.com/huangkiki/Dexlab/blob/main/{r["path"]})'
                 for r in row['evidence']]
        lines += [('**证据：** ' if language == 'zh' else '**Evidence:** ') + ' · '.join(links), '']
    lines += [MARKERS[1]]
    return '\n'.join(lines)


def update(root=ROOT, check=False):
    rows = load_experiences(root)
    stale = []
    for language in LABELS:
        path = root / f'docs/site/{language}/experience.md'
        source = path.read_text()
        if any(source.count(m) != 1 for m in MARKERS):
            raise ValueError('Expected one experience block')
        before, rest = source.split(MARKERS[0])
        _, after = rest.split(MARKERS[1])
        updated = before + render(rows, language) + after
        if updated != source:
            stale.append(str(path.relative_to(root)))
            if not check:
                path.write_text(updated)
    if check and stale:
        raise ValueError('Stale experience pages: ' + ', '.join(stale))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    update(check=parser.parse_args().check)
