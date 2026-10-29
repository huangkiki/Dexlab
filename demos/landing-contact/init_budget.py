#!/usr/bin/env python3
"""Create the frozen landing campaign using DexLab's existing durable ledger."""

import argparse
import hashlib
import json
from pathlib import Path

from dexlab.migration_budget import MigrationBudget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = Path(__file__).with_name('protocol.json').read_bytes()
    protocol = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    plan = protocol['repeat_plan']
    budget = MigrationBudget.create(args.output, {
        'protocol_sha256': digest,
        'work_package': {
            'id': 'landing-reference-20261026-v1',
            'hypothesis': 'Complete pre/post contact records can distinguish recording epochs and contact activation without replacement forces',
            'max_starts': plan['max_native_attempts'], 'wall_s': plan['max_total_native_wall_s'],
            'evidence_sha256': [protocol['release_evaluation_sha256'], digest],
        },
        'matrix': [{'id': case} for case in ('support-probe', 'policy-repeat-1', 'policy-repeat-2',
                                            'policy-repeat-3', 'conditional-1', 'conditional-2')],
    })
    print(json.dumps(budget.status(), indent=2))


if __name__ == '__main__':
    main()
