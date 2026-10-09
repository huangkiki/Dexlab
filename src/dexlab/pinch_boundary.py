"""Common pinch protocol identities, integer clocks and record shape checks.

This module imports no engine. Acquisition and offline campaign scoring are
separate follow-up deliveries; the presence of a protocol is not admission.
"""
from dataclasses import asdict, dataclass
from itertools import product
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


PROTOCOL_PATH = Path(__file__).resolve().parents[2] / 'demos/contact-benchmark/pinch-boundary-v1.json'


def _reject_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'Nonfinite JSON number: {value}')
    return number


def load_protocol(path=PROTOCOL_PATH):
    """Read the v1 contract, without treating its bytes as a campaign freeze."""
    return _parse_protocol(Path(path).read_bytes())


def _parse_protocol(raw):
    protocol = json.loads(raw, parse_constant=_reject_constant, parse_float=_finite_float)
    if type(protocol['schema']) is not int or protocol['schema'] != 1 or protocol['id'] != 'pinch-boundary-v1':
        raise ValueError('Unsupported pinch protocol')
    validate_protocol(protocol)
    return protocol


@dataclass(frozen=True)
class Case:
    engine: str
    kind: str
    cap_mN: int
    offset_um: int
    dt_us: int
    repeat: int
    probe: str = ''

    def __post_init__(self):
        if self.engine not in ('mujoco', 'genesis') or self.kind not in (
            'formal', 'open', 'zero_friction', 'qualification'
        ):
            raise ValueError('Unknown engine or case kind')
        for name in ('cap_mN', 'offset_um', 'dt_us', 'repeat'):
            if type(getattr(self, name)) is not int:
                raise ValueError(f'{name} must be an integer')
        if self.cap_mN <= 0 or self.dt_us <= 0 or self.repeat < 0:
            raise ValueError('Invalid cap, timestep or repeat')
        if not isinstance(self.probe, str) or bool(self.probe) != (self.kind == 'qualification'):
            raise ValueError('Only qualification cases have a probe')

    @property
    def id(self):
        probe = f'-{self.probe}' if self.probe else ''
        return (f'{self.engine}-{self.kind}{probe}-f{self.cap_mN:05d}'
                f'-x{self.offset_um:+05d}-h{self.dt_us:04d}-r{self.repeat}')

    def as_dict(self):
        return {'id': self.id, **asdict(self)}


def campaign_cases(protocol):
    """Enumerate the complete 594 formal + 24 control identities in fixed order."""
    matrix, clock = protocol['matrix'], protocol['clock']
    engines, steps = matrix['engines'], clock['physics_steps_us']
    formal = [Case(engine, 'formal', cap, offset, dt, repeat)
              for engine, cap, offset, dt, repeat in product(
                  engines, matrix['force_caps_mN'], matrix['offsets_um'], steps, matrix['repeats'])]
    cap = matrix['control_force_cap_mN']
    controls = [Case(engine, 'open', cap, offset, dt, 0)
                for engine, offset, dt in product(engines, matrix['offsets_um'], steps)]
    controls += [Case(engine, 'zero_friction', cap, 0, dt, 0)
                 for engine, dt in product(engines, steps)]
    return tuple(formal + controls)


def qualification_cases(protocol):
    """Enumerate 32 separately scored admission/bridge records, never formal cases."""
    engines, steps = protocol['matrix']['engines'], protocol['clock']['physics_steps_us']
    qualification = protocol['qualification']
    cap = qualification['bridge_cap_mN']
    cases = [Case(engine, 'qualification', cap, 0, dt, 0, probe)
             for engine, dt, probe in product(engines, steps, qualification['per_engine_per_step'])]
    cases += [Case(engine, 'qualification', cap, 0, 500, 0, probe)
              for engine, probe in product(engines, qualification['per_engine_500us'])]
    cases += [Case('genesis', 'qualification', cap, 0, dt, 0, probe)
              for dt, probe in product(steps, qualification['genesis_per_step'])]
    return tuple(cases)


def validate_protocol(protocol):
    """Check cardinality, integer grids and budget invariants before enumeration use."""
    clock, matrix, budget = protocol['clock'], protocol['matrix'], protocol['budget']
    if clock != {'duration_us': 4000000, 'control_period_us': 1000,
                 'physics_steps_us': [1000, 500, 250]}:
        raise ValueError('Unexpected v1 control/physics clock')
    for name in ('duration_us', 'control_period_us'):
        if type(clock[name]) is not int:
            raise ValueError('Clocks must be integer microseconds')
    cases, qualification = campaign_cases(protocol), qualification_cases(protocol)
    expected = {'formal': 594, 'open': 18, 'zero_friction': 6}
    if any(sum(case.kind == kind for case in cases) != count for kind, count in expected.items()):
        raise ValueError('Incomplete campaign matrix')
    all_cases = (*cases, *qualification)
    if len(qualification) != 32 or len({case.id for case in all_cases}) != len(all_cases):
        raise ValueError('Wrong qualification count or duplicate identity')
    if matrix['seed'] != 0 or type(matrix['seed']) is not int:
        raise ValueError('All repeats use the same seed 0')
    if (matrix['formal_count'], matrix['open_count'], matrix['nominal_zero_friction_count']) != (594, 18, 6):
        raise ValueError('Declared counts disagree with the campaign')
    if (budget['maximum_base_starts'] != len(all_cases)
            or budget['maximum_starts'] != 700 or budget['maximum_extra_starts'] != 50
            or budget['maximum_base_starts'] + budget['maximum_extra_starts'] != budget['maximum_starts']
            or budget['cumulative_process_wall_limit_s'] != 21600 or budget['process_wall_limit_s'] != 1800
            or budget['maximum_retries_per_case'] != 1 or budget['workers'] != 1):
        raise ValueError('Unexpected campaign budget')


def case_by_id(protocol, case_id):
    matches = [case for case in (*campaign_cases(protocol), *qualification_cases(protocol))
               if case.id == case_id]
    if len(matches) != 1:
        raise ValueError('Unknown or duplicate case identity')
    return matches[0]


def duration_us(protocol, case):
    qualification = protocol['qualification']
    if case.probe in ('known_force', 'pd_clock'):
        return qualification['short_duration_us']
    if case.probe == 'contact_observation':
        return qualification['contact_observation_duration_us']
    return protocol['clock']['duration_us']


def step_clock(protocol, case, step):
    """Return start/end microseconds, held controller tick and update flag."""
    if type(step) is not int or step < 0 or step * case.dt_us >= duration_us(protocol, case):
        raise ValueError('Step outside the case duration')
    period = protocol['clock']['control_period_us']
    if type(case.dt_us) is not int or case.dt_us <= 0 or period % case.dt_us:
        raise ValueError('Physics step must divide the control period')
    before = step * case.dt_us
    return before, before + case.dt_us, before // period, before % period == 0


def target_at_tick(protocol, tick, *, opened=False):
    """Evaluate the adopted piecewise trajectory at a controller tick, in metres."""
    clock, control = protocol['clock'], protocol['control']
    if type(tick) is not int or not 0 <= tick < clock['duration_us'] // clock['control_period_us']:
        raise ValueError('Control tick outside the trajectory')
    time_us = tick * clock['control_period_us']
    closure = (0. if opened or time_us >= control['open_at_us'] else
               control['closure_m'] * min(time_us / control['close_end_us'], 1.))
    fraction = (time_us - control['lift_start_us']) / (control['lift_end_us'] - control['lift_start_us'])
    return [control['lift_m'] * max(0., min(fraction, 1.)), closure, closure]


def _vector(value, size, field):
    if not isinstance(value, (list, tuple)) or len(value) != size or any(
        type(number) not in (int, float) or not math.isfinite(number) for number in value
    ):
        raise ValueError(f'{field} must contain {size} finite numbers')
    return value


def pd_command(protocol, case, target, position, velocity):
    """Shared external PD; native actuator measurement is deliberately separate."""
    for name, value in [('target', target), ('position', position), ('velocity', velocity)]:
        _vector(value, 3, name)
    control = protocol['control']
    raw = [kp * (reference - q) - kd * qdot for kp, kd, reference, q, qdot in zip(
        control['kp_N_m'], control['kd_N_s_m'], target, position, velocity)]
    _vector(raw, 3, 'PD result')
    caps = [control['lift_cap_N'], case.cap_mN / 1000, case.cap_mN / 1000]
    return raw, [max(-cap, min(value, cap)) for value, cap in zip(raw, caps)]


def actuator_matches(protocol, command, observed):
    """Check native output against the direct-force command, not contact force."""
    _vector(command, 3, 'command')
    _vector(observed, 3, 'observed actuator force')
    limits = protocol['acceptance']
    return all(abs(actual - expected) <= limits['actuator_output_abs_error_N']
               + limits['actuator_output_rel_error'] * abs(expected)
               for expected, actual in zip(command, observed))


def _state(state, protocol):
    for name in ('q_m', 'qdot_m_s', 'cube_position_m', 'cube_velocity_m_s', 'cube_angular_velocity_rad_s'):
        _vector(state[name], 3, name)
    quaternion = _vector(state['cube_quaternion_wxyz'], 4, 'cube_quaternion_wxyz')
    if abs(sum(x*x for x in quaternion) - 1) > protocol['acceptance']['quaternion_squared_norm_abs_error']:
        raise ValueError('Invalid cube quaternion')


def validate_step(protocol, case, record, expected_step):
    """Reject malformed/shifted complete samples; does not establish physical success.

    A numerical-abort event is stored outside the valid sample prefix. Cross-step
    continuity, physics metrics, native provenance and campaign completeness are
    checked by the independent scorer delivered in C.
    """
    before, after, tick, updated = step_clock(protocol, case, expected_step)
    for name, expected in [('step', expected_step), ('t_before_us', before),
                           ('t_after_us', after), ('control_tick', tick)]:
        if type(record[name]) is not int or record[name] != expected:
            raise ValueError(f'Incorrect {name}')
    if type(record['control_updated']) is not bool or record['control_updated'] != updated:
        raise ValueError('Incorrect control_updated')
    if record['force_epoch'] != 'applied_during_step' or record['geometry_epoch'] != 'state_after':
        raise ValueError('Incorrect observation epoch')
    _state(record['state_before'], protocol)
    _state(record['state_after'], protocol)
    for name in ('target_m', 'command_raw_N', 'command_N', 'actuator_force_N', 'cube_net_contact_force_N'):
        _vector(record[name], 3, name)
    for name in ('step_wall_s', 'observation_wall_s'):
        _vector([record[name]], 1, name)
        if record[name] < 0:
            raise ValueError('Negative wall time')
    contacts = record['contacts']
    if not isinstance(contacts, list):
        raise ValueError('Contacts must be a list')
    for contact in contacts:
        if contact['partner'] not in ('table', 'left', 'right'):
            raise ValueError('Unknown cube contact partner')
        for name in ('position_world_m', 'normal_toward_cube_world', 'force_on_cube_N'):
            _vector(contact[name], 3, name)
        if abs(sum(x*x for x in contact['normal_toward_cube_world']) - 1) > 1e-6:
            raise ValueError('Contact normal must be a unit vector')
        _optional_number(contact, 'native_penetration_m')
        native_id = contact['native_id']
        reason = contact['native_id_missing_reason']
        if native_id is None:
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError('Missing native contact ID needs a reason')
        elif type(native_id) not in (int, str) or reason is not None:
            raise ValueError('Invalid native contact ID')
    solver = record['solver']
    for name in ('iterations', 'convergence_residual', 'native_time_s'):
        _optional_number(solver, name)
        if solver[name] is not None and solver[name] < 0:
            raise ValueError(f'Negative solver {name}')
    if solver['iterations'] is not None and type(solver['iterations']) is not int:
        raise ValueError('Actual iterations must be an integer')
    if not isinstance(solver['warnings'], list) or any(not isinstance(x, str) for x in solver['warnings']):
        raise ValueError('Solver warnings must be strings')
    if solver['status'] is None:
        reason = solver['status_missing_reason']
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('Missing native solver status needs a reason')
    elif (not isinstance(solver['status'], str) or not solver['status'].strip()
          or solver['status_missing_reason'] is not None):
        raise ValueError('Invalid native solver status')


def _optional_number(record, field):
    value, reason = record[field], record[field + '_missing_reason']
    if value is None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f'Missing {field} needs a reason')
    else:
        _vector([value], 1, field)
        if reason is not None:
            raise ValueError(f'Observed {field} cannot have a missing reason')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list-cases', help='Expand protocol identities; does not admit or run engines')
    listing.add_argument('--protocol', type=Path, default=PROTOCOL_PATH)
    listing.add_argument('--include-qualification', action='store_true')
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    protocol = _parse_protocol(raw)
    cases = campaign_cases(protocol)
    if args.include_qualification:
        cases += qualification_cases(protocol)
    json.dump({'schema': 1, 'protocol_id': protocol['id'],
               'protocol_sha256': hashlib.sha256(raw).hexdigest(),
               'admitted': False, 'cases': [case.as_dict() for case in cases]}, sys.stdout, indent=2)
    print()


if __name__ == '__main__':
    main()
