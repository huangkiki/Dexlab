"""OpenArm V20 with two Wuji Hand 2 Beta1 hands."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from physics_utils import physics, robotics
ASSET = Path(__file__).resolve().parent.parent / "assets/robot"

def display_xml(prefab):
    display = {name: str((ASSET / path).resolve()) for name, path in json.loads((ASSET / "display.json").read_text()).items()}
    for link in prefab.links:
        if not link.render_model_file:
            continue
        path = ASSET / f"{link.name}_render.obj"
        if not path.exists():
            scene = trimesh.load_scene(link.render_model_file)
            pieces = []
            for node in scene.graph.nodes_geometry:
                transform, geometry = scene.graph[node]
                mesh = scene.geometry[geometry].copy()
                mesh.apply_transform(transform)
                mesh.apply_transform(
                    trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
                )
                pieces.append(mesh)
            trimesh.util.concatenate(pieces).export(path)
        display[link.name] = str(path.resolve())
    root = ET.Element(
        "mujoco", model="OpenArm + Wuji | SuperDex"
    )
    visual = ET.SubElement(root, "visual")
    ET.SubElement(visual, "global", offwidth="1280", offheight="960")
    ET.SubElement(visual, "headlight", ambient=".4 .4 .4", diffuse=".6 .6 .6")
    assets = ET.SubElement(root, "asset")
    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "light", pos="1 -2 4", diffuse=".8 .8 .8")
    ET.SubElement(
        assets,
        "texture",
        name="checker",
        type="2d",
        builtin="checker",
        rgb1=".16 .2 .25",
        rgb2=".2 .24 .3",
        width="256",
        height="256",
    )
    ET.SubElement(assets, "material", name="floor", texture="checker", texrepeat="8 8")
    ET.SubElement(world, "geom", type="plane", size="4 4 .1", material="floor")
    for link in prefab.links:
        body = ET.SubElement(world, "body", name=f"native_{link.name}", mocap="true")
        if link.name in display:
            ET.SubElement(assets, "mesh", name=link.name, file=display[link.name])
            color = ".74 .77 .8 1"
            if "pad" in link.name:
                color = ".2 .22 .25 1"
            ET.SubElement(
                body,
                "geom",
                type="mesh",
                mesh=link.name,
                rgba=color,
                contype="0",
                conaffinity="0",
            )
    return root
