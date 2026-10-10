"""Record official LIBERO action-driven dynamics; render saved states separately."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import time

from dexlab.libero_workflow import (TASK, file_hash, observation_difference,
                                    relocate_assets, settle_observation)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def model_record(env, object_body):
    import mujoco
    model = env.sim.model._model
    names = lambda kind, n: [mujoco.mj_id2name(model, kind, i) for i in range(n)]
    options = {key: getattr(model.opt, key) for key in
               ('timestep', 'iterations', 'tolerance', 'ls_iterations', 'ls_tolerance',
                'noslip_iterations', 'noslip_tolerance', 'integrator', 'solver', 'cone',
                'impratio', 'disableflags', 'enableflags') if hasattr(model.opt, key)}
    return {'options': options, 'gravity': model.opt.gravity.tolist(),
            'object_body_id': object_body, 'body_names': names(mujoco.mjtObj.mjOBJ_BODY, model.nbody),
            'geom_names': names(mujoco.mjtObj.mjOBJ_GEOM, model.ngeom),
            'actuator_names': names(mujoco.mjtObj.mjOBJ_ACTUATOR, model.nu),
            'arrays': {key: getattr(model, key).tolist() for key in
                       ('body_mass', 'body_inertia', 'body_ipos', 'body_iquat', 'body_parentid',
                        'geom_bodyid', 'geom_type', 'geom_size', 'geom_pos', 'geom_quat',
                        'geom_friction', 'geom_condim', 'geom_solref', 'geom_solimp',
                        'geom_contype', 'geom_conaffinity', 'geom_margin', 'geom_gap',
                        'geom_solmix', 'geom_priority', 'pair_solref', 'pair_solimp',
                        'actuator_ctrlrange', 'actuator_forcerange', 'actuator_gainprm',
                        'actuator_biasprm', 'actuator_gear', 'dof_damping')},
            'controller': {key: (getattr(env.robots[0].controller, key).tolist()
                                if hasattr(getattr(env.robots[0].controller, key), 'tolist')
                                else getattr(env.robots[0].controller, key))
                           for key in ('kp', 'kv', 'damping_ratio', 'input_min', 'input_max',
                                       'output_min', 'output_max', 'control_dim', 'policy_freq')
                           if hasattr(env.robots[0].controller, key)},
            'control_freq': env.control_freq, 'model_timestep': env.model_timestep,
            'control_timestep': env.control_timestep}


def contact_record(sim, body_ids, origin):
    import mujoco
    import numpy as np
    model, data = sim.model._model, sim.data._data
    rows, force, torque = [], np.zeros(3), np.zeros(3)
    finger_normal = 0.
    for index in range(data.ncon):
        contact = data.contact[index]
        in1, in2 = int(model.geom_bodyid[contact.geom1]) in body_ids, int(model.geom_bodyid[contact.geom2]) in body_ids
        if in1 == in2:
            continue
        local = np.zeros(6)
        mujoco.mj_contactForce(model, data, index, local)
        world = (1 if in2 else -1) * contact.frame.reshape(3, 3).T @ local[:3]
        moment = (1 if in2 else -1) * contact.frame.reshape(3, 3).T @ local[3:]
        other = contact.geom1 if in2 else contact.geom2
        other_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, other) or ''
        finger = 'finger' in other_name
        if finger:
            finger_normal += float(local[0])
        force += world
        torque += np.cross(contact.pos - origin, world) + moment
        rows.append({'geom1': int(contact.geom1), 'geom2': int(contact.geom2),
                     'position': contact.pos.tolist(), 'frame': contact.frame.tolist(),
                     'distance': float(contact.dist), 'dim': int(contact.dim),
                     'friction': contact.friction.tolist(), 'solref': contact.solref.tolist(),
                     'solimp': contact.solimp.tolist(),
                     'effective_timeconst_s': float(max(contact.solref[0], 2 * model.opt.timestep))
                         if contact.solref[0] > 0 and not model.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_REFSAFE)
                         else float(contact.solref[0]),
                     'local_wrench': local.tolist(),
                     'world_force_on_object': world.tolist(), 'finger': finger})
    return rows, force, torque, finger_normal


def run(payload, output):
    import h5py
    import mujoco
    import numpy as np
    import robosuite
    from libero.libero.envs import TASK_MAPPING

    actual_versions = {name: importlib.metadata.version(name) for name in payload['runtime_versions']}
    if actual_versions != payload['runtime_versions']:
        raise ValueError('Frozen native dependency versions changed')
    output = Path(output)
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    with h5py.File(payload['dataset'], 'r') as dataset:
        data = dataset['data']
        metadata = json.loads(data.attrs['env_args'])
        demo = data[payload['demo']]
        actions = demo['actions'][:]
        initial = demo['states'][0]
        original_xml = demo.attrs['model_file']
        expected_bddl = data.attrs.get('bddl_file_content')
        task_identity = str(data.attrs['bddl_file_name'])
        problem_info = json.loads(data.attrs['problem_info'])
        dataset_states = demo['states'][:]
    if actions.ndim != 2 or actions.shape[1] != 7 or not np.isfinite(actions).all():
        raise ValueError('Expected finite native seven-dimensional actions')
    bddl = Path(payload['libero_root']) / f'libero/libero/bddl_files/libero_object/{TASK}.bddl'
    if not task_identity.endswith(f'libero_object/{TASK}.bddl'):
        raise ValueError('Dataset identifies a different task')
    if problem_info['language_instruction'] != 'pick up the cream cheese and place it in the basket':
        raise ValueError('Dataset language instruction differs')
    if expected_bddl is not None and bddl.read_text().strip() != expected_bddl.strip():
        raise ValueError('Dataset and native task definitions differ')
    xml, asset_sources = relocate_assets(original_xml, payload['libero_root'], Path(robosuite.__file__).parent)
    (output / 'input-model.xml').write_text(original_xml)
    (output / 'relocated-model.xml').write_text(xml)
    write_json(output / 'assets.json', asset_sources)
    kwargs = dict(metadata['env_kwargs'])
    kwargs.update(bddl_file_name=str(bddl), has_renderer=False,
                  has_offscreen_renderer=False, use_camera_obs=False)
    env = TASK_MAPPING[metadata['problem_name']](**kwargs)
    candidate = payload['candidate']
    action_rows, physics_rows, contacts = [], [], []
    states, timestamps, success, measurements, targets = [], [], [], [], []
    controls, actuator_forces, qfrc_actuator = [], [], []
    native_seconds = 0.
    try:
        np.random.seed(payload['seed'])
        env.reset()
        env.reset_from_xml_string(xml)
        env.sim.reset()
        env.sim.set_state_from_flattened(initial)
        env.sim.forward()
        env._post_process()
        env._update_observables(force=True)
        initial_obs = env._get_observations()
        model, data = env.sim.model._model, env.sim.data._data
        body = int(env.obj_body_id['cream_cheese_1'])
        native_before = model_record(env, body)
        model.opt.timestep *= candidate['timestep_scale']
        env.model_timestep = float(model.opt.timestep)
        floor = candidate.get('solref_floor_s', 0.)
        for refs in (model.geom_solref, model.pair_solref):
            positive = refs[:, 0] > 0
            refs[positive, 0] = np.maximum(refs[positive, 0], floor)
        effective = model_record(env, body)
        write_json(output / 'parameters-before.json', native_before)
        write_json(output / 'parameters-effective.json', effective)
        (output / 'effective-model.xml').write_text(env.sim.model.get_xml())
        joint = int(model.body_jntadr[body])
        if joint < 0 or model.jnt_type[joint] != mujoco.mjtJoint.mjJNT_FREE:
            raise ValueError('The native target must have a free joint')
        qadr, dadr = int(model.jnt_qposadr[joint]), int(model.jnt_dofadr[joint])
        bodies = {body}
        for index in range(body + 1, model.nbody):
            if int(model.body_parentid[index]) in bodies:
                bodies.add(index)
        original_step = env.sim.step
        t0 = float(data.time)
        current_action = -1

        def record_step(*args, **kw):
            nonlocal native_seconds
            t = float(data.time)
            velocity0 = data.qvel[dadr:dadr + 3].copy()
            position0 = data.qpos[qadr:qadr + 3].copy()
            quat0 = data.qpos[qadr + 3:qadr + 7].copy()
            omega0 = data.qvel[dadr + 3:dadr + 6].copy()
            begin = time.perf_counter()
            original_step(*args, **kw)
            native_seconds += time.perf_counter() - begin
            rows, force, torque, finger_normal = contact_record(env.sim, bodies, position0)
            physics_rows.append([t, float(data.time), current_action,
                                 *velocity0, *data.qvel[dadr:dadr + 3], *force, *torque,
                                 finger_normal, max([max(0., -c['distance']) for c in rows], default=0.),
                                 len(rows), *quat0, *data.qpos[qadr + 3:qadr + 7],
                                 *omega0, *data.qvel[dadr + 3:dadr + 6]])
            contacts.append({'time_s': t, 'state_after_s': float(data.time), 'contacts': rows})
            controls.append(data.ctrl.copy())
            actuator_forces.append(data.actuator_force.copy())
            qfrc_actuator.append(data.qfrc_actuator.copy())

        if candidate['instrument']:
            env.sim.step = record_step
        audit = None
        if candidate['mode'] == 'observation-audit':
            fresh = settle_observation(env, initial_obs)
            audit = {'initial_time_s': t0, 'fresh_time_s': float(data.time),
                     'difference': observation_difference(initial_obs, fresh),
                     'policy_actions_evaluated': False,
                     'scope': 'native proprioception; no compatible learned checkpoint'}
        else:
            for current_action, action in enumerate(actions):
                before = float(data.time)
                obs, _, done, _ = env.step(action)
                action_rows.append([before, float(data.time), *action])
                states.append(env.sim.get_state().flatten())
                timestamps.append(float(data.time))
                success.append(bool(env._check_success()))
                measurements.append([float(data.time) - float(model.opt.timestep),
                                     *obs['cream_cheese_1_pos'], *obs['robot0_eef_pos'],
                                     *obs['cream_cheese_1_to_robot0_eef_pos'], *obs['robot0_gripper_qpos']])
                controller = env.robots[0].controller
                targets.append([*controller.goal_pos, *controller.goal_ori.reshape(-1)])
                # Full source action sequence, including release; never reset after success.
        env.sim.step = original_step
        np.savez_compressed(output / 'trajectory.npz',
                            state=np.asarray(states), time=np.asarray(timestamps),
                            initial=initial, dataset_state=dataset_states,
                            measurements=np.asarray(measurements), controller_targets=np.asarray(targets),
                            actions=np.asarray(action_rows), success=np.asarray(success),
                            physics=np.asarray(physics_rows), controls=np.asarray(controls),
                            actuator_force=np.asarray(actuator_forces), qfrc_actuator=np.asarray(qfrc_actuator))
        with (output / 'contacts.jsonl').open('w') as stream:
            for row in contacts:
                stream.write(json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n')
        if audit is not None:
            write_json(output / 'observation-audit.json', audit)
        parameters_after = model_record(env, body)
        write_json(output / 'parameters-after.json', parameters_after)
        receipt = {'schema_version': 1, 'status': 'completed', 'task': TASK,
                   'demo': payload['demo'], 'candidate': candidate,
                   'split': 'development' if payload['demo'] in payload['development'] else 'heldout',
                   'versions': {p: importlib.metadata.version(p) for p in
                                ('libero', 'robosuite', 'mujoco', 'numpy', 'numba', 'h5py')},
                   'source_commit': payload['upstream_commit'], 'input_sha256': payload['inputs'],
                   'effective_parameters_unchanged': parameters_after == effective,
                   'native_success_any': any(success), 'native_success_final': bool(success[-1]) if success else None,
                   'actions_executed': len(action_rows), 'expected_actions': len(actions),
                   'initial_time_s': t0, 'final_time_s': float(data.time),
                   'native_step_seconds': native_seconds if candidate['instrument'] else None,
                   'wall_seconds': time.monotonic() - started,
                   'physics_columns': ['force_time', 'state_time', 'action_index', 'vx0', 'vy0', 'vz0',
                                       'vx1', 'vy1', 'vz1', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz',
                                       'finger_normal', 'overlap', 'contacts',
                                       'qw0', 'qx0', 'qy0', 'qz0', 'qw1', 'qx1', 'qy1', 'qz1',
                                       'wx0', 'wy0', 'wz0', 'wx1', 'wy1', 'wz1'],
                   'force_epoch': 'mj_step constraints before integration; state after integration',
                   'measurement_epoch': 'native derived body/site observations at last pre-integration substep',
                   'measurement_columns': ['time', 'object_x', 'object_y', 'object_z', 'eef_x', 'eef_y', 'eef_z', 'relative_x', 'relative_y', 'relative_z', 'finger_q0', 'finger_q1'],
                   'initialization': 'official dataset states[0]; controller reset via native reset_from_xml_string',
                   'task_definition_provenance': {'dataset_task_id': task_identity,
                       'pinned_bddl_sha256': file_hash(bddl),
                       'historical_bddl_embedded': expected_bddl is not None},
                   'diagnostic_limits': {'overlap_m': .001, 'momentum_p99_weight_fraction': .05},
                   'mid_episode_restore_qualified': False, 'policy_closed_loop_evaluated': False,
                   'object_qpos_adr': qadr, 'object_dof_adr': dadr,
                   'object_body_ids': sorted(bodies),
                   'files': {p.name: file_hash(p) for p in output.iterdir() if p.is_file()}}
        write_json(output / 'run.json', receipt)
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run(json.loads(args.input.read_text()), args.output)


if __name__ == '__main__':
    main()
