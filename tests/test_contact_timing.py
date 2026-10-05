"""Timing coverage and API boundaries, independent of physics pass/fail."""

import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.contact_indent_run import valid_step_timing
from dexlab.contact_plane_native import MuJoCoPlane, SuperDexPlane


class TimingCoverageTests(unittest.TestCase):
    def setUp(self):
        self.receipt = {
            'step_timing': {'native_call_seconds': .2, 'observation_seconds': .3, 'steps': 4},
            'step_and_observation_seconds': .6,
        }

    def test_complete_disjoint_intervals_are_valid(self):
        self.assertTrue(valid_step_timing(self.receipt, 4))

    def test_missing_steps_and_double_counted_cost_fail(self):
        self.assertFalse(valid_step_timing(self.receipt, 5))
        self.receipt['step_and_observation_seconds'] = .4
        self.assertFalse(valid_step_timing(self.receipt, 4))
        self.assertFalse(valid_step_timing({}, 4))

    def test_nonfinite_negative_and_nonnumeric_timing_fail(self):
        for value in (-1, float('nan'), float('inf'), True, '.2', None):
            receipt = copy.deepcopy(self.receipt)
            receipt['step_timing']['native_call_seconds'] = value
            with self.subTest(value=value):
                self.assertFalse(valid_step_timing(receipt, 4))


class NativeTimingBoundaryTests(unittest.TestCase):
    def native(self, cls):
        native = object.__new__(cls)
        native.step_timing = {'native_call_seconds': 0., 'observation_seconds': 0., 'steps': 0}
        native.observe = lambda: (np.zeros(7), np.zeros(6))
        if cls is MuJoCoPlane:
            native.mj = SimpleNamespace(mj_step=lambda model, data: None)
            native.model = object()
            native.data = SimpleNamespace(xfrc_applied=np.zeros((2, 6)), ncon=0,
                                          warning=SimpleNamespace(number=np.zeros(7, dtype=int)))
        else:
            native.case = SimpleNamespace(timestep=.001)
            native.scene = SimpleNamespace(step=lambda dt: None)
            native.box = SimpleNamespace(
                set_external_forces_on_dofs=lambda indices, force: None,
                get_contact_points_world=lambda: [],
                get_convergence_status=lambda: SimpleNamespace(name='CONVERGED'),
                get_contact_force_world=lambda: np.zeros(3),
            )
        return native

    def test_both_adapters_count_native_and_observation_once(self):
        for cls in (MuJoCoPlane, SuperDexPlane):
            native = self.native(cls)
            with self.subTest(engine=cls.__name__), patch(
                'dexlab.contact_plane_native.time.perf_counter', side_effect=[10, 10.125, 10.5]
            ):
                result = native.step()
                self.assertTrue(result[4])
                self.assertEqual(native.step_timing,
                                 {'native_call_seconds': .125, 'observation_seconds': .375, 'steps': 1})

    def test_disabled_timing_never_reads_the_clock(self):
        for cls in (MuJoCoPlane, SuperDexPlane):
            native = self.native(cls)
            native.step_timing = None
            with self.subTest(engine=cls.__name__), patch(
                'dexlab.contact_plane_native.time.perf_counter', side_effect=AssertionError('unexpected timer')
            ):
                self.assertTrue(native.step()[4])
