"""Audit saved two-pad contact geometry and angular momentum without integration.

This post-hoc diagnosis does not change the frozen task acceptance.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

import scene
from plan_wuji_pinch import PAD_CONTACT_POINTS
from score import evaluate
from wrench import point_force_map


def analyze(directory, robot_assets):
    """Return diagnostics plus fixed pad-marker motion every 20 native steps."""
    run = Path(directory)
    acceptance = evaluate(run)
    if not acceptance['record_integrity_pass']:
        raise ValueError('Diagnose a complete, internally consistent record first')
    prefab_path = Path(robot_assets) / scene.PREFAB
    prefab = json.loads(prefab_path.read_text())
    manifest = json.loads((run / 'manifest.json').read_text())
    plan = json.loads((run / 'model/plan.json').read_text())
    if hashlib.sha256(prefab_path.read_bytes()).hexdigest() != plan['source_prefab_sha256']:
        raise ValueError('Source robot prefab differs from this attempt')
    path = run / 'observations.npz'
    with np.load(path, allow_pickle=False) as archive:
        raw = dict(archive)
    config, effective = manifest['config'], manifest['effective']
    t, dt = raw['time_s'], effective['timestep']
    hold = (t >= config['hold_start_s']) & (t < config['action_start_s'])
    hold_indices = np.flatnonzero(hold)
    wrist = Rotation.from_quat(plan['wrist_quaternion'])
    wrist_position = np.array(plan['wrist_position'])
    anchor_index = round(config['support_end_s'] / dt)

    def pad_markers(index):
        poses = scene.kinematics(prefab, raw['qpos_before'][index, :20])
        points = []
        for finger in ('index_finger', 'thumb'):
            position, rotation = poses['r_' + finger + '_pad']
            points.append(wrist_position + wrist.apply(position + rotation.apply(PAD_CONTACT_POINTS[finger])))
        return np.array(points)

    anchor_markers = pad_markers(anchor_index)
    anchor_center = raw['qpos_before'][anchor_index, 20:23]
    anchor_relative = anchor_center - anchor_markers.mean(axis=0)
    samples = []
    for i in hold_indices[::20]:
        markers = pad_markers(i)
        center = raw['qpos_before'][i, 20:23]
        samples.append([t[i], np.linalg.norm(markers.mean(axis=0)-anchor_markers.mean(axis=0)),
                        np.linalg.norm(center-markers.mean(axis=0)-anchor_relative),
                        *np.linalg.norm(markers-anchor_markers, axis=1)])

    pads = [effective['body_names'].index('r_' + finger + '_pad') for finger in ('index_finger', 'thumb')]
    gravity_force = effective['object_mass'] * np.asarray(effective['gravity'])
    inertia = np.asarray(effective['object_inertia'])
    if not np.allclose(inertia, inertia[0], rtol=0, atol=1e-16):
        raise ValueError('This angular audit requires the declared isotropic object inertia')
    before_rot = Rotation.from_quat(raw['qpos_before'][:, [24, 25, 26, 23]])
    after_rot = Rotation.from_quat(raw['qpos_after'][:, [24, 25, 26, 23]])
    omega_before = before_rot.apply(raw['qvel_before'][:, 23:26])
    omega_after = after_rot.apply(raw['qvel_after'][:, 23:26])
    rotation_change = (before_rot[anchor_index].inv() * before_rot).magnitude()
    torques = np.zeros((len(t), 3))
    ranks, axis_moments, axis_offsets, counts, intrinsic_moments = [], [], [], [], []
    spin_speeds = []
    ratios = []
    for i in hold_indices:
        a, b = raw['contact_offsets'][i:i+2]
        contacts = raw['contacts'][a:b]
        active = [c for c in contacts if c[16] > config['min_pad_normal_n']]
        counts.append(len(active))
        center = raw['qpos_before'][i, 20:23]
        for c in contacts:
            sign = 1 if int(c[1]) == effective['object_geom_id'] else -1
            frame = c[6:15].reshape(3, 3)
            force = sign * frame.T @ c[16:19]
            moment = sign * frame.T @ c[19:22]
            torques[i] += np.cross(c[3:6]-center, force) + moment
            intrinsic_moments.append(float(np.linalg.norm(moment)))
            if c[16] > config['min_pad_normal_n']:
                ratios.append(np.linalg.norm(c[17:19]) / c[16])
        if len(active) != 2 or {int(c[2]) for c in active} != set(pads):
            continue
        active.sort(key=lambda contact: pads.index(int(contact[2])))
        p1, p2 = (c[3:6] for c in active)
        axis = p2 - p1
        if np.linalg.norm(axis) < 1e-12:
            continue
        axis /= np.linalg.norm(axis)
        spin_speeds.append(float(omega_before[i] @ axis))
        axis_moments.append(float(axis @ np.cross(center-p1, gravity_force)))
        axis_offsets.append(float(np.linalg.norm(np.cross(center-p1, axis))))
        matrix = point_force_map([p1, p2], center, config['radius_m'])
        singular = np.linalg.svd(matrix, compute_uv=False)
        ranks.append(int(np.count_nonzero(singular > 1e-10)))
    residual = inertia[0] * (omega_after-omega_before) - dt * torques
    samples = np.asarray(samples)
    report = dict(attempt=run.name, raw_sha256=manifest['observations_sha256'],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        wrench_source_sha256=hashlib.sha256(Path(__file__).with_name('wrench.py').read_bytes()).hexdigest(),
        hold_steps=int(hold.sum()), active_contact_counts=sorted(set(counts)),
        measured_force_only_grasp_matrix_ranks=sorted(set(ranks)),
        rank_evaluated_steps=len(ranks), maximum_intrinsic_contact_moment_nm=max(intrinsic_moments, default=0.),
        gravity_moment_about_contact_chord_nm=(dict(min=min(axis_moments), max=max(axis_moments),
                                                  max_abs=max(abs(x) for x in axis_moments)) if axis_moments else None),
        com_distance_from_contact_chord_m=(dict(min=min(axis_offsets), max=max(axis_offsets)) if axis_offsets else None),
        tangential_over_normal_range=([min(ratios), max(ratios)] if ratios else None),
        angular_impulse_residual_max_nms=float(np.linalg.norm(residual[hold], axis=1).max()),
        object_rotation_from_support_removal_max_rad=float(rotation_change[hold].max()),
        rotation_metric='Principal relative angle in [0, pi], not unwrapped turns.',
        hold_rotation_path_length_rad=float((before_rot[hold_indices].inv() * after_rot[hold_indices]).magnitude().sum()),
        hold_angular_speed_max_rad_s=float(np.linalg.norm(omega_before[hold], axis=1).max()),
        angular_velocity_world_at_support_removal_rad_s=omega_before[anchor_index].tolist(),
        preparation_angular_speed_max_rad_s=float(np.linalg.norm(omega_before[t < config['support_end_s']], axis=1).max()),
        angular_speed_about_contact_chord_range_rad_s=([min(spin_speeds), max(spin_speeds)] if spin_speeds else None),
        sampled_marker_motion=dict(stride_steps=20, interval_s=20*dt,
            marker='Fixed source IK contact reference points on the two pads; not a claim that the actual contact stays at these markers.',
            midpoint_max_displacement_m=float(samples[:,1].max()),
            object_relative_midpoint_max_displacement_m=float(samples[:,2].max()),
            individual_pad_marker_max_displacement_m=np.max(samples[:,3:],axis=0).tolist()),
        equations=dict(grasp_matrix='[I,I; skew(p1-COM)/r,skew(p2-COM)/r]; numerical rank threshold1e-10 after length scaling.',
            chord_moment='axis dot ((COM-p1) cross m*g); point forces at p1,p2 cannot supply moment about their connecting line.',
            angular_balance='Isotropic sphere: I*(R_after*w_local_after - R_before*w_local_before) - h*sum((contact_pos-COM_before) cross F_world + moment_world).',
            boundary='Post-hoc diagnosis, not a new acceptance criterion. Rank5 does not rule out special static gravity equilibria; changing contacts/moving fingers prevent treating this as a fixed-pivot pendulum proof.'))
    return report, samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--robot-assets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        raise ValueError('Write diagnostics outside the immutable input attempt')
    report, samples = analyze(args.directory, args.robot_assets)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'diagnosis.json').write_text(json.dumps(report, indent=2) + '\n')
    np.savetxt(args.output / 'marker-motion.csv', samples, delimiter=',',
               header='time_before_s,pad_midpoint_displacement_m,object_relative_midpoint_displacement_m,index_marker_displacement_m,thumb_marker_displacement_m', comments='')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
