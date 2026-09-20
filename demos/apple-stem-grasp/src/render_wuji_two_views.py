"""Two fixed simultaneous views of an unmodified native physics trajectory."""

import argparse
import subprocess
from pathlib import Path

import mujoco
import numpy as np
from grasp_display import set_frame
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--snapshot", type=float)
    args = parser.parse_args()
    trace = np.load(args.input / "trajectory.npz")
    model = mujoco.MjModel.from_xml_path(str(args.input / "display.xml"))
    data = mujoco.MjData(model)
    side = mujoco.MjvCamera()
    side.lookat[:] = [0.06, 0.17, 0.48]
    side.distance, side.azimuth, side.elevation = 1.7, 135, -12
    detail = mujoco.MjvCamera()
    detail.lookat[:] = [0.295, 0.405, 0.4645]
    detail.distance, detail.azimuth, detail.elevation = 0.50, 0, -10
    dt = float(trace["dt"])
    with mujoco.Renderer(model, height=720, width=960) as renderer:

        def render(frame):
            set_frame(model, data, frame)
            panels = []
            for camera in (side, detail):
                renderer.update_scene(data, camera=camera)
                panels.append(renderer.render().copy())
            return np.concatenate(panels, axis=1)

        if args.snapshot is not None:
            index = min(round(args.snapshot / dt), len(trace["frames"]) - 1)
            path = args.input / f"two-views-{args.snapshot:g}s.png"
            Image.fromarray(render(trace["frames"][index])).save(path)
        else:
            path = args.input / "two-views.mp4"
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
                "1920x720",
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
                str(path),
            ]
            with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
                for frame in trace["frames"]:
                    encoder.stdin.write(render(frame).tobytes())
                encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError("Video encoding failed")
        print(path)


if __name__ == "__main__":
    main()
