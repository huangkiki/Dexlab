"""Input admission rejects corruption without selecting demonstrations by outcome."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import h5py
import numpy as np

from dexlab.libero_dataset import (
    EXPOSED_TASK, SPLIT_PROTOCOL, admit_file, aggregate, frozen_inputs, split_assignments, write_receipt,
)
from dexlab.libero_inputs import bddl_identity, benchmark_language
from dexlab.migration_budget import json_bytes
from test_libero_inputs import BDDL


class LiberoDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "task.hdf5"
        self.task = {
            "task_id": "libero_goal/open_the_middle_drawer_of_the_cabinet",
            "suite": "libero_goal", "task": "open_the_middle_drawer_of_the_cabinet",
            "bddl_sha256": hashlib.sha256(BDDL).hexdigest(),
            "definition": bddl_identity(BDDL),
            "benchmark_language": benchmark_language("open_the_middle_drawer_of_the_cabinet"),
        }
        self.make_file()

    def make_file(self, *, ids=("demo_0", "demo_2", "demo_10", "demo_11", "demo_23"), bddl=BDDL):
        self.task["definition"] = bddl_identity(bddl)
        self.task["bddl_sha256"] = hashlib.sha256(bddl).hexdigest()
        definition = self.task["definition"]
        canonical = f"libero/libero/bddl_files/{self.task['suite']}/{self.task['task']}.bddl"
        with h5py.File(self.path, "w") as f:
            data = f.create_group("data")
            data.attrs["bddl_file_name"] = canonical
            data.attrs["env_name"] = definition["problem"].upper()
            data.attrs["problem_info"] = json.dumps({
                "problem_name": definition["problem"], "domain_name": definition["domain"],
                "language_instruction": definition["language"].capitalize(),
            })
            data.attrs["env_args"] = json.dumps({
                "env_name": definition["problem"], "problem_name": definition["problem"],
                "bddl_file": "chiliocosm/bddl_files/old_task_name.bddl",
                "env_kwargs": {"bddl_file_name": canonical},
            })
            data.attrs["num_demos"] = len(ids)
            data.attrs["total"] = len(ids) * 3
            for i, name in enumerate(ids):
                group = data.create_group(name)
                states = np.arange(3 * (8 + i), dtype=np.float64).reshape(3, 8 + i)
                group["actions"] = np.ones((3, 7), dtype=np.float32)
                group["states"] = states
                group.attrs["init_state"] = states[0]
                group.attrs["num_samples"] = 3
                group.attrs["model_file"] = '<mujoco><worldbody><body name="cabinet"/></worldbody></mujoco>'
                # These labels must never be read or affect admission/split.
                group["rewards"] = np.array([float("nan")] * 3)
                group["dones"] = np.array([0, 0, 1])
        self.refresh_hash()

    def refresh_hash(self):
        self.task["dataset"] = {
            "path": f"{self.task['task_id']}_demo.hdf5", "bytes": self.path.stat().st_size,
            "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
        }

    def admit(self, bddl=BDDL):
        return admit_file(self.path, self.task, bddl, "f" * 64)

    def test_joint_task_inventory_keeps_all_nonconsecutive_ids_and_variable_state_widths(self):
        result = self.admit()
        self.assertEqual(result["demonstration_count"], 5)
        self.assertEqual(result["action_count"], 15)
        self.assertEqual(result["validation_count"], 1)
        self.assertEqual([d["demo_id"] for d in result["demonstrations"]],
                         ["demo_0", "demo_2", "demo_10", "demo_11", "demo_23"])
        self.assertEqual([d["state_width"] for d in result["demonstrations"]], [8, 9, 10, 11, 12])
        self.assertEqual(result["linkage"]["embedded_bddl"], "not-provided")
        self.assertEqual(result["linkage"]["environment_bddl_references"],
                         {"bddl_file": "differs", "env_kwargs.bddl_file_name": "matches"})
        self.assertFalse(result["native_qualified"])
        self.assertNotIn("chiliocosm", json.dumps(result))

    def test_free_object_and_multiple_native_goals_use_definition_not_task_name(self):
        for predicate, interest in ((b"(In soup basket)", b"soup basket"),
                                    (b"(And (In soup basket) (In tomato basket))", b"soup tomato basket")):
            raw = BDDL.replace(b"(And (Open cabinet_middle_region))", predicate)
            raw = raw.replace(b"(:obj_of_interest cabinet_middle_region)", b"(:obj_of_interest " + interest + b")")
            self.make_file(bddl=raw)
            self.assertEqual(self.admit(raw)["demonstration_count"], 5)

    def test_full_digest_and_size_are_checked_before_hdf5_is_opened(self):
        self.task["dataset"]["sha256"] = "0" * 64
        with patch("dexlab.libero_dataset.h5py.File") as reader:
            with self.assertRaisesRegex(ValueError, "hash differs"):
                self.admit()
            reader.assert_not_called()
        self.task["dataset"]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "byte count"):
            self.admit()
        self.refresh_hash()
        with self.assertRaisesRegex(ValueError, "BDDL hash"):
            self.admit(BDDL + b"\n")

    def test_canonical_identity_and_semantic_metadata_mismatches_are_rejected(self):
        mutations = [("bddl_file_name", "libero/bddl_files/libero_object/wrong.bddl"),
                     ("env_name", "wrong_problem"),
                     ("problem_info", json.dumps({"problem_name": "wrong"}))]
        for field, value in mutations:
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                f["data"].attrs[field] = value
            self.refresh_hash()
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.admit()
        for field in ("problem_name", "domain_name", "language_instruction"):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                info = json.loads(f["data"].attrs["problem_info"])
                info[field] = "wrong"
                f["data"].attrs["problem_info"] = json.dumps(info)
            self.refresh_hash()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                self.admit()

    def test_embedded_bddl_is_an_actual_byte_comparison_when_present(self):
        with h5py.File(self.path, "r+") as f:
            f["data"].attrs["bddl_file_content"] = BDDL.decode()
        self.refresh_hash()
        self.assertEqual(self.admit()["linkage"]["embedded_bddl"], "exact-byte-match")
        with h5py.File(self.path, "r+") as f:
            f["data"].attrs["bddl_file_content"] = BDDL.decode() + "\n"
        self.refresh_hash()
        with self.assertRaisesRegex(ValueError, "Embedded BDDL"):
            self.admit()

    def test_benchmark_language_match_preserves_bddl_divergence_without_fuzzy_matching(self):
        with h5py.File(self.path, "r+") as f:
            info = json.loads(f["data"].attrs["problem_info"])
            info["language_instruction"] = self.task["benchmark_language"]
            f["data"].attrs["problem_info"] = json.dumps(info)
        self.refresh_hash()
        language = self.admit()["linkage"]["language"]
        self.assertEqual(language["matches"], {"bddl": False, "benchmark": True})
        self.assertNotEqual(language["bddl"], language["benchmark"])
        with h5py.File(self.path, "r+") as f:
            info["language_instruction"] = "please " + self.task["benchmark_language"]
            f["data"].attrs["problem_info"] = json.dumps(info)
        self.refresh_hash()
        with self.assertRaisesRegex(ValueError, "neither"):
            self.admit()

    def test_counts_shapes_nonfinite_and_initial_state_mismatch_fail(self):
        mutations = [
            lambda d: d.attrs.__setitem__("total", 14),
            lambda d: d.attrs.__setitem__("num_demos", 50),
            lambda d: d["demo_0"].attrs.__setitem__("num_samples", 2),
            lambda d: d["demo_0/actions"].__setitem__((2, 6), np.nan),
            lambda d: d["demo_0/states"].__setitem__((2, 7), np.inf),
            lambda d: d["demo_0"].attrs.__setitem__("init_state", np.zeros(8)),
            lambda d: d["demo_0"].attrs.__setitem__("model_file", "<not_mujoco/>"),
            lambda d: d.move("demo_0", "demo_00"),
        ]
        for index, mutate in enumerate(mutations):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                mutate(f["data"])
            self.refresh_hash()
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.admit()
        for shape, dtype in (((3, 6), "f8"), ((2, 7), "f8"), ((3, 7), "i8")):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                del f["data/demo_0/actions"]
                f["data/demo_0/actions"] = np.ones(shape, dtype=dtype)
            self.refresh_hash()
            with self.subTest(shape=shape, dtype=dtype), self.assertRaisesRegex(ValueError, "actions"):
                self.admit()

    def test_soft_external_alias_and_cycle_links_are_rejected_before_following(self):
        for kind in ("soft", "external", "alias", "cycle"):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                if kind == "soft":
                    f["link"] = h5py.SoftLink("/missing")
                elif kind == "external":
                    f["link"] = h5py.ExternalLink("never-open-this.hdf5", "/secret")
                elif kind == "alias":
                    f["data/demo_1"] = f["data/demo_0"]
                else:
                    f["data/cycle"] = f["data"]
            self.refresh_hash()
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "links|Aliased/cyclic"):
                self.admit()

    def test_virtual_and_external_storage_cannot_escape_digest(self):
        for kind in ("virtual", "external"):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                if kind == "virtual":
                    layout = h5py.VirtualLayout(shape=(3, 7), dtype="f8")
                    layout[:] = h5py.VirtualSource("never-open-this.hdf5", "/actions", shape=(3, 7))
                    f.create_virtual_dataset("payload", layout)
                else:
                    f.create_dataset("payload", shape=(3, 7), dtype="f8",
                                     external=[("never-open-this.raw", 0, h5py.h5f.UNLIMITED)])
            self.refresh_hash()
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "storage"):
                self.admit()

    def test_split_is_order_independent_excludes_exposure_and_keeps_full_denominator(self):
        ids = [f"demo_{i}" for i in range(50)]
        split = split_assignments(EXPOSED_TASK, ids)
        self.assertEqual(split, split_assignments(EXPOSED_TASK, list(reversed(ids))))
        self.assertEqual(len(split), 50)
        self.assertEqual(sum(v == "validation" for v in split.values()), 7)
        self.assertTrue(all(split[f"demo_{i}"] == "development" for i in range(13)))
        self.assertEqual(set(split_assignments("small", ids[:4]).values()), {"development"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            split_assignments("duplicate", ["demo_0", "demo_0"])

    def test_resume_compares_whole_receipt_without_overwriting_evidence(self):
        result = self.admit()
        path = self.root / "receipt.json"
        write_receipt(path, result)
        original = path.read_bytes()
        write_receipt(path, self.admit())
        self.assertEqual(path.read_bytes(), original)
        changed = copy.deepcopy(result)
        changed["demonstration_count"] = 1
        with self.assertRaisesRegex(ValueError, "different evidence"):
            write_receipt(path, changed)
        self.assertEqual(path.read_bytes(), original)

    def test_frozen_inventory_and_split_cannot_be_replaced_silently(self):
        inputs = {"tasks": [self.task]}
        (self.root / "inventory.json").write_bytes(json_bytes(inputs))
        (self.root / "split-protocol.json").write_bytes(json_bytes(SPLIT_PROTOCOL))
        with patch("dexlab.libero_dataset.inventory", return_value=inputs):
            self.assertEqual(frozen_inputs(self.root, self.root)[0], inputs)
            (self.root / "split-protocol.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "split protocol"):
                frozen_inputs(self.root, self.root)
        with patch("dexlab.libero_dataset.inventory", return_value={"tasks": []}):
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                frozen_inputs(self.root, self.root)

    def test_aggregate_keeps_missing_and_invalid_inputs_separate_from_admitted_receipts(self):
        receipts = self.root / "receipts"
        inputs = {"tasks": [self.task]}
        data_root = self.root / "datasets"
        path = data_root / self.task["dataset"]["path"]
        path.parent.mkdir(parents=True)
        path.hardlink_to(self.path)
        result = self.admit()
        receipt = receipts / (self.task["task_id"] + ".json")
        write_receipt(receipt, result)
        snapshot = aggregate(inputs, "f" * 64, data_root, receipts)
        self.assertEqual((snapshot["expected_files"], snapshot["available_files"], snapshot["admitted_files"]),
                         (1, 1, 1))
        self.assertEqual(snapshot["observed_demonstrations"], 5)
        path.unlink()
        snapshot = aggregate(inputs, "f" * 64, data_root, receipts)
        self.assertEqual((snapshot["available_files"], snapshot["admitted_files"], snapshot["missing_files"]),
                         (0, 1, 1))
        for key, value in (("dataset_revision", "wrong"), ("demonstration_count", 1),
                           ("inventory_sha256", "e" * 64)):
            changed = copy.deepcopy(result); changed[key] = value
            receipt.write_bytes(json_bytes(changed))
            snapshot = aggregate(inputs, "f" * 64, data_root, receipts)
            self.assertEqual(snapshot["invalid_receipts"], 1)
            self.assertEqual(snapshot["observed_demonstrations"], 0)
            self.assertEqual(len(snapshot["tasks"]), 1)
        receipt.unlink()
        self.assertEqual(aggregate(inputs, "f" * 64, data_root, receipts)["tasks"][0]["content_admission"],
                         "missing-receipt")
        changed = copy.deepcopy(result)
        del changed["linkage"]
        receipt.write_bytes(json_bytes(changed))
        self.assertEqual(aggregate(inputs, "f" * 64, data_root, receipts)["invalid_receipts"], 1)
        partial = path.with_name(path.name + ".partial")
        partial.write_bytes(b"partial")
        snapshot = aggregate(inputs, "f" * 64, data_root, receipts)
        self.assertEqual((snapshot["partial_files"], snapshot["available_files"]), (1, 0))
        self.assertEqual(snapshot["tasks"][0]["partial_bytes"], 7)

    def test_aggregate_rejects_incomplete_or_contradictory_input_evidence(self):
        original = self.admit()
        mutations = {
            "empty linkage": lambda r: r.__setitem__("linkage", {}),
            "wrong language": lambda r: r["linkage"]["language"].__setitem__("dataset", "different task"),
            "wrong match flag": lambda r: r["linkage"]["language"]["matches"].__setitem__("bddl", False),
            "missing reader": lambda r: r.pop("reader"),
            "initial mismatch": lambda r: r["demonstrations"][0].__setitem__("initial_matches_first_state", False),
            "missing initial identity": lambda r: r["demonstrations"][0].pop("initial_state"),
            "wrong state shape": lambda r: r["demonstrations"][0]["initial_state"].__setitem__("shape", [99]),
            "missing model": lambda r: r["demonstrations"][0].pop("model_xml_sha256"),
            "wrong exposure": lambda r: r["demonstrations"][0].__setitem__("previously_exposed", True),
            "wrong dtype": lambda r: r["demonstrations"][0].__setitem__("actions_dtype", None),
            "wrong state dtype": lambda r: r["demonstrations"][0]["first_recorded_state"].__setitem__("dtype", "<f4"),
            "malformed digest": lambda r: r["demonstrations"][0]["initial_state"].__setitem__("sha256", "bad"),
            "unearned native qualification": lambda r: r["linkage"].__setitem__("native_environment_configuration_qualified", True),
        }
        receipts = self.root / "receipts"
        path = receipts / (self.task["task_id"] + ".json")
        path.parent.mkdir(parents=True)
        for name, mutate in mutations.items():
            changed = copy.deepcopy(original)
            mutate(changed)
            path.write_bytes(json_bytes(changed))
            snapshot = aggregate({"tasks": [self.task]}, "f" * 64, self.root, receipts)
            with self.subTest(name=name):
                self.assertEqual(snapshot["invalid_receipts"], 1)
                self.assertEqual(snapshot["admitted_files"], 0)
                self.assertEqual(snapshot["observed_demonstrations"], 0)
                self.assertEqual(snapshot["expected_files"], 1)

    def test_aggregate_preserves_numeric_initial_equality_across_byte_representations(self):
        # +0 and -0 compare equal; an independent attr can also use another float dtype.
        for dtype in ("f4", "f8"):
            self.make_file()
            with h5py.File(self.path, "r+") as f:
                initial = f["data/demo_0/states"][0].astype(dtype)
                initial[0] = -0.0
                del f["data/demo_0"].attrs["init_state"]
                f["data/demo_0"].attrs["init_state"] = initial
            self.refresh_hash()
            result = self.admit()
            demo = result["demonstrations"][0]
            self.assertNotEqual(demo["initial_state"]["sha256"], demo["first_recorded_state"]["sha256"])
            receipts = self.root / "receipts"
            path = receipts / (self.task["task_id"] + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(json_bytes(result))
            snapshot = aggregate({"tasks": [self.task]}, "f" * 64, self.root, receipts)
            self.assertEqual(snapshot["admitted_files"], 1)


if __name__ == "__main__":
    unittest.main()
