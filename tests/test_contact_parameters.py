"""Archive-level parameter checks without requiring the external PhysX SDK."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from test_contact_plane import exact_record

from dexlab.contact_archive import read_contacts, write_contacts
from dexlab.contact_parameters import native_checks
from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import verify
from dexlab.physx_baseline import digest, write_json


class NativeParameterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = PlaneCase(friction=0)
        self.receipt = {
            "engine": "physx",
            "native": {
                "mass_readback": [[0, self.case.mass, 10]],
                "friction_readback": [[[0, 0, 0], [0, 0, 0]]],
            },
        }
        write_json(
            self.root / "layout.json",
            {
                "nu": 0,
                "entities": [{"name": "box", "body_names": ["body"], "body_ids": [1]}],
            },
        )
        self.records = {
            "box": {
                "body_mass": [[self.case.mass]],
                "body_inertia": [[np.diag(self.case.inertia).tolist()]],
                "geom_friction": [[[0, 0, 0]]],
            },
            "table": {"geom_friction": [[[0, 0, 0]]]},
        }
        write_json(self.root / "native-records.json", self.records)
        write_json(
            self.root / "worker-exit.json", {"returncode": 0, "terminated": True}
        )

    def check(self):
        return native_checks(self.root, self.receipt, self.case)

    def test_native_mass_inertia_friction_and_exit_are_required(self):
        self.assertTrue(all(self.check().values()))
        self.records["box"]["body_inertia"][0][0][0][1] = 0.1
        write_json(self.root / "native-records.json", self.records)
        self.assertFalse(self.check()["native_inertia_matches"])
        self.receipt["native"]["mass_readback"] = [[0, 10, self.case.mass]]
        self.assertFalse(self.check()["native_mass_matches"])

    def test_failed_or_missing_worker_is_not_clean_shutdown(self):
        for payload in ({"returncode": -9, "terminated": True}, {}, {"returncode": 0}):
            write_json(self.root / "worker-exit.json", payload)
            self.assertFalse(self.check()["clean_worker_exit"])
        (self.root / "worker-exit.json").unlink()
        self.assertFalse(self.check()["clean_worker_exit"])

    def test_missing_or_malformed_native_record_fails_closed(self):
        for payload in ({}, {"box": {"body_mass": []}}):
            write_json(self.root / "native-records.json", payload)
            self.assertFalse(all(self.check().values()))
        (self.root / "native-records.json").write_text("{")
        self.assertFalse(all(self.check().values()))

    def test_corrupted_physx_archive_does_not_enter_scalar_mass_branch(self):
        from dataclasses import asdict

        from dexlab.contact_plane import LIMITS

        data = exact_record(self.case)
        np.savez(self.root / "states.npz", **data)
        write_json(
            self.root / "contacts.json",
            [
                {"normal_force": [f.tolist()], "friction_force": []}
                for f in data["contact_force"]
            ],
        )
        receipt = self.receipt | {
            "case": asdict(self.case),
            "limits": LIMITS,
            "status": "completed",
            "source_unchanged": True,
            "artifact_sha256": {"states.npz": digest(self.root / "states.npz")},
        }
        write_json(self.root / "run.json", receipt)
        result = verify(self.root)
        self.assertFalse(result["checks"]["artifact_hashes_match"])
        self.assertFalse(result["passed"])


class ContactArchiveTests(unittest.TestCase):
    def test_lossless_deterministic_archive_and_legacy_reader(self):
        rows = [{"force": [-0.0, 1e-99, 1.2345678901234567], "status": "STOPPED"}, []]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            name = write_contacts(root, rows)
            first = (root / name).read_bytes()
            self.assertEqual(read_contacts(root, {"contact_archive": name}), rows)
            write_contacts(root, rows)
            self.assertEqual(first, (root / name).read_bytes())
            (root / "contacts.json").write_text(json.dumps(rows))
            self.assertEqual(read_contacts(root, {}), rows)
            with self.assertRaises(ValueError):
                read_contacts(root, {"contact_archive": "../contacts.json"})
