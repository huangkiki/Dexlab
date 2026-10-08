"""Engine-free elastic-impact references, integrity checks and numerical scoring."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np


def elastic_velocities(masses, initial):
    m1, m2 = masses
    u1, u2 = initial
    if min(masses) <= 0 or u1 <= u2:
        raise ValueError('Require positive masses and approaching initial velocities')
    momentum = m1*u1 + m2*u2
    relative = u1-u2
    return np.array([(momentum-m2*relative)/(m1+m2),
                     (momentum+m1*relative)/(m1+m2)])


def score(protocol, case, trace):
    h = case['timestep']
    n = round(protocol['duration_s']/h)
    shapes = dict(states=(n+1,2,13), times=(n+1,), forces=(n,2,3),
                  force_times=(n,), contact_count=(n,), contact_distance=(n,))
    for name, shape in shapes.items():
        if name not in trace or np.asarray(trace[name]).shape != shape or not np.isfinite(trace[name]).all():
            raise ValueError(f'Missing, malformed or nonfinite {name}')
    w = np.asarray(trace.get('warnings', []))
    if w.ndim != 2 or w.shape[0] != n or w.shape[1] == 0 or not np.isfinite(w).all() or np.any(w):
        raise ValueError('Missing or nonzero native warnings')
    s = np.asarray(trace['states']); t = np.asarray(trace['times'])
    f = np.asarray(trace['forces']); count = np.asarray(trace['contact_count'])
    if not np.allclose(t,np.arange(n+1)*h,atol=1e-10,rtol=0) or not np.allclose(trace['force_times'],t[:-1],atol=1e-10,rtol=0):
        raise ValueError('Incorrect time/force epoch')
    initial = np.zeros((2,13));initial[:,0] = case.get('initial_x_m', protocol['initial_x_m'])
    initial[:,3] = 1;initial[:,7] = case['initial_vx_m_s']
    if not np.allclose(s[0],initial,atol=1e-12,rtol=0):
        raise ValueError('Incorrect initial state')
    if not np.allclose(np.linalg.norm(s[:,:,3:7],axis=2),1,atol=1e-10,rtol=0):
        raise ValueError('Nonunit orientation')
    if not np.allclose(np.diff(s[:,:,:3],axis=0),s[1:,:,7:10]*h,atol=1e-10,rtol=0):
        raise ValueError('Position/velocity inconsistency or state injection')
    masses = np.asarray(case['masses_kg'])
    residual = np.diff(s[:,:,7:10],axis=0)*masses[None,:,None] - f*h
    impulse_error = float(np.max(np.abs(residual)))
    if impulse_error > 1e-9 or not np.allclose(f.sum(axis=1),0,atol=1e-10,rtol=0):
        raise ValueError('Force/impulse inconsistency or state injection')
    if np.any((count!=0)&(count!=1)) or not np.any(count):
        raise ValueError('Missing collision or unexpected contact count')
    if np.any(f[count==0]):
        raise ValueError('Force without contact')
    window = t >= protocol['duration_s']-protocol['score_window_s']-1e-10
    force_window = t[:-1] >= protocol['duration_s']-protocol['score_window_s']-1e-10
    gap = np.linalg.norm(s[:,1,:3]-s[:,0,:3],axis=1)-2*protocol['radius_m']
    if np.any(count[force_window]) or not np.all(gap[window]>0) or not np.all(s[window,1,7]>s[window,0,7]):
        raise ValueError('Scoring window is not separated and receding')
    reference = elastic_velocities(masses,case['initial_vx_m_s'])
    velocity = s[:,:,7:10]
    momentum = (velocity*masses[None,:,None]).sum(axis=1)
    energy = .5*(masses[None,:]*np.square(velocity).sum(axis=2)).sum(axis=1)
    inertia = .4*masses*protocol['radius_m']**2
    energy += .5*(inertia[None,:]*np.square(s[:,:,10:13]).sum(axis=2)).sum(axis=1)
    energy_error = float(np.max(np.abs(energy[window]-energy[0])))
    metrics = dict(velocity_error_m_s=float(np.max(np.abs(s[window,:,7]-reference))),
                   relative_energy_error=energy_error/float(energy[0]),
                   momentum_error_kg_m_s=float(np.max(np.linalg.norm(momentum-momentum[0],axis=1))),
                   transverse_speed_m_s=float(np.max(np.linalg.norm(s[:,:,8:10],axis=2))),
                   spin_speed_rad_s=float(np.max(np.linalg.norm(s[:,:,10:13],axis=2))))
    checks = {k:metrics[k]<=v for k,v in protocol['limits'].items()}
    restitution = (s[window,1,7]-s[window,0,7])/(case['initial_vx_m_s'][0]-case['initial_vx_m_s'][1])
    return dict(metrics=metrics,checks=checks,passed=all(checks.values()),
                reference_velocity_m_s=reference.tolist(),measured_velocity_m_s=s[window,:,7].mean(axis=0).tolist(),
                energy_error_j=energy_error,restitution_error=float(np.max(np.abs(restitution-1))),
                penetration_m=float(max(0,-np.min(gap))),impulse_residual_ns=impulse_error)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_readback(p,c,r):
    expected=dict(nq=14,nv=12,nu=0,neq=0,timestep=c['timestep'],integrator=0,
                  solver=2,iterations=100,tolerance=1e-12)
    if any(r[k]!=v for k,v in expected.items()):
        raise ValueError('Native solver/DOF mismatch')
    d=p['impedance'];m=np.asarray(c['masses_kg'])
    stiffness = c.get('stiffness_s2', p['stiffness_s2'])
    arrays=dict(gravity=[0,0,0],mass=[0,*m],inertia=[[0,0,0],*[([.4*x*p['radius_m']**2]*3) for x in m]],
                condim=[1,1],solref=[[-stiffness,0]]*2,
                solimp=[[d,d,.001,.5,2]]*2,size=[[p['radius_m'],0,0]]*2,
                friction=[[0,0,0]]*2,margin=[0,0],gap=[0,0],damping=[0]*12,armature=[0]*12)
    for name,value in arrays.items():
        actual=np.asarray(r[name]);target=np.asarray(value)
        if actual.shape!=target.shape or not np.allclose(actual,target,atol=1e-12,rtol=0):
            raise ValueError(f'Native {name} mismatch')


def score_campaign(root):
    start=time.perf_counter()
    p=json.loads((root/'manifest.json').read_text());campaign=json.loads((root/'campaign.json').read_text())
    cases=p['cases']
    if campaign['manifest_sha256']!=file_hash(root/'manifest.json') or campaign['completed_cases']!=len(cases) or len({c['id'] for c in cases})!=len(cases):
        raise ValueError('Manifest binding or completion mismatch')
    if campaign['runtime']['version']!=p['version'] or not campaign['runtime']['record_verified']:
        raise ValueError('Runtime identity mismatch')
    results=[]
    for c in cases:
        directory=root/c['id'];meta=json.loads((directory/'metadata.json').read_text())
        if meta['case']!=c or meta['state_writes_after_initialization']!=0 or meta['force_epoch']!='times[i]; states[i+1] is postintegration':
            raise ValueError('Case/epoch mismatch or state injection')
        for name,key in [('trace.npz','trace_sha256'),('model.xml','xml_sha256')]:
            if file_hash(directory/name)!=meta[key]:raise ValueError('Artifact hash mismatch')
        verify_readback(p,c,meta['readback'])
        with np.load(directory/'trace.npz',allow_pickle=False) as z:
            result=score(p,c,dict(z))
        results.append(dict(id=c['id'],**result,trace_sha256=meta['trace_sha256'],
                            xml_sha256=meta['xml_sha256'],timing={k:meta[k] for k in
                            ['setup_s','native_step_s','observation_s','total_case_wall_s']}))
    return dict(protocol=p,campaign=campaign,results=results,passed_cases=sum(r['passed'] for r in results),
                scorer_sha256=file_hash(Path(__file__)),scoring_wall_s=time.perf_counter()-start)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=score_campaign(args.input)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')


if __name__=='__main__':
    main()
