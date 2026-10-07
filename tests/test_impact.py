"""Independent collision algebra and evidence rejection tests (no engine)."""
import copy
import json
from pathlib import Path
import unittest

import numpy as np
from dexlab.impact_score import elastic_velocities, score


class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((Path(__file__).parents[1]/'docs/evidence/elastic-impact/manifest.json').read_text())
        self.case = self.protocol['cases'][0]
        h = self.case['timestep']
        n = round(self.protocol['duration_s']/h)
        states = np.zeros((n+1,2,13))
        states[:,:,3] = 1
        states[:41,0,7] = .5
        states[41:,1,7] = .5
        states[0,:,0] = [-.06,.06]
        for i in range(n):
            states[i+1,:,:3] = states[i,:,:3]+h*states[i+1,:,7:10]
        forces = np.diff(states[:,:,7:10],axis=0)/h
        counts = np.zeros(n,dtype=int)
        counts[40] = 1
        self.trace = dict(states=states,times=np.arange(n+1)*h,force_times=np.arange(n)*h,
                          forces=forces,contact_count=counts,contact_distance=np.zeros(n),
                          warnings=np.zeros((n,1),dtype=int))

    def test_reference_unequal_masses(self):
        np.testing.assert_allclose(elastic_velocities([1,2],[2,0]),[-2/3,4/3])
        np.testing.assert_allclose(elastic_velocities([2,1],[1,-1]),[-1/3,5/3])

    def test_known_elastic_record(self):
        self.assertTrue(score(self.protocol,self.case,self.trace)['passed'])

    def test_reject_corrupted_evidence(self):
        def missing(t): del t['forces']
        def truncated(t): t['states']=t['states'][:-1]
        def nan(t): t['states'][10,0,0]=np.nan
        def injected(t): t['states'][100,0,0]+=.1
        def impulse(t): t['forces'][40,0,0]=0
        def epoch(t): t['force_times']+=.001
        def no_collision(t): t['contact_count'][:]=0
        def warning(t): t['warnings'][10,0]=1
        def initial(t): t['states'][0,0,7]=.6
        for mutate in [missing,truncated,nan,injected,impulse,epoch,no_collision,warning,initial]:
            with self.subTest(mutation=mutate.__name__):
                trace=copy.deepcopy(self.trace)
                mutate(trace)
                with self.assertRaises(ValueError):score(self.protocol,self.case,trace)

    def test_consistent_inelastic_record_is_physics_failure(self):
        # Keep momentum, integration and force records coherent, but lose energy.
        s=self.trace['states'];h=self.case['timestep']
        s[41:,0,7]=.1;s[41:,1,7]=.4
        for i in range(len(s)-1):s[i+1,:,:3]=s[i,:,:3]+h*s[i+1,:,7:10]
        self.trace['forces']=np.diff(s[:,:,7:10],axis=0)/h
        result=score(self.protocol,self.case,self.trace)
        self.assertFalse(result['passed'])
        self.assertTrue(result['checks']['momentum_error_kg_m_s'])
        self.assertFalse(result['checks']['relative_energy_error'])


if __name__=='__main__':
    unittest.main()
