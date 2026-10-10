"""Matched-core diagnostic using an exact framework MJB, outside Isaac/Kit.

This records native state and effective parameters. It does not qualify the
three-task coverage matrix or imply that framework state transfer is equivalent.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def align_inertia_parameters(model, requested):
    """Ablate the four observed import differences; validate before mutation."""
    import numpy as np

    targets = {'body_iquat': model.body_iquat, 'body_inertia': model.body_inertia,
               'body_invweight0': model.body_invweight0,
               'stat.meaninertia': model.stat.meaninertia}
    if requested.keys() != targets.keys():
        raise ValueError('Alignment must contain exactly the four frozen inertia fields')
    before, prepared = {}, {}
    for name, target in targets.items():
        original = target.numpy()
        value = np.asarray(requested[name], dtype=original.dtype)
        if value.shape != original.shape or not np.isfinite(value).all():
            raise ValueError(f'Invalid alignment shape/value: {name}')
        before[name], prepared[name] = original.tolist(), value
    for name, target in targets.items():
        target.assign(prepared[name])
    after = {name: target.numpy().tolist() for name, target in targets.items()}
    if any(not np.array_equal(after[name], value) for name, value in prepared.items()):
        raise ValueError('GPU alignment readback differs from the frozen assignment')
    return {'before': before, 'after': after,
            'scope': 'Explicit model-input alignment, no engine source/binary patch.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--source-case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--warp-cache', type=Path, required=True)
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    protocol = json.loads(raw)
    case = next(row for row in protocol['cases'] if row['id'] == args.case)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'protocol.json').write_bytes(raw)
    write_json(args.output / 'invocation.json', {
        'case': args.case, 'protocol_sha256': hashlib.sha256(raw).hexdigest(),
        'recorder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'runtime_path': 'native matched core; no Newton state synchronization',
    })
    for name, expected in case['source_sha256'].items():
        source = args.source_case / name
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen input changed: {name}')
        shutil.copyfile(source, args.output / name)

    import mujoco
    import mujoco_warp as mjw
    import warp as wp
    from dexlab.mujoco_artifacts import (
        conversion_parameters, parameter_differences,
        warp_model_parameters, warp_execution_options,
    )

    versions = {'mujoco': mujoco.__version__, 'mujoco_warp': mjw.__version__,
                'warp': wp.__version__}
    if versions != protocol['versions'] or mujoco.mj_versionString() != versions['mujoco']:
        raise ValueError('Native runtime does not match the frozen core')
    wp.config.kernel_cache_dir = str(args.warp_cache)
    if not wp.get_device(protocol['device']).is_cuda:
        raise ValueError('CUDA required; no CPU fallback')
    mapped = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split()
        if len(fields) >= 6 and (fields[5].endswith('/warp.so') or '/libmujoco.so.' in fields[5]):
            path = Path(fields[5]).resolve(strict=True)
            mapped[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if mapped != protocol['native_payload_sha256']:
        raise ValueError('Loaded native payload differs from the frozen matched combination')
    write_json(args.output / 'runtime-identity.json', {'versions': versions, 'native_sha256': mapped})
    model = mujoco.MjModel.from_binary_path(str(args.output / 'model.mjb'))
    original = json.loads((args.output / 'conversion-readback.json').read_text())['compiled']
    differences = parameter_differences(original, conversion_parameters(model))
    if not all(row['equal'] for row in differences.values()):
        raise ValueError('Native CPU model differs from the frozen framework binary')
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    with wp.ScopedDevice(protocol['device']):
        if protocol['sleep_policy_projection'] != 'official-newton-1.5-runtime-policy':
            raise ValueError('Unreviewed sleep-policy projection')
        # Match the official framework's authoring -> compiled policy mapping.
        # MJWarp accepts AUTO_* policies, not NEVER/ALLOWED/INIT authoring values.
        authored = model.tree_sleep_policy.copy()
        model.tree_sleep_policy[authored == mujoco.mjtSleepPolicy.mjSLEEP_NEVER] = mujoco.mjtSleepPolicy.mjSLEEP_AUTO_NEVER
        allowed = ((authored == mujoco.mjtSleepPolicy.mjSLEEP_ALLOWED)
                   | (authored == mujoco.mjtSleepPolicy.mjSLEEP_INIT))
        model.tree_sleep_policy[allowed] = mujoco.mjtSleepPolicy.mjSLEEP_AUTO_ALLOWED
        write_json(args.output / 'sleep-policy-projection.json', {
            'authoring': authored.tolist(), 'runtime': model.tree_sleep_policy.tolist(),
            'source': protocol['sleep_policy_projection'],
        })
        try:
            gpu_model = mjw.put_model(model)
        finally:
            model.tree_sleep_policy[:] = authored
        gpu = mjw.put_data(model, data, nworld=1, nconmax=protocol['nconmax'],
                           njmax=protocol['njmax'])
        wp.synchronize()
        if 'gpu_alignment' in case:
            write_json(args.output / 'gpu-model-unadjusted.json', warp_model_parameters(gpu_model))
            aligned = align_inertia_parameters(gpu_model, case['gpu_alignment'])
            aligned['source_sha256'] = case['alignment_source_sha256']
            write_json(args.output / 'gpu-alignment.json', aligned)
        write_json(args.output / 'gpu-model-initial.json', warp_model_parameters(gpu_model))
        gpu_model.opt.timestep.fill_(protocol['dt_s'])
        write_json(args.output / 'admission.json', {
            'cpu_model_matches_source': True, 'naconmax_shared': gpu.naconmax,
            'njmax_per_world': gpu.njmax, 'worlds': gpu.nworld,
            'use_mujoco_contacts': gpu_model.opt.run_collision_detection,
            'state_update_interval': 0,
        })
        graph = None
        started = time.perf_counter()
        with (args.output / 'steps.jsonl').open('x') as stream:
            for step in range(protocol['steps']):
                if step == 0 or not protocol['use_cuda_graph']:
                    mjw.step(gpu_model, gpu)
                else:
                    if graph is None:
                        with wp.ScopedCapture() as capture:
                            mjw.step(gpu_model, gpu)
                        graph = capture.graph
                    wp.capture_launch(graph)
                wp.synchronize()
                progress = args.output / 'progress.json'
                temporary = progress.with_suffix('.tmp')
                temporary.write_text(json.dumps({'physics_steps': step + 1}) + '\n')
                temporary.replace(progress)
                if step == 0:
                    write_json(args.output / 'gpu-model-first-step.json', warp_model_parameters(gpu_model))
                    write_json(args.output / 'gpu-execution-options.json', warp_execution_options())
                nacon, nefc = int(gpu.nacon.numpy()[0]), int(gpu.nefc.numpy()[0])
                if not 0 <= nacon <= gpu.naconmax or not 0 <= nefc <= gpu.njmax:
                    raise ValueError('Native contact/constraint capacity overflow')
                mjw.get_data_into(data, model, gpu)
                row = {'step': step + 1, 'gpu_time_s': float(data.time),
                       'gpu_dt_s': gpu_model.opt.timestep.numpy().tolist(),
                       'nacon': nacon, 'nefc': nefc,
                       'native_solver_niter': gpu.solver_niter.numpy().tolist(),
                       'native_efc_force': gpu.efc.force.numpy()[0, :nefc].tolist(),
                       'native_efc_address': gpu.contact.efc_address.numpy()[:nacon].tolist()}
                for name in ('qpos', 'qvel', 'qacc', 'qfrc_constraint', 'qfrc_smooth',
                             'qfrc_bias', 'qfrc_passive', 'qacc_warmstart'):
                    row[name] = getattr(data, name).tolist()
                stream.write(json.dumps(row, allow_nan=False) + '\n')
                stream.flush()
        write_json(args.output / 'completion.json', {
            'completed_steps': protocol['steps'], 'whole_step_loop_s': time.perf_counter() - started,
            'scope': 'Matched-core diagnostic only; no full task coverage claim.',
        })


if __name__ == '__main__':
    main()
