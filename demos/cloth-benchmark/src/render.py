"""Close-up playback of recorded cloth vertices; no physics stepping."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from dexlab.cloth import ClothCase


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(directory):
    started = time.perf_counter()
    metadata = json.loads((directory / "run.json").read_text())
    summary = json.loads((directory / "summary.json").read_text())
    if sha256(directory / "trajectory.npz") != metadata["trajectory_sha256"]:
        raise ValueError("Trajectory does not match the recorded digest")
    case = ClothCase(**metadata["case"])
    with np.load(directory / "trajectory.npz", allow_pickle=False) as archive:
        times, positions = archive["time"], archive["positions"]
        rest, triangles = archive["rest_positions"], archive["triangles"]
    if not len(times):
        raise ValueError("No recorded states to render")
    surface = " ".join(map(str, rest.ravel()))
    indices = " ".join(map(str, triangles.ravel()))
    pins = " ".join(map(str, range(len(rest))))
    obstacle = ""
    if case.experiment in ("drape", "folded-drop"):
        obstacle = '<geom type="plane" size=".3 .3 .01" rgba=".2 .24 .29 1"/>'
    if case.experiment == "drape":
        obstacle += (
            f'<geom type="sphere" size="{case.sphere_radius}" '
            f'pos="0 0 {case.sphere_height}" rgba=".83 .54 .2 1"/>'
        )
    xml = f'''<mujoco>
      <visual><global offwidth="960" offheight="640"/><headlight ambient=".4 .4 .4"/></visual>
      <worldbody><light pos="0 -.5 1" diffuse=".8 .8 .8"/>{obstacle}
        <flexcomp name="display" type="direct" dim="2" point="{surface}" element="{indices}"
                  radius="{case.radius}" rgba=".15 .65 .8 1"><pin id="{pins}"/></flexcomp>
      </worldbody></mujoco>'''
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    camera = mujoco.MjvCamera()
    bounds = np.array([positions.min(axis=(0, 1)), positions.max(axis=(0, 1))])
    camera.lookat[:] = bounds.mean(axis=0)
    camera.distance = max(0.32, float(np.linalg.norm(bounds[1] - bounds[0]) * 1.1))
    camera.azimuth, camera.elevation = 0, -20
    option = mujoco.MjvOption()
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXEDGE] = True
    target_times = np.arange(0, times[-1] + 1e-9, 1 / 25)
    selected = np.minimum(np.searchsorted(times, target_times), len(times) - 1)
    if selected[-1] != len(times) - 1:
        selected = np.r_[selected, len(times) - 1]
    media = directory / "media"
    media.mkdir(exist_ok=True)
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
        "960x640",
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
        str(media / "video.mp4"),
    ]
    font = ImageFont.load_default(size=20)
    status = (
        "Protocol checks passed"
        if summary["protocol_checks_passed"]
        else "FAILED protocol checks"
    )
    with mujoco.Renderer(model, height=640, width=960) as renderer:
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for number, index in enumerate(selected):
                # This display-only flex is fixed to world. No solver is invoked.
                data.flexvert_xpos[:] = positions[index]
                renderer.update_scene(data, camera=camera, scene_option=option)
                frame = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, 960, 66), fill=(15, 22, 31))
                draw.text(
                    (14, 10),
                    f"DexLab | {metadata['solver']} | {case.experiment} | {times[index]:.2f} s",
                    font=font,
                )
                draw.text(
                    (14, 37),
                    f"{status} | Nominal material; recorded native motion",
                    font=font,
                )
                encoder.stdin.write(frame.tobytes())
                if number in (0, len(selected) // 2, len(selected) - 1):
                    frame.save(media / f"frame-{number:03d}.png")
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Video encoding failed")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(media / "video.mp4"),
            "-filter_complex",
            "fps=15,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse",
            "-filter_complex_threads",
            "1",
            "-loop",
            "0",
            str(media / "preview.gif"),
        ],
        check=True,
    )
    provenance = {
        "trajectory_sha256": sha256(directory / "trajectory.npz"),
        "run_sha256": sha256(directory / "run.json"),
        "summary_sha256": sha256(directory / "summary.json"),
        "renderer_sha256": sha256(Path(__file__)),
        "render_engine": mujoco.__version__,
        "display_only": True,
        "physics_steps_executed": 0,
        "render_and_encoding_seconds": time.perf_counter() - started,
        "frame_indices": selected.tolist(),
        "frame_times_s": times[selected].tolist(),
        "video_sha256": sha256(media / "video.mp4"),
        "gif_sha256": sha256(media / "preview.gif"),
    }
    (media / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(media)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    render(parser.parse_args().directory)
