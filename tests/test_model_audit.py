"""Malformed physical models must be reported without changing their values."""

import json
import tempfile
import unittest
from pathlib import Path

import mujoco
import numpy as np

from dexlab.model_audit import (
    check_inertial,
    check_joint,
    findings,
    record_mujoco,
    sample_initial_overlaps,
    write_report,
)


def report_fixture():
    return {
        "schema_version": 1,
        "backend": "superdex",
        "units": {},
        "sources": {},
        "bodies": [
            {
                "name": "body",
                "static": False,
                "massless_reason": None,
                "source": {
                    "mass": 1.0,
                    "com": [0, 0, 0],
                    "inertia": np.eye(3).tolist(),
                },
                "effective": {
                    "mass": 1.0,
                    "com": [0, 0, 0],
                    "inertia": np.eye(3).tolist(),
                },
            }
        ],
        "joints": [],
        "drives": [],
        "initial_overlaps": {"pairs": []},
    }


class InertialAuditTests(unittest.TestCase):
    def test_positive_mass_valid_inertia(self):
        self.assertEqual(check_inertial(1, [0, 0, 0], np.diag([1, 2, 3])), [])

    def test_negative_and_zero_dynamic_mass(self):
        for mass in (-1, 0):
            with self.subTest(mass=mass):
                self.assertIn(
                    "non_positive_dynamic_mass",
                    check_inertial(mass, [0, 0, 0], np.eye(3)),
                )

    def test_massless_frame_is_explicit_and_has_zero_inertia(self):
        self.assertEqual(
            check_inertial(0, [0, 0, 0], np.zeros((3, 3)), massless_frame=True), []
        )
        self.assertIn(
            "non_positive_dynamic_mass", check_inertial(0, [0, 0, 0], np.zeros((3, 3)))
        )
        self.assertIn(
            "massless_frame_has_inertia",
            check_inertial(0, [0, 0, 0], np.eye(3), massless_frame=True),
        )

    def test_static_properties_do_not_require_positive_dynamic_mass(self):
        self.assertEqual(check_inertial(0, [0, 0, 0], np.eye(3), static=True), [])

    def test_asymmetry_not_silently_symmetrized(self):
        inertia = np.eye(3)
        inertia[0, 1] = 0.2
        before = inertia.copy()
        self.assertIn("asymmetric_inertia", check_inertial(1, [0, 0, 0], inertia))
        np.testing.assert_array_equal(inertia, before)

    def test_negative_eigenvalue_and_triangle_violation(self):
        self.assertIn(
            "negative_inertia_eigenvalue",
            check_inertial(1, [0, 0, 0], np.diag([-1, 1, 1])),
        )
        self.assertIn(
            "inertia_triangle_inequality",
            check_inertial(1, [0, 0, 0], np.diag([1, 1, 3])),
        )

    def test_nonfinite_and_malformed_fields(self):
        for mass, com, inertia in (
            (np.nan, [0, 0, 0], np.eye(3)),
            (1, [np.inf, 0, 0], np.eye(3)),
            (1, [0, 0, 0], np.eye(3) * np.nan),
        ):
            self.assertIn("non_finite_inertial", check_inertial(mass, com, inertia))
        self.assertIn("invalid_inertial_shape", check_inertial(1, [0, 0], np.eye(3)))

    def test_joint_axis_limits_and_nonfinite(self):
        self.assertEqual(check_joint([0, 0, 1], [-1, 1]), [])
        self.assertIn("non_unit_joint_axis", check_joint([0, 0, 0], [-1, 1]))
        self.assertIn("reversed_joint_limits", check_joint([0, 0, 1], [1, -1]))
        self.assertIn("non_finite_joint", check_joint([0, np.inf, 1], [-1, 1]))

    def test_partial_source_and_missing_runtime_are_not_success(self):
        report = report_fixture()
        report["bodies"][0]["source"].update(mass=-1, com=None)
        report["bodies"][0]["effective"]["inertia"] = None
        codes = {row["code"] for row in findings(report)}
        self.assertIn("non_positive_dynamic_mass", codes)
        self.assertIn("missing_effective_inertial", codes)

    def test_invalid_gains_and_contact_values_remain_visible_in_json(self):
        report = report_fixture()
        report["drives"] = [{"joint": "j", "stiffness": -1, "damping": 0}]
        report["bodies"][0]["collision"] = {"friction": float("nan")}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            write_report(report, path)
            saved = json.loads(
                path.read_text(),
                parse_constant=lambda _: self.fail("Invalid JSON number"),
            )
        self.assertEqual(saved["bodies"][0]["collision"]["friction"], "nan")
        self.assertGreater(saved["errors"], 0)
        self.assertLess(report["drives"][0]["stiffness"], 0)

    def test_partial_source_still_checks_given_inertia(self):
        report = report_fixture()
        report["bodies"][0]["source"].update(mass=None, inertia=np.diag([1, 1, 3]))
        self.assertIn(
            "inertia_triangle_inequality", {row["code"] for row in findings(report)}
        )


class MuJoCoAuditTests(unittest.TestCase):
    def test_overlap_filters_overrides_and_read_only_state(self):
        model = mujoco.MjModel.from_xml_string("""
        <mujoco><worldbody>
          <geom name="floor" type="plane" size="1 1 .1"/>
          <body name="body" pos="0 0 .05">
            <joint name="j" type="hinge" axis="0 0 1" range="-30 30"/>
            <geom name="ball" type="sphere" size=".1" mass="1"/>
          </body>
        </worldbody><actuator><position name="drive" joint="j" kp="3" kv=".1"/></actuator></mujoco>""")
        data = mujoco.MjData(model)
        data.qpos[:] = 0.1
        data.qvel[:] = 0.2
        data.ctrl[:] = 0.3
        data.time = 5
        before = [
            array.copy()
            for array in (
                model.body_mass,
                model.body_inertia,
                model.geom_contype,
                model.actuator_gainprm,
                data.qpos,
                data.qvel,
                data.ctrl,
            )
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "model-audit.superdex.json").write_text(
                json.dumps(report_fixture())
            )
            report = record_mujoco(model, data, path)
            self.assertEqual(report["errors"], 0)
            self.assertLess(
                report["initial_overlaps"]["pairs"][0]["minimum_distance_m"], 0
            )
            self.assertEqual(report["drives"][0]["stiffness"], 3)
            self.assertEqual(report["collision_filters"]["geometries"][0]["contype"], 1)
            self.assertEqual(
                report["bodies"][0]["source"]["inertia"], np.eye(3).tolist()
            )
            self.assertNotEqual(
                report["bodies"][0]["effective"]["inertia"], np.eye(3).tolist()
            )
            for actual, expected in zip(
                (
                    model.body_mass,
                    model.body_inertia,
                    model.geom_contype,
                    model.actuator_gainprm,
                    data.qpos,
                    data.qvel,
                    data.ctrl,
                ),
                before,
            ):
                np.testing.assert_array_equal(actual, expected)
            self.assertEqual(data.time, 5)
            model.geom_contype[:] = 0
            model.geom_conaffinity[:] = 0
            filtered = record_mujoco(model, data, path)
            self.assertEqual(filtered["initial_overlaps"]["pairs"], [])


class SuperDexAuditTests(unittest.TestCase):
    def test_native_overlap_sampling_and_static_properties_are_read_only(self):
        import trimesh
        from physics_utils import create_mesh_actor, physics

        from dexlab.model_audit import _properties

        physics.initialize(num_worker_threads=1)
        scene = physics.create_scene("audit test")
        try:
            mesh = trimesh.creation.box(extents=[0.2] * 3)
            fixed = create_mesh_actor(
                scene, mesh, "fixed", [0, 0, 0], static=True, box=True
            )
            moving = create_mesh_actor(scene, mesh, "moving", [0.05] * 3, box=True)
            far = create_mesh_actor(scene, mesh, "far", [10, 0, 0], box=True)
            before = np.asarray(moving.get_root_transform().translation).copy()
            self.assertEqual(
                _properties(fixed), {"mass": 0.0, "com": None, "inertia": None}
            )
            report = sample_initial_overlaps(
                [("fixed", fixed), ("moving", moving), ("far", far)], scene, set()
            )
            self.assertEqual(report["aabb_candidates"], 1)
            self.assertEqual(len(report["pairs"]), 1)
            self.assertLess(report["pairs"][0]["minimum_distance_m"], 0)
            np.testing.assert_array_equal(
                moving.get_root_transform().translation, before
            )
            np.testing.assert_array_equal(moving.get_linear_velocity(), [0, 0, 0])
        finally:
            physics.destroy_scene(scene)
            physics.shutdown()


if __name__ == "__main__":
    unittest.main()
