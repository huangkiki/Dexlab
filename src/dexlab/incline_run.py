"""Native free-box incline observations; analytical scoring is separate."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from dexlab.cloth_engines import package_identity
from dexlab.engine_versions import mujoco_profile_identity


def axes(angle_deg):
    angle = np.deg2rad(angle_deg)
    return (np.array([np.cos(angle), 0., -np.sin(angle)]),
            np.array([np.sin(angle), 0., np.cos(angle)]),
            np.array([np.cos(angle / 2), 0., np.sin(angle / 2), 0.]))


def model_xml(protocol, case):
    """Keep all six free-body DOFs; only gravity and native contact act."""
    _, normal, quat = axes(case['angle_deg'])
    half = protocol['side_m'] / 2
    mass = protocol['mass_kg']
    inertia = mass * protocol['side_m'] ** 2 / 6
    vec = lambda values: ' '.join(map(str, values))
    d = case['impedance']
    return f'''<mujoco model="analytical-incline">
<option timestep="{case['timestep']}" gravity="0 0 -{protocol['gravity_m_s2']}"
 integrator="Euler" solver="Newton" cone="elliptic" impratio="{case.get('impratio', 1)}"
 iterations="{protocol['solver_iterations']}" tolerance="{protocol['solver_tolerance']}"/>
<default><geom condim="3" friction="{case['friction']} 0 0"
 solref="{vec(protocol['solref'])}" solimp="{d} {d} 0.001 0.5 2"/></default>
<worldbody>
 <geom name="plane" type="plane" size="2 2 .1" quat="{vec(quat)}"/>
 <body name="box" pos="{vec(half * normal)}" quat="{vec(quat)}"><freejoint/>
 <inertial pos="0 0 0" mass="{mass}" diaginertia="{inertia} {inertia} {inertia}"/>
 <geom name="box" type="box" size="{half} {half} {half}"/>
 </body>
</worldbody></mujoco>'''


def run_case(mj, protocol, case, destination):
    destination.mkdir()
    started = time.perf_counter()
    xml = model_xml(protocol, case)
    (destination / 'model.xml').write_text(xml)
    model = mj.MjModel.from_xml_string(xml)
    data = mj.MjData(model)
    mj.mj_forward(model, data)
    steps = round(protocol['duration_s'] / case['timestep'])
    states = np.zeros((steps + 1, 14))  # time, qpos7, qvel6
    states[0] = np.r_[data.time, data.qpos, data.qvel]
    forces = np.zeros((steps, 3))
    distances = np.zeros(steps)
    counts = np.zeros(steps, dtype=int)
    friction = np.full((steps, 2), np.nan)
    warning_counts = np.zeros((steps, len(data.warning)), dtype=int)
    setup_s = time.perf_counter() - started
    native_s = observation_s = 0.
    for step in range(steps):
        before = time.perf_counter()
        mj.mj_step(model, data)
        after = time.perf_counter()
        native_s += after - before
        states[step + 1] = np.r_[data.time, data.qpos, data.qvel]
        counts[step] = data.ncon
        mus = []
        for contact_id in range(data.ncon):
            contact = data.contact[contact_id]
            local = np.zeros(6)
            mj.mj_contactForce(model, data, contact_id, local)
            sign = 1 if contact.geom2 == 1 else -1
            forces[step] += sign * contact.frame.reshape(3, 3).T @ local[:3]
            distances[step] = min(distances[step], contact.dist)
            mus.extend(contact.friction[:2])
        if mus:
            friction[step] = min(mus), max(mus)
        warning_counts[step] = data.warning.number
        observation_s += time.perf_counter() - after
    loop_wall_s = native_s + observation_s
    # I/O and hashing are outside the timed stepping loop.
    np.savez_compressed(destination / 'trace.npz', states=states, forces=forces,
                        force_times=states[:-1, 0], contact_distance=distances,
                        contact_count=counts, friction=friction, warnings=warning_counts)
    readback = dict(timestep=float(model.opt.timestep), gravity=model.opt.gravity.tolist(),
                    mass=model.body_mass.tolist(), inertia=model.body_inertia.tolist(),
                    geom_friction=model.geom_friction.tolist(), solref=model.geom_solref.tolist(),
                    solimp=model.geom_solimp.tolist(), condim=model.geom_condim.tolist(),
                    nq=model.nq, nv=model.nv, nu=model.nu,
                    integrator=int(model.opt.integrator), solver=int(model.opt.solver),
                    cone=int(model.opt.cone), iterations=int(model.opt.iterations),
                    tolerance=float(model.opt.tolerance), impratio=float(model.opt.impratio))
    result = dict(case=case, readback=readback, setup_s=setup_s, native_step_s=native_s,
                  observation_s=observation_s, loop_wall_s=loop_wall_s,
                  total_case_wall_s=time.perf_counter() - started,
                  state_writes_after_initialization=0,
                  force_epoch='states[i].time; states[i+1] is postintegration',
                  trace_sha256=hashlib.sha256((destination / 'trace.npz').read_bytes()).hexdigest(),
                  xml_sha256=hashlib.sha256(xml.encode()).hexdigest())
    (destination / 'metadata.json').write_text(json.dumps(result, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import mujoco as mj

    protocol = json.loads(args.manifest.read_text())
    if len(protocol['cases']) > 24 or protocol['version'] != mj.mj_versionString():
        raise ValueError('Case budget or native version mismatch')
    # Runtime file verification happens before timed stepping, once per campaign.
    identity = mujoco_profile_identity(package_identity('mujoco'), mj.mj_versionString(),
                                       profile='qualification-3.15.0')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'manifest.json').write_bytes(args.manifest.read_bytes())
    started = time.perf_counter()
    for case in protocol['cases']:
        run_case(mj, protocol, case, args.output / case['id'])
    report = dict(runtime=identity, wall_s=time.perf_counter() - started,
                  manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  completed_cases=len(protocol['cases']))
    (args.output / 'campaign.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
