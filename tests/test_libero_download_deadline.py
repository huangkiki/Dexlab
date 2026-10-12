"""Late receive/hash results must remain failed, without publishing a final file."""

import hashlib
import io
import json
import unittest
from unittest.mock import patch

import dexlab.libero_download as download
import test_libero_download as helpers


class DeadlineTests(unittest.TestCase):
    setUp = helpers.LiberoDownloadTests.setUp
    get = helpers.LiberoDownloadTests.get
    partial = helpers.LiberoDownloadTests.partial

    def assert_failed_without_final(self):
        self.assertFalse(self.destination.exists())
        receipt = json.loads((self.ledger / "attempts/0001.finished.json").read_text())
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["body_bytes_charged"], len(self.body))
        self.assertEqual(receipt["wall_s_charged"], download.LIMITS["attempt_wall_s"] + 1)
        self.assertEqual(len(list((self.ledger / "attempts").glob("*.started.json"))), 1)

    def test_late_last_response_chunk_is_retained_but_never_hashed_or_published(self):
        clock = [0.0]
        response = helpers.Response(self.body)
        original = response.read

        def late_read(size):
            result = original(size)
            clock[0] = download.LIMITS["attempt_wall_s"] + 1
            return result

        with patch.object(response, "read", side_effect=late_read), patch.object(
            download.urllib.request, "urlopen", return_value=response
        ), patch.object(download.time, "monotonic", side_effect=lambda: clock[0]), patch.object(
            download, "_hash_until"
        ) as hashing:
            with self.assertRaises(TimeoutError):
                self.get()
            hashing.assert_not_called()
        self.assert_failed_without_final()
        self.assertEqual(self.destination.with_name(self.destination.name + ".partial").read_bytes(), self.body)

    def test_late_correct_hash_is_rejected_before_publication(self):
        clock = [0.0]

        def late_hash(path, deadline):
            result = hashlib.sha256(path.read_bytes()).hexdigest()
            clock[0] = deadline + 1
            return result

        with patch.object(download.urllib.request, "urlopen", return_value=helpers.Response(self.body)), patch.object(
            download.time, "monotonic", side_effect=lambda: clock[0]
        ), patch.object(download.time, "sleep"), patch.object(download, "_hash_until", side_effect=late_hash):
            with self.assertRaises(TimeoutError):
                self.get()
        self.assert_failed_without_final()

    def test_hashing_checks_deadline_after_blocking_read(self):
        clock = [0.0]

        class DelayedRead(io.BytesIO):
            def read(self, size):
                result = super().read(size)
                clock[0] = 11.0
                return result

        with patch.object(download.Path, "open", return_value=DelayedRead(self.body)), patch.object(
            download.time, "monotonic", side_effect=lambda: clock[0]
        ):
            with self.assertRaises(TimeoutError):
                download._hash_until(self.destination, 10.0)

    def test_complete_partial_hash_is_still_deadline_bounded_without_network(self):
        self.partial(self.body)
        with patch.object(download.urllib.request, "urlopen") as request, patch.object(
            download, "_hash_until", side_effect=TimeoutError("verification deadline")
        ):
            with self.assertRaises(TimeoutError):
                self.get()
            request.assert_not_called()
        self.assertFalse(self.destination.exists())
        receipt = json.loads((self.ledger / "attempts/0001.finished.json").read_text())
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["received_body_bytes"], 0)
