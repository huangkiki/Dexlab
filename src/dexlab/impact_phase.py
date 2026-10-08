"""Hash-bound finite arrival-phase sensitivity, scored without a physics engine."""
import argparse
import itertools
import json
from pathlib import Path
import time

import numpy as np

from dexlab.impact_score import file_hash, score_campaign
from dexlab.impact_stiffness import make_row


def validate_pair(baseline, current):
    old, new = baseline['protocol'], current['protocol']
    shared = ('version', 'radius_m', 'initial_x_m', 'duration_s', 'score_window_s',
              'stiffness_s2', 'impedance', 'limits', 'overlap_budget_m')
    if any(old[key] != new[key] for key in shared):
        raise ValueError('Baseline settings or thresholds differ')
    if baseline['campaign']['manifest_sha256'] != new['baseline_manifest_sha256']:
        raise ValueError('Baseline manifest mismatch')
    if baseline['campaign']['runtime']['code_sha256'] != current['campaign']['runtime']['code_sha256']:
        raise ValueError('Native runtime mismatch')
    if new['overlap_budget_m'] != .001 or new['case_budget'] != 27:
        raise ValueError('Frozen budget mismatch')
    cases = {case['id']: case for case in old['cases']}
    results = {result['id']: result for result in baseline['results']}
    selected = []
    for binding in new['baseline_bindings']:
        case, result = cases[binding['id']], results[binding['id']]
        if any(result[key] != binding[key] for key in ('trace_sha256', 'xml_sha256')):
            raise ValueError('Baseline artifact mismatch')
        selected.append((case, result))
    grid = set(itertools.product((.5, 1., 2.), (.001, .0005, .00025)))
    if len(selected) != 9 or {(c['initial_vx_m_s'][0], c['timestep']) for c, _ in selected} != grid:
        raise ValueError('Incomplete baseline grid')
    expected = {(u, h, a) for u, h in grid for a in (.25, .5, .75)}
    actual = {(c['initial_vx_m_s'][0], c['timestep'], c['arrival_phase']) for c in new['cases']}
    if len(new['cases']) != 27 or actual != expected:
        raise ValueError('Incomplete phase grid')
    for case in [c for c, _ in selected] + new['cases']:
        u, h = case['initial_vx_m_s'][0], case['timestep']
        a = case.get('arrival_phase', 0.)
        if (case['masses_kg'] != [1., 1.] or case['initial_vx_m_s'][1] != 0.
                or case['stiffness_s2'] != 1e6
                or case.get('initial_x_m', old['initial_x_m']) != [-.06, .06+u*h*a]):
            raise ValueError('Phase mapping or physical conditions differ')
    return selected


def phase_row(protocol, case, result, trace, *, reused):
    row = make_row(protocol, case, result, trace['forces'], trace['contact_count'], reused=reused)
    x = case.get('initial_x_m', protocol['initial_x_m'])
    arrival = (x[1]-x[0]-2*protocol['radius_m'])/case['initial_vx_m_s'][0]
    first = int(np.flatnonzero(trace['contact_count'])[0])
    first_time = float(trace['force_times'][first])
    row.update(arrival_phase=case.get('arrival_phase', 0.),
               ballistic_arrival_s=arrival, first_contact_epoch_s=first_time,
               contact_onset_delay_s=first_time-arrival,
               overlap_boundary_only=abs(row['penetration_m']-protocol['overlap_budget_m']) <= 1e-12)
    return row


def summarize(rows):
    groups = []
    for u, h in itertools.product((.5, 1., 2.), (.001, .0005, .00025)):
        values = [r for r in rows if r['speed_m_s'] == u and r['timestep_s'] == h]
        if len(values) != 4 or {r['arrival_phase'] for r in values} != {0., .25, .5, .75}:
            raise ValueError('Each group requires exactly four distinct phases')
        extrema = {}
        for name in ('velocity_error_m_s', 'relative_energy_error', 'penetration_m'):
            numbers = [r[name] if name in r else r['metrics'][name] for r in values]
            extrema[name] = dict(minimum=min(numbers), maximum=max(numbers), span=max(numbers)-min(numbers))
        groups.append(dict(speed_m_s=u, timestep_s=h, cases=[r['id'] for r in values],
                           tested_phases=4, joint_passes=sum(r['joint_passed'] for r in values),
                           finite_phase_set_passed=all(r['joint_passed'] for r in values), extrema=extrema))
    if len(rows) != 36:
        raise ValueError('Unexpected cases outside frozen grid')
    return groups


def compare(baseline_root, current_root):
    started = time.perf_counter()
    baseline, current = score_campaign(baseline_root), score_campaign(current_root)
    selected = validate_pair(baseline, current)
    protocol = current['protocol']
    rows = []
    for root, cases, reused in ((baseline_root, selected, True),
                               (current_root, zip(protocol['cases'], current['results']), False)):
        for case, result in cases:
            with np.load(root/case['id']/'trace.npz', allow_pickle=False) as trace:
                rows.append(phase_row(protocol, case, result, trace, reused=reused))
    return dict(protocol=protocol, baseline_campaign=baseline['campaign'],
                new_campaign=current['campaign'], results=rows, groups=summarize(rows),
                reused_cases=9, new_cases=27,
                final_state_passed=sum(r['final_state_passed'] for r in rows),
                joint_passed=sum(r['joint_passed'] for r in rows),
                scorer_sha256=file_hash(Path(__file__)), scoring_wall_s=time.perf_counter()-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.baseline, args.input)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
