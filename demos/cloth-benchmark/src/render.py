"""Studio playback of exact recorded cloth surfaces; no physics stepping."""

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from dexlab.cloth import ClothCase
from dexlab import cloth_display


LABELS = {
    "mujoco": "MuJoCo / flex",
    "superdex-shell": "SuperDex / shell",
    "newton-xpbd": "Newton / XPBD",
    "newton-vbd": "Newton / VBD",
    "newton-style3d": "Newton / Style3D",
    "newton-semi_implicit": "Newton / SemiImplicit",
    "newton-featherstone": "Newton / Featherstone",
    "physx-surface": "PhysX / surface",
}
WIDTH, HEIGHT, FPS = 480, 360, 25


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_record(directory):
    """Read sealed inputs without writing into the experiment directory."""
    directory = Path(directory)
    hashes = {name: sha256(directory / name) for name in
              ("trajectory.npz", "run.json", "summary.json")}
    metadata = json.loads((directory / "run.json").read_text())
    summary = json.loads((directory / "summary.json").read_text())
    if hashes["trajectory.npz"] != metadata["trajectory_sha256"]:
        raise ValueError("Trajectory does not match the recorded digest")
    with np.load(directory / "trajectory.npz", allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in
                  ("time", "positions", "rest_positions", "triangles")}
    times, positions, rest = (arrays[key] for key in
                              ("time", "positions", "rest_positions"))
    if (len(times) < 2 or positions.shape != (len(times), len(rest), 3)
            or not np.isfinite(positions).all() or not np.isfinite(times).all()
            or times[0] != 0 or np.any(np.diff(times) <= 0)
            or not np.isclose(times[-1], metadata["case"]["duration"], rtol=0, atol=1e-9)):
        raise ValueError("Expected a complete finite recording with increasing times")
    expected = np.arange(round(metadata["case"]["duration"] / metadata["dt_s"]) + 1) * metadata["dt_s"]
    if times.shape != expected.shape or not np.allclose(times, expected, rtol=0, atol=1e-9):
        raise ValueError("Expected the complete recorded physics time grid")
    return {"directory": directory, "metadata": metadata, "summary": summary,
            "hashes": hashes, **arrays}


def check_comparison(records):
    """Different solver materials are allowed; different experiments are not."""
    reference = records[0]
    solvers = [record["metadata"]["solver"] for record in records]
    if len(set(solvers)) != len(solvers):
        raise ValueError("Each comparison panel must have a distinct solver profile")
    for record in records[1:]:
        if record["metadata"]["case"] != reference["metadata"]["case"]:
            raise ValueError("Comparison requires identical case inputs")
        for key in ("rest_positions", "triangles"):
            if not np.array_equal(record[key], reference[key]):
                raise ValueError(f"Comparison requires identical {key}")
        if not np.allclose(record["positions"][0], reference["positions"][0], rtol=0, atol=1e-7):
            raise ValueError("Comparison requires matched recorded initial positions")
        if (record["time"].shape != reference["time"].shape
                or not np.allclose(record["time"], reference["time"], rtol=0, atol=1e-9)):
            raise ValueError("Comparison requires synchronized recorded timestamps")


def studio_model(record):
    """Only display assets change: geometry comes directly from the recording."""
    case = ClothCase(**record["metadata"]["case"])
    rest = record["rest_positions"]
    surface = " ".join(map(str, rest.ravel()))
    indices = " ".join(map(str, record["triangles"].ravel()))
    pins = " ".join(map(str, range(len(rest))))
    uv = (rest[:, :2] - rest[:, :2].min(axis=0)) / np.maximum(np.ptp(rest[:, :2], axis=0), 1e-12)
    texcoord = " ".join(map(str, uv.ravel()))
    # Sag/extension have no physical ground. Keep their display-only backdrop
    # below every recorded vertex; never clamp cloth to a staging surface.
    floor = (0 if case.experiment in ("drape", "folded-drop")
             else min(0, float(record["positions"][:, :, 2].min()) - .06))
    obstacle = ""
    if case.experiment == "drape":
        obstacle = (f'<geom type="sphere" size="{case.sphere_radius}" '
                    f'pos="0 0 {case.sphere_height}" material="ceramic"/>')
    elif case.experiment in ("sag", "extension"):
        # The short rail marks the recorded fixed edge. It is a display guide,
        # not a new physical clamp or a simulated support.
        obstacle = (f'<geom type="capsule" size=".003" '
                    f'fromto="{-case.length / 2} {-case.width / 2} {case.height} '
                    f'{-case.length / 2} {case.width / 2} {case.height}" '
                    'rgba=".18 .22 .27 1"/>')
    xml = f'''<mujoco>
      <visual>
        <global offwidth="{WIDTH}" offheight="{HEIGHT}"/>
        <quality shadowsize="2048" offsamples="4"/>
        <headlight ambient=".45 .45 .45" diffuse=".4 .4 .4" specular="0 0 0"/>
        <map znear=".005"/>
      </visual>
      <asset>
        <texture name="sky" type="skybox" builtin="gradient"
                 rgb1=".86 .89 .92" rgb2=".96 .97 .98" width="256" height="1536"/>
        <texture name="weave" type="2d" builtin="checker" width="512" height="512"
                 rgb1=".25 .49 .62" rgb2=".31 .55 .67"/>
        <material name="fabric" texture="weave" texrepeat="40 40"
                  specular=".05" shininess=".05" rgba="1 1 1 1"/>
        <material name="ceramic" rgba=".63 .65 .68 1" specular=".2" shininess=".2"/>
        <material name="floor" rgba=".72 .74 .76 1" specular="0" reflectance="0"/>
      </asset>
      <worldbody>
        <light pos=".7 -.5 1.2" dir="-.7 .5 -1" directional="true"
               diffuse=".6 .58 .55" specular=".1 .1 .1" castshadow="false"/>
        <light pos="-.5 .5 .7" dir=".5 -.5 -.7" directional="true"
               diffuse=".2 .23 .28" specular="0 0 0" castshadow="false"/>
        <geom type="plane" pos="0 0 {floor}" size="0 0 .01" material="floor"/>
        {obstacle}
        <flexcomp name="display" type="direct" dim="2" point="{surface}"
                  element="{indices}" texcoord="{texcoord}" material="fabric"
                  radius="{case.radius}" flatskin="false"><pin id="{pins}"/></flexcomp>
      </worldbody></mujoco>'''
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_fwdPosition(model, data)
    return model, data


def shared_camera(records):
    camera = mujoco.MjvCamera()
    camera.azimuth, camera.elevation = 15, -20
    points = np.concatenate([record["positions"].reshape(-1, 3) for record in records])
    camera.lookat[:], camera.distance = cloth_display.fixed_view(points, camera.azimuth, camera.elevation)
    return camera


def panel_caption(picture, record):
    draw = ImageDraw.Draw(picture)
    passed = record["summary"]["protocol_checks_passed"]
    draw.rectangle((0, 0, WIDTH, 51), fill=(244, 246, 248))
    solver = record["metadata"]["solver"]
    draw.text((14, 7), LABELS.get(solver, solver), font=ImageFont.load_default(size=19),
              fill=(28, 40, 51))
    status = "Protocol checks passed" if passed else "Protocol checks FAILED"
    draw.text((14, 29), status, font=ImageFont.load_default(size=14),
              fill=(30, 109, 77) if passed else (169, 51, 37))
    # A failed contact can disappear below an opaque floor. Keep the measured
    # maximum penetration visible; never move the cloth for the picture.
    maxima = record["summary"]["metrics"]["maximum"]
    penetration = max(maxima.get("ground_penetration_m", 0),
                      maxima.get("sphere_penetration_m", 0)) * 1000
    if record["metadata"]["case"]["experiment"] in ("drape", "folded-drop"):
        draw.text((14, HEIGHT - 22), f"Max penetration {penetration:.2f} mm",
                  font=ImageFont.load_default(size=14), fill=(37, 48, 58))


def render(directories, *, output=None):
    started = time.perf_counter()
    renderer_hash = sha256(__file__)
    camera_hash = sha256(cloth_display.__file__)
    if isinstance(directories, (str, Path)):
        directories = [Path(directories)]
    records = [load_record(path) for path in directories]
    if not 1 <= len(records) <= 8:
        raise ValueError("Provide one to eight native solver recordings")
    check_comparison(records)
    destination = Path(output) if output else Path(directories[0]).with_name(
        Path(directories[0]).name + "-studio")
    if any(destination.resolve().is_relative_to(record["directory"].resolve())
           for record in records):
        raise ValueError("Output must be outside the original recordings")
    destination.mkdir(parents=True, exist_ok=False)
    times = records[0]["time"]
    target_times = np.arange(0, times[-1] + 1e-9, 1 / FPS)
    selected = np.minimum(np.searchsorted(times, target_times - 1e-10), len(times) - 1)
    if selected[-1] != len(times) - 1:
        selected = np.r_[selected, len(times) - 1]
    camera = shared_camera(records)
    columns = 1 if len(records) == 1 else (2 if len(records) <= 4 else 4)
    rows = (len(records) + columns - 1) // columns
    width, height = WIDTH * columns, HEIGHT * rows + 64
    command = ["ffmpeg", "-n", "-loglevel", "error", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(FPS),
               "-i", "-", "-an", "-c:v", "libx264", "-threads", "1",
               "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               str(destination / "video.mp4")]
    option = mujoco.MjvOption()
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXEDGE] = False
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXVERT] = False
    option.flags[mujoco.mjtVisFlag.mjVIS_FLEXSKIN] = True
    with ExitStack() as stack:
        displays = []
        for record in records:
            model, data = studio_model(record)
            renderer = stack.enter_context(mujoco.Renderer(model, height=HEIGHT, width=WIDTH))
            displays.append((data, renderer))
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for number, index in enumerate(selected):
                canvas = Image.new("RGB", (width, height), (233, 237, 241))
                for panel, (record, (data, renderer)) in enumerate(zip(records, displays)):
                    data.flexvert_xpos[:] = record["positions"][index]
                    if not np.array_equal(data.flexvert_xpos, record["positions"][index]):
                        raise ValueError("Display vertices differ from recorded geometry")
                    renderer.update_scene(data, camera=camera, scene_option=option)
                    picture = Image.fromarray(renderer.render())
                    panel_caption(picture, record)
                    canvas.paste(picture, (WIDTH * (panel % columns), HEIGHT * (panel // columns)))
                draw = ImageDraw.Draw(canvas)
                experiment = records[0]["metadata"]["case"]["name"]
                draw.text((14, height - 55), f"{experiment}   |   {times[index]:.2f} / {times[-1]:.2f} s",
                          font=ImageFont.load_default(size=20), fill=(28, 40, 51))
                draw.text((14, height - 28), "Recorded motion | nominal materials | shared camera",
                          font=ImageFont.load_default(size=14), fill=(68, 80, 91))
                encoder.stdin.write(canvas.tobytes())
                if number in (0, len(selected) // 2, len(selected) - 1):
                    canvas.save(destination / f"frame-{number:03d}.png")
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Video encoding failed")
    preview_width = min(width, 1280)
    subprocess.run([
        "ffmpeg", "-n", "-loglevel", "error", "-i", str(destination / "video.mp4"),
        "-filter_complex",
        f"fps=15,scale={preview_width}:-2:flags=lanczos,split[a][b];"
        "[a]palettegen[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
        "-filter_complex_threads", "1", "-loop", "0", str(destination / "preview.gif"),
    ], check=True)
    for record in records:
        if any(sha256(record["directory"] / name) != digest for name, digest in record["hashes"].items()):
            raise ValueError("A sealed input changed during rendering")
    if sha256(__file__) != renderer_hash or sha256(cloth_display.__file__) != camera_hash:
        raise ValueError("Renderer source changed during playback")
    provenance = {
        "records": [{"solver": record["metadata"]["solver"],
                     "case": record["metadata"]["case"],
                     "recorded_engine": {
                         key: record["metadata"]["engine"].get(key)
                         for key in ("engine", "version", "packages", "solver", "integrator", "device",
                                     "precision", "iterations", "tolerance", "material")
                     },
                     "dt_s": record["metadata"]["dt_s"],
                     "inputs_sha256": record["hashes"],
                     "protocol_checks_passed": record["summary"]["protocol_checks_passed"],
                     "frame_times_s": record["time"][selected].tolist()} for record in records],
        "renderer_sha256": renderer_hash, "render_engine": mujoco.__version__,
        "camera_helper_sha256": camera_hash,
        "display_only": True, "physics_steps_executed": 0,
        "geometry": "Exact recorded vertices and triangles; smooth lighting normals only",
        "backdrop": "Display-only; ground at z=0 only for drape/folded-drop; rail marks the fixed edge",
        "camera": {"lookat": camera.lookat.tolist(), "distance": camera.distance,
                   "azimuth": camera.azimuth, "elevation": camera.elevation},
        "frame_indices": selected.tolist(), "frame_times_s": times[selected].tolist(),
        "video_fps": FPS, "gif_fps": 15,
        "render_and_encoding_seconds": time.perf_counter() - started,
        "video_sha256": sha256(destination / "video.mp4"),
        "gif_sha256": sha256(destination / "preview.gif"),
    }
    (destination / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="New directory outside all recordings")
    args = parser.parse_args()
    render(args.directories, output=args.output)
