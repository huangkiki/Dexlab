#!/usr/bin/env python3
"""Create the AMP reference's finite ledger; this does not admit a native run."""

import argparse
import hashlib
import json
from pathlib import Path

from dexlab.migration_budget import MigrationBudget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--resource-plan", type=Path, required=True)
    args = parser.parse_args()
    raw = Path(__file__).with_name("protocol.json").read_bytes()
    protocol = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    resource_raw = args.resource_plan.read_bytes()
    resource_plan = json.loads(resource_raw)
    if not resource_plan.get("profile", "").startswith("adaptive-") or not resource_plan.get("measurement"):
        parser.error("Use a measured adaptive resource plan frozen by bounded_run.py")
    plan = protocol["repeat_plan"]
    budget = MigrationBudget.create(args.output, {
        "protocol_sha256": digest,
        "resource_plan": resource_plan,
        "resource_plan_file_sha256": hashlib.sha256(resource_raw).hexdigest(),
        "work_package": {
            "id": protocol["id"], "hypothesis": protocol["question"],
            "max_starts": plan["max_native_attempts"], "wall_s": plan["max_total_native_wall_s"],
            "evidence_sha256": [protocol["checkpoint_sha256"], digest, hashlib.sha256(resource_raw).hexdigest()],
        },
        "matrix": [{"id": case["id"]} for case in protocol["cases"]],
    })
    print(json.dumps(budget.status(), indent=2))


if __name__ == "__main__":
    main()
