#!/usr/bin/env python3
"""Render saved native states only: mj_forward for geometry, never mj_step."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def render(raw, output, label, libero_root=None):
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    if mujoco.__version__ != "2.3.7":
        raise ValueError("Replay uses the same pinned core as the recorded model")
    receipt = json.loads((raw / "run.json").read_text())
    with np.load(raw / "trajectory.npz", allow_pickle=False) as data:
        states = np.vstack((data["initial"], data["state"]))
    if libero_root is None:
        model = mujoco.MjModel.from_xml_path(str(raw / "effective-model.xml"))
    else:
        import robosuite

        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from dexlab.libero_workflow import relocate_assets

        xml, _ = relocate_assets(
            (raw / "effective-model.xml").read_text(),
            libero_root,
            Path(robosuite.__file__).parent,
        )
        model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=480, width=640)
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.0, 0.0, 0.13]
    camera.distance, camera.azimuth, camera.elevation = 1.35, 135, -45
    option = mujoco.MjvOption()
    option.geomgroup[0] = 0  # robosuite collision meshes; preserve visual group 1
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "640x480",
        "-r",
        "20",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "22",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    frames = []
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        try:
            for index, state in enumerate(states):
                data.time = state[0]
                data.qpos[:] = state[1 : 1 + model.nq]
                data.qvel[:] = state[1 + model.nq : 1 + model.nq + model.nv]
                mujoco.mj_forward(model, data)
                renderer.update_scene(data, camera=camera, scene_option=option)
                image = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(image)
                draw.rectangle((0, 0, 640, 42), fill="#122438")
                draw.text(
                    (12, 7),
                    f'{label} | {receipt["demo"]} | native time {state[0]:.3f} s',
                    fill="white",
                    font=font,
                )
                draw.text(
                    (12, 24),
                    "Recorded states / 20 fps / identical fixed camera / real scale",
                    fill="white",
                    font=font,
                )
                if index == len(states) // 2:
                    image.save(output.with_suffix(".png"))
                encoder.stdin.write(np.asarray(image).tobytes())
                frames.append(
                    dict(
                        frame=index,
                        time_s=index / 20.0,
                        native_time_s=float(state[0]),
                        state_index=index,
                    )
                )
        finally:
            encoder.stdin.close()
            renderer._mjr_context.free()
            renderer._gl_context.free()
        if encoder.wait() != 0:
            raise RuntimeError("Video encoding failed")
    output.with_suffix(".frames.json").write_text(
        json.dumps(frames, separators=(",", ":")) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--libero-root", type=Path, help="Resolve portable archive asset paths"
    )
    args = parser.parse_args()
    render(args.raw, args.output, args.label, args.libero_root)
