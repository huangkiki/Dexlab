"""Reconstruct sampled lagged forces from source equations, without rescoring physics."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from dexlab.drake_incline_score import validate_admission, validate_trace
from dexlab.incline_score import file_hash


def reconstruct(protocol, case, states, rows):
    """Zero-dissipation, isotropic free cube with no additional damping/inertia."""
    config = protocol['drake']
    if config['approximation'] != 'kLagged' or config['dissipation_s_m'] != 0:
        raise ValueError('Reconstruction requires the frozen zero-dissipation lagged fixture')
    mass, h, mu = protocol['mass_kg'], case['timestep'], case['friction']
    inertia = mass * protocol['side_m'] ** 2 / 6
    angle = np.deg2rad(case['angle_deg'])
    plane_normal = np.array([np.sin(angle), 0., np.cos(angle)])
    normal_forces, tangent_forces, counterfactual = [], [], []
    epsilons, directions, side_areas, side_elastic = [], [], [], []
    for i, row in enumerate(rows):
        normal_force, tangent_force, substitute = np.zeros((3, 3))
        side_area = side_force = 0.
        for contact in row['contacts']:
            for face in contact['faces']:
                area = face['area_m2']
                normal = np.asarray(face['normal_into_cube_world'])
                gradient = -np.asarray(face['plane_pressure_gradient_world']) @ normal
                if area <= 1e-14 or gradient < 1e-14:
                    continue  # Same quadrature eligibility as the qualified source.
                lever = np.asarray(face['centroid_world']) - states[i, 1:4]
                velocity = states[i + 1, 8:11] + np.cross(states[i + 1, 11:14], lever)
                vn = normal @ velocity
                vt = velocity - normal * vn
                elastic = area * face['pressure_pa']
                updated_normal = max(0., elastic - h * area * gradient * vn)
                # Native SAP uses a constant diagonal estimate ||W||_F / 3.
                # The norm is invariant to the arbitrary contact tangent basis.
                delassus = np.eye(3) / mass + (
                    (lever @ lever) * np.eye(3) - np.outer(lever, lever)) / inertia
                wt = np.linalg.norm(delassus) / 3
                epsilon = max(config['stiction_tolerance_m_s'], mu * 1e-3 * wt * h * max(0., elastic))
                direction = vt / np.sqrt(vt @ vt + epsilon ** 2)
                normal_force += updated_normal * normal
                tangent_force -= mu * max(0., elastic) * direction
                substitute -= mu * updated_normal * direction
                epsilons.append(epsilon)
                alignment = float(normal @ plane_normal)
                directions.append(alignment)
                if alignment < .99:  # Descriptive side-face grouping, not acceptance.
                    side_area += area
                    side_force += max(0., elastic)
        normal_forces.append(normal_force)
        tangent_forces.append(tangent_force)
        counterfactual.append(normal_force + substitute)
        side_areas.append(side_area)
        side_elastic.append(side_force)
    return (np.asarray(normal_forces), np.asarray(tangent_forces), np.asarray(counterfactual),
            epsilons, directions, side_areas, side_elastic)


def diagnose(root):
    protocol = json.loads((root / 'protocol.json').read_text())
    case = protocol['cases'][0]
    directory = root / case['id']
    meta = json.loads((directory / 'metadata.json').read_text())
    for name, digest in meta['hashes'].items():
        if Path(name).name != name or file_hash(directory / name) != digest:
            raise ValueError('Changed native observation')
    admission = json.loads((directory / 'admission.json').read_text())
    validate_admission(protocol, case, admission)
    with np.load(directory / 'trace.npz', allow_pickle=False) as values:
        trace = dict(values)
    with gzip.open(directory / 'contacts.jsonl.gz', 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    validate_trace(protocol, case, trace, rows)
    states, forces = trace['states'], trace['forces']
    fn, ft, counterfactual, eps, directions, areas, elastic = reconstruct(protocol, case, states, rows)
    error = np.linalg.norm(fn + ft - forces, axis=1)
    angle = np.deg2rad(case['angle_deg'])
    normal = np.array([np.sin(angle), 0., np.cos(angle)])
    tangent = np.array([normal[2], 0., -normal[0]])
    mask = states[:-1, 0] >= protocol['score_start_s'] - 1e-10
    return dict(
        case=case['id'], full_force_reconstruction_max_error_n=float(error.max()),
        full_force_reconstruction_rmse_n=float(np.sqrt(np.mean(error ** 2))),
        normal_component_mean_n=float((fn[mask] @ normal).mean()),
        friction_component_mean_tangent_n=float((ft[mask] @ tangent).mean()),
        native_force_mean_tangent_n=float((forces[mask] @ tangent).mean()),
        lagged_to_updated_normal_counterfactual_force_mean_tangent_n=float((counterfactual[mask] @ tangent).mean()),
        epsilon_soft_range_m_s=[float(min(eps)), float(max(eps))],
        face_normal_dot_plane_range=[min(directions), max(directions)],
        side_area_max_m2=max(areas), side_elastic_force_max_n=max(elastic))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Directory containing the three diagnostic cases')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    observations = [diagnose(root) for root in sorted(args.input.iterdir()) if root.is_dir()]
    result = dict(
        observations=observations, acceptance_changed=False, source_sha256=file_hash(Path(__file__)),
        scope='Source-derived reconstruction, not private native readbacks. The counterfactual holds observed states fixed; it is not a kSimilar simulation. Includes side-face normals and geometry at the update start.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
