"""Run a frozen development matrix or independently reproduce archived outcomes."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab import contact_transient
from dexlab.contact_indent_run import run, verify
from dexlab.contact_load import LIMITS, LoadCase
from dexlab.physx_baseline import digest, write_json


def evaluate(root, suite):
    plan = json.loads(suite.read_text())
    if plan["protocol"] != "normal-load" or plan["target"] != LIMITS:
        raise ValueError("Unexpected protocol or changed target limits")
    transient = "transient_target" in plan
    if transient and plan["transient_target"] != contact_transient.TARGET:
        raise ValueError("Changed transient target")
    ids = [job["id"] for job in plan["jobs"]]
    if len(ids) != len(set(ids)) or any(
        Path(i).name != i or i in (".", "..") for i in ids
    ):
        raise ValueError("Job IDs must be unique directory basenames")
    root.mkdir(parents=True, exist_ok=False)
    (root / "suite.json").write_bytes(suite.read_bytes())
    if transient:
        (root / "transient-scorer.py").write_bytes(
            Path(contact_transient.__file__).read_bytes()
        )
    rows = []
    for job in plan["jobs"]:
        output = root / "raw" / job["id"]
        result = run(
            LoadCase(**job["case"]),
            job["engine"],
            output,
            normal_parameters=job["normal_parameters"],
        )
        rows.append(
            {
                "id": job["id"],
                "role": job["role"],
                "engine": job["engine"],
                "receipt_sha256": digest(output / "run.json"),
                "result": result,
            }
        )
        if transient:
            with np.load(output / "states.npz", allow_pickle=False) as data:
                rows[-1]["transient"] = contact_transient.score(
                    LoadCase(**job["case"]), data
                )
        report = {
            "schema_version": 1,
            "scope": plan["scope"],
            "completed": len(rows),
            "passed": sum(r["result"]["passed"] for r in rows),
            "results": rows,
            "suite_sha256": digest(suite),
        }
        if transient:
            report.update(
                transient_scorer_sha256=digest(root / "transient-scorer.py"),
                transient_passed=sum(r["transient"]["passed"] for r in rows),
                combined_passed=sum(
                    r["result"]["passed"] and r["transient"]["passed"] for r in rows
                ),
            )
        write_json(root / "report.json", report)
        print(job["id"], result["passed"], flush=True)
    return report


def rescore(root):
    report = json.loads((root / "report.json").read_text())
    plan = json.loads((root / "suite.json").read_text())
    if digest(root / "suite.json") != report["suite_sha256"]:
        raise ValueError("Suite hash mismatch")
    transient = "transient_target" in plan
    if transient and (
        plan["transient_target"] != contact_transient.TARGET
        or digest(root / "transient-scorer.py") != report["transient_scorer_sha256"]
        or digest(Path(contact_transient.__file__)) != report["transient_scorer_sha256"]
    ):
        raise ValueError("Transient target or scorer changed")
    if [r["id"] for r in report["results"]] != [j["id"] for j in plan["jobs"]]:
        raise ValueError("Incomplete or reordered outcomes")
    for row, job in zip(report["results"], plan["jobs"], strict=True):
        folder = (root / "raw" / row["id"]).resolve()
        if not folder.is_relative_to(root.resolve()):
            raise ValueError("Outcome outside the archive")
        receipt = json.loads((folder / "run.json").read_text())
        if digest(folder / "run.json") != row["receipt_sha256"]:
            raise ValueError("Run receipt hash mismatch")
        if any(receipt[k] != job[k] for k in ("engine", "case")):
            raise ValueError("Run differs from declared case")
        from dexlab.contact_parameters import normal_parameters

        if receipt["normal_parameters"] != normal_parameters(
            job["engine"], job["normal_parameters"]
        ):
            raise ValueError("Run differs from declared native profile")
        if verify(folder) != row["result"]:
            raise ValueError(f"Outcome differs: {row['id']}")
        if transient:
            with np.load(folder / "states.npz", allow_pickle=False) as data:
                if (
                    contact_transient.score(LoadCase(**job["case"]), data)
                    != row["transient"]
                ):
                    raise ValueError(f"Transient outcome differs: {row['id']}")
    passed = sum(r["result"]["passed"] for r in report["results"])
    if len(report["results"]) != report["completed"] or passed != report["passed"]:
        raise ValueError("Incorrect aggregate counts")
    result = {
        "outcomes_reproduced": len(report["results"]),
        "physics_passed": passed,
        "physics_failed": len(report["results"]) - passed,
    }
    if transient:
        counts = {
            "transient_passed": sum(
                r["transient"]["passed"] for r in report["results"]
            ),
            "combined_passed": sum(
                r["result"]["passed"] and r["transient"]["passed"]
                for r in report["results"]
            ),
        }
        if any(report[key] != value for key, value in counts.items()):
            raise ValueError("Incorrect transient counts")
        result.update(counts)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--suite", type=Path, default=Path("benchmarks/contact-normal-v1.json")
    )
    args = parser.parse_args()
    report = (
        evaluate(args.directory, args.suite)
        if args.command == "run"
        else rescore(args.directory)
    )
    print(json.dumps(report, indent=2))
    # Successful reproduction includes preserved physical failures.
    if args.command == "run" and any(
        not row["result"]["checks"].get("native_run_completed", False)
        for row in report["results"]
    ):
        raise SystemExit(2)
