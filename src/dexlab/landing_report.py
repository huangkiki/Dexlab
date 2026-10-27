"""Summarize all three frozen G1 repeats without reclassifying upstream task success."""

import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.landing_replay import digest, load_record
from dexlab.migration_budget import MigrationBudget


def actuator_summary(native, metadata):
    """Keep measured joint force separate from an unobserved GPU clamp branch."""
    forces = native['qfrc_actuator']
    if forces.ndim != 2 or not np.isfinite(forces).all():
        raise ValueError('Invalid recorded generalized actuator force')
    joints = []
    for index, enabled in enumerate(metadata['joint_actuatorfrclimited']):
        if not enabled:
            continue
        if metadata['joint_type'][index] not in (2, 3):
            raise ValueError('Limit comparison requires a scalar slide or hinge joint')
        values = forces[:, metadata['joint_dofadr'][index]]
        low, high = metadata['joint_actuatorfrcrange'][index]
        joints.append({'joint': metadata['joint_names'][index], 'declared_cpu_range': [low, high],
                       'measured_range': [float(values.min()), float(values.max())],
                       'samples_exactly_at_bound': int(np.count_nonzero((values == low) | (values == high))),
                       'samples_outside_declared_range': int(np.count_nonzero((values < low) | (values > high)))})
    return {'scope': 'Recorded qfrc_actuator compared with scalar-joint limits in the saved CPU model. Exact equality is descriptive, not a tolerance-based task gate.',
            'native_gpu_clamp_branch': 'unavailable; measured bound hits alone do not establish which clipping branch ran',
            'individual_actuator_force_limits_enabled': sum(metadata['actuator_forcelimited']),
            'control_limits_enabled': sum(metadata['actuator_ctrllimited']), 'joints': joints,
            'whole_system_momentum_balance': 'unavailable: whole-system COM momentum was not recorded; root velocity is not substituted'}


def distance_summary(rows):
    """Compare errors only when pre/post share the same subset of native pairs."""
    comparable = [row for row in rows if row['pre']['common_pairs'] > 0
                  and row['pre']['native_only_pairs'] == row['post']['native_only_pairs']]
    return {
        'complete_substeps': len(rows),
        'same_common_native_pair_set_substeps': len(comparable),
        'pre_closer_substeps': sum(r['pre']['max_distance_error_m'] < r['post']['max_distance_error_m'] for r in comparable),
        'post_closer_substeps': sum(r['pre']['max_distance_error_m'] > r['post']['max_distance_error_m'] for r in comparable),
        'equal_error_substeps': sum(r['pre']['max_distance_error_m'] == r['post']['max_distance_error_m'] for r in comparable),
        'max_pre_distance_error_m': max((r['pre']['max_distance_error_m'] for r in comparable), default=None),
        'max_post_distance_error_m': max((r['post']['max_distance_error_m'] for r in comparable), default=None),
        'pre_nonfoot_penetration_samples': sum(r['pre']['nonfoot_penetration_m'] > 0 for r in rows),
        'post_nonfoot_penetration_samples': sum(r['post']['nonfoot_penetration_m'] > 0 for r in rows),
        'native_nonfoot_active_samples': sum(r['native_nonfoot_active'] > 0 for r in rows),
        'native_nonfoot_loaded_samples': sum(r['native_nonfoot_loaded'] > 0 for r in rows),
        'interpretation': 'Distance agreement on identical pairs supports a pre-step geometry association in these records; it does not identify the cause of the historical nonfoot discrepancy.',
    }


def resource_summary(path):
    receipt = json.loads(path.read_text())
    telemetry = receipt.get('telemetry') or {}
    final = telemetry.get('final') or {}
    events = dict(line.split() for line in final.get('memory.events', '').splitlines())
    if (receipt['state'] != 'completed' or receipt['returncode'] != 0
            or telemetry.get('state') != 'completed' or telemetry.get('returncode') != 0
            or events.get('oom') != '0' or events.get('oom_kill') != '0'
            or telemetry['effective_limits']['memory.swap.max'] != '0'
            or telemetry.get('gpu_budget_stop_reason')):
        raise ValueError('Missing or failed final resource evidence: ' + path.name)
    return {'receipt_sha256': digest(path), 'whole_window_wall_s': receipt['wall_s'],
            'bounded_child_wall_s': telemetry['wall_s'], 'peak_ram_bytes': int(final['memory.peak']),
            'effective_limits': telemetry['effective_limits'], 'oom_events': events,
            'sampled_gpu_guard': telemetry.get('gpu_budget'),
            'gpu_stop_reason': telemetry.get('gpu_budget_stop_reason')}


def summarize(campaign, protocol_path):
    from scipy.stats import beta

    protocol = json.loads(protocol_path.read_text())
    probe = campaign / 'native-runs/support-probe-1'
    qualification = json.loads((probe / 'validation/reference_env_probe.json').read_text())
    if qualification['passed'] is not True:
        raise ValueError('The original support probe did not qualify')
    reference = json.loads((probe / 'invocation.json').read_text())
    environment = json.loads((campaign / 'control/landing-environment-audit-2.json').read_text())
    if environment['pin_mismatches']:
        raise ValueError('Original runtime pins differ')
    budget = MigrationBudget(campaign / 'native-budget').status()
    expected = ['support-probe', 'policy-repeat-1', 'policy-repeat-2', 'policy-repeat-3']
    if ([attempt['case_id'] for attempt in budget['attempts']] != expected
            or any(attempt['terminal'] is None for attempt in budget['attempts'])):
        raise ValueError('The report must retain every completed attempt in the frozen batch')
    processes = {(a['handle']['boot_id'], a['handle']['pid'], a['handle']['process_start_ticks'])
                 for a in budget['attempts']}
    if len(processes) != len(expected):
        raise ValueError('Matched repeats require distinct process identities')
    cases = []
    for n in (1, 2, 3):
        name = f'policy-repeat-{n}'
        directory = campaign / 'native-runs' / name
        _, native, _, _, _, inputs = load_record(directory, protocol_path)
        invocation = json.loads((directory / 'invocation.json').read_text())
        if invocation['checkpoint_sha256'] != protocol['checkpoint_sha256']:
            raise ValueError('Checkpoint identity differs across the batch')
        if any(invocation[key] != reference[key] for key in ('runtime', 'asset_sha256', 'upstream_commit', 'recorder_sha256', 'runner_sha256')):
            raise ValueError('Reference identity changed across the qualified batch')
        metrics = json.loads((directory / 'metrics.json').read_text())
        audit = json.loads((directory / 'audit.json').read_text())
        metadata = json.loads((directory / 'native_metadata.json').read_text())
        rows = audit['geometry_reconstruction']['substeps']
        if len(rows) != protocol['control_steps'] * protocol['substeps_per_control']:
            raise ValueError('Geometry audit does not cover the complete episode')
        cases.append({
            'case': name, 'input_sha256': {**inputs, 'metrics.json': digest(directory / 'metrics.json')},
            'upstream_strict_success': metrics['success'], 'upstream_legacy_gate_pass': metrics['legacy_gate_pass'],
            'upstream_quality_checks': metrics['quality_checks'],
            'normalized_return': metrics['normalized_return'], 'first_failure_step': metrics['first_failure_step'],
            'last_2s_horizontal_drift_m': metrics['last_2s_horizontal_drift'],
            'last_2s_linear_speed_rms_m_s': metrics['last_2s_linear_speed_rms'],
            'state_alignment': audit['state_alignment'], 'native_clock': audit['native_clock'],
            'native_pairs': audit['native_pairs'], 'recorded_nonfoot': audit['recorded_nonfoot'],
            'effective_native_parameters': {key: metadata[key] for key in (
                'physics_dt_s', 'gravity', 'cone', 'integrator', 'solver', 'iterations', 'tolerance',
                'warp_options', 'native_state_dtype', 'newton_update_data_interval',
                'contact_capacity', 'constraint_capacity', 'recording_hook',
                'contact_copy_stage', 'solver_convergence_telemetry')},
            'upstream_geometric_nonfoot_frames': audit['upstream_geometric_nonfoot_frames'],
            'actuators': actuator_summary(native, metadata),
            'geometry': distance_summary(rows),
            'resources': resource_summary(campaign / f'control/landing-policy-resources-{n}.json'),
        })
    failures = sum(case['upstream_strict_success'] is not True for case in cases)
    count = len(cases)
    interval = [float(beta.ppf(.025, failures, count - failures + 1)) if failures else 0.,
                float(beta.ppf(.975, failures + 1, count - failures)) if failures < count else 1.]
    return {
        'schema_version': 1, 'protocol_sha256': digest(protocol_path),
        'reporter_sha256': digest(Path(__file__)), 'cohort': 'RTX 4090; fixed source reference; seed 137',
        'source_commit': reference['upstream_commit'], 'runtime': reference['runtime'],
        'asset_sha256': reference['asset_sha256'], 'checkpoint_sha256': protocol['checkpoint_sha256'],
        'native_support_probe': qualification,
        'support_probe_sha256': digest(probe / 'validation/reference_env_probe.json'),
        'probe_resources': resource_summary(campaign / 'control/landing-probe-resources-1.json'),
        'audit_resources': resource_summary(campaign / 'control/landing-audit-resources-1.json'),
        'original_environment': {
            'requirements_checked': environment['checked_original_requirements'],
            'pin_mismatches': environment['pin_mismatches'],
            'dependency_metadata_passed': environment['passed'],
            'constraint_diagnostics': [line for line in environment['dependency_check_stderr'].splitlines()
                                       if line.startswith('The package ')],
            'qualification_scope': 'The unchanged converter, native support fixture and three full policy repeats ran; other installed package paths remain unqualified.',
            'audit_sha256': digest(campaign / 'control/landing-environment-audit-2.json'),
        },
        'cases': cases,
        'native_budget': {
            'manifest_sha256': budget['manifest_sha256'], 'starts_used': budget['starts_used'],
            'wall_charged_or_reserved_s': budget['wall_charged_or_reserved_s'],
            'wall_limit_s': budget['wall_limit_s'], 'distinct_processes': len(processes),
            'clock_scope': 'Ledger reservations begin after input/runtime identity checks; full bounded-window durations are reported separately.',
            'attempts': [{'case': a['case_id'], 'outcome': a['terminal']['outcome'],
                          'wall_s': a['terminal']['wall_s'],
                          'invocation_sha256': a['terminal']['evidence_sha256']} for a in budget['attempts']],
        },
        'failure_frequency': {
            'failed': failures, 'total': count, 'two_sided_clopper_pearson_95': interval,
            'interpretation': 'Binomial-model interval for the requested descriptive report. Independence is not established; same-seed process repeats do not estimate random-initial-condition reliability.',
        },
        'historical_comparison': 'The author archive flags geometric frame119 but lacks its original model and complete pair stream. No nonfoot discrepancy was reproduced in this distinct hardware cohort; no historical solver-failure attribution follows.',
        'conditional_interventions': 'Not run: no localized historical mismatch supports a preregistered intervention.',
        'scientific_scope': 'Source task gates, record integrity, geometry association and physical validity remain separate. No hardware validation, new training, all-engine comparison or production UniSim adapter.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = summarize(args.campaign, args.protocol)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
