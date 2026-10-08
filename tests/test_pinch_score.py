"""Constructed algebraic traces, explicitly not native physics evidence."""
import copy
import json
from pathlib import Path
import unittest

import numpy as np
from dexlab.pinch_score import score_trace

P = json.loads((Path(__file__).resolve().parents[1]/'docs/evidence/pinch-load/manifest.json').read_text())


def static_trace(c=None):
    c = c or next(c for c in P['cases'] if c['capacity_ratio'] == 2.)
    h = c['timestep']; n = round(P['duration_s']/h); onset = round(P['preload_s']/h)
    state = np.zeros((n+1, 18)); state[:, 0] = np.arange(n+1)*h; state[:, 6] = 1
    weight = P['cube_mass_kg']*P['gravity_m_s2']
    normal = weight*c['capacity_ratio']/(2*P['friction'])*np.minimum(np.arange(n)/round(P['ramp_s']/h),1)
    external = np.zeros((n, 3)); external[onset:,2] = -weight
    forces = np.zeros((n,2,3)); forces[:,0,0] = normal; forces[:,1,0] = -normal
    forces[onset:,:,2] = weight/2
    contacts = np.full((n,16,13),np.nan)
    moments = np.zeros((n,2,3))
    for side, sign in ((0,1),(1,-1)):
        contacts[:,side] = 0
        contacts[:,side,0] = side
        contacts[:,side,1] = -sign*P['side_m']/2
        contacts[:,side,4] = sign
        contacts[:,side,7:10] = forces[:,side]
        contacts[:,side,11:13] = P['friction']
        moments[:,side] = np.cross(contacts[:,side,1:4], forces[:,side])
    actuator = np.zeros((n,8)); actuator[:,:2] = normal[:,None]
    constraint = -actuator; constraint[:,2:5] = forces.sum(axis=1)
    return c, dict(states=state,commands=actuator[:,:2].copy(),external=external,forces=forces,
                   moments=moments,contacts=contacts,counts=np.ones((n,2),int),actuator=actuator,
                   constraint=constraint,force_times=state[:-1,0].copy(),warnings=np.zeros((n,8),int))


class PinchScorerTests(unittest.TestCase):
    def test_algebraic_hold(self):
        c,t = static_trace()
        self.assertTrue(score_trace(P,c,t)['passed'])

    def test_epoch_and_injected_states(self):
        c,t = static_trace()
        for field,index,amount,message in (
            ('force_times',1,c['timestep'],'force epoch'),
            ('states',(20,5),.01,'contact moment mismatch'),
            ('states',(20,14),1,'Impulse mismatch'),
            ('states',(20,15),1,'Impulse mismatch')):
            with self.subTest(field=field,index=index):
                wrong=copy.deepcopy(t);wrong[field][index]+=amount
                with self.assertRaisesRegex(ValueError,message):score_trace(P,c,wrong)

    def test_missing_contact_side(self):
        c,t=static_trace();t['contacts'][:,1]=np.nan
        with self.assertRaisesRegex(ValueError,'count mismatch'):score_trace(P,c,t)

    def test_command_cannot_replace_measured_force(self):
        c,t=static_trace();t['forces'][:,0,2]=t['commands'][:,0]
        with self.assertRaisesRegex(ValueError,'contact force mismatch'):score_trace(P,c,t)

    def test_broken_contact_slots(self):
        c,t=static_trace();t['contacts'][1,0,11]=np.nan
        with self.assertRaisesRegex(ValueError,'Incomplete contact'):score_trace(P,c,t)

    def test_wrong_load_is_not_hidden_by_motion_fit(self):
        c,t=static_trace();t['external'][:,2]=0
        with self.assertRaisesRegex(ValueError,'external load'):score_trace(P,c,t)

    def test_marginal_is_never_robust_pass(self):
        c,t=static_trace();c=copy.deepcopy(c);c['capacity_ratio']=1
        for field in ('commands','actuator'): t[field]*=.5
        t['forces'][:,:,0]*=.5;t['contacts'][:,:2,7]*=.5;t['constraint'][:,:2]*=.5
        result=score_trace(P,c,t)
        self.assertIsNone(result['passed'])
        self.assertEqual(result['status'],'marginal diagnostic')


class PinchProvenanceTests(unittest.TestCase):
    def setUp(self):
        import hashlib
        import tempfile
        import mujoco as mj
        from dexlab.pinch_run import model_xml, compiled_readback
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = Path(__file__).resolve().parents[1]/'docs/evidence/pinch-load'
        self.digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = self.root/'manifest.json'
        manifest.write_bytes((self.evidence/'manifest.json').read_bytes())
        runner = Path(__file__).resolve().parents[1]/'src/dexlab/pinch_run.py'
        campaign = dict(manifest_sha256=self.digest(manifest),runner_sha256=self.digest(runner),
                        completed_cases=18,runtime=dict(version=P['version'],record_verified=True))
        (self.root/'campaign.json').write_text(json.dumps(campaign))
        for c in P['cases']:
            directory=self.root/c['id'];directory.mkdir()
            xml=model_xml(P,c);(directory/'model.xml').write_text(xml)
            _,trace=static_trace(c)
            np.savez_compressed(directory/'trace.npz',**trace)
            meta=dict(case=c,readback=compiled_readback(mj.MjModel.from_xml_string(xml)),
                      cube_body=3,cube_geom=2,jaw_geoms=[0,1],state_writes_after_initialization=0,
                      force_epoch='states[i].time; states[i+1] postintegration',
                      xml_sha256=self.digest(directory/'model.xml'),trace_sha256=self.digest(directory/'trace.npz'),
                      setup_s=0,control_s=0,native_step_s=0,observation_s=0,serialization_s=0,total_case_wall_s=0)
            (directory/'metadata.json').write_text(json.dumps(meta))

    def test_complete_synthetic_matrix(self):
        from dexlab.pinch_score import score_campaign
        result=score_campaign(self.root,self.evidence)
        self.assertEqual((result['passed_cases'],result['failed_cases'],result['diagnostic_cases']),(6,6,6))

    def test_rehashed_manifest_cannot_change_threshold(self):
        from dexlab.pinch_score import score_campaign
        path=self.root/'manifest.json';m=json.loads(path.read_text());m['limits']['static_speed_m_s']=999
        path.write_text(json.dumps(m));campaign=self.root/'campaign.json';m=json.loads(campaign.read_text())
        m['manifest_sha256']=self.digest(path);campaign.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'frozen protocol'):score_campaign(self.root,self.evidence)

    def test_changed_compiled_mass_rejected(self):
        from dexlab.pinch_score import score_campaign
        path=self.root/P['cases'][0]['id']/'metadata.json';m=json.loads(path.read_text())
        m['readback']['body_mass'][3]*=2;path.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'body_mass'):score_campaign(self.root,self.evidence)

    def test_corrupt_archive_and_runner_rejected(self):
        from dexlab.pinch_score import score_campaign
        path=self.root/P['cases'][0]['id']/'trace.npz';path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):score_campaign(self.root,self.evidence)
        path=self.root/'campaign.json';m=json.loads(path.read_text());m['runner_sha256']='0'*64
        path.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'Runner source'):score_campaign(self.root,self.evidence)


    def test_invalid_trace_does_not_hide_remaining_cases(self):
        from dexlab.pinch_score import score_campaign
        directory=self.root/P['cases'][0]['id'];path=directory/'trace.npz'
        with np.load(path) as source: trace={k:source[k] for k in source.files}
        trace['states'][20,14]+=1
        np.savez_compressed(path,**trace)
        meta_path=directory/'metadata.json';meta=json.loads(meta_path.read_text())
        meta['trace_sha256']=self.digest(path);meta_path.write_text(json.dumps(meta))
        result=score_campaign(self.root,self.evidence)
        self.assertEqual(len(result['results']),18)
        self.assertEqual(result['invalid_cases'],1)
        self.assertFalse(result['results'][0]['passed'])
