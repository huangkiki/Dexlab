"""Run the synthetic tofu-halving experiment and save replayable physical states."""

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
from dexlab.cutting_score import ACCEPTANCE, score_run


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


def run(directory, config, mode='full', duration=DURATION):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    if mode not in ('full', 'partial', 'uncut'):
        raise ValueError('Unknown cutting mode')
    if duration <= 0 or duration > DURATION or abs(round(duration / config.dt) * config.dt - duration) > 1e-12:
        raise ValueError('Duration must be in (0, 3] and an integer number of steps')
    source_root = Path(__file__).resolve().parent
    manifest = {
        'schema_version': 1, 'status': 'running', 'mode': mode, 'config': asdict(config),
        'duration_s': duration, 'probe_time_s': PROBE_TIME, 'acceptance': ACCEPTANCE,
        'paper': 'https://arxiv.org/abs/2609.27342v2',
        'implementation': 'independent single-cut CPU TLMPM reference, synthetic parameters',
        'source_sha256': {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest()
                          for name in ('cutting.py', 'cutting_score.py', 'tofu_cut.py')},
        'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'numba')},
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_root, text=True).strip(),
    }
    write_json(directory / 'manifest.json', manifest)
    start = time.monotonic()
    sim = CuttingSimulation(config)
    snapshots = {key: [] for key in ('position', 'velocity', 'sides', 'damage', 'time')}

    def snapshot(t):
        for key, value in [('position', sim.x), ('velocity', sim.velocity),
                           ('sides', sim.sides), ('damage', sim.damage)]:
            snapshots[key].append(value.copy())
        snapshots['time'].append(t)

    snapshot(0.)
    trace = []
    stride = max(1, round(.01 / config.dt))
    try:
        for step in range(round(duration / config.dt)):
            t = step * config.dt
            probe = np.array([.12, 0., .1]) if step == round(PROBE_TIME / config.dt) else None
            trace.append(sim.step(target_edge(t, mode, config.size[2]),
                                  cutting=mode != 'uncut' and .3 <= t < 1.6,
                                  probe_velocity=probe))
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
    parser.add_argument('--dt', type=float, default=.0005)
    parser.add_argument('--grid-spacing', type=float, default=.0075)
    parser.add_argument('--duration', type=float, default=DURATION, help='Short probes do not establish task completion')
    args = parser.parse_args()
    run(args.output, CutConfig(dt=args.dt, grid_spacing=args.grid_spacing), args.mode, args.duration)


if __name__ == '__main__':
    main()
