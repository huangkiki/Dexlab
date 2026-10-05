"""Reproduce all outcomes and summarize declared serial response-cost repeats."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import median

from normal_response import rescore


def summarize(root):
    verification = rescore(root)
    plan = json.loads((root / 'suite.json').read_text())
    report = json.loads((root / 'report.json').read_text())
    if plan.get('measure_step_timing') is not True:
        raise ValueError('Expected instrumented response-cost protocol')
    groups = defaultdict(list)
    for job, row in zip(plan['jobs'], report['results'], strict=True):
        receipt = json.loads((root / 'raw' / job['id'] / 'run.json').read_text())
        if not row['result']['checks'].get('complete_native_timing'):
            raise ValueError('Missing timing; do not summarize a successful subset')
        groups[job['candidate_id']].append((job, row, receipt))
    output = []
    for candidate, records in groups.items():
        if sorted(j['repeat'] for j, _, _ in records) != [1, 2, 3]:
            raise ValueError('Expected three declared repeats per candidate')
        first = records[0][0]
        for job, _, _ in records:
            if (job['engine'], job['normal_parameters'], {k:v for k,v in job['case'].items() if k != 'name'}) != (
                first['engine'], first['normal_parameters'], {k:v for k,v in first['case'].items() if k != 'name'}
            ):
                raise ValueError('Changed physical conditions within repeat group')
        timings = {
            'native_call_seconds': [r['step_timing']['native_call_seconds'] for _, _, r in records],
            'observation_seconds': [r['step_timing']['observation_seconds'] for _, _, r in records],
            'outer_step_seconds': [r['step_and_observation_seconds'] for _, _, r in records],
            'episode_wall_seconds': [row['episode_wall_seconds'] for _, row, _ in records],
        }
        windows = [window for _, row, _ in records for window in row['transient']['metrics']['windows']]
        output.append({
            'candidate': candidate, 'engine': first['engine'], 'timestep_s': first['case']['timestep'],
            'runs': 3, 'combined_passed': sum(row['result']['passed'] and row['transient']['passed'] for _, row, _ in records),
            'cost': {key:{'minimum':min(values),'median':median(values),'maximum':max(values)} for key, values in timings.items()},
            'worst_window_rms_m': max(w['rms_error_m'] for w in windows),
            'peak_error_m': max(w['peak_error_m'] for w in windows),
            'failed_checks': sorted({key for _, row, _ in records for score in (row['result'], row['transient']) for key, passed in score['checks'].items() if not passed}),
        })
    return {'verification': verification, 'groups': output,
            'scope': 'Worst positive-load window error; three serial fresh-scene repeats. No hardware accuracy or engine ranking.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory), indent=2))
