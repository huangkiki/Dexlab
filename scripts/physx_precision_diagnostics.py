"""Offline descriptive decomposition of retained PhysX incline observations.

No scores or tolerances change. Endpoint FP32 spacing is a diagnostic scale,
not an error bound for the internal solver or a replacement acceptance test.
"""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash
from dexlab.physx_incline_score import score_campaign


def projection_residual(impulse, normal):
    normal = np.asarray(normal, dtype=float)
    normal = normal / np.linalg.norm(normal)
    impulse = np.asarray(impulse, dtype=float)
    return float(np.max(np.abs(impulse - np.dot(impulse, normal) * normal)))


def analyze_case(admission, rows, case, *, nominal_mass, nominal_gravity):
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    mass, h = admission['mass'], admission['effective_timestep']
    gravity = np.asarray(admission['gravity'])
    descriptions = []
    for row in rows:
        impulses, analytical, native = [], [], []
        for pair in row['pairs']:
            sign = 1 if pair['cube_first'] else -1
            for contact in pair['contacts']:
                j = sign * np.asarray(contact['impulse'])
                impulses.append(j)
                analytical.append(projection_residual(j, normal))
                native.append(projection_residual(j, sign * np.asarray(contact['normal'])))
            impulses.extend(sign * np.asarray(a['impulse']) for a in pair['friction_anchors'])
        pre, post = np.asarray(row['pre_state'][8:11]), np.asarray(row['state'][8:11])
        total_impulse = np.sum(impulses, axis=0) if impulses else np.zeros(3)
        residual = mass * (post-pre) - mass * gravity * h - total_impulse
        original = nominal_mass * (post-pre) - np.array([0., 0., -nominal_mass*nominal_gravity]) * h - total_impulse
        # Half the larger adjacent representable gap at each published endpoint.
        def gap(v):
            a = np.asarray(v, dtype=np.float32)
            return np.maximum(np.nextafter(a, np.float32(np.inf)).astype(float)-a,
                              a-np.nextafter(a, np.float32(-np.inf)).astype(float))
        spacing = mass * (gap(pre) + gap(post)) / 2
        descriptions.append(dict(step=row['step'], time_s=row['interval_end_s'],
            residual_vector_ns=residual.tolist(), residual_norm_ns=float(np.linalg.norm(residual)),
            original_residual_norm_ns=float(np.linalg.norm(original)),
            endpoint_half_spacing_ns=spacing.tolist(),
            analytic_normal_residual_ns=max(analytical, default=0.),
            native_normal_residual_ns=max(native, default=0.)))
    peaks = {key: max(descriptions, key=lambda r: r[key]) for key in
             ('residual_norm_ns', 'original_residual_norm_ns', 'analytic_normal_residual_ns', 'native_normal_residual_ns')}
    first = next((r for r in descriptions if r['original_residual_norm_ns'] > 1e-7), None)
    return dict(first_original_momentum_exceedance=first, peaks=peaks, steps=len(rows),
                interpretation='Native readbacks used; endpoint spacing excludes internal arithmetic, impulse rounding and solver error. No new acceptance bound.')


def analyze(root):
    # Verifies protocol, source, case binding and every raw artifact before analysis;
    # numerical/physical failures remain results rather than disappearing.
    original = score_campaign(root)
    protocol = json.loads((root / 'manifest.json').read_text())
    cases = []
    for case, score in zip(protocol['cases'], original['results'], strict=True):
        path = root / case['id'] / 'native.jsonl.gz'
        with gzip.open(path, 'rt') as stream:
            records = [json.loads(line) for line in stream]
        cases.append(dict(case=case['id'], raw_sha256=file_hash(path), original_score=score,
                          diagnostics=analyze_case(records[0], records[1:-1], case, nominal_mass=protocol['mass_kg'], nominal_gravity=protocol['gravity_m_s2'])))
    return dict(profile=protocol['profile'], protocol_sha256=file_hash(root / 'manifest.json'),
                source_sha256=file_hash(Path(__file__)), cases=cases,
                scope='Offline diagnostics only; original scores unchanged; zero native launches')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.input)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
