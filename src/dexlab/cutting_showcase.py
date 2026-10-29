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
from dexlab.cutting_surface import LinkedVolumeSurface
from dexlab.cutting_metrics import ReplayMeasurements


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
    grain = (.012 * np.sin(.13 * y + 2.8 * np.sin(x / 240))
             + .009 * np.sin(1.7 * y + 4 * np.sin(x / 330))
             + .008 * rng.normal(size=x.shape))
    planks = .008 * (y // 128 % 3) - .012 * (y % 128 < 1)
    colors = np.clip(np.array([.81, .71, .55])[None, None] + (grain + planks)[:, :, None], 0, 1)
    data = vtk.vtkImageData()
    data.SetDimensions(1024, 512, 1)
    data.GetPointData().SetScalars(numpy_to_vtk((colors * 255).astype(np.uint8).reshape(-1, 3), deep=True))
    texture = vtk.vtkTexture()
    texture.SetInputData(data)
    texture.InterpolateOn()
    return texture


def tofu_texture():
    """Small material-attached pores; colour detail only, never a cut mask."""
    rng = np.random.default_rng(203)
    y, x = np.mgrid[:256, :256]
    shade = np.ones((256, 256))
    for cx, cy, radius in zip(rng.uniform(0, 256, 95), rng.uniform(0, 256, 95),
                              rng.uniform(.7, 2.2, 95), strict=True):
        distance = np.minimum(abs(x-cx), 256-abs(x-cx))**2 + np.minimum(abs(y-cy), 256-abs(y-cy))**2
        shade -= .12*np.exp(-distance/(2*radius**2))
    colors = np.clip(shade[:, :, None]*np.array([1., .996, .975]) +
                     rng.normal(0, .003, (256, 256, 1)), 0, 1)
    data = vtk.vtkImageData()
    data.SetDimensions(256, 256, 1)
    data.GetPointData().SetScalars(numpy_to_vtk((colors*255).astype(np.uint8).reshape(-1, 3), deep=True))
    texture = vtk.vtkTexture()
    texture.SetInputData(data)
    texture.RepeatOn()
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
    def __init__(self, config, width=960, height=520, *, task='tofu'):
        self.config = config
        self.task = task
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(.91, .93, .94)
        self.renderer.SetBackground2(.985, .985, .98)
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
        for position, intensity in [((-80, -90, 220), .8), ((180, -30, 120), .5), ((-60, 130, 90), .35)]:
            light = vtk.vtkLight()
            light.SetLightTypeToSceneLight()
            light.SetPosition(*position)
            light.SetFocalPoint(0, 0, 0)
            light.SetIntensity(intensity)
            self.renderer.AddLight(light)
        banana = config.get('shape') == 'banana'
        width_mm, depth_mm = (178, 110) if banana else (135, 105)
        board = cube(self.renderer, (width_mm, depth_mm, 5), (0, 0, -2.7), (1., 1., 1.))
        texture_coordinates = vtk.vtkTextureMapToPlane()
        texture_coordinates.SetInputConnection(board.GetMapper().GetInputConnection(0, 0))
        texture_coordinates.SetOrigin(-width_mm/2, -depth_mm/2, 0)
        texture_coordinates.SetPoint1(width_mm/2, -depth_mm/2, 0)
        texture_coordinates.SetPoint2(-width_mm/2, depth_mm/2, 0)
        board.GetMapper().SetInputConnection(texture_coordinates.GetOutputPort())
        board.SetTexture(wood_texture())
        board.GetProperty().SetAmbient(.35)
        board.GetProperty().SetDiffuse(.6)
        board.GetProperty().SetSpecular(.08)
        board.GetProperty().SetSpecularPower(20)
        floor = cube(self.renderer, (500, 400, 5), (0, 0, -10), (.85, .89, .885))
        self.half = np.asarray(config['blade_half_size']) * 1000
        self.blade = knife_actor(self.renderer, self.half, config.get('blade_bevel_height', 0) * 1000)
        self.blade.GetProperty().SetSpecular(.95)
        self.blade.GetProperty().SetSpecularPower(90)
        self.blade.GetProperty().SetAmbient(.3)
        self.handle = cube(self.renderer, (6, 12, 27), (0, 0, 100), (.105, .125, .13))
        self.handle.GetProperty().SetSpecular(.4)
        self.bolster = cube(self.renderer, (7, 15, 3), (0, 0, 80), (.67, .73, .76))
        self.body = vtk.vtkActor()
        self.body.GetProperty().SetSpecular(.12 if banana else .04)
        self.body.GetProperty().SetSpecularPower(35)
        self.body.GetProperty().SetAmbient(.38)
        self.body.GetProperty().SetDiffuse(.62)
        if not banana:
            self.body.SetTexture(tofu_texture())
        self.renderer.AddActor(self.body)
        self.particles = vtk.vtkActor()
        self.particles.GetProperty().SetAmbient(.52)
        self.particles.GetProperty().SetDiffuse(.48)
        self.particles.GetProperty().SetSpecular(0)
        self.renderer.AddActor(self.particles)
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(110, -220, 175)
        camera.SetFocalPoint(0, 0, 24)
        camera.SetViewUp(0, 0, 1)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(57 if banana else 54)
        if task == 'tofu-sequential':
            # Match the reference presentation, retaining native dimensions
            # and particle inventory. Geometry is never rescaled for appearance.
            self.renderer.GradientBackgroundOff()
            self.renderer.SetBackground(.94, .94, .93)
            ao.SetRadius(.8)
            board.SetVisibility(False)
            floor.SetPosition(0, 0, -2.62)
            floor.GetProperty().SetColor(.94, .94, .93)
            floor.GetProperty().SetAmbient(.8)
            floor.GetProperty().SetDiffuse(.2)
            self.handle.SetVisibility(False)
            self.bolster.SetVisibility(False)
            self.blade.GetProperty().SetColor(.77, .79, .79)
            self.particles.GetProperty().SetAmbient(.78)
            self.particles.GetProperty().SetDiffuse(.22)
            camera.SetPosition(15, -300, 190)
            camera.SetFocalPoint(0, 0, 15)
            camera.SetParallelScale(90)
            # These floor markers stay in reference space; they never follow a piece.
            for x, color in [(-30, (.55, .47, .75)), (0, (.92, .63, .35)), (30, (.40, .65, .79))]:
                cube(self.renderer, (.45, 20, .12), (x, -28, -.12), color)
        elif task == 'tofu-scoring':
            self.body.GetProperty().SetAmbient(.65)
            self.body.GetProperty().SetDiffuse(.3)
            ao.SetRadius(1.2)
            ao.SetBias(.02)
            antialias = vtk.vtkSSAAPass()
            antialias.SetDelegatePass(ao)
            self.renderer.SetPass(antialias)
            camera.SetPosition(200, -80, 280)
            camera.SetFocalPoint(0, 0, 17)
            camera.SetParallelScale(48)
        self.capture = vtk.vtkWindowToImageFilter()
        self.capture.SetInput(self.window)
        self.capture.SetInputBufferTypeToRGB()
        self.capture.ReadFrontBufferOff()

    def update(self, vertices, faces, rest, cut_vertices, positions, codes, blade, blade_yaw=0.):
        mesh = polydata(vertices*1000, faces)
        triangle = vtk.vtkTriangleFilter()
        triangle.SetInputData(mesh)
        triangle.Update()
        surface = triangle.GetOutput()
        banana = self.config.get('shape') == 'banana'
        base = np.array([.985, .95, .78]) if banana else np.array([.975, .965, .905])
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
            radius = np.linalg.norm(radial, axis=1)
            core = np.exp(-radius**2/.0028**2)
            star = np.exp(-radius**2/.005**2) * (.5+.5*np.cos(3*theta))**14
            colors[cut_vertices] -= (core[cut_vertices]*.11+star[cut_vertices]*.055)[:, None]
            colors = np.clip(colors, 0, 1)
        scalars = numpy_to_vtk((colors*255).astype(np.uint8), deep=True)
        scalars.SetName('MaterialColor')
        surface.GetPointData().SetScalars(scalars)
        material_coordinates = numpy_to_vtk(np.ascontiguousarray(rest), deep=True)
        material_coordinates.SetName('MaterialRest')
        surface.GetPointData().AddArray(material_coordinates)
        if not banana:
            uv = np.column_stack((rest[:, 0]+rest[:, 1], rest[:, 2]+.3*rest[:, 1]))/.012
            surface.GetPointData().SetTCoords(numpy_to_vtk(np.ascontiguousarray(uv), deep=True))
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(surface)
        # Average the small dual-contouring facets while retaining the near
        # right-angle edge between an outer skin and a fresh cut cap.
        normals.SetFeatureAngle(80)
        normals.SplittingOn()
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
            palette = np.array([[.94, .915, .82]])
            colour_index = np.zeros(len(codes), dtype=int)
        elif self.task == 'tofu-scoring':
            # Colour reveals recorded histories even when elastic faces reclose.
            # The unassigned lower bridge remains cream; no position is changed.
            palette = np.array([[.94, .915, .82], [.35, .65, .76], [.92, .61, .32],
                                [.60, .80, .84], [.98, .78, .46]])
            first, second = codes % 3, codes // 3 % 3
            colour_index = np.where(first > 0, first, second)
            colour_index[second == 2] += 2
        else:
            colour_index = codes % len(palette)
        particles.GetPointData().SetScalars(numpy_to_vtk((255*palette[colour_index]).astype(np.uint8), deep=True))
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(self.config['grid_spacing']*250)
        sphere.SetThetaResolution(16)
        sphere.SetPhiResolution(12)
        glyph = vtk.vtkGlyph3DMapper()
        glyph.SetInputData(particles)
        glyph.SetSourceConnection(sphere.GetOutputPort())
        glyph.ScalingOff()
        self.particles.SetMapper(glyph)
        self.blade.SetPosition(*(blade*1000))
        self.bolster.SetPosition(*(blade*1000 + [0, 0, self.half[2]+1.5]))
        self.handle.SetPosition(*(blade*1000 + [0, 0, self.half[2]+16.5]))
        for actor in (self.blade, self.bolster, self.handle):
            actor.SetOrientation(0., 0., np.degrees(blade_yaw))
        self.renderer.ResetCameraClippingRange()
        return 0.

    def frame(self, particles=False):
        self.body.SetVisibility(not particles)
        self.particles.SetVisibility(particles)
        self.window.Render()
        self.capture.Modified()
        self.capture.Update()
        output = self.capture.GetOutput()
        width, height, _ = output.GetDimensions()
        return vtk_to_numpy(output.GetPointData().GetScalars()).reshape(height, width, 3)[::-1].copy()

    def projected_bounds(self, positions):
        """Screen rectangle of a measured particle region, including proxy radii."""
        radius = self.config['grid_spacing'] * 250
        low, high = positions.min(axis=0)*1000-radius, positions.max(axis=0)*1000+radius
        points = []
        for x in (low[0], high[0]):
            for y in (low[1], high[1]):
                for z in (low[2], high[2]):
                    self.renderer.SetWorldPoint(x, y, z, 1.)
                    self.renderer.WorldToDisplay()
                    px, py, _ = self.renderer.GetDisplayPoint()
                    points.append((px, self.window.GetSize()[1]-py))
        points = np.asarray(points)
        return (*points.min(axis=0), *points.max(axis=0))


def caption(rgb, title, time, duration, view, metrics, task, particle_count, annotation=None):
    if metrics['motion_protocol'] in ('cut-push', 'cut-no-push'):
        return cut_push_caption(rgb, time, duration, view, metrics, task)
    if task == 'tofu-sequential':
        return comparison_caption(rgb, time, metrics, view, annotation)
    image = Image.new('RGB', (rgb.shape[1], rgb.shape[0]+180), (248, 249, 246))
    image.paste(Image.fromarray(rgb), (0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('DejaVuSans.ttf', 28)
    small = ImageFont.truetype('DejaVuSans.ttf', 20)
    number = ImageFont.truetype('DejaVuSans.ttf', 36)
    draw.rectangle((0, 0, image.width, 83), fill=(248, 250, 248))
    draw.text((26, 18), title, font=font, fill=(31, 49, 48))
    shown_view = 'Cut histories' if task == 'tofu-scoring' and view == 'Particles' else view
    draw.text((26, 54), f'{shown_view} | {particle_count:,} native particles | {metrics["phase"]}', font=small, fill=(83, 104, 101))
    draw.rounded_rectangle((image.width-150, 20, image.width-20, 60), radius=7, fill=(245, 248, 246))
    draw.text((image.width-138, 24), f'{time:.2f} s', font=font, fill=(38, 62, 59))
    top = rgb.shape[0]
    draw.line((26, top, image.width-26, top), fill=(188, 205, 198), width=2)
    gaps = metrics['face_opening_mm']
    fields = [('Cut 1 opening', '--' if gaps[0] is None else f'{gaps[0]:+.3f} mm'),
              ('Knife reaction', f'{metrics["knife_material_force_n"]:.3f} N'),
              ('Interior volume', f'{metrics["interior_volume_change_percent"]:+.3f}%')]
    if task == 'banana':
        fields = [(f'Cut {cut+1} opening', '--' if gap is None else f'{gap:+.3f} mm')
                  for cut, gap in enumerate(gaps)]
    if task == 'tofu-scoring':
        fields = [(f'Score {cut+1} opening', '--' if gap is None else f'{gap:+.3f} mm')
                  for cut, gap in enumerate(gaps)] + [('Knife depth', f'{metrics["blade_depth_mm"]:.2f} mm')]
    for x, (label, value) in zip((26, 344, 662), fields, strict=True):
        draw.text((x, top+13), label, font=small, fill=(83, 104, 101))
        draw.text((x, top+41), value, font=number, fill=(30, 77, 64))
    displacement = metrics['centroid_x_from_probe_mm']
    names = tuple(str(i+1) for i in range(len(gaps)+1))
    motion = 'After impulse: ' + ('pending' if displacement is None else '   '.join(
        f'{name} {value:+.2f}' for name, value in zip(names, displacement, strict=True)) + ' mm')
    if task == 'tofu-scoring':
        motion = (f'Connected pieces: {metrics["native_components"]}  |  Base: '
                  + ('intact' if metrics['base_intact'] else 'CHECK FAILED'))
    draw.text((26, top+96), motion, font=font, fill=(31, 49, 48))
    footnote = (f'Knife {metrics["knife_material_force_n"]:.3f} N | interior volume '
                f'{metrics["interior_volume_change_percent"]:+.3f}% | synthetic material'
                if task == 'banana' else 'Saved-state measurements | synthetic material | affine face / interior tetrahedra')
    if task == 'tofu-scoring':
        footnote = 'Mean interior openings | elastic surface can reclose | native cut histories persist'
    draw.text((26, top+137), footnote,
              font=small, fill=(83, 104, 101))
    draw.line((26, image.height-8, image.width-26, image.height-8), fill=(188, 205, 198), width=3)
    draw.line((26, image.height-8, 26+(image.width-52)*time/duration, image.height-8), fill=(46, 101, 87), width=3)
    return np.asarray(image)


def cut_push_caption(rgb, time, duration, view, metrics, task):
    """Show measured contact and every piece throughout the continuous action."""
    image = Image.new('RGB', (rgb.shape[1], rgb.shape[0] + 190), (248, 249, 246))
    image.paste(Image.fromarray(rgb), (0, 0))
    draw = ImageDraw.Draw(image)
    label = ImageFont.truetype('DejaVuSans.ttf', 22)
    number = ImageFont.truetype('DejaVuSans.ttf', 30)
    ink, secondary = (31, 49, 48), (83, 104, 101)
    title = 'Tofu / two cuts, then push' if task == 'tofu-sequential' else 'Banana / three cuts, then push'
    draw.rectangle((0, 0, image.width, 80), fill=(248, 249, 246))
    draw.text((24, 12), title, font=number, fill=ink)
    draw.text((24, 49), f'{view} | eta {metrics["dynamic_viscosity_pa_s"]:g} Pa s | {metrics["phase"]}',
              font=label, fill=secondary)
    draw.text((image.width - 145, 12), f'{time:.2f} s', font=number, fill=ink)
    top = rgb.shape[0]
    draw.line((24, top, image.width - 24, top), fill=(188, 205, 198), width=2)
    force = metrics['knife_on_material_n']
    fields = [('Knife contact |F|', f'{metrics["knife_material_force_n"]:.3f} N'),
              ('On material Fx', f'{force[0]:+.3f} N'),
              ('On material Fz', f'{force[2]:+.3f} N')]
    for column, (name, value) in enumerate(fields):
        x = 24 + column * 310
        draw.text((x, top + 9), name, font=label, fill=secondary)
        draw.text((x, top + 36), value, font=number, fill=ink)
    displacement = metrics['centroid_x_from_start_mm']
    names = ('Left', 'Middle', 'Right') if len(displacement) == 3 else ('Piece 1', 'Piece 2', 'Piece 3', 'Piece 4')
    for column, (name, value) in enumerate(zip(names, displacement, strict=True)):
        x = 24 + column * (image.width - 48) // len(displacement)
        draw.text((x, top + 85), name + ' dx', font=label, fill=secondary)
        draw.text((x, top + 112), f'{value:+.3f} mm', font=number, fill=ink)
    draw.text((24, top + 157), 'dx from initial state | pieces left to right | measured contact | synthetic material',
              font=ImageFont.truetype('DejaVuSans.ttf', 19), fill=secondary)
    draw.line((24, image.height - 6, image.width - 24, image.height - 6), fill=(188, 205, 198), width=3)
    draw.line((24, image.height - 6, 24 + (image.width - 48) * time / duration, image.height - 6),
              fill=(46, 101, 87), width=3)
    return np.asarray(image)


def comparison_caption(rgb, time, metrics, view, bounds=None):
    """Reference-sized neutral scene with readable measurements in its margins."""
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    label = ImageFont.truetype('DejaVuSans.ttf', 21)
    number = ImageFont.truetype('DejaVuSans.ttf', 32)
    ink, secondary = (52, 58, 59), (96, 101, 101)
    draw.text((24, 16), f'DexLab  /  {view}  /  {metrics["phase"]}', font=label, fill=ink)
    draw.text((image.width-145, 12), f'{time:.2f} s', font=number, fill=ink)
    if bounds is not None and time >= 4.:
        orange = (211, 121, 35)
        draw.rectangle(bounds, outline=orange, width=2)
        draw.text((bounds[2]+12, bounds[1]-32),
                  f'{-metrics["interior_volume_change_percent"]:.3f}%', font=number, fill=orange)
    top = image.height - 112
    draw.rectangle((0, top-8, image.width, image.height), fill=(241, 241, 238))
    gap = metrics['face_opening_mm'][0]
    fields = [('Cut 1 opening', '--' if gap is None else f'{gap:+.3f} mm'),
              ('Middle contraction', f'{-metrics["interior_volume_change_percent"]:.3f}%'),
              ('Knife on material / x', f'{metrics["knife_on_material_x_n"]:+.3f} N')]
    for x, (name, value) in zip((24, 335, 660), fields, strict=True):
        draw.text((x, top), name, font=label, fill=secondary)
        draw.text((x, top+27), value, font=number, fill=ink)
    displacement = metrics['centroid_x_from_probe_mm']
    motion = metrics['motion_protocol']
    line = ('Knife-face push after 4.00 s / negative force = left' if motion == 'knife-push' else
            'No-push control / no material kick' if motion == 'no-push' else 'Left-piece impulse at 4.20 s')
    if displacement is not None:
        line = 'dx (mm):  ' + '   '.join(f'{name} {value:+.3f}' for name, value in
                                       zip(('L', 'M', 'R'), displacement, strict=True))
    draw.text((24, top+75), line, font=label, fill=ink)
    return np.asarray(image)


def write_gif(frames, path):
    """One palette avoids frame-to-frame colour noise and bloated static regions."""
    sample = Image.new('RGB', (frames[0].width*3, frames[0].height))
    for column, index in enumerate((0, len(frames)//2, len(frames)-1)):
        sample.paste(frames[index], (column*frames[0].width, 0))
    palette = sample.quantize(colors=192)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=120,
                    loop=0, optimize=True, disposal=1)
    with Image.open(path) as encoded:
        for index in (0, len(frames)//2, len(frames)-1):
            encoded.seek(index)
            if not np.array_equal(np.asarray(encoded.convert('RGB')),
                                  np.asarray(indexed[index].convert('RGB'))):
                raise ValueError('GIF encoding changed a composed frame')


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
             'tofu-sequential': 'Tofu / two cuts + left impulse',
             'tofu-scoring': 'Tofu / crossed shallow cuts'}[task]
    if task == 'tofu-sequential' and manifest.get('motion_protocol') in ('knife-push', 'no-push'):
        title = 'Tofu / two cuts + ' + manifest['motion_protocol']
    if manifest.get('motion_protocol') in ('cut-push', 'cut-no-push'):
        title = ('Banana / three cuts + ' if task == 'banana' else 'Tofu / two cuts + ') + manifest['motion_protocol']
    measurements = ReplayMeasurements(states, trace, manifest)
    surface = LinkedVolumeSurface(
        states['reference'], measurements.planes, measurements.axes,
        config['size'], config['grid_spacing'], config['grid_spacing']/4,
        config.get('shape', 'block'))
    continuous = manifest.get('motion_protocol') in ('cut-push', 'cut-no-push')
    scene = CuttingScene(config, task=('tofu' if continuous and task == 'tofu-sequential' else task),
                         height=600 if task == 'tofu-sequential' and not continuous else 520)
    selected = list(range(0, len(states['time']), stride))
    if selected[-1] != len(states['time'])-1:
        selected.append(len(states['time'])-1)
    if preview:
        selected = sorted(set([0, int(np.argmin(abs(states['time']-.8))),
                               len(states['time'])//2, len(states['time'])-1]))
    writers = {} if preview else {view: imageio.get_writer(output/f'{view}.mp4', fps=fps,
        codec='libx264', quality=8, macro_block_size=1, pixelformat='yuv420p') for view in ('surface', 'particles')}
    maximum_smoothing_mm = 0.
    measured_frames, gif_frames = [], {'surface': [], 'particles': []}
    try:
        for i in selected:
            time = float(states['time'][i])
            measured = measurements.frame(i)
            measured_frames.append(measured)
            components, _ = grid_components(states['nodes'], states['weights'], states['sides'][i])
            vertices, faces, rest, cut_vertices = surface.mesh(
                states['position'][i], states['deformation'][i], states['sides'][i], components)
            trace_index = max(0, round(time/config['dt'])-1)
            maximum_smoothing_mm = max(maximum_smoothing_mm, scene.update(
                vertices, faces, rest, cut_vertices, states['position'][i], states['sides'][i],
                trace['blade_position_m'][trace_index],
                trace['blade_yaw_rad'][trace_index] if 'blade_yaw_rad' in trace else 0.))
            for view in ('surface', 'particles'):
                scene_frame = scene.frame(view == 'particles')
                bounds = (scene.projected_bounds(states['position'][i][measurements.regions == 1])
                          if task == 'tofu-sequential' else None)
                rgb = caption(scene_frame, title, time, states['time'][-1],
                              view.capitalize(), measured, task, len(states['reference']), bounds)
                if preview:
                    Image.fromarray(rgb).save(output/f'{view}-{i:04d}.png')
                else:
                    writers[view].append_data(rgb)
                    gif_height = round(720 * rgb.shape[0] / rgb.shape[1])
                    gif_frames[view].append(Image.fromarray(rgb).resize((720, gif_height), Image.Resampling.LANCZOS))
                    if i == (selected[0] if task == 'tofu-sequential' else selected[-1]):
                        Image.fromarray(rgb).save(output/f'{view}-poster.png')
            if i % (stride*20) == 0:
                print(f'{task}: rendered {time:.2f} s', flush=True)
    finally:
        for writer in writers.values():
            writer.close()
        scene.window.Finalize()
    if not preview:
        for view, frames in gif_frames.items():
            # Slower playback makes measurements legible; displayed time remains native time.
            write_gif(frames, output/f'{view}.gif')
    (output/'measurements.json').write_text(json.dumps(
        {'definitions': measurements.definitions(), 'frames': measured_frames}, indent=2, allow_nan=False)+'\n')
    provenance = {'source_artifacts': manifest['artifacts'], 'score': score,
        'renderer_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                           (Path(__file__), Path(__file__).with_name('cutting_surface.py'),
                            Path(__file__).with_name('cutting_metrics.py'))},
        'frames': len(selected), 'fps': fps, 'physical_duration_s': float(states['time'][-1]),
        'poster_state_frame': selected[0] if task == 'tofu-sequential' else selected[-1],
        'particle_colours': ('Native ternary cut histories; cream means unassigned. Elastic surface closure does not erase history.'
                             if task == 'tofu-scoring' else 'Cream native particles for sequential tofu; history palette for other tasks.'),
        'playback_duration_s': len(selected)/fps, 'vtk_version': vtk.vtkVersion.GetVTKVersion(),
        'gif_playback': {'duration_per_frame_ms': 120, 'native_state_frames': selected,
                         'description': 'Uniformly slowed recorded frames; no interpolated motion or invented physical time.'},
        'surface': 'Tofu and banana use a linked reference volume that stores point/normal Hermite samples on primal links for the authored original boundary and the recorded axis-aligned blade paths. Native opposing side digits disconnect candidate links only after the blade sweep labels both sides; unassigned links retain a partial-cut bridge. Connected material uses per-cell link components and QEF dual vertices. Once the saved mechanical state contains disjoint components, each observed component is reconstructed as a closed local dual-contouring volume clipped by its recorded cut half-spaces; this prevents a triangle from sharing two incompatible motion fields. Representatives inherit native cut codes/components and move through fixed trilinear weights in a compatible nodal field reconstructed by locally averaging saved particle x/F affine predictions; common affine motion remains exact. The surface grid spacing is one quarter of the mechanical grid spacing. Paths with lateral sweep beyond half a material spacing remain rejected by recorded-cut extraction. Fully intersecting through-cut motion is analytically tested but not qualified as a public recorded task; the public crossed task retains a connected lower bridge. This is a paper-inspired independent implementation for the current axis-aligned guided blade family, not an arbitrary curved-cut or author-code reproduction. Display normals average facets below 80 degrees, but no vertex smoothing or prescribed piece motion is applied. Particles remain the physical geometry reference. The fruit is authored, not scanned or food-calibrated.',
        'maximum_display_smoothing_displacement_mm': maximum_smoothing_mm,
        'description': 'Authored board, lighting and knife handle are scenery. Object and blade motion use saved native states; no added visual separation. Continuous cut-push tasks share the board/handle presentation and display measured force and all region displacements. Historical sequential tofu uses neutral ground, no board/handle, and an orange projected middle-region rectangle; contraction comes from interior tetrahedra, not rectangle area. Cross scoring uses saved blade yaw and retains the material-cell bridge; it is guided orthogonal scoring, not the author knife-tip path.',
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
