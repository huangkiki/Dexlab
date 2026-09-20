"""Render a continuous, single-view close-up of either SDF grasp recording.

The close-up camera follows the recorded apple only for presentation. Every
robot and object pose comes from the original trace; no physics is simulated.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from grasp_display import set_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="Run containing display.xml and trajectory.npz"
    )
    parser.add_argument(
        "--output", type=Path, help="Output directory; defaults to the run"
    )
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float, default=14.0, help="Exclusive end time")
    parser.add_argument("--poster-time", type=float, default=12.0)
    parser.add_argument("--poster-only", action="store_true")
    args = parser.parse_args()

    trace_path = args.input / "trajectory.npz"
    with np.load(trace_path, allow_pickle=False) as trace:
        frames = trace["frames"]
        names = trace["names"].tolist()
        dt = float(trace["dt"])
    first, last = round(args.start / dt), round(args.end / dt)
    poster = round(args.poster_time / dt)
    if not 0 <= first < last <= len(frames) or not 0 <= poster < len(frames):
        parser.error("Requested times must fall inside the recording")
    apple_index = names.index("apple")
    model = mujoco.MjModel.from_xml_path(str(args.input / "display.xml"))
    if model.nmocap != len(names):
        raise ValueError("Display model and recording have different actor counts")
    data = mujoco.MjData(model)
    output = args.output or args.input
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=16)
    engine = json.loads((args.input / "engine.json").read_text())
    backend = engine["backend"]
    label = "MuJoCo 3.11.0" if backend == "mujoco" else "SuperDex FP64"
    basename = backend + "-sdf"

    detail = mujoco.MjvCamera()
    detail.distance, detail.azimuth, detail.elevation = 0.24, 315, -8
    width, height, footer = 720, 540, 40

    with mujoco.Renderer(model, height=height, width=width) as close_renderer:

        def render(index):
            frame = frames[index]
            set_frame(model, data, frame)
            detail.lookat[:] = frame[apple_index, :3] + [0, 0, 0.035]
            close_renderer.update_scene(data, camera=detail)
            canvas = Image.new("RGB", (width, height + footer), "#14202d")
            canvas.paste(Image.fromarray(close_renderer.render().copy()), (0, 0))
            draw = ImageDraw.Draw(canvas)
            draw.text(
                (14, height + 10),
                f"{label} | OpenArm + Wuji | Stem pinch | t = {index * dt:.2f} s",
                fill="white",
                font=font,
            )
            return canvas

        poster_path = output / (basename + ".png")
        render(poster).save(poster_path)
        if not args.poster_only:
            video_path = output / (basename + ".mp4")
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
                f"{width}x{height + footer}",
                "-r",
                str(1 / dt),
                "-i",
                "-",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(video_path),
            ]
            with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
                for index in range(first, last):
                    encoder.stdin.write(render(index).tobytes())
                encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError("Video encoding failed")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(video_path),
                    "-filter_complex",
                    "fps=10,scale=640:-1:flags=lanczos,split[a][b];"
                    "[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
                    "-loop",
                    "0",
                    str(output / (basename + ".gif")),
                ],
                check=True,
            )
    metadata = {
        "source": label + " apple-stem-grasp recording",
        "task_runtime": json.loads((args.input / "unilab.json").read_text())
        if (args.input / "unilab.json").exists()
        else None,
        "trajectory_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        "recorded_frame_interval_s": dt,
        "poster_frame": poster,
        "poster_time_s": poster * dt,
        "video_first_frame": None if args.poster_only else first,
        "video_last_frame_inclusive": None if args.poster_only else last - 1,
        "video_time_range_s": None if args.poster_only else [first * dt, last * dt],
        "rendering": "Official MuJoCo; recorded poses only; no dynamics",
        "cameras": "Single close-up follows the recorded apple for presentation; not controller input",
        "overlays": "Identifying footer only; no fingertip markers",
    }
    (output / (basename + ".json")).write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"output": str(output.resolve()), **metadata}, indent=2))


if __name__ == "__main__":
    main()
