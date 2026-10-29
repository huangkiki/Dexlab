#!/usr/bin/env python3
"""Record the pinned RSS wiping example, with an explicit no-pinning ablation."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import dataclasses
import difflib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

RSS_COMMIT = "23417de77edf59d614531a833334ed4e2206fc2c"
EXAMPLE = Path("examples/08_demos/wipe_the_bar")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("The frozen upstream source no longer matches the ablation")
    return text.replace(old, new, 1)


def prepare_example(source: Path, output: Path, mode: str) -> Path:
    """Keep upstream untouched and save the complete reviewable ablation patch."""
    original = source / EXAMPLE
    if mode == "original":
        return original
    copied = output / "ablation-source"
    copied.mkdir()
    bar = (original / "bar.py").read_text()
    bar = replace_once(
        bar, "        self.pin: int | None = None",
        "        self.grasp_ready = False\n        self.pin: int | None = None",
    )
    bar = replace_once(
        bar, "        if gripper.command < 0.5:\n",
        "        if gripper.command < 0.5:\n            self.grasp_ready = False\n",
    )
    bar = replace_once(
        bar,
        "        if self.pin is not None:\n"
        "            return  # riding the hand: the bridge re-aims it every engine substep",
        "        if self.grasp_ready:\n"
        "            return  # retain the selected material patch, without constraining it",
    )
    first = bar.index('        self.pin = self.bridge.pin_nodes(')
    last = bar.index('\n\n\ndef latch(sim)', first)
    bar = bar[:first] + (
        "        self.grasp_ready = True\n"
        '        self.events.append((sim.step_count, "grasp_ready_without_pin", '
        'dict(self.readings, nodes=int(len(self.nodes)))))\n'
    ) + bar[last:]
    routine = (original / "routine.py").read_text()
    if routine.count("self.latch.latched") != 2:
        raise ValueError("Unexpected upstream routine readiness checks")
    routine = routine.replace("self.latch.latched", "self.latch.grasp_ready")
    routine = replace_once(
        routine, "latched {len(self.latch.nodes)} nodes",
        "tracked {len(self.latch.nodes)} material nodes; no pins",
    )
    changed = {
        "bar.py": bar, "routine.py": routine,
        "wipe_the_bar.py": (original / "wipe_the_bar.py").read_text(),
    }
    patch = []
    for name, text in changed.items():
        (copied / name).write_text(text)
        patch.extend(difflib.unified_diff(
            (original / name).read_text().splitlines(True), text.splitlines(True),
            fromfile=f"upstream/{name}", tofile=f"no-latch/{name}",
        ))
    (output / "no-latch.patch").write_text("".join(patch))
    return copied


def load_demo(folder):
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location("rss_wiping_demo", folder / "wipe_the_bar.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def save_compiled_model(sim, output):
    """Fingerprint generated collision geometry, not only the source meshes."""
    import numpy as np

    arrays = {}
    model = sim.model
    for name in (
        "shape_transform", "shape_body", "shape_flags", "shape_type", "shape_scale",
        "shape_material_mu", "shape_material_ke", "shape_material_kd",
        "body_mass", "body_inertia",
    ):
        value = getattr(model, name)
        arrays[name] = value.numpy()
    meshes = []
    for index, mesh in enumerate(model.shape_source):
        if mesh is None:
            continue
        vertices = np.asarray(mesh.vertices)
        indices = np.asarray(mesh.indices)
        arrays[f"mesh_{index}_vertices"] = vertices
        arrays[f"mesh_{index}_indices"] = indices
        meshes.append({
            "shape": index, "vertices": len(vertices), "indices": indices.size,
            "sha256": hashlib.sha256(vertices.tobytes() + indices.tobytes()).hexdigest(),
        })
    np.savez(output / "compiled-model.npz", **arrays)
    digest = hashlib.sha256()
    for name, value in sorted(arrays.items()):
        digest.update(name.encode())
        digest.update(str((value.shape, value.dtype.str)).encode())
        digest.update(value.tobytes())
    return {"sha256": digest.hexdigest(), "meshes": meshes}


def execute(args):
    import imageio.v2 as imageio
    import numpy as np
    import robosimstudio as rss
    from robosimstudio.core.math import quat_to_mat
    from tests.fixtures.examples import _stub_studio
    from tests.fixtures.grasp import open_session, tick
    from superdex.physics import uses_double_precision
    from geometry import frozen_colliders

    start = time.perf_counter()
    demo = load_demo(prepare_example(args.source, args.output, args.mode))
    geometry = (frozen_colliders(args.geometry_cache, args.capture_geometry)
                if args.geometry_cache else nullcontext(None))
    with geometry as geometry_entries, _stub_studio() as opened:
        demo.main()
    if len(opened) != 1:
        raise RuntimeError(f"Expected one upstream scene, received {len(opened)}")
    sim, kwargs = opened[0]
    session = open_session(sim, args.port, kwargs.get("page"))
    latch = demo.bar.latch(sim)
    sponge = sim["sponge"]
    stripe = sim["stripe"].entity
    grip = sim.gripper("right")
    original_factory = kwargs["routines"]["Wipe the bar"]
    active = {}

    def recorded_routine(sim, session):
        # This is exactly the upstream factory: Take(sim, session).steps().
        take = demo.routine.Take(sim, session)
        active["take"] = take
        return take.steps()

    session.add_routines({"Wipe the bar": recorded_routine})
    panel = session.panels[-1]
    camera = rss.CameraSpec(
        name="view", width=960, height=544, fov_y=45,
        eye=demo.bar.EYE, look_at=demo.bar.LOOK, up=(0, 0, 1), near=0.01, far=8.0,
    )
    hz = float(sim.request.physics.control_hz)
    stride = round(hz / args.fps)
    if stride < 1 or abs(hz / stride - args.fps) > 1e-8:
        raise ValueError("Video rate must divide the control rate")
    initial = np.asarray(sponge.particle_q, dtype=np.float64).copy()
    homes = {arm: np.asarray(session.arms[arm].ik.home_pose[0]).copy()
             for arm in ("right", "left")}
    np.save(args.output / "initial-particles.npy", initial)
    manifest = {
        "schema_version": 2, "mode": args.mode, "rss_commit": RSS_COMMIT,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "geometry_helper_sha256": hashlib.sha256(Path(__file__).with_name("geometry.py").read_bytes()).hexdigest(),
        "frozen_collision_geometry": geometry_entries,
        "example_sha256": {
            name: hashlib.sha256((args.source / EXAMPLE / name).read_bytes()).hexdigest()
            for name in ("bar.py", "routine.py", "wipe_the_bar.py")
        },
        "tracked_asset_tree": subprocess.check_output(
            ["git", "-C", str(args.source), "rev-parse", "HEAD:assets"], text=True,
        ).strip(),
        "camera": dataclasses.asdict(camera), "video_fps": args.fps,
        "renderer": sim.platform.renderer_for("")[0],
        "superdex_double_precision": bool(uses_double_precision()),
        "compiled_model": save_compiled_model(sim, args.output),
        "arm_home_positions_m": {name: pose.tolist() for name, pose in homes.items()},
        "stripe_cleared_below": float(stripe.spec.cleared_below),
        "authored_material": dataclasses.asdict(demo.bar.FOAM),
        "authored_layout": dataclasses.asdict(demo.bar.LAYOUT),
        "control_hz": hz, "physics": dataclasses.asdict(sim.request.physics),
        "routine_factory": str(original_factory),
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "force_semantics": "Native bridge.contact_points records after each control step; "
                           "not actuator commands, not an independently validated control-step mean.",
        "slip_semantics": "Fixed material patch in the measured right-hand frame; "
                          "Euclidean centroid displacement and maximum node displacement "
                          "are distinct. Sponge centroid displacement is reported separately.",
        "interpretation": "Upstream simulation reproduction; no real-material or sim-to-real claim.",
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
    }
    write_json(args.output / "manifest.json", manifest)
    states = args.output / "states"
    states.mkdir()
    buffers = {"step": [], "particles": [], "body_q": [], "joint_q": [], "stripe_ink": []}
    chunk = 0
    ready_step = None
    patch_reference = centroid_reference = None
    rows = []
    frame_times = []
    step_wall = render_wall = record_wall = 0.0
    writer = None
    error = None
    samples = (args.output / "observations.jsonl").open("x")
    contact_log = (args.output / "contacts.jsonl").open("x")
    built_wall = time.perf_counter() - start

    def flush_states():
        nonlocal chunk
        if not buffers["step"]:
            return
        np.savez(states / f"{chunk:04d}.npz", **{k: np.asarray(v) for k, v in buffers.items()})
        for values in buffers.values():
            values.clear()
        chunk += 1

    def observe():
        nonlocal ready_step, patch_reference, centroid_reference, record_wall, render_wall, writer
        began = time.perf_counter()
        step = int(sim.step_count)
        pos, quat = session.arms["right"].ik.ee_pose(sim.state)
        pos, quat = np.asarray(pos), np.asarray(quat)
        rotation = quat_to_mat(quat)
        particles = np.asarray(sponge.particle_q, dtype=np.float64).copy()
        local = (particles - pos) @ rotation
        sides = []
        raw_contacts = []
        gaps = []
        for side in latch.sides:
            force = 0.0
            for body in side:
                contacts = latch.bridge.contact_points("sponge", against=body)
                force += float(np.sum(contacts["force"] * contacts["normal"]))
                raw_contacts.append({
                    "body": body,
                    **{key: np.asarray(contacts[key]).tolist()
                       for key in ("pos", "force", "normal", "area", "gap")},
                })
                gaps.extend(np.asarray(contacts["gap"]).tolist())
            sides.append(force)
        bar_contacts = latch.bridge.contact_points("sponge", against=stripe.bar_body)
        ready = bool(latch.events)
        if ready and ready_step is None:
            if len(latch.nodes) == 0:
                raise RuntimeError("Grasp readiness did not identify a material patch")
            ready_step = step
            patch_reference = local[latch.nodes].copy()
            centroid_reference = local.mean(axis=0).copy()
            np.save(args.output / "tracked-patch.npy", latch.nodes)
        displacement = None if patch_reference is None else local[latch.nodes] - patch_reference
        pins = len(latch.bridge._pins)  # actual bridge constraints, independent of routine readiness
        row = {
            "step": step, "sim_time_s": float(sim.sim_time),
            "phase": active["take"].phase if "take" in active else "settle",
            "hand_position_m": pos.tolist(), "hand_quaternion_xyzw": quat.tolist(),
            "arm_positions_m": {
                arm: np.asarray(session.arms[arm].ik.ee_pose(sim.state)[0]).tolist()
                for arm in homes
            },
            "jaw_width_m": float(grip.width(sim.state)), "grip_command": float(grip.command),
            "sponge_centroid_m": particles.mean(axis=0).tolist(),
            "pad_normal_forces_n": sides, "bar_force_n": float(stripe.press),
            "bar_peak_pressure_pa": float(stripe.peak), "cleaned_fraction": float(stripe.cleaned),
            "active_pins": pins,
            "pad_min_contact_gap_m": min(gaps) if gaps else None,
            "patch_centroid_slip_m": None if displacement is None else float(np.linalg.norm(displacement.mean(axis=0))),
            "patch_max_node_displacement_m": None if displacement is None else float(np.linalg.norm(displacement, axis=1).max()),
            "centroid_relative_displacement_m": None if centroid_reference is None else float(np.linalg.norm(local.mean(axis=0) - centroid_reference)),
        }
        rows.append(row)
        samples.write(json.dumps(row, allow_nan=False) + "\n")
        contact_log.write(json.dumps({
            "step": step, "pads": raw_contacts,
            "bar": {key: np.asarray(bar_contacts[key]).tolist()
                    for key in ("pos", "force", "normal", "area", "gap")},
        }, allow_nan=False) + "\n")
        for key, value in (
            ("step", step), ("particles", particles), ("body_q", sim.state.body_q.numpy()),
            ("joint_q", sim.state.joint_q.numpy()), ("stripe_ink", stripe.ink),
        ):
            buffers[key].append(value.copy() if hasattr(value, "copy") else value)
        if len(buffers["step"]) >= 60:
            flush_states()
            samples.flush()
            contact_log.flush()
        record_wall += time.perf_counter() - began
        if args.mode == "no-latch" and pins:
            raise RuntimeError("No-latch ablation created an active pin")
        if args.video and step % stride == 0:
            began = time.perf_counter()
            rgb = sim.render(camera)["rgb"]
            if writer is None:
                writer = imageio.get_writer(args.output / "video.mp4", fps=args.fps, codec="libx264", quality=8)
                imageio.imwrite(args.output / "first-frame.png", rgb)
            writer.append_data(rgb)
            frame_times.append(float(sim.sim_time))
            render_wall += time.perf_counter() - began
        if step % 60 == 0:
            print(f"[record] {row['sim_time_s']:.1f}s {row['phase']} "
                  f"cleaned={row['cleaned_fraction']:.3f} "
                  f"pins={pins} slip={row['patch_centroid_slip_m']}", flush=True)

    try:
        observe()
        for _ in range(20):
            began = time.perf_counter()
            tick(session, 1)
            step_wall += time.perf_counter() - began
            observe()
        # Match the unchanged native test's return reference after settling.
        initial = np.asarray(sponge.particle_q, dtype=np.float64).copy()
        np.save(args.output / "settled-particles.npy", initial)
        panel.requested = "Wipe the bar"
        for iteration in range(round(args.max_seconds * hz) - 20):
            began = time.perf_counter()
            tick(session, 1)
            step_wall += time.perf_counter() - began
            observe()
            if iteration > 0 and panel.gen is None:
                break
        else:
            error = "simulation_time_limit"
    except BaseException:
        error = traceback.format_exc()
        print(error, file=sys.stderr, flush=True)
    finally:
        flush_states()
        samples.close()
        contact_log.close()
        if writer is not None:
            writer.close()
        np.save(args.output / "video-times.npy", np.asarray(frame_times))
        final_particles = np.asarray(sponge.particle_q, dtype=np.float64)
        held = [r for r in rows if r["patch_centroid_slip_m"] is not None and r["grip_command"] >= 0.5]
        take = active.get("take")
        home_errors = {
            arm: float(np.linalg.norm(session.arms[arm].ik.ee_pose(sim.state)[0] - homes[arm]))
            for arm in homes
        }
        summary = {
            "mode": args.mode, "error": error, "phase": take.phase if take else None,
            "status_text": panel._status.value if panel._status else "",
            "routine_log": take.log if take else [],
            "sim_time_s": float(sim.sim_time), "recorded_steps": len(rows),
            "video_frames": len(frame_times), "ready_step": ready_step,
            "events": [(int(s), name, values) for s, name, values in latch.events],
            "final_cleaned_fraction": float(stripe.cleaned),
            "peak_bar_force_n": max(r["bar_force_n"] for r in rows),
            "peak_pressure_pa": max(r["bar_peak_pressure_pa"] for r in rows),
            "max_hold_patch_centroid_slip_m": max((r["patch_centroid_slip_m"] for r in held), default=None),
            "max_hold_patch_node_displacement_m": max((r["patch_max_node_displacement_m"] for r in held), default=None),
            "max_active_pins": max(r["active_pins"] for r in rows),
            "final_active_pins": len(latch.bridge._pins),
            "sponge_return_xy_error_m": float(np.linalg.norm(final_particles.mean(axis=0)[:2] - initial.mean(axis=0)[:2])),
            "sponge_return_min_z_error_m": float(abs(final_particles[:, 2].min() - initial[:, 2].min())),
            "home_errors_m": home_errors, "finite": bool(sim.state_is_finite()),
            "wall_s": time.perf_counter() - start, "build_wall_s": built_wall,
            "step_wall_s": step_wall, "render_wall_s": render_wall, "record_wall_s": record_wall,
        }
        write_json(args.output / "summary.json", summary)
        print(json.dumps(summary, indent=2), flush=True)
        session.teardown()
    return 1 if error else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("original", "no-latch"), required=True)
    parser.add_argument("--max-seconds", type=float, default=120)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--port", type=int, default=9351)
    parser.add_argument("--video", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--geometry-cache", type=Path)
    parser.add_argument("--capture-geometry", action="store_true")
    args = parser.parse_args()
    args.source = args.source.resolve()
    args.output = args.output.resolve()
    if args.capture_geometry and args.geometry_cache is None:
        parser.error("--capture-geometry requires a new --geometry-cache")
    if args.geometry_cache:
        args.geometry_cache = args.geometry_cache.resolve()
    if not 0.5 <= args.max_seconds <= 120:
        parser.error("Expected 0.5 <= max-seconds <= 120")
    commit = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    if commit != RSS_COMMIT:
        parser.error(f"Expected RSS {RSS_COMMIT}; found {commit}")
    if subprocess.run(["git", "-C", str(args.source), "diff", "--quiet", "HEAD"]).returncode:
        parser.error("The upstream tracked source has modifications")
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.source))
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
