from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
parser=argparse.ArgumentParser(description='Plot immutable pinch traces; rejected records remain diagnostic only')
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
batch=args.input;root=args.output
root.mkdir(parents=True,exist_ok=False)
p=json.loads((batch/'manifest.json').read_text())
fig,axes=plt.subplots(2,3,figsize=(12,7),sharex=True)
rows=[]
for c in p['cases']:
 with np.load(batch/c['id']/'trace.npz') as t:
  h=c['timestep'];state=t['states'];onset=round(.5/h)
  masses=np.array([.1,.1]+[.064]*3+[.064*.04**2/6]*3)
  net=t['constraint']+t['actuator'];net[:,2:5]+=t['external']
  residual=np.diff(state[:,10:18],axis=0)*masses-net*h
  linear=float(np.abs(residual[:,:5]).max());angular=float(np.abs(residual[:,5:]).max())
  peak=np.unravel_index(np.abs(residual[:,:5]).argmax(),residual[:,:5].shape)
  normal=t['forces'][:,:,0]*[1,-1]
  cmd=c['capacity_ratio']*.064*9.81
  rows.append(dict(id=c['id'],linear_impulse_peak_ns=linear,angular_impulse_peak_nms=angular,
   linear_peak_epoch_s=float(state[peak[0],0]),linear_peak_dof=int(peak[1]),
   linear_peak_force_equivalent_n=linear/h,
   linear_rejected=linear>p['limits']['impulse_residual_n_s'],
   force_source='recorded native generalized constraint plus actuator and declared external force',
   trace_sha256=hashlib.sha256((batch/c['id']/'trace.npz').read_bytes()).hexdigest(),
   loaded_travel_m=float(-(state[-1,5]-state[onset,5])),
   loaded_speed_max_m_s=float(np.abs(state[onset:,14]).max()),
   bilateral_contact_loss_fraction=float(np.mean(np.any(t['counts'][onset:]==0,axis=1)))))
  col={.5:0,1.:1,2.:2}[c['capacity_ratio']]
  color={.9:'#2166ac',.99:'#b2182b'}[c['impedance']]
  style={.002:'-',.001:'--',.0005:':'}[h]
  label=f"d={c['impedance']}, h={h*1000:g} ms"
  axes[0,col].plot(state[onset:,0]-.5,-(state[onset:,5]-state[onset,5]),color=color,ls=style,label=label)
  # Downsample display only; raw perstep traces and metrics remain complete.
  stride=max(1,round(.01/h))
  axes[1,col].plot(state[onset:-1:stride,0]-.5,normal[onset::stride].mean(axis=1)/cmd,color=color,ls=style,label=label)
for col,r in enumerate((.5,1.,2.)):
 axes[0,col].set_title(f'R={r:g}'+(' (records rejected)' if r==1 else ''))
 axes[1,col].axhline(1,color='black',lw=.8,label='command reference')
 axes[1,col].set_xlabel('Time after loading (s)')
 for ax in axes[:,col]:ax.grid(alpha=.2)
axes[1,1].set_ylim(0,1.1);axes[1,2].set_ylim(0,1.1)
times=np.linspace(0,1,200);axes[0,0].plot(times,.5*9.81*.5*times**2,color='black',lw=1,label='ideal sliding')
axes[0,2].axhline(.001,color='black',lw=.8,label='1 mm hold limit')
axes[0,0].set_ylabel('Downward travel (m)');axes[1,0].set_ylabel('Mean inward force / command')
axes[0,0].legend(fontsize=7);axes[0,2].legend(fontsize=7)
fig.suptitle('Guided cube pinch: measured motion and inward load\nR=1 traces fail the frozen impulse-consistency bound; displayed only as rejected diagnostics')
fig.tight_layout();fig.savefig(root/'pinch-load-curves.png',dpi=160);plt.close(fig)
result=dict(scope='Offline diagnostics of immutable records; not a repaired acceptance or physical rerun',
 root_cause='Unresolved: records lack native qacc and solver convergence history; residual alone does not establish state injection or an engine defect',
 thresholds_unchanged=True,results=rows)
(root/'impulse-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
print('Saved all18 diagnostics and load/slip curves')
