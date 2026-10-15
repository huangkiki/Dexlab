"""Record synthetic tofu/banana cutting with replayable physical states."""

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from dexlab.cutting import CutConfig, CuttingSimulation
from dexlab.cutting_score import ACCEPTANCE, BANANA_ACCEPTANCE, PUSH_ACCEPTANCE, SCORING_ACCEPTANCE, score_run


DURATION = 3.0
PROBE_TIME = 2.4


def target_edge(t, mode, height):
    top = height + .012
    bottom = height / 2 if mode == 'partial' else -.004
    if mode == 'uncut':
        return np.array([0., 0., top])
    times = [.0, .3, 1.3, 1.6, 2.2, DURATION]
    heights = [top, top, bottom, bottom, top + .015, top + .015]
    return np.array([0., 0., np.interp(t, times, heights)])


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def sequential_target(t, mode, task):
    cuts = (-.03, 0., .03) if task == 'banana' else (.015, -.015)
    cut = min(int(t // 2), len(cuts)-1)
    x = cuts[cut]
    local = t - 2 * cut
    bottom = .012 if mode == 'partial' and cut == len(cuts)-1 else -.004
    z = np.interp(local, [0, .4, 1.1, 1.3, 1.8, 3.],
                  [.036, .036, bottom, bottom, .036, .036])
    cutting = mode != 'uncut' and .4 <= local < 1.3
    return np.array([x, 0., .036 if mode == 'uncut' else z]), cut, cutting


def scoring_target(t, mode):
    """Two guided perpendicular shallow incisions, with withdrawal between them."""
    cut = min(int(t // 2), 1)
    local = t - 2 * cut
    z = np.interp(local, [0., .35, 1., 1.2, 1.75, 2.2],
                  [.042, .042, .024, .024, .042, .042])
    return np.array([0., 0., .042 if mode == 'uncut' else z]), cut, (
        mode != 'uncut' and .35 <= local < 1.2), cut * np.pi / 2


def knife_push_target(t):
    """Re-enter the second kerf, push with the blade face, then withdraw.

    These are drive targets, not prescribed blade or material positions.
    Cutting is disabled throughout this contact-only phase.
    """
    times = [4., 4.8, 6., 6.6, 7.]
    return np.array([np.interp(t, times, [-.015, -.015, -.027, -.027, -.027]),
                     0., np.interp(t, times, [.036, .002, .002, .036, .036])])


def run(directory, config, mode='full', duration=None, task='tofu', motion_protocol=None):
    if task not in ('tofu', 'banana', 'tofu-sequential', 'tofu-scoring'):
        raise ValueError('Unknown task')
    full_duration, probe_time = {'banana': (7., 6.2), 'tofu-sequential': (5., 4.2),
                                 'tofu': (DURATION, PROBE_TIME), 'tofu-scoring': (4.2, None)}[task]
    if motion_protocol is None:
        motion_protocol = 'knife-push' if task == 'tofu-sequential' else 'impulse'
    if motion_protocol not in ('impulse', 'knife-push', 'no-push'):
        raise ValueError('Unknown motion protocol')
    contact_motion = motion_protocol != 'impulse'
    if contact_motion and task != 'tofu-sequential':
        raise ValueError('Knife-push protocols require sequential tofu')
    if contact_motion:
        full_duration, probe_time = 7., None
    duration = full_duration if duration is None else duration
    if (config.shape == 'banana') != (task == 'banana'):
        raise ValueError('Task and geometry do not match')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    if mode not in ('full', 'partial', 'uncut'):
        raise ValueError('Unknown cutting mode')
    if task == 'tofu-scoring' and mode == 'partial':
        raise ValueError('Scoring is already a partial-cut task; choose full or uncut')
    if duration <= 0 or duration > full_duration or abs(round(duration / config.dt) * config.dt - duration) > 1e-12:
        raise ValueError('Duration must fit the protocol and contain an integer number of steps')
    source_root = Path(__file__).resolve().parent
    manifest = {
        'schema_version': 1, 'status': 'running', 'mode': mode, 'config': asdict(config),
        'duration_s': duration, 'probe_time_s': probe_time, 'task': task,
        'acceptance': (SCORING_ACCEPTANCE if task == 'tofu-scoring' else
                       PUSH_ACCEPTANCE if contact_motion else
                       BANANA_ACCEPTANCE if task != 'tofu' else ACCEPTANCE),
        'paper': 'https://arxiv.org/abs/2609.27342v2',
        'implementation': 'independent CPU TLMPM reference, synthetic parameters',
        'source_sha256': {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest()
                          for name in ('cutting.py', 'cutting_geometry.py', 'cutting_score.py', 'tofu_cut.py')},
        'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'numba')},
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_root, text=True).strip(),
    }
    if task == 'tofu-sequential':
        manifest.update(motion_protocol=motion_protocol,
                        motion_start_time_s=4. if contact_motion else probe_time)
    write_json(directory / 'manifest.json', manifest)
    start = time.monotonic()
    sim = CuttingSimulation(config)
    snapshots = {key: [] for key in ('position', 'velocity', 'sides', 'damage', 'deformation', 'time')}

    def snapshot(t):
        for key, value in [('position', sim.x), ('velocity', sim.velocity),
                           ('sides', sim.sides), ('damage', sim.damage), ('deformation', sim.deformation)]:
            snapshots[key].append(value.copy())
        snapshots['time'].append(t)

    if task in ('banana', 'tofu-sequential'):
        sim.blade_x[0] = -.03 if task == 'banana' else .015
        sim.blade_x[2] = .036 + sim.half_size[2]
    snapshot(0.)
    previous_cut = 0
    trace = []
    stride = max(1, round(.01 / config.dt))
    try:
        for step in range(round(duration / config.dt)):
            t = step * config.dt
            probe = (np.array([.12, 0., .1]) if probe_time is not None and
                     step == round(probe_time / config.dt) else None)
            if task == 'tofu-sequential' and probe is not None:
                probe = np.array([-.12, 0., 0.])
            blade_yaw = 0.
            if task == 'tofu-scoring':
                target, cut_index, cutting, blade_yaw = scoring_target(t, mode)
                probe_mask = None
            elif task != 'tofu':
                target, cut_index, cutting = sequential_target(t, mode, task)
                if motion_protocol == 'knife-push' and t >= 4.:
                    target = knife_push_target(t)
                probe_mask = (sim.reference[:, 0] > .03 if task == 'banana' else
                              sim.reference[:, 0] < -.015)
            else:
                target, cut_index = target_edge(t, mode, config.size[2]), 0
                cutting, probe_mask = mode != 'uncut' and .3 <= t < 1.6, None
            if cut_index != previous_cut:
                sim.damage.fill(0.)  # Reset progress, retain every earlier ternary digit.
                previous_cut = cut_index
            observed = sim.step(target, cutting=cutting, probe_velocity=probe,
                                probe_mask=probe_mask, cut_index=cut_index, blade_yaw=blade_yaw)
            observed.update(cut_index=cut_index, cutting_active=cutting)
            trace.append(observed)
            if (step + 1) % stride == 0 or step + 1 == round(duration / config.dt):
                snapshot((step + 1) * config.dt)
            if (step + 1) % max(1, round(.5 / config.dt)) == 0:
                print(json.dumps({'time_s': trace[-1]['time_s'],
                                  'labelled': trace[-1]['labelled_particles'],
                                  'blade_edge_m': float(sim.blade_x[2] - sim.half_size[2]),
                                  'det_f_min': trace[-1]['minimum_det_f']}), flush=True)
        manifest['status'] = 'complete'
    except Exception as error:
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        np.savez_compressed(directory / 'states.npz', **{k: np.asarray(v) for k, v in snapshots.items()},
                            reference=sim.reference, nodes=sim.nodes, weights=sim.weights)
        np.savez_compressed(directory / 'trace.npz',
                            **({key: np.asarray([row[key] for row in trace]) for key in trace[0]} if trace else {}))
        manifest['wall_s_including_jit'] = time.monotonic() - start
        manifest['completed_steps'] = len(trace)
        manifest['artifacts'] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                 for name in ('states.npz', 'trace.npz')}
        write_json(directory / 'manifest.json', manifest)
    result = score_run(directory)
    write_json(directory / 'score.json', result)
    print(json.dumps(result, indent=2), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('full', 'partial', 'uncut'), default='full')
    parser.add_argument('--dt', type=float)
    parser.add_argument('--grid-spacing', type=float)
    parser.add_argument('--task', choices=('tofu', 'banana', 'tofu-sequential', 'tofu-scoring'), default='tofu')
    parser.add_argument('--duration', type=float, default=None, help='Short probes do not establish task completion')
    parser.add_argument('--motion-protocol', choices=('knife-push', 'no-push', 'impulse'),
                        help='Sequential tofu defaults to knife-push; impulse preserves the historical velocity probe')
    args = parser.parse_args()
    banana = args.task == 'banana'
    options = {
        'dt': args.dt if args.dt is not None else (.00025 if banana else .0005),
        'grid_spacing': args.grid_spacing if args.grid_spacing is not None else (.006 if banana else .0075),
    }
    if banana:
        options.update(shape='banana', size=(.12, .06, .03),
                       blade_half_size=(.0005, .04, .02), blade_bevel_height=.005)
    elif args.task == 'tofu-sequential':
        options.update(size=(.09, .03, .03), blade_half_size=(.00025, .025, .02),
                       blade_bevel_height=.005,
                       dt=args.dt if args.dt is not None else .00025)
    elif args.task == 'tofu-scoring':
        options.update(size=(.045, .045, .03), blade_half_size=(.00025, .0275, .02),
                       blade_bevel_height=.005,
                       grid_spacing=args.grid_spacing if args.grid_spacing is not None else .005,
                       dt=args.dt if args.dt is not None else .00025)
    run(args.output, CutConfig(**options), args.mode, args.duration, args.task, args.motion_protocol)


if __name__ == '__main__':
    main()
