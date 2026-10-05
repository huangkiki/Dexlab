"""Synthetic state sequences test observation only; no dynamics are integrated."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import mujoco
import numpy as np

SOURCE = Path(__file__).resolve().parents[1] / "demos/cloth-folding/src"
sys.path.insert(0, str(SOURCE))
import run_cloth
import settling_trace as trace


class SettlingTraceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.record = self.root / "settling"
        self.model = mujoco.MjModel.from_xml_string('''
          <mujoco><option timestep=".0005"/><worldbody>
          <geom name="table_0" type="box" size="1 1 .003"/>
          <flexcomp name="cloth" type="direct" dim="2" mass=".01"
            point="-2 -2 .01 2 -2 .01 0 2 .01" element="0 1 2">
            <edge equality="true"/>
          </flexcomp></worldbody></mujoco>''')
        self.data = mujoco.MjData(self.model)

    def capture(self, steps=2, directory=None):
        return trace.capture_settling(self.model, self.data, directory or self.record,
                                      steps=steps, engine={"version": mujoco.__version__})

    def advance(self, height):
        self.data.time += self.model.opt.timestep
        self.data.qpos[2::3] = height - .01

    def write_record(self, heights=(0, .01)):
        with self.capture(len(heights)) as capture:
            for height in heights:
                self.advance(height)
                capture()

    def rewrite_states(self, **replacements):
        path = self.record / "states.npz"
        with np.load(path, allow_pickle=False) as source:
            states = dict(source)
        states.update(replacements)
        np.savez(path, **states)
        manifest = json.loads((self.record / "manifest.json").read_text())
        manifest["files"]["states.npz"] = trace.digest(path)
        (self.record / "manifest.json").write_text(json.dumps(manifest))

    def test_first_interior_crossing_with_all_vertices_outside(self):
        with patch("mujoco.mj_step", side_effect=AssertionError("integration")), \
             patch("mujoco.mj_forward", side_effect=AssertionError("forward")), \
             patch("mujoco.mj_fwdPosition", side_effect=AssertionError("native contacts")):
            self.write_record()
            before = {p.name: trace.digest(p) for p in self.record.iterdir()}
            report = trace.audit_saved(self.record)
        first = report["first_intrusion"]
        self.assertEqual(first["frame_index"], 1)
        self.assertAlmostEqual(first["depth_m"], .003)
        self.assertEqual(first["previous_sample_without_intrusion_s"], 0)
        self.assertEqual(report["evaluated_frames"], 2)
        self.assertEqual(report["recorded_frames"], 3)
        self.assertEqual(report["scientific_acceptance"], "not_assessed")
        self.assertEqual(before, {p.name: trace.digest(p) for p in self.record.iterdir()})
        bounds = np.asarray(report["table_bounds_m"])
        points = np.asarray(first["triangle_vertices_m"])
        self.assertTrue(np.all(np.any((points < bounds[0]) | (points > bounds[1]), axis=1)))

    def test_no_crossing_evaluates_all_samples(self):
        self.write_record((.01, .02))
        report = trace.audit_saved(self.record)
        self.assertIsNone(report["first_intrusion"])
        self.assertEqual(report["evaluated_frames"], 3)

    def test_initial_intrusion_has_no_previous_clear_sample(self):
        self.data.qpos[2::3] = -.01
        self.write_record((.01, .02))
        first = trace.audit_saved(self.record)["first_intrusion"]
        self.assertEqual(first["frame_index"], 0)
        self.assertIsNone(first["previous_sample_without_intrusion_s"])

    def test_exception_retains_prefix_and_failed_state_without_success(self):
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with self.capture() as capture:
                self.advance(.01)
                capture()
                self.data.qpos[:] = np.nan
                raise RuntimeError("synthetic failure")
        report = trace.audit_saved(self.record)
        self.assertFalse(report["record_completed"])
        self.assertEqual(report["recorded_frames"], 2)
        with np.load(self.record / "failed-state.npz") as failed:
            self.assertTrue(np.isnan(failed["qpos"]).all())

    def test_duplicate_capture_and_early_finish_are_failures(self):
        for name, duplicate in (("duplicate", True), ("early", False)):
            with self.subTest(name=name), self.assertRaises(ValueError):
                with self.capture(directory=self.root / name) as capture:
                    if duplicate:
                        capture()
            manifest = json.loads((self.root / name / "manifest.json").read_text())
            self.assertFalse(manifest["completed"])

    def test_existing_output_is_never_overwritten(self):
        self.write_record()
        before = trace.digest(self.record / "manifest.json")
        with self.assertRaises(FileExistsError):
            with self.capture():
                pass
        self.assertEqual(before, trace.digest(self.record / "manifest.json"))

    def test_hash_corruption_is_rejected(self):
        self.write_record()
        with (self.record / "states.npz").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            trace.audit_saved(self.record)

    def test_missing_physics_step_is_rejected_even_with_updated_hash(self):
        self.write_record()
        self.rewrite_states(time_s=np.array([0, .001, .0015]))
        with self.assertRaisesRegex(ValueError, "sampling metadata"):
            trace.audit_saved(self.record)

    def test_model_solver_and_report_must_agree(self):
        self.write_record()
        path = self.record / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["iterations"] += 1
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "sampling metadata"):
            trace.audit_saved(self.record)

    def test_nonfinite_velocity_and_wrong_topology_are_rejected(self):
        self.write_record()
        self.rewrite_states(qvel=np.full((3, self.model.nv), np.nan))
        with self.assertRaises(ValueError):
            trace.audit_saved(self.record)
        self.rewrite_states(qvel=np.zeros((3, self.model.nv)), triangles=np.array([[2, 1, 0]]))
        with self.assertRaisesRegex(ValueError, "topology"):
            trace.audit_saved(self.record)

    def test_inputs_changed_during_audit_are_rejected(self):
        self.write_record()
        original = trace.first_table_intrusion

        def mutate(*args):
            result = original(*args)
            with (self.record / "manifest.json").open("a") as stream:
                stream.write(" ")
            return result

        with patch.object(trace, "first_table_intrusion", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                trace.audit_saved(self.record)

    def test_unsupported_table_geometry_is_not_zero_intrusion(self):
        self.model.geom_type[0] = mujoco.mjtGeom.mjGEOM_SPHERE
        with self.assertRaisesRegex(ValueError, "Unsupported table solid"):
            trace.first_table_intrusion(self.model, np.array([0.]), self.data.qpos[None],
                                        self.model.flex_elem.reshape(-1, 3))

    def test_recording_does_not_change_initialization_commands_or_state(self):
        results = []
        for enabled in (False, True):
            self.data = mujoco.MjData(self.model)
            calls = []
            target = self.data.qpos.copy()

            def synthetic_step(model, data, opened):
                self.assertIs(opened, target)
                calls.append((model.opt.timestep, model.opt.solver, model.opt.iterations))
                data.time += model.opt.timestep
                data.qpos[:] += .00001

            with patch.object(run_cloth, "step", side_effect=synthetic_step), \
                 patch("mujoco.mj_step", side_effect=AssertionError("integration")):
                run_cloth.settle_cloth(self.model, self.data, target,
                                       output=self.record if enabled else None,
                                       engine={"version": mujoco.__version__})
            self.assertEqual(len(calls), 4000)
            self.assertEqual(set(calls), {(.0005, int(mujoco.mjtSolver.mjSOL_CG), 100)})
            results.append((self.data.time, self.data.qpos.copy(), self.data.qvel.copy()))
        for a, b in zip(*results, strict=True):
            np.testing.assert_array_equal(a, b)
        manifest = json.loads((self.record / "manifest.json").read_text())
        self.assertTrue(manifest["completed"])
        self.assertEqual(manifest["recorded_steps"], 4000)

    def test_cli_refuses_existing_report_and_writes_outside_record(self):
        self.write_record()
        output = self.root / "report.json"
        with patch.object(sys, "argv", ["settling_trace", str(self.record), "--output", str(output)]):
            trace.main()
        for destination in (output, self.record / "audit.json"):
            with patch.object(sys, "argv", ["settling_trace", str(self.record), "--output", str(destination)]):
                with self.assertRaises(SystemExit) as error:
                    trace.main()
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
