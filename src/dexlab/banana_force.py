"""Run the frozen independent BladeMaster banana-force protocol."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from dexlab.banana_force_score import score_force_run, score_force_suite
from dexlab.cutting import CutConfig, CuttingSimulation
from dexlab.cutting_geometry import material_points
from dexlab.tofu_cut import BLADEMASTER_BANANA_MATERIAL, write_json


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = ROOT / 'demos/banana-force/force-protocol.json'
SOURCE_FILES = (
    'src/dexlab/banana_force.py', 'src/dexlab/banana_force_score.py',
    'src/dexlab/cutting.py', 'src/dexlab/cutting_geometry.py', 'src/dexlab/tofu_cut.py',
)


def load_protocol(path=DEFAULT_PROTOCOL):
    path = Path(path)
    protocol = json.loads(path.read_text())
    if protocol.get('status') != 'frozen-before-acceptance-runs':
        raise ValueError('Banana-force protocol is not frozen')
    return protocol


def stratified_reference(spacing, seed, jitter_fraction=.35):
    """Return one reproducible equal-volume sample inside each banana voxel."""
    reference = material_points((.12, .06, .03), spacing, 'banana')
    rng = np.random.default_rng(seed)
    particle_spacing = spacing / 2
    return reference + rng.uniform(-.5, .5, reference.shape) * particle_spacing * jitter_fraction


def refined_reference(base_spacing, factor=4):
    """Split every unjittered base voxel into exactly ``factor**3`` children."""
    reference = material_points((.12, .06, .03), base_spacing, 'banana')
    particle_spacing = base_spacing / 2
    coordinates = ((np.arange(factor) + .5) / factor - .5) * particle_spacing
    offsets = np.stack(np.meshgrid(coordinates, coordinates, coordinates, indexing='ij'), axis=-1)
    return (reference[:, None, :] + offsets.reshape(1, factor**3, 3)).reshape(-1, 3)


def sampling_sha256(reference):
    contiguous = np.ascontiguousarray(reference, dtype='<f8')
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def source_sha256():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


def cgroup_limits():
    """Read effective cgroup-v2 limits; missing limits cannot qualify a run."""
    entry = next((line for line in Path('/proc/self/cgroup').read_text().splitlines()
                  if line.startswith('0::')), None)
    if entry is None:
        return None
    root = Path('/sys/fs/cgroup') / entry.split('::', 1)[1].lstrip('/')
    names = ('memory.max', 'memory.swap.max', 'cpu.max')
    try:
        return {name: (root / name).read_text().strip() for name in names}
    except OSError:
        return None


def force_config(protocol, *, dt=None, normal_scale=None, refined=False):
    choices = protocol['independent_choices']
    contact, trajectory = choices['contact'], choices['trajectory']
    spacing = (protocol['refinement']['grid_spacing_m'] if refined
               else choices['geometry']['base_grid_spacing_m'])
    selected_dt = (protocol['refinement']['timestep_s'] if refined else
                   contact['base_timestep_s']) if dt is None else dt
    return CutConfig(
        shape='banana', size=tuple(choices['geometry']['size_m']),
        grid_spacing=spacing, dt=selected_dt,
        blade_half_size=tuple(choices['blade']['half_size_m']),
        blade_bevel_height=choices['blade']['bevel_height_m'],
        drive_stiffness=trajectory['drive_stiffness_n_m'],
        drive_damping=trajectory['drive_damping_n_s_m'],
        drive_force_limit=trajectory['drive_force_limit_n'],
        normal_scale=contact['normal_scale'] if normal_scale is None else normal_scale,
        tangent_stiffness=contact['tangent_stiffness_scale'],
        tangent_damping=contact['tangent_damping_ratio'],
        flip_fraction=choices['transfer']['flip_fraction'],
        **BLADEMASTER_BANANA_MATERIAL,
    )


def force_target(t, protocol):
    trajectory = protocol['independent_choices']['trajectory']
    z = np.interp(t, trajectory['time_s'], trajectory['edge_height_m'])
    return np.array([0., 0., z])


def run_force_case(directory, *, protocol_path=DEFAULT_PROTOCOL, seed=0, refined=False,
                   dt=None, normal_scale=None, duration=None, case_id=None,
                   resume=False, segment_wall_s=None):
    """Execute one case and save every force substep for independent scoring."""
    protocol_path = Path(protocol_path).resolve()
    protocol = load_protocol(protocol_path)
    config = force_config(protocol, dt=dt, normal_scale=normal_scale, refined=refined)
    trajectory = protocol['independent_choices']['trajectory']
    duration = trajectory['duration_s'] if duration is None else duration
    if duration <= 0 or duration > trajectory['duration_s']:
        raise ValueError('Duration must lie within the frozen trajectory')
    steps = round(duration / config.dt)
    if abs(steps * config.dt - duration) > 1e-12:
        raise ValueError('Duration must contain an integer number of substeps')
    base_spacing = protocol['independent_choices']['geometry']['base_grid_spacing_m']
    reference = (refined_reference(base_spacing, protocol['refinement']['factor_per_axis'])
                 if refined else stratified_reference(
                     base_spacing, seed,
                     protocol['independent_choices']['sampling']['jitter_fraction_of_particle_spacing']))
    case_id = case_id or (f'refined-seed-{seed}' if refined else f'base-seed-{seed}')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=resume)
    try:
        recorded_protocol_path = str(protocol_path.relative_to(ROOT))
    except ValueError:
        recorded_protocol_path = str(protocol_path)
    identity = {
        'protocol_path': recorded_protocol_path,
        'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        'config': asdict(config), 'sampling_seed': seed,
        'sampling_kind': 'hierarchical-refined-centres' if refined else 'stratified-jitter',
        'sampling_sha256': sampling_sha256(reference), 'particle_count': len(reference),
        'duration_s': duration,
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_dirty': bool(subprocess.check_output(
            ['git', 'status', '--porcelain', '--untracked-files=normal'],
            cwd=ROOT, text=True).strip()),
        'source_sha256': source_sha256(),
    }
    identity = json.loads(json.dumps(identity))  # Normalize tuples to the saved JSON representation.
    if resume:
        manifest = json.loads((directory / 'manifest.json').read_text())
        if manifest.get('status') != 'paused':
            raise ValueError('Only a paused force run can resume')
        for name in ('trace.npz', 'checkpoint.npz'):
            path = directory / name
            if manifest.get('artifacts', {}).get(name) != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError(f'Resume artifact changed: {name}')
        for name, value in identity.items():
            if manifest.get(name) != value:
                raise ValueError(f'Resume identity changed: {name}')
    else:
        manifest = {'schema_version': 1, 'status': 'running', 'case_id': case_id,
                    **identity, 'segments': []}
        write_json(directory / 'manifest.json', manifest)
    sim = CuttingSimulation(config, reference)
    previous_trace = {}
    if resume:
        with np.load(directory / 'checkpoint.npz') as checkpoint:
            for name in ('x', 'velocity', 'deformation', 'sides', 'damage', 'blade_x',
                         'blade_v', 'rigid_history', 'pair_keys', 'pair_history'):
                setattr(sim, name, np.asarray(checkpoint[name]).copy())
            sim.blade_yaw = float(checkpoint['blade_yaw'])
            sim.step_count = int(checkpoint['step_count'])
        with np.load(directory / 'trace.npz') as archive:
            previous_trace = {name: np.asarray(archive[name]) for name in archive.files}
    else:
        sim.blade_x = force_target(0., protocol) + np.array([0., 0., sim.half_size[2]])
    trace = []
    start = time.monotonic()
    start_step = sim.step_count
    paused = False
    try:
        for step in range(start_step, steps):
            t = step * config.dt
            observed = sim.step(force_target(t, protocol), cutting=True, cut_index=0)
            material = float(observed['material_reaction_n'][2])
            support = float(observed['blade_board_impulse_ns'][2] / config.dt)
            observed.update(
                material_resistance_n=material,
                rigid_support_resistance_n=support,
                total_resistance_n=material + support,
                actuator_axial_force_n=float(-observed['drive_force_n'][2]),
            )
            trace.append(observed)
            if (segment_wall_s is not None and step + 1 < steps
                    and time.monotonic() - start >= segment_wall_s):
                paused = True
                break
        manifest['status'] = 'paused' if paused else 'complete'
    except (Exception, KeyboardInterrupt) as error:
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        current_trace = ({key: np.asarray([row[key] for row in trace])
                          for key in trace[0]} if trace else {})
        combined = {}
        for key in set(previous_trace) | set(current_trace):
            if key not in previous_trace:
                combined[key] = current_trace[key]
            elif key not in current_trace:
                combined[key] = previous_trace[key]
            else:
                combined[key] = np.concatenate((previous_trace[key], current_trace[key]))
        np.savez_compressed(directory / 'trace.npz',
                            **combined)
        np.savez_compressed(
            directory / 'checkpoint.npz', x=sim.x, velocity=sim.velocity,
            deformation=sim.deformation, sides=sim.sides, damage=sim.damage,
            blade_x=sim.blade_x, blade_v=sim.blade_v, blade_yaw=sim.blade_yaw,
            rigid_history=sim.rigid_history, pair_keys=sim.pair_keys,
            pair_history=sim.pair_history, step_count=sim.step_count)
        wall = time.monotonic() - start
        manifest['completed_steps'] = sim.step_count
        manifest['wall_s_including_jit'] = sum(
            segment['wall_s'] for segment in manifest['segments']) + wall
        manifest['segments'].append({
            'index': len(manifest['segments']), 'start_step': start_step,
            'end_step': sim.step_count, 'wall_s': wall,
            'cgroup_limits': cgroup_limits(),
        })
        manifest['artifacts'] = {
            'trace.npz': hashlib.sha256((directory / 'trace.npz').read_bytes()).hexdigest(),
            'checkpoint.npz': hashlib.sha256((directory / 'checkpoint.npz').read_bytes()).hexdigest(),
        }
        write_json(directory / 'manifest.json', manifest)
    if paused:
        return {'schema_version': 1, 'case_id': case_id, 'status': 'paused',
                'completed_steps': sim.step_count, 'total_steps': steps}
    result = score_force_run(directory)
    write_json(directory / 'score.json', result)
    return result


def suite_cases(protocol, suite):
    """Enumerate the frozen cohort without silently duplicating the baseline."""
    seeds = protocol['independent_choices']['sampling']['seeds']
    baseline = [dict(case_id=f'base-seed-{seed}', seed=seed, refined=False)
                for seed in seeds]
    base_dt = protocol['independent_choices']['contact']['base_timestep_s']
    base_normal = protocol['independent_choices']['contact']['normal_scale']
    sensitivity = []
    for dt in protocol['sensitivity']['timestep_s']:
        if dt != base_dt:
            sensitivity.append(dict(case_id=f'sensitivity-dt-{dt:g}', seed=0,
                                    refined=False, dt=dt))
    for normal in protocol['sensitivity']['normal_scale']:
        if normal != base_normal:
            sensitivity.append(dict(case_id=f'sensitivity-normal-{normal:g}', seed=0,
                                    refined=False, normal_scale=normal))
    refined = [dict(case_id='refined-centres', seed=0, refined=True)]
    selected = {
        'baseline': baseline,
        'sensitivity': [baseline[0], *sensitivity],
        'refined': [baseline[0], *refined],
        'all': [*baseline, *sensitivity, *refined],
    }
    return selected[suite]


def run_force_suite(directory, *, protocol_path=DEFAULT_PROTOCOL, suite='all', segment_wall_s=None):
    """Run or resume one declared cohort and write an independently recomputed summary."""
    protocol_path = Path(protocol_path).resolve()
    protocol = load_protocol(protocol_path)
    if suite not in ('baseline', 'sensitivity', 'refined', 'all'):
        raise ValueError('Unknown force suite')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'cases').mkdir(exist_ok=True)
    try:
        recorded_protocol_path = str(protocol_path.relative_to(ROOT))
    except ValueError:
        recorded_protocol_path = str(protocol_path)
    cases = suite_cases(protocol, suite)
    suite_record = {
        'schema_version': 1, 'suite': suite, 'protocol_path': recorded_protocol_path,
        'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        'cases': cases,
    }
    write_json(directory / 'suite.json', suite_record)
    for spec in cases:
        output = directory / 'cases' / spec['case_id']
        if output.exists():
            status = json.loads((output / 'manifest.json').read_text()).get('status')
            if status == 'complete':
                score_force_run(output)
                continue
            if status != 'paused':
                raise ValueError(f'Cannot resume {spec["case_id"]}: {status}')
            result = run_force_case(output, protocol_path=protocol_path, resume=True,
                                    segment_wall_s=segment_wall_s, **spec)
        else:
            result = run_force_case(output, protocol_path=protocol_path,
                                    segment_wall_s=segment_wall_s, **spec)
        if result.get('status') == 'paused':
            progress = {'schema_version': 1, 'suite': suite, **result}
            write_json(directory / 'progress.json', progress)
            return progress
    summary = score_force_suite(directory)
    write_json(directory / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--refined', action='store_true')
    parser.add_argument('--dt', type=float)
    parser.add_argument('--normal-scale', type=float)
    parser.add_argument('--duration', type=float, help='bounded probe; default executes the frozen trajectory')
    parser.add_argument('--case-id')
    parser.add_argument('--suite', choices=('baseline', 'sensitivity', 'refined', 'all'))
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--segment-wall-s', type=float)
    args = parser.parse_args()
    if args.suite:
        if any((args.refined, args.dt is not None, args.normal_scale is not None,
                args.duration is not None, args.case_id is not None, args.seed != 0)):
            parser.error('--suite cannot be combined with single-case overrides')
        result = run_force_suite(args.output, protocol_path=args.protocol, suite=args.suite,
                                 segment_wall_s=args.segment_wall_s)
    else:
        result = run_force_case(args.output, protocol_path=args.protocol, seed=args.seed,
                                refined=args.refined, dt=args.dt, normal_scale=args.normal_scale,
                                duration=args.duration, case_id=args.case_id, resume=args.resume,
                                segment_wall_s=args.segment_wall_s)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
