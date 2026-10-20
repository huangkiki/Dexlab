"""Render saved physics states without rerunning or editing the simulation."""

import os

os.environ.setdefault("MUJOCO_GL", "egl")

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import mujoco
import numpy as np

from dexlab import cloth_display


def cloth_view(vertices, vertical_fov_degrees):
    """Keep the entire measured cloth and a 4 cm context margin in view."""
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    radius = float(np.linalg.norm(vertices - center, axis=1).max()) + .04
    distance = max(.30, radius / np.sin(np.deg2rad(vertical_fov_degrees) / 2))
    return center, distance


def render(model, positions, source, task, *, output=None):
    from verify_cloth import SCORER_VERSION, input_hashes, verify_saved

    started = time.perf_counter()
    renderer_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    camera_hash = hashlib.sha256(Path(cloth_display.__file__).read_bytes()).hexdigest()
    source = Path(source)
    destination = Path(output) if output is not None else source.with_name(
        source.name + '-media-' + SCORER_VERSION
    )
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError('Media output must be outside the original recording')
    # Never replace a previous render or add files to a sealed input record.
    destination.mkdir(parents=True, exist_ok=False)
    verification = verify_saved(source)
    verification_path = destination / f"verification-{SCORER_VERSION}.json"
    report_text = json.dumps(verification, indent=2) + "\n"
    with verification_path.open("x") as stream:
        stream.write(report_text)
    with np.load(source / "states.npz", allow_pickle=False) as archive:
        times = archive["time_s"]
        if not np.array_equal(archive["qpos"], positions):
            raise ValueError("Render input differs from saved physics recording")
    if len(times) != len(positions) or not np.allclose(
        times, np.arange(len(times)) / 25, rtol=0, atol=1e-10
    ):
        raise ValueError("Expected complete, uniform 25 Hz playback states")
    data = mujoco.MjData(model)
    camera, overview = mujoco.MjvCamera(), mujoco.MjvCamera()
    camera.azimuth, camera.elevation = 0, -25
    overview.azimuth, overview.elevation = 0, -25
    # A fixed overview preserves absolute motion while the close-up shows
    # contact and folds through the full lift and fall. Neither advances physics.
    vertices = []
    for pose in positions:
        data.qpos[:] = pose
        mujoco.mj_fwdPosition(model, data)
        vertices.append(data.flexvert_xpos.copy())
    overview.lookat[:], overview.distance = cloth_display.fixed_view(
        np.concatenate(vertices), overview.azimuth, overview.elevation,
        model.vis.global_.fovy, aspect=480 / 720,
    )
    model.vis.headlight.ambient[:] = .45
    model.vis.headlight.diffuse[:] = .55
    model.vis.headlight.specular[:] = .05
    model.light_diffuse[:] = (.65, .64, .61)
    model.light_ambient[:] = .15
    model.flex_rgba[:] = (.25, .53, .66, 1)
    model.flex_flatskin[:] = 0
    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if name == "floor":
            model.geom_rgba[geom_id] = (.65, .68, .72, 1)
            model.geom_size[geom_id, :2] = 0  # Infinite visual extent of the existing plane.
        elif name.startswith("table_"):
            model.geom_rgba[geom_id] = (.60, .56, .50, 1)
    option = mujoco.MjvOption()
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXEDGE] = False
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXVERT] = False
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXSKIN] = True
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "1200x780",
        "-r",
        "25",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        "1",
        "-crf",
        "21",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(destination / "video.mp4"),
    ]
    from PIL import Image, ImageDraw, ImageFont

    status = {
        "protocol_failed": "PROTOCOL FAILED",
        "geometry_review_required": "GEOMETRY REVIEW REQUIRED",
        "limited_protocol_pass": "LIMITED PROTOCOL PASS",
    }[verification["assessment"]]
    font = ImageFont.load_default(size=20)
    camera_frames = []
    with (mujoco.Renderer(model, height=720, width=720) as renderer,
          mujoco.Renderer(model, height=720, width=480) as wide_renderer):
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for index, pose in enumerate(positions):
                data.qpos[:] = pose
                mujoco.mj_fwdPosition(model, data)
                camera.lookat[:], camera.distance = cloth_view(
                    data.flexvert_xpos, model.vis.global_.fovy)
                camera_frames.append([*camera.lookat.tolist(), camera.distance])
                picture = Image.new("RGB", (1200, 780), (244, 246, 248))
                for display, view, x in ((renderer, camera, 0), (wide_renderer, overview, 720)):
                    display.update_scene(data, camera=view, scene_option=option)
                    display.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
                    for geom in display.scene.geoms[:display.scene.ngeom]:
                        if geom.objtype == mujoco.mjtObj.mjOBJ_FLEX:
                            geom.specular, geom.shininess = .03, .05
                    picture.paste(Image.fromarray(display.render()), (x, 60))
                draw = ImageDraw.Draw(picture)
                draw.text(
                    (14, 10),
                    f"Cloth {task} | MuJoCo | {times[index]:.2f} / {len(times) / 25:.2f} s",
                    font=font,
                    fill=(28, 40, 51),
                )
                draw.text(
                    (14, 37),
                    f"{status} | Recorded motion, scripted joints",
                    font=font,
                    fill=(68, 80, 91),
                )
                for x, label in ((14, "Cloth detail / tracking camera"),
                                 (734, "Fixed overview")):
                    draw.text((x, 72), label, font=font, fill=(28, 40, 51),
                              stroke_width=2, stroke_fill=(244, 246, 248))
                encoder.stdin.write(picture.tobytes())
                if index in (0, len(positions) // 2, len(positions) - 1):
                    picture.save(destination / f"frame-{index:04d}.png")
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Video encoding failed")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(destination / "video.mp4"),
         "-filter_complex", "fps=12,scale=800:-2:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
         "-filter_complex_threads", "1", "-loop", "0", str(destination / "preview.gif")],
        check=True,
    )
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    if input_hashes(source) != verification["input_sha256"]:
        raise ValueError("A sealed input changed during rendering")
    if digest(Path(__file__)) != renderer_hash or digest(Path(cloth_display.__file__)) != camera_hash:
        raise ValueError("Renderer source changed during playback")
    provenance = {
        "inputs_sha256": verification['input_sha256'],
        "verification_sha256": digest(verification_path),
        "assessment": verification["assessment"],
        "scorer_version": SCORER_VERSION,
        "renderer_sha256": renderer_hash,
        "camera_helper_sha256": camera_hash,
        "display_engine": mujoco.__version__,
        "physics_steps_executed": 0,
        "frame_times_s": times.tolist(),
        "video_fps": 25,
        "gif_fps": 12,
        "camera": {"mode": "synchronized tracking detail plus fixed overview; display only",
                   "detail_lookat_distance": camera_frames,
                   "detail_azimuth": camera.azimuth, "detail_elevation": camera.elevation,
                   "overview_lookat": overview.lookat.tolist(), "overview_distance": overview.distance,
                   "overview_azimuth": overview.azimuth, "overview_elevation": overview.elevation},
        "appearance": "Existing plane with infinite visual extent, neutral floor/table colors, matte cloth and smooth normals; no geometry smoothing",
        "render_and_encoding_seconds": time.perf_counter() - started,
        "video_sha256": digest(destination / "video.mp4"),
        "gif_sha256": digest(destination / "preview.gif"),
    }
    (destination / "media-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New directory outside the recording")
    args = parser.parse_args()
    metadata = json.loads((args.run / "summary.json").read_text())
    model = mujoco.MjModel.from_binary_path(str(args.run / "model.mjb"))
    with np.load(args.run / "states.npz") as recording:
        render(model, recording["qpos"], args.run, metadata["task"], output=args.output)
