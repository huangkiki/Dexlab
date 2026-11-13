"""Publish pinned Sim Learning courses through the existing Sphinx reader."""

import hashlib
import html
import json
import posixpath
import re
import shutil
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'docs/learning'
NAMES = {'sim': 'Sim Learning', 'mujoco': 'MuJoCo', 'superdex': 'SuperDex',
         'genesis': 'Genesis', 'newton': 'Newton Physics', 'physx': 'PhysX', 'drake': 'Drake'}


def load_sources():
    sources = json.loads((SOURCES / 'sources.json').read_text())
    for source in sources:
        for path, expected in source['files'].items():
            actual = hashlib.sha256((SOURCES / source['slug'] / path).read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f'Course snapshot changed: {source["slug"]}/{path}')
    return sources


def entry(source):
    return 'README.md' if source['slug'] == 'sim' else 'docs/curriculum.md'


def rewrite_url(url, source, path, sources):
    """Localize reading links; retain immutable citations and source-code links."""
    parts = urlsplit(url)
    if not parts.path:
        return url
    target = source
    target_path = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(parts.path)))
    if parts.netloc or parts.scheme:
        if parts.netloc != 'github.com':
            return url
        segments = unquote(parts.path).strip('/').split('/')
        if segments == ['huangkiki', 'Dexlab'] or segments == ['huangkiki', 'DexLab']:
            return posixpath.relpath('index.md', posixpath.dirname(f'learn/{source["slug"]}/{path}'))
        target = next((item for item in sources if item['repo'] == '/'.join(segments[:2])), None)
        if target is None:
            return url
        if len(segments) == 2:
            target_path = entry(target)
        elif len(segments) >= 4 and segments[2] in ('blob', 'tree'):
            if segments[3] not in ('main', target['revision']):
                return url  # A historical citation must not silently point to a newer text.
            target_path = '/'.join(segments[4:])
        else:
            return url
    if target_path not in target['files']:
        candidate = posixpath.join(target_path, 'README.md')
        if candidate in target['files']:
            target_path = candidate
        else:
            return f'https://github.com/{target["repo"]}/blob/{target["revision"]}/{quote(target_path)}' + (
                f'#{parts.fragment}' if parts.fragment else '')
    destination = f'{target["slug"]}/{target_path}'
    relative = posixpath.relpath(destination, posixpath.dirname(f'{source["slug"]}/{path}'))
    return urlunsplit(('', '', quote(relative), parts.query, parts.fragment))


def prepare_markdown(text, source, path, sources):
    """Adapt GitHub Markdown syntax, leaving prose and code examples intact."""
    def rewrite(match):
        return match[1] + rewrite_url(match[2], source, path, sources)

    def prose(chunk):
        chunk = re.sub(r'(!?\[[^\]\n]*\]\()([^\s)]+)', rewrite, chunk)
        chunk = re.sub(r'(?m)^(\[[^\]\n]+\]:\s*)(\S+)', rewrite, chunk)
        chunk = re.sub(r'((?:href|src)=["\'])([^"\']+)', rewrite, chunk)
        chunk = re.sub(r'(?m)^\\\[\s*\n([\s\S]*?)^\\\]\s*$', lambda m: '$$\n' + m[1].rstrip() + '\n$$\n', chunk)
        chunk = re.sub(r'\\\(([^\n]+?)\\\)', lambda m: '$' + m[1] + '$', chunk)
        return re.sub(r'\$`([^`\n]+)`\$', r'$\1$', chunk)

    # Do not rewrite paths or dollar syntax inside executable examples.
    chunks = re.split(r'(?m)(^```[^\n]*\n[\s\S]*?^```\s*$|^~~~[^\n]*\n[\s\S]*?^~~~\s*$)', text)
    def fence(chunk):
        if chunk.startswith('```mermaid\n'):
            diagram = chunk.removeprefix('```mermaid\n').rstrip().removesuffix('```')
            return '```{raw} html\n<pre class="mermaid">' + html.escape(diagram) + '</pre>\n```'
        return re.sub(r'^```math\s*\n', '```{math}\n', chunk)

    return ''.join(fence(chunk) if i % 2 else prose(chunk) for i, chunk in enumerate(chunks))


def prepare_courses(language_dir):
    sources = load_sources()
    output = language_dir / 'learn'
    if output.exists():
        shutil.rmtree(output)
    # MyST treats existing non-document files as downloadable assets.
    copy_course_assets(language_dir, sources)
    chinese = language_dir.name == 'zh'
    for source in sources:
        pages = [path for path in source['files'] if path.endswith('.md')]
        for path in pages:
            raw = (SOURCES / source['slug'] / path).read_text()
            body = prepare_markdown(raw, source, path, sources)
            if not re.search(r'^# ', body, flags=re.M):
                body = f'# {NAMES[source["slug"]]}\n\n' + body
            parent = posixpath.dirname(f'learn/{source["slug"]}/{path}')
            home = posixpath.relpath('learning.md', parent)
            directory = posixpath.relpath(f'learn/{source["slug"]}/{entry(source)}', parent)
            source_url = f'https://github.com/{source["repo"]}/blob/{source["revision"]}/{path}'
            navigation = (f'[学习首页]({home}) · [{NAMES[source["slug"]]} 目录]({directory})' if chinese else
                          f'[Learning home]({home}) · [{NAMES[source["slug"]]} contents]({directory})')
            note = '' if chinese else '\n\n*Course text is primarily Chinese, with English terminology and summaries. The original content is preserved.*'
            body = re.sub(r'(?m)^(# .+)$', lambda m: m[0] + '\n\n' + navigation + note, body, count=1)
            label = '课程来源' if chinese else 'Course source'
            body += f'\n\n[{label} · GitHub]({source_url}) · [{"许可" if chinese else "License"}]({posixpath.relpath("LICENSE", posixpath.dirname(path))})\n'
            if path == entry(source):
                # Follow the authored course sequence before reference/maintenance pages.
                linked = re.findall(r'\]\(([^)#]+\.md)(?:#[^)]*)?\)', raw)
                ordered = ['docs/guide.md'] + [posixpath.normpath(posixpath.join(posixpath.dirname(path), item)) for item in linked] + pages
                ordered = list(dict.fromkeys(item for item in ordered if item in pages and item != path))
                others = [posixpath.relpath(item, posixpath.dirname(path))[:-3] for item in ordered]
                body += '\n```{toctree}\n:hidden:\n:maxdepth: 1\n\n' + '\n'.join(others) + '\n```\n'
            target = output / source['slug'] / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
    return sources


def copy_course_assets(output, sources):
    for source in sources:
        for path in source['files']:
            if not path.endswith('.md'):
                target = output / 'learn' / source['slug'] / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCES / source['slug'] / path, target)
