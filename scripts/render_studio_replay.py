"""Render saved rigid-scene states with USD/OVRTX; never integrate physics.

Scene-specific readers live in prepare_studio_replays.py. MuJoCo's official
USD exporter retains meshes and textures. Every published frame evaluates one
explicit USD sample; no frame interpolation, temporal accumulation or motion blur.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sample_indices(times, fps):
    """Nearest existing samples over the entire episode, with both endpoints."""
    times = np.asarray(times, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all()
            or np.any(np.diff(times) <= 0) or not np.isfinite(fps) or fps <= 0):
        raise ValueError('Expected increasing finite timestamps and positive FPS')
    targets = np.arange(round((times[-1] - times[0]) * fps) + 1) / fps + times[0]
    right = np.searchsorted(times, targets).clip(0, len(times) - 1)
    left = np.maximum(right - 1, 0)
    indices = np.where(abs(times[left] - targets) <= abs(times[right] - targets), left, right)
    indices[0], indices[-1] = 0, len(times) - 1
    return indices


def camera_matrix(position, forward, up):
    """USD row-vector transform: +X right, +Y up, -Z forward."""
    forward, up = np.array(forward, dtype=float, copy=True), np.array(up, dtype=float, copy=True)
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    matrix = np.eye(4)
    matrix[:3, :3] = [right, np.cross(right, forward), -forward]
    matrix[3, :3] = position
    return matrix


def add_studio(stage, center, scale, width, height, samples):
    from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdRender

    dome = UsdLux.DomeLight.Define(stage, '/World/StudioAmbient')
    dome.CreateIntensityAttr(500.)
    dome.CreateColorAttr(Gf.Vec3f(.88, .93, 1.))
    for name, offset, size, strength, color in (
        ('Key', (1, -1.5, 2), 1.4, 4400., (1., .92, .81)),
        ('Fill', (-1.5, -.5, 1), 1.8, 2100., (.79, .87, 1.)),
        ('Rim', (0, 1.5, 1.7), 1., 2600., (1., 1., 1.)),
    ):
        light = UsdLux.RectLight.Define(stage, '/World/Studio' + name)
        position = np.asarray(center) + np.asarray(offset) * scale
        light.AddTransformOp().Set(Gf.Matrix4d(camera_matrix(position, np.asarray(center) - position, [0, 0, 1]).tolist()))
        light.CreateWidthAttr(size * scale)
        light.CreateHeightAttr(size * scale)
        light.CreateIntensityAttr(strength)
        light.CreateColorAttr(Gf.Vec3f(*color))
    camera = UsdGeom.Camera.Define(stage, '/World/StudioCamera')
    camera.CreateClippingRangeAttr(Gf.Vec2f(.0001, 1000.))
    camera.CreateVerticalApertureAttr(20.955)
    camera.CreateHorizontalApertureAttr(20.955 * width / height)
    camera.CreateFocalLengthAttr(20.955 / (2 * np.tan(np.deg2rad(45) / 2)))
    camera.CreateShutterOpenAttr(0.)
    camera.CreateShutterCloseAttr(0.)
    product = UsdRender.Product.Define(stage, '/Render/Camera')
    product.CreateResolutionAttr(Gf.Vec2i(width, height))
    product.CreateCameraRel().SetTargets([camera.GetPath()])
    variable = UsdRender.Var.Define(stage, '/Render/Camera/LdrColor')
    variable.CreateSourceNameAttr('LdrColor')
    product.CreateOrderedVarsRel().SetTargets([variable.GetPath()])
    for name, dtype, value in (
        ('rendermode', Sdf.ValueTypeNames.Token, 'PathTracing'),
        ('pt:samplesPerPixel', Sdf.ValueTypeNames.Int, samples),
        ('pt:denoising:enabled', Sdf.ValueTypeNames.Bool, True),
        ('post:motionblur:enabled', Sdf.ValueTypeNames.Bool, False),
    ):
        product.GetPrim().CreateAttribute('omni:rtx:' + name, dtype).Set(value)
    return camera


def export_scene(model, states, times, camera, camera_targets, output, *, fps=20, width=800, height=600, samples=32, pilot=False):
    """Author each exact recorded qpos/mocap sample; use kinematics only."""
    import mujoco
    from mujoco.usd.exporter import USDExporter
    from pxr import Gf, UsdGeom

    fields = {'qpos': (model.nq,), 'mocap_pos': (model.nmocap, 3), 'mocap_quat': (model.nmocap, 4)}
    if not states or set(states) - set(fields):
        raise ValueError('Unsupported or empty state channels')
    for name, values in states.items():
        if values.shape != (len(times), *fields[name]) or not np.isfinite(values).all():
            raise ValueError('Invalid recorded ' + name)
    if np.shape(camera_targets) != (len(times), 3) or not np.isfinite(camera_targets).all():
        raise ValueError('Invalid camera targets')
    indices = sample_indices(times, fps)
    if pilot:
        indices = indices[[0, len(indices) // 2, -1]]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model.vis.global_.offwidth, model.vis.global_.offheight = width, height
    exporter = USDExporter(model, width=width, height=height, output_directory='usd', output_directory_root=str(output), verbose=False)
    data = mujoco.MjData(model)
    scene = mujoco.MjvScene(model, maxgeom=max(10000, model.ngeom * 2))
    option = mujoco.MjvOption()
    map_frames, cameras = [], []
    stage = None
    for frame, index in enumerate(indices):
        for name, values in states.items():
            getattr(data, name)[:] = values[index]
        mujoco.mj_fwdPosition(model, data)
        for name, values in states.items():
            error = np.max(abs(getattr(data, name) - values[index]), initial=0.)
            if error > 1e-14:
                raise ValueError('Kinematics changed more than quaternion roundoff')
            getattr(data, name)[:] = values[index]
        exporter.update_scene(data)
        if stage is None:
            stage = exporter.stage
            UsdGeom.SetStageMetersPerUnit(stage, 1.)
            stage.SetTimeCodesPerSecond(fps)
            usd_camera = add_studio(stage, camera_targets[0], camera.distance, width, height, samples)
            transform = usd_camera.AddTransformOp()
        camera.lookat[:] = camera_targets[index]
        mujoco.mjv_updateScene(model, data, option, None, camera, mujoco.mjtCatBit.mjCAT_ALL, scene)
        eye = mujoco.mjv_averageCamera(scene.camera[0], scene.camera[1])
        matrix = camera_matrix(eye.pos, eye.forward, eye.up)
        transform.Set(Gf.Matrix4d(matrix.tolist()), frame)
        # Match the native perspective rather than relying on an exporter default.
        fovy = 2 * np.arctan((eye.frustum_top - eye.frustum_bottom) / (2 * eye.frustum_near))
        usd_camera.GetFocalLengthAttr().Set(20.955 / (2 * np.tan(fovy / 2)), frame)
        cameras.append(matrix.tolist())
        row = {'frame': frame, 'sample': int(index), 'time_s': float(times[index])}
        if model.nq == 7 and 'qpos' in states:
            row['world_position_m'] = states['qpos'][index, :3].tolist()
        map_frames.append(row)
    # Finish the native export before removing its animated light prims.
    from pxr import UsdLux
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdLux.SphereLight):
            stage.RemovePrim(prim.GetPath())
    stage.SetEndTimeCode(len(indices) - 1)
    usd_path = output / 'usd/frames/replay.usdc'
    stage.Export(str(usd_path))
    return usd_path, map_frames, cameras


def render_usd(usd_path, frames, cameras, output, *, fps=20, label='', passes=2):
    """Explicitly evaluate every authored sample and verify camera readback."""
    import imageio.v2 as imageio
    import ovrtx
    from pxr import Usd, UsdGeom
    from PIL import Image, ImageDraw, ImageFont

    output = Path(output)
    config = ovrtx.RendererConfig(log_level='error', log_file_path=str(output / 'renderer.log'), active_cuda_gpus='0')
    renderer = ovrtx.Renderer(config)
    source_stage = Usd.Stage.Open(str(usd_path))
    transform_paths = ['/World/StudioCamera'] + [str(p.GetPath()) for p in source_stage.Traverse() if p.GetName().startswith('Mesh_Xform_')]
    timings, transform_errors = [], []
    font = ImageFont.truetype('DejaVuSans.ttf', 16)
    try:
        renderer.open_usd(str(usd_path))
        with imageio.get_writer(output / 'replay.mp4', fps=fps, codec='libx264', quality=8,
                               macro_block_size=1, ffmpeg_params=['-threads', '1', '-movflags', '+faststart']) as writer:
            for row, expected in zip(frames, cameras, strict=True):
                start = time.perf_counter()
                renderer.update_from_usd_time(row['frame'] / fps)
                renderer.reset()
                for _ in range(passes):
                    products = renderer.step(render_products={'/Render/Camera'}, delta_time=1/fps)
                actual = np.from_dlpack(renderer.read_attribute('omni:xform', transform_paths)).copy().reshape(-1, 4, 4)
                expected_transforms = np.array([np.asarray(UsdGeom.Xformable(source_stage.GetPrimAtPath(p)).GetLocalTransformation(row['frame'])) for p in transform_paths])
                error = float(np.max(abs(actual - expected_transforms)))
                if error > 3e-6:
                    raise ValueError(f'Scene sample readback differs: {error}')
                transform_errors.append(error)
                product = products['/Render/Camera']
                var = product.frames[-1].render_vars['LdrColor'].map(device=ovrtx.Device.CPU)
                view = np.from_dlpack(var)
                rgb = view[:, :, :3].copy()
                del view
                var.unmap()
                del var, products, product
                timings.append(time.perf_counter() - start)
                canvas = Image.new('RGB', (rgb.shape[1], rgb.shape[0] + 60), '#17242c')
                canvas.paste(Image.fromarray(rgb))
                ImageDraw.Draw(canvas).text((15, rgb.shape[0] + 10), f'{label} | recorded t={row["time_s"]:.3f} s | RTX replay', fill='white', font=font)
                if 'world_position_m' in row:
                    x, y, z = row['world_position_m']
                    ImageDraw.Draw(canvas).text((15, rgb.shape[0] + 33), f'World position: x={x:+.5f} m  y={y:+.5f} m  z={z:+.5f} m', fill='white', font=font)
                writer.append_data(np.asarray(canvas))
                if row['frame'] in (0, len(frames) // 2, len(frames) - 1):
                    canvas.save(output / f'frame-{row["frame"]:04d}.png')
                if row['frame'] % 20 == 0:
                    print(f'{label}: {row["frame"] + 1}/{len(frames)} frames', flush=True)
    finally:
        renderer.destroy()
    return {'renderer': 'OVRTX ' + importlib.metadata.version('ovrtx'),
            'mujoco_display_version': importlib.metadata.version('mujoco'),
            'mode': 'PathTracing', 'passes_per_frame': passes,
            'transform_readback_max_error': max(transform_errors), 'transforms_checked_per_frame': len(transform_paths),
            'render_readback_s': timings, 'physics_steps': 0}


def render(model, states, times, camera, targets, output, *, sources, label, fps=20, pilot=False):
    """One validated replay, its source hashes, frame mapping and timing receipt."""
    output = Path(output)
    before = {str(p): digest(p) for p in sources}
    started = time.perf_counter()
    usd, frames, cameras = export_scene(model, states, times, camera, targets, output, fps=fps, pilot=pilot)
    receipt = render_usd(usd, frames, cameras, output, fps=fps, label=label)
    if before != {str(p): digest(p) for p in sources}:
        raise ValueError('Input changed during replay')
    receipt.update({'schema': 1, 'label': label, 'sources': [{'name': Path(p).name, 'sha256': h} for p, h in before.items()],
                    'frame_map': frames, 'camera_transforms': cameras, 'fps': fps,
                    'samples_per_pixel': 32, 'pilot': pilot,
                    'wall_s': time.perf_counter() - started,
                    'usd_sha256': digest(usd), 'video_sha256': digest(output / 'replay.mp4'),
                    'renderer_source_sha256': digest(__file__),
                    'presentation': 'Original mesh/texture display geometry; authored three-area-light studio. No physics integration or interpolation. MuJoCo performs only kinematics and USD export.'})
    (output / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
