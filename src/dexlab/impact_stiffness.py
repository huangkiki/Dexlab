"""Compare verified impact records under a separate geometric overlap budget."""

import argparse
import itertools
import json
from pathlib import Path
import time

import numpy as np

from dexlab.impact_score import file_hash, score_campaign


def validate_pair(baseline, current):
    """Require matching physical settings and the exact published baseline traces."""
    old = baseline['protocol']
    new = current['protocol']
    shared = ('version', 'radius_m', 'initial_x_m', 'duration_s', 'score_window_s',
              'stiffness_s2', 'impedance', 'limits')
    if any(old[key] != new[key] for key in shared):
        raise ValueError('Baseline physical settings or original thresholds differ')
    if baseline['campaign']['manifest_sha256'] != new['baseline_manifest_sha256']:
        raise ValueError('Baseline manifest binding mismatch')
    if baseline['campaign']['runtime']['code_sha256'] != current['campaign']['runtime']['code_sha256']:
        raise ValueError('Native runtime code differs between campaigns')
    if new['overlap_budget_m'] != .001:
        raise ValueError('Frozen overlap budget mismatch')
    selected = []
    results = {result['id']: result for result in baseline['results']}
    cases = {case['id']: case for case in old['cases']}
    for binding in new['baseline_bindings']:
        result = results[binding['id']]
        if any(result[key] != binding[key] for key in ('trace_sha256', 'xml_sha256')):
            raise ValueError('Published baseline artifact binding mismatch')
        case = cases[binding['id']]
        if case['masses_kg'] != [1., 1.] or case['initial_vx_m_s'][1] != 0.:
            raise ValueError('Baseline must contain isolated equal-mass cases')
        selected.append((case, result))
    grid = set(itertools.product((.5, 1., 2.), (.001, .0005, .00025)))
    old_grid = {(case['initial_vx_m_s'][0], case['timestep']) for case, _ in selected}
    if len(selected) != 9 or old_grid != grid:
        raise ValueError('Baseline selection is incomplete or duplicated')
    expected = {(k, u, h) for k in (100000., 1000000.) for u, h in grid}
    actual = {(case['stiffness_s2'], case['initial_vx_m_s'][0], case['timestep'])
              for case in new['cases']}
    if len(new['cases']) != 18 or actual != expected:
        raise ValueError('New stiffness grid differs from preregistration')
    if any(case['masses_kg'] != [1., 1.] or case['initial_vx_m_s'][1] != 0.
           for case in new['cases']):
        raise ValueError('New cases change masses or target velocity')
    return selected


def make_row(protocol, case, result, forces, contact_count, *, reused):
    """Add geometric feasibility without altering historical physical verdicts."""
    force = np.asarray(forces)[:, 0, :]
    h = case['timestep']
    measured_impulse = np.sum(force, axis=0) * h
    reference_impulse = case['masses_kg'][0] * (
        result['reference_velocity_m_s'][0] - case['initial_vx_m_s'][0])
    overlap_passed = result['penetration_m'] <= protocol['overlap_budget_m']
    return dict(
        id=case['id'], reused=reused,
        stiffness_s2=case.get('stiffness_s2', protocol['stiffness_s2']),
        speed_m_s=case['initial_vx_m_s'][0], timestep_s=h,
        final_state_passed=result['passed'], overlap_passed=overlap_passed,
        joint_passed=result['passed'] and overlap_passed,
        metrics=result['metrics'], penetration_m=result['penetration_m'],
        peak_force_n=float(np.max(np.linalg.norm(force, axis=1))),
        impulse_vector_ns=measured_impulse.tolist(),
        impulse_error_ns=float(np.linalg.norm(measured_impulse - [reference_impulse, 0, 0])),
        contact_duration_s=float(np.count_nonzero(contact_count) * h),
        steps=len(contact_count), timing=result['timing'],
        trace_sha256=result['trace_sha256'], xml_sha256=result['xml_sha256'],
    )


def compare(baseline_root, current_root):
    started = time.perf_counter()
    baseline = score_campaign(baseline_root)
    current = score_campaign(current_root)
    selected = validate_pair(baseline, current)
    protocol = current['protocol']
    groups = [(baseline_root, selected, True),
              (current_root, zip(protocol['cases'], current['results']), False)]
    rows = []
    for root, cases, reused in groups:
        for case, result in cases:
            with np.load(root / case['id'] / 'trace.npz', allow_pickle=False) as trace:
                rows.append(make_row(protocol, case, result, trace['forces'],
                                     trace['contact_count'], reused=reused))
    return dict(
        protocol=protocol, baseline_campaign=baseline['campaign'],
        new_campaign=current['campaign'], results=rows,
        reused_cases=9, new_cases=18,
        final_state_passed=sum(row['final_state_passed'] for row in rows),
        joint_passed=sum(row['joint_passed'] for row in rows),
        scorer_sha256=file_hash(Path(__file__)),
        scoring_wall_s=time.perf_counter() - started,
    )


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
