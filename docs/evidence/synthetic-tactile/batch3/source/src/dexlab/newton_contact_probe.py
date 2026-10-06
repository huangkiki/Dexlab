"""Finite native XPBD sphere-plane observations; no surrogate or tuning loop."""
import argparse
import hashlib
import json
import math
import time
from importlib.metadata import version
from pathlib import Path


def run(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / 'runner.py').write_bytes(source)
    record = {'schema': 1, 'completed': False, 'episodes': [],
              'source_sha256': hashlib.sha256(source).hexdigest(),
              'dt_s': .001, 'steps': 1000, 'mass_kg': .1, 'radius_m': .05,
              'initial_height_m': .1, 'gravity_m_s2': -9.81,
              'device': 'cpu', 'precision': 'float32',
              'solver': {'name': 'SolverXPBD', 'iterations': 4,
                         'rigid_contact_relaxation': .8,
                         'rigid_contact_con_weighting': True,
                         'enable_restitution': False},
              'scope': 'Primitive development admission, not SDF, grasp, hardware or speed ranking'}
    started = time.perf_counter()
    try:
        import newton
        import warp as wp
        record['versions'] = {name: version(name) for name in ('newton', 'warp-lang', 'numpy')}
        if record['versions']['newton'] != '1.6.1' or record['versions']['warp-lang'] != '1.18.0':
            raise RuntimeError('Requires official Newton 1.6.1 and Warp 1.18.0')
        wp.init()
        with wp.ScopedDevice('cpu'):
            for case in ('support', 'support-repeat', 'collision-disabled'):
                builder = newton.ModelBuilder(gravity=(0., 0., -9.81))
                cfg = newton.ModelBuilder.ShapeConfig(
                    density=.1 / (4 * math.pi * .05**3 / 3), mu=0.,
                    mu_torsional=0., mu_rolling=0., ka=0., margin=0.,
                    restitution=0., collision_group=0 if case == 'collision-disabled' else 1)
                builder.add_ground_plane(cfg=newton.ModelBuilder.ShapeConfig(
                    mu=0., mu_torsional=0., mu_rolling=0., ka=0., margin=0., restitution=0.))
                body = builder.add_body(xform=wp.transform(wp.vec3(0., 0., .1), wp.quat_identity()))
                builder.add_shape_sphere(body, radius=.05, cfg=cfg)
                model = builder.finalize(device='cpu')
                model.request_contact_attributes('force')
                pipeline = newton.CollisionPipeline(model)
                contacts = pipeline.contacts()
                solver = newton.solvers.SolverXPBD(model, iterations=4,
                            rigid_contact_relaxation=.8, rigid_contact_con_weighting=True,
                            enable_restitution=False)
                current, following = model.state(), model.state()
                control = model.control()
                newton.eval_fk(model, model.joint_q, model.joint_qd, current)
                episode = {'case': case, 'rows': [], 'body_index': body,
                           'shape_body': model.shape_body.numpy().tolist(),
                           'observed_mass_kg': float(model.body_mass.numpy()[body]),
                           'shape_scale': model.shape_scale.numpy().tolist(),
                           'shape_transform': model.shape_transform.numpy().tolist(),
                           'shape_type': model.shape_type.numpy().tolist(),
                           'shape_mu': model.shape_material_mu.numpy().tolist(),
                           'shape_margin': model.shape_margin.numpy().tolist(),
                           'initial_q': current.body_q.numpy()[body].tolist(),
                           'initial_qd': current.body_qd.numpy()[body].tolist()}
                record['episodes'].append(episode)
                for step in range(1, 1001):
                    current.clear_forces()
                    pipeline.collide(current, contacts)
                    solver.step(current, following, control, contacts, .001)
                    solver.update_contacts(contacts)
                    count = int(contacts.rigid_contact_count.numpy()[0])
                    if count < 0 or count > contacts.rigid_contact_max:
                        raise RuntimeError('Invalid or overflowing contact count')
                    episode['rows'].append({
                        'step': step, 'q': following.body_q.numpy()[body].tolist(),
                        'qd': following.body_qd.numpy()[body].tolist(),
                        'shape0': contacts.rigid_contact_shape0.numpy()[:count].tolist(),
                        'shape1': contacts.rigid_contact_shape1.numpy()[:count].tolist(),
                        'force': contacts.force.numpy()[:count].tolist()})
                    current, following = following, current
        record['completed'] = True
    except Exception as error:
        record['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        record['wall_s'] = time.perf_counter() - started
        (output / 'record.json').write_text(json.dumps(record, indent=2, allow_nan=True) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    run(parser.parse_args().output)
