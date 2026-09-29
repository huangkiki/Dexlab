"""Qualify native normal and friction reporting with a sliding rigid block.

This is an observation-consistency test, not a material calibration or grasp
success test. Verification uses saved actual velocities and contact records.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import traceback

import numpy as np

from dexlab.physx_baseline import (
    ContactCase,
    create_scene,
    digest,
    native_parameter_checks,
    write_json,
)

CASE = ContactCase(
    "contact-details-slide", friction=0.3, initial_speed=0.5, duration=0.25, settle=0.1
)
# Engineering tolerances declared for this protocol, not hardware accuracy.
LIMITS = {"momentum_residual_weight_ratio": 0.01, "minimum_friction_n": 0.1}


def score(states: dict, contacts: list[dict]) -> dict:
    """Reject incomplete records; check native force against actual momentum."""
    steps = round(CASE.duration / CASE.timestep)
    shapes = {"time": (steps,), "velocity": (steps, 3), "initial_velocity": (3,)}
    complete = all(
        key in states and states[key].shape == shape for key, shape in shapes.items()
    )
    complete = complete and all(np.isfinite(states[key]).all() for key in shapes)
    grid = complete and np.allclose(
        states["time"], np.arange(1, steps + 1) * CASE.timestep, rtol=0, atol=1e-10
    )
    checks = {
        "complete_time_and_velocity": bool(grid),
        "one_contact_record_per_step": len(contacts) == steps,
    }
    result = {"passed": False, "checks": checks, "metrics": {}}
    if not all(checks.values()):
        return result
    forces = {}
    try:
        for kind in ("normal", "friction"):
            values = []
            for row in contacts:
                force = np.asarray(row[kind + "_force"], dtype=float)
                if force.size == 0:
                    force = force.reshape(0, 3)
                ids = np.asarray(row[kind + "_body_ids"])
                if (
                    force.ndim != 2
                    or force.shape[1] != 3
                    or ids.ndim != 1
                    or (ids.size and (ids.dtype.kind not in "iu" or np.any(ids < 0)))
                    or force.shape[0] != len(ids)
                    or not np.isfinite(force).all()
                ):
                    raise ValueError("Invalid native contact record")
                values.append(force.sum(axis=0))
            forces[kind] = np.asarray(values)
    except (KeyError, TypeError, ValueError):
        checks["finite_contact_forces"] = False
        return result
    checks["finite_contact_forces"] = True
    previous = np.vstack((states["initial_velocity"], states["velocity"][:-1]))
    momentum_rate = CASE.mass * (states["velocity"] - previous) / CASE.timestep
    residual = momentum_rate - forces["normal"] - forces["friction"]
    residual[:, 2] += CASE.mass * CASE.gravity
    maximum = float(np.linalg.norm(residual, axis=1).max())
    friction = float(np.linalg.norm(forces["friction"], axis=1).max())
    checks.update(
        initial_slide=bool(
            np.allclose(
                states["initial_velocity"],
                [CASE.initial_speed, 0, 0],
                rtol=0,
                atol=1e-6,
            )
        ),
        friction_observed=friction > LIMITS["minimum_friction_n"],
        momentum_balance=maximum / (CASE.mass * CASE.gravity)
        < LIMITS["momentum_residual_weight_ratio"],
    )
    result["metrics"] = {
        "maximum_momentum_residual_n": maximum,
        "maximum_momentum_residual_weight_ratio": maximum / (CASE.mass * CASE.gravity),
        "maximum_friction_n": friction,
    }
    result["passed"] = all(checks.values())
    return result


def verify(directory: Path) -> dict:
    """Offline rescoring; preserve the original receipt and evidence files."""
    receipt = json.loads((directory / "run.json").read_text())
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        result = score(
            dict(saved), json.loads((directory / "contacts.json").read_text())
        )
    artifacts = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        "contacts.json",
        "native-records.json",
        "layout.json",
        "import-report.json",
        "source.py",
        "baseline-source.py",
        "scene/box.xml",
        "scene/table.xml",
        "scene/sensors.xml",
        "unisim-contact-details.py",
        "unisim-backend.py",
        "unisim-worker.py",
        "unisim-scene-worker.py",
    }
    hashes_match = required <= artifacts.keys() and all(
        not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and (directory / name).is_file()
        and digest(directory / name) == expected
        for name, expected in artifacts.items()
    )
    result["checks"].update(
        native_run_completed=receipt.get("status") == "completed",
        clean_shutdown="cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True,
        artifact_hashes_match=hashes_match,
        frozen_protocol=receipt.get("case") == asdict(CASE)
        and receipt.get("limits") == LIMITS,
    )
    layout = json.loads((directory / "layout.json").read_text()) if hashes_match else {}
    result["checks"].update(native_parameter_checks(CASE, receipt, layout))
    result["passed"] = all(result["checks"].values())
    result["scope"] = __doc__.strip()
    return result


def run(output: Path) -> dict:
    from dexlab import physx_baseline
    from unisim.backend.isaacsim import (
        backend as adapter,
        contact_details,
        scene_worker,
        worker,
    )
    from unisim.entities import EntityStatePatch, SceneResetRequest
    from unisim.factory import create_backend

    output.mkdir(parents=True, exist_ok=False)
    sources = {
        "source.py": Path(__file__),
        "baseline-source.py": Path(physx_baseline.__file__),
        "unisim-contact-details.py": Path(contact_details.__file__),
        "unisim-backend.py": Path(adapter.__file__),
        "unisim-worker.py": Path(worker.__file__),
        "unisim-scene-worker.py": Path(scene_worker.__file__),
    }
    source_hashes = {name: digest(path) for name, path in sources.items()}
    for name, path in sources.items():
        shutil.copyfile(path, output / name)
    receipt = {
        "status": "preparing",
        "case": asdict(CASE),
        "limits": LIMITS,
        "source_sha256": source_hashes,
        "scope": __doc__.strip(),
    }
    write_json(output / "run.json", receipt)
    backend, velocities, contacts = None, [], []
    initial = np.full(3, np.nan)
    try:
        backend = create_backend(
            "isaacsim",
            create_scene(CASE, output / "scene"),
            num_envs=1,
            sim_dt=CASE.timestep,
            isaacsim_worker_timeout_s=600,
            isaacsim_solver_position_iteration_count=8,
            isaacsim_solver_velocity_iteration_count=2,
            isaacsim_external_forces_every_iteration=True,
            isaacsim_contact_offset=0.0001,
            isaacsim_rest_offset=0.0,
        )
        backend.materialize()
        receipt["contact_details"] = backend.enable_contact_details("box")
        receipt["body_mass_readback"] = backend.get_body_mass().tolist()
        receipt["geom_friction_readback"] = backend.get_geom_friction().tolist()
        for name, value in (
            ("native-records.json", backend._native_entity_records),
            ("layout.json", backend.get_scene_layout().to_dict()),
            ("import-report.json", backend.get_import_report().to_dict()),
        ):
            write_json(output / name, value)
        controls = np.empty((1, 0), dtype=np.float32)
        for _ in range(round(CASE.settle / CASE.timestep)):
            backend.step(controls)
        velocity = np.zeros((1, 6), dtype=np.float32)
        velocity[0, 0] = CASE.initial_speed
        backend.reset_entities(
            SceneResetRequest(
                env_ids=(0,),
                patches=(EntityStatePatch("box", root_velocity=velocity),),
            )
        )
        # This block's inertial origin equals its link origin.
        initial = backend.get_entity_state("box")["root_velocity"][0, :3].copy()
        for _ in range(round(CASE.duration / CASE.timestep)):
            backend.step(controls)
            velocities.append(
                backend.get_entity_state("box")["root_velocity"][0, :3].copy()
            )
            contacts.append(
                {
                    name: np.asarray(value).tolist()
                    for name, value in backend.get_contact_details().items()
                }
            )
        receipt["status"] = "completed"
    except Exception:
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if backend is not None:
            (output / "worker-stderr.log").write_text(backend._stderr_tail())
            try:
                backend.close()
                backend.cleanup_scene_assets()
            except Exception:
                receipt["cleanup_error"] = traceback.format_exc()
        np.savez_compressed(
            output / "states.npz",
            time=np.arange(1, len(velocities) + 1) * CASE.timestep,
            velocity=np.asarray(velocities).reshape(-1, 3),
            initial_velocity=initial,
        )
        write_json(output / "contacts.json", contacts)
        receipt["source_unchanged"] = all(
            digest(path) == source_hashes[name] for name, path in sources.items()
        )
        receipt["artifact_sha256"] = {
            str(path.relative_to(output)): digest(path)
            for path in output.rglob("*")
            if path.is_file() and path.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    return verify(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("run").add_argument("--output", type=Path, required=True)
    commands.add_parser("verify").add_argument("directory", type=Path)
    args = parser.parse_args()
    result = (
        run(args.output.resolve())
        if args.command == "run"
        else verify(args.directory.resolve())
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
