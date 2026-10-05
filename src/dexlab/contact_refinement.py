"""Shared-time trajectory differences, not exact errors or hardware accuracy."""
from dataclasses import asdict

import numpy as np


def compare_grids(coarse_case, coarse, fine_case, fine, *, same_grid=False):
    """Compare nested grids with matching physical settings and observed starts.

    Inputs are independently integrity-verified records. Native solver/contact
    profiles and history initialization must additionally be checked by callers.
    This function never infers convergence or changes a physical verdict.
    """
    result = {'comparable': False, 'reason': None, 'metrics': None}
    left, right = asdict(coarse_case), asdict(fine_case)
    for key in ('name', 'timestep'):
        left.pop(key)
        right.pop(key)
    if left != right:
        return result | {'reason': 'physical_protocol_mismatch'}
    ratio = coarse_case.timestep / fine_case.timestep
    stride = round(ratio)
    minimum_stride = 1 if same_grid else 2
    if (same_grid and ratio != 1) or stride < minimum_stride or not np.isclose(ratio, stride, rtol=0, atol=1e-10):
        return result | {'reason': 'grids_not_nested_refinements'}
    records = []
    try:
        for case, data in ((coarse_case, coarse), (fine_case, fine)):
            t, pose, velocity = (np.asarray(data[k], dtype=float)
                                 for k in ('time', 'pose', 'velocity'))
            n = case.steps + 1
            if t.shape != (n,) or pose.shape != (n, 7) or velocity.shape != (n, 6):
                return result | {'reason': 'incomplete_state_coverage'}
            if not all(np.isfinite(x).all() for x in (t, pose, velocity)):
                return result | {'reason': 'nonfinite_state'}
            if not np.allclose(t, np.arange(n) * case.timestep, rtol=0, atol=1e-10):
                return result | {'reason': 'invalid_time_grid'}
            if not np.allclose(np.linalg.norm(pose[:, 3:], axis=1), 1, rtol=0, atol=1e-8):
                return result | {'reason': 'invalid_orientation'}
            records.append((t, pose, velocity))
    except (KeyError, TypeError, ValueError):
        return result | {'reason': 'malformed_record'}
    t, p, v = records[0]
    tf, pf, vf = (x[::stride] for x in records[1])
    if t.shape != tf.shape or not np.allclose(t, tf, rtol=0, atol=1e-10):
        return result | {'reason': 'shared_times_mismatch'}
    same_start = (np.allclose(p[0, :3], pf[0, :3], rtol=0, atol=1e-12)
                  and np.allclose(v[0], vf[0], rtol=0, atol=1e-12)
                  and np.isclose(abs(p[0, 3:] @ pf[0, 3:]), 1, rtol=0, atol=1e-12))
    if not same_start:
        return result | {'reason': 'observed_initial_state_mismatch'}
    position = np.linalg.norm(p[:, :3] - pf[:, :3], axis=1)
    speed = np.linalg.norm(v[:, :3] - vf[:, :3], axis=1)
    angular = np.linalg.norm(v[:, 3:] - vf[:, 3:], axis=1)
    # Quaternion sign is unobservable. Normalize before angular comparison.
    q = p[:, 3:] / np.linalg.norm(p[:, 3:], axis=1)[:, None]
    qf = pf[:, 3:] / np.linalg.norm(pf[:, 3:], axis=1)[:, None]
    angle = 2 * np.arccos(np.clip(np.abs(np.sum(q*qf, axis=1)), 0, 1))
    metrics = {'shared_samples': len(t), 'coarse_timestep_s': coarse_case.timestep,
               'fine_timestep_s': fine_case.timestep}
    for name, values in (('position_m', position), ('linear_velocity_m_s', speed),
                         ('angular_velocity_rad_s', angular), ('orientation_rad', angle)):
        metrics['maximum_' + name] = float(values.max())
        metrics['rms_' + name] = float(np.sqrt(np.mean(values**2)))
    return {'comparable': True, 'reason': None, 'metrics': metrics}


def matching_profiles(left, right, *, varying_solver=False):
    """Require native readbacks and frozen source; absence is not agreement."""
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    engine = left.get('engine')
    if engine not in ('mujoco', 'superdex') or engine != right.get('engine'):
        return False
    sources = left.get('source_sha256')
    if not sources or sources != right.get('source_sha256'):
        return False
    common = ('identity', 'mass_readback', 'inertia_readback', 'friction_readback',
              'normal_parameters_readback', 'solver')
    extra = ('geometry_readback',) if engine == 'mujoco' else ('actor_contact_parameters',)
    a, b = left.get('native', {}), right.get('native', {})
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    if varying_solver:
        mutable = {"iterations", "tolerance"} if engine == "mujoco" else {
            "iterations", "absolute_tolerance", "relative_tolerance"}
        first, second = a.get("solver"), b.get("solver")
        if not isinstance(first, dict) or not isinstance(second, dict):
            return False
        if first.keys() != second.keys() or first == second:
            return False
        fixed_first = {key: value for key, value in first.items() if key not in mutable}
        fixed_second = {key: value for key, value in second.items() if key not in mutable}
        if fixed_first != fixed_second:
            return False
        common = tuple(key for key in common if key != "solver")
    return all(key in a and a[key] is not None and key in b and a[key] == b[key]
               for key in common + extra)


def compare_archives(coarse_directory, fine_directory, *, varying_solver=False):
    """Retain physical scores independently of a trusted grid comparison."""
    import json
    from pathlib import Path
    from dexlab.contact_plane import PlaneCase
    from dexlab.contact_plane_native import verify

    integrity = ('native_run_completed', 'source_unchanged',
                 'archived_source_hashes_match', 'clean_shutdown',
                 'declared_limits', 'artifact_hashes_match', 'contact_ledger_matches')
    receipts, records, scores = [], [], []
    try:
        for directory in (Path(coarse_directory), Path(fine_directory)):
            scores.append(verify(directory))
            receipts.append(json.loads((directory / 'run.json').read_text()))
            with np.load(directory / 'states.npz', allow_pickle=False) as saved:
                records.append(dict(saved))
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return {'comparable': False, 'reason': 'unreadable_archive', 'metrics': None,
                'physical_scores': scores, 'error_type': type(exc).__name__}
    if not all(score['checks'].get(key, False) for score in scores for key in integrity):
        comparison = {'comparable': False, 'reason': 'untrusted_archive', 'metrics': None}
    elif any(receipt.get("solver_overrides") and not score["checks"].get("solver_overrides_match", False)
             for receipt, score in zip(receipts, scores)):
        comparison = {"comparable": False, "reason": "unapplied_solver_controls", "metrics": None}
    elif not matching_profiles(*receipts, varying_solver=varying_solver):
        comparison = {'comparable': False, 'reason': 'native_profile_or_source_mismatch',
                      'metrics': None}
    else:
        comparison = compare_grids(PlaneCase(**receipts[0]['case']), records[0],
                                   PlaneCase(**receipts[1]['case']), records[1], same_grid=varying_solver)
    return comparison | {'physical_scores': scores,
                         'physical_passed': [score['passed'] for score in scores]}
