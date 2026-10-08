"""Record native isolated two-sphere impacts without prescribing their response."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from dexlab.cloth_engines import package_identity
from dexlab.engine_versions import mujoco_profile_identity


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_xml(protocol, case):
    radius = protocol['radius_m']
    bodies = []
    for i, (mass, x) in enumerate(zip(case['masses_kg'], case.get('initial_x_m', protocol['initial_x_m']))):
        inertia = 0.4 * mass * radius**2
        bodies.append(f'''<body name="sphere{i}" pos="{x} 0 0"><freejoint/>
<inertial pos="0 0 0" mass="{mass}" diaginertia="{inertia} {inertia} {inertia}"/>
<geom name="sphere{i}" type="sphere" size="{radius}"/></body>''')
    d = protocol['impedance']
    stiffness = case.get('stiffness_s2', protocol['stiffness_s2'])
    return f'''<mujoco model="elastic-impact"><option timestep="{case['timestep']}"
 gravity="0 0 0" integrator="Euler" solver="Newton" iterations="100" tolerance="1e-12"/>
<default><geom condim="1" friction="0 0 0" solref="-{stiffness} 0"
 solimp="{d} {d} 0.001 0.5 2" margin="0" gap="0"/></default>
<worldbody>{''.join(bodies)}</worldbody></mujoco>'''


def run_case(mj, protocol, case, output):
    output.mkdir()
    start = time.perf_counter()
    xml = model_xml(protocol, case)
    (output / 'model.xml').write_text(xml)
    model = mj.MjModel.from_xml_string(xml)
    data = mj.MjData(model)
    for i, velocity in enumerate(case['initial_vx_m_s']):
        data.qvel[6*i] = velocity
    mj.mj_forward(model, data)
    steps = round(protocol['duration_s'] / case['timestep'])
    states = np.empty((steps+1, 2, 13))
    times = np.empty(steps+1)
    forces = np.zeros((steps, 2, 3))
    counts = np.zeros(steps, dtype=int)
    distances = np.zeros(steps)
    warnings = np.zeros((steps, len(data.warning)), dtype=int)
    def record(i):
        times[i] = data.time
        states[i, :, :7] = data.qpos.reshape(2, 7)
        states[i, :, 7:] = data.qvel.reshape(2, 6)
    record(0)
    setup_s = time.perf_counter() - start
    native_s = observation_s = 0.
    for i in range(steps):
        before = time.perf_counter()
        mj.mj_step(model, data)
        after = time.perf_counter()
        native_s += after-before
        record(i+1)
        counts[i] = data.ncon
        for j in range(data.ncon):
            contact = data.contact[j]
            if {contact.geom1, contact.geom2} != {0, 1} or contact.dim != 1:
                raise ValueError('Unexpected native contact pair/dimension')
            force = np.zeros(6)
            mj.mj_contactForce(model, data, j, force)
            world = contact.frame.reshape(3, 3).T @ force[:3]
            forces[i, contact.geom1] -= world
            forces[i, contact.geom2] += world
            distances[i] = min(distances[i], contact.dist)
        warnings[i] = data.warning.number
        observation_s += time.perf_counter()-after
    np.savez_compressed(output/'trace.npz', states=states, times=times,
                        force_times=times[:-1], forces=forces, contact_count=counts,
                        contact_distance=distances, warnings=warnings)
    readback = dict(nq=model.nq, nv=model.nv, nu=model.nu, neq=model.neq,
                    timestep=model.opt.timestep, gravity=model.opt.gravity.tolist(),
                    integrator=int(model.opt.integrator), solver=int(model.opt.solver),
                    iterations=int(model.opt.iterations), tolerance=model.opt.tolerance,
                    mass=model.body_mass.tolist(), inertia=model.body_inertia.tolist(),
                    condim=model.geom_condim.tolist(), solref=model.geom_solref.tolist(),
                    solimp=model.geom_solimp.tolist(), size=model.geom_size.tolist(),
                    friction=model.geom_friction.tolist(), margin=model.geom_margin.tolist(),
                    gap=model.geom_gap.tolist(), damping=model.dof_damping.tolist(),
                    armature=model.dof_armature.tolist())
    meta = dict(case=case, readback=readback, state_writes_after_initialization=0,
                force_epoch='times[i]; states[i+1] is postintegration',
                trace_sha256=file_hash(output/'trace.npz'), xml_sha256=file_hash(output/'model.xml'),
                setup_s=setup_s, native_step_s=native_s, observation_s=observation_s,
                total_case_wall_s=time.perf_counter()-start)
    (output/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import mujoco as mj
    protocol = json.loads(args.manifest.read_text())
    budget = protocol.get('case_budget', 18)
    if budget not in (18, 27) or len(protocol['cases']) != budget or protocol['version'] != mj.mj_versionString():
        raise ValueError('Frozen case budget or version mismatch')
    identity = mujoco_profile_identity(package_identity('mujoco'), mj.mj_versionString(),
                                       profile='qualification-3.15.0')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'manifest.json').write_bytes(args.manifest.read_bytes())
    start = time.perf_counter()
    for case in protocol['cases']:
        run_case(mj, protocol, case, args.output/case['id'])
    (args.output/'campaign.json').write_text(json.dumps(dict(runtime=identity,
        manifest_sha256=file_hash(args.manifest), runner_sha256=file_hash(Path(__file__)),
        completed_cases=len(protocol['cases']), wall_s=time.perf_counter()-start), indent=2)+'\n')


if __name__ == '__main__':
    main()
