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
    solver = protocol.get('solver', 'Newton')
    cone = protocol.get('cone', 'elliptic')
    if solver not in ('PGS', 'CG', 'Newton') or cone not in ('pyramidal', 'elliptic'):
        raise ValueError('Unsupported incline solver or cone')
    if protocol.get('integrator', 'Euler') != 'Euler':
        raise ValueError('This recorder requires the Euler force epoch')
    collision = ' contype="0" conaffinity="0"' if case.get('negative_no_floor', False) else ''
    return f'''<mujoco model="analytical-incline">
<option timestep="{case['timestep']}" gravity="0 0 -{protocol['gravity_m_s2']}"
 integrator="Euler" solver="{solver}" cone="{cone}" impratio="{case.get('impratio', 1)}"
 iterations="{protocol['solver_iterations']}" tolerance="{protocol['solver_tolerance']}"/>
<default><geom condim="3" friction="{case['friction']} 0 0"
 solref="{vec(protocol['solref'])}" solimp="{d} {d} 0.001 0.5 2"/></default>
<worldbody>
 <geom name="plane" type="plane" size="2 2 .1" quat="{vec(quat)}"{collision}/>
 <body name="box" pos="{vec(half * normal)}" quat="{vec(quat)}"><freejoint/>
 <inertial pos="0 0 0" mass="{mass}" diaginertia="{inertia} {inertia} {inertia}"/>
 <geom name="box" type="box" size="{half} {half} {half}"/>
 </body>
</worldbody></mujoco>'''


def native_readback(model, data):
    """Read compiled geometry, frames and solver settings before any integration."""
    arrays = ('body_mass', 'body_inertia', 'body_ipos', 'body_iquat', 'body_gravcomp',
              'geom_type', 'geom_bodyid', 'geom_size', 'geom_pos', 'geom_quat',
              'geom_friction', 'geom_solref', 'geom_solimp', 'geom_condim',
              'geom_contype', 'geom_conaffinity', 'geom_priority', 'geom_solmix',
              'geom_margin', 'geom_gap', 'dof_damping', 'dof_armature', 'dof_frictionloss')
    result = {name: getattr(model, name).tolist() for name in arrays}
    # Keep the original evidence vocabulary for historical readers.
    for old, new in dict(mass='body_mass', inertia='body_inertia', solref='geom_solref',
                         solimp='geom_solimp', condim='geom_condim').items():
        result[old] = result[new]
    options = ('timestep', 'integrator', 'solver', 'cone', 'iterations', 'tolerance',
               'impratio', 'jacobian', 'ls_iterations', 'ls_tolerance',
               'noslip_iterations', 'noslip_tolerance', 'disableflags', 'enableflags')
    for name in options:
        result[name] = getattr(model.opt, name)
    result.update(gravity=model.opt.gravity.tolist(), nq=model.nq, nv=model.nv, nu=model.nu,
                  state=np.r_[data.time, data.qpos, data.qvel].tolist(),
                  geom_xpos=data.geom_xpos.tolist(), geom_xmat=data.geom_xmat.tolist(),
                  arena_bytes=int(model.narena))
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def run_case(mj, protocol, case, destination, *, admission_only=False):
    destination.mkdir()
    started = time.perf_counter()
    xml = model_xml(protocol, case)
    (destination / 'model.xml').write_text(xml)
    model = mj.MjModel.from_xml_string(xml)
    data = mj.MjData(model)
    mj.mj_forward(model, data)
    readback = native_readback(model, data)
    write_json(destination / 'admission.json', readback)
    # Retain the compiled export and independently compare its native readback.
    mj.mj_saveLastXML(str(destination / 'compiled.xml'), model)
    exported = mj.MjModel.from_xml_path(str(destination / 'compiled.xml'))
    exported_data = mj.MjData(exported)
    mj.mj_forward(exported, exported_data)
    write_json(destination / 'export-readback.json', native_readback(exported, exported_data))
    if admission_only:
        return
    steps = round(protocol['duration_s'] / case['timestep'])
    states = np.zeros((steps + 1, 14))
    states[0] = np.r_[data.time, data.qpos, data.qvel]
    forces = np.zeros((steps, 3))
    generalized = np.zeros((steps, 6))
    accelerations = np.zeros((steps, 6))
    distances = np.zeros(steps)
    counts = np.zeros(steps, dtype=int)
    friction = np.full((steps, 2), np.nan)
    warning_counts = np.zeros((steps, len(data.warning)), dtype=int)
    iterations = np.zeros(steps, dtype=int)
    contact_fields = dict(geom=[], frame=[], pos=[], force_local=[], distance=[],
                          friction=[], solref=[], solimp=[])
    offsets = [0]
    setup_s = time.perf_counter() - started
    native_s = observation_s = 0.
    completed, error = 0, None
    try:
        for step in range(steps):
            before = time.perf_counter()
            mj.mj_step(model, data)
            after = time.perf_counter()
            native_s += after - before
            states[step + 1] = np.r_[data.time, data.qpos, data.qvel]
            counts[step] = data.ncon
            generalized[step] = data.qfrc_constraint
            accelerations[step] = data.qacc
            iterations[step] = np.max(data.solver_niter)
            mus = []
            for contact_id in range(data.ncon):
                contact = data.contact[contact_id]
                local = np.zeros(6)
                mj.mj_contactForce(model, data, contact_id, local)
                sign = 1 if contact.geom2 == 1 else -1
                forces[step] += sign * contact.frame.reshape(3, 3).T @ local[:3]
                distances[step] = min(distances[step], contact.dist)
                mus.extend(contact.friction[:2])
                contact_fields['geom'].append([contact.geom1, contact.geom2])
                contact_fields['force_local'].append(local.copy())
                contact_fields['distance'].append(contact.dist)
                for name in ('frame', 'pos', 'friction', 'solref', 'solimp'):
                    contact_fields[name].append(getattr(contact, name).copy())
            offsets.append(len(contact_fields['geom']))
            if mus:
                friction[step] = min(mus), max(mus)
            warning_counts[step] = data.warning.number
            completed = step + 1
            observation_s += time.perf_counter() - after
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        # Partial evidence is kept at its actual length, never padded into success.
        contact_shapes = dict(geom=2, frame=9, pos=3, force_local=6, friction=5, solref=2, solimp=5)
        contacts = {name: np.asarray(values).reshape((-1, contact_shapes[name]))
                    if name in contact_shapes else np.asarray(values)
                    for name, values in contact_fields.items()}
        np.savez_compressed(destination / 'contacts.npz', offsets=np.asarray(offsets), **contacts)
        np.savez_compressed(destination / 'trace.npz', states=states[:completed+1],
                            forces=forces[:completed], generalized_contact_forces=generalized[:completed],
                            accelerations=accelerations[:completed], solver_iterations=iterations[:completed],
                            force_times=states[:completed, 0], contact_distance=distances[:completed],
                            contact_count=counts[:completed], friction=friction[:completed],
                            warnings=warning_counts[:completed])
        from dexlab.incline_score import file_hash
        result = dict(case=case, readback=readback, setup_s=setup_s, native_step_s=native_s,
                      observation_s=observation_s, loop_wall_s=native_s + observation_s,
                      total_case_wall_s=time.perf_counter() - started,
                      completed_steps=completed, error=error, state_writes_after_initialization=0,
                      force_epoch='states[i].time; states[i+1] is postintegration',
                      max_arena_bytes=int(data.maxuse_arena),
                      trace_sha256=file_hash(destination / 'trace.npz'), xml_sha256=file_hash(destination / 'model.xml'),
                      hashes={name: file_hash(destination / name) for name in
                              ('admission.json', 'compiled.xml', 'export-readback.json', 'contacts.npz')})
        write_json(destination / 'metadata.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--proof', type=Path)
    parser.add_argument('--admission-only', action='store_true')
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
    from dexlab.incline_score import file_hash
    source = args.output / 'source'
    source.mkdir()
    source_hashes = {}
    for name in ('incline_run.py', 'incline_score.py'):
        (source / name).write_bytes(Path(__file__).with_name(name).read_bytes())
        source_hashes[name] = file_hash(source / name)
    if protocol.get('schema_version') == 2:
        if args.proof is None:
            raise ValueError('Prospective qualification requires an official wheel proof')
        from dexlab.apple_admission import loaded_mujoco_library, record_native_file
        proof = json.loads(args.proof.read_bytes())
        native_hash = record_native_file('mujoco', loaded_mujoco_library())
        if (identity['code_sha256'] != proof['wheel']['package_code_sha256']
                or native_hash != proof['native_core_sha256'] or proof['version'] != protocol['version']):
            raise ValueError('Loaded runtime differs from the official qualification')
        identity.update(native_version=mj.mj_versionString(), native_core_sha256=native_hash,
                        precision='float64', device='cpu', engine_patches=False)
        (args.output / 'official-proof.json').write_bytes(args.proof.read_bytes())
    started = time.perf_counter()
    completed, error = 0, None
    try:
        for case in protocol['cases']:
            if any(file_hash(Path(__file__).with_name(name)) != digest for name, digest in source_hashes.items()):
                raise ValueError('Source changed during frozen campaign')
            run_case(mj, protocol, case, args.output / case['id'], admission_only=args.admission_only)
            completed += 1
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report = dict(runtime=identity, wall_s=time.perf_counter() - started,
                      manifest_sha256=file_hash(args.manifest), runner_sha256=file_hash(Path(__file__)),
                      completed_cases=completed, admission_only=args.admission_only, error=error,
                      source_hashes=source_hashes,
                      proof_sha256=file_hash(args.output / 'official-proof.json') if args.proof else None)
        write_json(args.output / 'campaign.json', report)



if __name__ == '__main__':
    main()
