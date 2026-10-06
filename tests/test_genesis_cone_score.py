import copy
import unittest
from dexlab.genesis_cone_score import summarize, validate_manifest


class GenesisConeScoreTests(unittest.TestCase):
    def trace(self):
        row = dict(position=[0, 0, .025], velocity=[0, 0, 0],
                   quaternion=[1, 0, 0, 0], force=[[0, 0, 1.22625]])
        return dict(before=copy.deepcopy(row), after=copy.deepcopy(row),
                    samples=[copy.deepcopy(row) for _ in range(40)])

    def test_stationary_supported_block(self):
        result = summarize(self.trace())
        self.assertEqual(result['max_abs_vertical_speed_m_s'], 0)
        self.assertEqual(result['max_conditional_vx_error_m_s'], 0)

    def test_missing_sample_is_not_success(self):
        record = self.trace()
        record['samples'].pop()
        with self.assertRaises(ValueError):
            summarize(record)

    def test_nonfinite_force_rejected(self):
        record = self.trace()
        record['samples'][9]['force'][0][2] = float('nan')
        with self.assertRaises(ValueError):
            summarize(record)

    def test_transient_is_retained(self):
        record = self.trace()
        record['samples'][0]['velocity'][2] = .2
        self.assertEqual(summarize(record)['max_abs_vertical_speed_m_s'], .2)

    def test_incomplete_protocol_rejected(self):
        with self.assertRaises(ValueError):
            validate_manifest({"dt_s": .005, "steps": 40, "mu": .5})
