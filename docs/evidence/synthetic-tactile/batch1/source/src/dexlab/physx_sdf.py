"""Native PhysX SDF concavity/contact controls through the UniSim adapter."""

from __future__ import annotations

import argparse
import json
import subprocess
import traceback
from importlib.metadata import distribution, version
from pathlib import Path

import numpy as np

from dexlab.physx_baseline import digest, write_json

PROTOCOL = "physx-sdf-concavity-v3"
CASES = ("sdf-hole", "sdf-surface", "convex-hole")
DT, DURATION = 0.001, 0.35
MASS, GRAVITY = 0.02, 9.81
RING_MAJOR, RING_MINOR, BALL_RADIUS = 0.03, 0.008, 0.008
RING_Z, INITIAL_Z = 0.05, 0.13
# Engineering tolerances, frozen before qualification; not measured material accuracy.
LIMITS = {
    "penetration_m": 0.001,
    "rest_height_m": 0.001,
    "support_relative": 0.05,
    "rest_speed_m_s": 0.005,
    "ballistic_position_m": 0.002,
    "ballistic_velocity_m_s": 0.002,
    "fixed_ring_m": 1e-6,
    "freefall_force_n": 1e-5,
}


def create_scene(case: str, directory: Path):
    import trimesh
    from unisim.dr.types import ModelSourceDescriptor
    from unisim.entities import EntityInitialState, SceneEntitySpec
    from unisim.scene import SceneCfg

    if case not in CASES:
        raise ValueError(f"Unknown SDF control: {case}")
    directory.mkdir(parents=True, exist_ok=False)
    trimesh.creation.torus(
        major_radius=RING_MAJOR,
        minor_radius=RING_MINOR,
        major_sections=96,
        minor_sections=32,
    ).export(directory / "ring.obj")
    trimesh.creation.icosphere(subdivisions=4, radius=BALL_RADIUS).export(
        directory / "ball.obj"
    )
    for name, mass in (("ring", 1.0), ("ball", MASS)):
        kind = "mesh" if case == "convex-hole" and name == "ring" else "sdf"
        # Ring is a fixed fixture; sphere inertia is analytic, approximating its triangle mesh.
        inertia = 0.001 if name == "ring" else 0.4 * MASS * BALL_RADIUS**2
        joint = '<freejoint name="root"/>' if name == "ball" else ""
        (directory / f"{name}.xml").write_text(
            f'<mujoco model="{name}"><asset><mesh name="shape" file="{directory / name}.obj"/>'
            f'</asset><worldbody><body name="body">{joint}'
            f'<inertial pos="0 0 0" mass="{mass}" diaginertia="{inertia} {inertia} {inertia}"/>'
            f'<geom name="surface" type="{kind}" mesh="shape" friction=".5 0 0"/>'
            "</body></worldbody></mujoco>\n"
        )
    sensor = directory / "sensors.xml"
    sensor.write_text(
        '<mujoco><sensor><contact name="support" geom1="ball/surface" '
        'geom2="ring/surface" data="force" reduce="netforce"/></sensor></mujoco>\n'
    )
    x = RING_MAJOR if case == "sdf-surface" else 0.0
    return SceneCfg(
        entity_assets=tuple(
            SceneEntitySpec(
                name,
                ModelSourceDescriptor(str(directory / f"{name}.xml")),
                kind="rigid",
                root_mode="floating" if name == "ball" else "fixed",
                initial_state=EntityInitialState(
                    position=(x, 0, INITIAL_Z) if name == "ball" else (0, 0, RING_Z)
                ),
            )
            for name in ("ball", "ring")
        ),
        fragment_files=[str(sensor)],
    )


def score(case: str, arrays: dict[str, np.ndarray]) -> dict:
    if case not in CASES:
        raise ValueError(f"Unknown SDF control: {case}")
    count = round(DURATION / DT)
    shapes = {
        "time": (count,),
        "position": (count, 2, 3),
        "velocity": (count, 2, 3),
        "force": (count, 3),
    }
    complete = all(
        k in arrays and arrays[k].shape == shape for k, shape in shapes.items()
    )
    finite = complete and all(np.isfinite(arrays[k]).all() for k in shapes)
    uniform = finite and np.allclose(
        arrays["time"], np.arange(1, count + 1) * DT, rtol=0, atol=1e-10
    )
    checks = {"complete_finite_steps": bool(finite), "uniform_timestep": bool(uniform)}
    metrics = {}
    if not all(checks.values()):
        return {"passed": False, "checks": checks, "metrics": metrics}
    position, velocity, force = (arrays[k] for k in ("position", "velocity", "force"))
    fixed_error = float(np.abs(position[:, 1] - [0, 0, RING_Z]).max())
    checks["ring_remains_fixed"] = fixed_error < LIMITS["fixed_ring_m"]
    relative = position[:, 0] - [0, 0, RING_Z]
    clearance = (
        np.sqrt(
            (np.linalg.norm(relative[:, :2], axis=1) - RING_MAJOR) ** 2
            + relative[:, 2] ** 2
        )
        - RING_MINOR
        - BALL_RADIUS
    )
    metrics.update(
        fixed_ring_error_m=fixed_error,
        minimum_analytic_torus_clearance_m=float(clearance.min()),
        final_ball_position_m=position[-1, 0].tolist(),
    )
    if case == "sdf-hole":
        ballistic_z = INITIAL_Z - 0.5 * GRAVITY * arrays["time"] ** 2
        z_error = float(np.abs(position[:, 0, 2] - ballistic_z).max())
        v_error = float(np.abs(velocity[:, 0, 2] + GRAVITY * arrays["time"]).max())
        max_force = float(np.linalg.norm(force, axis=1).max())
        checks.update(
            falls_through_hole=bool(position[-1, 0, 2] < -0.4),
            no_false_contact=max_force < LIMITS["freefall_force_n"],
            positive_clearance=bool(clearance.min() > 0.01),
            ballistic_position=z_error < LIMITS["ballistic_position_m"],
            ballistic_velocity=v_error < LIMITS["ballistic_velocity_m_s"],
        )
        metrics.update(
            ballistic_position_error_m=z_error,
            ballistic_velocity_error_m_s=v_error,
            maximum_force_n=max_force,
        )
    else:
        late = arrays["time"] >= 0.25
        height_error = float(
            np.abs(position[late, 0, 2] - (RING_Z + RING_MINOR + BALL_RADIUS)).max()
        )
        speed = float(np.linalg.norm(velocity[late, 0], axis=1).max())
        support = float(force[late, 2].mean())
        checks.update(
            surface_support=abs(support / (MASS * GRAVITY) - 1)
            < LIMITS["support_relative"],
            supported_height=height_error < LIMITS["rest_height_m"],
            low_late_speed=speed < LIMITS["rest_speed_m_s"],
        )
        if case == "sdf-surface":
            checks["bounded_analytic_penetration"] = bool(
                clearance.min() > -LIMITS["penetration_m"]
            )
        else:
            # Explicit negative geometry control: the convex hull fills the torus hole.
            checks["convex_hull_blocks_hole"] = bool(position[-1, 0, 2] > 0.06)
        metrics.update(
            late_height_error_m=height_error,
            late_maximum_speed_m_s=speed,
            late_mean_support_n=support,
        )
    return {"passed": bool(all(checks.values())), "checks": checks, "metrics": metrics}


def verify(output: Path) -> dict:
    receipt = json.loads((output / "run.json").read_text())
    with np.load(output / "states.npz", allow_pickle=False) as saved:
        result = score(receipt["case"], dict(saved))
    hashes = receipt["artifact_sha256"]
    required = {
        "states.npz",
        "source.py",
        "native-records.json",
        "import-report.json",
        "layout.json",
        "scene/ball.xml",
        "scene/ring.xml",
        "scene/ball.obj",
        "scene/ring.obj",
        "unisim-sdf-collision.py",
        "unisim-scene-materialization.py",
        "unisim-scene-worker.py",
    }
    matched = required <= hashes.keys() and all(
        (output / p).is_file() and digest(output / p) == sha
        for p, sha in hashes.items()
    )
    native = json.loads((output / "native-records.json").read_text()) if matched else {}
    expected = {"approximation": "sdf", "resolution": 256, "subgrid_resolution": 6}
    sdf_ok = all(
        native.get(name, {}).get("geom_sdf")
        == [[None if name == "ring" and receipt["case"] == "convex-hole" else expected]]
        for name in ("ball", "ring")
    )
    report = json.loads((output / "import-report.json").read_text()) if matched else {}
    fields = {f["field"]: f for f in report.get("fields", [])}
    offsets_ok = all(
        name in fields
        and np.isclose(
            fields[name].get("effective", float("nan")),
            expected_value,
            rtol=1e-6,
            atol=1e-9,
        )
        and any(
            p.get("kind") == "engine_readback"
            for p in fields[name].get("provenance", [])
        )
        for name, expected_value in (("contact_offset", 0.0001), ("rest_offset", 0.0))
    )
    masses = np.asarray(receipt.get("native_mass", []))
    result["checks"].update(
        frozen_protocol=receipt.get("protocol") == PROTOCOL
        and receipt.get("limits") == LIMITS,
        archive_hashes_match=matched,
        native_completed=receipt.get("status") == "completed"
        and "cleanup_error" not in receipt,
        unchanged_sources=receipt.get("source_unchanged") is True,
        native_sdf_authoring_readback=sdf_ok,
        native_contact_offsets=bool(offsets_ok),
        native_mass_matches=bool(
            masses.shape == (1, 3) and np.allclose(masses, [[0, MASS, 1]], atol=1e-7)
        ),
    )
    result["passed"] = bool(all(result["checks"].values()))
    result["verifier_sha256"] = digest(Path(__file__))
    write_json(output / "summary.json", result)
    return result


def run(case: str, output: Path) -> dict:
    from unisim import factory
    from unisim.backend.isaacsim import backend as adapter
    from unisim.backend.isaacsim import physx_solver, scene_worker, sdf_collision
    from unisim.backend.isaacsim.dependencies import resolve_isaacsim_runtime
    from unisim.backend.subprocess_ipc import scene_materialization

    output.mkdir(parents=True, exist_ok=False)
    snapshots = {
        "source.py": Path(__file__),
        "unisim-factory.py": Path(factory.__file__),
        "unisim-backend.py": Path(adapter.__file__),
        "unisim-physx-solver.py": Path(physx_solver.__file__),
        "unisim-scene-worker.py": Path(scene_worker.__file__),
        "unisim-sdf-collision.py": Path(sdf_collision.__file__),
        "unisim-scene-materialization.py": Path(scene_materialization.__file__),
    }
    hashes = {name: digest(path) for name, path in snapshots.items()}
    for name, path in snapshots.items():
        (output / name).write_bytes(path.read_bytes())
    receipt = {
        "protocol": PROTOCOL,
        "limits": LIMITS,
        "case": case,
        "status": "preparing",
        "source_sha256": hashes,
        "unisim_version": version("unisim-core"),
        "unisim_install_origin": distribution("unisim-core").read_text(
            "direct_url.json"
        ),
        "scope": "0.35 s SDF concavity/contact; fixed torus and dynamic sphere; not robot grasp",
        "force_measurement": "PhysX pair normal force only; no tangential force claim",
    }
    write_json(output / "run.json", receipt)
    backend, rows = None, []
    try:
        runtime = resolve_isaacsim_runtime()
        metadata = subprocess.run(
            [
                str(runtime.python),
                "-c",
                (
                    "import importlib.metadata as m,json,sys; "
                    "print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in "
                    "['isaacsim','isaacsim-kernel','isaaclab','torch']}}))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        receipt["worker"] = json.loads(metadata.stdout)
        backend = factory.create_backend(
            "isaacsim",
            create_scene(case, output / "scene"),
            num_envs=1,
            sim_dt=DT,
            isaacsim_worker_timeout_s=600,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_contact_offset=0.0001,
            isaacsim_rest_offset=0.0,
        )
        backend.materialize()
        write_json(output / "layout.json", backend.get_scene_layout().to_dict())
        write_json(output / "import-report.json", backend.get_import_report().to_dict())
        # Qualification-only native audit; public contract does not expose SDF cooking metadata.
        write_json(output / "native-records.json", backend._native_entity_records)
        receipt["native_mass"] = backend.get_body_mass().tolist()
        ids = backend.get_body_ids(["ball/body", "ring/body"])
        for step in range(round(DURATION / DT)):
            backend.step(np.empty((1, 0), dtype=np.float32))
            rows.append(
                {
                    "time": (step + 1) * DT,
                    "position": backend.get_body_pos_w(ids)[0].copy(),
                    "velocity": backend.get_body_lin_vel_w(ids)[0].copy(),
                    "force": backend.get_sensor_data("support")[0].copy(),
                }
            )
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 - archive failed native runs before independent scoring
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            (output / "worker-stderr.log").write_text(backend._stderr_tail())
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:  # noqa: BLE001 - cleanup failure must invalidate the run
                receipt["cleanup_error"] = traceback.format_exc()
        arrays = (
            {k: np.asarray([row[k] for row in rows]) for k in rows[0]} if rows else {}
        )
        np.savez_compressed(output / "states.npz", **arrays)
        receipt["source_unchanged"] = all(
            digest(p) == hashes[n] for n, p in snapshots.items()
        )
        receipt["artifact_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file() and p.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    return verify(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--case", choices=CASES, required=True)
    execute.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = (
        run(args.case, args.output.resolve())
        if args.command == "run"
        else verify(args.directory.resolve())
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
