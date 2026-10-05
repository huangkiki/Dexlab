"""Reproduce the timestep-dependent initialization confound and its correction.

Run under the repository resource guard. This intentionally preserves the old
initialization order as a negative control, independent of settle_cloth fixes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from cloth_model import load_model
from run_cloth import engine_identity, step


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(record, output):
    identity = engine_identity()
    if identity['version'] != '3.14.0':
        raise ValueError('This development comparison is pinned to official MuJoCo 3.14.0')
    output.mkdir(parents=True, exist_ok=False)
    inputs = {name: digest(record / name) for name in ('model.xml', 'settling/states.npz')}
    with np.load(record / 'settling/states.npz', allow_pickle=False) as saved:
        initial = saved['qpos'][0].copy()
    results, states = {}, {}
    for mode in ('original', 'configured', 'refreshed'):
        for timestep in (.00025, .000125):
            name = f'{mode}-{timestep}'
            folder = output / name
            folder.mkdir()
            xml = ET.parse(record / 'model.xml')
            xml.getroot().find('option').set('timestep', str(timestep))
            xml.write(folder / 'model.xml', encoding='unicode')
            model = load_model(folder / 'model.xml')
            data = mujoco.MjData(model)
            data.qpos[:] = initial
            if mode != 'original':
                model.opt.timestep = .0005
                model.opt.solver = mujoco.mjtSolver.mjSOL_CG
                model.opt.iterations = 100
            factor = model.efm0_L.copy()
            if mode == 'refreshed':
                mujoco.mj_setConst(model, mujoco.MjData(model))
            factor_delta = float(np.max(np.abs(model.efm0_L - factor), initial=0))
            mujoco.mj_forward(model, data)
            # The former settling loop: do not call the now-corrected settle_cloth.
            model.opt.solver = mujoco.mjtSolver.mjSOL_CG
            model.opt.iterations = 100
            model.opt.timestep = .0005
            start = time.monotonic()
            for _ in range(4000):
                step(model, data, initial)
            states[name] = (data.qpos.copy(), data.qvel.copy())
            np.savez(folder / 'final-state.npz', qpos=data.qpos, qvel=data.qvel)
            results[name] = {'wall_s': time.monotonic() - start,
                             'cached_factor_max_change': factor_delta,
                             'model_xml_sha256': digest(folder / 'model.xml'),
                             'final_state_sha256': digest(folder / 'final-state.npz')}
            print(name, flush=True)
    for mode in ('original', 'configured', 'refreshed'):
        comparison = {}
        for field, left, right in zip(('qpos', 'qvel'), states[f'{mode}-0.00025'],
                                      states[f'{mode}-0.000125']):
            comparison[f'{field}_bitwise_equal'] = bool(np.array_equal(left, right))
            comparison[f'{field}_max_abs_delta'] = float(np.max(np.abs(left - right)))
        results[f'{mode}-comparison'] = comparison
    if inputs != {name: digest(record / name) for name in inputs}:
        raise RuntimeError('Input changed during comparison')
    sources = [Path(__file__), Path(__file__).with_name('run_cloth.py'),
               Path(__file__).with_name('cloth_model.py')]
    report = {'engine': identity, 'input_sha256': inputs,
              'source_sha256': {path.name: digest(path) for path in sources},
              'results': results,
              'scope': 'Six passive development controls; no grasp or material calibration.'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path, help='Complete record with model.xml and initial settling states')
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory outside the record')
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.record.resolve()):
        parser.error('Output must be outside the immutable input record')
    run(args.record, args.output)
