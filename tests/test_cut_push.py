"""The last cut must transition continuously to contact, without a material kick."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

try:
    from dexlab.cutting import CutConfig
    from dexlab.tofu_cut import cut_push_target, run, sequential_target
except ModuleNotFoundError as error:
    if error.name not in ('numba', 'scipy'):
        raise
    raise unittest.SkipTest('Install dexlab[cutting]') from error


class CutPushTests(unittest.TestCase):
    def test_blade_stays_in_last_cut_until_side_push_finishes(self):
        for task, start, direction in [('tofu-sequential', 3.3, -1), ('banana', 5.3, 1)]:
            with self.subTest(task=task):
                before = sequential_target(start - 1e-9, 'full', task)[0]
                np.testing.assert_allclose(cut_push_target(start, task), before, atol=1e-9)
                times = np.linspace(start, start + 1.4, 100)
                targets = np.array([cut_push_target(t, task) for t in times])
                self.assertLessEqual(targets[:, 2].max(), .002 + 1e-12)
                self.assertAlmostEqual(direction * (targets[-1, 0] - targets[0, 0]), .012)
                control = np.array([cut_push_target(t, task, push=False) for t in times])
                np.testing.assert_allclose(control[:, 2], targets[:, 2])
                np.testing.assert_allclose(control[:, 0], targets[0, 0])

    def test_both_tasks_default_to_contact_and_never_schedule_a_velocity_probe(self):
        for task, count, start in [('tofu-sequential', 3, 3.3), ('banana', 4, 5.3)]:
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temporary:
                config = (CutConfig(shape='banana', size=(.12, .06, .03), grid_spacing=.006)
                          if task == 'banana' else CutConfig(size=(.09, .03, .03)))
                folder = Path(temporary) / 'run'
                with contextlib.redirect_stdout(io.StringIO()):
                    result = run(folder, config, duration=.001, task=task)
                manifest = json.loads((folder / 'manifest.json').read_text())
                self.assertIsNone(manifest['probe_time_s'])
                self.assertEqual(manifest['motion_start_time_s'], start)
                self.assertEqual(len(result['piece_displacements_m']), count)
                self.assertTrue(result['checks']['external_impulse_matches'])
                self.assertFalse(result['passed'])


if __name__ == '__main__':
    unittest.main()
