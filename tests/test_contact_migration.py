"""Migration acceptance rejects altered observations without a native runtime."""
from dataclasses import dataclass
import copy
from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.contact_migration import compare_contacts, compare_trial, contact_rows
from dexlab.genesis_pinch_probe import read_initial, read_sample, require_contacts
from test_force_limit_protocol import stationary_record


class ContactComparisonTests(unittest.TestCase):
    def fixture(self):
        native = {'native': {'geom_a': [5, 5], 'geom_b': [8, 8],
            'position': [[0., 0., 0.], [1., 0., 0.]],
            'force': [[0., 0., 1.], [0., 0., 2.]],
            'normal': [[0., 0., -1.]] * 2, 'penetration': [.001, .002]},
            'normal_orientation': 'native B to A', 'force_side': 'B'}
        candidate = {'env_ids': [0, 0], 'available': [True],
            'geom_a': [1, 1], 'geom_b': [0, 0],
            'position': [[1., 0., 0.], [0., 0., 0.]],
            'force_a': [[0., 0., 2.], [0., 0., 1.]],
            'force_b': [[0., 0., -2.], [0., 0., -1.]],
            'normal': [[0., 0., -1.]] * 2, 'signed_distance': [-.002, -.001]}
        return native, candidate

    def normalized(self):
        native, candidate = self.fixture()
        return (contact_rows(native, {'reference_geometry_names': {'5': 'ground', '8': 'cube'}}, native=True),
                contact_rows(candidate, {'geom_names': ['ground', 'cube']}, native=False))

    def test_reversed_sides_permuted_slots_and_ids_keep_physical_identity(self):
        native, candidate = self.normalized()
        self.assertEqual(compare_contacts(native, candidate),
                         dict(position=0., distance=0., normal=0., force=0.))

    def test_force_is_compared_after_geometric_matching(self):
        native, candidate = self.normalized()
        candidate[0]['force'] *= 3
        self.assertEqual(compare_contacts(native, candidate)['force'], 4.)

    def test_missing_duplicate_and_wrong_geometry_are_rejected(self):
        native, candidate = self.normalized()
        for rows in (candidate[:1], [candidate[0], candidate[0]],
                     [{**candidate[0], 'pair': ('other', 'cube')}, candidate[1]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                compare_contacts(native, rows)

    def test_missing_reset_and_nonfinite_observations_are_not_empty_contacts(self):
        _, candidate = self.fixture()
        for key, value in (('available', [False]), ('normal', None),
                           ('env_ids', [0]), ('force_b', [[0., 0., float('nan')]] * 2)):
            broken = {**candidate, key: value}
            with self.subTest(key=key), self.assertRaises((ValueError, TypeError)):
                contact_rows(broken, {'geom_names': ['ground', 'cube']}, native=False)


@dataclass
class Snapshot:
    state_time: np.ndarray
    available: np.ndarray
    env_ids: np.ndarray
    geom_a: np.ndarray
    geom_b: np.ndarray
    force_a: np.ndarray
    force_b: np.ndarray
    normal: np.ndarray
    signed_distance: np.ndarray
    body_ids: np.ndarray | None
    body_net_force: np.ndarray | None


class PublicRecordingTests(unittest.TestCase):
    def test_unpatched_backend_reports_the_required_dependency(self):
        with self.assertRaisesRegex(RuntimeError, 'contact-readback patch'):
            require_contacts(SimpleNamespace())

    def test_changed_native_storage_is_rejected_before_recording(self):
        values = dict(native_precision='float64', native_device='cpu',
                      native_deterministic_algorithms=True, native_friction_cone='elliptic',
                      native_rigid_options=dict(batch_links_info=False, batch_dofs_info=True))
        report = SimpleNamespace(to_dict=lambda: {'fields': [dict(field=k, effective=v)
                                                           for k, v in values.items()]})
        with self.assertRaisesRegex(RuntimeError, 'batched parameter storage'):
            read_initial(SimpleNamespace(get_import_report=lambda: report))

    def test_wrong_native_friction_cone_is_rejected_before_any_trajectory(self):
        values = dict(native_precision='float64', native_device='cpu',
                      native_deterministic_algorithms=True, native_friction_cone='pyramidal')
        report = SimpleNamespace(to_dict=lambda: {'fields': [dict(field=k, effective=v)
                                                           for k, v in values.items()]})
        backend = SimpleNamespace(get_import_report=lambda: report)
        with self.assertRaisesRegex(RuntimeError, 'native_friction_cone'):
            read_initial(backend)

    def fixture(self):
        snapshot = Snapshot(np.array([.001]), np.array([True]), np.array([0, 0]),
                            np.array([0, 1]), np.array([1, 2]),
                            np.array([[0., 0., -1.], [2., 0., 0.]]),
                            np.array([[0., 0., 1.], [-2., 0., 0.]]),
                            np.array([[0., 0., 1.], [1., 0., 0.]]),
                            np.array([-.001, -.002]), np.array([9, 7, 3]),
                            np.array([[[0., 0., -1.], [99., 0., 1.], [-2., 0., 0.]]]))
        state = dict(root_pose=np.array([[0., 0., .02, 1., 0., 0., 0.]]),
                     root_velocity=np.zeros((1, 6)), joint_positions=np.zeros((1, 3)),
                     joint_velocities=np.zeros((1, 3)))
        backend = SimpleNamespace(get_contact_snapshot=lambda: snapshot,
                                  get_entity_state=lambda _: state)
        return backend, snapshot, {'geom_body_ids': [9, 7, 3], 'cube_link': 7}

    def test_native_net_force_is_not_reconstructed_from_contact_rows(self):
        backend, _, initial = self.fixture()
        row = read_sample(backend, initial, np.zeros((1, 3)))
        self.assertEqual(row['object_contact_force'], [[99., 0., 1.]])
        self.assertEqual(row['contacts']['link_a'], [9, 7])
        self.assertEqual(len(row['complete_contacts']['env_ids']), 2)

    def test_missing_aggregate_and_reset_rows_fail_before_recording(self):
        backend, snapshot, initial = self.fixture()
        snapshot.body_net_force = None
        with self.assertRaisesRegex(RuntimeError, 'net contact force'):
            read_sample(backend, initial, np.zeros((1, 3)))
        snapshot.available[0] = False
        with self.assertRaisesRegex(RuntimeError, 'observed world'):
            read_sample(backend, initial, np.zeros((1, 3)))

    def test_full_ledger_preserves_contacts_outside_the_scored_object(self):
        backend, _, initial = self.fixture()
        row = read_sample(backend, {**initial, 'cube_link': 9}, np.zeros((1, 3)))
        self.assertEqual(len(row['contacts']['link_a']), 1)
        self.assertEqual(len(row['complete_contacts']['env_ids']), 2)


class TrajectoryComparisonTests(unittest.TestCase):
    def fixture(self, condition='open_negative'):
        record = stationary_record(condition, cap=10., x=0.)
        record.update(repeat=0, case_id=None)
        record['initial'].update(
            cube_inertia=[[[.064*.04**2/6 if i == j else 0. for j in range(3)]
                           for i in range(3)]], geom_friction=[.5]*4,
            qvel=[0.]*3, object_quat=[1., 0., 0., 0.], object_ang=[0.]*3,
            options={'batch_links_info': False, 'batch_dofs_info': False},
            reference_geometry_names={'0': 'ground', '1': 'cube'},
            geom_names=['ground', 'cube'])
        weight = .064*9.81
        for index, row in enumerate(record['samples']):
            row.update(qvel=[0.]*3, object_ang=[0.]*3, command=[0.]*3)
            row['complete_contacts'] = {
                'state_time': (index+1)*.001, 'geometry_time': index*.001,
                'force_start_time': index*.001, 'force_end_time': (index+1)*.001,
                'normal_orientation': 'native B to A', 'force_side': 'B',
                'native': {'geom_a': [1], 'geom_b': [0], 'position': [[0., 0., 0.]],
                           'force': [[0., 0., -weight]], 'normal': [[0., 0., 1.]],
                           'penetration': [0.]}}
        candidate = copy.deepcopy(record)
        candidate['initial']['options'] = {'batch_links_info': True, 'batch_dofs_info': True}
        for row in candidate['samples']:
            contact = row['complete_contacts']
            contact.pop('native')
            for name in ('state_time', 'geometry_time', 'force_start_time', 'force_end_time'):
                contact[name] = [contact[name]]
            contact.update(available=[True], env_ids=[0], geom_a=[1], geom_b=[0],
                           position=[[0., 0., 0.]], force_a=[[0., 0., weight]],
                           force_b=[[0., 0., -weight]], normal=[[0., 0., -1.]],
                           signed_distance=[0.])
        return record, candidate

    def test_complete_unchanged_observations_preserve_a_physical_failure(self):
        reference, candidate = self.fixture('pinch')
        result = compare_trial(reference, candidate, .001)
        self.assertTrue(result['passed'])
        self.assertFalse(result['native_score']['checks']['hold_or_negative'])
        self.assertFalse(result['candidate_score']['passed'])

    def test_equal_but_physically_invalid_records_cannot_qualify(self):
        reference, candidate = self.fixture()
        for record in (reference, candidate):
            record['samples'][20]['object_contact_force'] = [[0., 0., 0.]]
        result = compare_trial(reference, candidate, .001)
        self.assertEqual(result['state_max_absolute_errors']['object_contact_force'], 0.)
        self.assertFalse(result['passed'])
        self.assertEqual(result['first_failure_time_s']['physical_validity_force_ledger'], .021)

    def test_missing_step_and_shifted_solve_epoch_are_refused(self):
        reference, candidate = self.fixture()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            compare_trial(reference, {**candidate, 'samples': candidate['samples'][:-1]}, .001)
        candidate['samples'][30]['complete_contacts']['geometry_time'] = [.031]
        with self.assertRaisesRegex(ValueError, 'epoch'):
            compare_trial(reference, candidate, .001)

    def test_changed_command_contact_and_native_net_force_do_not_pass(self):
        for field in ('command', 'contact_force', 'object_contact_force'):
            with self.subTest(field=field):
                reference, candidate = self.fixture()
                row = candidate['samples'][20]
                if field == 'command':
                    row['command'][0] = .001
                elif field == 'object_contact_force':
                    row[field][0][2] += 1.
                else:
                    row['complete_contacts']['force_a'][0][2] += 1.
                    row['complete_contacts']['force_b'][0][2] -= 1.
                result = compare_trial(reference, candidate, .001)
                self.assertFalse(result['passed'])
                self.assertEqual(result['first_failure_time_s'][field], .021)
