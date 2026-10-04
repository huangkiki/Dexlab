"""Fail-closed metadata checks before runtime qualification, not qualification itself."""

from datetime import datetime, timedelta, timezone

from packaging.requirements import Requirement
from packaging.version import Version


def validate_versions(audit, installed, native, *, extras=None, now=None):
    """Check a dated official inventory against a proposed runtime combination.

    ``audit`` contains the freshly collected PyPI metadata for each participating
    engine/binding. Unrelated optional engines must be omitted, not downgraded.
    Runtime hashes, solver settings and task evidence are separate requirements.
    """
    now = now or datetime.now(timezone.utc)
    extras = extras or {}
    rows = {row["package"]: row for row in audit}
    if len(rows) != len(audit) or not rows or set(rows) != set(installed):
        raise ValueError("Inventory must cover exactly the participating packages")
    for name, version in installed.items():
        row = rows[name]
        checked = datetime.fromisoformat(row["checked_at"])
        if checked.tzinfo is None or not timedelta(0) <= now - checked <= timedelta(hours=24):
            raise ValueError("Release inventory is stale or future-dated")
        parsed = Version(version)
        if parsed.is_prerelease or parsed.is_devrelease or parsed.local:
            raise ValueError("Pre-release, development and local versions are not stable")
        if parsed != Version(row["version"]):
            raise ValueError("Installed pin differs from the audited latest stable version")
        if row.get("yanked") is not False:
            raise ValueError("Non-yanked distribution evidence is required")
        if row.get("source") != f"https://pypi.org/pypi/{name}/json":
            raise ValueError("Unexpected metadata source")
        if any("Development Status :: " in label and any(
            state in label for state in ("Planning", "Pre-Alpha", "Alpha", "Beta")
        ) for label in row["classifiers"]):
            raise ValueError("Distribution maturity excludes the primary stable comparison")
        for value in row.get("requires_dist") or []:
            dependency = Requirement(value)
            if dependency.name not in installed:
                continue  # General dependencies still require the package manager's check.
            active = dependency.marker is None or any(
                dependency.marker.evaluate({"extra": extra})
                for extra in ("", *extras.get(name, ()))
            )
            if active and Version(installed[dependency.name]) not in dependency.specifier:
                raise ValueError(f"Incompatible participating versions: {name} requires {dependency}")
    if "mujoco" in installed and native.get("mujoco") != installed["mujoco"]:
        raise ValueError("Loaded MuJoCo native version differs from its package")
    return {"metadata_compatible": True, "runtime_qualified": False}
