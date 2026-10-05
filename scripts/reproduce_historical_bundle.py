#!/usr/bin/env python3
"""Verify public bundle hashes, then reproduce its pinned historical scores."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys


def reproduce(bundle, output):
    bundle = bundle.resolve(strict=True)
    output = output.resolve()
    if output.exists() or output.is_relative_to(bundle):
        raise ValueError("Use a fresh output directory outside the bundle")
    manifest = json.loads((bundle / "manifest.json").read_text())
    if manifest["schema"] != "public-historical-bundle-v1":
        raise ValueError("Unsupported bundle schema")
    for package, version in manifest["environment"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"Historical reproduction requires {package}=={version}")
    declared = set(manifest["files"]) | {"manifest.json"}
    entries = list(bundle.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise ValueError("Bundle symlinks are not permitted")
    actual_files = {str(path.relative_to(bundle)) for path in entries if path.is_file()}
    if actual_files != declared:
        raise ValueError("Bundle has missing or undeclared files")
    for name, expected in manifest["files"].items():
        path = (bundle / name).resolve(strict=True)
        if not path.is_relative_to(bundle) or not path.is_file():
            raise ValueError("Bundle entry escapes its root")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Bundle hash mismatch: {name}")
    output.mkdir(parents=True)
    locations = {name: str(bundle / "raw" / name) for name in ("cloth-heldout", "robot-cloth")}
    (output / "locations-private.json").write_text(json.dumps(locations, indent=2) + "\n")
    environment = dict(os.environ, PYTHONPATH=str(bundle / "scorer/src"), PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-m", "dexlab.evidence_report", "--selection",
                    str(bundle / "scorer/docs/evidence/public-cohorts.json"), "--locations",
                    str(output / "locations-private.json"), "--output", str(output / "rescored.json")],
                   cwd=bundle / "scorer", env=environment, check=True)
    actual = json.loads((output / "rescored.json").read_text())
    expected = json.loads((bundle / "expected-records.json").read_text())
    if actual["records"] != expected:
        expected_rows = {(r["cohort"], r["id"]): r for r in expected}
        different = [{"cohort": r["cohort"], "id": r["id"],
                      "fields": sorted(k for k in set(r) | set(expected_rows.get((r["cohort"], r["id"]), {}))
                                       if r.get(k) != expected_rows.get((r["cohort"], r["id"]), {}).get(k))}
                     for r in actual["records"] if r != expected_rows.get((r["cohort"], r["id"]))]
        (output / "differences.json").write_text(json.dumps(different, indent=2) + "\n")
        raise ValueError("Historical results differ; see differences.json. Do not replace the baseline.")
    result = {"schema": "public-historical-reproduction-v1", "records": len(expected),
              "all_record_fields_equal": True, "environment": actual["environment"],
              "scorer_sha256": actual["scorer_sha256"],
              "manifest_sha256": hashlib.sha256((bundle / "manifest.json").read_bytes()).hexdigest()}
    (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = reproduce(args.bundle, args.output)
    print(f"Verified {result['records']} records against the frozen historical report.")


if __name__ == "__main__":
    main()
