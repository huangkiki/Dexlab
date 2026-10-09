"""Native Genesis incline acquisition; optional engine, no adapter or state playback."""

import argparse
import gzip
import json
import os
from pathlib import Path
import time

import numpy as np

from dexlab.cloth_engines import package_identity
from dexlab.incline_score import file_hash


def write_json(path, value):
    raw = json.dumps(value, indent=2, allow_nan=False) + '\n'
    with path.open('x') as stream:
        stream.write(raw)


def runtime_identity(proof):
    """Record the running compiler configuration and actually mapped library."""
    import genesis as gs
    import quadrants as qd

    packages = {}
    for name in ('genesis-world', 'quadrants'):
        identity = package_identity(name)
        identity.pop('installation_origin', None)
        if identity != proof['packages'][name]['identity']:
            raise ValueError('Installed package differs from the official proof')
        packages[name] = identity
    root = Path(qd.__file__).resolve().parent
    mapped = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) != 6 or not fields[5].startswith('/'):
            continue
        path = Path(fields[5]).resolve()
        if path.is_relative_to(root) and '.so' in path.name:
            name = str(path.relative_to(root.parent))
            if name not in mapped:
                mapped[name] = file_hash(path)
    if mapped != proof['packages']['quadrants']['native_files']:
        raise ValueError('Mapped compiler payload differs from official wheel')
    config = qd.lang.impl.current_cfg()
    return dict(packages=packages, mapped_native=mapped,
                backend=gs.backend.name, precision=np.dtype(gs.np_float).name,
                deterministic=gs.use_deterministic_algorithms, seed=gs.SEED,
                compiler={key: getattr(config, key) for key in
                          ('cpu_max_num_threads', 'num_compile_threads', 'fast_math', 'random_seed')},
                compiler_default_fp=str(config.default_fp), engine_patches=False)


class GenesisIncline:
    """Own one plane and one free cube; all setters run before the first step."""

    def __init__(self, protocol, case):
        import genesis as gs
        from genesis.utils.misc import qd_to_numpy

        self.to_numpy = qd_to_numpy
        config = protocol['genesis']
        options = dict(config['options'])
        for key, enum in (('constraint_solver', gs.constraint_solver),
                          ('friction_cone', gs.friction_cone),
                          ('contact_resolution', gs.contact_resolution),
                          ('integrator', gs.integrator)):
            options[key] = getattr(enum, options[key])
        self.scene = gs.Scene(show_viewer=False,
                              sim_options=gs.options.SimOptions(dt=case['timestep'], substeps=1,
                                                               gravity=(0, 0, -protocol['gravity_m_s2'])),
                              rigid_options=gs.options.RigidOptions(**options))
        angle = np.deg2rad(case['angle_deg'])
        normal = np.array([np.sin(angle), 0., np.cos(angle)])
        side = protocol['side_m']
        negative = case.get('negative_no_floor', False)
        plane_mask, cube_mask = (1, 2) if negative else (65535, 65535)
        # Rigid's constructor rejects friction < .01, whereas the official geom
        # setter accepts zero. Preserve both stages and the contact floor.
        material_friction = max(case['friction'], .01)
        self.plane = self.scene.add_entity(
            gs.morphs.Plane(euler=(0, case['angle_deg'], 0), contype=plane_mask, conaffinity=plane_mask),
            material=gs.materials.Rigid(friction=material_friction))
        self.cube = self.scene.add_entity(
            gs.morphs.Box(size=(side,) * 3, pos=tuple(side / 2 * normal),
                          euler=(0, case['angle_deg'], 0), contype=cube_mask, conaffinity=cube_mask),
            material=gs.materials.Rigid(rho=protocol['density_kg_m3'], friction=material_friction))
        self.scene.build()
        self.solver = self.scene.rigid_solver
        self.initial_geom_parameters = self.geom_parameters()
        for geom in (self.plane.geoms[0], self.cube.geoms[0]):
            geom.set_friction(case['friction'])
            geom.set_sol_params(config['sol_params'])
        rigid = self.solver
        self.admission = dict(
            state=self.state().tolist(), options=rigid._options.model_dump(mode='json'),
            sim_options=self.scene.sim.options.model_dump(mode='json'),
            static_config={key: value.item() if isinstance(value, np.generic) else value
                           for key in type(rigid.rigid_config).__annotations__
                           for value in (getattr(rigid.rigid_config, key),)},
            n_envs=rigid.n_envs, n_dofs=self.cube.n_dofs, n_geoms=rigid.n_geoms,
            mass=self.cube.get_links_mass().tolist(), com=self.cube.get_links_COM().tolist(),
            inertia=self.cube.get_links_inertia().tolist(),
            geom_parameters=self.geom_parameters(),
            authored_material_friction=material_friction,
            before_geom_setters=self.initial_geom_parameters,
            friction_ratio=rigid.get_geoms_friction_ratio().tolist(),
            initial_contact_count=int(qd_to_numpy(rigid.collider.collider_state.n_contacts).item()),
            initial_errors=qd_to_numpy(rigid._errno).tolist(),
            contact_capacity=int(rigid.collider.collider_state.contact_data.friction.shape[0]),
            constraint_storage_shape=list(rigid.constraint_solver.constraint_state.Jaref.shape),
            solver_statistics=dict(achieved_iterations=None,
                reason='CPU monolithic iteration loop does not persist its iteration count; graph-loop counter is not used'),
        )

    def geom_parameters(self):
        return [dict(id=geom.idx, type=int(geom.type), data=geom.data.tolist(),
                     pos=geom.get_pos().tolist(), quat=geom.get_quat().tolist(),
                     friction=geom.get_friction().tolist(), sol_params=geom.get_sol_params().tolist(),
                     contype=geom.contype, conaffinity=geom.conaffinity)
                for geom in (self.plane.geoms[0], self.cube.geoms[0])]

    def state(self):
        return np.r_[self.scene.get_time().item(), self.cube.get_pos().numpy(), self.cube.get_quat().numpy(),
                     self.cube.get_vel().numpy(), self.cube.get_ang().numpy()]

    def step(self):
        start = time.perf_counter()
        self.scene.step()
        native_s = time.perf_counter() - start
        start = time.perf_counter()
        rigid = self.solver
        contacts = {key: value.tolist() for key, value in rigid.collider.get_contacts().items()}
        count = len(contacts['geom_a'])
        data = rigid.collider.collider_state
        # Match the public ledger's sorted order, including pruning permutations.
        indices = self.to_numpy(data.contact_sort_idx, transpose=True)[0, :count].astype(int)
        for key in ('friction', 'sol_params'):
            contacts[key] = self.to_numpy(getattr(data.contact_data, key), transpose=True)[0, indices].tolist()
        state = self.state()
        force = self.cube.get_links_net_contact_force().numpy().sum(axis=0)
        errors = self.to_numpy(rigid._errno).copy()
        return state, force, contacts, errors, native_s, time.perf_counter() - start

    def close(self):
        self.scene.destroy()


def run_case(protocol, case, destination, *, admission_only=False):
    from dexlab.genesis_incline_score import validate_admission

    destination.mkdir(exist_ok=False)
    start = time.perf_counter()
    native = GenesisIncline(protocol, case)
    try:
        write_json(destination / 'admission.json', native.admission)
        validate_admission(protocol, case, native.admission)
        if admission_only:
            return
        steps = round(protocol['duration_s'] / case['timestep'])
        states = np.zeros((steps + 1, 14))
        states[0] = native.state()
        forces = np.zeros((steps, 3))
        counts, errors = np.zeros(steps, dtype=int), np.zeros((steps, 1), dtype=int)
        completed = attempts = 0
        setup_s = time.perf_counter() - start
        native_s = observation_s = 0.
        error = None
        try:
            with gzip.open(destination / 'contacts.jsonl.gz', 'xt') as stream:
                for index in range(steps):
                    attempts = index + 1
                    state, force, contacts, errno, physics_s, read_s = native.step()
                    states[index + 1], forces[index], counts[index], errors[index] = state, force, len(contacts['geom_a']), errno
                    stream.write(json.dumps(dict(interval_start_s=states[index, 0], interval_end_s=state[0],
                                                contacts=contacts), allow_nan=False) + '\n')
                    completed = index + 1
                    native_s += physics_s
                    observation_s += read_s
        except BaseException as exc:
            error = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            np.savez_compressed(destination / 'trace.npz', states=states[:completed + 1],
                                forces=forces[:completed], contact_count=counts[:completed],
                                native_errors=errors[:completed], force_times=states[:completed, 0])
            write_json(destination / 'metadata.json', dict(
                case=case, completed_steps=completed, attempted_steps=attempts,
                error=error, state_writes_after_initialization=0,
                setup_s=setup_s, native_step_s=native_s, observation_s=observation_s,
                total_case_wall_s=time.perf_counter() - start,
                force_epoch='Contact force used in [states[i].time, states[i+1].time], read after step',
                contact_geometry_epoch='Pre-integration collision detection for the same update',
                hashes={name: file_hash(destination / name) for name in
                        ('admission.json', 'contacts.jsonl.gz', 'trace.npz')},
            ))
    finally:
        native.close()


def main():
    import genesis as gs
    from dexlab.genesis_incline_score import validate_protocol, validate_runtime

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--admission-only', action='store_true')
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_bytes())
    validate_protocol(protocol)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'protocol.json').write_bytes(args.protocol.read_bytes())
    (args.output / 'official-proof.json').write_bytes(args.proof.read_bytes())
    proof = json.loads(args.proof.read_bytes())
    os.environ['QD_NUM_THREADS'] = str(protocol['threads'])
    gs.init(backend=gs.cpu, precision='64', seed=0, use_deterministic_algorithms=True, logging_level='warning')
    try:
        runtime = runtime_identity(proof)
        validate_runtime(protocol, proof, runtime)
        write_json(args.output / 'runtime.json', runtime)
        sources = args.output / 'source'
        sources.mkdir()
        hashes = {}
        for name in ('genesis_incline.py', 'genesis_incline_score.py', 'incline_score.py'):
            source = Path(__file__).with_name(name)
            (sources / name).write_bytes(source.read_bytes())
            hashes[name] = file_hash(sources / name)
        completed, error = [], None
        try:
            for case in protocol['cases']:
                if any(file_hash(Path(__file__).with_name(name)) != digest for name, digest in hashes.items()):
                    raise ValueError('Source changed during the frozen batch')
                run_case(protocol, case, args.output / case['id'], admission_only=args.admission_only)
                completed.append(case['id'])
                print(case['id'], 'recorded', flush=True)
        except BaseException as exc:
            error = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            write_json(args.output / 'campaign.json', dict(
                protocol_sha256=file_hash(args.protocol), official_proof_sha256=file_hash(args.proof),
                runtime_sha256=file_hash(args.output / 'runtime.json'), admission_only=args.admission_only,
                completed_cases=completed, error=error, source_hashes=hashes))
    finally:
        gs.destroy()


if __name__ == '__main__':
    main()
