import unittest

from dexlab.cloth_pad_sweep import audit


def rows(start, end, pad_end=(0, 0, 0)):
    return [
        {
            "step": i,
            "pos": [point],
            "pad_pos": [pad, [10, 10, 10]],
            "pad_quat": [[1, 0, 0, 0], [1, 0, 0, 0]],
        }
        for i, point, pad in [(0, start, [0, 0, 0]), (1, end, pad_end)]
    ]


class SweepTests(unittest.TestCase):
    def test_crossing_invisible_at_both_endpoints(self):
        result = audit(rows([-0.02, 0, 0], [0.02, 0, 0]))
        self.assertEqual(result["endpoint_invisible_intrusion_intervals"], 1)
        witness = result["first_endpoint_invisible_witness"]
        self.assertAlmostEqual(witness["enter_fraction"], 0.25)
        self.assertAlmostEqual(witness["exit_fraction"], 0.75)

    def test_translating_pad_hits_stationary_vertex(self):
        result = audit(rows([0.02, 0, 0], [0.02, 0, 0], [0.04, 0, 0]))
        self.assertEqual(result["endpoint_invisible_intrusion_intervals"], 1)

    def test_grazing_and_parallel_miss(self):
        for y in (0.03, 0.04):
            self.assertEqual(
                audit(rows([-0.02, y, 0], [0.02, y, 0]))[
                    "intruding_vertex_pad_intervals"
                ],
                0,
            )

    def test_endpoint_intrusion_is_not_hidden(self):
        result = audit(rows([0, 0, 0], [0.02, 0, 0]))
        self.assertEqual(result["intruding_vertex_pad_intervals"], 1)
        self.assertEqual(result["endpoint_invisible_intrusion_intervals"], 0)

    def test_invalid_records_rejected(self):
        for change in ("step", "rotation", "nonfinite"):
            data = rows([0, 0, 0], [0.02, 0, 0])
            if change == "step":
                data[1]["step"] = 2
            if change == "rotation":
                data[1]["pad_quat"][0] = [0, 1, 0, 0]
            if change == "nonfinite":
                data[1]["pos"][0][0] = float("nan")
            with self.assertRaises(ValueError):
                audit(data)
