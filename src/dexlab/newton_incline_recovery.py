"""Offline provenance checks for a separately recovered Newton negative."""

import gzip
import json
from pathlib import Path

from dexlab.incline_score import file_hash


def validate_recovery(root, campaign, protocol):
    recovery = campaign['continuation']
    original = root / 'interrupted-attempt'
    if (file_hash(original / 'campaign.json') != recovery['original_campaign_sha256']
            or file_hash(root / 'continuation.py') != recovery['runner_sha256']):
        raise ValueError('Changed recovery provenance')
    previous = json.loads((original / 'campaign.json').read_text())
    if (previous['state'] != 'interrupted' or previous['admission_only']
            or len(previous['cases']) != len(protocol['cases'])
            or campaign['cases'][:-1] != previous['cases'][:-1]
            or campaign['packages'] != previous['packages']):
        raise ValueError('Recovery changed completed positives or runtime')
    for name, key in [('manifest.json', 'protocol_sha256'), ('recorder.py', 'recorder_sha256'),
                      ('official-proof.json', 'proof_sha256')]:
        if file_hash(original / name) != campaign[key] or previous[key] != campaign[key]:
            raise ValueError('Recovery changed frozen source, proof or protocol')
    interrupted = previous['cases'][-1]
    case = protocol['cases'][-1]
    if (interrupted['case'] != case or not case.get('negative_no_floor', False)
            or recovery['replaced_case'] != case['id']
            or not isinstance(interrupted['error'], str)
            or not interrupted['error'].startswith('KeyboardInterrupt:')
            or recovery['original_completed_steps'] != interrupted['completed_steps']):
        raise ValueError('Recovery did not preserve the interrupted negative')
    completed = interrupted['completed_steps']
    if not 0 < completed < round(protocol['duration_s'] / case['timestep']):
        raise ValueError('Not an incomplete negative')
    for item, expected in zip(previous['cases'], protocol['cases'], strict=True):
        directory = original / expected['id']
        if item['case'] != expected or item != json.loads((directory / 'metadata.json').read_text()):
            raise ValueError('Changed original case metadata')
        if item is not interrupted and (item['error'] or
                item['completed_steps'] != round(protocol['duration_s'] / expected['timestep'])):
            raise ValueError('An incomplete positive cannot be reused')
        for name, digest in item['hashes'].items():
            if Path(name).name != name or file_hash(directory / name) != digest:
                raise ValueError('Changed original case artifact')
        if item['hashes'].get('admission.json') != protocol['admission_sha256'][expected['id']]:
            raise ValueError('Original admission differs from freeze')
    with gzip.open(original / case['id'] / 'steps.jsonl.gz', 'rt') as stream:
        old_rows = [json.loads(line) for line in stream]
    with gzip.open(root / case['id'] / 'steps.jsonl.gz', 'rt') as stream:
        new_rows = [json.loads(line) for line in stream]
    if len(old_rows) < completed or len(new_rows) < completed:
        raise ValueError('Missing recovery overlap')
    for before, after in zip(old_rows[:completed], new_rows[:completed], strict=True):
        if before['state'] != after['state'] or before['net_force'] != after['net_force']:
            raise ValueError('Recovered state/force prefix differs from original')
    return dict(reused_positive_cases=len(protocol['cases']) - 1,
                preserved_interrupted_attempt=True, identical_prefix_steps=completed,
                original_campaign_sha256=recovery['original_campaign_sha256'],
                continuation_runner_sha256=recovery['runner_sha256'])
