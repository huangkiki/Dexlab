"""Verify a released archive and reproduce its complete development report.

Exit zero means that all recorded outcomes were reproduced, including failures.
No physics engine is stepped. Use the DexLab version matching the release.
"""

import argparse
import json
from pathlib import Path

from dexlab.contact_indent_run import verify as verify_indent
from dexlab.contact_pinch_run import verify as verify_cylinder
from dexlab.contact_plane_native import verify as verify_plane
from dexlab.physx_baseline import digest


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing file or path outside the evidence directory: {name}")
    return path


def rescore(root):
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text())["files"]
    for name, expected in manifest.items():
        if digest(inside(root, name)) != expected:
            raise ValueError(f"Archive hash mismatch: {name}")
    report = json.loads((root / "report.json").read_text())
    passed = 0
    for row in report["results"]:
        receipt = inside(root, "raw/" + row["run"] + "/run.json")
        if digest(receipt) != row["run_sha256"]:
            raise ValueError(f"Run receipt mismatch: {row['run']}")
        if row["kind"] in ("plane", "material-readback"):
            verify = verify_plane
        elif row["kind"] == "indent":
            verify = verify_indent
        elif row["kind"] in (
            "cylinder",
            "timestep-refinement",
            "iteration-refinement",
            "surface-refinement",
            "refined-surface-controls",
        ):
            verify = verify_cylinder
        else:
            raise ValueError(f"Unknown experiment kind: {row['kind']}")
        result = verify(receipt.parent)
        if result != row["current_review"]:
            raise ValueError(f"Recomputed summary differs: {row['run']}")
        passed += result["passed"]
    count = len(report["results"])
    if count != report["completed"] or passed != report["passed"]:
        raise ValueError("Report counts differ from the per-run results")
    return {
        "all_outcomes_reproduced": True,
        "completed": count,
        "physics_passed": passed,
        "physics_failed": count - passed,
        "archive_files_verified": len(manifest),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    print(json.dumps(rescore(args.evidence), indent=2))
