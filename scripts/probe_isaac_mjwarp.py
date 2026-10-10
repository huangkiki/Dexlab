"""Frozen Isaac/MJWarp clock and contact diagnostic, not task qualification.

Run with the official compatible Isaac Python launcher and the bounded runner.
The launcher owns CUDA library selection, portable state and resource limits.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--warp-cache', type=Path, required=True)
    args, kit_args = parser.parse_known_args()
    raw = args.protocol.read_bytes()
    protocol = json.loads(raw)
    case = next(row for row in protocol['cases'] if row['id'] == args.case)
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    (output / 'protocol.json').write_bytes(raw)
    write_json(output / 'invocation.json', {
        'case': case['id'], 'protocol_sha256': hashlib.sha256(raw).hexdigest(),
        'recorder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'kit_args': kit_args,
    })
    from isaacsim import SimulationApp

    app = SimulationApp(
        dict(headless=True, create_new_stage=False, disable_viewport_updates=True,
             limit_cpu_threads=4, multi_gpu=False,
             extra_args=['--enable', 'isaacsim.physics.newton', '--/renderer/asyncInit=false']),
        experience=str(Path(os.environ['ISAAC_PATH']) / 'apps/isaacsim.exp.base.python.kit'))
    try:
        acquire(args, protocol, case, output)
    except BaseException as error:
        traceback.print_exc()
        write_json(output / 'exception.json', {
            'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
        raise
    finally:
        if sys.exc_info()[0] is None:
            import omni.usd
            import omni.timeline
            # Direct physics stepping does not drain Kit's stage events. Detach
            # the completed scene before processing these events, so updates
            # cannot advance or contaminate the recorded experiment.
            assert not omni.timeline.get_timeline_interface().is_playing()
            if not omni.usd.get_context().close_stage():
                raise RuntimeError('Failed to detach completed diagnostic stage')
            for _ in range(10):
                app.update()
            write_json(output / 'stage-detached.json', {'app_updates_without_stage': 10})
        # Kit fast shutdown can otherwise turn a caught Python failure into exit 0.
        app.close(skip_cleanup=sys.exc_info()[0] is not None,
                  exit_code=1 if sys.exc_info()[0] is not None else 0)


def acquire(args, protocol, case, output):
    import mujoco
    import mujoco_warp as mjw
    import newton
    import numpy as np
    import warp as wp
    import omni.usd
    import omni.timeline
    import isaacsim.physics.newton as extension
    from isaacsim.core.simulation_manager import SimulationManager
    from isaacsim.physics.newton.impl.solver_config import MuJoCoSolverConfig
    from isaacsim.physics.newton.impl.utils import newton_solver_to_api_schema
    from pxr import Gf, UsdGeom, UsdPhysics, UsdShade
    from dexlab.mujoco_artifacts import (
        save_conversion_evidence, warp_model_parameters, warp_execution_options,
        cpu_contact_address_valid,
    )

    versions = dict(mujoco=mujoco.__version__, mujoco_warp=mjw.__version__,
                    newton=newton.__version__, warp=wp.__version__)
    if versions != protocol['versions'] or mujoco.mj_versionString() != versions['mujoco']:
        raise ValueError('Runtime differs from the frozen compatible combination')
    wp.config.kernel_cache_dir = str(args.warp_cache)
    if not wp.get_device(protocol['device']).is_cuda:
        raise ValueError('CUDA required; no CPU fallback')
    mapped = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name in protocol['native_payload_sha256']:
            path = Path(fields[5]).resolve(strict=True)
            mapped[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if mapped != protocol['native_payload_sha256']:
        raise ValueError('Actually loaded native payload differs from the frozen vendor combination')
    write_json(output / 'runtime-identity.json', {
        'versions': versions, 'mapped_native_sha256': mapped,
        'modules': {name: {'sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                           'source_basename': Path(module.__file__).name}
                    for name, module in [('mujoco', mujoco), ('mujoco_warp', mjw),
                                          ('newton', newton), ('warp', wp)]},
    })
    assert not omni.timeline.get_timeline_interface().is_playing()
    omni.usd.get_context().new_stage()
    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    scene = UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(protocol['gravity_m_s2'])
    scene.GetPrim().ApplyAPI(newton_solver_to_api_schema['mujoco'])
    material = UsdShade.Material.Define(stage, '/World/Material')
    props = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    props.CreateStaticFrictionAttr(protocol['friction'])
    props.CreateDynamicFrictionAttr(protocol['friction'])
    props.CreateRestitutionAttr(0.)
    angle = np.deg2rad(protocol['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    side = protocol['side_m']
    for name, scale, center, dynamic in [
        ('Floor', (1., 1., .02), -.01 * normal, False),
        ('Cube', (side, side, side), (side / 2 + protocol['clearance_m']) * normal, True),
    ]:
        geom = UsdGeom.Cube.Define(stage, '/World/' + name)
        geom.CreateSizeAttr(1.)
        xform = UsdGeom.Xformable(geom)
        xform.AddTranslateOp().Set(Gf.Vec3d(*center))
        xform.AddOrientOp().Set(Gf.Quatf(float(np.cos(angle / 2)),
                                       Gf.Vec3f(0., float(np.sin(angle / 2)), 0.)))
        xform.AddScaleOp().Set(Gf.Vec3f(*scale))
        prim = geom.GetPrim()
        collision = UsdPhysics.CollisionAPI.Apply(prim)
        if name == 'Floor' and case['no_floor']:
            collision.CreateCollisionEnabledAttr(False)
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material, materialPurpose='physics')
        if dynamic:
            UsdPhysics.RigidBodyAPI.Apply(prim)
            UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(protocol['mass_kg'])
    stage.GetRootLayer().Export(str(output / 'input.usda'))
    assert SimulationManager.switch_physics_engine('newton')
    native = extension.acquire_stage()
    native.cfg.use_cuda_graph = protocol['use_cuda_graph']
    native.cfg.physics_frequency = 1. / protocol['dt_s']
    native.cfg.solver_cfg = MuJoCoSolverConfig(
        use_mujoco_contacts=case['mujoco_contacts'], save_to_mjcf=str(output / 'converted.xml'))
    native.initialize_newton(protocol['device'])
    if not native.initialized or native._init_failed:
        raise RuntimeError('Framework initialization failed')
    solver, gpu = native.solver, native.solver.mjw_data
    wp.synchronize()
    evidence = save_conversion_evidence(solver.mj_model, output, intermediate=output / 'converted.xml')
    write_json(output / 'gpu-model-initial.json', warp_model_parameters(solver.mjw_model))
    labels = native.model.body_label
    cube = labels.index('/World/Cube')
    write_json(output / 'admission.json', {
        'versions': versions, 'native_version': mujoco.mj_versionString(),
        'isaac_version': (Path(os.environ['ISAAC_PATH']) / 'VERSION').read_text().strip(),
        'config': asdict(native.cfg), 'framework_dt_s': native.sim_dt,
        'compiled_cpu_dt_s': solver.mj_model.opt.timestep,
        'gpu_dt_s': solver.mjw_model.opt.timestep.numpy().tolist(),
        'naconmax_shared': gpu.naconmax, 'njmax_per_world': gpu.njmax,
        'worlds': gpu.nworld, 'use_mujoco_contacts': solver._use_mujoco_contacts,
        'body_labels': labels, 'cube_index': cube,
        'binary_sha256': evidence['sha256']['model.mjb'],
        'state_update_interval': solver.update_data_interval,
        'solver_deterministic': str(solver._deterministic),
    })
    data = mujoco.MjData(solver.mj_model)
    contact_ids = wp.array(np.arange(gpu.naconmax, dtype=np.int32), dtype=wp.int32,
                           device=protocol['device'])
    contact_forces = wp.zeros(gpu.naconmax, dtype=wp.spatial_vector, device=protocol['device'])
    started = time.perf_counter()
    completed = 0
    # JSONL is deliberately incremental: retain every completed readback on failure.
    with (output / 'steps.jsonl').open('x') as stream:
        for step in range(protocol['steps']):
            before = native.state_0.body_qd.numpy()[cube].tolist()
            native.step_sim(protocol['dt_s'])
            wp.synchronize()
            # Preserve the actual counter even if a later readback fails.
            progress = output / 'progress.json'
            temporary = progress.with_suffix('.tmp')
            temporary.write_text(json.dumps({'physics_steps': step + 1,
                                              'recorded_steps': completed}) + '\n')
            temporary.replace(progress)
            if step == 0:
                write_json(output / 'gpu-model-first-step.json',
                           warp_model_parameters(solver.mjw_model))
                write_json(output / 'gpu-execution-options.json', warp_execution_options())
            nacon = int(gpu.nacon.numpy()[0])
            nefc = int(gpu.nefc.numpy()[0])
            counters = {'step': step + 1, 'nacon': nacon, 'nefc': nefc}
            if not 0 <= nacon <= gpu.naconmax or not 0 <= nefc <= gpu.njmax:
                write_json(output / 'capacity-overflow.json', counters)
                raise ValueError('Native capacity overflow; readback would truncate contacts')
            # Official conversion remaps sparse/pyramidal constraint addresses.
            mjw.get_data_into(data, solver.mj_model, gpu)
            with wp.ScopedDevice(protocol['device']):
                mjw.contact_force(solver.mjw_model, gpu, contact_ids, False, contact_forces)
            native_forces = contact_forces.numpy()[:nacon]
            addresses = gpu.contact.efc_address.numpy()[:nacon]
            contacts = []
            for i in range(data.ncon):
                contact = data.contact[i]
                force = np.zeros(6)
                cpu_valid = cpu_contact_address_valid(
                    int(contact.efc_address), int(contact.dim),
                    solver.mj_model.opt.cone == mujoco.mjtCone.mjCONE_PYRAMIDAL,
                    int(data.nefc))
                # get_data_into can assign a CPU address beyond nefc. Preserve
                # the address, but never pass it to native force dereferencing.
                if cpu_valid:
                    mujoco.mj_contactForce(solver.mj_model, data, i, force)
                contacts.append({
                    'geom': contact.geom.tolist(), 'frame': contact.frame.tolist(),
                    'position': contact.pos.tolist(), 'distance': float(contact.dist),
                    'friction': contact.friction.tolist(),
                    'force_local': native_forces[i].tolist(),
                    'cpu_converted_force_local': force.tolist() if cpu_valid else None,
                    'cpu_address_in_bounds': cpu_valid,
                    'native_efc_address': addresses[i].tolist(),
                    'cpu_efc_address': int(contact.efc_address),
                    'dim': int(contact.dim),
                })
            row = {
                **counters, 'framework_time_s': native.sim_time,
                'framework_step_count': native.simulation_step_count,
                'gpu_time_s': float(data.time),
                'gpu_dt_s': solver.mjw_model.opt.timestep.numpy().tolist(),
                'qpos': data.qpos.tolist(), 'qvel': data.qvel.tolist(),
                'qacc': data.qacc.tolist(), 'qfrc_constraint': data.qfrc_constraint.tolist(),
                'qfrc_smooth': data.qfrc_smooth.tolist(),
                'qfrc_bias': data.qfrc_bias.tolist(), 'qfrc_passive': data.qfrc_passive.tolist(),
                'native_efc_force': gpu.efc.force.numpy()[0, :nefc].tolist(),
                'native_solver_niter': gpu.solver_niter.numpy().tolist(),
                'newton_velocity_before': before,
                'newton_velocity_after': native.state_0.body_qd.numpy()[cube].tolist(),
                'newton_pose_after': native.state_0.body_q.numpy()[cube].tolist(),
                'contacts': contacts,
            }
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
            completed += 1
    write_json(output / 'completion.json', {
        'completed_steps': completed, 'requested_steps': protocol['steps'],
        'whole_step_loop_s': time.perf_counter() - started,
        'scope': 'Clock/contact diagnostic only; no reliable task coverage claim.',
    })
    print('DEXLAB_DIAGNOSTIC_COMPLETE', case['id'], completed, flush=True)


if __name__ == '__main__':
    main()
