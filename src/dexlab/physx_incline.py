"""Run one native PhysX process per case and retain every raw observation."""

import argparse
import gzip
import json
from pathlib import Path
import shutil
import signal
import subprocess
import time

from dexlab.incline_score import file_hash


def checkpoint(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def run(protocol_path, proof_path, binary, output, admission_only=False):
    from dexlab.physx_incline_score import validate_admission, validate_protocol

    protocol = json.loads(protocol_path.read_text())
    validate_protocol(protocol)
    proof = json.loads(proof_path.read_text())
    if (file_hash(binary) != protocol['binary_sha256']
            or proof['binary_sha256'] != protocol['binary_sha256']
            or proof['recorder_sha256'] != protocol['recorder_sha256']
            or proof['source_commit'] != protocol['source_commit']):
        raise ValueError('Unqualified native recorder or SDK identity')
    if not admission_only and protocol['runner_sha256'] != file_hash(Path(__file__)):
        raise ValueError('Runner differs from frozen source')
    output.mkdir(parents=True, exist_ok=False)
    for source, name in [(protocol_path, 'manifest.json'), (proof_path, 'official-proof.json'),
                         (Path(__file__), 'runner.py')]:
        shutil.copyfile(source, output / name)
    campaign = dict(state='running', admission_only=admission_only, cases=[],
                    protocol_sha256=file_hash(protocol_path), proof_sha256=file_hash(proof_path),
                    runner_sha256=file_hash(Path(__file__)), binary_sha256=file_hash(binary),
                    clock='requested step, native FP32 step and native scene timestamp all recorded')
    checkpoint(output / 'campaign.json', campaign)
    for case in protocol['cases']:
        directory = output / case['id']
        directory.mkdir()
        steps = 0 if admission_only else round(protocol['duration_s'] / case['timestep'])
        command = [str(binary), protocol['profile'], str(case['angle_deg']), str(case['friction']),
                   str(case['timestep']), str(steps), str(int(case.get('negative_no_floor', False))), '0']
        meta = dict(case=case, requested_steps=steps, returncode=None, error=None)
        started = time.perf_counter()
        interrupted = False
        try:
            with (directory / 'native.jsonl').open('x') as stream, (directory / 'stderr.txt').open('x') as errors:
                child = subprocess.Popen(command, stdout=stream, stderr=errors)
                try:
                    meta['returncode'] = child.wait()
                except KeyboardInterrupt:
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    meta['returncode'] = child.returncode
                    raise
            with (directory / 'native.jsonl').open() as stream:
                admission = json.loads(next(stream))
            validate_admission(protocol, case, admission)
            checkpoint(directory / 'admission.json', admission)
            if not admission_only and file_hash(directory / 'admission.json') != protocol['admission_sha256'][case['id']]:
                raise ValueError('Native parameters differ from frozen admission')
            if meta['returncode']:
                raise RuntimeError(f'Native process returned {meta["returncode"]}')
        except (Exception, KeyboardInterrupt) as error:
            meta['error'] = f'{type(error).__name__}: {error}'
            interrupted = isinstance(error, KeyboardInterrupt)
        meta['wall_s'] = time.perf_counter() - started
        # Compress only after the native process exits; preserve the exact bytes.
        raw = directory / 'native.jsonl'
        if raw.exists():
            with raw.open('rb') as source, gzip.open(directory / 'native.jsonl.gz', 'xb') as destination:
                shutil.copyfileobj(source, destination)
            with gzip.open(directory / 'native.jsonl.gz', 'rb') as stream:
                if stream.read() != raw.read_bytes():
                    raise ValueError('Raw compression verification failed')
            raw.unlink()
        meta['hashes'] = {p.name: file_hash(p) for p in directory.iterdir()}
        checkpoint(directory / 'metadata.json', meta)
        campaign['cases'].append(meta)
        if interrupted:
            campaign['state'] = 'interrupted'
        checkpoint(output / 'campaign.json', campaign)
        if interrupted:
            raise KeyboardInterrupt('Interrupted native observations preserved')
    campaign['state'] = 'completed'
    checkpoint(output / 'campaign.json', campaign)
    if any(c['error'] for c in campaign['cases']):
        raise RuntimeError('Native errors retained; campaign requires independent scoring')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--proof', required=True, type=Path)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--admission-only', action='store_true')
    args = parser.parse_args()

    def interrupt(signum, frame):
        raise KeyboardInterrupt(f'Signal {signum}')

    signal.signal(signal.SIGTERM, interrupt)
    run(args.protocol, args.proof, args.binary, args.output, args.admission_only)
