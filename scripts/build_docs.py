"""Build both public documentation languages without installing DexLab."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def preserve_homepage_anchors(html):
    """Keep the four published Chinese homepage anchors after adding sections."""
    # Sphinx's anonymous id1/id2/... change when sections are inserted.
    for number in range(1, 5):
        html = html.replace(f'<span id="id{number}"></span>', '')
    html = re.sub(r'(id="|href="#)(id\d+)(")', r'\1visual-\2\3', html)
    for number, target in enumerate(('research-findings', 'research-diagnosis', 'research-selection', 'research-scope'), 1):
        section = f'<section id="{target}">'
        if html.count(section) != 1:
            raise ValueError(f'Missing homepage compatibility target: {target}')
        html = html.replace(section, section + f'<span id="id{number}"></span>')
    return html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/_build/html')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'scripts/task_coverage.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/research_experience.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_visual_research.py'), '--check'], check=True)
    output = args.output.resolve()
    source = ROOT / 'docs/site'
    for directory, language, route in [('zh', 'zh_CN', 'zh-cn'), ('en', 'en', 'en')]:
        subprocess.run([
            sys.executable, '-m', 'sphinx', '-W', '--keep-going', '-n', '-b', 'html',
            '-c', str(source), str(source / directory), str(output / route / 'latest'),
        ], env={**os.environ, 'DEXLAB_DOCS_LANGUAGE': language}, check=True)
        if directory == 'zh':
            homepage = output / route / 'latest/index.html'
            homepage.write_text(preserve_homepage_anchors(homepage.read_text()))
    (output / 'index.html').write_text(
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=zh-cn/latest/index.html">'
        '<title>DexLab 文档</title></head><body>'
        '<a href="zh-cn/latest/index.html">中文文档</a> · '
        '<a href="en/latest/index.html">English documentation</a></body></html>\n'
    )
    (output / '.nojekyll').touch()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (output / 'build-info.json').write_text(json.dumps({'source_revision': revision}) + '\n')



if __name__ == '__main__':
    main()
