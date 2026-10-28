"""Full saved-pose AMP replay with independently decoded native-force curves."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from dexlab.libero_substeps import read_chunk


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def control_samples(initial, actions, force_time, protocol, time_dtype):
    """Retain the initial pose and every pre-reset control endpoint."""
    stride = protocol['conditions']['decimation']
    dt = protocol['conditions']['physics_dt_s']
    force_time = np.asarray(force_time)
    if (force_time.shape != (len(actions) * stride,) or not len(actions)
            or not np.isfinite(force_time).all() or np.any(np.diff(force_time) <= 0)
            or float(initial['time']) != force_time[0]):
        raise ValueError('Incomplete or inconsistent native clock')
    poses, times = [np.asarray(initial['qpos'])], [float(initial['time'])]
    indices = [-1]
    for index, action in enumerate(actions):
        feedback = action['feedback']
        last = (index + 1) * stride - 1
        expected = float(np.asarray(force_time[last], dtype=time_dtype)
                         + np.asarray(dt, dtype=time_dtype))
        pose = np.asarray(feedback['qpos'])
        if (action['status'] != 'completed' or action['action_index'] != index
                or feedback['automatic_reset'] != (index + 1 == 3000)
                or feedback['native_time'] != expected or pose.shape != poses[0].shape):
            raise ValueError('Control endpoint does not match its completed native substep')
        # returned_observations may describe a new episode. Never use them here.
        poses.append(pose)
        times.append(expected)
        indices.append(last)
    poses = np.asarray(poses)
    if poses.ndim != 2 or not np.isfinite(poses).all():
        raise ValueError('Nonfinite or malformed saved poses')
    return poses, np.asarray(times), np.asarray(indices)


def load_record(directory, audit_directory, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    invocation = json.loads((directory / 'invocation.json').read_text())
    report_path = audit_directory / 'diagnostics.json'
    report = json.loads(report_path.read_text())
    metadata = json.loads((directory / 'native/recording.json').read_text())
    case = invocation['case']
    if (invocation['status'] != 'completed' or report['record_integrity'] != 'passed'
            or invocation['protocol_sha256'] != digest(protocol_path)
            or case not in protocol['cases'] or report['case'] != case
            or not case['record_substeps'] or metadata['status'] != 'completed'
            or invocation['completed_actions'] != case['actions']):
        raise ValueError('Replay requires a complete independently audited recorded case')
    expected = {'invocation.json', 'initial-state.npz', 'native/recording.json',
                'native/effective-model.npz'}
    for index in range(case['actions']):
        expected.update(f'{folder}/action-{index:06d}.npz'
                        for folder in ('actions', 'native/substeps'))
    if set(report['evidence_sha256']) != expected:
        raise ValueError('Independent audit does not cover the whole episode')
    for name, checksum in report['evidence_sha256'].items():
        if digest(directory / name) != checksum:
            raise ValueError('Input changed after independent scoring: ' + name)
    series_path = audit_directory / 'diagnostic-series.npz'
    if digest(series_path) != report['series_sha256']:
        raise ValueError('Diagnostic series changed after scoring')
    with np.load(series_path, allow_pickle=False) as archive:
        series = dict(archive)
    initial = read_chunk(directory / 'initial-state.npz')
    actions = [read_chunk(directory / f'actions/action-{index:06d}.npz')
               for index in range(case['actions'])]
    if len(initial) != 1 or any(len(rows) != 1 for rows in actions):
        raise ValueError('Invalid initial/control record extent')
    poses, times, indices = control_samples(initial[0], [rows[0] for rows in actions],
                                           series['time_s'], protocol, metadata['time_dtype'])
    total = case['actions'] * protocol['conditions']['decimation']
    for name, shape in (('support_force_n', (total, 4, 3)), ('root_height_m', (total,)),
                        ('tilt_rad', (total,)), ('penetration_m', (total,))):
        if series[name].shape != shape or not np.isfinite(series[name]).all():
            raise ValueError('Invalid diagnostic channel: ' + name)
    hashes = {**report['evidence_sha256'], 'protocol.json': digest(protocol_path),
              'diagnostics.json': digest(report_path), 'diagnostic-series.npz': digest(series_path),
              'native/compiled-template.mjb': digest(directory / 'native/compiled-template.mjb')}
    return protocol, invocation, report, series, poses, times, indices, hashes


def set_display_pose(mujoco, model, data, pose):
    """Compute display geometry only; do not integrate, collide or solve forces."""
    data.qpos[:] = pose
    mujoco.mj_kinematics(model, data)
    mujoco.mj_camlight(model, data)
    if not np.array_equal(data.qpos, pose):
        raise ValueError('Display kinematics changed the saved pose')


def force_panel(series, report, times, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image

    figure, axes = plt.subplots(3, 1, figsize=(3.84, 6.72), dpi=100)
    figure.patch.set_facecolor('#f8fafc')
    for axis in axes:
        axis.set_facecolor('#f8fafc')
        axis.grid(alpha=.2)
        axis.tick_params(labelsize=8)
        axis.set_xlim(times[0], times[-1])
    clock = series['time_s']
    for index, (name, color) in enumerate(zip(('Left hand', 'Right hand', 'Ground', 'Other'),
                                             ('#087f8c', '#e07a2d', '#6b7280', '#a33a62'))):
        axes[0].plot(clock, series['support_force_n'][:, index, 2], label=name, lw=1, color=color)
    axes[0].set_title('Native object force | 200 Hz', fontsize=11, loc='left')
    axes[0].set_ylabel('Vertical force [N]', fontsize=9)
    axes[0].legend(fontsize=7)
    axes[1].plot(clock, series['root_height_m'], color='#3559a8', lw=1)
    axes[1].axhline(report['required_root_height_m'], color='#6b7280', ls='--', lw=.8)
    axes[1].set_ylabel('Object root height [m]', fontsize=9)
    axes[1].set_title('Native derived-state epoch', fontsize=10, loc='left')
    axes[2].plot(clock, series['penetration_m'] * 1000, color='#a33a62', lw=1)
    axes[2].set_ylabel('Contact penetration [mm]', fontsize=9)
    axes[2].set_xlabel('Native step boundary clock [s]', fontsize=9)
    figure.tight_layout(pad=1.6)
    figure.savefig(output / 'curves.png')
    figure.savefig(output / 'curves.svg')
    figure.canvas.draw()
    panel = Image.fromarray(np.asarray(figure.canvas.buffer_rgba())[:, :, :3].copy())
    boxes = []
    for axis in axes:
        box = axis.get_window_extent()
        boxes.append((box.x0, panel.height - box.y1, box.x1, panel.height - box.y0))
    plt.close(figure)
    return panel, boxes


def render(directory, audit_directory, protocol_path, output):
    from PIL import Image, ImageDraw, ImageFont
    os.environ.setdefault('MUJOCO_GL', 'egl')
    import mujoco

    protocol, invocation, report, series, poses, times, indices, hashes = load_record(
        directory, audit_directory, protocol_path)
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None or mujoco.__version__ != invocation['runtime']['packages']['mujoco']:
        raise ValueError('Require the recorded native MuJoCo version and existing system ffmpeg')
    model = mujoco.MjModel.from_binary_path(str(directory / 'native/compiled-template.mjb'))
    if poses.shape[1] != model.nq or protocol['conditions']['control_dt_s'] != .02:
        raise ValueError('Saved poses/model/control rate differ')
    address = int(model.joint('robot/floating_base_joint').qposadr[0])
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'schema_version': 1, 'status': 'started', 'input_sha256': hashes,
                'renderer_sha256': digest(Path(__file__)), 'mujoco_version': mujoco.__version__,
                'scope': 'Saved poses and native diagnostic curves; no physics integration or replacement force.',
                'geometry': 'Saved compiled geometry template; GPU mass/COM/friction randomization is not simulated in playback.',
                'force_epoch': 'Last completed substep indexed by its before-step clock; initial pose has no force sample.',
                'fps': 50, 'expected_frames': len(poses), 'frames_completed': 0,
                'native_state_span_s': float(times[-1] - times[0]),
                'presentation_duration_s': len(poses) / 50,
                'duration_note': 'One frame per boundary, including one extra frame displaying the final pre-reset endpoint.',
                'task_success': None, 'frame_map': []}
    started = time.monotonic()
    try:
        panel, boxes = force_panel(series, report, times, output)
        model.vis.global_.offwidth, model.vis.global_.offheight = 896, 672
        model.vis.headlight.active = 1
        model.vis.headlight.ambient[:] = .45
        model.vis.headlight.diffuse[:] = .7
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [float(poses[:, address].mean()), float(poses[:, address + 1].mean()), .8]
        span = float(np.ptp(poses[:, address:address + 2], axis=0).max())
        camera.distance, camera.azimuth, camera.elevation = max(2.6, span * 1.5), 120, -15
        manifest['camera'] = {'lookat': camera.lookat.tolist(), 'distance': camera.distance,
                              'azimuth': camera.azimuth, 'elevation': camera.elevation, 'fixed': True}
        manifest['display_only_changes'] = {'headlight_ambient': .45, 'headlight_diffuse': .7}
        data = mujoco.MjData(model)
        font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=15)
        previews = set(np.linspace(0, len(poses) - 1, 5, dtype=int))
        command = [ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'error', '-n',
                   '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1280x720',
                   '-framerate', '50', '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-crf', '20',
                   '-threads', '1', '-filter_threads', '1', '-pix_fmt', 'yuv420p',
                   '-movflags', '+faststart', str(output / 'replay.mp4')]
        manifest['encoder_version'] = subprocess.check_output([ffmpeg, '-version'], text=True).splitlines()[0]
        with mujoco.Renderer(model, height=672, width=896) as renderer, (output / 'encoder.log').open('xb') as log:
            encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            try:
                for index, (pose, timestamp, force_index) in enumerate(zip(poses, times, indices)):
                    set_display_pose(mujoco, model, data, pose)
                    renderer.update_scene(data, camera=camera)
                    canvas = Image.new('RGB', (1280, 720), '#17242c')
                    canvas.paste(Image.fromarray(renderer.render()), (0, 48))
                    current = panel.copy()
                    cursor = ImageDraw.Draw(current)
                    fraction = float((timestamp - times[0]) / (times[-1] - times[0]))
                    for left, top, right, bottom in boxes:
                        x = left + fraction * (right - left)
                        cursor.line((x, top, x, bottom), fill='#be123c', width=2)
                    canvas.paste(current, (896, 48))
                    draw = ImageDraw.Draw(canvas)
                    draw.text((16, 8), f'G1 AMP | {invocation["case"]["id"]} | saved-pose replay', font=font, fill='white')
                    draw.text((16, 29), f'Native t={timestamp:.5f} s | {index + 1}/{len(poses)} | no physics rerun', font=small, fill='#cbd5e1')
                    encoder.stdin.write(canvas.tobytes())
                    if index in previews:
                        canvas.save(output / f'frame-{index:04d}.png')
                    manifest['frame_map'].append({'frame': index, 'native_time_s': float(timestamp),
                        'last_completed_force_substep': int(force_index) if force_index >= 0 else None})
                    manifest['frames_completed'] = index + 1
            finally:
                try:
                    encoder.stdin.close()
                except BrokenPipeError:
                    pass
                code = encoder.wait()
            if code:
                raise RuntimeError('Encoder failed; retain partial output and encoder.log')
        manifest.update(status='completed', video_sha256=digest(output / 'replay.mp4'),
                        curve_sha256={name: digest(output / name) for name in ('curves.png', 'curves.svg')})
    except BaseException as error:
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        manifest['render_encode_wall_s'] = time.monotonic() - started
        (output / 'replay.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.run, args.audit, args.protocol, args.output)
