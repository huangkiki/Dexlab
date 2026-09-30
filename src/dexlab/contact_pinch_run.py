"""Archive and independently score native UniLab cylinder load/release runs."""

import argparse
import json
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import numpy as np
from unilab.base import registry

from dexlab import (
    cloth_engines,
    contact_archive,
    contact_kinematics,
    contact_parameters,
    contact_pinch,
    contact_pinch_native,
    physx_baseline,
    physx_pinch,
)
from dexlab.contact_pinch import DURATION, LIMITS, CylinderCase, score
from dexlab.physx_baseline import digest, write_json
from dexlab.tasks import contact_pinch as contact_task


def run(case, engine, output):
    if not case.name.startswith("dev-"):
        raise ValueError("Development cases only until the complete suite freeze")
    output.mkdir(parents=True, exist_ok=False)
    modules = (
        contact_archive,
        contact_kinematics,
        contact_parameters,
        cloth_engines,
        contact_pinch,
        contact_pinch_native,
        physx_baseline,
        physx_pinch,
        contact_task,
    )
    sources = {
        "runner.py": Path(__file__),
        **{m.__name__.replace(".", "_") + ".py": Path(m.__file__) for m in modules},
    }
    hashes = {name: digest(path) for name, path in sources.items()}
    for name, path in sources.items():
        (output / name).write_bytes(path.read_bytes())
    receipt = {
        "case": asdict(case),
        "limits": LIMITS,
        "engine": engine,
        "task": contact_task.TASK,
        "status": "preparing",
        "source_sha256": hashes,
        "scope": "Nominal cylinder development; no material calibration or held-out claim",
    }
    write_json(output / "run.json", receipt)
    env = None
    rows = []
    actions = []
    contacts = []
    statuses = []
    started = time.perf_counter()
    step_seconds = 0.0
    try:
        env = registry.make(
            contact_task.TASK,
            sim_backend="isaacsim" if engine == "physx" else engine,
            env_cfg_override={
                "case": asdict(case),
                "sim_dt": case.timestep,
                "ctrl_dt": case.timestep,
                "max_episode_seconds": DURATION,
                "output_dir": str(output),
            },
        )
        state = env.init_state()
        rows.append(state.info)
        receipt.update(
            native=env.native.metadata,
            status="running",
            preparation_seconds=time.perf_counter() - started,
        )
        write_json(output / "run.json", receipt)
        for step in range(case.steps):
            action = case.force(step)
            tick = time.perf_counter()
            state = env.step(action[None])
            step_seconds += time.perf_counter() - tick
            rows.append(state.info)
            actions.append(action)
            contacts.append(state.info["contacts"])
            statuses.append(state.info["native_status"])
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 -- archive every native failure.
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:  # noqa: BLE001 -- preserve a native shutdown failure.
                receipt["cleanup_error"] = traceback.format_exc()
        data = {
            "time": np.array([r["time_s"] for r in rows]),
            "pose": np.array([r["pose"] for r in rows]).reshape(-1, 3, 7),
            "velocity": np.array([r["velocity"] for r in rows]).reshape(-1, 3, 6),
            "external_force": np.array(actions).reshape(-1, 3, 3),
            "contact_force": np.array([r["contact_force"] for r in rows[1:]]).reshape(
                -1, 2, 3
            ),
            "normal_force": np.array([r["normal_force"] for r in rows[1:]]).reshape(
                -1, 2, 3
            ),
            "contact_known": np.array(
                [r["contact_known"] for r in rows[1:]], dtype=bool
            ),
            "step_completed": np.array(
                [r["step_completed"] for r in rows[1:]], dtype=bool
            ),
        }
        np.savez_compressed(output / "states.npz", **data)
        receipt["contact_archive"] = contact_archive.write_contacts(output, contacts)
        write_json(output / "native-status.json", statuses)
        receipt.update(
            total_seconds=time.perf_counter() - started,
            step_and_observation_seconds=step_seconds,
            source_unchanged=all(
                digest(path) == hashes[name] for name, path in sources.items()
            ),
        )
        receipt["artifact_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file() and p.name != "run.json"
        }
        write_json(output / "run.json", receipt)
    result = verify(output)
    write_json(output / "summary.json", result)
    return result


def normal_components_consistent(row, engine):
    """Check native arithmetic without pairing PhysX friction anchors to normals."""
    try:
        if engine == "physx":
            direction = np.asarray(row["normal_direction"], dtype=float).reshape(-1, 3)
            normal = np.asarray(row["normal_force"], dtype=float).reshape(-1, 3)
            magnitude = np.asarray(row["normal_magnitude"], dtype=float)
        else:
            direction = np.array(
                [p["normal_direction"] for p in row], dtype=float
            ).reshape(-1, 3)
            normal = np.array([p["normal_force"] for p in row], dtype=float).reshape(
                -1, 3
            )
            force = np.array([p["force"] for p in row], dtype=float).reshape(-1, 3)
            magnitude = np.einsum("ij,ij->i", force, direction)
            if np.any(magnitude < -1e-7):
                return False
        if (
            normal.shape != direction.shape
            or magnitude.shape != (len(normal),)
            or not np.isfinite(direction).all()
            or not np.isfinite(normal).all()
            or not np.isfinite(magnitude).all()
            or not np.allclose(np.linalg.norm(direction, axis=1), 1, rtol=0, atol=1e-5)
        ):
            return False
        # FP32 observation arithmetic, not a relaxed physical force limit.
        error = np.linalg.norm(normal - magnitude[:, None] * direction, axis=1)
        return bool(np.all(error <= 1e-7 + 1e-6 * np.linalg.norm(normal, axis=1)))
    except (KeyError, TypeError, ValueError):
        return False


def verify(directory):
    receipt = json.loads((directory / "run.json").read_text())
    case = CylinderCase(**receipt["case"])
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        data = dict(saved)
    result = score(case, data)
    artifacts = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        contact_archive.contact_file(receipt),
        "native-status.json",
        "geometry.npz",
        "cylinder.obj",
        *receipt.get("source_sha256", {}),
    }
    required |= contact_parameters.required_native_files(
        receipt["engine"], cylinder=True
    )
    matched = required <= artifacts.keys() and all(
        not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and (directory / name).is_file()
        and digest(directory / name) == expected
        for name, expected in artifacts.items()
    )
    checks = result["checks"]
    checks.update(
        artifact_hashes_match=matched,
        native_run_completed=receipt.get("status") == "completed",
        clean_shutdown="cleanup_error" not in receipt,
        source_unchanged=receipt.get("source_unchanged") is True,
        archived_source_hashes_match=contact_archive.source_snapshots_match(
            directory, receipt
        ),
        declared_limits=receipt.get("limits") == LIMITS,
    )
    ledger = []
    normals = []
    checks["native_normal_components_consistent"] = False
    try:
        contacts = contact_archive.read_contacts(directory, receipt)
        if len(contacts) != case.steps:
            raise ValueError("Incomplete contact ledger")
        checks["native_normal_components_consistent"] = all(
            normal_components_consistent(row, receipt["engine"]) for row in contacts
        )
        for row in contacts:
            force = np.zeros((2, 3))
            normal = np.zeros((2, 3))
            if receipt["engine"] == "physx":
                lookup = {
                    int(body): i for i, body in enumerate(receipt["native"]["body_ids"])
                }
                for kind in ("normal", "friction"):
                    ids = row[kind + "_body_ids"]
                    values = np.asarray(row[kind + "_force"]).reshape(-1, 3)
                    if len(ids) != len(values):
                        raise ValueError("Incomplete contact pairs")
                    for other, f in zip(ids, values):
                        pad = lookup[other]
                        if pad not in (0, 1):
                            raise ValueError("Unexpected contact partner")
                        force[pad] += f
                        if kind == "normal":
                            normal[pad] += f
            else:
                for point in row:
                    pad = point["pad"]
                    if pad not in (0, 1):
                        raise ValueError("Unexpected contact partner")
                    force[pad] += point["force"]
                    normal[pad] += point["normal_force"]
            ledger.append(force)
            normals.append(normal)
        if (
            result["checks"].get("finite_record")
            and result["checks"]["complete_shapes"]
        ):
            result["contact_motion"] = contact_kinematics.summarize_cylinder_motion(
                data,
                contacts,
                receipt["engine"],
                receipt.get("native", {}).get("body_ids", ()),
            )
            checks["contact_motion_observation_complete"] = result["contact_motion"][
                "complete_observation_coverage"
            ]
        checks["contact_ledger_matches"] = bool(
            np.allclose(ledger, data["contact_force"], atol=1e-7, rtol=1e-6)
            and np.allclose(normals, data["normal_force"], atol=1e-7, rtol=1e-6)
        )
    except (KeyError, TypeError, ValueError):
        checks["contact_ledger_matches"] = False
    result["checks"].update(
        contact_parameters.native_checks(directory, receipt, case, cylinder=True)
    )
    result["passed"] = all(checks.values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("mujoco", "superdex", "physx"))
    parser.add_argument("--case", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        if args.engine or args.case or args.output:
            parser.error("--verify cannot combine with run arguments")
        result = verify(args.verify.resolve())
    else:
        if not args.engine or not args.output:
            parser.error("--engine and --output required")
        case = (
            CylinderCase(**json.loads(args.case.read_text()))
            if args.case
            else CylinderCase()
        )
        result = run(case, args.engine, args.output.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
