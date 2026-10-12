"""Resumable downloads retain failures and cannot escape their finite allowance."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dexlab.libero_download import LIMITS, _headers, create_plan, download_one, recover
from dexlab.migration_budget import json_bytes, publish


class Response(io.BytesIO):
    def __init__(self, body, *, status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {"Content-Length": str(len(body)), "ETag": '"pinned"'}


class LiberoDownloadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ledger = self.root / "ledger"
        self.inventory_hash = "f" * 64
        create_plan(self.ledger, self.inventory_hash)
        self.body = b"complete official bytes"
        self.expected = {"path": "libero_goal/task_demo.hdf5", "bytes": len(self.body),
                         "sha256": hashlib.sha256(self.body).hexdigest()}
        self.destination = self.root / "data" / self.expected["path"]

    def get(self):
        return download_one(self.ledger, self.inventory_hash, self.expected, self.destination)

    def partial(self, body, *, etag='"pinned"'):
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        path = self.destination.with_name(self.destination.name + ".partial")
        path.write_bytes(body)
        metadata = self.destination.with_name(self.destination.name + ".http.json")
        metadata.write_bytes(json_bytes({"dataset": self.expected, "etag": etag}))
        return path

    def test_complete_file_is_hash_verified_and_existing_final_is_never_overwritten(self):
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=Response(self.body)):
            self.assertEqual(self.get()["status"], "downloaded-hash-verified")
        self.assertEqual(self.destination.read_bytes(), self.body)
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            self.assertEqual(self.get()["status"], "existing-pinned-file")
            request.assert_not_called()
        self.destination.write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "Existing final"):
            self.get()
        self.assertEqual(self.destination.read_bytes(), b"bad")

    def test_resume_checks_range_etag_and_identity_before_appending(self):
        offset = 4
        self.partial(self.body[:offset])
        response = Response(self.body[offset:], status=206, headers={
            "Content-Length": str(len(self.body) - offset), "ETag": '"pinned"',
            "Content-Range": f"bytes {offset}-{len(self.body)-1}/{len(self.body)}"})
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=response) as request:
            self.assertEqual(self.get()["received_bytes"], len(self.body) - offset)
        self.assertEqual(request.call_args.args[0].get_header("Range"), "bytes=4-")
        self.assertEqual(request.call_args.args[0].get_header("If-range"), '"pinned"')
        self.assertEqual(self.destination.read_bytes(), self.body)

    def test_ignored_range_or_wrong_etag_cannot_modify_existing_partial(self):
        original = self.body[:4]
        partial = self.partial(original)
        for status, etag in ((200, '"pinned"'), (206, '"changed"')):
            response = Response(self.body[4:], status=status, headers={
                "Content-Length": str(len(self.body) - 4), "ETag": etag,
                "Content-Range": f"bytes 4-{len(self.body)-1}/{len(self.body)}"})
            with patch("dexlab.libero_download.urllib.request.urlopen", return_value=response):
                with self.assertRaisesRegex(ValueError, "Resume requires"):
                    self.get()
            self.assertEqual(partial.read_bytes(), original)
            self.assertFalse(self.destination.exists())

    def test_premature_eof_retains_bytes_and_failed_attempt_charges_full_reservation(self):
        response = Response(self.body[:4], headers={"Content-Length": str(len(self.body)), "ETag": '"pinned"'})
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "ended before"):
                self.get()
        partial = self.destination.with_name(self.destination.name + ".partial")
        self.assertEqual(partial.read_bytes(), self.body[:4])
        receipt = json.loads((self.ledger / "attempts/0001.finished.json").read_bytes())
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["received_body_bytes"], 4)
        self.assertEqual(receipt["body_bytes_charged"], len(self.body))
        self.assertFalse(self.destination.exists())

    def test_wrong_complete_digest_is_retained_without_publishing_final(self):
        body = b"x" * len(self.body)
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=Response(body)):
            with self.assertRaisesRegex(ValueError, "digest"):
                self.get()
        self.assertEqual(self.destination.with_name(self.destination.name + ".partial").read_bytes(), body)
        self.assertFalse(self.destination.exists())

    def test_header_length_encoding_and_strong_etag_are_required(self):
        for change in ({"Content-Length": "wrong"}, {"Content-Encoding": "gzip"}):
            headers = {"Content-Length": str(len(self.body)), "ETag": '"pinned"', **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                _headers(Response(self.body, headers=headers), self.expected, 0, None)
        self.partial(self.body[:4], etag='W/"weak"')
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "strong ETag"):
                self.get()
            request.assert_not_called()

    def test_per_file_retry_budget_stops_before_another_request(self):
        for _ in range(3):
            with patch("dexlab.libero_download.urllib.request.urlopen", side_effect=OSError("offline")):
                with self.assertRaises(OSError):
                    self.get()
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                self.get()
            request.assert_not_called()
        self.assertEqual(len(list((self.ledger / "attempts").glob("*.started.json"))), 3)

    def test_unfinished_owner_blocks_then_dead_owner_is_charged_before_resume(self):
        plan_hash = hashlib.sha256((self.ledger / "plan.json").read_bytes()).hexdigest()
        started = {"plan_sha256": plan_hash, "dataset": self.expected["path"],
                   "owner": {"pid": 1234}, "reserved_body_bytes": len(self.body)}
        publish(self.ledger / "attempts/0001.started.json", json_bytes(started))
        with self.assertRaisesRegex(ValueError, "Unfinished"):
            self.get()
        with patch("dexlab.libero_download._alive", return_value=True):
            with self.assertRaisesRegex(ValueError, "still live"):
                recover(self.ledger, self.inventory_hash)
        with patch("dexlab.libero_download._alive", return_value=False):
            self.assertEqual(recover(self.ledger, self.inventory_hash), 1)
        receipt = json.loads((self.ledger / "attempts/0001.finished.json").read_bytes())
        self.assertEqual(receipt["wall_s_charged"], LIMITS["attempt_wall_s"])
        self.assertEqual(receipt["body_bytes_charged"], len(self.body))
        self.assertIsNone(receipt["actual_received_bytes"])

    def test_changed_plan_or_missing_attempt_cannot_reset_the_budget(self):
        with self.assertRaisesRegex(ValueError, "Transfer plan differs"):
            download_one(self.ledger, "a" * 64, self.expected, self.destination)
        publish(self.ledger / "attempts/0002.started.json", json_bytes({}))
        with self.assertRaisesRegex(ValueError, "sequence is incomplete"):
            self.get()

    def test_corrupt_usage_and_cumulative_limits_block_new_network_requests(self):
        with patch("dexlab.libero_download.urllib.request.urlopen", return_value=Response(self.body)):
            self.get()
        self.destination.unlink()
        receipt = self.ledger / "attempts/0001.finished.json"
        original = json.loads(receipt.read_bytes())
        for key, value in (("body_bytes_charged", -1), ("wall_s_charged", -1)):
            receipt.write_bytes(json_bytes({**original, key: value}))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Invalid transfer accounting"):
                self.get()
        receipt.write_bytes(json_bytes({**original, "wall_s_charged": LIMITS["max_wall_s"]}))
        with patch("dexlab.libero_download.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                self.get()
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
