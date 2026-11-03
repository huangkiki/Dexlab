"""Convert a flattened browser GLB to a textured USD scene. No physics ownership."""
from pathlib import Path
import json
import struct

import numpy as np
import trimesh
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdRender, UsdShade, Vt


def matrix(values):
    return Gf.Matrix4d(*np.asarray(values, dtype=float).reshape(-1).tolist())


def look_at(position, target):
    back = np.subtract(position, target).astype(float)
    back /= np.linalg.norm(back)
    right = np.cross([0., 0., 1.], back)
    right /= np.linalg.norm(right)
    transform = np.eye(4)
    transform[:3, :3] = [right, np.cross(back, right), back]
    transform[3, :3] = position
    return matrix(transform)


def build_scene(glb: Path, output: Path):
    blob = glb.read_bytes()
    length, kind = struct.unpack_from("<II", blob, 12)
    if kind != 0x4E4F534A:
        raise ValueError("GLB must start with its JSON chunk")
    description = json.loads(blob[20:20 + length])
    for item in description.get("buffers", []) + description.get("images", []):
        if "uri" in item and not item["uri"].startswith("data:"):
            raise ValueError("Only embedded GLB resources are accepted")
    scene = trimesh.load_scene(glb, process=False)
    nodes = sorted(scene.graph.nodes_geometry, key=lambda n: int(n.removeprefix("part_")))
    if not 1 <= len(nodes) <= 512 or any(n != f"part_{i}" for i, n in enumerate(nodes)):
        raise ValueError("Expected a bounded, contiguous flattened scene")
    if sum(len(g.faces) for g in scene.geometry.values()) > 2_000_000:
        raise ValueError("Scene exceeds two million triangles")
    stage = Usd.Stage.CreateNew(str(output / "scene.usda"))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    UsdGeom.Xform.Define(stage, "/World")
    for index, node in enumerate(nodes):
        transform, key = scene.graph[node]
        mesh = scene.geometry[key]
        path = f"/World/part_{index}"
        usd = UsdGeom.Mesh.Define(stage, path)
        usd.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(mesh.vertices.astype(np.float32)))
        usd.CreateFaceVertexCountsAttr([3] * len(mesh.faces))
        usd.CreateFaceVertexIndicesAttr(mesh.faces.ravel().tolist())
        usd.CreateSubdivisionSchemeAttr("none")
        usd.CreateDoubleSidedAttr(True)
        usd.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(mesh.vertex_normals.astype(np.float32)))
        usd.SetNormalsInterpolation("vertex")
        usd.AddTransformOp().Set(matrix(transform.T))
        material = UsdShade.Material.Define(stage, f"/World/Materials/m{index}")
        shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("Surface"))
        shader.CreateIdAttr("UsdPreviewSurface")
        source = getattr(mesh.visual, "material", None)
        factor = getattr(source, "baseColorFactor", None)
        color = np.asarray(factor[:3], dtype=float) / 255 if factor is not None else np.ones(3)
        # glTF baseColorFactor is linear; trimesh stores it as uint8.
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        roughness = getattr(source, "roughnessFactor", None)
        metallic = getattr(source, "metallicFactor", None)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness if roughness is not None else 1.))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic if metallic is not None else 0.))
        emission = getattr(source, "emissiveFactor", None)
        if emission is not None:
            shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*np.asarray(emission, dtype=float)))
        texture = getattr(source, "baseColorTexture", None)
        if texture is not None:
            if not hasattr(mesh.visual, "uv") or mesh.visual.uv is None:
                raise ValueError("Textured mesh has no UVs")
            texture.save(output / f"texture-{index}.png")
            uv = UsdGeom.PrimvarsAPI(usd).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, "vertex")
            uv.Set(Vt.Vec2fArray.FromNumpy(mesh.visual.uv.astype(np.float32)))
            reader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("UV"))
            reader.CreateIdAttr("UsdPrimvarReader_float2")
            reader.CreateInput("varname", Sdf.ValueTypeNames.String).Set("st")
            tex = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("Color"))
            tex.CreateIdAttr("UsdUVTexture")
            tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f"texture-{index}.png")
            tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
            tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(), "result")
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(), "rgb")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(usd.GetPrim()).Bind(material)
    camera = UsdGeom.Camera.Define(stage, "/World/Camera")
    camera.CreateClippingRangeAttr((.01, 10))
    camera.CreateFocalLengthAttr(18.)
    camera.CreateHorizontalApertureAttr(24.)
    camera.CreateVerticalApertureAttr(18.)
    camera.AddTransformOp().Set(look_at((0, -1, .66), (0, 0, .10)))
    for name, pos, power, color in [
        ("Key", (-.3, -.6, 1.1), 650., (1., .93, .86)),
        ("Fill", (.5, -.1, .75), 300., (.88, .75, 1.)),
        ("Rim", (0., .5, .9), 400., (1., .70, .89)),
    ]:
        light = UsdLux.RectLight.Define(stage, f"/World/{name}")
        light.CreateIntensityAttr(power)
        light.CreateColorAttr(color)
        light.CreateWidthAttr(.7)
        light.CreateHeightAttr(.7)
        light.AddTransformOp().Set(look_at(pos, (0, 0, .05)))
    ambient = UsdLux.DomeLight.Define(stage, "/Lighting/Ambient")
    ambient.CreateIntensityAttr(80.)
    ambient.CreateColorAttr((.76, .66, .88))
    for lane in range(3):
        root = "/World" if lane == 0 else f"/Lane{lane}"
        if lane:
            duplicate = UsdGeom.Xform.Define(stage, root)
            duplicate.GetPrim().GetReferences().AddInternalReference("/World")
            duplicate.AddTranslateOp().Set((lane * 4., 0., 0.))
        product = UsdRender.Product.Define(stage, f"/Render/Camera{lane}")
        product.CreateCameraRel().SetTargets([root + "/Camera"])
        product.CreateResolutionAttr(Gf.Vec2i(640, 480))
        var = UsdRender.Var.Define(stage, product.GetPath().AppendChild("HdrColor"))
        var.CreateSourceNameAttr("HdrColor")
        product.CreateOrderedVarsRel().SetTargets([var.GetPath()])
        prim = product.GetPrim()
        prim.AddAppliedSchema("OmniRtxSettingsCommonAPI_1")
        prim.CreateAttribute("omni:rtx:background:source:type", Sdf.ValueTypeNames.Token).Set("color")
        prim.CreateAttribute("omni:rtx:background:source:color", Sdf.ValueTypeNames.Color3f).Set((.0018, .0011, .0028))
        prim.CreateAttribute("omni:rtx:rendermode", Sdf.ValueTypeNames.Token).Set("RealTimePathTracing")
        prim.CreateAttribute("omni:rtx:rtpt:maxBounces", Sdf.ValueTypeNames.UInt).Set(4)
    stage.GetRootLayer().Save()
    return [f"/World/part_{i}" for i in range(len(nodes))]
