import gzip
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from dexlab.contact_tangent import commands, fit_response, score
from dexlab.contact_tangent_verify import verify
from dexlab.physx_baseline import digest


class TangentIdentificationTests(unittest.TestCase):
    def test_recovers_known_independent_stiffness_and_damping(self):
        t = np.arange(800) * 0.0005
        depth = 0.0002 + 1e-6 * np.sin(2 * np.pi * 20 * t)
        speed = 1e-6 * 2 * np.pi * 20 * np.cos(2 * np.pi * 20 * t)
        fit = fit_response(depth, speed, 1 + 20000 * depth + 40 * speed)
        self.assertAlmostEqual(fit["stiffness_n_m"], 20000, places=6)
        self.assertAlmostEqual(fit["damping_ns_m"], 40, places=6)

    def test_rejects_unidentifiable_and_nonfinite_signals(self):
        x = np.linspace(0, 1, 30)
        for a, b, f in [(x, x, x), (x, x * 0, x), (x, np.sin(x), x * np.nan)]:
            with self.assertRaises(ValueError):
                fit_response(a, b, f)

    def test_commands_freeze_settling_and_amplitude(self):
        loads = commands(4.0, 0.0005)
        np.testing.assert_array_equal(loads[:800], 4.0)
        np.testing.assert_allclose(
            loads[800:1600] - 4, 2 * (loads[1600:] - 4), atol=1e-14
        )
        with self.assertRaises(ValueError):
            commands(3.0, 0.0005)

    @staticmethod
    def synthetic_data():
        # Independent backward-Euler mass/spring/damper reference, not a native run.
        dt, load, mass, stiffness, damping = 0.0005, 4.0, 0.2, 20000.0, 40.0
        command = commands(load, dt)
        n = len(command)
        pose = np.zeros((n + 1, 7))
        pose[:, 3] = 1
        pose[0, 2] = 0.02 - load / stiffness
        velocity = np.zeros((n + 1, 6))
        force = np.zeros((n, 3))
        for i, value in enumerate(command):
            depth = 0.02 - pose[i, 2]
            v = (mass * velocity[i, 2] + dt * (stiffness * depth - value)) / (
                mass + dt * damping + dt * dt * stiffness
            )
            velocity[i + 1, 2] = v
            pose[i + 1, 2] = pose[i, 2] + dt * v
            force[i, 2] = stiffness * (0.02 - pose[i + 1, 2]) - damping * v
        return {
            "time": np.arange(n + 1) * dt,
            "pose": pose,
            "velocity": velocity,
            "force": force,
            "ledger": force.copy(),
            "load": command,
            "completed": np.ones(n, dtype=bool),
            "contacts": np.full(n, 4),
        }

    def test_full_score_recovers_known_model_and_predicts_smaller_amplitude(self):
        result = score(4.0, 0.0005, self.synthetic_data())
        self.assertTrue(result["valid"], result["checks"])
        post = result["epochs"]["post_step"]
        self.assertAlmostEqual(post["fit"]["damping_ns_m"], 40.0, places=6)
        self.assertTrue(post["prediction_ok"])
        self.assertTrue(post["conditional_cL_ok"])
        self.assertTrue(post["amplitude_stability_ok"])

    def test_force_injection_and_missing_contact_are_rejected(self):
        for key, index, change, failed in [
            ("force", (1000, 2), -1.0, "force_ledger"),
            ("ledger", (1000, 2), 1.0, "force_ledger"),
            ("contacts", 1000, -4, "contact_retained"),
            ("velocity", (1000, 2), 0.1, "momentum"),
        ]:
            data = self.synthetic_data()
            data[key][index] += change
            result = score(4.0, 0.0005, data)
            self.assertFalse(result["valid"])
            self.assertFalse(result["checks"][failed])

    def test_archive_verification_reconstructs_force_ledger_and_rejects_tampering(self):
        data = self.synthetic_data()
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            np.savez(root / "states.npz", **data)
            with gzip.open(root / "contacts.jsonl.gz", "wt") as stream:
                for force in data["force"]:
                    stream.write(
                        json.dumps(
                            {
                                "status": "CONVERGED",
                                "contacts": [
                                    {"force_on_box": (force / 4).tolist()}
                                    for _ in range(4)
                                ],
                            }
                        )
                        + "\n"
                    )
            receipt = {
                "load_n": 4.0,
                "timestep_s": 0.0005,
                "arrays_sha256": digest(root / "states.npz"),
                "contacts_sha256": digest(root / "contacts.jsonl.gz"),
            }
            (root / "receipt.json").write_text(json.dumps(receipt))
            self.assertTrue(verify(root)["valid"])
            data["ledger"][1000, 2] += 1
            np.savez(root / "states.npz", **data)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify(root)
            receipt["arrays_sha256"] = digest(root / "states.npz")
            (root / "receipt.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "disagree"):
                verify(root)

    def test_coherent_adhesive_force_injection_fails_momentum(self):
        data = self.synthetic_data()
        data["force"][1000, 2] = -1.0
        data["ledger"][1000, 2] = -1.0
        result = score(4.0, 0.0005, data)
        self.assertTrue(result["checks"]["force_ledger"])
        self.assertFalse(result["checks"]["momentum"])
        self.assertFalse(result["valid"])

    def test_missing_measurements_never_pass(self):
        self.assertFalse(score(2.0, 0.0005, {})["valid"])


if __name__ == "__main__":
    unittest.main()
