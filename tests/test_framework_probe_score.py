"""Reject plausible-looking traces with wrong clocks, epochs or missing contacts."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from dexlab.framework_probe_score import decode_pyramidal_contact, score


class ClockProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        protocol = json.loads((Path(__file__).parents[1] / 'configs/framework-clock-probe-v4.json').read_text())
        protocol['steps'] = 2
        self.write('protocol.json', protocol)
        self.write('invocation.json', {'case': 'mjwarp-support', 'protocol_sha256': hashlib.sha256(
            (self.root / 'protocol.json').read_bytes()).hexdigest()})
        self.write('admission.json', {'naconmax_shared': 200, 'njmax_per_world': 1200,
                                      'use_mujoco_contacts': True})
        self.write('completion.json', {'completed_steps': 2, 'requested_steps': 2})
        self.write('conversion-readback.json', {'compiled': {
            'body_mass': [0., .064], 'nq': 7, 'nv': 6, 'geom_bodyid': [0, 1],
            'state': [0., 0., 0., .02, 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]}})
        self.rows = [{
            'step': i, 'framework_step_count': i, 'framework_time_s': i * .001,
            'gpu_time_s': i * .001, 'gpu_dt_s': [.001], 'nacon': 1, 'nefc': 3,
            'qpos': [0., 0., .02, 1., 0., 0., 0.], 'qvel': [0.] * 6,
            'qacc': [0.] * 6, 'qfrc_constraint': [0., 0., .064 * 9.81, 0., 0., 0.],
            'contacts': [{'geom': [0, 1], 'frame': [0., 0., 1., 1., 0., 0., 0., 1., 0.],
                          'force_local': [.064 * 9.81, 0., 0., 0., 0., 0.]}],
        } for i in (1, 2)]

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def result(self):
        (self.root / 'steps.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in self.rows))
        return score(self.root)

    def test_static_force_balance_passes_without_an_engine(self):
        self.assertTrue(self.result()['passed'])

    def test_initialized_cpu_dt_is_not_used_as_the_gpu_clock(self):
        self.rows[1]['gpu_time_s'] = .004
        result = self.result()
        self.assertFalse(result['checks']['clocks'])
        self.assertFalse(result['passed'])

    def test_dropped_contact_is_rejected_even_when_velocity_is_static(self):
        self.rows[1]['contacts'] = []
        result = self.result()
        self.assertFalse(result['checks']['contact_readback_complete'])
        self.assertFalse(result['checks']['contact_force'])

    def test_wrong_constraint_epoch_is_not_hidden_by_a_support_test(self):
        self.rows[1]['qfrc_constraint'][2] = 0.
        result = self.result()
        self.assertTrue(result['checks']['positive_support'])
        self.assertFalse(result['checks']['momentum'])

    def test_incomplete_or_overflowed_run_is_not_a_pass(self):
        self.rows.pop()
        self.assertFalse(self.result()['checks']['complete'])
        self.rows[0]['nacon'] = 201
        self.assertFalse(self.result()['checks']['capacity'])

    def test_changed_protocol_is_rejected(self):
        path = self.root / 'protocol.json'
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'protocol hash'):
            self.result()

    def test_inactive_contacts_do_not_consume_native_constraint_addresses(self):
        values = [0., 0., .2, 0., 0., 0., .3, 0.]
        self.assertEqual(decode_pyramidal_contact(values, [-1] * 4, [.5] * 5, 3).tolist(), [0.] * 6)
        first = decode_pyramidal_contact(values, [0, 1, 2, 3], [.5] * 5, 3)
        second = decode_pyramidal_contact(values, [4, 5, 6, 7], [.5] * 5, 3)
        self.assertEqual(first.tolist(), [.2, 0., .1, 0., 0., 0.])
        self.assertEqual(second.tolist(), [.3, 0., .15, 0., 0., 0.])
        # Converting all four contacts to contiguous offsets 0,4,8,12 is wrong.
        with self.assertRaisesRegex(ValueError, 'outside'):
            decode_pyramidal_contact(values, [8, 9, 10, 11], [.5] * 5, 3)
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            decode_pyramidal_contact([float('nan')] * 4, [0, 1, 2, 3], [.5] * 5, 3)


if __name__ == '__main__':
    unittest.main()
