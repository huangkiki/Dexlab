"""Guided force-controlled jaws and a free cube; no analytical scoring here."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from dexlab.cloth_engines import package_identity
from dexlab.engine_versions import mujoco_profile_identity


def commands(protocol, case, step):
    """Integer epochs keep preload and ramp timing identical across stepsizes."""
    h = case['timestep']
    normal = case['capacity_ratio'] * protocol['cube_mass_kg'] * protocol['gravity_m_s2'] / (2 * protocol['friction'])
    ramp = min(step / round(protocol['ramp_s'] / h), 1.)
    load = protocol['cube_mass_kg'] * protocol['gravity_m_s2'] if step >= round(protocol['preload_s'] / h) else 0.
    return np.array([normal * ramp, normal * ramp]), np.array([0., 0., -load])


def model_xml(protocol, case):
    half = protocol['side_m'] / 2
    inertia = protocol['cube_mass_kg'] * protocol['side_m'] ** 2 / 6
    size = protocol['jaw_half_size_m']
    d = case['impedance']
    jaw_inertia = [protocol['jaw_mass_kg'] * (size[(i+1)%3] ** 2 + size[(i+2)%3] ** 2) / 3 for i in range(3)]
    vec = lambda x: ' '.join(map(str, x))
    jaws = []
    for name, sign in (('left', -1), ('right', 1)):
        jaws.append(f'''<body name="{name}" pos="{sign * (half + size[0])} 0 0">
<joint name="{name}" type="slide" axis="{-sign} 0 0" limited="false" damping="0" frictionloss="0" armature="0"/>
<inertial pos="0 0 0" mass="{protocol['jaw_mass_kg']}" diaginertia="{vec(jaw_inertia)}"/>
<geom name="{name}" type="box" size="{vec(size)}"/></body>''')
    return f'''<mujoco model="pinch-load">
<option timestep="{case['timestep']}" gravity="0 0 0" integrator="Euler" solver="Newton" cone="elliptic" impratio="1" iterations="{protocol['solver_iterations']}" tolerance="{protocol['solver_tolerance']}"/>
<default><geom condim="3" friction="{protocol['friction']} 0 0" solref="{vec(protocol['solref'])}" solimp="{d} {d} .001 .5 2"/></default>
<worldbody>{''.join(jaws)}
<body name="cube"><freejoint name="cube"/>
<inertial pos="0 0 0" mass="{protocol['cube_mass_kg']}" diaginertia="{inertia} {inertia} {inertia}"/>
<geom name="cube" type="box" size="{half} {half} {half}"/></body>
</worldbody><actuator><motor joint="left" gear="1"/><motor joint="right" gear="1"/></actuator>
</mujoco>'''


def compiled_readback(model):
    """Record all fields checked by the independent configuration audit."""
    fields = ('body_mass','body_inertia','body_pos','jnt_type','jnt_axis','jnt_qposadr','jnt_dofadr',
              'dof_damping','dof_frictionloss','dof_armature','geom_type','geom_size','geom_bodyid',
              'geom_friction','geom_solref','geom_solimp','geom_condim','actuator_gear',
              'actuator_gainprm','actuator_biasprm','actuator_trnid')
    readback = {name: getattr(model, name).tolist() for name in fields}
    readback.update(nq=model.nq,nv=model.nv,nu=model.nu,gravity=model.opt.gravity.tolist(),
                    timestep=float(model.opt.timestep),integrator=int(model.opt.integrator),
                    solver=int(model.opt.solver),cone=int(model.opt.cone),impratio=float(model.opt.impratio),
                    iterations=int(model.opt.iterations),tolerance=float(model.opt.tolerance))
    return readback


def run_case(mj, protocol, case, output):
    output.mkdir()
    started = time.perf_counter()
    xml = model_xml(protocol, case)
    (output / 'model.xml').write_text(xml)
    model = mj.MjModel.from_xml_string(xml)
    data = mj.MjData(model)
    cube = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, 'cube')
    cube_geom = mj.mj_name2id(model, mj.mjtObj.mjOBJ_GEOM, 'cube')
    jaw_geoms = [mj.mj_name2id(model, mj.mjtObj.mjOBJ_GEOM, side) for side in ('left', 'right')]
    mj.mj_forward(model, data)
    n = round(protocol['duration_s'] / case['timestep'])
    states = np.zeros((n+1, 1+model.nq+model.nv))
    states[0] = np.r_[data.time, data.qpos, data.qvel]
    ctrl = np.zeros((n, 2)); external = np.zeros((n, 3))
    forces = np.zeros((n, 2, 3)); moments = np.zeros((n, 2, 3))
    counts = np.zeros((n, 2), dtype=int)
    actuator = np.zeros((n, model.nv)); constraint = np.zeros_like(actuator)
    # Slots retain per-contact data, not only a summed force: side, position3,
    # normal3, world force on cube3, distance, friction2. Unused slots are NaN.
    contacts = np.full((n, 16, 13), np.nan)
    warnings = np.zeros((n, len(data.warning)), dtype=int)
    setup_s = time.perf_counter()-started
    native_s = observation_s = control_s = 0.
    for step in range(n):
        before = time.perf_counter()
        ctrl[step], external[step] = commands(protocol, case, step)
        data.ctrl[:] = ctrl[step]
        data.xfrc_applied[cube, :3] = external[step]
        control_s += time.perf_counter() - before
        before = time.perf_counter()
        # mj_step leaves pose/contact kinematics at this solve epoch.
        mj.mj_step(model, data)
        after = time.perf_counter(); native_s += after-before
        states[step+1] = np.r_[data.time, data.qpos, data.qvel]
        actuator[step] = data.qfrc_actuator
        constraint[step] = data.qfrc_constraint
        if data.ncon > 16:
            raise ValueError('Contact capacity exceeded; no truncation allowed')
        for k in range(data.ncon):
            c = data.contact[k]
            pair = (c.geom1, c.geom2)
            if cube_geom not in pair or not any(g in pair for g in jaw_geoms):
                raise ValueError('Unexpected support/contact pair')
            side = next(i for i, g in enumerate(jaw_geoms) if g in pair)
            local = np.zeros(6); mj.mj_contactForce(model, data, k, local)
            sign = 1 if c.geom2 == cube_geom else -1
            rotation = c.frame.reshape(3, 3).T
            force = sign * rotation @ local[:3]
            forces[step, side] += force
            moments[step, side] += np.cross(c.pos-data.xipos[cube], force) + sign * rotation @ local[3:]
            counts[step, side] += 1
            contacts[step, k] = np.r_[side, c.pos, sign * rotation[:, 0], force, c.dist, c.friction[:2]]
        warnings[step] = data.warning.number
        observation_s += time.perf_counter()-after
    serialized = time.perf_counter()
    np.savez_compressed(output/'trace.npz', states=states, commands=ctrl, external=external,
                        forces=forces, moments=moments, contacts=contacts, counts=counts,
                        actuator=actuator, constraint=constraint, warnings=warnings,
                        force_times=states[:-1, 0])
    readback = compiled_readback(model)
    metadata = dict(case=case, readback=readback, cube_body=cube, cube_geom=cube_geom,
                    jaw_geoms=jaw_geoms, state_writes_after_initialization=0,
                    force_epoch='states[i].time; states[i+1] postintegration',
                    setup_s=setup_s,control_s=control_s,native_step_s=native_s,observation_s=observation_s,
                    serialization_s=time.perf_counter()-serialized,
                    total_case_wall_s=time.perf_counter()-started,
                    xml_sha256=hashlib.sha256(xml.encode()).hexdigest(),
                    trace_sha256=hashlib.sha256((output/'trace.npz').read_bytes()).hexdigest())
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    import mujoco as mj
    p = json.loads(args.manifest.read_text())
    if len(p['cases']) != 18 or p['version'] != mj.mj_versionString():
        raise ValueError('Budget/version mismatch')
    identity = mujoco_profile_identity(package_identity('mujoco'), mj.mj_versionString(),profile='qualification-3.15.0')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'manifest.json').write_bytes(args.manifest.read_bytes())
    start = time.perf_counter()
    for case in p['cases']:
        run_case(mj,p,case,args.output/case['id'])
    report = dict(runtime=identity,completed_cases=len(p['cases']),wall_s=time.perf_counter()-start,
                  manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/'campaign.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
