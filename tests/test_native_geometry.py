"""Reject incomplete or incorrectly framed native geometry evidence."""
import copy
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from dexlab.contact_transfer import native_box_observation_matches


class NativeGeometryTests(unittest.TestCase):
    def setUp(self):
        mesh = trimesh.creation.box(extents=[.04]*3)
        local = .02*np.array([[0,0,0],[1,0,0],[-1,0,0],[0,1,0],
                             [0,0,-1],[1.5,0,0],[1.5,1.5,0]])
        rotation = Rotation.from_euler('xyz', [.2,-.3,.7])
        quat = rotation.as_quat()
        self.record = dict(box_collider='BOX', plane_collider='PLANE', nodes_per_element=3,
            vertices=mesh.vertices.tolist(), faces=mesh.faces.tolist(),
            pose=[.1,.2,.3,quat[3],*quat[:3]], local_points=local.tolist(),
            world_points=(rotation.apply(local)+[.1,.2,.3]).tolist(),
            distances=[-.02,0,0,0,0,.01,np.sqrt(2)*.01],
            aabb_min=[-.02]*3, aabb_max=[.02]*3)

    def test_rotated_translated_box_and_quaternion_sign(self):
        self.assertTrue(native_box_observation_matches(self.record,.02))
        self.record['pose'][3:]=[-x for x in self.record['pose'][3:]]
        self.assertTrue(native_box_observation_matches(self.record,.02))

    def test_missing_fields_rejected(self):
        for key in self.record:
            item=copy.deepcopy(self.record); del item[key]
            with self.subTest(key=key):
                self.assertFalse(native_box_observation_matches(item,.02))

    def test_wrong_frame_scale_collider_and_signed_distance_rejected(self):
        for key,value in [('world_points',self.record['local_points']),
                          ('box_collider','SDF'),('aabb_max',[.04]*3),
                          ('distances',[.02,0,0,0,0,.01,np.sqrt(2)*.01]),
                          ('local_points',[[0,0,0]]*7),('pose',[0]*7),
                          ('distances',[float('nan')]*7)]:
            item=copy.deepcopy(self.record);item[key]=value
            with self.subTest(key=key):
                self.assertFalse(native_box_observation_matches(item,.02))
        self.assertFalse(native_box_observation_matches(self.record,.03))
