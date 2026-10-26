"""Replay complete saved landing poses with their recorded native force curves."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def control_samples(native, protocol):
    """Keep the initial state and every completed control boundary, including the last."""
    controls = protocol['control_steps']
    stride = protocol['substeps_per_control']
    steps = controls * stride
    pre, post = native['pre_qpos'], native['qpos']
    before, after = native['native_time_before'], native['native_time_after']
    if (pre.ndim != 2 or pre.shape != post.shape or len(pre) != steps
            or before.shape != (steps,) or after.shape != (steps,)
            or not all(np.isfinite(a).all() for a in (pre, post, before, after))
            or np.any(after <= before) or not np.array_equal(before[1:], after[:-1])):
        raise ValueError('Incomplete, nonfinite or discontinuous native record')
    ends = np.arange(stride - 1, steps, stride)
    poses = np.concatenate((pre[:1], post[ends]))
    times = np.r_[before[0], after[ends]]
    return poses, times, np.r_[-1, ends]


def load_record(directory, protocol_path):
    invocation = json.loads((directory / 'invocation.json').read_text())
    audit_path = directory / 'audit.json'
    audit = json.loads(audit_path.read_text())
    protocol_sha = digest(protocol_path)
    if (invocation['status'] != 'completed'
            or invocation['protocol_sha256'] != protocol_sha
            or audit['protocol_sha256'] != protocol_sha
            or audit['state_alignment']['aligned'] is not True
            or not isinstance(audit['geometry_reconstruction'], dict)):
        raise ValueError('Replay requires a completed, aligned independent native audit')
    hashes = audit['input_sha256']
    required = {'rollout.npz', 'contact_forces_200hz.npz', 'native_contacts.npz',
                'warp_candidates.npz', 'native_metadata.json', 'native_model.mjb'}
    if not required.issubset(hashes):
        raise ValueError('Independent audit lacks the complete native inputs')
    for name in required:
        if digest(directory / name) != hashes[name]:
            raise ValueError('Native input changed after audit: ' + name)
    with np.load(directory / 'contact_forces_200hz.npz', allow_pickle=False) as archive:
        native = dict(archive)
    protocol = json.loads(protocol_path.read_text())
    poses, times, force_indices = control_samples(native, protocol)
    steps = protocol['control_steps'] * protocol['substeps_per_control']
    for name, shape in (('forces', (steps, 2, 3)), ('nonfoot_force', (steps, 3))):
        if native[name].shape != shape or not np.isfinite(native[name]).all():
            raise ValueError('Invalid native force channel: ' + name)
    return protocol, native, poses, times, force_indices, {
        **{name: hashes[name] for name in sorted(required)},
        'audit.json': digest(audit_path), 'invocation.json': digest(directory / 'invocation.json'),
        'protocol.json': protocol_sha,
    }


def set_display_pose(mujoco, model, data, pose):
    """Update geometry and lights only; never compute contacts, forces or a new state."""
    data.qpos[:] = pose
    mujoco.mj_kinematics(model, data)
    mujoco.mj_camlight(model, data)
    if not np.array_equal(data.qpos, pose):
        raise ValueError('Display kinematics changed the recorded pose')


def force_panel(native, poses, times, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image

    # This is the observed substep boundary, not a separately measured cache timestamp.
    force_time = native['native_time_before']
    figure, axes = plt.subplots(3, 1, figsize=(3.84, 6.72), dpi=100)
    figure.patch.set_facecolor('#f8fafc')
    for axis in axes:
        axis.set_facecolor('#f8fafc')
        axis.grid(alpha=.2)
        axis.tick_params(labelsize=8)
        axis.set_xlim(float(times[0]), float(times[-1]))
    axes[0].plot(force_time, native['forces'][:, 0, 2], label='Left foot', lw=1, color='#087f8c')
    axes[0].plot(force_time, native['forces'][:, 1, 2], label='Right foot', lw=1, color='#e07a2d')
    axes[0].axhline(float(native['mass']) * 9.81, color='#6b7280', lw=.8, ls='--', label='Whole weight')
    axes[0].set_ylabel('Vertical force [N]', fontsize=9)
    axes[0].legend(fontsize=7, loc='upper right')
    axes[0].set_title('Native forces | 200 Hz', fontsize=11, loc='left')
    axes[1].plot(times, poses[:, 2], color='#3559a8', lw=1.3)
    axes[1].set_ylabel('Pelvis height [m]', fontsize=9)
    axes[1].set_title('Saved poses | 50 Hz', fontsize=11, loc='left')
    magnitude = np.linalg.norm(native['nonfoot_force'], axis=1)
    axes[2].plot(force_time, magnitude, color='#a33a62', lw=1.2)
    axes[2].set_ylim(0, max(1., float(magnitude.max()) * 1.05))
    axes[2].set_ylabel('Nonfoot resultant [N]', fontsize=9)
    axes[2].set_xlabel('Native boundary clock [s]', fontsize=9)
    axes[2].set_title('Recorded ground force on other bodies', fontsize=9, loc='left')
    figure.tight_layout(pad=1.6)
    figure.savefig(output / 'curves.svg')
    figure.savefig(output / 'curves.png')
    figure.canvas.draw()
    panel = Image.fromarray(np.asarray(figure.canvas.buffer_rgba())[:, :, :3].copy())
    boxes = []
    for axis in axes:
        box = axis.get_window_extent()
        boxes.append((box.x0, panel.height - box.y1, box.x1, panel.height - box.y0))
    plt.close(figure)
    return panel, boxes


def render(directory, protocol_path, output):
    from PIL import Image, ImageDraw, ImageFont
    os.environ.setdefault('MUJOCO_GL', 'egl')
    import mujoco

    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        raise ValueError('The existing system ffmpeg executable is required for encoding')
    protocol, native, poses, times, force_indices, hashes = load_record(directory, protocol_path)
    metadata = json.loads((directory / 'native_metadata.json').read_text())
    if mujoco.__version__ != metadata['mujoco_version']:
        raise ValueError('Replay requires the recorded native MuJoCo version')
    model = mujoco.MjModel.from_binary_path(str(directory / 'native_model.mjb'))
    if poses.shape[1] != model.nq:
        raise ValueError('Recorded poses do not match the native model')
    control_dt = protocol['physics_dt_s'] * protocol['substeps_per_control']
    fps = 1 / control_dt
    if fps != 50 or len(poses) != protocol['control_steps'] + 1:
        raise ValueError('This complete reference replay requires every 50 Hz boundary')
    output.mkdir(parents=True, exist_ok=False)
    record = {
        'schema_version': 1, 'status': 'started', 'input_sha256': hashes,
        'renderer_source_sha256': digest(Path(__file__)), 'mujoco_version': mujoco.__version__,
        'scope': 'Saved native poses; mj_kinematics and mj_camlight only. No physics integration, collision or replacement force.',
        'force_axis': 'native_time_before: substep boundary, not an independently timestamped collision cache',
        'frame_force': 'Last completed substep; no force sample at the initial pose',
        'fps': fps, 'expected_frames': len(poses), 'frames_completed': 0,
        'native_state_span_s': float(times[-1] - times[0]),
        'presentation_duration_s': len(poses) / fps,
        'duration_note': 'Every boundary has one video frame, so the final endpoint remains visible for one additional frame.',
        'frame_map': [],
    }
    manifest = output / 'replay.json'
    manifest.write_text(json.dumps(record, indent=2) + '\n')
    started = time.monotonic()
    try:
        panel, boxes = force_panel(native, poses, times, output)
        model.vis.global_.offwidth, model.vis.global_.offheight = 896, 672
        model.vis.headlight.active = 1
        model.vis.headlight.ambient[:] = [.45] * 3
        model.vis.headlight.diffuse[:] = [.7] * 3
        model.geom_rgba[:, 3] = 1
        floor = metadata['floor']
        model.geom_rgba[floor] = [.55, .66, .72, 1]
        option = mujoco.MjvOption()
        option.geomgroup[:] = 1
        w, x, y, z = poses[0, 3:7]
        heading = np.degrees(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [(poses[:, 0].min() + poses[:, 0].max()) / 2,
                            (poses[:, 1].min() + poses[:, 1].max()) / 2, .85]
        camera.distance, camera.azimuth, camera.elevation = 2.9, heading + 65, -18
        record['camera'] = {'lookat': camera.lookat.tolist(), 'distance': camera.distance,
                            'azimuth': camera.azimuth, 'elevation': camera.elevation,
                            'fixed': True}
        record['display_only_changes'] = {
            'headlight_ambient': [.45] * 3, 'headlight_diffuse': [.7] * 3,
            'all_native_geom_groups_visible': True, 'all_native_geom_alpha': 1,
            'floor_geoms': floor, 'floor_rgba': [.55, .66, .72, 1],
            'scope': 'Native model shapes; display settings change only this in-memory rendering copy.'}
        data = mujoco.MjData(model)
        font = ImageFont.load_default(size=18)
        small = ImageFont.load_default(size=15)
        previews = {0, 80, 115, 160, len(poses) - 1}
        encoder_command = [ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'error', '-n',
                           '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1280x720',
                           '-framerate', str(fps), '-i', 'pipe:0', '-an', '-c:v', 'libx264',
                           '-crf', '20', '-threads', '1', '-filter_threads', '1',
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output / 'replay.mp4')]
        record['encoder_version'] = subprocess.check_output([ffmpeg, '-version'], text=True).splitlines()[0]
        with mujoco.Renderer(model, height=672, width=896) as renderer, (output / 'encoder.log').open('xb') as log:
            encoder = subprocess.Popen(encoder_command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            try:
                for index, (pose, timestamp, force_index) in enumerate(zip(poses, times, force_indices)):
                    set_display_pose(mujoco, model, data, pose)
                    renderer.update_scene(data, camera=camera, scene_option=option)
                    canvas = Image.new('RGB', (1280, 720), '#17242c')
                    canvas.paste(Image.fromarray(renderer.render()), (0, 48))
                    current_panel = panel.copy()
                    cursor = ImageDraw.Draw(current_panel)
                    fraction = float((timestamp - times[0]) / (times[-1] - times[0]))
                    for left, top, right, bottom in boxes:
                        x = left + fraction * (right - left)
                        cursor.line((x, top, x, bottom), fill='#be123c', width=2)
                    canvas.paste(current_panel, (896, 48))
                    draw = ImageDraw.Draw(canvas)
                    draw.text((16, 8), f'G1 backflip | {directory.name} | saved-pose replay', font=font, fill='white')
                    draw.text((16, 29), f'Native t={timestamp:.5f} s | frame {index + 1}/{len(poses)} | physics is not rerun', font=small, fill='#cbd5e1')
                    encoder.stdin.write(canvas.tobytes())
                    if index in previews:
                        canvas.save(output / f'frame-{index:04d}.png')
                    record['frame_map'].append({'frame': index, 'control_boundary': index,
                                                 'native_time_s': float(timestamp),
                                                 'last_completed_force_substep': int(force_index) if force_index >= 0 else None})
                    record['frames_completed'] = index + 1
                    if index % 100 == 0:
                        print(f'{directory.name}: rendered {index + 1}/{len(poses)}', flush=True)
            finally:
                try:
                    encoder.stdin.close()
                except BrokenPipeError:
                    pass
                encoder_status = encoder.wait()
            if encoder_status != 0:
                raise RuntimeError('Video encoder failed; retain encoder.log and partial outputs')
        record.update(status='completed', video_sha256=digest(output / 'replay.mp4'),
                      curve_sha256={name: digest(output / name) for name in ('curves.svg', 'curves.png')})
    except BaseException as error:
        record.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        record['render_encode_wall_s'] = time.monotonic() - started
        manifest.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    render(args.directory, args.protocol, args.output)
