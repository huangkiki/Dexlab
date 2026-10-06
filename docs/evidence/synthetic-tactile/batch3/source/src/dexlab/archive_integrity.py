"""Content-verified archival of completed runs; never deletes source evidence."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import uuid


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def write_receipt(path, receipt):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def snapshot(directory):
    """Reject links/special files and detect mutation while reading each file."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Source must be a real directory')
    paths = sorted(directory.rglob('*'))
    entries = []
    for path in paths:
        before = path.lstat()
        if stat.S_ISDIR(before.st_mode):
            continue
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('Symlinks and special files are not archive evidence')
        with path.open('rb') as stream:
            opened = stream.fileno()
            if identity(os.fstat(opened)) != identity(before):
                raise ValueError('Source changed before hashing')
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = path.lstat()
        if identity(before) != identity(after):
            raise ValueError('Source changed while hashing')
        entries.append({'path': path.relative_to(directory).as_posix(),
                        'bytes': before.st_size, 'sha256': digest,
                        'source_identity': list(identity(before))})
    if sorted(directory.rglob('*')) != paths:
        raise ValueError('Source file list changed during hashing')
    if not entries:
        raise ValueError('Empty evidence directory')
    return {'schema_version': 1, 'files': entries, 'file_count': len(entries),
            'total_bytes': sum(item['bytes'] for item in entries)}


def content_manifest(manifest):
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported archive manifest')
    files = []
    names = set()
    for item in manifest['files']:
        name = item['path']
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or '\\' in name
                or path.as_posix() != name or name in names):
            raise ValueError('Unsafe or duplicate manifest path')
        if (type(item['bytes']) is not int or item['bytes'] < 0
                or len(item['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in item['sha256'])):
            raise ValueError('Invalid file size or SHA-256')
        names.add(name)
        files.append({key: item[key] for key in ('path', 'bytes', 'sha256')})
    if not files or manifest['file_count'] != len(files) or manifest['total_bytes'] != sum(x['bytes'] for x in files):
        raise ValueError('Manifest totals do not match its files')
    return sorted(files, key=lambda item: item['path'])


def verify_copy(directory, expected):
    actual = snapshot(directory)
    if content_manifest(actual) != content_manifest(expected):
        raise ValueError('Archive has missing, extra or changed files')
    return actual


def finalize(stage, destination, source_before, source_after, offline_reader, *, receipt_path):
    """Promote only after source stability, integrity and real offline reading.

    The reader must be read-only and return a structured readability receipt;
    scientific acceptance may be false for a successfully preserved failed run.
    """
    stage, destination = Path(stage), Path(destination)
    receipt_path = Path(receipt_path)
    if destination.is_symlink():
        raise ValueError('Destination must not be a symlink')
    payload = json.dumps(content_manifest(source_before), sort_keys=True, separators=(',', ':')).encode()
    fingerprint = hashlib.sha256(payload).hexdigest()
    if any(receipt_path.resolve().is_relative_to(p.resolve()) for p in (stage, destination)):
        raise ValueError('Receipt must be outside original evidence')
    previous = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    if previous is not None and (previous.get('content_manifest_sha256') != fingerprint
                                 or previous.get('destination_name') != destination.name):
        raise FileExistsError('Receipt belongs to another archive')
    recovered = destination.exists()
    if recovered and (stage.exists() or previous is None):
        raise FileExistsError('Existing archive is immutable; choose a new run ID')
    if not recovered and previous is not None and previous.get('state') != 'verified_pending_promotion':
        raise ValueError('Completed archive directory is missing')
    if stage.is_symlink() or stage.parent.resolve() != destination.parent.resolve():
        raise ValueError('Stage and destination must be real siblings for atomic promotion')
    content_manifest(source_before)
    if source_before != source_after:
        raise ValueError('Source changed during transfer; retain source and staging copy')
    reading_directory = destination if recovered else stage
    verify_copy(reading_directory, source_before)
    reading = offline_reader(reading_directory)
    if not isinstance(reading, dict) or reading.get('readable') is not True:
        raise ValueError('Offline model/trajectory reading did not pass')
    verify_copy(reading_directory, source_before)  # Readers must not rewrite original evidence.
    receipt = {'schema_version': 1, 'archived': False, 'state': 'verified_pending_promotion',
               'destination_name': destination.name,
               'file_count': source_before['file_count'], 'total_bytes': source_before['total_bytes'],
               'content_manifest_sha256': fingerprint,
               'source_unchanged': True, 'source_deleted': False, 'offline_read': reading}
    # A single controller owns this archive root; never replace an existing run.
    if not recovered:
        if destination.exists():
            raise FileExistsError('Destination appeared before promotion')
        write_receipt(receipt_path, receipt)
        stage.rename(destination)
    receipt.update(archived=True, state='completed')
    write_receipt(receipt_path, receipt)
    return receipt
