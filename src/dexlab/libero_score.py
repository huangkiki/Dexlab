"""Offline LIBERO evidence checks; task success and physical diagnostics stay separate."""
import argparse
import json
from pathlib import Path

from dexlab.libero_workflow import TASK, file_hash


def rotation(quaternion):
    import numpy as np
    w, x, y, z = quaternion
    return np.array([[1 - 2*(y*y + z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def momentum_residual(physics, mass, gravity, inertial_offset):
    """Free-joint angular velocities are local; compare world COM momentum."""
    import numpy as np
    r0 = np.asarray([rotation(q) for q in physics[:, 18:22]])
    r1 = np.asarray([rotation(q) for q in physics[:, 22:26]])
    offset0, offset1 = r0 @ inertial_offset, r1 @ inertial_offset
    omega0 = np.einsum('nij,nj->ni', r0, physics[:, 26:29])
    omega1 = np.einsum('nij,nj->ni', r1, physics[:, 29:32])
    v0 = physics[:, 3:6] + np.cross(omega0, offset0)
    v1 = physics[:, 6:9] + np.cross(omega1, offset1)
    dt = physics[:, 1] - physics[:, 0]
    expected = dt[:, None] * (physics[:, 9:12] + mass * gravity)
    residual = mass * (v1 - v0) - expected
    return np.linalg.norm(residual, axis=1) / (dt * mass * np.linalg.norm(gravity))


def score(directory):
    import numpy as np
    directory = Path(directory)
    run = json.loads((directory / 'run.json').read_text())
    checks = {'task_identity': run['task'] == TASK,
              'completed': run['status'] == 'completed',
              'source_hashes': all(file_hash(directory / name) == sha for name, sha in run['files'].items()),
              'parameters_stable': json.loads((directory / 'parameters-after.json').read_text()) ==
                                   json.loads((directory / 'parameters-effective.json').read_text())}
    before = json.loads((directory / 'parameters-before.json').read_text())
    expected = json.loads(json.dumps(before))
    expected['options']['timestep'] *= run['candidate']['timestep_scale']
    expected['model_timestep'] *= run['candidate']['timestep_scale']
    for key in ('geom_solref', 'pair_solref'):
        for ref in expected['arrays'].get(key, []):
            if ref[0] > 0:
                ref[0] = max(ref[0], run['candidate'].get('solref_floor_s', 0.))
    checks['requested_parameters_match'] = expected == json.loads((directory / 'parameters-effective.json').read_text())
    result = {'checks': checks, 'native_success_any': run['native_success_any'],
              'native_success_final': run['native_success_final'],
              'physical_acceptance': 'not-evaluated', 'policy_closed_loop_evaluated': False}
    with np.load(directory / 'trajectory.npz', allow_pickle=False) as record:
        checks['finite'] = all(np.isfinite(record[key]).all() for key in record.files)
        if run['candidate']['mode'] == 'observation-audit':
            audit = json.loads((directory / 'observation-audit.json').read_text())
            checks['settle_duration'] = abs(audit['fresh_time_s'] - audit['initial_time_s'] - .25) < 1e-8
            result['observation_audit'] = audit
        else:
            state, times, actions = record['state'], record['time'], record['actions']
            checks['full_actions'] = len(actions) == len(state) == len(times) == len(record['success']) == run['expected_actions'] == run['actions_executed']
            checks['terminal_state'] = bool(len(state) and abs(state[-1, 0] - run['final_time_s']) < 1e-9
                                            and abs(record['initial'][0] - run['initial_time_s']) < 1e-9)
            checks['clock'] = bool(len(times) and np.all(np.diff(times) > 0)
                                   and np.allclose(actions[:, 1], times, atol=1e-10, rtol=0)
                                   and np.allclose(state[:, 0], times, atol=1e-10, rtol=0)
                                   and np.allclose(actions[:, 1]-actions[:, 0], expected['control_timestep'], atol=1e-9, rtol=0))
            checks['success_readback'] = bool(np.array_equal(record['success'], record['success'].astype(bool))
                                              and bool(np.any(record['success'])) == run['native_success_any']
                                              and bool(record['success'][-1]) == run['native_success_final'])
            qadr = run['object_qpos_adr']
            height = state[:, 1 + qadr + 2]
            result['height_m'] = {'initial': float(record['initial'][1 + qadr + 2]),
                                  'max': float(np.max(height)), 'final': float(height[-1])}
        if run['candidate']['instrument']:
            physics = record['physics']
            checks['native_substeps_present'] = bool(physics.ndim == 2 and physics.shape[1] == 32 and len(physics))
            if checks['native_substeps_present']:
                checks['force_state_clock'] = bool(np.all(physics[:, 1] > physics[:, 0])
                                                   and np.allclose(physics[1:, 0], physics[:-1, 1], atol=1e-10, rtol=0))
                contacts = [json.loads(line) for line in (directory / 'contacts.jsonl').read_text().splitlines()]
                checks['contact_readback_complete'] = len(contacts) == len(physics) and all(
                    len(c['contacts']) == int(p[17]) and abs(c['time_s'] - p[0]) < 1e-10
                    and abs(c['state_after_s'] - p[1]) < 1e-10
                    and np.allclose(np.sum([r['world_force_on_object'] for r in c['contacts']], axis=0)
                                    if c['contacts'] else np.zeros(3), p[9:12], atol=1e-10, rtol=0)
                    for c, p in zip(contacts, physics))
                checks['full_physics_window'] = bool(abs(physics[0, 0] - run['initial_time_s']) < 1e-9
                                                         and abs(physics[-1, 1] - run['final_time_s']) < 1e-9
                                                         and np.allclose(physics[:, 1]-physics[:, 0], expected['options']['timestep'], atol=1e-10, rtol=0))
                params = json.loads((directory / 'parameters-effective.json').read_text())
                body = params['object_body_id']
                mass = params['arrays']['body_mass'][body]
                child_mass = sum(params['arrays']['body_mass'][i] for i in run['object_body_ids'] if i != body)
                diagnostics = {'object_mass_kg': mass, 'max_overlap_m': float(max(physics[:, 16])),
                               'max_finger_normal_n': float(max(physics[:, 15])),
                               'contact_samples': int(np.sum(physics[:, 17] > 0))}
                if mass > 0 and child_mass == 0:
                    residual = momentum_residual(physics, mass, np.asarray(params['gravity']),
                                                 np.asarray(params['arrays']['body_ipos'][body]))
                    diagnostics['momentum_residual_weight_fraction'] = {
                        'median': float(np.median(residual)), 'p99': float(np.quantile(residual, .99)),
                        'max': float(max(residual))}
                    # Reuse DexLab's declared numerical thresholds as diagnostics,
                    # not a measured material law or a new task-coverage acceptance.
                    result['physical_acceptance'] = ('diagnostic-pass' if np.quantile(residual, .99) <= .05
                                                       and max(physics[:, 16]) <= .001 else 'diagnostic-fail')
                else:
                    result['physical_acceptance'] = 'unsupported-composite-target'
                result['physics'] = diagnostics
        else:
            result['physical_acceptance'] = 'not-recorded-parity-control'
    result['observation_valid'] = all(checks.values())
    if not result['observation_valid']:
        result['physical_acceptance'] = 'invalid-record'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = score(args.directory)
    print(json.dumps(result, indent=2, allow_nan=False))
    if not result['observation_valid']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
