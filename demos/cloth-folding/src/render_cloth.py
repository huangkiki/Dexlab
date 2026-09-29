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


def render(model, positions, destination, task):
    from verify_cloth import verify_saved

    started = time.perf_counter()
    verification = verify_saved(destination)
    with np.load(destination / "states.npz", allow_pickle=False) as archive:
        times = archive["time_s"]
        if not np.array_equal(archive["qpos"], positions):
            raise ValueError("Render input differs from saved physics recording")
    if len(times) != len(positions) or not np.allclose(
        times, np.arange(len(times)) / 25, rtol=0, atol=1e-10
    ):
        raise ValueError("Expected complete, uniform 25 Hz playback states")
    data = mujoco.MjData(model)
    camera = mujoco.MjvCamera()
    camera.distance = 0.65 if task == "fold" else 0.42
    camera.azimuth, camera.elevation = 0, -25
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
        "960x720",
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

    status = "PASSED" if verification["passed"] else "FAILED / NOT VERIFIED"
    font = ImageFont.load_default(size=20)
    with np.load(destination / "plan-r.npz") as plan:
        data.qpos[:] = plan["opened"]
        mujoco.mj_fwdPosition(model, data)
        wrist = model.body("r_wrist").id
        local_point = data.xmat[wrist].reshape(3, 3).T @ (
            plan["point"] - data.xpos[wrist]
        )
    with mujoco.Renderer(model, height=720, width=960) as renderer:
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for index, pose in enumerate(positions):
                data.qpos[:] = pose
                mujoco.mj_fwdPosition(model, data)
                # Display-only camera: combine the actual cloth and grasp anchor.
                # It does not change physics or supply controller observations.
                anchor = data.xpos[wrist] + data.xmat[wrist].reshape(3, 3) @ local_point
                cloth_center = (data.flexvert_xpos.min(axis=0) + data.flexvert_xpos.max(axis=0)) / 2
                camera.lookat[:] = (anchor + cloth_center) / 2
                renderer.update_scene(data, camera=camera)
                frame = renderer.render()
                picture = Image.fromarray(frame)
                draw = ImageDraw.Draw(picture)
                draw.rectangle((0, 0, 960, 66), fill=(14, 20, 29))
                draw.text(
                    (14, 10),
                    f"DexLab | MuJoCo cloth {task} | {status} | t={times[index]:.2f}s",
                    font=font,
                    fill="white",
                )
                draw.text(
                    (14, 37),
                    "Scripted joints | Passive cloth | Recorded physics",
                    font=font,
                    fill=(173, 192, 203),
                )
                encoder.stdin.write(picture.tobytes())
                if index in (0, len(positions) // 2, len(positions) - 1):
                    picture.save(destination / f"frame-{index:04d}.png")
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Video encoding failed")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(destination / "video.mp4"),
         "-filter_complex", "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
         "-filter_complex_threads", "1", "-loop", "0", str(destination / "preview.gif")],
        check=True,
    )
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    provenance = {
        "inputs_sha256": {name: digest(destination / name) for name in
                          ("states.npz", "model.mjb", "summary.json", "trace.json", "plan-r.npz", "verification.json")},
        "renderer_sha256": digest(Path(__file__)),
        "display_engine": mujoco.__version__,
        "physics_steps_executed": 0,
        "frame_times_s": times.tolist(),
        "video_fps": 25,
        "gif_fps": 12,
        "camera": "close-up following measured cloth center and wrist anchor; display only",
        "render_and_encoding_seconds": time.perf_counter() - started,
        "video_sha256": digest(destination / "video.mp4"),
        "gif_sha256": digest(destination / "preview.gif"),
    }
    (destination / "media-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    metadata = json.loads((args.run / "summary.json").read_text())
    model = mujoco.MjModel.from_binary_path(str(args.run / "model.mjb"))
    with np.load(args.run / "states.npz") as recording:
        render(model, recording["qpos"], args.run, metadata["task"])
