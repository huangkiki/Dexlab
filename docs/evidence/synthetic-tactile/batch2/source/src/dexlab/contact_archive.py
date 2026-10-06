"""Lossless deterministic storage of complete native contact observations."""

import gzip
import io
import json
from pathlib import Path

from dexlab.physx_baseline import digest

CONTACT_FILE = "contacts.json.gz"


def write_contacts(directory, rows):
    """Keep every contact while avoiding repeated whitespace/numeric-zero blobs."""
    with (
        (directory / CONTACT_FILE).open("wb") as target,
        gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as compressed,
        io.TextIOWrapper(compressed, encoding="utf-8") as stream,
    ):
        json.dump(rows, stream, allow_nan=False, separators=(",", ":"))
    return CONTACT_FILE


def contact_file(receipt):
    name = receipt.get("contact_archive", "contacts.json")
    if name not in ("contacts.json", CONTACT_FILE):
        raise ValueError("Unknown contact archive format")
    return name


def read_contacts(directory, receipt):
    name = contact_file(receipt)
    if name == CONTACT_FILE:
        with gzip.open(directory / name, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    return json.loads((directory / name).read_text())


def source_snapshots_match(directory, receipt):
    """Bind archived source bytes to the hashes captured before execution.

    Early plane receipts used absolute source paths as keys. Only their local
    snapshot names are resolved; verification never reads the original checkout.
    """
    sources = receipt.get("source_sha256", {})
    if not isinstance(sources, dict) or not sources:
        return False
    try:
        names = []
        for source, expected in sources.items():
            path = Path(source)
            if path.is_absolute():
                name = (
                    "contact_plane_task.py"
                    if path.parent.name == "tasks" and path.name == "contact_plane.py"
                    else path.name
                )
            elif len(path.parts) == 1:
                name = source
            else:
                return False
            snapshot = directory / name
            if (
                not snapshot.is_file()
                or not snapshot.resolve().is_relative_to(directory.resolve())
                or digest(snapshot) != expected
            ):
                return False
            names.append(name)
        return len(names) == len(set(names))
    except (OSError, TypeError, ValueError):
        return False
