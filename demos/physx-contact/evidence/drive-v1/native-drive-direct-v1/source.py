"""Standalone SDK drive diagnostic: no DexLab/UniSim imports or MJCF converter."""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import traceback

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--dt', type=float, default=0.001)
parser.add_argument('--device', default='cuda:0')
parser.add_argument('--solver', type=int, choices=[0, 1], default=1)
parser.add_argument('--velocity-iterations', type=int, default=2)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
source = Path(__file__).resolve()
(output/'source.py').write_bytes(source.read_bytes())
receipt = {'status': 'preparing', 'dt': args.dt, 'device': args.device,
           'solver_type': args.solver, 'position_iterations': 8,
           'velocity_iterations': args.velocity_iterations,
           'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
           'scope': __doc__, 'packages': {n: version(n) for n in ['isaacsim', 'isaaclab', 'torch']}}

def save_receipt():
    (output/'run.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')

save_receipt()
application = None
rows = []
try:
    from isaaclab.app import AppLauncher
    application = AppLauncher({'headless': True, 'enable_cameras': False,
                               'device': args.device, 'multi_gpu': False}).app
    import numpy as np
    import torch
    import isaaclab.sim as sim_utils
    from isaaclab.assets import Articulation, ArticulationCfg
    from isaaclab.actuators import ImplicitActuatorCfg
    from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema

    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(
        dt=args.dt, device=args.device, gravity=(0., 0., -9.81),
        physx=sim_utils.PhysxCfg(solver_type=args.solver,
            min_position_iteration_count=8, max_position_iteration_count=8,
            min_velocity_iteration_count=args.velocity_iterations,
            max_velocity_iteration_count=args.velocity_iterations)))
    stage = sim.stage
    root = UsdGeom.Xform.Define(stage, '/World/fixture').GetPrim()
    UsdPhysics.ArticulationRootAPI.Apply(root)
    articulation_api = PhysxSchema.PhysxArticulationAPI.Apply(root)
    articulation_api.CreateEnabledSelfCollisionsAttr().Set(False)
    articulation_api.CreateSolverPositionIterationCountAttr().Set(8)
    articulation_api.CreateSolverVelocityIterationCountAttr().Set(args.velocity_iterations)
    for name, inertia in [('base', (.001, .001, .001)),
                          ('pad', (.000074166667, .000054166667, .000021666667))]:
        body = UsdGeom.Xform.Define(stage, f'/World/fixture/{name}')
        body.AddTranslateOp().Set(Gf.Vec3d(-.0152, 0, .2))
        prim = body.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim).CreateRigidBodyEnabledAttr().Set(True)
        PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
        mass = UsdPhysics.MassAPI.Apply(prim)
        mass.CreateMassAttr().Set(.1)
        mass.CreateDiagonalInertiaAttr().Set(Gf.Vec3f(*inertia))
        mass.CreateCenterOfMassAttr().Set(Gf.Vec3f(0))
    cube = UsdGeom.Cube.Define(stage, '/World/fixture/pad/shape')
    cube.CreateSizeAttr().Set(2.)
    cube.AddScaleOp().Set(Gf.Vec3f(.005, .025, .04))
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    fixed = UsdPhysics.FixedJoint.Define(stage, '/World/fixture/fixed')
    fixed.CreateBody1Rel().SetTargets(['/World/fixture/base'])
    fixed.CreateLocalPos0Attr().Set(Gf.Vec3f(-.0152, 0, .2))
    fixed.CreateLocalPos1Attr().Set(Gf.Vec3f(0))
    joint = UsdPhysics.PrismaticJoint.Define(stage, '/World/fixture/slide')
    joint.CreateBody0Rel().SetTargets(['/World/fixture/base'])
    joint.CreateBody1Rel().SetTargets(['/World/fixture/pad'])
    joint.CreateAxisAttr().Set('X')
    joint.CreateLowerLimitAttr().Set(-.02)
    joint.CreateUpperLimitAttr().Set(.02)
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0))
    joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0))
    robot = Articulation(ArticulationCfg(prim_path='/World/fixture', spawn=None,
        actuators={'drive': ImplicitActuatorCfg(joint_names_expr=['slide'],
            stiffness=500., damping=10., effort_limit_sim=2., armature=0., friction=0.)}))
    sim.reset()
    pad = robot.body_names.index('pad')
    view = robot.root_physx_view
    def array(tensor):
        return tensor.detach().cpu().numpy().copy()
    receipt.update(status='running', body_names=robot.body_names, joint_names=robot.joint_names,
                   fixed_base=robot.is_fixed_base, masses=array(view.get_masses()).tolist(),
                   stiffness=array(view.get_dof_stiffnesses()).tolist(),
                   damping=array(view.get_dof_dampings()).tolist(),
                   effort_limits=array(view.get_dof_max_forces()).tolist(),
                   unisim_imported=any(n=='unisim' or n.startswith('unisim.') for n in sys.modules))
    assert not receipt['unisim_imported']
    assert robot.is_fixed_base
    stage.Export(str(output/'scene.usda'))
    save_receipt()
    forces = torch.zeros((1, robot.num_bodies, 3), device=sim.device)
    torques = torch.zeros_like(forces)
    for step in range(round(2./args.dt)):
        t = step*args.dt
        target = .01 if t < 1.5 else 0.
        load = -1. if .5 <= t < 1. else -3. if 1. <= t < 1.04 else 0.
        forces.zero_()
        forces[0, pad, 0] = load
        robot.set_joint_position_target(torch.full((1, 1), target, device=sim.device))
        robot.set_external_force_and_torque(forces, torques, is_global=True)
        robot.write_data_to_sim()
        sim.step(render=False)
        robot.update(args.dt)
        rows.append({'time': (step+1)*args.dt, 'target': target, 'external_force': load,
                     'q': array(robot.data.joint_pos)[0, 0],
                     'dq': array(robot.data.joint_vel)[0, 0],
                     'raw_q': array(view.get_dof_positions())[0, 0],
                     'raw_dq': array(view.get_dof_velocities())[0, 0],
                     'position': array(robot.data.body_link_state_w)[0, pad, :3],
                     'velocity': array(robot.data.body_link_state_w)[0, pad, 7:10],
                     'raw_position': array(view.get_link_transforms())[0, pad, :3],
                     'raw_velocity': array(view.get_link_velocities())[0, pad, :3]})
    receipt['status'] = 'completed'
except Exception:
    receipt.update(status='error', error=traceback.format_exc())
finally:
    import numpy as np
    arrays = {k: np.array([r[k] for r in rows]) for k in rows[0]} if rows else {}
    np.savez_compressed(output/'states.npz', **arrays)
    receipt['archive_sha256'] = hashlib.sha256((output/'states.npz').read_bytes()).hexdigest()
    save_receipt()
    if application is not None:
        application.close()
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt['status']=='completed' else 1)
