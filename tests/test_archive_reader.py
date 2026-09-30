import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mujoco
import numpy as np

SPEC = importlib.util.spec_from_file_location(
    'archive_run', Path(__file__).resolve().parents[1] / 'scripts/archive_run.py')
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


class ArchiveReaderTests(unittest.TestCase):
    def test_native_joint_states_are_distinct_from_display_poses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = mujoco.MjModel.from_xml_string(
                '<mujoco><worldbody><body><freejoint/><geom size=".1"/></body></worldbody></mujoco>')
            mujoco.mj_saveModel(model, str(root / 'model.mjb'))
            (root / 'engine.json').write_text(json.dumps({'backend': 'mujoco', 'completed': True}))
            np.savez(root / 'sdf-dynamics.npz', qpos=[[0, 0, 1, 1, 0, 0, 0]])
            np.savez(root / 'trajectory.npz', frames=np.zeros((2, 1, 7)))
            with patch('verify_sdf_grasp.verify_grasp', return_value={'passed': False}):
                result = archive.read_apple(root)
                self.assertTrue(result['readable'])
                self.assertFalse(result['scientific_acceptance'])
                self.assertEqual(result['model_kind'], 'native_mujoco_model')
                np.savez(root / 'sdf-dynamics.npz', qpos=[[float('nan')] * 7])
                with self.assertRaisesRegex(ValueError, 'native joint states'):
                    archive.read_apple(root)

    def test_superdex_display_proxy_and_frame_shape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'engine.json').write_text(json.dumps({'backend': 'superdex', 'completed': True}))
            (root / 'display.xml').write_text(
                '<mujoco><worldbody><body mocap="true"><geom size=".1"/></body></worldbody></mujoco>')
            np.savez(root / 'trajectory.npz', frames=[[[0, 0, 1, 0, 0, 0, 1]]])
            with patch('verify_sdf_grasp.verify_grasp', return_value={'passed': True}):
                result = archive.read_apple(root)
                self.assertEqual(result['model_kind'], 'visual_mocap_proxy_not_superdex_checkpoint')
                np.savez(root / 'trajectory.npz', frames=np.zeros((1, 2, 7)))
                with self.assertRaisesRegex(ValueError, 'do not match'):
                    archive.read_apple(root)

    def test_incomplete_episodes_are_not_sealed_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'engine.json').write_text('{"backend":"mujoco","completed":false}')
            with self.assertRaisesRegex(ValueError, 'sealed complete'):
                archive.read_apple(root)

    def test_repository_mesh_is_hash_checked_and_relocated_only_in_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root / 'demos/apple-stem-grasp/assets'
            assets.mkdir(parents=True)
            mesh = assets / 'small.obj'
            mesh.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n'
                            'f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n')
            (assets.parent / 'assets.json').write_text(json.dumps({
                'archives': [], 'files': [], 'repository_files': {
                    'small.obj': hashlib.sha256(mesh.read_bytes()).hexdigest()}}))
            xml = ('<mujoco><asset><mesh name="shape" file="/old/assets/small.obj"/></asset>'
                   '<worldbody><body mocap="true"><geom type="mesh" mesh="shape"/></body>'
                   '</worldbody></mujoco>')
            (root / 'display.xml').write_text(xml)
            (root / 'engine.json').write_text('{"backend":"superdex","completed":true}')
            np.savez(root / 'trajectory.npz', frames=[[[0, 0, 1, 0, 0, 0, 1]]])
            with patch.object(archive, 'ROOT', root), patch('verify_sdf_grasp.verify_grasp', return_value={'passed': True}):
                self.assertTrue(archive.read_apple(root)['readable'])
                self.assertEqual((root / 'display.xml').read_text(), xml)
                mesh.write_text(mesh.read_text() + '# changed\n')
                with self.assertRaisesRegex(ValueError, 'differs from its manifest'):
                    archive.read_apple(root)

    def test_relative_names_cannot_escape_root(self):
        for name in ('', '.', '../elsewhere', '/absolute', 'a/../b', 'a//b', 'a\\b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive.relative(name)
        self.assertEqual(str(archive.relative('runs/complete')), 'runs/complete')
