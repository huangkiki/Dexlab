#!/usr/bin/env python3
"""Fetch the immutable reference evidence, optionally including its policy weight."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

BASE = 'https://github.com/liudi159/supermimic-backflip-5090/releases/download/v14-baseline-9029/'
ASSETS = {
    'v14_final9029_evaluation.zip': (2248466, '51a5126210c36cc9a297105684b1bcebbad0489b2e739fda143c34245f57ac4a'),
    'v14_final9029_last.pt': (218547489, '7933f7638b02f0c378606b23c361e328fb3bd6da97086cc2ff9c20aff9aefab2'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--checkpoint', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'raw').mkdir()
    manifest = {}
    for name, (size, expected) in ASSETS.items():
        if name.endswith('.pt') and not args.checkpoint:
            continue
        target = args.output / 'raw' / name
        with urllib.request.urlopen(BASE + name, timeout=60) as source, target.open('xb') as dest:
            shutil.copyfileobj(source, dest)
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if target.stat().st_size != size or digest != expected:
            raise ValueError(f'Source checksum/size mismatch: {name}')
        manifest[name] = {'source': BASE + name, 'bytes': size, 'sha256': digest}
    archive = args.output / 'raw' / 'v14_final9029_evaluation.zip'
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            path = Path(member.filename)
            if path.is_absolute() or '..' in path.parts or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe archive member')
        expanded = sum(member.file_size for member in bundle.infolist())
        if shutil.disk_usage(args.output).free - expanded < 50 * 1024**3:
            raise ValueError('Extraction would leave less than 50 GiB free')
        if bundle.testzip() is not None:
            raise ValueError('Corrupt ZIP member')
        bundle.extractall(args.output / 'evaluation')
    (args.output / 'accepted.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(args.output / 'accepted.json')


if __name__ == '__main__':
    main()
