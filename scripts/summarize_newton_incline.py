"""Descriptive measurements of Newton traces, including rejected records.

This does not calculate acceptance or change the frozen scorer. Quaternion
direction is normalized only for the separately labeled geometric diagnostic.
"""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash
from dexlab.newton_incline_score import EPS32, validate_protocol


def summarize(root):
    protocol = json.loads((root / 'manifest.json').read_text())
    validate_protocol(protocol)
    measurements = []
    for case in protocol['cases']:
        directory = root / case['id']
        meta = json.loads((directory / 'metadata.json').read_text())
        for name, digest in meta['hashes'].items():
            if Path(name).name != name or file_hash(directory / name) != digest:
                raise ValueError('Changed raw observation')
        with gzip.open(directory / 'steps.jsonl.gz', 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        admission = json.loads((directory / 'admission.json').read_text())
        states = np.array([admission['initial_state']] + [r['state'] for r in rows])
        forces = np.array([r['net_force'] for r in rows])
        if (len(rows) != round(protocol['duration_s'] / case['timestep'])
                or not np.isfinite(states).all() or not np.isfinite(forces).all()):
            raise ValueError('Diagnostic requires a complete finite trace')
        h, mass, gravity = case['timestep'], protocol['mass_kg'], protocol['gravity_m_s2']
        angle = np.deg2rad(case['angle_deg'])
        normal = np.array([np.sin(angle), 0., np.cos(angle)])
        tangent = np.array([np.cos(angle), 0., -np.sin(angle)])
        position, velocity = states[:, 1:4] @ tangent, states[:, 8:11] @ tangent
        mask = states[:, 0] >= protocol['score_start_s'] - 1e-10
        force_mask = states[:-1, 0] >= protocol['score_start_s'] - 1e-10
        time = states[mask, 0] - states[mask, 0][0]
        static = case['regime'] == 'static'
        acceleration = 0. if static else gravity * (np.sin(angle) - case['friction'] * np.cos(angle))
        target = mass * gravity * np.cos(angle) * normal
        target -= mass * gravity * (np.sin(angle) if static else case['friction'] * np.cos(angle)) * tangent
        qnorm = np.linalg.norm(states[:, 4:8], axis=1)
        unit = states[:, 4:8] / qnorm[:, None]
        initial = np.array([np.cos(angle / 2), 0, np.sin(angle / 2), 0])
        local_normal = normal + 2 * np.cross(-unit[:, 1:],
                            np.cross(-unit[:, 1:], normal) + unit[:, :1] * normal)
        lowest = states[:, 1:4] @ normal - protocol['side_m'] / 2 * np.abs(local_normal).sum(axis=1)
        delta = np.diff(states[:, 1:4], axis=0) - states[1:, 8:11] * h
        bound = 8 * EPS32 * (abs(states[:-1, 1:4]) + abs(states[1:, 8:11] * h) + protocol['side_m'])
        residual = mass * np.diff(states[:, 8:11], axis=0) - (forces + [0, 0, -mass * gravity]) * h
        counts = np.array([len(row['contacts']['shape0']) for row in rows])
        rmse = lambda x: float(np.sqrt(np.mean(np.square(x))))
        measurements.append(dict(
            case=case['id'], negative=case.get('negative_no_floor', False),
            trace_sha256=meta['hashes']['steps.jsonl.gz'], acceptance_calculated=False,
            tangent_displacement_max_m=float(np.max(abs(position - position[0]))),
            tangent_speed_max_m_s=float(np.max(abs(velocity[mask]))),
            fitted_acceleration_m_s2=float(np.polyfit(time, velocity[mask], 1)[0]),
            reference_acceleration_m_s2=float(acceleration),
            velocity_rmse_m_s=rmse(velocity[mask] - velocity[mask][0] - acceleration * time),
            position_rmse_m=rmse(position[mask] - position[mask][0] - velocity[mask][0] * time - .5 * acceleration * time**2),
            force_rmse_n=rmse(np.linalg.norm(forces[force_mask] - target, axis=1)),
            force_magnitude_max_n=float(np.max(np.linalg.norm(forces, axis=1))),
            quaternion_norm_error_max=float(np.max(abs(qnorm - 1))),
            rotation_unit_direction_max_rad=float(np.max(2 * np.arccos(np.clip(abs(unit @ initial), 0, 1)))),
            penetration_unit_direction_max_m=float(max(0., -lowest.min())),
            position_velocity_error_max_m=float(abs(delta).max()),
            position_velocity_bound_ratio_max=float(np.max(abs(delta) / bound)),
            impulse_residual_max_ns=float(np.max(np.linalg.norm(residual, axis=1))),
            continuous_support=bool((counts[force_mask] > 0).all()),
            contact_count_min=int(counts.min()), contact_count_max=int(counts.max())))
    return dict(profile=protocol['profile'], measurements=measurements,
                source_sha256=file_hash(Path(__file__)),
                scope='Posthoc descriptive measurements, including invalid records. No acceptance or replacement scores. Geometric orientation diagnostics use normalized quaternion direction; raw norm drift stays explicit.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(summarize(args.input), stream, indent=2, allow_nan=False)
        stream.write('\n')
