"""Render recorded cutting as a lit material surface or an auditable particle view."""

import argparse
import hashlib
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from dexlab.cutting_score import grid_components, score_run
from dexlab.cutting_surface import BananaSkin, MaterialSurface


def polydata(vertices, faces):
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(vertices), deep=True))
    cells = vtk.vtkCellArray()
    packed = np.column_stack((np.full(len(faces), faces.shape[1]), faces)).astype(np.int64)
    cells.SetCells(len(faces), numpy_to_vtkIdTypeArray(packed.ravel(), deep=True))
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(points)
    mesh.SetPolys(cells)
    return mesh


def actor_from_source(source, color, renderer):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    renderer.AddActor(actor)
    return actor


def cube(renderer, lengths, center, color):
    source = vtk.vtkCubeSource()
    source.SetXLength(lengths[0])
    source.SetYLength(lengths[1])
    source.SetZLength(lengths[2])
    actor = actor_from_source(source, color, renderer)
    actor.SetPosition(*center)
    return actor


def wood_texture():
    y, x = np.mgrid[:512, :1024]
    rng = np.random.default_rng(197)
    grain = (.025 * np.sin(.22 * y + .8 * np.sin(x / 170))
             + .018 * np.sin(1.65 * y + 2 * np.sin(x / 400))
             + .009 * rng.normal(size=x.shape))
    planks = .012 * (y // 85 % 3) - .01 * (y % 85 < 2)
    colors = np.clip(np.array([.82, .65, .44])[None, None] + (grain + planks)[:, :, None], 0, 1)
    data = vtk.vtkImageData()
    data.SetDimensions(1024, 512, 1)
    data.GetPointData().SetScalars(numpy_to_vtk((colors * 255).astype(np.uint8).reshape(-1, 3), deep=True))
    texture = vtk.vtkTexture()
    texture.SetInputData(data)
    texture.InterpolateOn()
    return texture


def knife_actor(renderer, half, bevel):
    if bevel == 0:
        return cube(renderer, 2 * half, (0, 0, 60), (.66, .72, .76))
    hx, hy, hz = half
    section = [(0, -hz), (hx, -hz + bevel), (hx, hz),
               (-hx, hz), (-hx, -hz + bevel)]
    vertices = np.array([(x, y, z) for y in (-hy, hy) for x, z in section])
    faces = []
    for i in range(1, 4):
        faces.extend([(0, i, i + 1), (5, i + 6, i + 5)])
    for i in range(5):
        j = (i + 1) % 5
        faces.extend([(i, j + 5, j), (i, i + 5, j + 5)])
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata(vertices, np.asarray(faces)))
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(.66, .72, .76)
    renderer.AddActor(actor)
    return actor


class CuttingScene:
    def __init__(self, config, width=960, height=640, *, task='tofu'):
        self.config = config
        self.task = task
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(.88, .91, .91)
        self.renderer.SetBackground2(.97, .98, .975)
        self.renderer.GradientBackgroundOn()
        self.window = vtk.vtkEGLRenderWindow()
        self.window.SetOffScreenRendering(1)
        self.window.SetSize(width, height)
        self.window.SetMultiSamples(0)
        self.window.AddRenderer(self.renderer)
        steps = vtk.vtkRenderStepsPass()
        ao = vtk.vtkSSAOPass()
        ao.SetDelegatePass(steps)
        ao.SetRadius(2.5)
        ao.SetBias(.15)
        ao.SetKernelSize(64)
        ao.BlurOn()
        self.renderer.SetPass(ao)
        self.renderer.RemoveAllLights()
        for position, intensity in [((-100, -80, 220), .65), ((140, 70, 140), .45), ((-100, 100, 90), .3)]:
            light = vtk.vtkLight()
            light.SetLightTypeToSceneLight()
            light.SetPosition(*position)
            light.SetFocalPoint(0, 0, 0)
            light.SetIntensity(intensity)
            self.renderer.AddLight(light)
        banana = config.get('shape') == 'banana'
        width_mm, depth_mm = (178, 110) if banana else (135, 105)
        board = cube(self.renderer, (width_mm, depth_mm, 7), (0, 0, -3.7), (.8, .65, .44))
        texture_coordinates = vtk.vtkTextureMapToPlane()
        texture_coordinates.SetInputConnection(board.GetMapper().GetInputConnection(0, 0))
        texture_coordinates.SetOrigin(-width_mm/2, -depth_mm/2, 0)
        texture_coordinates.SetPoint1(width_mm/2, -depth_mm/2, 0)
        texture_coordinates.SetPoint2(-width_mm/2, depth_mm/2, 0)
        board.GetMapper().SetInputConnection(texture_coordinates.GetOutputPort())
        board.SetTexture(wood_texture())
        if task == 'tofu-sequential':
            board.SetTexture(None)
            board.GetProperty().SetColor(.91, .93, .92)
        board.GetProperty().SetAmbient(.35)
        board.GetProperty().SetDiffuse(.6)
        board.GetProperty().SetSpecular(.08)
        board.GetProperty().SetSpecularPower(20)
        cube(self.renderer, (500, 400, 5), (0, 0, -10), (.85, .89, .885))
        self.half = np.asarray(config['blade_half_size']) * 1000
        self.blade = knife_actor(self.renderer, self.half, config.get('blade_bevel_height', 0) * 1000)
        self.blade.GetProperty().SetSpecular(.95)
        self.blade.GetProperty().SetSpecularPower(90)
        self.blade.GetProperty().SetAmbient(.55)
        self.handle = cube(self.renderer, (6, 12, 27), (0, 0, 100), (.105, .125, .13))
        self.handle.GetProperty().SetSpecular(.4)
        self.bolster = cube(self.renderer, (7, 15, 3), (0, 0, 80), (.67, .73, .76))
        self.body = vtk.vtkActor()
        self.body.GetProperty().SetSpecular(.22 if banana else .06)
        self.body.GetProperty().SetSpecularPower(48)
        self.body.GetProperty().SetAmbient(.3)
        self.body.GetProperty().SetDiffuse(.7)
        self.renderer.AddActor(self.body)
        self.particles = vtk.vtkActor()
        self.renderer.AddActor(self.particles)
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(135, -210, 160)
        camera.SetFocalPoint(0, 0, 30)
        camera.SetViewUp(0, 0, 1)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(72 if banana else 62)
        if task == 'tofu-sequential':
            camera.SetPosition(0, -220, 125)
            camera.SetFocalPoint(0, 0, 28)
        self.capture = vtk.vtkWindowToImageFilter()
        self.capture.SetInput(self.window)
        self.capture.SetInputBufferTypeToRGB()
        self.capture.ReadFrontBufferOff()

    def update(self, vertices, faces, rest, cut_vertices, positions, codes, blade):
        mesh = polydata(vertices*1000, faces)
        triangle = vtk.vtkTriangleFilter()
        triangle.SetInputData(mesh)
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetInputConnection(triangle.GetOutputPort())
        smooth.SetNumberOfIterations(40 if self.config.get('shape') == 'banana' else 0)
        smooth.SetPassBand(.015)
        smooth.NormalizeCoordinatesOn()
        smooth.BoundarySmoothingOff()
        smooth.Update()
        surface = smooth.GetOutput()
        smoothed = vtk_to_numpy(surface.GetPoints().GetData())
        # These examples have x-normal cuts. Preserve the measured cap x
        # coordinates so filtering never creates a larger visual cut opening.
        smoothed[cut_vertices, 0] = vertices[cut_vertices, 0]*1000
        surface.GetPoints().Modified()
        deviation = float(np.linalg.norm(smoothed - vertices*1000, axis=1).max())
        banana = self.config.get('shape') == 'banana'
        base = np.array([.98, .956, .835]) if banana else np.array([.94, .925, .84])
        # Material-attached colour variation; it cannot change geometry or cuts.
        noise = np.sin(rest[:, 0]*4260 + np.sin(rest[:, 1]*3870))*np.sin(rest[:, 2]*5160)
        colors = np.clip(base + .012*noise[:, None], 0, 1)
        if banana:
            u = rest[:, 0] / .06
            radial = rest[:, 1:] - np.column_stack((.035*(u*u-.5), np.full(len(u), .012)))
            theta = np.arctan2(radial[:, 1], radial[:, 0])
            # Long pale fibres and fine brown end tissue follow material
            # coordinates, so they travel with the fruit rather than the camera.
            fibres = (.5 + .5*np.cos(5*theta+.3))**12
            striae = np.sin(theta*89 + .22*np.sin(rest[:, 0]*240))
            colors -= (.035*fibres + .004*striae)[:, None] * np.array([.7, .8, 1.])
            end = np.clip((np.abs(u)-.90)/.10, 0, 1)**2
            colors = colors*(1-.55*end[:, None]) + np.array([.40,.27,.13])*.55*end[:, None]
            # Fresh transverse flesh has a faint three-fold core; this is
            # colour only and cannot create a crack or move a piece.
            core = np.exp(-np.linalg.norm(radial, axis=1)**2/.003**2)
            colors[cut_vertices] -= (core[cut_vertices]*.075)[:, None]
            colors = np.clip(colors, 0, 1)
        scalars = numpy_to_vtk((colors*255).astype(np.uint8), deep=True)
        scalars.SetName('MaterialColor')
        surface.GetPointData().SetScalars(scalars)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(surface)
        normals.SetFeatureAngle(65)
        if banana:
            normals.SplittingOff()
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        self.body.SetMapper(mapper)
        points = vtk.vtkPoints()
        points.SetData(numpy_to_vtk(positions*1000, deep=True))
        particles = vtk.vtkPolyData()
        particles.SetPoints(points)
        palette = np.array([[.90,.76,.47],[.24,.58,.70],[.95,.58,.31],[.51,.70,.47],[.68,.52,.76]])
        if self.task == 'tofu-sequential':
            palette[:] = (.93, .90, .81)
        particles.GetPointData().SetScalars(numpy_to_vtk((255*palette[codes % len(palette)]).astype(np.uint8), deep=True))
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(self.config['grid_spacing']*250)
        sphere.SetThetaResolution(10)
        sphere.SetPhiResolution(8)
        glyph = vtk.vtkGlyph3DMapper()
        glyph.SetInputData(particles)
        glyph.SetSourceConnection(sphere.GetOutputPort())
        glyph.ScalingOff()
        self.particles.SetMapper(glyph)
        self.blade.SetPosition(*(blade*1000))
        self.bolster.SetPosition(*(blade*1000 + [0, 0, self.half[2]+1.5]))
        self.handle.SetPosition(*(blade*1000 + [0, 0, self.half[2]+16.5]))
        self.renderer.ResetCameraClippingRange()
        return deviation

    def frame(self, particles=False):
        self.body.SetVisibility(not particles)
        self.particles.SetVisibility(particles)
        self.window.Render()
        self.capture.Modified()
        self.capture.Update()
        output = self.capture.GetOutput()
        width, height, _ = output.GetDimensions()
        return vtk_to_numpy(output.GetPointData().GetScalars()).reshape(height, width, 3)[::-1].copy()


def caption(rgb, title, time, duration, view):
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('DejaVuSans.ttf', 23)
    small = ImageFont.truetype('DejaVuSans.ttf', 15)
    draw.text((30, 22), title, font=font, fill=(31, 49, 48))
    draw.text((30, 54), f'{view}  /  recorded simulation', font=small, fill=(83, 104, 101))
    draw.rounded_rectangle((image.width-118, 25, image.width-26, 55), radius=7, fill=(245, 248, 246))
    draw.text((image.width-105, 31), f'{time:.2f} s', font=small, fill=(38, 62, 59))
    draw.line((30, image.height-23, image.width-30, image.height-23), fill=(188, 205, 198), width=3)
    draw.line((30, image.height-23, 30+(image.width-60)*time/duration, image.height-23), fill=(46, 101, 87), width=3)
    return np.asarray(image)


def render(directory, output, *, stride=5, fps=20, preview=False):
    directory, output = Path(directory), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    score = score_run(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    with np.load(directory/'states.npz', allow_pickle=False) as data:
        states = {k: data[k] for k in data.files}
    with np.load(directory/'trace.npz', allow_pickle=False) as data:
        trace = {k: data[k] for k in data.files}
    config = manifest['config']
    task = manifest.get('task', 'tofu')
    title = {'banana': 'Banana / three cuts', 'tofu': 'Tofu / cut in half',
             'tofu-sequential': 'Tofu / two cuts + left-piece motion'}[task]
    surface = (BananaSkin(states['reference']) if task == 'banana' else
               MaterialSurface(states['reference'], config['grid_spacing']/2))
    scene = CuttingScene(config, task=task)
    selected = list(range(0, len(states['time']), stride))
    if selected[-1] != len(states['time'])-1:
        selected.append(len(states['time'])-1)
    if preview:
        selected = [0, len(states['time'])//2, len(states['time'])-1]
    writers = {} if preview else {view: imageio.get_writer(output/f'{view}.mp4', fps=fps,
        codec='libx264', quality=8, macro_block_size=1, pixelformat='yuv420p') for view in ('surface', 'particles')}
    maximum_smoothing_mm = 0.
    try:
        for i in selected:
            time = float(states['time'][i])
            if task == 'banana':
                components, _ = grid_components(states['nodes'], states['weights'], states['sides'][i])
                vertices, faces, rest, cut_vertices = surface.mesh(
                    states['position'][i], states['deformation'][i], components)
            else:
                vertices, faces, rest, cut_vertices = surface.mesh(states['position'][i], states['sides'][i],
                    states['deformation'][i] if 'deformation' in states else None)
            trace_index = max(0, round(time/config['dt'])-1)
            maximum_smoothing_mm = max(maximum_smoothing_mm, scene.update(
                vertices, faces, rest, cut_vertices, states['position'][i], states['sides'][i], trace['blade_position_m'][trace_index]))
            for view in ('surface', 'particles'):
                rgb = caption(scene.frame(view == 'particles'), title, time, states['time'][-1], view.capitalize())
                if preview:
                    Image.fromarray(rgb).save(output/f'{view}-{i:04d}.png')
                else:
                    writers[view].append_data(rgb)
                    if i == selected[-1]:
                        Image.fromarray(rgb).save(output/f'{view}-poster.png')
            if i % (stride*20) == 0:
                print(f'{task}: rendered {time:.2f} s', flush=True)
    finally:
        for writer in writers.values():
            writer.close()
        scene.window.Finalize()
    provenance = {'source_artifacts': manifest['artifacts'], 'score': score,
        'renderer_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                           (Path(__file__), Path(__file__).with_name('cutting_surface.py'))},
        'frames': len(selected), 'fps': fps, 'physical_duration_s': float(states['time'][-1]),
        'playback_duration_s': len(selected)/fps, 'vtk_version': vtk.vtkVersion.GetVTKVersion(),
        'surface': 'Tofu: exposed material-cell faces embedded in saved positions/F, with local reconstruction for older records. Banana: a dense authored fruit skin fitted to the seed profile, with longitudinal ridges, fibres and end/core colours. Completed separations from the native transfer graph create segment caps; incomplete incisions are not resolved by this skin and must be inspected in particles. Every skin vertex blends up to 32 local particle affine maps within its observed separated component. Subsequent smoothing retains embedded cap x coordinates. No prescribed piece motion. Particles remain the physical geometry reference. This is not a scan or calibrated food model.',
        'maximum_display_smoothing_displacement_mm': maximum_smoothing_mm,
        'description': 'Authored board, lighting and knife handle are scenery. Object and blade motion use saved native states; no added visual separation.',
        'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--stride', type=int, default=5)
    args = parser.parse_args()
    render(args.directory, args.output, preview=args.preview, stride=args.stride)


if __name__ == '__main__':
    main()
