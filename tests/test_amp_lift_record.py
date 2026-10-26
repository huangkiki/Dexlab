"""Step-boundary and failure preservation tests; no GPU qualification claim."""

from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.amp_lift_record import (AmpEpisodeObserver, AmpLiftRecorder,
                                    MODEL_ARRAYS, INPUT_ARRAYS, RESULT_ARRAYS)
from dexlab.libero_substeps import read_chunk


class Array:
    def __init__(self, value, **_):
        self.value = np.asarray(value)

    def numpy(self):
        return self.value.copy()

    def detach(self):
        return self

    def cpu(self):
        return self

    def __ge__(self, other):
        return Array(self.value >= other)


def decode_fixture(_model, data, _ids, to_world, output):
    if to_world:
        raise AssertionError("Fixture expects contact-local forces")
    output.value[0] = [float(data.efc.force.value[0, 0]), 0, 0, 0, 0, 0]


class AmpLiftRecordTests(unittest.TestCase):
    def test_timeout_endpoint_is_saved_before_original_reset(self):
        fields = {name: Array([20]) for name in (
            "episode_length_buf", "success_hold_buf", "contact_settle_buf", "lift_start_step",
            "reset_terminated", "reset_time_outs", "reward_buf")}
        fields.update(trajectory_start_pos_w=Array([[0., 0., .125]]),
                      trajectory_goal_pos_w=Array([[0., 0., .5]]), assist_force_frac=Array([0.]))
        data = SimpleNamespace(qpos=Array([[1., 2.]]), qvel=Array([[3., 4.]]), time=Array([60.]))
        sensor = SimpleNamespace(data=SimpleNamespace(found=Array([[1]]), force=Array([[0., 0., 10.]])))
        resets = []
        env = SimpleNamespace(
            **fields, cfg=SimpleNamespace(hold_steps=20), virtual_pd_assistance_scale=0.,
            object_reset_height_frac=0., sim=SimpleNamespace(wp_data=data),
            toaster=SimpleNamespace(data=SimpleNamespace(root_link_pos_w=Array([[0., 0., .5]]))),
            scene={f"{side}_hand_toaster_contact": sensor for side in ("left", "right")},
            _object_lifted=lambda: Array([True]), _both_marker_contacts=lambda: Array([True]),
            _get_hand_toaster_dis=lambda: Array(np.zeros((1, 2, 3))))

        def reset(ids=None):
            resets.append(ids)
            env.success_hold_buf.value[:] = 0
            data.qpos.value[:] = 99
            data.time.value[:] = 0
            sensor.data.found.value[:] = 0

        env._reset_idx = reset

        def step(action):
            self.assertEqual(action, "original command")
            env._reset_idx([0])
            return {"reset_observation": 99}

        observer = AmpEpisodeObserver(env)
        result, feedback = observer.step(SimpleNamespace(step=step), "original command")
        observer.close()
        self.assertIs(env._reset_idx, reset)
        self.assertEqual(resets, [[0]])
        self.assertEqual(result, {"reset_observation": 99})
        self.assertTrue(feedback["automatic_reset"])
        self.assertTrue(feedback["source_success"][0])
        self.assertEqual(feedback["success_hold_buf"][0], 20)
        self.assertEqual(feedback["native_time"], 60.)
        np.testing.assert_array_equal(feedback["qpos"], [1., 2.])
        self.assertEqual(feedback["sensors"]["left"]["found"][0, 0], 1)

    def test_observer_preserves_failure_and_only_restores_its_own_hook(self):
        original = lambda _ids=None: None
        env = SimpleNamespace(_reset_idx=original)
        observer = AmpEpisodeObserver(env)

        def fail(_actions):
            raise RuntimeError("native failure")

        with self.assertRaisesRegex(RuntimeError, "native failure"):
            observer.step(SimpleNamespace(step=fail), None)
        self.assertFalse(observer.stepping)
        replacement = lambda _ids=None: None
        env._reset_idx = replacement
        observer.close()
        self.assertIs(env._reset_idx, replacement)

    def test_original_step_graph_and_failed_prefix_are_preserved(self):
        # A caller writes its action immediately before the original step.
        # Only that original step advances time/state or solves a contact.
        fields = {name: Array([[0.]]) for name in set(INPUT_ARRAYS + RESULT_ARRAYS)}
        fields.update(nworld=1, naconmax=1, njmax=1, nacon=Array([0]), nefc=Array([0]),
                      time=Array([0.]), solver_niter=Array([0]),
                      efc=SimpleNamespace(force=Array([[0.]])))
        contact = SimpleNamespace(
            geom=Array([[0, 1]]), dist=Array([-.001]), pos=Array([[0., 0., 0.]]),
            frame=Array([np.eye(3)]), worldid=Array([0]), efc_address=Array([[0]]),
            dim=Array([1]), friction=Array([[1., 1., 1., 1., 1.]]),
            includemargin=Array([0.]), solref=Array([[.02, 1.]]), solimp=Array([[.9] * 5]))
        data = SimpleNamespace(**fields, contact=contact)
        options = {name: 0 for name in (
            "integrator", "cone", "solver", "iterations", "ls_iterations",
            "ccd_iterations", "disableflags", "enableflags")}
        options.update({name: Array([.005]) for name in (
            "timestep", "gravity", "tolerance", "ls_tolerance", "ccd_tolerance")})
        model = SimpleNamespace(**{name: Array([0.]) for name in MODEL_ARRAYS},
                                opt=SimpleNamespace(**options))
        template = SimpleNamespace(nbody=2, ngeom=2, njnt=1, nu=1, nsite=1,
                                   **{name: lambda i: SimpleNamespace(name=str(i))
                                      for name in ("body", "geom", "joint", "actuator", "site")})
        calls = []

        def original():
            calls.append(float(data.ctrl.value[0, 0]))
            data.qpos.value[0, 0] += data.ctrl.value[0, 0]
            data.time.value[0] += .005
            data.nacon.value[0] = 1
            data.nefc.value[0] = 1
            data.efc.force.value[0, 0] = 9.81

        sim = SimpleNamespace(wp_data=data, wp_model=model, mj_model=template,
                              use_cuda_graph=True, wp_device="fixture", step=original)
        modules = {
            "mujoco": SimpleNamespace(mj_saveModel=lambda _m, p: Path(p).write_bytes(b"fixture")),
            "mujoco_warp": SimpleNamespace(contact_force=decode_fixture),
            "warp": SimpleNamespace(ScopedDevice=lambda _device: nullcontext(),
                                    array=Array, spatial_vector=object(),
                                    zeros=lambda n, **_: Array(np.zeros((n, 6)))),
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict("sys.modules", modules):
            output = Path(tmp) / "run"
            recorder = AmpLiftRecorder(sim, output)
            recorder.start_action(0)
            data.ctrl.value[0, 0] = 7
            sim.step()
            self.assertEqual(calls, [7.])
            self.assertTrue(sim.use_cuda_graph)
            # A failed second substep must not erase the first observation.
            data.nefc.value[0] = 2
            with self.assertRaisesRegex(ValueError, "overflow"):
                sim.step()
            recorder.close()
            self.assertIs(sim.step, original)
            self.assertEqual(calls, [7.])
            rows = read_chunk(output / "substeps/action-000000.npz")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["before"]["ctrl"][0], 7)
            self.assertEqual(rows[0]["before"]["qpos"][0], 0)
            self.assertEqual(rows[0]["after"]["qpos"][0], 7)
            self.assertEqual(rows[0]["contacts"]["local_force"][0, 0], 9.81)
            metadata = json.loads((output / "recording.json").read_text())
            self.assertEqual(metadata["status"], "partial")
            self.assertFalse(metadata["native_qualified"])


if __name__ == "__main__":
    unittest.main()
