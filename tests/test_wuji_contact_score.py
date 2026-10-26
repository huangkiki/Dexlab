"""Analytical force/impulse fixtures distinguish retention from record integrity."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wuji_contact_score", ROOT / "demos/wuji-contact/score.py")
SCORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORE)


class WujiContactScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        config = json.loads((ROOT / "demos/wuji-contact/protocol.json").read_text())
        dt = .01
        config["dt_s"] = dt
        n = round(config["duration_s"] / dt)
        raw = dict(time_s=np.arange(n)*dt, qpos_before=np.zeros((n,27)), qpos_after=np.zeros((n,27)),
                   qvel_before=np.zeros((n,26)), qvel_after=np.zeros((n,26)),
                   support_force=np.zeros((n,3)), object_contact_force=np.zeros((n,3)),
                   external_wrenches=np.zeros((n,4,6)), qfrc_applied=np.zeros((n,26)),
                   actuator_force=np.zeros((n,20)), requested_torque=np.zeros((n,20)),
                   warnings=np.zeros((n,8)), max_penetration_m=np.zeros(n),
                   solver_niter=np.ones((n,20)), solver_last_gradient=np.zeros(n), step_wall_s=np.zeros(n))
        contacts, offsets = [], [0]
        position, velocity = np.zeros(3), np.zeros(3)
        mass, gravity = config["mass_kg"], np.array([0.,0.,-9.81])
        for i,t in enumerate(raw["time_s"]):
            raw["qpos_before"][i,20:23] = position
            raw["qvel_before"][i,20:23] = velocity
            if t < 3.6:
                for geom, frame in [(1,np.eye(3)), (2,np.diag([-1.,1.,-1.]))]:
                    force = np.array([1. if geom==1 else -1.,0.,-mass*gravity[2]/2])
                    local = np.r_[frame @ force, np.zeros(3)]
                    contacts.append(np.r_[geom,3,geom,np.zeros(3),frame.reshape(-1),0.,local])
                raw["object_contact_force"][i] = -mass*gravity
            else:
                velocity = velocity + dt*gravity
            position = position + dt*velocity
            raw["qpos_after"][i,20:23] = position
            raw["qvel_after"][i,20:23] = velocity
            offsets.append(len(contacts))
        raw["contacts"],raw["contact_offsets"] = np.array(contacts),np.array(offsets)
        self.raw=raw
        self.manifest=dict(state="recorded",case="hold-release",config=config,
                           effective=dict(timestep=dt,object_geom_id=3,object_body_id=3,
                                          body_names=["world","r_index_finger_pad","r_thumb_pad","object"],
                                          object_mass=mass,gravity=gravity.tolist(),eq_count=0,
                                          actuator_force_limits=[1.]*20))

    def save(self):
        np.savez(self.path/"observations.npz",**self.raw)
        self.manifest["observations_sha256"]=hashlib.sha256((self.path/"observations.npz").read_bytes()).hexdigest()
        (self.path/"manifest.json").write_text(json.dumps(self.manifest))

    def test_supported_then_ballistic_release(self):
        self.save(); report=SCORE.evaluate(self.path)
        self.assertTrue(report["qualification_pass"])
        self.assertTrue(report["numerical_balance_pass"])

    def test_false_contact_force_cannot_pass_balance(self):
        self.raw["contacts"][:,18]*=.5
        # Keep the redundant total consistent, so the independent m*dv check is exercised.
        self.raw["object_contact_force"][:360,2]*=.5
        self.save();report=SCORE.evaluate(self.path)
        self.assertFalse(report["numerical_balance_pass"])
        self.assertFalse(report["hold_pass"])

    def test_hidden_support_rejects_qualification(self):
        self.raw["external_wrenches"][200,3,2]=.1
        self.save();self.assertFalse(SCORE.evaluate(self.path)["record_integrity_pass"])

    def test_state_injection_rejected(self):
        self.raw["qpos_before"][200,20]+=.01
        self.save()
        with self.assertRaisesRegex(ValueError,"discontinuity"):
            SCORE.evaluate(self.path)

    def test_dropped_contacts_rejected(self):
        self.raw["contact_offsets"][-1]-=1
        self.save()
        with self.assertRaisesRegex(ValueError,"contact record"):
            SCORE.evaluate(self.path)

    def test_no_release_is_not_qualification(self):
        # A valid held trajectory can satisfy holding without active release.
        self.raw["qpos_before"][:]=0;self.raw["qpos_after"][:]=0
        self.raw["qvel_before"][:]=0;self.raw["qvel_after"][:]=0
        self.save();report=SCORE.evaluate(self.path)
        self.assertFalse(report["release_pass"])
        self.assertFalse(report["qualification_pass"])

    def test_raw_hash_change_rejected(self):
        self.save()
        with (self.path/"observations.npz").open("ab") as stream:stream.write(b"changed")
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            SCORE.evaluate(self.path)


if __name__ == "__main__":
    unittest.main()
