"""Bundle completed cloth batch evidence without rerunning or changing experiments."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def collect(directory):
    """Check archived identities and retain every scheduled job in the report.

    This checks evidence integrity, not physical accuracy. Native trajectories are
    independently scored by cloth_benchmark verify before collection.
    """
    batch_path = directory / "batch.json"
    batch = read_json(batch_path)
    jobs = batch["jobs"]
    names = [f"{job['case']}-{job['solver']}" for job in jobs]
    if (
        batch["status"] != "completed"
        or not jobs
        or len(jobs) != batch["total_count"]
        or len(set(names)) != len(names)
        or any(Path(name).name != name for name in names)
    ):
        raise ValueError("Require a completed batch with unique, complete job accounting")
    report = {
        "scope": "Frozen nominal cloth profiles; no calibrated material or engine accuracy ranking",
        "evidence": "Hash-checked archived measurements; collection does not rerun dynamics or rescore physics",
        "raw_records": "Full trajectories remain in run directories; this bundle alone cannot replay or independently rescore them",
        "batch_sha256": digest(batch_path),
        "collector_sha256": digest(Path(__file__)),
        "configuration": batch["configuration"],
        "source_sha256": batch["source_sha256"],
        "suite_sha256": batch["suite_sha256"],
        "split": batch["split"],
        "profiles": {},
        "records": [],
    }
    for job, name in zip(jobs, names):
        if job["status"] not in ("completed", "timeout"):
            raise ValueError(f"Unfinished job: {name}")
        record = {"run": name, "job": job, "metadata": None, "summary": None}
        run_directory = directory / name
        passed = False
        experiment = "unavailable"
        if "summary_sha256" in job:
            summary_path = run_directory / "summary.json"
            meta_path = run_directory / "run.json"
            if digest(summary_path) != job["summary_sha256"]:
                raise ValueError(f"Summary changed after batch scoring: {name}")
            meta, summary = read_json(meta_path), read_json(summary_path)
            if (
                meta["case"]["name"] != job["case"]
                or meta["solver"] != job["solver"]
                or meta["split"] != batch["split"]
                or meta["suite_sha256"] != batch["suite_sha256"][job["suite"]]
                or meta["source_before"] != batch["source_sha256"]
                or meta["source_after"] != batch["source_sha256"]
                or digest(run_directory / "trajectory.npz") != meta["trajectory_sha256"]
            ):
                raise ValueError(f"Record does not match frozen batch inputs: {name}")
            for relative, expected in meta["source_before"].items():
                if digest(run_directory / "source" / relative) != expected:
                    raise ValueError(f"Source snapshot changed: {name}: {relative}")
            checks = summary["checks"]
            if (
                not checks
                or any(type(value) is not bool for value in checks.values())
                or summary["protocol_checks_passed"] != all(checks.values())
            ):
                raise ValueError(f"Invalid summary check accounting: {name}")
            passed = bool(
                job["status"] == "completed"
                and job["exit_code"] == 0
                and meta["status"] == "completed"
                and summary["protocol_checks_passed"]
            )
            experiment = meta["case"]["experiment"]
            record.update(metadata=meta, summary=summary, run_sha256=digest(meta_path))
        if passed != job["protocol_checks_passed"]:
            raise ValueError(f"Batch and record disagree on outcome: {name}")
        profile = report["profiles"].setdefault(
            job["solver"], {"passed": 0, "total": 0, "timeouts": 0, "experiments": {}}
        )
        profile["passed"] += int(passed)
        profile["total"] += 1
        profile["timeouts"] += int(job["status"] == "timeout")
        counts = profile["experiments"].setdefault(experiment, {"passed": 0, "total": 0})
        counts["passed"] += int(passed)
        counts["total"] += 1
        report["records"].append(record)
    report["total_count"] = len(report["records"])
    report["passed_count"] = sum(profile["passed"] for profile in report["profiles"].values())
    if report["passed_count"] != batch["passed_count"]:
        raise ValueError("Batch pass count disagrees with its individual records")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = collect(args.directory)
    # Refuse to overwrite either raw evidence or an earlier published bundle.
    with args.output.open("x") as output:
        output.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed_count", "total_count", "profiles")}, indent=2))


if __name__ == "__main__":
    main()
