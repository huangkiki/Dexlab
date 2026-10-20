"""Independent integrity and physics checks for the banana-force protocol."""

import hashlib
import json
from pathlib import Path

import numpy as np


REQUIRED_TRACE = (
    'time_s', 'blade_position_m', 'target_edge_m', 'drive_force_n',
    'material_reaction_n', 'blade_board_impulse_ns', 'momentum_residual_ns',
    'material_resistance_n', 'rigid_support_resistance_n', 'total_resistance_n',
    'actuator_axial_force_n', 'minimum_det_f', 'labelled_particles',
)
EXPECTED_SOURCE_FILES = {
    'src/dexlab/banana_force.py', 'src/dexlab/banana_force_score.py',
    'src/dexlab/cutting.py', 'src/dexlab/cutting_geometry.py', 'src/dexlab/tofu_cut.py',
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _configuration_matches(manifest, protocol):
    config = manifest['config']
    reported = protocol['paper']['specified_values']
    choices = protocol['independent_choices']
    expected = {
        'young_modulus': reported['young_modulus_pa'],
        'poisson_ratio': reported['poisson_ratio'],
        'density': reported['density_kg_m3'],
        'yield_stress': reported['yield_stress_pa'],
        'blade_mass': reported['knife_mass_kg'],
        'friction_static': reported['friction_coefficient'],
        'friction_dynamic': reported['friction_coefficient'],
        'cutting_energy': reported['cutting_energy_j_m2'],
        'sharpness': reported['sharpness'],
        'dynamic_viscosity': 0.,
        'flip_fraction': choices['transfer']['flip_fraction'],
        'drive_stiffness': choices['trajectory']['drive_stiffness_n_m'],
        'drive_damping': choices['trajectory']['drive_damping_n_s_m'],
        'drive_force_limit': choices['trajectory']['drive_force_limit_n'],
        'tangent_stiffness': choices['contact']['tangent_stiffness_scale'],
        'tangent_damping': choices['contact']['tangent_damping_ratio'],
        'size': choices['geometry']['size_m'],
        'blade_half_size': choices['blade']['half_size_m'],
        'blade_bevel_height': choices['blade']['bevel_height_m'],
        'shape': 'banana',
    }
    if any(config.get(name) != value for name, value in expected.items()):
        return False
    refined = manifest['sampling_kind'] == 'hierarchical-refined-centres'
    expected_spacing = (protocol['refinement']['grid_spacing_m'] if refined else
                        choices['geometry']['base_grid_spacing_m'])
    allowed_dt = ({protocol['refinement']['timestep_s']} if refined else
                  set(protocol['sensitivity']['timestep_s']))
    allowed_normal = ({choices['contact']['normal_scale']} if refined else
                      set(protocol['sensitivity']['normal_scale']))
    return (config['grid_spacing'] == expected_spacing and config['dt'] in allowed_dt
            and config['normal_scale'] in allowed_normal)


def _resource_limits_match(manifest, protocol):
    segments = manifest.get('segments')
    if not isinstance(segments, list) or not segments:
        return False
    budget = protocol['execution_budget']
    if len(segments) > budget['maximum_segments_per_case']:
        return False
    expected_start = 0
    for segment in segments:
        limits = segment.get('cgroup_limits')
        try:
            memory = int(limits['memory.max'])
            swap = int(limits['memory.swap.max'])
            quota, period = map(int, limits['cpu.max'].split())
        except (KeyError, TypeError, ValueError):
            return False
        if (segment.get('start_step') != expected_start
                or segment.get('end_step', 0) <= expected_start
                or segment.get('wall_s', np.inf) > budget['checkpoint_segment_wall_s'] + 30
                or memory > budget['memory_mib'] * 1024**2
                or swap > budget['swap_mib'] * 1024**2
                or quota / period > budget['cpu_cores']):
            return False
        expected_start = segment['end_step']
    return expected_start == manifest.get('completed_steps')


def score_force_run(directory):
    """Score saved observations without trusting the runner's summary."""
    directory = Path(directory)
    manifest_path, trace_path = directory / 'manifest.json', directory / 'trace.npz'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('status') != 'complete':
        raise ValueError('Force run is not complete')
    for name in ('trace.npz', 'checkpoint.npz'):
        path = directory / name
        if manifest.get('artifacts', {}).get(name) != _sha256(path):
            raise ValueError(f'Force {name} digest mismatch')
    protocol_path = Path(manifest['protocol_path'])
    if not protocol_path.is_absolute():
        protocol_path = Path(__file__).resolve().parents[2] / protocol_path
    if manifest.get('protocol_sha256') != _sha256(protocol_path):
        raise ValueError('Force protocol digest mismatch')
    protocol = json.loads(protocol_path.read_text())
    root = Path(__file__).resolve().parents[2]
    source_hashes = manifest.get('source_sha256')
    if not isinstance(source_hashes, dict) or set(source_hashes) != EXPECTED_SOURCE_FILES:
        raise ValueError('Force run source identities are missing')
    source_matches = all(_sha256(root / name) == digest
                         for name, digest in source_hashes.items())
    with np.load(trace_path) as archive:
        missing = [name for name in REQUIRED_TRACE if name not in archive.files]
        if missing:
            raise ValueError(f'Force observations are missing: {missing}')
        trace = {name: np.asarray(archive[name]) for name in archive.files}
    count = len(trace['time_s'])
    if not count or any(len(trace[name]) != count for name in REQUIRED_TRACE):
        raise ValueError('Force trace lengths are inconsistent')
    with np.load(directory / 'checkpoint.npz') as checkpoint:
        checkpoint_step = int(checkpoint['step_count'])
    observed = np.concatenate([
        trace['time_s'][:, None], trace['blade_position_m'], trace['target_edge_m'],
        trace['drive_force_n'], trace['material_reaction_n'],
        trace['blade_board_impulse_ns'], trace['momentum_residual_ns'],
        trace['material_resistance_n'][:, None], trace['rigid_support_resistance_n'][:, None],
        trace['total_resistance_n'][:, None], trace['actuator_axial_force_n'][:, None],
        trace['minimum_det_f'][:, None], trace['labelled_particles'][:, None],
    ], axis=1)
    finite = bool(np.isfinite(observed).all())
    dt = float(manifest['config']['dt'])
    material = trace['material_reaction_n'][:, 2]
    support = trace['blade_board_impulse_ns'][:, 2] / dt
    total = material + support
    identity_error = float(max(
        np.max(abs(trace['material_resistance_n'] - material)),
        np.max(abs(trace['rigid_support_resistance_n'] - support)),
        np.max(abs(trace['total_resistance_n'] - total)),
        np.max(abs(trace['actuator_axial_force_n'] + trace['drive_force_n'][:, 2])),
    ))
    support_mask = support > 0
    first_support = int(np.flatnonzero(support_mask)[0]) if support_mask.any() else count
    material_before_support = material[:first_support]
    residual = np.linalg.norm(trace['momentum_residual_ns'], axis=1)
    acceptance = protocol['acceptance']
    checks = {
        'clean_exact_source': not manifest.get('git_dirty', True) and source_matches,
        'configuration_matches_protocol': _configuration_matches(manifest, protocol),
        'bounded_execution': _resource_limits_match(manifest, protocol),
        'timeline_matches_manifest': bool(
            count == manifest.get('completed_steps')
            and checkpoint_step == count
            and abs(trace['time_s'][0] - dt) <= 1e-12
            and abs(trace['time_s'][-1] - manifest['duration_s']) <= 1e-12),
        'finite_observations': finite,
        'force_channel_identity': identity_error <= 1e-12,
        'momentum_balance': float(residual.max()) <= acceptance['maximum_momentum_residual_ns'],
        'positive_jacobian': float(trace['minimum_det_f'].min()) > acceptance['minimum_jacobian'],
        'material_epoch_before_support': bool(first_support > 0 and
                                              np.max(material_before_support, initial=0.) > 0),
        'support_epoch_observed': bool(support_mask.any()),
        'cut_progress_observed': int(trace['labelled_particles'].max()) > 0,
    }
    return {
        'schema_version': 1,
        'case_id': manifest['case_id'],
        'passed': all(checks.values()),
        'checks': checks,
        'sampling_sha256': manifest['sampling_sha256'],
        'particle_count': manifest['particle_count'],
        'timestep_s': dt,
        'normal_scale': manifest['config']['normal_scale'],
        'first_support_time_s': (float(trace['time_s'][first_support])
                                 if first_support < count else None),
        'peak_material_resistance_n_before_support': float(np.max(material_before_support, initial=0.)),
        'peak_support_resistance_n': float(np.max(support, initial=0.)),
        'peak_total_resistance_n': float(np.max(total, initial=0.)),
        'material_impulse_ns_before_support': float(dt * material_before_support.sum()),
        'maximum_momentum_residual_ns': float(residual.max()),
        'minimum_jacobian': float(trace['minimum_det_f'].min()),
        'force_channel_identity_error_n': identity_error,
        'evidence_scope': ('Numerical observations from the independent DexLab protocol; no raw '
                           'robot-force agreement or author-code equivalence claim.'),
    }


def _force_curve(directory):
    with np.load(Path(directory) / 'trace.npz') as trace:
        return np.asarray(trace['time_s']), np.asarray(trace['total_resistance_n'])


def _normalized_rmse(reference_time, reference, candidate_time, candidate, mask=None):
    selected = np.ones(len(reference_time), dtype=bool) if mask is None else mask
    selected &= reference_time >= candidate_time[0]
    selected &= reference_time <= candidate_time[-1]
    if not selected.any():
        return None
    aligned = np.interp(reference_time[selected], candidate_time, candidate)
    scale = max(float(np.ptp(reference[selected])), float(np.max(abs(reference[selected]))), 1e-12)
    return float(np.sqrt(np.mean((aligned - reference[selected])**2)) / scale)


def score_force_suite(directory):
    """Aggregate a declared suite while retaining incomplete and failed cases."""
    directory = Path(directory)
    suite = json.loads((directory / 'suite.json').read_text())
    protocol_path = Path(suite['protocol_path'])
    if not protocol_path.is_absolute():
        protocol_path = Path(__file__).resolve().parents[2] / protocol_path
    if suite['protocol_sha256'] != _sha256(protocol_path):
        raise ValueError('Suite protocol digest mismatch')
    protocol = json.loads(protocol_path.read_text())
    scores, failures = {}, {}
    for spec in suite['cases']:
        case_id = spec['case_id']
        case = directory / 'cases' / case_id
        try:
            scores[case_id] = score_force_run(case)
        except (FileNotFoundError, ValueError, KeyError) as error:
            failures[case_id] = f'{type(error).__name__}: {error}'

    baseline_ids = [f'base-seed-{seed}' for seed in protocol['independent_choices']['sampling']['seeds']]
    baseline_complete = all(case_id in scores for case_id in baseline_ids)
    sampling_hashes = {scores[case_id]['sampling_sha256'] for case_id in baseline_ids if case_id in scores}
    refined_id = 'refined-centres'
    refined_complete = refined_id in scores
    particle_ratio = (scores[refined_id]['particle_count'] / scores['base-seed-0']['particle_count']
                      if refined_complete and 'base-seed-0' in scores else None)
    requires_cohort = suite['suite'] in ('baseline', 'all')
    requires_refined = suite['suite'] in ('refined', 'all')
    checks = {
        'all_declared_cases_present': not failures and len(scores) == len(suite['cases']),
        'all_declared_cases_pass': bool(scores) and all(item['passed'] for item in scores.values()),
        'twenty_distinct_sampling_hashes': ((baseline_complete and
                                             len(sampling_hashes) == len(baseline_ids))
                                            if requires_cohort else None),
        'exact_refined_particle_ratio': ((particle_ratio ==
                                          protocol['acceptance']['require_exact_refined_particle_ratio'])
                                         if requires_refined else None),
    }

    convergence = {}
    baseline_time = mean = pre_support = None
    if baseline_complete:
        curves = [_force_curve(directory / 'cases' / case_id) for case_id in baseline_ids]
        baseline_time = curves[0][0]
        if not all(np.array_equal(time, baseline_time) for time, _ in curves):
            raise ValueError('Baseline cohort time axes differ')
        cohort = np.stack([force for _, force in curves])
        mean = cohort.mean(axis=0)
        standard_deviation = cohort.std(axis=0, ddof=1)
        first_support = min(item['first_support_time_s'] or np.inf
                            for item in scores.values())
        pre_support = baseline_time < first_support
        convergence.update(
            cohort_peak_mean_n=float(mean.max()),
            cohort_peak_standard_deviation_n=float(standard_deviation.max()),
            cohort_mean_pointwise_standard_deviation_n=float(standard_deviation.mean()),
            cohort_pre_support_peak_mean_n=float(mean[pre_support].max()),
            cohort_pre_support_peak_standard_deviation_n=float(
                standard_deviation[pre_support].max()),
            individual_material_peak_mean_n=float(np.mean([
                scores[case_id]['peak_material_resistance_n_before_support']
                for case_id in baseline_ids])),
            individual_material_peak_standard_deviation_n=float(np.std([
                scores[case_id]['peak_material_resistance_n_before_support']
                for case_id in baseline_ids], ddof=1)),
            material_impulse_mean_ns=float(np.mean([
                scores[case_id]['material_impulse_ns_before_support']
                for case_id in baseline_ids])),
            material_impulse_standard_deviation_ns=float(np.std([
                scores[case_id]['material_impulse_ns_before_support']
                for case_id in baseline_ids], ddof=1)),
        )
        if refined_complete:
            refined_time, refined_force = _force_curve(directory / 'cases' / refined_id)
            convergence['refined_vs_cohort_mean_pre_support_normalized_rmse'] = _normalized_rmse(
                baseline_time, mean, refined_time, refined_force, pre_support)
    if 'base-seed-0' in scores:
        seed_time, seed_force = _force_curve(directory / 'cases' / 'base-seed-0')
        first_support = min(item['first_support_time_s'] or np.inf
                            for item in scores.values())
        seed_pre_support = seed_time < first_support
        sensitivity = {}
        for case_id in scores:
            if case_id.startswith('sensitivity-'):
                candidate_time, candidate_force = _force_curve(directory / 'cases' / case_id)
                sensitivity[case_id] = _normalized_rmse(
                    seed_time, seed_force, candidate_time, candidate_force, seed_pre_support)
        convergence['sensitivity_vs_seed_0_pre_support_normalized_rmse'] = sensitivity

    return {
        'schema_version': 1,
        'suite': suite['suite'],
        'complete': checks['all_declared_cases_present'],
        'passed': all(value for value in checks.values() if value is not None),
        'checks': checks,
        'case_scores': scores,
        'case_failures': failures,
        'baseline_sampling_hash_count': len(sampling_hashes),
        'refined_particle_ratio': particle_ratio,
        'convergence': convergence,
        'interpretation': ('Convergence and sensitivity describe this frozen independent model. '
                           'They are not errors against the unavailable raw robot-force trace.'),
    }
