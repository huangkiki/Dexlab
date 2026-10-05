"""Qualify static official SDF construction paths; preserve unequal results."""
import json
from pathlib import Path
import shutil

import numpy as np
from dexlab.apple_admission import observe_runtime, refresh_inventory
from dexlab.engine_versions import validate_versions
from dexlab.official_wheels import verify_official_wheel
from dexlab.physx_baseline import digest, write_json

import argparse
parser=argparse.ArgumentParser(description="Static official SDF construction-path qualification")
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--wheel-dir',type=Path,required=True)
args=parser.parse_args()
root = Path(__file__).resolve().parents[2]
output = args.output.resolve()
wheels = args.wheel_dir.resolve()
output.mkdir(parents=True, exist_ok=False)
sources = sorted(set(root.glob('src/dexlab/*.py')) | set(root.glob('src/dexlab/tasks/*.py')) | {root/'demos/contact-benchmark/normal_response.py', root/'benchmarks/contact-transfer-v1.json'})
sources = sorted(set(sources) | {Path(__file__).resolve()})
hashes = {str(p.relative_to(root)): digest(p) for p in sources}
for p in sources:
    destination = output / 'source' / p.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, destination)
runtime = observe_runtime()
audit = refresh_inventory()
validate_versions(audit, runtime['installed'], runtime['native'])
receipts = {}
for row in audit:
    available = [(wheels/name, sha) for name,sha in row['distribution_sha256'].items()
                 if name.endswith('.whl') and (wheels/name).is_file()]
    if len(available) != 1:
        raise ValueError('Expected exactly one official wheel')
    path, sha = available[0]
    name = row['package']
    receipts[name] = verify_official_wheel(path, package=name, version=runtime['installed'][name],
                                          official_sha256=sha, installed_code_sha256=runtime['package_code_sha256'][name])
write_json(output/'admission.json', {'runtime':runtime,'audit':audit,'official_wheels':receipts})


import trimesh
from superdex import physics as physics
physics.initialize(num_worker_threads=0)
scene=physics.create_scene('static-sdf-bake-pair')
try:
    half=np.array([.02,.015,.01])
    mesh=trimesh.creation.box(extents=2*half)
    params=physics.GridSdfParams(resolution_mode=physics.GridSdfResolutionMode.EXPLICIT,resolution_delta=[.002]*3)
    shape_auto=physics.create_tri_mesh_shape(mesh.vertices.ravel(),mesh.faces.astype(np.int32).ravel())
    model=physics.ModelData()
    model.mesh=physics.MeshData(coordinates=mesh.vertices.ravel(),connectivity=mesh.faces.astype(np.int32).ravel(),nodes_per_element=3)
    physics.model.bake_sdf(model,params)
    grid=model.sdf
    dims=np.asarray(grid.dims).copy()
    values=np.asarray(grid.values).copy()
    assert values.size<1000000 and np.isfinite(values).all()
    np.savez(output/'baked-grid.npz',values=values,dims=dims,vertices=mesh.vertices,faces=mesh.faces)
    grid_meta={'dims':dims.tolist(),'values_shape':list(values.shape),'bounds_min':np.asarray(grid.bounds.min).tolist(),
        'bounds_max':np.asarray(grid.bounds.max).tolist(),'rotation':np.asarray(grid.rotation).tolist(),
        'scale':np.asarray(grid.scale).tolist(),'translation':np.asarray(grid.translation).tolist()}
    shape_baked=physics.create_model_shape(model)
    angle=.7;quat=[0,0,np.sin(angle/2),np.cos(angle/2)];translation=np.array([.1,.2,.3])
    actors=[]
    for name,shape in [('automatic',shape_auto),('precomputed',shape_baked)]:
        actors.append(scene.create_rigid_actor(name=name,shape=shape,is_static=True,collider_type=physics.ColliderType.SDF,
             sdf=params,world_from_local=physics.TransformRT(rotation=quat,translation=translation)))
        physics.release_shape(shape)
    scene.step(0)
    local=np.array(np.meshgrid(*[np.linspace(-b*.9,b*.9,9) for b in half],indexing='ij')).reshape(3,-1).T
    rot=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    world=local@rot.T+translation
    observed=[]
    for actor in actors:
        distances=np.empty(len(world),dtype=np.float64);actor.get_points_distance_to_surface(world,distances);observed.append(distances)
    q=np.abs(local)-half;analytic=np.linalg.norm(np.maximum(q,0),axis=1)+np.minimum(q.max(axis=1),0)
    np.savez(output/'queries.npz',local=local,world=world,automatic=observed[0],precomputed=observed[1],analytic=analytic)
    poses=[]
    for actor in actors:
        transform=actor.get_root_transform()
        poses.append([*np.asarray(transform.translation).tolist(),*np.asarray(transform.rotation).tolist()])
    report={'source_sha256':hashes,'engine_versions':runtime['installed'],'actual_poses':poses,'requested_spacing_m':[.002]*3,'grid':grid_meta,'actual_colliders':[a.get_collider_type().name for a in actors],
        'query_count':len(local),'query_region':'inside original box, avoids documented outside-SDF upper-bound behavior',
        'maximum_pair_difference_m':float(np.max(np.abs(observed[0]-observed[1]))),
        'maximum_analytic_difference_m':[float(np.max(np.abs(x-analytic))) for x in observed],
        'finite':bool(all(np.isfinite(x).all() for x in observed)),
        'time_s':float(scene.get_total_simulation_time()),
        'scope':'Single static asymmetric box, official precomputed grid vs automatic native collider queries; not exhaustive internal-grid identity or dynamic equivalence'}
    from dexlab.sdf_observability import summarize
    with np.load(output/'baked-grid.npz',allow_pickle=False) as saved_grid, np.load(output/'queries.npz',allow_pickle=False) as saved_queries:
        report['independent_summary']=summarize(report,saved_grid,saved_queries)
    report['source_unchanged']=all(digest(root/name)==sha for name,sha in hashes.items())
    if not report['source_unchanged']:
        raise RuntimeError('Source changed during static qualification')
    write_json(output/'comparison.json',report)
    public_files=[output/'comparison.json', output/'baked-grid.npz', output/'queries.npz', *(output/'source').rglob('*.py'), output/'source/benchmarks/contact-transfer-v1.json']
    write_json(output/'manifest.json', {str(path.relative_to(output)):digest(path) for path in public_files})
    print(json.dumps(report,indent=2),flush=True)
finally:
    physics.destroy_scene(scene)
