"""Native Newton rigid incline observations, with solver-specific force readback."""

import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import signal
import time

import numpy as np

from dexlab.cloth_engines import package_identity


PROFILES = {
    'xpbd': ('SolverXPBD', {'iterations': 100}),
    'semiimplicit': ('SolverSemiImplicit', {'angular_damping': 0.}),
    'featherstone': ('SolverFeatherstone', {'angular_damping': 0.}),
    'vbd-legacy': ('SolverVBD', {'iterations': 100, 'rigid_compliant_alm': False}),
    'vbd-compliant': ('SolverVBD', {'iterations': 100, 'rigid_compliant_alm': True}),
    'kamino-padmm': ('SolverKamino', {}),
    'kamino-dvi': ('SolverKamino', {}),
}


def write_json(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_value(value):
    return value.item() if isinstance(value, np.generic) else value


def array_value(value):
    return None if value is None else value.numpy().tolist()


def checkpoint(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


class NewtonIncline:
    """Own a single free cube; initialization is the only state-writing phase."""

    def __init__(self, protocol, case):
        import newton
        import warp as wp

        self.wp = wp
        self.profile = protocol['profile']
        name, options = PROFILES[self.profile]
        cls = getattr(newton.solvers, name)
        builder = newton.ModelBuilder(gravity=(0., 0., -protocol['gravity_m_s2']))
        builder.begin_world()
        cls.register_custom_attributes(builder)
        angle = np.deg2rad(case['angle_deg'])
        normal = np.array([np.sin(angle), 0., np.cos(angle)])
        half = protocol['side_m'] / 2
        quat = wp.quat_from_axis_angle(wp.vec3(0, 1, 0), float(angle))
        cfg = newton.ModelBuilder.ShapeConfig(
            density=protocol['density_kg_m3'], mu=case['friction'],
            mu_torsional=0., mu_rolling=0., ka=0., margin=0., gap=.01,
            restitution=0., ke=2500., kd=100., kf=1000.)
        builder.add_shape_plane(plane=(*normal, 0.), width=0., length=0., cfg=cfg)
        # add_body already creates a FREE joint. SemiImplicit's joint-force
        # branch uses an inaccessible temporary force buffer; a stand-alone
        # link has the same six free-body states and exposes its applied force.
        add_body = builder.add_link if self.profile == 'semiimplicit' else builder.add_body
        self.body = add_body(xform=wp.transform(wp.vec3(*(half * normal)), quat))
        cfg.collision_group = 0 if case.get('negative_no_floor', False) else 1
        builder.add_shape_box(self.body, hx=half, hy=half, hz=half, cfg=cfg)
        builder.end_world()
        builder.color()
        self.model = model = builder.finalize(device='cpu')
        model.request_contact_attributes('force')
        self.pipeline = newton.CollisionPipeline(model)
        self.contacts = self.pipeline.contacts()
        options = dict(options)
        if self.profile.startswith('kamino'):
            options['config'] = cls.Config(dynamics_solver=self.profile.split('-')[1])
        self.solver = cls(model, **options)
        self.current, self.following = model.state(), model.state()
        self.control = model.control()
        newton.eval_fk(model, model.joint_q, model.joint_qd, self.current)
        self.shape_body = model.shape_body.numpy()
        self.admission = {
            'model': {key: array_value(getattr(model, key)) for key in (
                'body_mass', 'body_inertia', 'body_com', 'body_q', 'body_flags',
                'shape_transform', 'shape_type', 'shape_scale', 'shape_body',
                'shape_material_mu', 'shape_material_ke', 'shape_material_kd',
                'shape_material_kf', 'shape_material_ka', 'shape_material_restitution',
                'shape_material_mu_torsional', 'shape_material_mu_rolling',
                'shape_gap', 'shape_margin', 'shape_collision_group', 'body_world',
                'joint_type', 'joint_target_ke', 'joint_target_kd', 'joint_damping', 'gravity')},
            'counts': {key: getattr(model, key) for key in (
                'body_count', 'joint_count', 'joint_dof_count', 'joint_coord_count',
                'articulation_count', 'world_count', 'shape_count', 'particle_count')},
            'solver_scalars': {key: json_value(value) for key, value in vars(self.solver).items()
                               if isinstance(value, (str, bool, int, float, np.generic))},
            'contact_capacity': self.contacts.rigid_contact_max,
            'initial_state': self.state(0.).tolist(),
            'control_joint_f': array_value(self.control.joint_f),
        }
        if self.profile.startswith('kamino'):
            self.admission['kamino_config'] = asdict(self.solver._config)

    def state(self, timestamp):
        pose = self.current.body_q.numpy()[self.body].astype(float)
        velocity = self.current.body_qd.numpy()[self.body].astype(float)
        return np.r_[timestamp, pose[:3], pose[6], pose[3:6], velocity]

    def step(self, step, dt):
        """Preserve contact geometry before solvers mutate their input state."""
        c, solver, wp = self.contacts, self.solver, self.wp
        self.current.clear_forces()
        self.pipeline.collide(self.current, c)
        count = int(c.rigid_contact_count.numpy()[0])
        if not 0 <= count <= c.rigid_contact_max:
            raise ValueError('Native contact capacity overflow')
        row = {'interval_start_s': step * dt, 'interval_end_s': (step + 1) * dt,
               'pre_state': self.state(step * dt).tolist(),
               'contacts': {key: getattr(c, 'rigid_contact_' + key).numpy()[:count].tolist()
                            for key in ('shape0', 'shape1', 'normal', 'point0', 'point1',
                                        'offset0', 'offset1', 'margin0', 'margin1')}}
        previous = None
        if self.profile.startswith('vbd'):
            previous = wp.clone(self.current.body_q if step == 0 else solver.body_q_prev)
        physics_started = time.perf_counter()
        solver.step(self.current, self.following, self.control, c, dt)
        physics_s = time.perf_counter() - physics_started
        if self.profile.startswith('vbd'):
            b0, b1, p0, p1, force, size = solver.collect_rigid_contact_forces(
                self.following.body_q, previous, c, dt)
            if int(size.numpy()[0]) != count:
                raise ValueError('VBD changed external contact count')
            force = force.numpy()[:count].astype(float)
            body0, body1 = b0.numpy()[:count], b1.numpy()[:count]
            signs = (body1 == self.body).astype(int) - (body0 == self.body).astype(int)
            total = np.sum(signs[:, None] * force, axis=0)
            row['force_readback'] = dict(convention='force_on_body1', force=force.tolist(),
                                         body0=body0.tolist(), body1=body1.tolist(),
                                         point0_world=p0.numpy()[:count].tolist(),
                                         point1_world=p1.numpy()[:count].tolist(),
                                         last_primal_body_force=solver.body_forces.numpy().tolist())
        elif self.profile == 'xpbd' or self.profile.startswith('kamino'):
            solver.update_contacts(c, self.current)
            if int(c.rigid_contact_count.numpy()[0]) != count:
                raise ValueError('Solver changed external contact count')
            force = c.force.numpy()[:count].astype(float)
            shape0, shape1 = (np.array(row['contacts'][key], dtype=int) for key in ('shape0', 'shape1'))
            signs = ((self.shape_body[shape0] == self.body).astype(int)
                     - (self.shape_body[shape1] == self.body).astype(int))
            total = np.sum(signs[:, None] * force[:, :3], axis=0)
            row['force_readback'] = dict(convention='wrench_on_shape0', force=force.tolist())
        else:
            # Featherstone eval_rigid_tau replaces body_f_ext with the negative
            # wrench about its solve origin. Its linear part must be negated.
            wrench = (solver.body_f_ext if self.profile == 'featherstone'
                      else self.current.body_f).numpy()[self.body].astype(float)
            total = (-1 if self.profile == 'featherstone' else 1) * wrench[:3]
            row['force_readback'] = dict(
                convention='negative_solve_wrench' if self.profile == 'featherstone' else 'com_wrench',
                wrench=wrench.tolist(), per_contact_force=None)
        self.current, self.following = self.following, self.current
        state = self.state((step + 1) * dt)
        row.update(state=state.tolist(), net_force=total.tolist(), native_step_wall_s=physics_s)
        return row


def run(protocol_path, proof_path, output, admission_only=False):
    import warp as wp
    from dexlab.newton_incline_score import validate_admission, validate_protocol

    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    proof = json.loads(proof_path.read_text())
    validate_protocol(protocol)
    if proof['source_commit'] != protocol['source_commit']:
        raise ValueError('Official source identity differs from protocol')
    if not admission_only and protocol['recorder_sha256'] != sha256(Path(__file__)):
        raise ValueError('Recorder differs from frozen protocol')
    (output / 'manifest.json').write_bytes(protocol_path.read_bytes())
    (output / 'official-proof.json').write_bytes(proof_path.read_bytes())
    (output / 'recorder.py').write_bytes(Path(__file__).read_bytes())
    wp.config.kernel_cache_dir = str(output.parent / 'kernel-cache')
    wp.init()
    identities = {}
    for name in ('newton', 'warp-lang'):
        identity = package_identity(name)
        identity.pop('installation_origin', None)
        if identity != proof['packages'][name]['identity']:
            raise ValueError('Official package identity differs')
        identities[name] = identity
    campaign = dict(profile=protocol['profile'], admission_only=admission_only,
                    packages=identities, protocol_sha256=sha256(protocol_path),
                    proof_sha256=sha256(proof_path), recorder_sha256=sha256(Path(__file__)),
                    cases=[], clock='scheduled step intervals; no separate native clock API',
                    device='cpu', precision='float32', engine_patches=False, state='running')
    write_json(output / 'campaign.json', campaign)
    with wp.ScopedDevice('cpu'):
        for case in protocol['cases']:
            directory = output / case['id']
            directory.mkdir()
            meta = dict(case=case, completed_steps=0, attempted_steps=0,
                        state_writes_after_initialization=0, error=None, native_step_wall_s=0.)
            started = time.perf_counter()
            interrupted = False
            try:
                scene = NewtonIncline(protocol, case)
                write_json(directory / 'admission.json', scene.admission)
                validate_admission(protocol, case, scene.admission)
                if not admission_only and sha256(directory / 'admission.json') != protocol['admission_sha256'][case['id']]:
                    raise ValueError('Effective parameters differ from frozen admission')
                meta['setup_s'] = time.perf_counter() - started
                with gzip.open(directory / 'steps.jsonl.gz', 'xt') as stream:
                    if not admission_only:
                        for step in range(round(protocol['duration_s'] / case['timestep'])):
                            meta['attempted_steps'] += 1
                            row = scene.step(step, case['timestep'])
                            # Preserve a nonfinite native observation as a failed
                            # raw row; it can never enter independent acceptance.
                            stream.write(json.dumps(row, allow_nan=True) + '\n')
                            meta['native_step_wall_s'] += row['native_step_wall_s']
                            if not np.isfinite(np.r_[row['state'], row['net_force']]).all():
                                raise ValueError('Nonfinite native state or force')
                            meta['completed_steps'] += 1
                if not admission_only and meta['completed_steps'] == 0:
                    raise ValueError('No physical observations')
            except (Exception, KeyboardInterrupt) as error:
                meta['error'] = f'{type(error).__name__}: {error}'
                interrupted = isinstance(error, KeyboardInterrupt)
            meta['wall_s'] = time.perf_counter() - started
            meta['hashes'] = {p.name: sha256(p) for p in directory.iterdir()}
            write_json(directory / 'metadata.json', meta)
            campaign['cases'].append(meta)
            if interrupted:
                campaign['state'] = 'interrupted'
            checkpoint(output / 'campaign.json', campaign)
            if interrupted:
                raise KeyboardInterrupt('Interrupted observations preserved')
    campaign['state'] = 'completed'
    checkpoint(output / 'campaign.json', campaign)
    if any(case['error'] for case in campaign['cases']):
        raise RuntimeError('One or more native cases failed; all observations preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--admission-only', action='store_true')
    args = parser.parse_args()
    def interrupt(signum, frame):
        raise KeyboardInterrupt(f'Signal {signum}')
    signal.signal(signal.SIGTERM, interrupt)
    run(args.protocol, args.proof, args.output, args.admission_only)
