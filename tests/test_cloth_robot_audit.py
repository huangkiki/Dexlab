"""Analytic controls and archive boundaries for independent robot geometry."""

import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mujoco
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

from dexlab.archive_integrity import snapshot
from dexlab.cloth_robot_audit import audit_robot, audit_saved, robot_hulls, triangle_hull_depth
from dexlab.cloth_table_audit import triangle_box_depth

CUBE = np.array(list(itertools.product([-.01, .01], repeat=3)))
FACE = np.array([[-.03, -.03, 0], [.03, -.03, 0], [0, .03, 0]])


def fixture_model(*, mesh_attributes="", geom_type="mesh", extra=""):
    vertices = " ".join(str(x) for x in CUBE.ravel())
    mesh = f'<mesh name="pad" vertex="{vertices}" {mesh_attributes}/>'
    geometry = 'type="mesh" mesh="pad"' if geom_type == "mesh" else 'type="sphere" size=".01"'
    return mujoco.MjModel.from_xml_string(
        f'<mujoco><asset>{mesh}</asset><worldbody>'
        f'<body name="robot"><freejoint/><geom name="collision_pad" {geometry}/></body>'
        '<flexcomp name="cloth" type="direct" dim="2" radius=".0012" '
        'point="-.03 -.03 0 .03 -.03 0 0 .03 0" element="0 1 2">'
        f'<edge equality="true"/></flexcomp>{extra}</worldbody></mujoco>')


class TriangleHullTests(unittest.TestCase):
    def setUp(self):
        self.planes = ConvexHull(CUBE).equations

    def test_triangle_interior_detected_with_all_vertices_outside(self):
        self.assertTrue(np.all(np.max(np.abs(FACE), axis=1) > .01))
        self.assertAlmostEqual(triangle_hull_depth(FACE, self.planes), .01, places=10)

    def test_separation_and_surface_touch(self):
        for height in (.01, .03):
            with self.subTest(height=height):
                self.assertAlmostEqual(triangle_hull_depth(FACE + [0, 0, height], self.planes), 0, places=10)

    def test_rigid_transform_preserves_analytic_depth(self):
        rotation = Rotation.from_euler('xyz', [25, 43, -17], degrees=True).as_matrix()
        offset = np.array([1, 2, 3])
        planes = ConvexHull(CUBE @ rotation.T + offset).equations
        self.assertAlmostEqual(triangle_hull_depth(FACE @ rotation.T + offset, planes), .01, places=9)

    def test_tetrahedron_incenter_has_known_distance(self):
        hull = ConvexHull(np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]))
        radius = 1 / (3 + np.sqrt(3))
        center = np.full(3, radius)
        triangle = center + [[-.1, -.1, 0], [.1, -.1, 0], [0, .1, 0]]
        self.assertAlmostEqual(triangle_hull_depth(triangle, hull.equations), radius, places=10)

    def test_agrees_with_box_reference_on_fixed_random_triangles(self):
        for triangle in np.random.default_rng(3201).uniform(-.03, .03, (20, 3, 3)):
            self.assertAlmostEqual(triangle_hull_depth(triangle, self.planes),
                                   triangle_box_depth(triangle, CUBE.min(0), CUBE.max(0)), delta=1e-9)

    def test_invalid_triangle_or_planes_are_not_zero(self):
        for triangle, planes in [(np.zeros((3, 3)), self.planes),
                                 (FACE * np.nan, self.planes), (FACE, self.planes * 2)]:
            with self.subTest(triangle=triangle), self.assertRaises(ValueError):
                triangle_hull_depth(triangle, planes)


class RobotAuditTests(unittest.TestCase):
    def setUp(self):
        self.model = fixture_model()
        self.triangles = self.model.flex_elem.reshape(-1, 3).copy()

    def test_uses_actual_moving_pose_without_contacts_or_integration(self):
        poses = np.tile(self.model.qpos0, (2, 1))
        poses[1, 0] = .1  # Move the robot, not the cloth.
        with (patch('mujoco.mj_step', side_effect=AssertionError('integration')),
              patch('mujoco.mj_fwdPosition', side_effect=AssertionError('contact pipeline'))):
            report = audit_robot(self.model, [0, .04], poses, self.triangles)
        self.assertEqual(report['frames_with_intrusion'], 1)
        self.assertAlmostEqual(report['rows'][0]['maximum_interior_depth_m'], .01, places=8)
        self.assertEqual(report['rows'][1]['maximum_interior_depth_m'], 0)
        self.assertNotIn('passed', report)

    def test_mesh_compiler_transform_is_applied_once(self):
        # Off-center source geometry with anisotropic scale and geom rotation.
        original = CUBE + [.03, .02, .01]
        raw = ' '.join(map(str, original.ravel()))
        model = mujoco.MjModel.from_xml_string(
            f'<mujoco><asset><mesh name="offset" scale="2 3 4" vertex="{raw}"/>'
            '</asset><worldbody><geom name="collision_pad" type="mesh" mesh="offset" '
            'pos="1 2 3" euler="15 30 45"/></worldbody></mujoco>')
        hull = robot_hulls(model)[0]
        data = mujoco.MjData(model)
        mujoco.mj_kinematics(model, data)
        actual = hull.vertices @ data.geom_xmat[0].reshape(3, 3).T + data.geom_xpos[0]
        rotation = Rotation.from_euler('XYZ', [15, 30, 45], degrees=True).as_matrix()
        expected = (original * [2, 3, 4]) @ rotation.T + [1, 2, 3]
        self.assertLess(np.linalg.norm(actual[:, None] - expected[None, :], axis=2).min(axis=1).max(), 1e-7)

    def test_limited_native_hull_is_not_full_render_hull(self):
        model = fixture_model(mesh_attributes='maxhullvert="4"')
        hull = robot_hulls(model)[0]
        self.assertEqual(len(hull.vertices), 4)
        self.assertGreater(model.mesh_vertnum[0], len(hull.vertices))

    def test_missing_unsupported_or_unclassified_geometry_is_rejected(self):
        models = [mujoco.MjModel.from_xml_string('<mujoco/>'),
                  fixture_model(geom_type='sphere'),
                  fixture_model(extra='<geom name="unknown" type="box" size="1 1 1"/>')]
        for model in models:
            with self.subTest(geoms=model.ngeom), self.assertRaises(ValueError):
                robot_hulls(model)

    def test_corrupt_topology_or_states_are_rejected(self):
        for times, poses, faces in [([], [], self.triangles),
                                   ([0], [self.model.qpos0], self.triangles.astype(float)),
                                   ([0, 0], [self.model.qpos0] * 2, self.triangles),
                                   ([0], [self.model.qpos0 * np.nan], self.triangles)]:
            with self.subTest(times=times), self.assertRaises(ValueError):
                audit_robot(self.model, times, poses, faces)


class RobotArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.record = self.root / 'record'
        self.record.mkdir()
        self.model = fixture_model()
        mujoco.mj_saveModel(self.model, str(self.record / 'model.mjb'))
        self.save_states()
        (self.record / 'summary.json').write_text(json.dumps({'schedule_s': {'duration': .08}}))

    def save_states(self, times=(0, .04)):
        np.savez(self.record / 'states.npz', time_s=times,
                 qpos=np.tile(self.model.qpos0, (len(times), 1)),
                 triangles=self.model.flex_elem.reshape(-1, 3))

    def test_complete_archive_is_read_only_and_hash_bound(self):
        before = snapshot(self.record)
        report = audit_saved(self.record)
        self.assertEqual(report['physics_steps_executed'], 0)
        self.assertEqual(report['saved_frames'], 2)
        self.assertEqual(report['status'], 'sampled_intrusion_detected')
        self.assertEqual(len(report['input_sha256']), 3)
        self.assertEqual(snapshot(self.record), before)

    def test_missing_frame_is_not_reported_as_complete(self):
        self.save_states((0,))
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            audit_saved(self.record)

    def test_mid_audit_mutation_is_rejected(self):
        def mutate(*args):
            path = self.record / 'summary.json'
            path.write_text(path.read_text() + '\n')
            return {}
        with patch('dexlab.cloth_robot_audit.audit_robot', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                audit_saved(self.record)

    def test_cli_protects_record_and_existing_reports(self):
        old = self.root / 'old.json'
        old.write_text('preserved')
        for output in (self.record / 'audit.json', old):
            result = subprocess.run([sys.executable, '-m', 'dexlab.cloth_robot_audit',
                                     str(self.record), '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.record / 'audit.json').exists())
        self.assertEqual(old.read_text(), 'preserved')


if __name__ == '__main__':
    unittest.main()
