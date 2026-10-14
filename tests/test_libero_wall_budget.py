"""A wall extension preserves accounting and cannot modify a live reservation."""

import hashlib
import json
import unittest
from unittest.mock import patch

from dexlab.libero_download import EXTENDED_WALL_LIMITS, LIMITS, amend_wall_budget, recover
from dexlab.migration_budget import json_bytes
import test_libero_download as helpers


class WallBudgetTests(unittest.TestCase):
    setUp = helpers.LiberoDownloadTests.setUp
    get = helpers.LiberoDownloadTests.get

    def seed_and_evidence(self):
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=helpers.Response(self.body)):
            self.get()
        self.destination.unlink()
        evidence = self.root / "evidence.json"
        evidence.write_bytes(json_bytes({
            "inventory_sha256": self.inventory_hash,
            "transfer_plan_sha256": hashlib.sha256((self.ledger / "plan.json").read_bytes()).hexdigest(),
            "completed_successful_transfers": 1,
            "observed_largest_transfer_estimate_s": 1023,
        }))
        return evidence

    def amend(self, evidence):
        with patch("dexlab.libero_download._alive", return_value=False):
            return amend_wall_budget(self.ledger, self.inventory_hash, evidence, "Measured largest file exceeds the old window")

    def test_extension_keeps_original_plan_and_every_prior_charge(self):
        evidence = self.seed_and_evidence()
        frozen = {p: p.read_bytes() for p in self.ledger.rglob("*.json")}
        self.amend(evidence)
        for path, raw in frozen.items():
            self.assertEqual(path.read_bytes(), raw)
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=helpers.Response(self.body)):
            self.get()
        start = json.loads((self.ledger / "attempts/0002.started.json").read_bytes())
        self.assertEqual(start["reserved_wall_s"], EXTENDED_WALL_LIMITS["attempt_wall_s"])
        self.assertEqual(start["wall_amendment_sha256"], hashlib.sha256((self.ledger / "wall-amendment.json").read_bytes()).hexdigest())
        receipts = [json.loads(p.read_bytes()) for p in (self.ledger / "attempts").glob("*.finished.json")]
        self.assertEqual(sum(r["body_bytes_charged"] for r in receipts), 2 * len(self.body))

    def test_live_owner_or_unfinished_reservation_blocks_amendment(self):
        evidence = self.seed_and_evidence()
        with patch("dexlab.libero_download._alive", return_value=True):
            with self.assertRaisesRegex(ValueError, "terminal history"):
                amend_wall_budget(self.ledger, self.inventory_hash, evidence, "Measured capacity")
        (self.ledger / "attempts/0001.finished.json").unlink()
        with self.assertRaisesRegex(ValueError, "terminal history"):
            self.amend(evidence)
        self.assertFalse((self.ledger / "wall-amendment.json").exists())

    def test_new_interruption_charges_its_extended_reservation(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        with patch("dexlab.libero_download.urllib.request.urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                self.get()
        (self.ledger / "attempts/0002.finished.json").unlink()
        with patch("dexlab.libero_download._alive", return_value=False):
            self.assertEqual(recover(self.ledger, self.inventory_hash), 1)
        receipt = json.loads((self.ledger / "attempts/0002.finished.json").read_bytes())
        self.assertEqual(receipt["wall_s_charged"], EXTENDED_WALL_LIMITS["attempt_wall_s"])

    def test_old_cumulative_wall_cost_still_exhausts_new_allowance(self):
        evidence = self.seed_and_evidence()
        receipt = self.ledger / "attempts/0001.finished.json"
        old = json.loads(receipt.read_bytes())
        receipt.write_bytes(json_bytes({**old, "wall_s_charged": EXTENDED_WALL_LIMITS["max_wall_s"] - 1799}))
        self.amend(evidence)
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                self.get()
            request.assert_not_called()

    def test_repeated_amendment_does_not_create_another_allowance(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        with self.assertRaisesRegex(ValueError, "no prior amendment"):
            self.amend(evidence)

    def test_prior_receipt_or_evidence_mutation_blocks_network(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        for path in [self.ledger / "attempts/0001.finished.json", self.ledger / "wall-amendment-evidence.json"]:
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.subTest(path=path), patch("dexlab.libero_download.urllib.request.urlopen") as request:
                with self.assertRaisesRegex(ValueError, "Invalid wall-budget amendment"):
                    self.get()
                request.assert_not_called()
            path.write_bytes(original)

    def test_removing_amendment_after_a_new_attempt_cannot_revert_accounting(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        with patch("dexlab.libero_download.urllib.request.urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                self.get()
        (self.ledger / "wall-amendment.json").unlink()
        with self.assertRaisesRegex(ValueError, "frozen wall allowance"):
            self.get()

    def test_wrong_plan_evidence_is_rejected_before_publication(self):
        evidence = self.seed_and_evidence()
        report = json.loads(evidence.read_bytes())
        evidence.write_bytes(json_bytes({**report, "inventory_sha256": "0" * 64}))
        with self.assertRaisesRegex(ValueError, "measured evidence"):
            self.amend(evidence)
        self.assertFalse((self.ledger / "wall-amendment.json").exists())

    def test_per_file_attempt_cap_is_not_extended(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        for _ in range(LIMITS["max_attempts_per_file"] - 1):
            with patch("dexlab.libero_download.urllib.request.urlopen", side_effect=OSError("offline")):
                with self.assertRaises(OSError):
                    self.get()
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                self.get()
            request.assert_not_called()

    def test_body_byte_cap_keeps_prior_cost(self):
        evidence = self.seed_and_evidence()
        self.amend(evidence)
        self.expected = {**self.expected, "bytes": LIMITS["max_body_bytes"]}
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                self.get()
            request.assert_not_called()
