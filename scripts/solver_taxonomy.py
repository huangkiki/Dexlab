"""Render recorded profile labels by explicit engine-specific roles, not peer rank."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/solver-taxonomy.json"


def load_taxonomy(path: Path = CATALOG) -> dict[str, Any]:
    """Read display vocabulary; this never changes an experimental inventory."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported solver taxonomy schema")
    roles = data.get("roles", {})
    if "unresolved" not in roles or not data.get("engines"):
        raise ValueError("Missing taxonomy roles or engines")
    for role, labels in roles.items():
        if not isinstance(labels, dict) or any(
            not isinstance(labels.get(lang), str) or not labels[lang].strip()
            for lang in ("en", "zh")
        ):
            raise ValueError("Missing bilingual role label: " + role)
    for engine, item in data["engines"].items():
        if not item.get("sources") or not isinstance(item.get("tokens"), dict):
            raise ValueError("Missing source or token map: " + engine)
        for token, meaning in item["tokens"].items():
            if (
                not token or token != token.strip().casefold()
                or not isinstance(meaning, list) or len(meaning) != 2
                or meaning[0] not in roles
                or not isinstance(meaning[1], str) or not meaning[1].strip()
            ):
                raise ValueError("Invalid role mapping: " + engine + "/" + token)
    return data


def classify_profiles(
    engine: str,
    rows: Iterable[Mapping[str, Any]],
    taxonomy: Mapping[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Preserve unknown labels; roles describe names, not actual solver telemetry."""
    data = load_taxonomy() if taxonomy is None else taxonomy
    if engine not in data["engines"]:
        raise ValueError("Unclassified engine: " + engine)
    tokens = data["engines"][engine]["tokens"]
    buckets: dict[str, set[str]] = {role: set() for role in data["roles"]}
    for row in rows:
        if row.get("engine", engine) != engine:
            raise ValueError("Mixed engines in solver summary")
        name = row.get("solver")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Missing profile label")
        if name.startswith("MJWarp"):
            # The existing separate path table retains core/version/status per row.
            continue
        if any(word in name.lower() for word in (
            "unqualified", "not qualified", "pending", "historical"
        )):
            buckets["unresolved"].add(name)
            continue
        for part in name.split("/"):
            part = part.strip()
            if not part:
                raise ValueError("Empty profile component: " + name)
            role, label = tokens.get(part.casefold(), ("unresolved", part))
            buckets[role].add(label)
    return {role: sorted(values) for role, values in buckets.items() if values}


def _escape(value: str) -> str:
    """Keep native names from becoming Markdown columns or raw HTML."""
    return html.escape(" ".join(value.split()), quote=True).replace("|", "&#124;")


def summarize_roles(
    engine: str,
    rows: Iterable[Mapping[str, Any]],
    language: str = "en",
    taxonomy: Mapping[str, Any] | None = None,
) -> str:
    if language not in ("en", "zh"):
        raise ValueError("Unsupported summary language")
    data = load_taxonomy() if taxonomy is None else taxonomy
    grouped = classify_profiles(engine, rows, data)
    if not grouped:
        return "未登记角色；见完整矩阵" if language == "zh" else "No recorded roles; see full matrix"
    return "<br>".join(
        _escape(data["roles"][role][language]) + ": "
        + " · ".join(_escape(value) for value in values)
        for role, values in grouped.items()
    )
