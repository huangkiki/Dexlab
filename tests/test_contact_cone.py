"""Analytic synthetic records test the independent scorer, not the native engine."""

from dataclasses import asdict
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from dexlab.contact_cone import IMPEDANCE, case_for, jobs, verify, verify_matrix
from dexlab.contact_plane import reference
from dexlab.physx_baseline import digest


def write_fixture(directory, job=None):
    job = jobs()[0] if job is None else job
    case = case_for(job)
    t = np.arange(case.steps + 1) * case.timestep
    x, vx = reference(case, t)
    pose = np.zeros((case.steps + 1, 7))
    pose[:, 0] = x
    pose[:, 2] = 0.02
    pose[:, 3] = 1
    velocity = np.zeros((case.steps + 1, 6))
    velocity[:, 0] = vx
    force = case.mass * np.diff(velocity[:, :3], axis=0) / case.timestep
    force[:, 2] += case.mass * case.gravity
    np.savez_compressed(
        directory / "states.npz",
        time=t,
        pose=pose,
        velocity=velocity,
        contact_force=force,
        external_force=np.zeros_like(force),
        contact_known=np.ones(case.steps, dtype=bool),
        step_completed=np.ones(case.steps, dtype=bool),
    )
    normal = {"solref": [job["timeconst"], 1.0], "solimp": IMPEDANCE}
    metadata = {
        "engine": "mujoco",
        "identity": {
            "version": "3.15.0",
            "compatibility_profile": "qualification-3.15.0",
        },
        "simulation_options": {
            "timestep": case.timestep,
            "gravity": [0, 0, -9.81],
            "actuator_count": 0,
        },
        "solver": {
            "integrator": 0,
            "algorithm": 2,
            "cone": 1 if job["cone"] == "elliptic" else 0,
            "iterations": 100,
            "tolerance": 1e-10,
            "impratio": 1.0,
            "disableflags": 0,
            "enableflags": 0,
        },
        "normal_parameters_readback": normal,
        "mass_readback": 0.2,
        "inertia_readback": case.inertia.tolist(),
        "friction_readback": [[case.friction, 0, 0]] * 2,
        "geometry_readback": {
            "type": [0, 6],
            "size": [[2, 2, 0.1], [0.02, 0.02, 0.02]],
            "priority": [0, 0],
            "solmix": [1, 1],
            "condim": [3, 3],
            "solref": [normal["solref"]] * 2,
            "solimp": [IMPEDANCE] * 2,
        },
    }
    (directory / "native.json").write_text(json.dumps(metadata))
    (directory / "model.xml").write_text(
        f'<mujoco><option cone="{job["cone"]}" integrator="Euler" solver="Newton" timestep="{case.timestep}" iterations="100" tolerance="1e-10" gravity="0 0 -9.81"/><default><geom solref="{job["timeconst"]} 1" solimp=".95 .99 .001 .5 2"/></default></mujoco>'
    )
    with gzip.open(directory / "contacts.jsonl.gz", "wt") as stream:
        for f in force:
            stream.write(
                json.dumps(
                    {
                        "warnings": [0] * 8,
                        "contacts": [
                            {
                                "force_on_box": f.tolist(),
                                "parameters": {"dimension": 3, **normal},
                            }
                        ],
                    }
                )
                + "\n"
            )
    (directory / "receipt.json").write_text(
        json.dumps({"job": job, "case": asdict(case), "hashes": {}})
    )
    rehash(directory)


def rehash(directory):
    p = directory / "receipt.json"
    r = json.loads(p.read_text())
    r["hashes"] = {
        name: digest(directory / name)
        for name in ("states.npz", "contacts.jsonl.gz", "native.json", "model.xml")
    }
    p.write_text(json.dumps(r))


class ConeScoringTests(unittest.TestCase):
    def test_synthetic_positive_and_exact_frozen_order(self):
        self.assertEqual(len(jobs()), 26)
        self.assertEqual(
            {k: v for k, v in jobs()[0].items() if k != "id"},
            {k: v for k, v in jobs()[24].items() if k != "id"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            write_fixture(p)
            result = verify(p)
            self.assertTrue(result["valid"], result)
            self.assertTrue(result["engineering"]["passed"], result)
            self.assertAlmostEqual(
                result["metrics"]["first10ms_excess_normal_impulse_ns"], 0
            )

    def test_changed_native_or_authored_parameter_fails_despite_rehash(self):
        for kind in ("native", "xml"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)
                write_fixture(p)
                if kind == "native":
                    d = json.loads((p / "native.json").read_text())
                    d["solver"]["cone"] = 0
                    (p / "native.json").write_text(json.dumps(d))
                else:
                    f = p / "model.xml"
                    f.write_text(
                        f.read_text().replace('cone="elliptic"', 'cone="pyramidal"')
                    )
                rehash(p)
                self.assertFalse(verify(p)["valid"])

    def test_coherent_force_injection_is_rejected_by_momentum(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            write_fixture(p)
            with np.load(p / "states.npz") as archive:
                data = dict(archive)
            data["contact_force"][:, 2] += 1
            np.savez_compressed(p / "states.npz", **data)
            with gzip.open(p / "contacts.jsonl.gz", "rt") as stream:
                rows = [json.loads(line) for line in stream]
            for row in rows:
                row["contacts"][0]["force_on_box"][2] += 1
            with gzip.open(p / "contacts.jsonl.gz", "wt") as stream:
                for row in rows:
                    stream.write(json.dumps(row) + "\n")
            rehash(p)
            result = verify(p)
            self.assertTrue(result["checks"]["raw_force_ledger"])
            self.assertFalse(result["checks"]["momentum_balance"])
            self.assertFalse(result["valid"])

    def test_missing_rows_and_stale_hash_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            write_fixture(p)
            with gzip.open(p / "contacts.jsonl.gz", "wt") as stream:
                stream.write("")
            with self.assertRaises(ValueError):
                verify(p)
            rehash(p)
            self.assertFalse(verify(p)["valid"])
            with self.assertRaises(ValueError):
                verify_matrix(p)

    def test_complete_matrix_contrasts_reject_nonidentical_initial_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = Path(__file__).resolve().parents[1]
            (directory / "protocol.json").write_bytes(
                (root / "benchmarks/contact-cone-timeconst-v1.json").read_bytes()
            )
            snapshot = directory / "source"
            snapshot.mkdir()
            hashes = {}
            for source in (root / "src/dexlab").glob("*.py"):
                (snapshot / source.name).write_bytes(source.read_bytes())
                hashes[source.name] = digest(source)
            (directory / "source-hashes.json").write_text(json.dumps(hashes))
            for job in jobs():
                path = directory / job["id"]
                path.mkdir()
                write_fixture(path, job)
            result = verify_matrix(directory)
            self.assertEqual(result["valid_count"], 26)
            self.assertEqual(len(result["contrasts"]), 24)
            self.assertTrue(all(pair["comparable"] for pair in result["contrasts"]))
            path = directory / "case-00"
            with np.load(path / "states.npz") as archive:
                data = dict(archive)
            data["velocity"][0, 0] += 1e-8
            np.savez_compressed(path / "states.npz", **data)
            rehash(path)
            result = verify_matrix(directory)
            self.assertEqual(result["valid_count"], 25)
            self.assertFalse(result["repeats"][0]["exact_arrays"])
            self.assertFalse(any(pair["comparable"] for pair in result["contrasts"]))
