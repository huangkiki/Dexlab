"""Read VBD force/pose fields on a frozen 20-step incline prefix.

Run inside the same bounded resource/research-lock envelope as acquisition.
Iteration probes are diagnostics; they never replace original task scores.
"""

import argparse
import gzip
from itertools import islice
import json
from pathlib import Path

import numpy as np

from dexlab import newton_incline as recorder
from dexlab.incline_score import file_hash
from dexlab.newton_incline_score import validate_admission, validate_protocol


def diagnose(root, output, probe_step=None):
    import warp as wp

    output.mkdir(parents=True, exist_ok=False)
    wp.config.kernel_cache_dir = str(output / 'kernel-cache')
    wp.init()
    steps = probe_step or 20
    if not 1 <= steps <= 20:
        raise ValueError('Diagnostic prefix must contain 1..20 steps')
    report = dict(source_sha256=file_hash(Path(__file__)), cases=[], probe_step=probe_step,
                  scope='Development prefixes; no replacement scores or coverage credit')
    for profile in ('vbd-legacy', 'vbd-compliant'):
        directory = root / profile
        protocol = json.loads((directory / 'manifest.json').read_text())
        campaign = json.loads((directory / 'campaign.json').read_text())
        proof = json.loads((directory / 'official-proof.json').read_text())
        validate_protocol(protocol)
        if (protocol['profile'] != profile or campaign['state'] != 'completed'
                or campaign['protocol_sha256'] != file_hash(directory / 'manifest.json')
                or campaign['proof_sha256'] != file_hash(directory / 'official-proof.json')
                or protocol['recorder_sha256'] != file_hash(Path(recorder.__file__))):
            raise ValueError('Use the original frozen campaign and recorder')
        for name in ('newton', 'warp-lang'):
            identity = recorder.package_identity(name)
            identity.pop('installation_origin', None)
            if identity != proof['packages'][name]['identity']:
                raise ValueError('Runtime differs from official frozen identity')
        case = next(c for c in protocol['cases'] if c['id'] == 'static-h0.001')
        source = directory / case['id'] / 'steps.jsonl.gz'
        metadata = json.loads((source.parent / 'metadata.json').read_text())
        if metadata['hashes'][source.name] != file_hash(source):
            raise ValueError('Changed original observations')
        with gzip.open(source, 'rt') as stream:
            original = [json.loads(line) for line in islice(stream, steps)]
        if len(original) != steps:
            raise ValueError('Missing original prefix')
        for iterations in (99, 100, 101, 1000, 1001):
            with wp.ScopedDevice('cpu'):
                scene = recorder.NewtonIncline(protocol, case)
                validate_admission(protocol, case, scene.admission)
                # In v1.6.1 this scalar controls only the primal/dual loop;
                # no iteration-sized allocation exists. Change before stepping.
                scene.solver.iterations = iterations if probe_step is None else 100
                rows = []
                for step in range(steps):
                    if probe_step is not None and step == steps - 1:
                        scene.solver.iterations = iterations
                    row = scene.step(step, case['timestep'])
                    row['diagnostic_iterations'] = scene.solver.iterations
                    row['diagnostic_fields'] = {
                        name: getattr(scene.solver, name).numpy().tolist()
                        for name in ('body_inertia_q', 'body_hessian_ll', 'body_hessian_al',
                                     'body_hessian_aa', 'body_forces', 'body_torques')}
                    mass = scene.admission['model']['body_mass'][0]
                    delta_v = np.array(row['state'][8:11]) - row['pre_state'][8:11]
                    impulse = (np.array(row['net_force']) + [0, 0, -mass * 9.81]) * .001
                    row['impulse_residual_ns'] = float(np.linalg.norm(mass * delta_v - impulse))
                    rows.append(row)
                result = dict(profile=profile, iterations=iterations, case=case,
                              original_trace_sha256=file_hash(source), rows=rows,
                              admission=scene.admission,
                              state_force_prefix_identical=all(
                                  row['state'] == old['state'] and row['net_force'] == old['net_force']
                                  for row, old in zip(rows, original, strict=True)),
                              impulse_residual_max_ns=max(r['impulse_residual_ns'] for r in rows))
                report['cases'].append(result)
                recorder.checkpoint(output / 'diagnostic.json', report)
                if probe_step is not None and any(
                        row['state'] != old['state'] or row['net_force'] != old['net_force']
                        for row, old in zip(rows[:-1], original[:-1], strict=True)):
                    raise ValueError('The input history of the probed step changed')
                print(profile, iterations, result['state_force_prefix_identical'],
                      result['impulse_residual_max_ns'], flush=True)
                if iterations == 100 and not result['state_force_prefix_identical']:
                    raise ValueError('Default diagnostic does not reproduce the original prefix')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Archived campaign-v1 directory')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--probe-step', type=int,
                        help='Keep the preceding prefix at 100 iterations; change only this step')
    args = parser.parse_args()
    diagnose(args.input, args.output, args.probe_step)
