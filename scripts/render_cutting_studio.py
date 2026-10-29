"""Path-trace saved cutting surfaces; no integration or changes to native records."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import time

import imageio.v2 as imageio
import numpy as np
from PIL import Image
import vtk
from vtk.util.numpy_support import vtk_to_numpy

from dexlab.cutting_metrics import ReplayMeasurements
from dexlab.cutting_score import grid_components, score_run
from dexlab.cutting_showcase import CuttingScene, cut_push_caption, write_gif
from dexlab.cutting_surface import LinkedVolumeSurface
from render_studio_replay import add_studio, camera_matrix, digest


def banana_texture():
    """Authored flesh detail in material space, with a separate transverse atlas."""
    y, x = np.mgrid[:1024, :1024] / 1023
    theta = y[:512]*4*np.pi
    u = x[:512]*2-1
    fibres = (.5+.5*np.cos(5*theta+.3))**12
    fine = np.sin(93*theta+.4*np.sin(x[:512]*31))
    noise = np.random.default_rng(237).normal(0, .004, theta.shape)
    shade = .045*fibres + .008*fine + noise
    skin = np.array([.97, .90, .66])[None, None] - shade[:, :, None]
    end = np.clip((abs(u)-.91)/.09, 0, 1)**2
    skin = skin*(1-.65*end[:, :, None]) + np.array([.38,.22,.08])*.65*end[:, :, None]
    cy, cx = np.mgrid[:512, :1024]
    a, b = (cx/1023-.5)*2, (cy/511-.5)*2
    radius, angle = np.hypot(a,b), np.arctan2(b,a)
    core = .10*np.exp(-(radius/.20)**2)
    star = .08*np.exp(-(radius/.45)**2)*(.5+.5*np.cos(3*angle))**14
    cap = np.array([.985,.945,.79])[None,None] - (core+star+noise)[:, :, None]
    return np.clip(np.concatenate((skin,cap))*255,0,255).astype(np.uint8)


def banana_uv(rest, faces, planes):
    """Face-varying coordinates keep the cut disc separate from the outer fibres."""
    triangle = rest[faces.reshape(-1,3)]
    x = triangle[:, :, 0]
    u = x/.06
    y = triangle[:, :, 1]-.035*(u*u-.5)
    z = triangle[:, :, 2]-.012
    angle = np.arctan2(z,y)/(2*np.pi)+.5
    # Clamp the narrow seam to one atlas edge, never interpolate through the cap.
    wrapped = np.ptp(angle,axis=1) > .5
    angle[wrapped] = np.where(angle[wrapped] < .5, 1., angle[wrapped])
    uv = np.stack(((u+1)/2, .005+angle*.48),axis=-1)
    cap = (np.ptp(x,axis=1)<1e-9) & np.any(
        np.isclose(x[:,0,None], planes, atol=1e-8),axis=1)
    radius = .003+.009*np.maximum(0,1-u*u)**.55
    uv[cap,:,0] = .5+.49*y[cap]/radius[cap]
    uv[cap,:,1] = .75+.24*z[cap]/radius[cap]
    return uv.reshape(-1,2).astype(np.float32)


def material(stage, name, actor, output):
    """Use the existing material-attached colours/UVs with explicit PBR values."""
    from pxr import Gf, Sdf, UsdShade

    path = '/Materials/' + name
    result = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, path + '/Surface')
    shader.CreateIdAttr('UsdPreviewSurface')
    shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(
        .18 if name in ('blade', 'bolster') else .32 if name == 'body' else .48)
    shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(
        1. if name in ('blade', 'bolster') else 0.)
    shader.CreateInput('ior', Sdf.ValueTypeNames.Float).Set(1.4)
    color = np.asarray(actor.GetProperty().GetColor()) ** 2.2
    shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    actor.GetMapper().Update()
    data = actor.GetMapper().GetInput()
    if data.GetPointData().GetScalars() is not None:
        reader = UsdShade.Shader.Define(stage, path + '/Color')
        reader.CreateIdAttr('UsdPrimvarReader_float3')
        reader.CreateInput('varname', Sdf.ValueTypeNames.Token).Set('displayColor')
        reader.CreateOutput('result', Sdf.ValueTypeNames.Float3)
        shader.GetInput('diffuseColor').ConnectToSource(reader.ConnectableAPI(), 'result')
    textured_banana = name == 'body' and (output/'body.png').exists()
    if actor.GetTexture() is not None or textured_banana:
        if not textured_banana:
            texture = actor.GetTexture().GetInput()
            width, height, _ = texture.GetDimensions()
            rgb = vtk_to_numpy(texture.GetPointData().GetScalars()).reshape(height, width, 3)
            Image.fromarray(np.flipud(rgb)).save(output/(name + '.png'))
        uv = UsdShade.Shader.Define(stage, path + '/UV')
        uv.CreateIdAttr('UsdPrimvarReader_float2')
        uv.CreateInput('varname', Sdf.ValueTypeNames.Token).Set('st')
        uv.CreateOutput('result', Sdf.ValueTypeNames.Float2)
        sampler = UsdShade.Shader.Define(stage, path + '/Texture')
        sampler.CreateIdAttr('UsdUVTexture')
        sampler.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(name + '.png'))
        sampler.CreateInput('sourceColorSpace', Sdf.ValueTypeNames.Token).Set('sRGB')
        sampler.CreateInput('wrapS', Sdf.ValueTypeNames.Token).Set('repeat')
        sampler.CreateInput('wrapT', Sdf.ValueTypeNames.Token).Set('repeat')
        sampler.CreateInput('st', Sdf.ValueTypeNames.Float2).ConnectToSource(uv.ConnectableAPI(), 'result')
        sampler.CreateOutput('rgb', Sdf.ValueTypeNames.Float3)
        shader.GetInput('diffuseColor').ConnectToSource(sampler.ConnectableAPI(), 'rgb')
    result.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
    return result


def export_actor(stage, name, actor, frame, output, banana_planes=None):
    """Convert the original scene mesh, in metres, without rescaling its shape."""
    from pxr import Gf, Sdf, UsdGeom, UsdShade, Vt

    actor.GetMapper().Update()
    triangles = vtk.vtkTriangleFilter()
    triangles.SetInputData(actor.GetMapper().GetInput())
    triangles.Update()
    data = triangles.GetOutput()
    points = vtk_to_numpy(data.GetPoints().GetData()) / 1000
    faces = vtk_to_numpy(data.GetPolys().GetConnectivityArray()).astype(np.int32)
    mesh = UsdGeom.Mesh.Define(stage, '/World/' + name)
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateDoubleSidedAttr(True)
    mesh.CreatePointsAttr().Set(Vt.Vec3fArray.FromNumpy(points.astype(np.float32)), frame)
    mesh.CreateFaceVertexCountsAttr().Set(Vt.IntArray.FromNumpy(np.full(len(faces)//3, 3, np.int32)), frame)
    mesh.CreateFaceVertexIndicesAttr().Set(Vt.IntArray.FromNumpy(faces), frame)
    normals = data.GetPointData().GetNormals()
    if normals is not None:
        mesh.CreateNormalsAttr().Set(Vt.Vec3fArray.FromNumpy(vtk_to_numpy(normals).astype(np.float32)), frame)
        mesh.SetNormalsInterpolation('vertex')
    colors = data.GetPointData().GetScalars()
    if colors is not None:
        colors = (vtk_to_numpy(colors)[:, :3] / 255) ** 2.2
        mesh.CreateDisplayColorPrimvar('vertex').Set(Vt.Vec3fArray.FromNumpy(colors.astype(np.float32)), frame)
    coordinates = data.GetPointData().GetTCoords()
    if name == 'body' and banana_planes is not None:
        rest = vtk_to_numpy(data.GetPointData().GetArray('MaterialRest'))
        coordinates = banana_uv(rest, faces, banana_planes)
        UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray, 'faceVarying').Set(
            Vt.Vec2fArray.FromNumpy(coordinates), frame)
    elif coordinates is not None:
        UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray, 'vertex').Set(
            Vt.Vec2fArray.FromNumpy(vtk_to_numpy(coordinates).astype(np.float32)), frame)
    matrix = np.array([[actor.GetMatrix().GetElement(i, j) for j in range(4)] for i in range(4)])
    matrix[:3, 3] /= 1000
    transform = UsdGeom.Xformable(mesh)
    operations = transform.GetOrderedXformOps()
    operation = operations[0] if operations else transform.AddTransformOp()
    operation.Set(Gf.Matrix4d(matrix.T.tolist()), frame)
    if frame == 0:
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material(stage, name, actor, output))
    return points


def export(directory, output, *, preview=False, preview_frames=None, fps=20):
    from pxr import Gf, Usd, UsdGeom

    manifest = json.loads((directory/'manifest.json').read_text())
    for name, expected in manifest['artifacts'].items():
        if digest(directory/name) != expected:
            raise ValueError('Saved record hash mismatch: ' + name)
    with np.load(directory/'states.npz', allow_pickle=False) as archive:
        states = dict(archive)
    with np.load(directory/'trace.npz', allow_pickle=False) as archive:
        trace = dict(archive)
    if manifest.get('motion_protocol') != 'cut-push':
        raise ValueError('This presentation requires a complete cut-push record')
    config = manifest['config']
    measurements = ReplayMeasurements(states, trace, manifest)
    banana = config.get('shape') == 'banana'
    if banana:
        Image.fromarray(np.flipud(banana_texture())).save(output/'body.png')
    surface = LinkedVolumeSurface(states['reference'], measurements.planes, measurements.axes,
                                  config['size'], config['grid_spacing'],
                                  config['grid_spacing']/4, config.get('shape', 'block'))
    scene = CuttingScene(config, task='banana' if config.get('shape') == 'banana' else 'tofu')
    stage = Usd.Stage.CreateNew(str(output/'replay.usdc'))
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.SetInterpolationType(Usd.InterpolationTypeHeld)
    stage.SetTimeCodesPerSecond(fps)
    camera = add_studio(stage, [0, 0, .02], .18, 960, 600, 64)
    stage.GetPrimAtPath('/World/StudioAmbient').GetAttribute('inputs:intensity').Set(180.)
    stage.GetPrimAtPath('/World/StudioFill').GetAttribute('inputs:intensity').Set(1000.)
    position, target = np.array([.11, -.22, .175]), np.array([0, 0, .024])
    camera.AddTransformOp().Set(Gf.Matrix4d(camera_matrix(position, target-position, [0, 0, 1]).tolist()))
    camera.CreateProjectionAttr('orthographic')
    camera.GetVerticalApertureAttr().Set(1.3)
    camera.GetHorizontalApertureAttr().Set(1.3*960/600)
    actors = list(scene.renderer.GetActors())
    names = ('board', 'floor', 'blade', 'handle', 'bolster', 'body')
    actors = dict(zip(names, actors[:6], strict=True))
    selected = list(range(0, len(states['time']), 5))
    if selected[-1] != len(states['time'])-1:
        selected.append(len(states['time'])-1)
    if not np.allclose(np.diff(states['time'][selected]), 1/fps, atol=1e-9):
        raise ValueError('Expected the complete existing 20 FPS source sample schedule')
    if preview:
        selected = preview_frames or [0, 80, len(states['time'])//2, len(states['time'])-1]
        if not all(0 <= index < len(states['time']) for index in selected):
            raise ValueError('Preview frame is outside the saved record')
    frames = []
    geometry_error = 0.
    try:
        for frame, index in enumerate(selected):
            started = time.monotonic()
            measured = measurements.frame(index)
            components, _ = grid_components(states['nodes'], states['weights'], states['sides'][index])
            vertices, faces, rest, caps = surface.mesh(
                states['position'][index], states['deformation'][index], states['sides'][index], components)
            ti = max(0, int(np.searchsorted(trace['time_s'], states['time'][index]+1e-12, side='right'))-1)
            scene.update(vertices, faces, rest, caps, states['position'][index], states['sides'][index],
                         trace['blade_position_m'][ti], trace.get('blade_yaw_rad', np.zeros(1))[ti]
                         if 'blade_yaw_rad' in trace else 0.)
            for name, actor in actors.items():
                points = export_actor(stage, name, actor, frame, output,
                                      measurements.planes if banana else None)
                encoded = np.asarray(UsdGeom.Mesh(stage.GetPrimAtPath('/World/'+name)).GetPointsAttr().Get(frame))
                geometry_error = max(geometry_error, float(np.max(abs(points-encoded))))
            frames.append({'frame':frame, 'sample':int(index), 'time_s':float(states['time'][index]),
                           'metrics':measured, 'mesh_wall_s':time.monotonic()-started})
            if preview:
                np.savez(output/f'mesh-{index:04d}.npz',vertices=vertices,faces=faces,rest=rest,caps=caps)
            print(f'Export {manifest["task"]}: {frame+1}/{len(selected)}', flush=True)
    finally:
        scene.window.Finalize()
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(len(frames)-1)
    stage.GetRootLayer().Save()
    return manifest, frames, geometry_error


def render(directory, output, *, preview=False, preview_frames=None):
    import ovrtx
    from pxr import Usd, UsdGeom

    directory, output = Path(directory), Path(output)
    if preview_frames and not preview:
        raise ValueError('Selected frames are only allowed for an explicitly labelled preview')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    manifest, frames, export_error = export(directory, output, preview=preview,preview_frames=preview_frames)
    score = score_run(directory)
    stage = Usd.Stage.Open(str(output/'replay.usdc'))
    paths = [str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    renderer = ovrtx.Renderer(ovrtx.RendererConfig(
        log_level='error', log_file_path=str(output/'renderer.log'), active_cuda_gpus='0'))
    gif_frames, errors, transform_errors = [], [], []
    try:
        renderer.open_usd(str(output/'replay.usdc'))
        with imageio.get_writer(output/'surface.mp4', fps=20, codec='libx264', quality=8,
                               macro_block_size=1, ffmpeg_params=['-threads', '1', '-movflags', '+faststart']) as writer:
            for row in frames:
                frame = row['frame']
                renderer.update_from_usd_time(frame/20)
                renderer.reset()
                for _ in range(4):
                    products = renderer.step(render_products={'/Render/Camera'}, delta_time=1/20)
                readback = renderer.read_array_attribute('points', paths)
                error = max(float(np.max(abs(np.from_dlpack(readback[p])-np.asarray(
                    UsdGeom.Mesh(stage.GetPrimAtPath(p)).GetPointsAttr().Get(frame))))) for p in paths)
                if error > 1e-7:
                    raise ValueError(f'Renderer mesh readback differs: {error}')
                errors.append(error)
                transform_paths = paths + ['/World/StudioCamera']
                actual_transforms = np.from_dlpack(
                    renderer.read_attribute('omni:xform', transform_paths)).reshape(-1,4,4)
                expected_transforms = np.array([
                    np.asarray(UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetLocalTransformation(frame))
                    for p in transform_paths])
                transform_error = float(np.max(abs(actual_transforms-expected_transforms)))
                if transform_error > 3e-6:
                    raise ValueError(f'Renderer pose readback differs: {transform_error}')
                transform_errors.append(transform_error)
                del actual_transforms
                product = products['/Render/Camera']
                mapped = product.frames[-1].render_vars['LdrColor'].map(device=ovrtx.Device.CPU)
                view = np.from_dlpack(mapped)
                rgb = view[:, :, :3].copy()
                del view
                mapped.unmap()
                del mapped, products, product, readback
                rgb = cut_push_caption(rgb, row['time_s'], manifest['duration_s'],
                                       'RTX surface replay', row['metrics'], manifest['task'])
                writer.append_data(rgb)
                picture = Image.fromarray(rgb)
                if preview or frame in (0, len(frames)//2, len(frames)-1):
                    picture.save(output/f'frame-{frame:04d}.png')
                if frame == len(frames)-1:
                    picture.save(output/'surface-poster.png')
                gif_frames.append(picture.resize((720, round(720*picture.height/picture.width)), Image.Resampling.LANCZOS))
                if frame % 20 == 0:
                    print(f'Render {manifest["task"]}: {frame+1}/{len(frames)}', flush=True)
    finally:
        renderer.destroy()
    if not preview:
        write_gif(gif_frames, output/'surface.gif')
    for name, expected in manifest['artifacts'].items():
        if digest(directory/name) != expected:
            raise ValueError('Source changed during replay')
    receipt = {'source_artifacts':manifest['artifacts'], 'score':score, 'preview':preview,
               'frames':frames, 'fps':20, 'physical_duration_s':manifest['duration_s'],
               'physics_steps':0, 'renderer':'OVRTX '+importlib.metadata.version('ovrtx'),
               'samples_per_pixel':64, 'passes_per_frame':4, 'mode':'PathTracing',
               'reconstruction':{
                   'surface_spacing_m':manifest['config']['grid_spacing']/4,
                   'qef_relative_singular_cutoff':.1,
                   'triangulation':'whole-quad winding; diagonal maximizing minimum projected area',
                   'motion':'saved x/F and persistent cut/component histories',
                   'vertex_smoothing':False,
                   'materials':'authored colour/roughness/texture; not measured food properties'},
               'usd_float32_export_max_error_m':export_error, 'renderer_points_max_error_m':max(errors),
               'renderer_transform_max_error':max(transform_errors),
               'packages':{name:importlib.metadata.version(name) for name in
                           ('numpy','scipy','vtk','usd-core','ovrtx','Pillow','imageio')},
               'wall_s':time.monotonic()-started,
               'renderer_sha256':{p.name:digest(p) for p in (
                   Path(__file__), Path(__file__).with_name('render_studio_replay.py'),
                   Path(__file__).parents[1]/'src/dexlab/cutting_surface.py',
                   Path(__file__).parents[1]/'src/dexlab/cutting_showcase.py',
                   Path(__file__).parents[1]/'src/dexlab/cutting_metrics.py')},
               'assets':{p.name:digest(p) for p in output.iterdir() if p.suffix in ('.mp4','.png','.gif')}}
    (output/'provenance.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--preview-frames',type=int,nargs='+')
    args = parser.parse_args()
    render(args.directory, args.output, preview=args.preview,preview_frames=args.preview_frames)
