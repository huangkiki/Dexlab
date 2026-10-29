#!/usr/bin/env python3
"""Render a saved RSS wiping trajectory with matched tiled and RTX cameras."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import dataclasses
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


CHANNELS = ("body_q", "joint_q", "particles", "stripe_ink")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def frame_steps(control_hz: float, fps: float, start: float, end: float) -> np.ndarray:
    """Require exact recorded steps; never interpolate or invent a final frame."""
    values = (control_hz, fps, start, end)
    if not all(np.isfinite(values)) or not 0 < fps <= control_hz or not 0 <= start < end:
        raise ValueError("Require finite rates and 0 <= start < end")
    stride = control_hz / fps
    first, stop = start * control_hz, end * control_hz
    if any(abs(value - round(value)) > 1e-7 for value in (stride, first, stop)):
        raise ValueError("Frame rate and interval must align with recorded control steps")
    if (round(stop) - round(first)) % round(stride):
        raise ValueError("Duration must contain a whole number of output frames")
    return np.arange(round(first), round(stop), round(stride), dtype=np.int64)


def read_frames(record: Path, steps: np.ndarray, inputs: dict[str, str]):
    """Stream chunks, rejecting missing/duplicate steps and malformed channels."""
    wanted = set(steps.tolist())
    previous = -1
    found = 0
    shapes = None
    for path in sorted((record / "states").glob("*.npz")):
        inputs[str(path.relative_to(record))] = sha256(path)
        with np.load(path, allow_pickle=False) as chunk:
            recorded = chunk["step"]
            if recorded.ndim != 1 or recorded.dtype.kind not in "iu" or not len(recorded):
                raise ValueError("Invalid recorded step array")
            expected = np.arange(previous + 1, previous + 1 + len(recorded))
            if not np.array_equal(recorded, expected):
                raise ValueError("Missing or duplicate recorded steps")
            arrays = {name: chunk[name] for name in CHANNELS}
            current_shapes = {name: array.shape[1:] for name, array in arrays.items()}
            if shapes is not None and current_shapes != shapes:
                raise ValueError("State dimensions changed between chunks")
            shapes = current_shapes
            for name, array in arrays.items():
                if len(array) != len(recorded) or not np.isfinite(array).all():
                    raise ValueError(f"Invalid state channel: {name}")
            for index, step in enumerate(recorded):
                if int(step) in wanted:
                    found += 1
                    yield int(step), {name: array[index].copy() for name, array in arrays.items()}
            previous = int(recorded[-1])
            if previous >= steps[-1]:
                break
    if found != len(steps):
        raise ValueError(f"Truncated record: requested {len(steps)} frames, found {found}")


def check_state_shapes(frame, *, bodies: int, joints: int, particles: int, ink: int):
    expected = {
        "body_q": (bodies, 7), "joint_q": (joints,),
        "particles": (particles, 3), "stripe_ink": (ink,),
    }
    for name, shape in expected.items():
        if frame[name].shape != shape or not np.isfinite(frame[name]).all():
            raise ValueError(f"{name} does not match the rebuilt scene: expected {shape}")
    if np.any((frame["stripe_ink"] < 0) | (frame["stripe_ink"] > 1)):
        raise ValueError("Ink must remain within [0, 1]")


def readback(sim, stripe, particle_indices):
    return {
        "body_q": sim.state.body_q.numpy(),
        "joint_q": sim.state.joint_q.numpy(),
        "particles": sim.state.particle_q.numpy()[particle_indices],
        "stripe_ink": stripe.ink.copy(),
        "shape_color": sim.model.shape_color.numpy(),
    }


def assert_unchanged(expected, actual):
    for name, before in expected.items():
        if not np.array_equal(before, actual[name]):
            raise ValueError(f"Rendering changed loaded state: {name}")


def restore_visibility(current, recorded, visible_bit):
    """Restore the Studio's saved display toggles, rejecting collision-bit changes."""
    if current.shape != recorded.shape or not np.array_equal(
        current & ~visible_bit, recorded & ~visible_bit
    ):
        raise ValueError("Recorded collision flags differ from the rebuilt scene")
    return recorded.copy()


def execute(args):
    import imageio.v2 as imageio
    import robosimstudio as rss
    import newton
    from geometry import frozen_colliders
    from run import EXAMPLE, RSS_COMMIT, load_demo, save_compiled_model, write_json

    source = args.source.resolve()
    record = args.record.resolve()
    manifest = json.loads((record / "manifest.json").read_text())
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain",
                                     "--untracked-files=no"], text=True).strip()
    if commit != RSS_COMMIT or manifest["rss_commit"] != RSS_COMMIT or dirty:
        raise ValueError("Replay requires the unchanged pinned RSS checkout")
    if not Path(rss.__file__).resolve().is_relative_to(source):
        raise ValueError("Imported RoboSimStudio differs from --source")
    steps = frame_steps(manifest["control_hz"], args.fps, args.start, args.end)
    inputs = {name: sha256(record / name) for name in
              ("manifest.json", "compiled-model.npz", "observations.jsonl")}
    observations = {}
    for line in (record / "observations.jsonl").read_text().splitlines():
        row = json.loads(line)
        step = row["step"]
        if step in observations:
            raise ValueError("Duplicate observation step")
        observations[step] = row["sim_time_s"]
    for step in steps:
        timestamp = observations.get(int(step), float("nan"))
        if not np.isfinite(timestamp) or abs(timestamp - step / manifest["control_hz"]) > 1e-6:
            raise ValueError(f"Missing or inconsistent observation timestamp at step {step}")

    args.output.mkdir(parents=True, exist_ok=False)
    demo = load_demo(source / EXAMPLE)
    started = time.perf_counter()
    with frozen_colliders(args.geometry_cache, False) as geometry:
        sim = demo.bar.scene().build(control_mode="joint_position")
    with ExitStack() as stack:
        stack.callback(sim.close)
        if geometry != manifest["frozen_collision_geometry"]:
            raise ValueError("Collision preprocessing differs from the recorded cohort")
        current_flags = sim.model.shape_flags.numpy()
        with np.load(record / "compiled-model.npz", allow_pickle=False) as saved:
            flags = restore_visibility(current_flags, saved["shape_flags"], int(newton.ShapeFlags.VISIBLE))
        sim.model.shape_flags.assign(flags)
        compiled = save_compiled_model(sim, args.output)
        if compiled["sha256"] != manifest["compiled_model"]["sha256"]:
            raise ValueError("Rebuilt compiled model differs from the recorded model")
        with np.load(record / "compiled-model.npz", allow_pickle=False) as saved, \
                np.load(args.output / "compiled-model.npz", allow_pickle=False) as rebuilt:
            if set(saved.files) != set(rebuilt.files):
                raise ValueError("Recorded model arrays differ from the rebuilt scene")
            assert_unchanged(dict(saved), dict(rebuilt))
        camera = rss.CameraSpec(**manifest["camera"])
        sponge = sim["sponge"]
        particle_indices = np.asarray(sponge.particles)
        if len(particle_indices) != sim.model.particle_count:
            raise ValueError("Record does not describe every particle in this scene")
        stripe = sim["stripe"].entity
        renderers = {}
        for backend in ("tiled", "rtx"):
            kwargs = {"quality": "final", "accumulate": args.passes} if backend == "rtx" else {}
            renderer = sim.make_renderer(backend, cameras=[camera], channels=["rgb"], **kwargs)
            stack.callback(renderer.close)
            # Establish UVs from the canonical scene, before writing recorded deformation.
            renderer.render(sim.state)
            renderers[backend] = renderer
        setup_s = time.perf_counter() - started
        writers = {
            name: stack.enter_context(imageio.get_writer(
                args.output / f"{name}.mp4", fps=args.fps, codec="libx264",
                quality=8, macro_block_size=1, ffmpeg_params=["-threads", "2"],
            ))
            for name in ("tiled", "rtx", "comparison")
        }
        timings = {backend: [] for backend in renderers}
        frame_map = []
        max_load_error = {name: 0.0 for name in CHANNELS}
        for output_frame, (step, frame) in enumerate(read_frames(record, steps, inputs)):
            check_state_shapes(frame, bodies=sim.model.body_count, joints=sim.model.joint_coord_count,
                               particles=len(particle_indices), ink=len(stripe.ink))
            sim.state.body_q.assign(frame["body_q"])
            sim.state.joint_q.assign(frame["joint_q"])
            particles = sim.state.particle_q.numpy()
            particles[particle_indices] = frame["particles"]
            sim.state.particle_q.assign(particles)
            stripe.ink[:] = frame["stripe_ink"]
            stripe.paint()
            loaded = readback(sim, stripe, particle_indices)
            for name in CHANNELS:
                max_load_error[name] = max(
                    max_load_error[name],
                    float(np.max(np.abs(loaded[name].astype(np.float64) - frame[name]))),
                )
                if not np.array_equal(loaded[name], frame[name].astype(loaded[name].dtype)):
                    raise ValueError(f"Recorded state was not loaded exactly: {name}")
            images = {}
            for backend, renderer in renderers.items():
                began = time.perf_counter()
                image = np.asarray(renderer.render(sim.state)[camera.name]["rgb"])
                timings[backend].append(time.perf_counter() - began)
                if image.dtype != np.uint8 or image.shape != (camera.height, camera.width, 3):
                    raise ValueError(f"Unexpected {backend} RGB output")
                images[backend] = image.copy()
                writers[backend].append_data(image)
            assert_unchanged(loaded, readback(sim, stripe, particle_indices))
            if sim.step_count != 0:
                raise ValueError("Offline replay unexpectedly advanced physics")
            comparison = np.concatenate([images["tiled"], images["rtx"]], axis=1)
            writers["comparison"].append_data(comparison)
            if output_frame == 0 or output_frame == len(steps) // 2:
                suffix = "first" if output_frame == 0 else "middle"
                for backend, image in images.items():
                    imageio.imwrite(args.output / f"{backend}-{suffix}.png", image)
                imageio.imwrite(args.output / f"comparison-{suffix}.png", comparison)
            frame_map.append({"frame": output_frame, "step": step, "sim_time_s": observations[step]})
            if output_frame % 10 == 0:
                print(f"[replay] frame={output_frame} simulation={observations[step]:.3f}s", flush=True)
        for name, expected in inputs.items():
            if sha256(record / name) != expected:
                raise ValueError(f"Input changed during rendering: {name}")
        report = {
            "schema_version": 1, "source_commit": commit, "record_mode": manifest["mode"],
            "input_sha256": inputs, "compiled_model_sha256": compiled["sha256"],
            "restored_display_flag_indices": np.flatnonzero(current_flags != flags).tolist(),
            "renderer_script_sha256": sha256(Path(__file__)),
            "camera": dataclasses.asdict(camera), "fps": args.fps, "rtx_passes": args.passes,
            "render_spec": dataclasses.asdict(sim.look),
            "frames": frame_map, "physics_steps_executed": sim.step_count,
            "loaded_state_max_absolute_error": max_load_error,
            "render_state_unchanged": True, "input_files_unchanged": True,
            "setup_and_warmup_wall_s": setup_s,
            "render_wall_s": {name: {"total": sum(costs), "mean": float(np.mean(costs)),
                                    "p95": float(np.percentile(costs, 95))}
                              for name, costs in timings.items()},
            "packages": {name: importlib.metadata.version(name)
                         for name in ("ovrtx", "newton", "warp-lang", "imageio")},
            "scope": "Recorded state replay. Left: tiled collision view. Right: RTX with upstream "
                     "materials and room. No physics stepping, interpolation or rescoring. "
                     "Frame rate is playback rate; costs are this render job, not a simulator benchmark.",
        }
    report["outputs_sha256"] = {
        path.name: sha256(path) for path in sorted(args.output.iterdir())
        if path.suffix in (".png", ".mp4")
    }
    write_json(args.output / "render.json", report)
    print(json.dumps({"frames": len(frame_map), "render_wall_s": report["render_wall_s"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--geometry-cache", type=Path, default=Path(__file__).with_name("geometry-cache"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start", type=float, default=10)
    parser.add_argument("--end", type=float, default=20)
    parser.add_argument("--fps", type=float, default=10)
    parser.add_argument("--passes", type=int, default=12)
    args = parser.parse_args()
    if args.passes < 1:
        parser.error("--passes must be positive")
    execute(args)


if __name__ == "__main__":
    main()
