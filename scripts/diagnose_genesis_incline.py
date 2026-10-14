"""Read native stopping fields at a frozen incline case's worst impulse sample.

Separate diagnostic acquisition; never updates the original campaign or scores.
Run with the same bounded resource/research-lock wrapper as physics acquisition.
"""

import argparse
import copy
import json
import os
from pathlib import Path

import numpy as np

from dexlab.genesis_incline import GenesisIncline, runtime_identity, write_json
from dexlab.genesis_incline_score import score_record, validate_admission, validate_runtime
from dexlab.incline_score import file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='One archived profile directory')
    parser.add_argument('--case', required=True)
    parser.add_argument('--iterations', type=int, help='Optional diagnostic iteration-cap change')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    protocol = json.loads((args.input / 'protocol.json').read_text())
    case = next(case for case in protocol['cases'] if case['id'] == args.case)
    original_score = score_record(protocol, case, args.input / case['id'])
    campaign = json.loads((args.input / 'campaign.json').read_text())
    import dexlab.genesis_incline as recorder
    source_root = Path(recorder.__file__).parent
    for name, digest in campaign['source_hashes'].items():
        if Path(name).name != name or file_hash(source_root / name) != digest:
            raise ValueError('Use the frozen recorder/scorer source for this diagnostic')
    with np.load(args.input / case['id'] / 'trace.npz', allow_pickle=False) as data:
        original = dict(data)
    h, mass = case['timestep'], protocol['mass_kg']
    residual = mass * np.diff(original['states'][:, 8:11], axis=0)
    residual -= (original['forces'] + [0, 0, -mass * protocol['gravity_m_s2']]) * h
    index = int(np.argmax(np.linalg.norm(residual, axis=1)))
    config = copy.deepcopy(protocol)
    if args.iterations is not None:
        if not 1 <= args.iterations <= 1000:
            raise ValueError('Diagnostic iteration cap must be in [1, 1000]')
        config['genesis']['options']['iterations'] = args.iterations
        config['genesis']['expected_options']['iterations'] = args.iterations
    args.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    os.environ['QD_NUM_THREADS'] = str(protocol['threads'])
    gs.init(backend=gs.cpu, precision='64', seed=0, use_deterministic_algorithms=True, logging_level='warning')
    try:
        proof = json.loads((args.input / 'official-proof.json').read_text())
        runtime = runtime_identity(proof)
        validate_runtime(protocol, proof, runtime)
        native = GenesisIncline(config, case)
        try:
            validate_admission(config, case, native.admission)
            states, forces = [native.state().tolist()], []
            for _ in range(index + 1):
                state, force, _, errno, _, _ = native.step()
                if errno.any():
                    raise ValueError('Native error during diagnostic prefix')
                states.append(state.tolist())
                forces.append(force.tolist())
            fields = native.solver.constraint_solver.constraint_state
            readback = {key: native.to_numpy(getattr(fields, key)).tolist()
                        for key in ('grad', 'Mgrad', 'Ma', 'qacc', 'qfrc_constraint', 'improved')}
            readback['island'] = {key: native.to_numpy(getattr(fields.island, key)).tolist()
                                 for key in ('inertia', 'ls_improvement', 'improved', 'n_islands')}
            write_json(args.output / 'diagnostic.json', dict(
                protocol=config, case=case, steps=index + 1, runtime=runtime,
                original_score=original_score, original_trace_sha256=file_hash(args.input / case['id'] / 'trace.npz'),
                diagnostic_source_sha256=file_hash(Path(__file__)), admission=native.admission,
                state_force_prefix_identical=bool(np.array_equal(states, original['states'][:index + 2])
                    and np.array_equal(forces, original['forces'][:index + 1])),
                states=states, forces=forces, native_fields=readback,
                scope='Separate development diagnostic; no new coverage or original-score replacement'))
        finally:
            native.close()
    finally:
        gs.destroy()


if __name__ == '__main__':
    main()
