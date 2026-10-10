"""Alignment cannot partially mutate a model before a malformed field is rejected."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location(
    'native_probe', Path(__file__).parents[1] / 'scripts/probe_native_mjwarp.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class Array:
    def __init__(self, data):
        self.data = np.asarray(data, dtype=np.float32)

    def numpy(self):
        return self.data.copy()

    def assign(self, value):
        self.data[:] = value


class AlignmentTests(unittest.TestCase):
    def test_last_field_shape_error_leaves_every_array_unchanged(self):
        model = SimpleNamespace(
            body_iquat=Array([[[1., 0., 0., 0.]]]), body_inertia=Array([[[1., 1., 1.]]]),
            body_invweight0=Array([[[1., 1.]]]), stat=SimpleNamespace(meaninertia=Array([1.])))
        requested = {'body_iquat': [[[0., 1., 0., 0.]]], 'body_inertia': [[[2., 2., 2.]]],
                     'body_invweight0': [[[.5, .5]]], 'stat.meaninertia': [2., 2.]}
        with self.assertRaisesRegex(ValueError, 'shape/value'):
            probe.align_inertia_parameters(model, requested)
        self.assertEqual(model.body_iquat.numpy().tolist(), [[[1., 0., 0., 0.]]])
        self.assertEqual(model.body_inertia.numpy().tolist(), [[[1., 1., 1.]]])
        requested['stat.meaninertia'] = [2.]
        receipt = probe.align_inertia_parameters(model, requested)
        self.assertEqual(receipt['after'], requested)
        self.assertEqual(receipt['before']['stat.meaninertia'], [1.])
        requested['body_mass'] = [1.]
        with self.assertRaisesRegex(ValueError, 'exactly the four'):
            probe.align_inertia_parameters(model, requested)


if __name__ == '__main__':
    unittest.main()
