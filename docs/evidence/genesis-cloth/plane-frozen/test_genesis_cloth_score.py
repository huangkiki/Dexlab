"""Synthetic scorer tests are not native-engine evidence."""
import copy
import unittest
import numpy as np
from dexlab.genesis_cloth_score import score


def fixture():
    vertices = np.array([[-.02,-.02,0],[.02,-.02,0],[.02,.02,0],[-.02,.02,0]])
    record = {'completed': True, 'versions': {'genesis-world': '1.4.3'},
              'protocol': {'dt_s': .002, 'steps': 150, 'repeats': 2, 'diameter_m': .008,
                           'area_density_kg_m2': .2, 'initial_height_m': .02,
                           'initial_vx_m_s': .2, 'gravity_m_s2': [0,0,-9.81]}, 'scenes': []}
    for name, mu, coupled in [('low',.01,True),('high',.5,True),('disabled',.01,False)]:
        rows=[]
        for step in range(151):
            z=.02-9.81*.002**2*step*(step+1)/2
            supported=coupled and z<.004
            p=vertices.copy(); p[:,0]+=.2*.002*step; p[:,2]=.004 if supported else z
            v=np.tile([.2,0,0 if supported else -9.81*.002*step],(4,1))
            rows.append({'step':step,'pos':p.tolist(),'vel':v.tolist()})
        record['scenes'].append({'name':name,'mu':mu,'coupled':coupled,
            'native':{'particle_count':4,'particle_mass_kg':[.00008]*4,
                      'mesh_vertices':vertices.tolist(),'mesh_faces':[[0,1,2],[0,2,3]],
                      'particle_diameter_m':.008},
            'episodes':[{'repeat':i,'rows':copy.deepcopy(rows)} for i in range(2)]})
    return record


class ClothScoreTests(unittest.TestCase):
    def test_supported_and_freefall_controls(self):
        self.assertTrue(score(fixture())['passed'])

    def test_invalid_records_fail_closed(self):
        for value in [None, [], {}, {'completed':False}]:
            with self.subTest(value=value):
                self.assertFalse(score(value)['valid'])

    def test_missing_frame_and_nonfinite_and_bad_geometry(self):
        for defect in ['frame','nan','mass','geometry']:
            r=fixture(); scene=r['scenes'][0]
            if defect=='frame': scene['episodes'][0]['rows'].pop()
            if defect=='nan': scene['episodes'][0]['rows'][50]['pos'][0][0]=float('nan')
            if defect=='mass': scene['native']['particle_mass_kg'][0]=0
            if defect=='geometry': scene['native']['mesh_vertices'][0][0]=-.2
            with self.subTest(defect=defect): self.assertFalse(score(r)['valid'])

    def test_penetration_fails_even_if_final_support_recovers(self):
        r=fixture(); r['scenes'][0]['episodes'][0]['rows'][80]['pos'][0][2]=-.001
        self.assertFalse(score(r)['passed'])

    def test_disabled_coupling_must_fall(self):
        r=fixture(); r['scenes'][2]['episodes']=copy.deepcopy(r['scenes'][0]['episodes'])
        self.assertFalse(score(r)['passed'])

    def test_reset_drift_fails(self):
        r=fixture(); r['scenes'][0]['episodes'][1]['rows'][80]['pos'][0][0]+=.001
        self.assertFalse(score(r)['passed'])

    def test_friction_difference_is_reported_not_required(self):
        r=fixture()
        for episode in r['scenes'][1]['episodes']:
            for row in episode['rows'][1:]:
                for p in row['pos']: p[0]+=.001
        result=score(r)
        self.assertTrue(result['passed'])
        self.assertGreater(result['high_low_max_position_difference_m'],0)
