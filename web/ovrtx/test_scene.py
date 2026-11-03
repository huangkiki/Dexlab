"""Run with the optional OVRTX environment; these checks do not initialize a GPU."""
from pathlib import Path
import tempfile
import unittest

import numpy as np
import trimesh
from pxr import Usd

from scene import build_scene
from server import validate_request


class BridgeContractTest(unittest.TestCase):
    def test_export_preserves_meshes_and_independent_camera_products(self):
        source = trimesh.Scene()
        source.add_geometry(trimesh.creation.box(), node_name="part_0")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source.export(root / "test.glb")
            self.assertEqual(build_scene(root / "test.glb", root), ["/World/part_0"])
            stage = Usd.Stage.Open(str(root / "scene.usda"))
            for lane, prefix in enumerate(("/World", "/Lane1", "/Lane2")):
                self.assertTrue(stage.GetPrimAtPath(prefix + "/part_0").IsValid())
                product = stage.GetPrimAtPath(f"/Render/Camera{lane}")
                self.assertEqual(str(product.GetRelationship("camera").GetTargets()[0]), prefix + "/Camera")
                self.assertEqual(tuple(product.GetAttribute("resolution").Get()), (640, 480))

    def test_rejects_malformed_pose_frames_before_rendering(self):
        request = dict(worlds=[[np.eye(4).ravel().tolist()]], camera=np.eye(4).ravel().tolist(),
                       width=640, height=480, columns=1, fov=37., time=.1, sequence=1)
        worlds, camera = validate_request(request, 1)
        self.assertEqual(worlds.shape, (1, 1, 4, 4))
        for patch in ({"width": 8192}, {"columns": 3}, {"fov": float("nan")},
                      {"sequence": True}, {"worlds": []}, {"camera": [float("inf")] * 16}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_request({**request, **patch}, 1)


if __name__ == "__main__":
    unittest.main()
