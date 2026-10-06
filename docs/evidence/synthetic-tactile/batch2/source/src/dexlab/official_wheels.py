"""Bind installed package code to an official hash-verified wheel."""
import hashlib
import json
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

from packaging.utils import canonicalize_name


def stream_sha256(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def verify_official_wheel(path, *, package, version, official_sha256, installed_code_sha256):
    """Bind observed installed code to a hash-verified official wheel payload.

    official_sha256 must come from the freshly collected release inventory for
    this exact filename. This supports the current flat wheels, not arbitrary
    installation relocations. Private wheel paths never enter returned evidence.
    """
    path = Path(path)
    with path.open('rb') as stream:
        digest = stream_sha256(stream)
    if digest != official_sha256:
        raise ValueError('Wheel differs from official distribution SHA256')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate wheel archive members')
        metadata = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata) != 1:
            raise ValueError('Expected one wheel distribution metadata entry')
        info = BytesParser().parsebytes(archive.read(metadata[0]))
        if canonicalize_name(info['Name']) != canonicalize_name(package) or info['Version'] != version:
            raise ValueError('Wheel package/version identity mismatch')
        hashes = {}
        for name in names:
            member = PurePosixPath(name)
            if not (name.endswith('.py') or '.so' in member.name):
                continue
            if member.is_absolute() or '..' in member.parts or any(part.endswith('.data') for part in member.parts):
                raise ValueError('Unsupported wheel code relocation')
            with archive.open(name) as stream:
                hashes[name] = stream_sha256(stream)
    if not hashes:
        raise ValueError('Wheel has no auditable code payload')
    code_digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    if code_digest != installed_code_sha256:
        raise ValueError('Installed code differs from official wheel payload')
    return {'filename': path.name, 'sha256': digest,
            'package_code_sha256': code_digest, 'code_files': len(hashes)}
