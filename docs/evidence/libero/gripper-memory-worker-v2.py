"""Private native intervention: gripper command memory with observed controls."""
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import sys

import numpy as np

from dexlab.libero_bindings import bind_task
from dexlab.libero_demo import load_demo
from dexlab.libero_execute import execute_actions, source_hashes, NUMERICAL_ENVIRONMENT
from dexlab.libero_initialization import initialize_demo, _controller_snapshot
from dexlab.libero_inputs import _source_identity
from dexlab.libero_workflow import file_hash, relocate_assets
from dexlab.migration_budget import json_bytes, publish

root, case_id, output = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
read = lambda p: json.loads(Path(p).read_bytes())
plan = read(root / 'plan.json')
case = next(c for c in plan['matrix'] if c['id'] == case_id)
task = next(t for t in plan['tasks'] if t['id'] == case['task'])
payload = task['execution']
assert file_hash(__file__) == plan['worker_sha256']
for item in plan['evidence'] + plan['source_files']:
    assert file_hash(item['path']) == item['sha256']
assert payload['source_sha256'] == source_hashes()
assert {k: importlib.metadata.version(k) for k in payload['runtime_versions']} == payload['runtime_versions']
assert {k: os.environ.get(k) for k in NUMERICAL_ENVIRONMENT} == payload['numerical_environment']
inputs = load_demo(payload['input_dir'], payload['input_manifest_sha256'], payload['demo_id'])
assert inputs['demonstration']['split'] == 'development'
assert inputs['demonstration']['action_count'] == task['actions']
source = Path(payload['libero_root'])
_source_identity(source)
bddl = source / inputs['task']['bddl_path']
assert bddl.read_bytes() == inputs['bddl']
assert file_hash(task['source_npz']) == task['source_npz_sha256']
with np.load(task['source_npz'], allow_pickle=False) as archive:
    source_states = archive['states']
    assert np.array_equal(archive['actions'], inputs['actions'])
    assert np.array_equal(source_states[0], inputs['initial'])

import robosuite
from libero.libero.envs import TASK_MAPPING

output.mkdir(exist_ok=False)
env = None
trace, groups = [], []
report = dict(case_id=case_id, status='failed', intervention=case['intervention'],
              plan_sha256=file_hash(root / 'plan.json'), snapshots={})

def snapshot():
    robot = env.robots[0]
    return dict(flat_state=env.sim.get_state().flatten().tolist(),
                controller=_controller_snapshot(robot.controller, robot.gripper),
                native_ctrl=np.array(env.sim.data.ctrl).tolist(),
                native_qacc_warmstart=np.array(env.sim.data.qacc_warmstart).tolist())

try:
    reference = Path(task['reference'])
    xml, assets = relocate_assets(inputs['model_xml'], source, Path(robosuite.__file__).parent)
    assert xml == (reference / 'raw/relocated-model.xml').read_text()
    assert assets == read(reference / 'raw/assets.json')
    kwargs = dict(inputs['metadata']['env_kwargs'])
    kwargs.update(bddl_file_name=str(bddl), has_renderer=False, has_offscreen_renderer=False, use_camera_obs=False)
    np.random.seed(payload['seed'])
    env = TASK_MAPPING[inputs['metadata']['problem_name']](**kwargs)
    initialization = {}
    initialize_demo(env, xml, inputs['initial'], initialization)
    assert initialization == read(reference / 'raw/initialization.json')
    assert bind_task(env, inputs['task']['definition']) == read(reference / 'raw/bindings.json')
    assert env.sim.model.get_xml() == (reference / 'raw/effective-model.xml').read_text()
    report['initialization'] = initialization
    robot = env.robots[0]
    gripper = robot.gripper
    indices = [env.sim.model.actuator_name2id(name) for name in gripper.actuators]
    ctrl_range = np.array(env.sim.model.actuator_ctrlrange[indices]).copy()
    method_path = Path(inspect.getsourcefile(type(gripper)))
    method_digest = file_hash(method_path)
    assert method_digest in {s['sha256'] for s in plan['source_files']}
    report['native_identity'] = dict(gripper_class=type(gripper).__qualname__,
        gripper_module=type(gripper).__module__, gripper_source_sha256=method_digest,
        gripper_dof=int(gripper.dof), actuators=list(gripper.actuators), actuator_indices=indices,
        actuator_ctrlrange=ctrl_range.tolist(), speed=float(gripper.speed),
        model_timestep_s=float(env.model_timestep), control_timestep_s=float(env.control_timestep))
    assert len(indices) == 2 and int(env.control_timestep / env.model_timestep) == 25
    before = snapshot()
    report['snapshots']['restored'] = before
    if case['intervention'] == 'positive-memory':
        gripper.current_action = np.array([1., -1.])
    elif case['intervention'] == 'negative-memory':
        gripper.current_action = np.array([-1., 1.])
    else:
        assert case['intervention'] == 'observe-only'
    after = snapshot()
    report['snapshots']['before-first-action'] = after
    assert all(before[k] == after[k] for k in ('flat_state', 'native_ctrl', 'native_qacc_warmstart'))
    assert all(before['controller'][k] == after['controller'][k]
               for k in before['controller'] if k != 'gripper_current_action')
    original_format, original_grip = gripper.format_action, robot.grip_action

    def observed_format(action):
        entry = dict(time_s=float(env.sim.data.time), input=np.asarray(action).copy().tolist(),
                     memory_before=gripper.current_action.copy().tolist())
        result = original_format(action)
        entry.update(memory_after=gripper.current_action.copy().tolist(),
                     normalized_output=np.asarray(result).copy().tolist())
        trace.append(entry)
        return result

    def observed_grip(gripper, gripper_action):
        assert gripper is robot.gripper
        count = len(trace)
        result = original_grip(gripper, gripper_action)
        assert len(trace) == count + 1
        trace[-1]['native_actuator_ctrl'] = np.array(env.sim.data.ctrl[indices]).tolist()
        return result

    gripper.format_action, robot.grip_action = observed_format, observed_grip
    markers_all = []
    try:
        for part in (inputs['actions'][:1], inputs['actions'][1:]):
            rows, events, markers = {}, [], []
            groups.append(rows)
            execute_actions(env, part, inputs['task']['definition'], recording=False,
                            rows=rows, events=events, markers=markers)
            assert not events
            markers_all.extend(markers)
            if len(groups) == 1:
                report['snapshots']['after-first-action'] = snapshot()
                report['first_action_format_calls'] = len(trace)
    finally:
        gripper.format_action, robot.grip_action = original_format, original_grip
    arrays = {k: np.asarray(groups[0][k] + groups[1][k]) for k in groups[0]}
    arrays['initial'] = inputs['initial']
    assert np.array_equal(arrays['actions'], inputs['actions'])
    assert arrays['actions'].shape == (task['actions'], 7)
    assert markers_all == read(reference / 'raw/visual-markers.json')
    assert report['first_action_format_calls'] == 25 and len(trace) == task['actions'] * 25
    with (output / 'trajectory.npz').open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    with np.load(reference / 'raw/trajectory.npz', allow_pickle=False) as original:
        assert set(arrays) == set(original.files)
        equal = {k: bool(np.array_equal(v, original[k])) for k, v in arrays.items()}
    report['reference_array_equal'] = equal
    if case['intervention'] == 'observe-only':
        assert all(equal.values()), 'Diagnostic observer changed the complete reference trace'
    assert np.array_equal(arrays['state'][:-1, 0], source_states[1:, 0])
    delta = arrays['state'][:-1] - source_states[1:]
    target = np.linalg.norm(delta[:, task['target_state_translation_indices']], axis=1)
    report['curves'] = dict(target_translation_difference_m=target.tolist(),
        arm_max_coordinate_difference_rad=np.max(np.abs(delta[:, 1:8]), axis=1).tolist(),
        finger_max_coordinate_difference_m=np.max(np.abs(delta[:, 8:10]), axis=1).tolist())
    report.update(status='completed', actions=task['actions'], format_calls=len(trace),
        native_success_any=bool(arrays['done'].any()), native_success_final=bool(arrays['done'][-1]),
        trajectory_sha256=file_hash(output / 'trajectory.npz'),
        scope='Explicit development counterfactual, not a production baseline, original-memory estimate or physical accuracy claim.')
finally:
    publish(output / 'gripper-trace.json', json_bytes(trace))
    report['gripper_trace_sha256'] = file_hash(output / 'gripper-trace.json')
    report['observed_format_calls'] = len(trace)
    publish(output / 'result.json', json_bytes(report))
    if env is not None:
        env.close()
print(json.dumps({k: report[k] for k in ('case_id', 'status', 'native_success_final', 'format_calls')}), flush=True)
