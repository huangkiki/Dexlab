"""Geometry, force protocol and adversarial native-cylinder evidence checks."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from dexlab.contact_pinch import PAD_HALF, CylinderCase, cylinder_box_overlap, score
from dexlab.contact_pinch_run import normal_components_consistent, run, verify


class CylinderGeometryTests(unittest.TestCase):
    def test_surface_depth_and_finite_pad_separation(self):
        case = CylinderCase()
        body = np.array([0, 0, 0, 1, 0, 0, 0], dtype=float)
        pad = np.array([case.radius + PAD_HALF[0] - 0.0004, 0, 0, 1, 0, 0, 0])
        self.assertAlmostEqual(
            cylinder_box_overlap(body, pad, case)[0], 0.0004, places=12
        )
        pad[0] += 0.001
        self.assertEqual(cylinder_box_overlap(body, pad, case)[0], 0)
        pad[0] -= 0.001
        pad[2] = case.half_height + PAD_HALF[2] + 0.001
        self.assertEqual(cylinder_box_overlap(body, pad, case)[0], 0)

    def test_common_rigid_rotation_preserves_depth(self):
        case = CylinderCase()
        poses = np.array(
            [
                [0, 0, 0, 1, 0, 0, 0],
                [case.radius + PAD_HALF[0] - 0.0004, 0, 0, 1, 0, 0, 0],
            ],
            dtype=float,
        )
        rotation = Rotation.from_rotvec([0.37, -0.21, 0.54])
        q = rotation.as_quat()
        poses[:, :3] = rotation.apply(poses[:, :3]) + [1, 2, 3]
        poses[:, 3:] = [q[3], *q[:3]]
        self.assertAlmostEqual(
            cylinder_box_overlap(poses[0], poses[1], case)[0], 0.0004, places=11
        )

    def test_declared_inertia_matches_the_archived_prism(self):
        import trimesh

        case = CylinderCase()
        mesh = trimesh.creation.cylinder(
            radius=case.radius, height=2 * case.half_height, sections=case.sections
        )
        actual = np.diag(mesh.moment_inertia * case.mass / mesh.mass)
        np.testing.assert_allclose(case.inertia, actual, rtol=1e-12, atol=1e-14)

    def test_surface_refinement_preserves_volume_inertia_and_prism_surface(self):
        from dexlab.contact_pinch_native import geometry

        case = CylinderCase(surface_subdivisions=2)
        with tempfile.TemporaryDirectory() as tmp:
            mesh = geometry(case, Path(tmp))
        self.assertEqual(len(mesh.faces), 4 * case.sections * 4**2)
        self.assertTrue(mesh.is_watertight)
        expected_volume = (
            case.sections
            * case.radius**2
            * np.sin(2 * np.pi / case.sections)
            * case.half_height
        )
        self.assertAlmostEqual(mesh.volume, expected_volume, places=14)
        np.testing.assert_allclose(
            np.diag(mesh.moment_inertia * case.mass / mesh.mass),
            case.inertia,
            rtol=1e-12,
        )
        theta = (np.arange(case.sections) + 0.5) * 2 * np.pi / case.sections
        face_normals = np.c_[np.cos(theta), np.sin(theta)]
        distances = mesh.vertices[:, :2] @ face_normals.T
        side = distances.max(axis=1)
        cap = np.abs(mesh.vertices[:, 2])
        self.assertTrue(
            np.all(
                (np.abs(side - case.radius * np.cos(np.pi / case.sections)) < 1e-12)
                | (np.abs(cap - case.half_height) < 1e-12)
            )
        )

    def test_invalid_quaternion_is_not_silently_normalized(self):
        case = CylinderCase()
        with self.assertRaises(ValueError):
            cylinder_box_overlap([0, 0, 0, 2, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0], case)

    def test_load_ramp_is_held_at_fixed_physical_control_period(self):
        case = CylinderCase(mode="ramp")
        refined = replace(case, timestep=0.00025)
        for step in (0, 599, 600, 1600, 1601, 2600, 3000, 3050, 3100):
            np.testing.assert_array_equal(case.force(step), refined.force(2 * step))
        np.testing.assert_array_equal(case.force(1600), case.force(1601))
        self.assertGreater(case.force(0)[2, 2], 0)
        self.assertEqual(case.force(600)[2, 2], 0)
        self.assertLess(case.force(3000)[0, 0], 0)
        self.assertEqual(case.force(3100)[2, 2], 0)

    def test_inconsistent_negative_controls_are_rejected(self):
        for kw in (
            {"mode": "overload"},
            {"mode": "frictionless"},
            {"sections": 15},
            {"controller_period": 0.0001},
            {"surface_subdivisions": -1},
            {"surface_subdivisions": 1.5},
        ):
            with self.assertRaises(ValueError):
                CylinderCase(**kw)


class CylinderEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "native"
        cls.case = CylinderCase()
        cls.result = run(cls.case, "mujoco", cls.output)
        with np.load(cls.output / "states.npz", allow_pickle=False) as saved:
            cls.data = dict(saved)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def copy_data(self):
        return {k: v.copy() for k, v in self.data.items()}

    def test_actual_native_ledger_release_and_overall_verdict(self):
        self.assertEqual(self.result["passed"], all(self.result["checks"].values()))
        for key in (
            "complete_shapes",
            "momentum_balance",
            "measured_normal_load",
            "fully_released",
            "contact_ledger_matches",
        ):
            self.assertTrue(self.result["checks"][key], key)
        self.assertTrue(self.result["checks"]["native_normal_components_consistent"])
        np.testing.assert_allclose(
            self.result["metrics"]["measured_preload_n"], [4, 4], atol=0.001
        )
        self.assertEqual(verify(self.output), self.result)

    def test_adhesion_after_release_cannot_pass(self):
        data = self.copy_data()
        released = data["time"][1:] > 1.75
        data["contact_force"][released, 0, 2] += 0.5
        data["external_force"][released, 2, 2] -= 0.5
        result = score(self.case, data)
        self.assertTrue(result["checks"]["momentum_balance"])
        self.assertFalse(result["checks"]["fully_released"])
        self.assertFalse(result["checks"]["declared_external_forces"])

    def test_missing_force_data_and_corrupt_time_fail(self):
        data = self.copy_data()
        data["contact_known"][90] = False
        self.assertFalse(score(self.case, data)["passed"])
        data = self.copy_data()
        data["time"][90] = 0
        self.assertFalse(score(self.case, data)["checks"]["uniform_time_grid"])

    def test_independent_geometry_rejects_interpenetration(self):
        data = self.copy_data()
        data["pose"][800, 0, 0] += 0.004
        self.assertFalse(score(self.case, data)["checks"]["bounded_penetration"])

    def test_modified_raw_archive_is_rejected(self):
        path = self.output / "native-status.json"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n")
            self.assertFalse(verify(self.output)["checks"]["artifact_hashes_match"])
        finally:
            path.write_bytes(original)


class ContactNormalTests(unittest.TestCase):
    def test_tangential_component_cannot_be_disguised_as_normal_load(self):
        row = [
            {
                "force": [4, 0, 1],
                "normal_force": [4, 0, 0],
                "normal_direction": [1, 0, 0],
            }
        ]
        self.assertTrue(normal_components_consistent(row, "superdex"))
        row[0]["normal_force"] = [4, 0, 1]
        self.assertFalse(normal_components_consistent(row, "superdex"))
        row[0]["normal_force"] = [8, 0, 0]
        self.assertFalse(normal_components_consistent(row, "mujoco"))

    def test_tensile_or_invalid_native_normal_is_rejected(self):
        row = [
            {
                "force": [-1, 0, 0],
                "normal_force": [-1, 0, 0],
                "normal_direction": [1, 0, 0],
            }
        ]
        self.assertFalse(normal_components_consistent(row, "mujoco"))
        for engine, row in (("physx", {}), ("mujoco", [{}])):
            self.assertFalse(normal_components_consistent(row, engine))

    def test_physx_signed_magnitude_and_independent_friction_anchors(self):
        row = {
            "normal_direction": [[-1, 0, 0]],
            "normal_force": [[4, 0, 0]],
            "normal_magnitude": [-4],
            "friction_point": [[1, 2, 3], [4, 5, 6]],
        }
        self.assertTrue(normal_components_consistent(row, "physx"))
        row["normal_magnitude"] = [-2]
        self.assertFalse(normal_components_consistent(row, "physx"))
