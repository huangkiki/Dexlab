import copy
import json
from pathlib import Path
import unittest

import numpy as np
import trimesh

from dexlab.contact_transfer import (box_mesh_matches, geometry_observation,
                                     initial_state_matches, validate_plan)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.case = {'half_size': .02}
        self.mesh = trimesh.creation.box(extents=[.04]*3)

    def test_closed_box_and_missing_internal_geometry_are_distinct(self):
        result = geometry_observation('superdex', self.case, {},
            {'vertices': self.mesh.vertices, 'faces': self.mesh.faces})
        self.assertTrue(result['representation_matches'])
        self.assertIsNone(result['cooked_mesh_equivalence'])
        self.assertIsNone(result['combined_contact_law_readback'])

    def test_open_reversed_duplicate_and_wrong_scale_meshes_fail(self):
        v, f = self.mesh.vertices.copy(), self.mesh.faces.copy()
        for vertices, faces in [(v, f[:-1]), (v, f[:, ::-1]), (v*2, f),
                                (v, np.vstack([f[:-1], f[0]])), (v, f.astype(float))]:
            self.assertFalse(box_mesh_matches(vertices, faces, .02))

    def test_actual_initial_state_and_quaternion_sign(self):
        pose = np.array([0,0,.02,1,0,0,0], dtype=float)
        self.assertTrue(initial_state_matches(self.case, 0, pose, np.zeros(6)))
        pose[3] = -1
        self.assertTrue(initial_state_matches(self.case, 0, pose, np.zeros(6)))
        pose[2] += .001
        self.assertFalse(initial_state_matches(self.case, 0, pose, np.zeros(6)))
        self.assertFalse(initial_state_matches(self.case, 0, np.full(7,np.nan), np.zeros(6)))

    def test_native_box_type_size_and_missing_readback(self):
        native = {'geometry_readback': {'type':[0,6], 'size':[[2,2,.1],[.02]*3]}}
        self.assertTrue(geometry_observation('mujoco',self.case,native)['representation_matches'])
        native['geometry_readback']['type'][1] = 7
        self.assertFalse(geometry_observation('mujoco',self.case,native)['representation_matches'])
        self.assertFalse(geometry_observation('mujoco',self.case,{})['representation_matches'])

    def test_frozen_pairs_reject_missing_case_retuning_and_changed_mass(self):
        plan = json.loads((Path(__file__).resolve().parents[1]/'benchmarks/contact-transfer-v1.json').read_text())
        self.assertTrue(validate_plan(plan))
        for change in ('missing','retune','retune-all','mass','engine'):
            modified=copy.deepcopy(plan)
            if change=='missing': modified['jobs'].pop()
            if change=='retune': modified['jobs'][-1]['normal_parameters']={}
            if change=='retune-all':
                for job in modified['jobs']:
                    if job['profile_id']=='mujoco-imp09-500us':
                        job['normal_parameters']['solref'][0]=-999
            if change=='mass': modified['jobs'][0]['case']['mass']+=.001
            if change=='engine': modified['jobs'][0]['engine']='superdex'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_plan(modified)
