"""Verify displayed contact forces and piece motion directly from saved arrays."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_studio(media, manifest, measured):
    """Check the optional RTX derivative against the independently checked captions."""
    path = media / 'studio-provenance.json'
    if not path.exists():
        return None
    studio = json.loads(path.read_text())
    if studio['source_artifacts'] != manifest['artifacts'] or studio['physics_steps'] != 0:
        raise ValueError('RTX media does not describe the original saved-state replay')
    frames = studio['frames']
    if len(frames) != len(measured['frames']) or studio['fps'] != 20:
        raise ValueError('RTX frame schedule differs from the complete source schedule')
    for row, original in zip(frames, measured['frames'], strict=True):
        current = row['metrics']
        if (row['sample'] != original['state_frame'] or row['time_s'] != original['time_s']
                or current['state_frame'] != row['sample'] or current['time_s'] != row['time_s']):
            raise ValueError('RTX frame mapping differs from its displayed state')
        for name in ('knife_on_material_n', 'knife_material_force_n', 'centroid_x_from_start_mm',
                     'dynamic_viscosity_pa_s'):
            np.testing.assert_allclose(current[name], original[name], rtol=0, atol=1e-12)
    for name, expected in studio['assets'].items():
        if Path(name).name != name or digest(media / name) != expected:
            raise ValueError(f'RTX artifact changed: {name}')
    with Image.open(media / 'surface-rtx.gif') as gif:
        if gif.n_frames != len(frames):
            raise ValueError('RTX GIF frame inventory differs from its source schedule')
        for frame in range(gif.n_frames):
            gif.seek(frame)
            if gif.info['duration'] != 120:
                raise ValueError('Unexpected RTX GIF playback timing')
    return {'frames_verified':len(frames), 'captions_match_native':True,
            'artifact_hashes_match':True, 'gif_timing_verified':True}


def verify(run, media, planes):
    manifest = json.loads((run / 'manifest.json').read_text())
    for name in ('states.npz', 'trace.npz'):
        if digest(run / name) != manifest['artifacts'][name]:
            raise ValueError(f'Raw record changed: {name}')
    measured = json.loads((media / 'measurements.json').read_text())
    provenance = json.loads((media / 'provenance.json').read_text())
    if provenance['source_artifacts'] != manifest['artifacts']:
        raise ValueError('Media provenance refers to a different raw recording')
    with np.load(run / 'states.npz', allow_pickle=False) as archive:
        states = {key: archive[key] for key in ('reference', 'position', 'time')}
    with np.load(run / 'trace.npz', allow_pickle=False) as archive:
        reaction = archive['material_reaction_n']
    regions = np.digitize(states['reference'][:, 0], planes)
    for frame in measured['frames']:
        if frame['dynamic_viscosity_pa_s'] != manifest['config'].get('dynamic_viscosity', 0.):
            raise ValueError('Displayed viscosity differs from the recorded material')
        index = frame['state_frame']
        time = states['time'][index]
        trace_index = max(0, round(time / manifest['config']['dt']) - 1)
        force = -reaction[trace_index] if index else np.zeros(3)
        displacement = [1000 * np.mean(
            states['position'][index, regions == region, 0]
            - states['reference'][regions == region, 0]) for region in range(len(planes) + 1)]
        np.testing.assert_allclose(frame['knife_on_material_n'], force, rtol=0, atol=1e-12)
        np.testing.assert_allclose(frame['knife_material_force_n'], np.linalg.norm(force), rtol=0, atol=1e-12)
        np.testing.assert_allclose(frame['centroid_x_from_start_mm'], displacement, rtol=0, atol=1e-12)
        if frame['time_s'] != time:
            raise ValueError('Displayed time differs from the saved state')
    if (measured['frames'][0]['time_s'] != 0
            or measured['frames'][-1]['time_s'] != manifest['duration_s']):
        raise ValueError('Media omits the beginning or end of the task')
    for name, expected in provenance['artifacts'].items():
        if Path(name).name != name or digest(media / name) != expected:
            raise ValueError(f'Media changed: {name}')
    for view in ('surface', 'particles'):
        with Image.open(media / f'{view}.gif') as gif:
            if gif.n_frames != len(measured['frames']):
                raise ValueError('GIF frame inventory differs from the measurements')
            for index in range(gif.n_frames):
                gif.seek(index)
                if gif.info['duration'] != 120:
                    raise ValueError('Unexpected GIF playback timing')
    studio = verify_studio(media, manifest, measured)
    return {'task': manifest['task'], 'frames_verified': len(measured['frames']),
            'pieces': len(planes) + 1, 'force_and_displacements_match': True,
            'artifact_hashes_match': True, 'gif_timing_verified': True,
            'material_viscosity_matches': True, 'studio':studio}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tofu-run', type=Path, required=True)
    parser.add_argument('--banana-run', type=Path, required=True)
    parser.add_argument('--media-root', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'docs/evidence/cutting')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reports = [verify(args.tofu_run, args.media_root / 'tofu-cut-push', [-.015, .015]),
               verify(args.banana_run, args.media_root / 'banana-cut-push', [-.03, 0., .03])]
    with args.output.open('x') as stream:
        json.dump({'schema_version': 1, 'state': 'passed', 'checks': reports}, stream, indent=2)
        stream.write('\n')
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()
