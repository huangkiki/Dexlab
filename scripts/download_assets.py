"""Install a demo's versioned assets, checking archives and every installed file."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def destination(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise ValueError(f'Unsafe asset path: {name}')
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Asset path escapes destination: {name}')
    return path


def matches(path: Path, digest: str) -> bool:
    return path.is_file() and sha256(path) == digest


def fetch(url: str, digest: str, cache: Path) -> Path:
    cached = cache / digest
    if matches(cached, digest):
        return cached
    cache.mkdir(parents=True, exist_ok=True)
    print(f'Downloading {url}', flush=True)
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'DexLab-assets/1'})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        if not matches(temporary, digest):
            raise ValueError(f'SHA-256 mismatch: {url}')
        temporary.replace(cached)
    finally:
        temporary.unlink(missing_ok=True)
    return cached


def install_file(source: Path, target: Path, digest: str) -> None:
    if matches(target, digest):
        return
    if target.exists():
        raise ValueError(f'Modified asset left unchanged: {target}. Move it aside and rerun setup.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copyfile(source, temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def install(manifest: Path, root: Path, cache: Path) -> None:
    data = json.loads(manifest.read_text())
    if data['version'] != 1:
        raise ValueError('Unsupported asset manifest version')
    expected = {}
    for archive in data['archives']:
        expected.update(archive['files'])
    expected.update({item['path']: item['sha256'] for item in data['files']})
    # Check before any writes: preserve locally edited assets.
    for name, digest in expected.items():
        path = destination(root, name)
        if path.exists() and not matches(path, digest):
            raise ValueError(f'Modified asset left unchanged: {path}. Move it aside and rerun setup.')
    for archive in data['archives']:
        files = archive['files']
        if all(matches(destination(root, name), digest) for name, digest in files.items()):
            continue
        packed = fetch(archive['url'], archive['sha256'], cache)
        with tempfile.TemporaryDirectory(prefix='dexlab-assets-') as directory:
            stage = Path(directory)
            seen = set()
            with tarfile.open(packed, 'r:*') as tar:
                for member in tar:
                    target = destination(stage, member.name)
                    if member.isdir():
                        continue
                    if not member.isfile() or member.name not in files or member.name in seen:
                        raise ValueError(f'Unexpected archive member: {member.name}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, target.open('wb') as output:
                        shutil.copyfileobj(source, output)
                    if not matches(target, files[member.name]):
                        raise ValueError(f'Asset checksum mismatch: {member.name}')
                    seen.add(member.name)
            if seen != set(files):
                raise ValueError('Archive is missing required files')
            for name, digest in files.items():
                install_file(destination(stage, name), destination(root, name), digest)
    for item in data['files']:
        target = destination(root, item['path'])
        if not matches(target, item['sha256']):
            source = fetch(item['url'], item['sha256'], cache)
            install_file(source, target, item['sha256'])
    print(f'Assets ready: {len(expected)} files verified in {root}', flush=True)


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=repo / 'demos/apple-stem-grasp/assets.json')
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'dexlab/assets')
    args = parser.parse_args()
    try:
        install(args.manifest, args.destination or args.manifest.parent / 'assets', args.cache)
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f'Asset installation failed: {error}\n')


if __name__ == '__main__':
    main()
