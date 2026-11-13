"""Refresh course snapshots from GitHub; normal documentation builds stay offline.

With no arguments, restore the revisions in sources.json. Use --latest to
explicitly refresh selected repositories, then review and publish the diff.
"""

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from learning_docs import SOURCES, NAMES


def course_file(path):
    return path.name != 'AGENTS.md' and (
        path.suffix in ('.md', '.svg', '.png', '.jpg') or path.name in ('LICENSE', 'NOTICE'))


def sync(source, latest=False):
    repo = source['repo']
    revision = source['revision']
    if latest:
        revision = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/commits/main']))['sha']
    archive = subprocess.check_output(['gh', 'api', f'repos/{repo}/tarball/{revision}'])
    with tempfile.TemporaryDirectory(dir=SOURCES) as staging:
        folder = Path(staging)
        files = {}
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
            for member in bundle.getmembers():
                path = PurePosixPath(*PurePosixPath(member.name).parts[1:])
                if not member.isfile() or not course_file(path):
                    continue
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError(f'Unsafe archive path: {path}')
                data = bundle.extractfile(member).read()
                target = folder / str(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                files[str(path)] = hashlib.sha256(data).hexdigest()
        if 'LICENSE' not in files or 'README.md' not in files:
            raise ValueError(f'Incomplete course archive: {repo}')
        destination = SOURCES / source['slug']
        shutil.rmtree(destination)
        shutil.copytree(folder, destination)
    return {**source, 'revision': revision, 'files': dict(sorted(files.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', choices=NAMES, action='append', help='Limit the refresh to these course slugs')
    parser.add_argument('--latest', action='store_true', help='Explicitly advance selected snapshots to current main')
    args = parser.parse_args()
    manifest = SOURCES / 'sources.json'
    sources = json.loads(manifest.read_text())
    for index, source in enumerate(sources):
        if args.repo and source['slug'] not in args.repo:
            continue
        sources[index] = sync(source, args.latest)
        # Save progress per repository so an interrupted download is recoverable.
        temporary = manifest.with_suffix('.tmp')
        temporary.write_text(json.dumps(sources, indent=2) + '\n')
        temporary.replace(manifest)
        print(source['repo'], sources[index]['revision'])


if __name__ == '__main__':
    main()
