"""Record native solver diagnostics for the preregistered pinch fixture."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from dexlab.cloth_engines import package_identity
from dexlab.engine_versions import mujoco_profile_identity
from dexlab.pinch_run import commands, compiled_readback, model_xml


FORCE_FIELDS = ('qfrc_smooth', 'qfrc_constraint', 'qfrc_bias', 'qfrc_passive',
                'qfrc_actuator', 'qfrc_applied')
STAT_FIELDS = ('improvement', 'gradient', 'lineslope', 'nactive', 'nchange', 'neval', 'nupdate')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_case(mj, protocol, case, output):
    output.mkdir()
    started = time.perf_counter()
    specification = dict(protocol, solver_tolerance=case['solver_tolerance'])
    xml = model_xml(specification, case)
    (output / 'model.xml').write_text(xml)
    model = mj.MjModel.from_xml_string(xml)
    data = mj.MjData(model)
    mj.mj_forward(model, data)
    cube = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, 'cube')
    n = round(protocol['duration_s'] / case['timestep'])
    islands = len(data.solver_niter)
    slots = len(data.solver) // islands
    if slots * islands != len(data.solver) or model.opt.iterations > slots:
        raise ValueError('Solver statistics capacity cannot represent the declared budget')
    trace = {name: np.zeros((n, model.nv)) for name in FORCE_FIELDS}
    trace.update(states=np.zeros((n + 1, 18)), qacc=np.zeros((n, model.nv)),
                 mass=np.zeros((n, model.nv, model.nv)), commands=np.zeros((n, 2)),
                 external=np.zeros((n, 3)), body_load=np.zeros((n, model.nbody, 6)), force_times=np.zeros(n),
                 warnings=np.zeros((n, len(data.warning)), dtype=int),
                 solver_niter=np.zeros((n, islands), dtype=int), nefc=np.zeros(n, dtype=int),
                 solver_offsets=np.zeros(n + 1, dtype=int))
    trace['states'][0] = np.r_[data.time, data.qpos, data.qvel]
    stats = []
    setup_s = time.perf_counter() - started
    control_s = native_s = observation_s = 0.
    for step in range(n):
        before = time.perf_counter()
        command, external = commands(protocol, case, step)
        data.ctrl[:] = command
        data.xfrc_applied[cube, :3] = external
        control_s += time.perf_counter() - before
        before = time.perf_counter()
        mj.mj_step(model, data)
        after = time.perf_counter()
        native_s += after - before
        trace['states'][step + 1] = np.r_[data.time, data.qpos, data.qvel]
        trace['qacc'][step] = data.qacc
        mj.mj_fullM(model, data, trace['mass'][step])
        for name in FORCE_FIELDS:
            trace[name][step] = getattr(data, name)
        trace['commands'][step] = command
        trace['external'][step] = data.xfrc_applied[cube, :3]
        trace['body_load'][step] = data.xfrc_applied
        trace['force_times'][step] = trace['states'][step, 0]
        trace['warnings'][step] = data.warning.number
        trace['nefc'][step] = data.nefc
        trace['solver_niter'][step] = data.solver_niter
        for island, count in enumerate(data.solver_niter):
            if not 0 <= count <= slots:
                raise ValueError('Solver iteration statistics truncated')
            for iteration in range(count):
                row = data.solver[island * slots + iteration]
                stats.append([island, iteration, *(getattr(row, name) for name in STAT_FIELDS)])
        trace['solver_offsets'][step + 1] = len(stats)
        observation_s += time.perf_counter() - after
    trace['solver_stats'] = np.asarray(stats, dtype=float).reshape(-1, 9)
    before = time.perf_counter()
    np.savez_compressed(output / 'trace.npz', **trace)
    serialization_s = time.perf_counter() - before
    metadata = dict(case=case, readback=compiled_readback(model), cube_body=cube,
                    state_writes_after_initialization=0,
                    force_epoch='states[i].time; states[i+1] postintegration',
                    statistic_fields=['island', 'iteration', *STAT_FIELDS],
                    solver_island_capacity=islands, solver_iteration_capacity=slots,
                    trace_sha256=digest(output / 'trace.npz'), xml_sha256=digest(output / 'model.xml'),
                    setup_s=setup_s, control_s=control_s, native_step_s=native_s,
                    observation_s=observation_s, serialization_s=serialization_s,
                    total_case_wall_s=time.perf_counter() - started)
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import mujoco as mj
    from dexlab import pinch_run
    protocol = json.loads(args.manifest.read_text())
    if len(protocol['cases']) != 6 or mj.mj_versionString() != protocol['version']:
        raise ValueError('Version or campaign budget mismatch')
    runtime = mujoco_profile_identity(package_identity('mujoco'), mj.mj_versionString(),
                                      profile='qualification-3.15.0')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'manifest.json').write_bytes(args.manifest.read_bytes())
    started = time.perf_counter()
    for case in protocol['cases']:
        run_case(mj, protocol, case, args.output / case['id'])
    report = dict(runtime=runtime, completed_cases=6, wall_s=time.perf_counter() - started,
                  manifest_sha256=digest(args.manifest), runner_sha256=digest(__file__),
                  fixture_source_sha256=digest(pinch_run.__file__))
    (args.output / 'campaign.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
