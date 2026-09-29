"""Development-only native PhysX fixture probes; not a frozen benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np

from dexlab.physx_baseline import write_json
from unisim.dr.types import ModelSourceDescriptor
from unisim.entities import EntityInitialState, SceneEntitySpec
from unisim.factory import create_backend
from unisim.scene import SceneCfg


def scene_files(output, mode, mass, friction):
    directory = output / 'scene'
    directory.mkdir()
    option = '<option gravity="0 0 -9.81" timestep="0.001"/>'
    entities = []
    for name, direction in [('left', 1), ('right', -1)]:
        if mode == 'drive' and name == 'right':
            continue
        actuator = ('<actuator><position name="drive" joint="slide" kp="500" kv="10" '
                    'ctrlrange="-0.02 0.02" forcerange="-2 2"/></actuator>') if mode == 'drive' else ''
        xml = directory / f'{name}.xml'
        xml.write_text(
            f'<mujoco model="{name}">{option}<worldbody><body name="base">'
            '<inertial pos="0 0 0" mass="0.1" diaginertia="0.001 0.001 0.001"/>'
            '<body name="pad"><inertial pos="0 0 0" mass="0.1" '
            'diaginertia="0.000074166667 0.000054166667 0.000021666667"/>'
            f'<joint name="slide" type="slide" axis="{direction} 0 0" '
            f'range="-0.02 0.02" damping="{0 if mode == "drive" else 2}"/>'
            f'<geom name="surface" type="box" size="0.005 0.025 0.04" '
            f'friction="{friction} 0 0" condim="3"/>'
            f'</body></body></worldbody>{actuator}</mujoco>\n'
        )
        entities.append(SceneEntitySpec(
            name, ModelSourceDescriptor(str(xml.resolve())), kind='articulation', root_mode='fixed',
            initial_state=EntityInitialState(position=(-direction * 0.0152, 0.0, 0.2)),
            gravity_disabled=True,
        ))
    fragments = []
    if mode == 'pinch':
        xml = directory / 'object.xml'
        ixx = mass * (0.01**2 + 0.03**2) / 3
        izz = 2 * mass * 0.01**2 / 3
        xml.write_text(
            f'<mujoco model="object">{option}<worldbody><body name="body">'
            '<freejoint name="root"/>'
            f'<inertial pos="0 0 0" mass="{mass}" diaginertia="{ixx} {ixx} {izz}"/>'
            f'<geom name="surface" type="box" size="0.01 0.01 0.03" '
            f'friction="{friction} 0 0" condim="3"/>'
            '</body></worldbody></mujoco>\n'
        )
        entities.append(SceneEntitySpec(
            'object', ModelSourceDescriptor(str(xml.resolve())), kind='rigid', root_mode='floating',
            initial_state=EntityInitialState(position=(0.0, 0.0, 0.2)),
        ))
        sensors = directory / 'sensors.xml'
        sensors.write_text('<mujoco><sensor>' + ''.join(
            f'<contact name="{side}_force" geom1="object/surface" geom2="{side}/surface" '
            'data="force" reduce="netforce"/>' for side in ('left', 'right')
        ) + '</sensor></mujoco>\n')
        fragments = [str(sensors.resolve())]
    return SceneCfg(entity_assets=tuple(entities), fragment_files=fragments)


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve()
    (output / 'source.py').write_bytes(source.read_bytes())
    receipt = {'mode': args.mode, 'mass': args.mass, 'friction': args.friction,
               'pad_force_n': args.force, 'timestep': 0.001,
               'scope': 'development probe; ideal prismatic fixture, not robot qualification',
               'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'gravity_compensation': 'object +mg for t<0.5s only; zero thereafter',
               'release': 'reverse pad forces at t=2.5s; no pose reset or attachment',
               'status': 'preparing'}
    write_json(output / 'run.json', receipt)
    rows = []
    backend = None
    try:
        backend = create_backend('isaacsim', scene_files(output, args.mode, args.mass, args.friction),
                                 num_envs=1, sim_dt=0.001, isaacsim_worker_timeout_s=120,
                                 isaacsim_solver_position_iteration_count=8,
                                 isaacsim_solver_velocity_iteration_count=2,
                                 isaacsim_contact_offset=0.001, isaacsim_rest_offset=0.0)
        backend.materialize()
        write_json(output / 'layout.json', backend.get_scene_layout().to_dict())
        write_json(output / 'import-report.json', backend.get_import_report().to_dict())
        names = ['left/pad'] if args.mode == 'drive' else ['left/pad', 'right/pad', 'object/body']
        ids = backend.get_body_ids(names)
        controls = np.zeros((1, backend.num_actuators), dtype=np.float32)
        count = 2000 if args.mode == 'drive' else 3500
        receipt.update(status='running', body_names=names,
                       mass_readback=backend.get_body_mass().tolist(),
                       friction_readback=backend.get_geom_friction().tolist())
        write_json(output / 'run.json', receipt)
        start = time.perf_counter()
        for step in range(count):
            t = step * 0.001
            force = np.zeros((1, len(ids), 3), dtype=np.float32)
            if args.mode == 'drive':
                controls[0, 0] = 0.01 if t < 1.5 else 0.0
                force[0, 0, 0] = -1.0 if 0.5 <= t < 1.0 else 0.0
            else:
                normal = args.force if t < 2.5 else -2.0
                force[0, 0, 0] = normal
                force[0, 1, 0] = -normal
                force[0, 2, 2] = args.mass * 9.81 if t < 0.5 else 0.0
            backend.apply_body_force(ids, force)
            backend.step(controls)
            contact = np.zeros((2, 3)) if args.mode == 'drive' else np.array([
                backend.get_sensor_data('left_force')[0], backend.get_sensor_data('right_force')[0]])
            rows.append({'time': (step + 1) * 0.001,
                         'position': backend.get_body_pos_w(ids)[0].copy(),
                         'quaternion': backend.get_body_quat_w(ids)[0].copy(),
                         'velocity': backend.get_body_lin_vel_w(ids)[0].copy(),
                         'q': backend.get_dof_pos()[0].copy(),
                         'dq': backend.get_dof_vel()[0].copy(),
                         'external_force': force[0].copy(), 'control': controls[0].copy(),
                         'contact_normal_force': contact.copy()})
            if step % 500 == 499:
                print(round(t + 0.001, 3), rows[-1]['position'].tolist(), contact.tolist(), flush=True)
        receipt.update(status='completed', step_seconds=time.perf_counter()-start)
    except Exception:
        receipt.update(status='error', error=traceback.format_exc())
    finally:
        if backend is not None:
            try:
                backend.close(); backend.cleanup_scene_assets()
            except Exception:
                receipt['cleanup_error'] = traceback.format_exc()
        archive = {name: np.array([row[name] for row in rows]) for name in rows[0]} if rows else {}
        np.savez_compressed(output / 'states.npz', **archive)
        receipt['archive_sha256'] = hashlib.sha256((output / 'states.npz').read_bytes()).hexdigest()
        receipt['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == receipt['source_sha256']
        write_json(output / 'run.json', receipt)
    print(json.dumps(receipt, indent=2))
    return receipt['status'] == 'completed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['drive', 'pinch'], required=True)
    parser.add_argument('--mass', type=float, default=0.2)
    parser.add_argument('--friction', type=float, default=0.3)
    parser.add_argument('--force', type=float, default=4.0)
    parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(0 if run(parser.parse_args()) else 1)
