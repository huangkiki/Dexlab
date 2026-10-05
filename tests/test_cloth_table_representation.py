"""Verify the production table option preserves geometry and cloth parameters."""
from itertools import product
from pathlib import Path
import sys
import tempfile
import unittest

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demos/cloth-folding/src'))
from cloth_model import build_model


class TableRepresentationTests(unittest.TestCase):
    def test_compiled_cuboids_match_and_cloth_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            robot = root / 'empty-robot.xml'
            robot.write_text('<mujoco><compiler/><option/><default><geom/></default>'
                             '<asset/><worldbody/><actuator/></mujoco>')
            box, *_ = build_model(robot, root / 'box')
            mesh, *_ = build_model(robot, root / 'mesh', table_contact='convex-mesh')
            a, b = mujoco.MjData(box), mujoco.MjData(mesh)
            mujoco.mj_fwdPosition(box, a)
            mujoco.mj_fwdPosition(mesh, b)
            for field in ('nq', 'nv', 'nbody', 'ngeom'):
                self.assertEqual(getattr(box, field), getattr(mesh, field), field)
            for field in ('flex_elem', 'flexedge_length0', 'flex_radius', 'flex_vertbodyid'):
                np.testing.assert_array_equal(getattr(box, field), getattr(mesh, field))
            np.testing.assert_array_equal(box.body_mass[box.flex_vertbodyid],
                                          mesh.body_mass[mesh.flex_vertbodyid])
            np.testing.assert_array_equal(a.flexvert_xpos, b.flexvert_xpos)
            corners = np.array(list(product((-1, 1), repeat=3)))
            table_ids = [g for g in range(box.ngeom)
                         if (box.geom(g).name or '').startswith('table_')]
            self.assertEqual(len(table_ids), 96)
            for g in table_ids:
                self.assertEqual(box.geom_type[g], mujoco.mjtGeom.mjGEOM_BOX)
                self.assertEqual(mesh.geom_type[g], mujoco.mjtGeom.mjGEOM_MESH)
                mid = mesh.geom_dataid[g]
                start, count = mesh.mesh_vertadr[mid], mesh.mesh_vertnum[mid]
                self.assertEqual(count, 8)
                actual = mesh.mesh_vert[start:start+count] @ b.geom_xmat[g].reshape(3, 3).T + b.geom_xpos[g]
                expected = corners * box.geom_size[g] + a.geom_xpos[g]
                distances = np.linalg.norm(actual[:, None] - expected[None, :], axis=2)
                self.assertLess(float(distances.min(axis=0).max()), 1e-8)
                self.assertLess(float(distances.min(axis=1).max()), 1e-8)
                for field in ('geom_friction', 'geom_solref', 'geom_solimp'):
                    np.testing.assert_array_equal(getattr(box, field)[g], getattr(mesh, field)[g])


class IndependentCuboidVerificationTests(unittest.TestCase):
    def scene(self, *, offset=.5, angle=0, distorted=False, dynamic=False, maxhullvert=64):
        vertices = np.array(list(product((-.5, .5), repeat=3)))
        if distorted:
            vertices[-1, 0] -= .1
        vertex_text = ' '.join(map(str, vertices.ravel()))
        bodies = ''.join(
            f'<body pos="{sign*offset} 0 0">'
            + ('<freejoint/>' if dynamic else '')
            + f'<geom name="table_{sign}" type="mesh" mesh="cube" euler="0 0 {angle}"/>'
            + '</body>' for sign in (-1, 1))
        model = mujoco.MjModel.from_xml_string(
            f'<mujoco><asset><mesh name="cube" maxhullvert="{maxhullvert}" vertex="{vertex_text}"/></asset>'
            f'<worldbody>{bodies}</worldbody></mujoco>')
        data = mujoco.MjData(model)
        mujoco.mj_kinematics(model, data)
        return model, data

    def test_verified_mesh_solid_detects_inside_face_with_outside_vertices(self):
        from dexlab.cloth_table_audit import verified_table_bounds, triangle_box_depth
        lo, hi, evidence = verified_table_bounds(*self.scene())
        np.testing.assert_allclose(lo, [-1, -.5, -.5], atol=1e-12, rtol=0)
        np.testing.assert_allclose(hi, [1, .5, .5], atol=1e-12, rtol=0)
        self.assertEqual(evidence['verified_cuboid_mesh_count'], 2)
        triangle = np.array([[-2, 0, 0], [2, 0, 0], [0, 2, 0]])
        self.assertAlmostEqual(triangle_box_depth(triangle, lo, hi), .5)
        self.assertEqual(triangle_box_depth(triangle+[0, 0, 2], lo, hi), 0)

    def test_arbitrary_mesh_rotation_moving_table_gap_and_overlap_rejected(self):
        from dexlab.cloth_table_audit import verified_table_bounds
        for arguments in ({'distorted': True}, {'angle': 10}, {'dynamic': True},
                          {'offset': .500001}, {'offset': .499999}, {'maxhullvert': 4}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                verified_table_bounds(*self.scene(**arguments))

    def test_numerical_plane_reconciliation_is_measured_and_bounded(self):
        from dexlab.cloth_table_audit import verified_table_bounds, NUMERICAL_EPS_M
        _, _, evidence = verified_table_bounds(*self.scene(offset=.500000001))
        self.assertGreater(evidence['maximum_tile_plane_snap_m'], 0)
        self.assertLess(evidence['maximum_tile_plane_snap_m'], NUMERICAL_EPS_M)


class GraspClearanceTrajectoryTests(unittest.TestCase):
    def test_retreat_finishes_before_lift_and_preserves_lift_height(self):
        from run_cloth import trajectory
        point = np.array([.25, .395, .485])
        baseline = trajectory(point, 'grasp')
        candidate = trajectory(point, 'grasp', .08)
        np.testing.assert_array_equal(baseline[:, [0, 2]], candidate[:, [0, 2]])
        raised = candidate[candidate[:, 2] > point[2]]
        self.assertTrue(np.allclose(raised[:, 1], point[1]-.08, atol=1e-12, rtol=0))
        self.assertAlmostEqual(candidate[-1, 2]-point[2], .12)
        self.assertAlmostEqual(baseline[-1, 1]-candidate[-1, 1], .02)


if __name__ == '__main__':
    unittest.main()
