"""Reproduce the complete prospective cohort without discarding physical failures."""
import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.contact_transfer import geometry_observation, initial_state_matches, validate_plan
from normal_response import rescore


def summarize(root):
    plan = json.loads((root/'suite.json').read_text())
    validate_plan(plan)
    verification = rescore(root)
    report = json.loads((root/'report.json').read_text())
    rows = []
    for job, result in zip(plan['jobs'], report['results'], strict=True):
        folder = root/'raw'/job['id']
        receipt = json.loads((folder/'run.json').read_text())
        with np.load(folder/'states.npz', allow_pickle=False) as data:
            initial = (len(data['time']) > 0 and initial_state_matches(
                job['case'], data['time'][0], data['pose'][0], data['velocity'][0]))
            minimum_normal_force = (float(data['contact_force'][:,2].min())
                                    if len(data['contact_force']) else None)
        mesh = None
        if (folder/'geometry.npz').is_file():
            with np.load(folder/'geometry.npz', allow_pickle=False) as data:
                mesh = {key:data[key] for key in ('vertices','faces')}
        geometry = geometry_observation(job['engine'],job['case'],receipt.get('native',{}),mesh)
        required = ('native_run_completed','native_mass_matches','native_inertia_matches',
                    'normal_parameters_match','declared_force_commands')
        completeness = {key:result['result']['checks'].get(key, False) for key in required}
        completeness.update(actual_initial_state_matches=bool(initial),
                            checked_representation_matches=geometry['representation_matches'])
        windows = result['transient']['metrics'].get('windows',[])
        rows.append({'id':job['id'],'seed':job['seed'],'profile':job['profile_id'],
                     'mass_kg':job['case']['mass'],'half_size_m':job['case']['half_size'],
                     'observed_comparison_checks':completeness,
                     'observed_comparison_complete':all(completeness.values()),
                     'representation':geometry,
                     'physics_passed':result['result']['passed'],
                     'transient_passed':result['transient']['passed'],
                     'worst_window_rms_m':max((w['rms_error_m'] for w in windows),default=None),
                     'peak_error_m':max((w['peak_error_m'] for w in windows),default=None),
                     'minimum_recorded_normal_force_n':minimum_normal_force,
                     'maximum_penetration_m':result['result']['metrics'].get('maximum_penetration_m'),
                     'episode_wall_seconds':result.get('episode_wall_seconds'),
                     'failed_checks':sorted({key for score in (result['result'],result['transient'])
                                            for key,passed in score['checks'].items() if not passed})})
    return {'verification':verification,'declared_episodes':30,
            'observed_comparison_complete':sum(r['observed_comparison_complete'] for r in rows),
            'results':rows,
            'scope':'Prospective synthetic-reference profile transfer. Input-mesh checks do not observe internal cooking; no engine equivalence or hardware accuracy claim.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(summarize(args.directory),indent=2))
