"""Native rest-distance exclusion diagnostic; two disconnected patches, not CCD."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from time import monotonic

from dexlab.genesis_cloth_probe import write_grid


def write_layers(path, separation):
    """Duplicate our authored patch without joining or downloading any surface."""
    write_grid(path)
    original=path.read_text().splitlines()
    vertices=[line for line in original if line.startswith('v ')]
    faces=[line for line in original if line.startswith('f ')]
    upper=[]
    for line in vertices:
        _,x,y,z=line.split();upper.append(f'v {x} {y} {float(z)+separation:.8f}')
    shifted=['f '+' '.join(str(int(i)+len(vertices)) for i in line.split()[1:]) for line in faces]
    path.write_text('\n'.join(vertices+upper+faces+shifted)+'\n')


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    record={'completed':False,'version':version('genesis-world'),'dt_s':.002,'steps':10,
            'diameter_m':.008,'scenes':[]}
    start=monotonic()
    try:
        import genesis as gs
        import numpy as np
        if record['version']!='1.4.3': raise RuntimeError('Frozen runtime changed')
        record['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        for separation in (.03,.006):
            mesh=output/f'layers-{separation}.obj';write_layers(mesh,separation)
            case={'rest_separation_m':separation,'episodes':[]};record['scenes'].append(case)
            print('Building rest separation',separation,flush=True)
            gs.init(backend=gs.cpu,precision='64',seed=0,use_deterministic_algorithms=True,logging_level='warning')
            try:
                options=gs.options.PBDOptions(particle_size=.008,lower_bound=(-1,-1,-1),upper_bound=(1,1,1),
                    max_stretch_solver_iterations=4,max_bending_solver_iterations=1)
                material=gs.materials.PBD.Cloth(rho=.2,static_friction=.5,kinetic_friction=.5,
                    stretch_compliance=1e-7,bending_compliance=1e-5,
                    stretch_relaxation=.3,bending_relaxation=.1,air_resistance=0)
                scene=gs.Scene(show_viewer=False,sim_options=gs.options.SimOptions(dt=.002,substeps=1,gravity=(0,0,0)),pbd_options=options)
                cloth=scene.add_entity(gs.morphs.Mesh(file=str(mesh),pos=(0,0,.2),decimate=False),material=material)
                begin=monotonic();scene.build();case['build_s']=monotonic()-begin
                rest=cloth.get_particles_pos().cpu().numpy().copy()
                groups=rest[:,2]>.2+separation/2
                if not groups.any() or groups.all(): raise RuntimeError('Native remesh lost a layer')
                if np.max(abs(rest[:,2]-(.2+separation*groups)))>1e-8:
                    raise RuntimeError('Native remesh is not two parallel layers')
                initial=rest.copy();initial[:,2]=.2+np.where(groups,.003,-.003)
                case['native']={'rest':rest.tolist(),'rest_field':cloth.solver.particles_info.pos_rest.to_numpy().tolist(),
                    'groups':groups.tolist(),'faces':cloth._mesh.faces.tolist(),
                    'mass':cloth.solver.particles_info.mass.to_numpy().tolist(),
                    'options':options.model_dump(mode='json'),'material':material.model_dump(mode='json')}
                for repeat in range(2):
                    scene.reset();cloth.set_particles_pos(initial);cloth.set_particles_vel(np.zeros_like(initial))
                    def sample(step):
                        return {'step':step,'pos':cloth.get_particles_pos().tolist(),'vel':cloth.get_particles_vel().tolist()}
                    episode={'repeat':repeat,'rows':[sample(0)]};case['episodes'].append(episode)
                    for step in range(1,11):
                        scene.step();episode['rows'].append(sample(step))
                    print('separation',separation,'repeat',repeat,'complete',flush=True)
            finally: gs.destroy()
        record['completed']=True
    except Exception as error:
        record['error']=f'{type(error).__name__}: {error}';raise
    finally:
        record['wall_s']=monotonic()-start
        (output/'record.json').write_text(json.dumps(record,indent=2,allow_nan=True)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    run(parser.parse_args().output)
