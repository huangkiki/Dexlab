"""Build both public documentation languages without installing DexLab."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from concept_atlas import prepare_concept_pages
from learning_docs import copy_course_assets, prepare_courses
from paper_sharing import prepare_paper_readers

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/_build/html')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'scripts/task_coverage.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/research_experience.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_visual_research.py'), '--check'], check=True)
    output = args.output.resolve()
    source = ROOT / 'docs/site'
    papers = prepare_paper_readers(source)
    for directory, language, route in [('zh', 'zh_CN', 'zh-cn'), ('en', 'en', 'en')]:
        destination = output / route / 'latest'
        prepare_concept_pages(source / directory)
        courses = prepare_courses(source / directory)
        subprocess.run([
            sys.executable, '-m', 'sphinx', '-W', '--keep-going', '-n', '-b', 'html',
            '-c', str(source), str(source / directory), str(destination),
        ], env={**os.environ, 'DEXLAB_DOCS_LANGUAGE': language}, check=True)
        copy_course_assets(destination, courses)
        for path, html in papers.items():
            (destination / path).write_text(html, encoding='utf-8')
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
