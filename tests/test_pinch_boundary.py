"""Protocol cardinality, timing and adversarial raw-record contract checks."""
import copy
from dataclasses import replace
from itertools import product
import math
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dexlab.pinch_boundary import (
    actuator_matches, campaign_cases, case_by_id, load_protocol, pd_command, qualification_cases,
    step_clock, target_at_tick, validate_protocol, validate_step,
)


def sample(protocol, case, step=0):
    before, after, tick, updated = step_clock(protocol, case, step)
    state = {
        'q_m': [0., 0., 0.], 'qdot_m_s': [0., 0., 0.],
        'cube_position_m': [case.offset_um * 1e-6, 0., .02],
        'cube_quaternion_wxyz': [1., 0., 0., 0.],
        'cube_velocity_m_s': [0., 0., 0.], 'cube_angular_velocity_rad_s': [0., 0., 0.],
    }
    weight = .064 * 9.81
    target = target_at_tick(protocol, tick)
    raw, command = pd_command(protocol, case, target, state['q_m'], state['qdot_m_s'])
    return {
        'step': step, 't_before_us': before, 't_after_us': after,
        'control_tick': tick, 'control_updated': updated,
        'force_epoch': 'applied_during_step', 'geometry_epoch': 'state_after',
        'state_before': copy.deepcopy(state), 'state_after': copy.deepcopy(state),
        'target_m': target, 'command_raw_N': raw, 'command_N': command,
        'actuator_force_N': [0., 0., 0.], 'cube_net_contact_force_N': [0., 0., weight],
        'step_wall_s': .001, 'observation_wall_s': .002,
        'contacts': [{'partner': 'table', 'position_world_m': [0., 0., 0.],
                      'normal_toward_cube_world': [0., 0., 1.], 'force_on_cube_N': [0., 0., weight],
                      'native_penetration_m': None, 'native_penetration_m_missing_reason': 'API unavailable',
                      'native_id': None, 'native_id_missing_reason': 'No persistent identifier'}],
        'solver': {'status': None, 'status_missing_reason': 'Not exposed',
                   'iterations': None, 'iterations_missing_reason': 'Not exposed',
                   'convergence_residual': None, 'convergence_residual_missing_reason': 'Not exposed',
                   'native_time_s': None, 'native_time_s_missing_reason': 'Not exposed', 'warnings': []},
    }


class PinchProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_protocol()
        cls.cases = campaign_cases(cls.protocol)

    def test_full_factorial_has_no_missing_or_duplicate_identity(self):
        formal = [c for c in self.cases if c.kind == 'formal']
        expected = set(product(('mujoco', 'genesis'),
                               (200, 400, 450, 500, 550, 600, 650, 700, 750, 800, 10000),
                               (-2000, 0, 2000), (1000, 500, 250), (0, 1, 2)))
        actual = {(c.engine, c.cap_mN, c.offset_um, c.dt_us, c.repeat) for c in formal}
        self.assertEqual(actual, expected)
        self.assertEqual(len(formal), 594)
        self.assertEqual(len(self.cases), 618)
        self.assertEqual(len({c.id for c in self.cases}), 618)

    def test_controls_preserve_every_offset_and_timestep(self):
        opened = [c for c in self.cases if c.kind == 'open']
        zero = [c for c in self.cases if c.kind == 'zero_friction']
        self.assertEqual({(c.engine, c.offset_um, c.dt_us) for c in opened},
                         set(product(('mujoco', 'genesis'), (-2000, 0, 2000), (1000, 500, 250))))
        self.assertEqual(len(opened), 18)
        self.assertEqual(len(zero), 6)
        self.assertTrue(all(c.offset_um == 0 and c.cap_mN == 10000 and c.repeat == 0 for c in zero))
        self.assertTrue(all(c.cap_mN == 10000 and c.repeat == 0 for c in opened))

    def test_qualification_and_bridge_are_separate_from_formal_cases(self):
        cases = qualification_cases(self.protocol)
        self.assertEqual(len(cases), 32)
        self.assertFalse({c.id for c in cases} & {c.id for c in self.cases})
        bridge = [c for c in cases if c.probe.startswith('bridge_')]
        self.assertEqual(len(bridge), 6)
        self.assertTrue(all(c.engine == 'genesis' for c in bridge))
        self.assertEqual({c.probe for c in bridge}, {'bridge_native', 'bridge_external'})

    def test_identity_lookup_never_accepts_unregistered_cap_or_repeat(self):
        case = self.cases[0]
        self.assertEqual(case_by_id(self.protocol, case.id), case)
        for changed in (replace(case, cap_mN=201), replace(case, repeat=3)):
            with self.assertRaisesRegex(ValueError, 'Unknown'):
                case_by_id(self.protocol, changed.id)
        for kwargs in ({'dt_us': 500.}, {'repeat': True}, {'cap_mN': 0}, {'probe': 'retuned'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(case, **kwargs)

    def test_matrix_corruption_and_invalid_budget_limits_are_rejected(self):
        for mutate in (
            lambda p: p['matrix']['offsets_um'].pop(),
            lambda p: p['matrix']['offsets_um'].__setitem__(0, 0),
            lambda p: p['clock'].__setitem__('control_period_us', 500),
            lambda p: p['budget'].__setitem__('maximum_base_starts', 618),
            lambda p: p['budget'].__setitem__('maximum_starts', 701),
            lambda p: p['budget'].__setitem__('maximum_retries_per_case', 2),
        ):
            protocol = copy.deepcopy(self.protocol)
            mutate(protocol)
            with self.assertRaises(ValueError):
                validate_protocol(protocol)

    def test_protocol_rejects_nonfinite_json_values_including_exponent_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'protocol.json'
            for value in ('NaN', 'Infinity', '-Infinity', '1e309', '-1e309'):
                raw = json.dumps({**self.protocol, 'invalid_numeric_field': 'REPLACE'})
                path.write_text(raw.replace('"REPLACE"', value))
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Nonfinite JSON'):
                    load_protocol(path)

    def test_all_physics_grids_share_exactly_4000_controller_updates(self):
        for dt in (1000, 500, 250):
            case = replace(self.cases[0], dt_us=dt)
            updates = []
            for index in range(4000000 // dt):
                before, after, tick, changed = step_clock(self.protocol, case, index)
                self.assertEqual(after - before, dt)
                self.assertEqual(tick * 1000, before - before % 1000)
                if changed:
                    updates.append((tick, before))
            self.assertEqual(updates, [(tick, tick * 1000) for tick in range(4000)])
            self.assertEqual(after, 4000000)
            with self.assertRaises(ValueError):
                step_clock(self.protocol, case, 4000000 // dt)

    def test_time_and_phase_boundaries_use_pre_step_control_ticks(self):
        p = self.protocol
        self.assertEqual(target_at_tick(p, 0), [0., 0., 0.])
        self.assertAlmostEqual(target_at_tick(p, 499)[1], .011976)
        self.assertEqual(target_at_tick(p, 500), [0., .012, .012])
        self.assertEqual(target_at_tick(p, 1000), [0., .012, .012])
        self.assertEqual(target_at_tick(p, 2000), [.08, .012, .012])
        self.assertEqual(target_at_tick(p, 3199), [.08, .012, .012])
        self.assertEqual(target_at_tick(p, 3200), [.08, 0., 0.])
        self.assertEqual(target_at_tick(p, 3999, opened=True), [.08, 0., 0.])
        for tick in (-1, 4000, True, 1.):
            with self.assertRaises(ValueError):
                target_at_tick(p, tick)

    def test_pd_has_signed_damping_and_symmetric_per_finger_clipping(self):
        case = replace(self.cases[0], cap_mN=500)
        raw, clipped = pd_command(self.protocol, case, [.1, .02, .03], [.2, .05, -.1], [.3, -.4, .5])
        for actual, expected in zip(raw, [-115., -7., 55.]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(clipped, [-50., -.5, .5])
        for bad in (math.nan, math.inf, True, 1e308):
            with self.assertRaises(ValueError):
                pd_command(self.protocol, case, [bad, 0, 0], [0, 0, 0], [0, 0, 0])

    def test_fixture_inertias_match_declared_boxes_and_axes(self):
        fixture = self.protocol['fixture']
        for half, mass, inertia in [
            (fixture['cube']['half_size_m'], fixture['cube']['mass_kg'], fixture['cube']['inertia_kg_m2']),
            (fixture['fingers']['half_size_m'], .1, fixture['fingers']['inertia_kg_m2_each']),
        ]:
            for axis in range(3):
                expected = mass * sum(half[i]**2 for i in range(3) if i != axis) / 3
                self.assertAlmostEqual(inertia[axis], expected, places=18)
        self.assertEqual(fixture['dof_axes_world'], [[0, 0, 1], [1, 0, 0], [-1, 0, 0]])
        self.assertEqual(len(fixture['collision_pairs']), 6)

    def test_actuator_tolerance_is_separate_from_contact_accounting(self):
        self.assertTrue(actuator_matches(self.protocol, [50, 0, -50], [50 + 4e-8, 1e-9, -50]))
        self.assertFalse(actuator_matches(self.protocol, [50, 0, -50], [50, 1.01e-9, -50]))
        self.assertFalse(actuator_matches(self.protocol, [.5, 0, -.5], [.50000001, 0, -.5]))
        with self.assertRaises(ValueError):
            actuator_matches(self.protocol, [0, 0, 0], [None, 0, 0])

    def test_cli_exports_complete_identities_but_does_not_claim_admission(self):
        output = subprocess.check_output([sys.executable, '-m', 'dexlab.pinch_boundary',
                                          'list-cases', '--include-qualification'], text=True)
        manifest = json.loads(output)
        self.assertEqual(len(manifest['cases']), 650)
        self.assertFalse(manifest['admitted'])
        self.assertEqual(len(manifest['protocol_sha256']), 64)

    def test_unimplemented_acquisition_command_cannot_silently_succeed(self):
        result = subprocess.run([sys.executable, '-m', 'dexlab.pinch_boundary', 'run'],
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr)

    def test_all_six_engines_remain_visible_and_unadmitted(self):
        coverage = self.protocol['coverage']
        self.assertEqual({x['engine'] for x in coverage}, {'mujoco', 'genesis', 'superdex', 'newton', 'physx', 'drake'})
        self.assertTrue(all(x['status'] in ('unqualified', 'not_run') for x in coverage))

    def test_complete_shape_does_not_assert_a_grasp_or_native_actuation_match(self):
        case = self.cases[0]
        record = sample(self.protocol, case, 100)
        self.assertNotEqual(record['command_N'], record['actuator_force_N'])
        self.assertIsNone(validate_step(self.protocol, case, record, 100))

    def test_missing_force_and_bad_state_are_not_silently_zero_filled(self):
        case = self.cases[0]
        for key, value in [('actuator_force_N', None), ('cube_net_contact_force_N', []),
                           ('command_N', [math.nan, 0, 0]), ('step_wall_s', -1)]:
            record = sample(self.protocol, case)
            record[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_step(self.protocol, case, record, 0)
        record = sample(self.protocol, case)
        record['state_after']['cube_quaternion_wxyz'] = [2., 0., 0., 0.]
        with self.assertRaisesRegex(ValueError, 'quaternion'):
            validate_step(self.protocol, case, record, 0)

    def test_missing_step_wrong_epoch_and_control_tick_are_rejected(self):
        case = replace(self.cases[0], dt_us=250)
        record = sample(self.protocol, case, 3)
        self.assertFalse(record['control_updated'])
        validate_step(self.protocol, case, record, 3)
        for key, value in [('step', 4), ('t_before_us', 0), ('control_tick', 1),
                           ('control_updated', True), ('force_epoch', 'state_after')]:
            changed = copy.deepcopy(record)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_step(self.protocol, case, changed, 3)

    def test_absent_native_fields_need_reasons_and_observed_values_cannot_claim_missing(self):
        case = self.cases[0]
        for section, key, value in [('solver', 'status_missing_reason', ''),
                                    ('solver', 'iterations_missing_reason', None),
                                    ('solver', 'iterations', 8),
                                    ('contacts', 'native_id_missing_reason', ''),
                                    ('contacts', 'native_penetration_m', 0.)]:
            record = sample(self.protocol, case)
            target = record[section][0] if section == 'contacts' else record[section]
            target[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_step(self.protocol, case, record, 0)

    def test_contact_partner_and_normal_frame_have_explicit_constraints(self):
        case = self.cases[0]
        for key, value in [('partner', 'unknown'), ('normal_toward_cube_world', [0., 0., 2.]),
                           ('force_on_cube_N', [0., 0.])]:
            record = sample(self.protocol, case)
            record['contacts'][0][key] = value
            with self.assertRaises(ValueError):
                validate_step(self.protocol, case, record, 0)


if __name__ == '__main__':
    unittest.main()
