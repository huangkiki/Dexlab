"""Rescore the eight readback records and optionally compare historical states.

Inputs are existing archives. This command never runs physics or changes records.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.contact_archive import read_contacts
from dexlab.contact_readback import diagnose_archive


def compare_records(previous, current):
    """Compare all original state bytes and contact fields, excluding new readback."""
    with np.load(previous / 'states.npz', allow_pickle=False) as left, np.load(
        current / 'states.npz', allow_pickle=False
    ) as right:
        same_keys = set(left.files) == set(right.files)
        equal = {key: key in right.files and left[key].dtype == right[key].dtype
                 and left[key].shape == right[key].shape
                 and left[key].tobytes() == right[key].tobytes() for key in left.files}
    contacts = []
    for directory in (previous, current):
        receipt = json.loads((directory / 'run.json').read_text())
        contacts.append(read_contacts(directory, receipt))
    projected = [[{key: value for key, value in contact.items() if key != 'parameters'}
                  for contact in frame] for frame in contacts[1]]
    return {'state_keys_equal': same_keys, 'state_arrays_bitwise': equal,
            'original_contact_fields_equal': contacts[0] == projected,
            'previous_states_sha256': hashlib.sha256((previous / 'states.npz').read_bytes()).hexdigest(),
            'current_states_sha256': hashlib.sha256((current / 'states.npz').read_bytes()).hexdigest()}


def report_records(directory, previous=None):
    rows = []
    for engine in ('mujoco', 'superdex'):
        for case in ('forward', 'frictionless', 'rest', 'half-step'):
            name = f'{engine}-dev-readback-{case}'
            current = directory / name
            diagnosis = diagnose_archive(current)
            acceptance = diagnosis['archive_acceptance']
            row = {'id': name, 'archive_status': diagnosis['status'],
                   'physics_passed': acceptance['passed'], 'checks': acceptance['checks'],
                   'readback': diagnosis['readback']}
            if previous is not None:
                old = previous / f'{engine}-dev-friction-{case}'
                row['previous_archive_passed'] = diagnose_archive(old)['archive_acceptance']['passed']
                row['recording_comparison'] = compare_records(old, current)
            rows.append(row)
    return {'scope': 'Eight development records; no held-out or general engine ranking', 'runs': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = report_records(args.directory, args.previous)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    valid = all(row['archive_status'] == 'available' and row['physics_passed'] for row in report['runs'])
    for row in report['runs']:
        readback = row['readback']
        valid &= readback is not None and readback['actor_profiles_equal']
        if row['id'].startswith('mujoco-'):
            valid &= readback is not None and readback['status'] == 'consistent'
        if args.previous is not None:
            comparison = row['recording_comparison']
            valid &= (row['previous_archive_passed'] and comparison['state_keys_equal']
                      and all(comparison['state_arrays_bitwise'].values())
                      and comparison['original_contact_fields_equal'])
    if not valid:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
