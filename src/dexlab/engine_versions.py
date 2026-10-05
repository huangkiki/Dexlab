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


def mujoco_profile_identity(identity, native_version, *, profile=None):
    """Select an explicit compatibility profile without granting qualification.

    Historical reproduction remains the default. Candidate mode permits the
    qualification tests to execute; it never authorizes a formal batch.
    """
    import os

    if profile is None:
        profile = os.environ.get("DEXLAB_MUJOCO_PROFILE", "historical-3.11.0")
    versions = {"historical-3.11.0": "3.11.0", "qualification-3.14.0": "3.14.0"}
    if profile not in versions:
        raise ValueError("Unknown MuJoCo compatibility profile")
    expected = versions[profile]
    if identity["version"] != expected or native_version != expected:
        raise ValueError(f"{profile} requires matching package and native MuJoCo {expected}")
    return {**identity, "compatibility_profile": profile,
            "profile_status": "candidate" if profile.startswith("qualification-") else "historical",
            "formal_batch_qualified": False}


def require_formal_batch_qualification(task, profiles, *, receipt=None,
                                       source_hashes=None, runtime=None,
                                       evidence=None, required_checks=None, now=None):
    """Require task-owner observations; absent production evidence fails closed.

    Task owners must observe runtime/source and independently rescore records.
    There is no caller-supplied success boolean or CLI override. Batch entrypoints
    without those observations remain blocked until their adapters are connected.
    """
    if any(value is None for value in
           (receipt, source_hashes, runtime, evidence, required_checks)):
        raise ValueError(
            f"Formal batch not qualified: {task} / {', '.join(profiles)}. "
            "Task-owner native/source observations and independent evidence required."
        )
    return validate_runtime_qualification(
        receipt, task=task, profiles=profiles, source_hashes=source_hashes,
        runtime=runtime, evidence=evidence, required_checks=required_checks, now=now,
    )


def validate_runtime_qualification(receipt, *, task, profiles, source_hashes,
                                   runtime, evidence, required_checks, now=None):
    """Validate a qualification against caller-observed inputs and rescored evidence.

    ``runtime`` is observed in the execution process; ``evidence`` is independently
    rescored from hash-checked raw records by the task owner. Neither is taken
    from the qualification receipt. This function does not load engines or infer
    physical success from a saved boolean. Callers must retain the returned
    freeze and compare it throughout execution.
    """
    if receipt.get("schema_version") != 1 or receipt.get("task") != task:
        raise ValueError("Qualification task or schema mismatch")
    if not profiles or receipt.get("profiles") != profiles:
        raise ValueError("Qualification does not cover exact requested profiles/settings")
    if not source_hashes or receipt.get("source_sha256") != source_hashes:
        raise ValueError("Qualification source differs from the executing source")
    if receipt.get("runtime") != runtime:
        raise ValueError("Loaded runtime differs from qualified runtime")
    if not runtime.get("installed") or not runtime.get("native"):
        raise ValueError("Package and independently observed native identities required")
    artifacts = runtime.get("artifact_sha256", {})
    if not artifacts or any(
        not isinstance(value, str) or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        for value in artifacts.values()
    ):
        raise ValueError("Observed native artifact SHA256 hashes required")
    validate_versions(receipt["audit"], runtime["installed"], runtime["native"],
                      extras=receipt.get("extras"), now=now)
    if set(evidence) != set(profiles) or set(required_checks) != set(profiles):
        raise ValueError("Independent evidence must cover every requested profile")
    declared = receipt.get("evidence_sha256", {})
    if set(declared) != set(evidence):
        raise ValueError("Qualification evidence coverage mismatch")
    for profile, record in evidence.items():
        digest = record.get("raw_record_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
                or declared[profile] != digest):
            raise ValueError("Raw qualification record differs from frozen evidence")
        checks = record.get("checks", {})
        expected = required_checks[profile]
        if (not expected or set(checks) != set(expected)
                or not all(value is True for value in checks.values())):
            raise ValueError("Independent task checks are missing, extra or failed")
        if record.get("profile") != profiles[profile]:
            raise ValueError("Scored configuration differs from requested profile")
    # Copy via JSON so the caller cannot mutate the original receipt into a
    # different freeze after admission; this is evidence, not a persistent flag.
    import json

    return json.loads(json.dumps({
        "schema_version": 1, "task": task, "profiles": profiles,
        "source_sha256": source_hashes, "runtime": runtime,
        "evidence_sha256": declared, "audit": receipt["audit"],
    }, allow_nan=False))


def verify_frozen_runtime(frozen, *, task, profiles, source_hashes, runtime):
    """Resume/step check: retain the dated release, reject any input replacement.

    Do not re-run freshness checks inside a frozen batch. An upstream release
    queues new qualification; it does not authorize changing this batch.
    """
    if (frozen.get("schema_version") != 1 or not task or frozen.get("task") != task
            or not profiles or not source_hashes or not runtime
            or frozen.get("profiles") != profiles
            or frozen.get("source_sha256") != source_hashes
            or frozen.get("runtime") != runtime):
        raise ValueError("Qualified frozen source, runtime or settings changed")

    if task == "apple-stem":
        wheels = frozen.get("official_wheels", {})
        installed = runtime.get("installed", {})
        code = runtime.get("package_code_sha256", {})
        audit = {row["package"]: row for row in frozen.get("audit", [])}
        if not installed or set(wheels) != set(installed) or set(code) != set(installed):
            raise ValueError("Frozen official wheel evidence is incomplete")
        for package, wheel in wheels.items():
            official = audit.get(package, {}).get("distribution_sha256", {})
            if (not wheel.get("sha256")
                    or official.get(wheel.get("filename")) != wheel["sha256"]
                    or wheel.get("package_code_sha256") != code[package]):
                raise ValueError("Frozen official wheel and observed code differ")
