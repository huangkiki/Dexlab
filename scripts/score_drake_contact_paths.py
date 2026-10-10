"""Score every frozen Drake case, retaining invalid and failed observations."""

import argparse
import json
from pathlib import Path

from dexlab.drake_incline_score import score_campaign
from dexlab.incline_score import ImpulseConsistencyError, file_hash


def score_profiles(frozen, campaign):
    manifest = json.loads((frozen / 'manifest.json').read_text())
    expected = [entry for entry in manifest['cases'] if entry['kind'] == 'formal']
    ledger = json.loads((campaign / 'ledger.json').read_text())
    by_id = {(entry['profile'], entry['case']): entry for entry in ledger}
    if len(by_id) != len(ledger) or set(by_id) != {(e['profile'], e['case']) for e in expected}:
        raise ValueError('Missing or duplicate acquisition ledger entries')
    profiles = {}
    for entry in expected:
        name, case_id = entry['profile'], entry['case']
        receipt = by_id[name, case_id]
        source = receipt.get('source_campaign', campaign.name)
        if Path(source).name != source:
            raise ValueError('Campaign reference must be an adjacent directory')
        root = campaign.parent / source / name / case_id
        protocol = json.loads((frozen / entry['protocol']).read_text())
        if file_hash(root / 'protocol.json') != entry['protocol_sha256']:
            raise ValueError('Changed frozen protocol')
        for path, digest in manifest['source_hashes'].items():
            archived = root / 'source' / Path(path).name
            if archived.exists() and file_hash(archived) != digest:
                raise ValueError('Recorder/scorer changed after freezing')
        try:
            result = score_campaign(root)['results'][0]
        except ValueError as error:
            result = dict(id=case_id, record_valid=False, passed=False,
                          expected_negative=protocol['cases'][0].get('negative_no_floor', False),
                          failure=str(error), checks={'record_valid': False}, metrics=None)
            if isinstance(error, ImpulseConsistencyError):
                result['impulse_residual_max_ns'] = error.residual
        result['protocol_sha256'] = entry['protocol_sha256']
        profiles.setdefault(name, []).append(result)
    summary = {}
    for name, results in profiles.items():
        positives = [r for r in results if not r['expected_negative']]
        negatives = [r for r in results if r['expected_negative']]
        summary[name] = dict(
            positive_passed=sum(r['passed'] for r in positives), positive_total=len(positives),
            invalid_positive=sum(not r['record_valid'] for r in positives),
            valid_rejected_negative=sum(r['record_valid'] and not r['passed'] for r in negatives),
            negative_total=len(negatives), results=results)
    return dict(profiles=summary, manifest_sha256=file_hash(frozen / 'manifest.json'),
                scorer_sha256=file_hash(Path(__file__)),
                scope='Fixed native configurations; old kLagged/hydroelastic retained separately; no coverage-v1 admission')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(score_profiles(args.frozen, args.campaign), stream, indent=2, allow_nan=False)
        stream.write('\n')
