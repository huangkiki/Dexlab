"""Descriptive raw measurements; never replace the frozen acceptance result."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.incline_score import file_hash
from dexlab.physx_incline_score import validate_protocol


def summarize(root):
    p = json.loads((root / 'manifest.json').read_text())
    validate_protocol(p)
    observations = []
    for case in p['cases']:
        directory = root / case['id']
        meta = json.loads((directory / 'metadata.json').read_text())
        for name, digest in meta['hashes'].items():
            if Path(name).name != name or file_hash(directory / name) != digest:
                raise ValueError('Changed raw artifact')
        with gzip.open(directory / 'native.jsonl.gz', 'rt') as stream:
            records = [json.loads(line) for line in stream]
        a, rows = records[0], records[1:-1]
        states = np.array([a['initial_state']] + [row['state'] for row in rows])
        h = a['effective_timestep']
        if (len(rows) != round(p['duration_s'] / case['timestep'])
                or not np.isfinite(states).all() or meta['error']):
            raise ValueError('Descriptive measurements require complete finite observations')
        angle = np.deg2rad(case['angle_deg'])
        n, t = np.array([np.sin(angle), 0, np.cos(angle)]), np.array([np.cos(angle), 0, -np.sin(angle)])
        impulses, distances, counts, direction_errors = [], [], [], []
        for row in rows:
            impulse, count, separation = np.zeros(3), 0, 0.
            for pair in row['pairs']:
                sign = 1 if pair['cube_first'] else -1
                for contact in pair['contacts']:
                    raw = sign * np.array(contact['impulse'])
                    direction_errors.append(float(np.max(abs(raw - (raw @ n) * n))))
                    impulse += raw; count += 1; separation = min(separation, contact['separation'])
                for anchor in pair['friction_anchors']: impulse += sign * np.array(anchor['impulse'])
            impulses.append(impulse); distances.append(separation); counts.append(count)
        forces = np.array(impulses) / h
        mass, g = p['mass_kg'], p['gravity_m_s2']
        residual = mass * np.diff(states[:, 8:11], axis=0) - (forces + [0, 0, -mass * g]) * h
        native_residual = a['mass'] * np.diff(states[:, 8:11], axis=0) - (forces + a['mass'] * np.array(a['gravity'])) * h
        mask, fm = states[:, 0] >= p['score_start_s'], states[:-1, 0] >= p['score_start_s']
        tau = states[mask, 0] - states[mask, 0][0]
        position, speed = states[:, 1:4] @ t, states[:, 8:11] @ t
        static = case['regime'] == 'static'
        acceleration = 0 if static else g * (np.sin(angle) - case['friction'] * np.cos(angle))
        target = mass * g * np.cos(angle) * n - mass * g * (np.sin(angle) if static else case['friction'] * np.cos(angle)) * t
        norm = np.linalg.norm(states[:, 4:8], axis=1)
        unit = states[:, 4:8] / norm[:, None]
        initial = np.array([np.cos(angle/2), 0, np.sin(angle/2), 0])
        rmse = lambda v: float(np.sqrt(np.mean(np.square(v))))
        observations.append(dict(case=case['id'], negative=case.get('negative_no_floor', False),
            raw_sha256=meta['hashes']['native.jsonl.gz'], acceptance_calculated=False,
            tangent_displacement_max_m=float(abs(position-position[0]).max()),
            tangent_speed_max_m_s=float(abs(speed[mask]).max()),
            acceleration_fitted_m_s2=float(np.polyfit(tau, speed[mask], 1)[0]),
            acceleration_reference_m_s2=float(acceleration),
            position_rmse_m=rmse(position[mask]-position[mask][0]-speed[mask][0]*tau-.5*acceleration*tau**2),
            velocity_rmse_m_s=rmse(speed[mask]-speed[mask][0]-acceleration*tau),
            force_balance_rmse_n=rmse(np.linalg.norm(forces[fm]-target, axis=1)),
            reported_penetration_max_m=float(max(0,-min(distances))),
            normalized_rotation_max_rad=float(np.max(2*np.arccos(np.clip(abs(unit @ initial),0,1)))),
            quaternion_norm_error_max=float(abs(norm-1).max()),
            impulse_residual_max_ns=float(np.linalg.norm(residual,axis=1).max()),
            native_parameter_impulse_residual_max_ns=float(np.linalg.norm(native_residual,axis=1).max()),
            normal_impulse_direction_error_max_ns=max(direction_errors,default=0),
            contact_count_min=min(counts),contact_count_max=max(counts),
            continuous_support=bool((np.array(counts)[fm]>0).all()),
            native_step_wall_s=records[-1]['native_step_wall_s'],case_wall_s=meta['wall_s'],updates=len(rows)))
    return dict(profile=p['profile'],observations=observations,source_sha256=file_hash(Path(__file__)),
                scope='Posthoc descriptions, including invalid records. No acceptance changes. Rotation uses normalized direction; raw norm drift is reported separately.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(summarize(args.input),stream,indent=2,allow_nan=False);stream.write('\n')
