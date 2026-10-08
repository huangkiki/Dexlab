"""Score recorded candidate traces against fixed native traces, without an engine."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.adapter_qualification import compare_initial, numeric_error


def score_trial(candidate, reference):
    result = compare_initial(candidate['initial'], reference['initial'], storage_trial=True)
    failures = result['failures']
    maxima = {key: 0. for key in ('q', 'object_pos', 'object_vel', 'object_quat',
                                  'object_contact_force', 'public_state', 'public_force')}
    rows, expected = candidate['samples'], reference['samples']
    if len(rows) != 8000 or len(expected) != 8000:
        raise ValueError('Incomplete four-second trace')
    initial = candidate['initial']
    cube = initial['cube_link']
    others = dict(zip(('left_force', 'right_force', 'ground_force'),
                      [*initial['pad_links'], initial['plane_link']]))
    for index, (row, target) in enumerate(zip(rows, expected)):
        if row['time'] != (index + 1) * .0005 or row['time'] != target['time']:
            raise ValueError('Mismatched sample time')
        if row['command'] != target['command']:
            raise ValueError('Mismatched command replay')
        for key in ('q', 'object_pos', 'object_vel', 'object_quat', 'object_contact_force'):
            maxima[key] = max(maxima[key], numeric_error(row[key], target[key]))
        state = row['adapter_state']
        pose = np.asarray(state['root_pose']).reshape(-1)
        velocity = np.asarray(state['root_velocity']).reshape(-1)
        maxima['public_state'] = max(maxima['public_state'],
            numeric_error(pose[:3].tolist(), row['object_pos']),
            numeric_error(pose[3:].tolist(), row['object_quat']),
            numeric_error(velocity[:3].tolist(), row['object_vel']))
        contact = {key: np.asarray(value) for key, value in row['contacts'].items()}
        a, b = contact['link_a'].reshape(-1), contact['link_b'].reshape(-1)
        valid = contact['valid_mask'].reshape(-1).astype(bool)
        fa, fb = contact['force_a'].reshape(-1, 3), contact['force_b'].reshape(-1, 3)
        if not np.isfinite(fa).all() or not np.isfinite(fb).all():
            raise ValueError('Nonfinite native contact force')
        for name, other in others.items():
            force = fa[valid & (a == cube) & (b == other)].sum(axis=0)
            force += fb[valid & (b == cube) & (a == other)].sum(axis=0)
            maxima['public_force'] = max(maxima['public_force'],
                numeric_error(row['adapter_forces'][name], force.tolist()))
    for key, value in maxima.items():
        tolerance = 1e-7 if 'force' in key else 1e-9
        if value > tolerance:
            failures.append(key)
    for force in initial['adapter_reset_sensors'].values():
        if np.count_nonzero(force):
            failures.append('stale_reset_contact')
    return {**result, 'passed': not failures, 'maximum_absolute_errors': maxima}


def score_physics(candidate, reference_initial):
    """Strip the declared single-env axis, then use the existing physical scorer."""
    from dexlab.genesis_pinch_score import score_trial as physical_score

    def depth(value):
        return 1 + depth(value[0]) if isinstance(value, list) and value else 0

    def normalize(value, target):
        while depth(value) > depth(target) and len(value) == 1:
            value = value[0]
        if isinstance(value, list) and isinstance(target, list) and len(value) == len(target):
            return [normalize(a, b) for a, b in zip(value, target)]
        return value

    record = copy.deepcopy(candidate)
    for key, value in reference_initial.items():
        if isinstance(value, list):
            record['initial'][key] = normalize(record['initial'][key], value)
    for row in record['samples']:
        for key in ('q', 'object_pos', 'object_vel', 'object_quat'):
            row[key] = normalize(row[key], [0., 0., 0.])
        row['object_contact_force'] = normalize(row['object_contact_force'], [[0., 0., 0.]])
        contacts = row['contacts']
        if len(contacts['valid_mask']) != 1:
            raise ValueError('Physical scoring requires one environment')
        valid = contacts['valid_mask'][0]
        if any(len(value) != 1 or len(value[0]) != len(valid) for value in contacts.values()):
            raise ValueError('Malformed batched contact ledger')
        row['contacts'] = {
            key: [value[0][i] for i, selected in enumerate(valid) if selected]
            for key, value in contacts.items()}
    return physical_score(record, .0005)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('reference_root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    reference = json.loads((args.candidate / 'reference.json').read_text())
    results = {}
    for name, provenance in reference['trials'].items():
        source = args.reference_root / provenance['source_trial'] / 'run'
        condition = name.rsplit('-', 1)[0]
        raw = (source / f'{condition}-0.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != provenance['sha256']:
            raise ValueError('Native trace hash mismatch')
        native = json.loads(raw)
        native['initial'] = provenance['initial']
        candidate = json.loads((args.candidate / name).read_text())
        results[name] = score_trial(candidate, native)
        results[name]['physical'] = score_physics(candidate, provenance['initial'])
    repeats = {}
    for condition in ('pinch', 'open_negative'):
        first = json.loads((args.candidate / f'{condition}-0.json').read_text())
        second = json.loads((args.candidate / f'{condition}-1.json').read_text())
        repeats[condition] = score_trial(second, first)
    args.output.write_text(json.dumps({'trials': results, 'reset_repeats': repeats,
        'passed': all(result['passed'] and result['physical']['passed'] for result in results.values())
                  and all(result['passed'] for result in repeats.values())}, indent=2) + '\n')



if __name__ == '__main__':
    main()
