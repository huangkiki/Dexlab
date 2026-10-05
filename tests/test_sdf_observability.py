import copy
import json
import tempfile
from pathlib import Path
from dexlab.physx_baseline import digest
from dexlab.sdf_observability import verify_directory
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from dexlab.sdf_observability import summarize, reference_points, HALF_SIZE, TRANSLATION, ANGLE


class SdfObservabilityTests(unittest.TestCase):
    def setUp(self):
        local=reference_points(); rotation=Rotation.from_euler('z',ANGLE)
        distance=(np.abs(local)-HALF_SIZE).max(axis=1)
        self.queries={'local':local,'world':rotation.apply(local)+TRANSLATION,
                      'automatic':distance,'precomputed':distance+1e-4}
        import trimesh
        mesh = trimesh.creation.box(extents=2*HALF_SIZE)
        self.grid={'dims':np.array([27,22,17]),'values':np.zeros(10098),
                   'vertices':np.asarray(mesh.vertices), 'faces':np.asarray(mesh.faces)}
        self.meta={'actual_colliders':['SDF','SDF'],'time_s':0,'requested_spacing_m':[.002]*3,
                   'actual_poses':[[*TRANSLATION,*rotation.as_quat()]]*2,
                   'grid':{'dims':[27,22,17], 'values_shape':[10098],
                           'bounds_min':[-.025,-.020,-.015], 'bounds_max':[.025,.020,.015]}}

    def test_negative_equivalence_is_valid_evidence_not_accuracy_pass(self):
        result=summarize(self.meta,self.grid,self.queries)
        self.assertTrue(result['evidence_complete'])
        self.assertFalse(result['sampled_paths_exactly_equal'])
        self.assertAlmostEqual(result['maximum_pair_difference_m'],1e-4)

    def test_missing_probes_wrong_frame_and_nonfinite_distance_rejected(self):
        for field,value in [('local',self.queries['local'][:-1]),('world',self.queries['local']),
                            ('automatic',np.full(729,np.nan))]:
            q=copy.deepcopy(self.queries);q[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):summarize(self.meta,self.grid,q)

    def test_wrong_actual_pose_collider_and_corrupt_grid_rejected(self):
        for field,value in [('actual_colliders',['BOX','SDF']),('actual_poses',[]),
                            ('actual_poses',[[0]*7]*2),('time_s',.001),('requested_spacing_m',[.001]*3)]:
            m=copy.deepcopy(self.meta);m[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):summarize(m,self.grid,self.queries)
        with self.assertRaises(ValueError):summarize(self.meta,{'dims':np.array([2,2,3]),'values':np.zeros(8)},self.queries)

    def test_grid_declaration_and_input_geometry_are_checked(self):
        for key, value in [('dims', [27, 22, 18]), ('bounds_min', [0, 0, 0]),
                           ('bounds_max', [.25, .2, .15]), ('values_shape', [1])]:
            metadata = copy.deepcopy(self.meta)
            metadata['grid'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                summarize(metadata, self.grid, self.queries)
        for key in ('vertices', 'faces'):
            grid = copy.deepcopy(self.grid)
            del grid[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                summarize(self.meta, grid, self.queries)

    def test_offline_integrity_and_summary_are_independently_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'source').mkdir(); (root/'source/probe.py').write_text('# frozen fixture')
            metadata=copy.deepcopy(self.meta)
            metadata.update(source_sha256={'probe.py':digest(root/'source/probe.py')},source_unchanged=True,
                            independent_summary=summarize(self.meta,self.grid,self.queries))
            np.savez(root/'baked-grid.npz',**self.grid);np.savez(root/'queries.npz',**self.queries)
            def write_receipt():
                (root/'comparison.json').write_text(json.dumps(metadata))
                manifest={n:digest(root/n) for n in ['baked-grid.npz','queries.npz','comparison.json','source/probe.py']}
                (root/'manifest.json').write_text(json.dumps(manifest))
            write_receipt()
            self.assertFalse(verify_directory(root)['sampled_paths_exactly_equal'])
            metadata['independent_summary']['maximum_pair_difference_m']=0
            write_receipt()
            with self.assertRaises(ValueError):verify_directory(root)
            metadata['independent_summary']=summarize(self.meta,self.grid,self.queries)
            write_receipt();(root/'source/probe.py').write_text('# changed')
            with self.assertRaises(ValueError):verify_directory(root)
            metadata['source_sha256']={'/etc/passwd':'not-read'};write_receipt()
            with self.assertRaises(ValueError):verify_directory(root)
