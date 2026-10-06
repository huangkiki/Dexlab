import copy
import unittest
from dexlab.genesis_gpu_score import score


def fixture(case="isolation"):
    count = 1 if case == "reset" else 2
    row = {"pos": [[[0., 0., .02] for _ in range(count)]],
           "force": [[[[0., 0., .62784]] for _ in range(count)]],
           "error_mask": [False] * count}
    episodes = [[copy.deepcopy(row) for _ in range(20)] for _ in range(2)]
    if case == "isolation":
        for sample in episodes[1]:
            sample["pos"][0][1][0] = .1
    return {"case": case, "num_envs": count, "completed": True, "episodes": episodes}


class GPUScoreTests(unittest.TestCase):
    def test_isolation_and_reset(self):
        for case in ("reset", "isolation"):
            self.assertTrue(score(fixture(case))["passed"])

    def test_leak_and_missing_samples(self):
        record = fixture()
        record["episodes"][1][5]["force"][0][0][0][0] = .001
        self.assertFalse(score(record)["passed"])
        record = fixture();record["episodes"][1].pop()
        self.assertFalse(score(record)["passed"])

    def test_missing_or_nonfinite_observation(self):
        for bad in ([], [[float("nan"), 0, 0]]):
            record = fixture();record["episodes"][0][0]["force"][0][0] = bad
            self.assertFalse(score(record)["passed"])

    def test_overflow_requires_specific_failure(self):
        record = {"case": "overflow", "completed": False, "error": "CUDA unavailable"}
        self.assertFalse(score(record)["passed"])
        record.pop("error")
        record["expected_overflow"] = "Exceeding max number of candidate contact points (5)."
        self.assertTrue(score(record)["passed"])
