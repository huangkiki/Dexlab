"""Build both public documentation languages without installing DexLab."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/_build/html')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'scripts/task_coverage.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/research_experience.py'), '--check'], check=True)
    output = args.output.resolve()
    source = ROOT / 'docs/site'
    for directory, language, route in [('zh', 'zh_CN', 'zh-cn'), ('en', 'en', 'en')]:
        subprocess.run([
            sys.executable, '-m', 'sphinx', '-W', '--keep-going', '-n', '-b', 'html',
            '-c', str(source), str(source / directory), str(output / route / 'latest'),
        ], env={**os.environ, 'DEXLAB_DOCS_LANGUAGE': language}, check=True)
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
