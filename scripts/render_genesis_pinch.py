"""Render recorded Genesis poses; MuJoCo is a display renderer, never a solver here."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import numpy as np


def frame_indices(samples, fps=30):
    """Keep the entire episode, choosing the nearest recorded step without smoothing."""
    times = np.asarray([row['time'] for row in samples], dtype=float)
    if len(times) < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError('Expected finite, strictly increasing physics timestamps')
    if fps <= 0 or times[0] <= 0:
        raise ValueError('Expected positive FPS and post-step timestamps')
    dt = times[0]
    if not np.allclose(np.diff(times), dt, rtol=1e-6, atol=1e-10):
        raise ValueError('Missing physics steps: refusing a discontinuous replay')
    targets = np.linspace(times[0], times[-1], round(times[-1] * fps) + 1)
    right = np.searchsorted(times, targets).clip(0, len(times) - 1)
    left = np.maximum(right - 1, 0)
    return np.where(abs(times[left] - targets) <= abs(times[right] - targets), left, right)


def render(record_path, model_path, output):
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    os.environ.setdefault('MUJOCO_GL', 'egl')
    import mujoco

    if output.exists():
        raise FileExistsError(output)
    record = json.loads(record_path.read_text())
    rows = record['samples']
    indices = frame_indices(rows)
    root = ET.fromstring(model_path.read_text())
    world = root.find('worldbody')
    ET.SubElement(root, 'visual')
    ET.SubElement(root.find('visual'), 'global', offwidth='800', offheight='600')
    ET.SubElement(world, 'light', pos='0 -0.3 0.5', dir='0 0 -1', diffuse='0.9 0.9 0.9')
    ET.SubElement(world, 'geom', type='plane', size='0.3 0.3 0.01', rgba='0.22 0.25 0.28 1')
    cube = ET.SubElement(world, 'body', name='recorded_cube')
    ET.SubElement(cube, 'freejoint', name='recorded_pose')
    ET.SubElement(cube, 'geom', type='box', size='0.02 0.02 0.02', rgba='0.95 0.55 0.15 1')
    for geom in world.findall('.//body[@name="left"]/geom') + world.findall('.//body[@name="right"]/geom'):
        geom.set('rgba', '0.25 0.65 0.85 1')
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0, 0, .065]
    camera.distance, camera.azimuth, camera.elevation = .32, 90, -15
    addresses = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)]
                 for name in ('lift', 'left_slide', 'right_slide')]
    cube_address = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'recorded_pose')]
    output.mkdir(parents=True)
    start = time.perf_counter()
    frame_map = []
    with mujoco.Renderer(model, height=600, width=800) as renderer, imageio.get_writer(
            output / 'replay.mp4', fps=30, codec='libx264', quality=8, macro_block_size=1,
            ffmpeg_params=['-threads', '1', '-filter_threads', '1']) as writer:
        for frame, index in enumerate(indices):
            row = rows[int(index)]
            q, pos, quat = (np.asarray(row[key], dtype=float) for key in ('q', 'object_pos', 'object_quat'))
            if q.shape != (3,) or pos.shape != (3,) or quat.shape != (4,) or not np.isfinite(np.r_[q, pos, quat]).all():
                raise ValueError('Invalid recorded pose')
            if not np.isclose(np.linalg.norm(quat), 1, atol=1e-6):
                raise ValueError('Invalid recorded quaternion')
            data.qpos[addresses] = q
            data.qpos[cube_address:cube_address + 7] = np.r_[pos, quat]
            mujoco.mj_forward(model, data)  # Kinematics only: never mj_step.
            renderer.update_scene(data, camera=camera)
            image = renderer.render()
            canvas = Image.fromarray(image)
            draw = ImageDraw.Draw(canvas)
            draw.text((20, 16), f"Genesis | {record.get('case_id') or record['condition']} | t={row['time']:.3f} s", fill='white', font_size=20)
            draw.text((20, 46), "Measured-pose replay; MuJoCo display only", fill='white', font_size=18)
            image = np.asarray(canvas)
            writer.append_data(image)
            if frame in (0, 60, len(indices) - 1):
                imageio.imwrite(output / f'frame-{frame:03d}.png', image)
            frame_map.append({'frame': frame, 'sample': int(index), 'time_s': row['time']})
    elapsed = time.perf_counter() - start
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        'schema': 1, 'physics': 'Recorded Genesis; no physics integration during replay',
        'renderer': f'MuJoCo {mujoco.__version__}', 'condition': record['condition'],
        'record_sha256': digest(record_path), 'model_sha256': digest(model_path),
        'renderer_source_sha256': digest(Path(__file__)), 'video_sha256': digest(output / 'replay.mp4'),
        'fps': 30, 'frames': frame_map, 'render_encode_wall_s': elapsed,
        'camera': {'lookat': [0, 0, .065], 'distance': .32, 'azimuth': 90, 'elevation': -15},
        'sampling': 'Nearest recorded state, full episode, no interpolation; video is not full-rate collision validation',
    }
    (output / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('model', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.record, args.model, args.output)
