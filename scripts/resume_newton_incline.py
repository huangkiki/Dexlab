"""Finish an interrupted campaign without rerunning completed cases.

The output retains the entire interrupted attempt, unchanged completed cases,
and records from the interrupted case onward. Use the bounded research wrapper.
"""

import argparse
import gzip
import json
from pathlib import Path
import shutil
import signal
import time

import numpy as np

from dexlab import newton_incline as recorder
from dexlab.newton_incline_score import validate_admission, validate_protocol


def resume(source, output):
    import warp as wp

    protocol = json.loads((source / 'manifest.json').read_text())
    campaign = json.loads((source / 'campaign.json').read_text())
    proof = json.loads((source / 'official-proof.json').read_text())
    validate_protocol(protocol)
    cases = protocol['cases']
    recorded = campaign['cases']
    if (campaign['state'] != 'interrupted' or campaign['admission_only']
            or not 1 <= len(recorded) <= len(cases)
            or protocol['recorder_sha256'] != recorder.sha256(Path(recorder.__file__))):
        raise ValueError('Expected the original interrupted campaign and recorder')
    first_pending = len(recorded) - 1
    for index, (item, case) in enumerate(zip(recorded, cases)):
        if item['case'] != case:
            raise ValueError('Changed case identity')
        directory = source / case['id']
        if item != json.loads((directory / 'metadata.json').read_text()):
            raise ValueError('Changed original metadata')
        for name, digest in item['hashes'].items():
            if Path(name).name != name or recorder.sha256(directory / name) != digest:
                raise ValueError('Changed original observations')
        if item['hashes']['admission.json'] != protocol['admission_sha256'][case['id']]:
            raise ValueError('Changed original admission')
        steps = round(protocol['duration_s'] / case['timestep'])
        if index == first_pending:
            if (not isinstance(item['error'], str) or not item['error'].startswith('KeyboardInterrupt:')
                    or not 0 < item['completed_steps'] < steps):
                raise ValueError('Final recorded case must have an incomplete observed prefix')
        elif item['error'] or item['completed_steps'] != steps:
            raise ValueError('Completed cases must be reused unchanged')
    for name, key in [('manifest.json', 'protocol_sha256'), ('recorder.py', 'recorder_sha256'),
                      ('official-proof.json', 'proof_sha256')]:
        if recorder.sha256(source / name) != campaign[key]:
            raise ValueError('Changed frozen artifact')
    for name in ('newton', 'warp-lang'):
        identity = recorder.package_identity(name)
        identity.pop('installation_origin', None)
        if identity != campaign['packages'][name] or identity != proof['packages'][name]['identity']:
            raise ValueError('Changed official runtime')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, output / 'interrupted-attempt')
    for name in ('manifest.json', 'official-proof.json', 'recorder.py'):
        shutil.copyfile(source / name, output / name)
    shutil.copyfile(Path(__file__), output / 'continuation.py')
    for case in cases[:first_pending]:
        shutil.copytree(source / case['id'], output / case['id'])
    interrupted = recorded.pop()
    campaign['state'] = 'running'
    campaign['continuation'] = dict(
        original_campaign_sha256=recorder.sha256(source / 'campaign.json'),
        runner_sha256=recorder.sha256(Path(__file__)), replaced_case=interrupted['case']['id'],
        reason='Original service reached its frozen wall limit; no physical parameter change',
        original_completed_steps=interrupted['completed_steps'])
    recorder.checkpoint(output / 'campaign.json', campaign)
    wp.config.kernel_cache_dir = str(output.parent / 'kernel-cache')
    wp.init()
    with wp.ScopedDevice('cpu'):
        for case in cases[first_pending:]:
            directory = output / case['id']
            directory.mkdir()
            meta = dict(case=case, completed_steps=0, attempted_steps=0, error=None,
                        state_writes_after_initialization=0, native_step_wall_s=0.)
            started = time.perf_counter()
            try:
                record_case(protocol, case, directory, meta, started)
            except (Exception, KeyboardInterrupt) as error:
                meta['error'] = f'{type(error).__name__}: {error}'
            meta['wall_s'] = time.perf_counter() - started
            meta['hashes'] = {p.name: recorder.sha256(p) for p in directory.iterdir()}
            recorder.write_json(directory / 'metadata.json', meta)
            recorded.append(meta)
            if meta['error']:
                campaign['state'] = 'interrupted'
            recorder.checkpoint(output / 'campaign.json', campaign)
            if meta['error']:
                raise RuntimeError(meta['error'])
    campaign['state'] = 'completed'
    recorder.checkpoint(output / 'campaign.json', campaign)


def record_case(protocol, case, directory, meta, started):
    scene = recorder.NewtonIncline(protocol, case)
    recorder.write_json(directory / 'admission.json', scene.admission)
    validate_admission(protocol, case, scene.admission)
    if recorder.sha256(directory / 'admission.json') != protocol['admission_sha256'][case['id']]:
        raise ValueError('Effective parameters differ from frozen admission')
    meta['setup_s'] = time.perf_counter() - started
    with gzip.open(directory / 'steps.jsonl.gz', 'xt') as stream:
        for step in range(round(protocol['duration_s'] / case['timestep'])):
            meta['attempted_steps'] += 1
            row = scene.step(step, case['timestep'])
            stream.write(json.dumps(row, allow_nan=True) + '\n')
            meta['native_step_wall_s'] += row['native_step_wall_s']
            if not np.isfinite(np.r_[row['state'], row['net_force']]).all():
                raise ValueError('Nonfinite native state or force')
            meta['completed_steps'] += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()

    def interrupt(signum, frame):
        raise KeyboardInterrupt(f'Signal {signum}')

    signal.signal(signal.SIGTERM, interrupt)
    resume(args.input, args.output)
