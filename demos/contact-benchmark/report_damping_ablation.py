"""Reproduce every archived outcome before interpreting paired damping forces."""
import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.contact_damping import force_windows, pair_native_matches, validate_plan, point_force_windows
from dexlab.contact_archive import read_contacts
from dexlab.contact_load import LoadCase
from dexlab.contact_transfer import initial_state_matches
from normal_response import rescore


def summarize(root, *, pointwise=False):
    root = Path(root)
    plan = json.loads((root/'suite.json').read_text())
    validate_plan(plan)
    verification = rescore(root)
    report = json.loads((root/'report.json').read_text())
    rows, observations = [], {}
    for job, outcome in zip(plan['jobs'], report['results'], strict=True):
        folder = root/'raw'/job['id']
        receipt = json.loads((folder/'run.json').read_text())
        checks = outcome['result']['checks']
        required = ('native_run_completed', 'native_mass_matches', 'native_inertia_matches',
                    'normal_parameters_match', 'declared_force_commands', 'momentum_balance',
                    'contact_ledger_matches', 'native_friction_matches', 'source_unchanged',
                    'archived_source_hashes_match', 'artifact_hashes_match')
        if not all(checks.get(key, False) for key in required):
            raise ValueError('Cannot interpret forces without native/state/momentum checks')
        with np.load(folder/'states.npz', allow_pickle=False) as data:
            if not initial_state_matches(job['case'], data['time'][0], data['pose'][0], data['velocity'][0]):
                raise ValueError('Recorded initial state differs from declared case')
            windows = force_windows(LoadCase(**job['case']), data)
            inputs = {key: data[key].copy() for key in ('time', 'external_force', 'downward_load')}
        with np.load(folder/'geometry.npz', allow_pickle=False) as mesh:
            inputs.update({key: mesh[key].copy() for key in mesh.files})
        point_result = None
        if pointwise:
            with np.load(folder/'states.npz', allow_pickle=False) as data:
                point_result = point_force_windows(LoadCase(**job['case']), data,
                                                  read_contacts(folder, receipt))
        key = (job['case']['timestep'], job['normal_parameters']['normal_viscous_damping_coefficient'])
        observations[key] = (receipt, inputs)
        rows.append({'id': job['id'], 'timestep_s': key[0], 'damping_s_m': key[1],
                     'windows': windows, 'engineering_passed': outcome['result']['passed'],
                     'transient_passed': outcome['transient']['passed'],
                     'failed_engineering_checks': sorted(k for k,v in checks.items() if not v)})
        if pointwise:
            rows[-1]['point_force_windows'] = point_result
    for dt in sorted({key[0] for key in observations}):
        (left, a), (right, b) = observations[dt, 0.], observations[dt, 10.]
        if (not pair_native_matches(left['native'], right['native'])
                or left['source_sha256'] != right['source_sha256']
                or a.keys() != b.keys()
                or any(not np.array_equal(a[key], b[key]) for key in a)):
            raise ValueError('Pair differs beyond normal damping in recorded inputs/native metadata')
    return {'verification': verification, 'paired_comparison_complete': True, 'results': rows,
            'scope': 'Recorded actor/solver/input matching and solved-step forces; not hidden contact-law readback or hardware calibration'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--pointwise', action='store_true',
                        help='Add horizontal-plane point-force diagnostics; preserve original verdicts')
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory, pointwise=args.pointwise), indent=2))
