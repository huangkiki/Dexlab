"""Strict, independently testable admission for the fixed adapter comparison."""
from __future__ import annotations

import math

INITIAL_FIELDS = (
    'cube_mass', 'cube_inertia', 'geom_friction', 'gripper_mass', 'armature',
    'kp', 'kv', 'force_range', 'q', 'qvel', 'object_pos', 'object_vel',
    'object_quat', 'object_ang', 'geom_sol_params', 'joint_sol_params',
)


def numeric_error(actual, expected):
    """Compare nested numeric values, allowing only a leading single-env axis."""
    def normalize(value):
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value

    actual, expected = normalize(actual), normalize(expected)
    if isinstance(actual, list) or isinstance(expected, list):
        if not isinstance(actual, list) or not isinstance(expected, list):
            raise ValueError('Incompatible numeric structure')
        if len(actual) != len(expected):
            raise ValueError('Incompatible numeric dimensions')
        return max((numeric_error(a, b) for a, b in zip(actual, expected)), default=0.)
    if isinstance(actual, bool) or isinstance(expected, bool):
        raise ValueError('Boolean is not a physical measurement')
    if not math.isfinite(actual) or not math.isfinite(expected):
        raise ValueError('Nonfinite measurement')
    return abs(actual - expected)


def compare_initial(actual, expected, *, storage_trial=False):
    """Return all mismatches; never hide a missing field or change tolerance."""
    errors = {}
    failures = []
    for field in INITIAL_FIELDS:
        try:
            errors[field] = numeric_error(actual[field], expected[field])
            if errors[field] > 1e-12:
                failures.append(field)
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f'{field}: {exc}')
    option_differences = {}
    if 'options' not in actual or 'options' not in expected:
        failures.append('options: missing')
    else:
        for key in actual['options'].keys() | expected['options'].keys():
            left, right = actual['options'].get(key), expected['options'].get(key)
            if left != right:
                option_differences[key] = {'native': right, 'adapter': left}
                declared_storage_change = (
                    storage_trial and key in ('batch_links_info', 'batch_dofs_info')
                    and right is False and left is True)
                if not declared_storage_change:
                    failures.append(f'options: {key}')
    return {'passed': not failures, 'absolute_errors': errors, 'failures': failures,
            'option_differences': option_differences,
            'configuration_identical': not option_differences,
            'scope': 'admission to storage representation trial' if storage_trial else 'strict admission'}
