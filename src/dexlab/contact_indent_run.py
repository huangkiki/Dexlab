"""Execute and independently rescore the UniLab indentation/unloading fixture."""

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
    contact_indent,
    contact_parameters,
    contact_plane,
    contact_plane_native,
    physx_baseline,
)
from dexlab.contact_indent import LIMITS, IndentCase, score
from dexlab.physx_baseline import digest, write_json
from dexlab.tasks import contact_plane as contact_task


def run(case, engine, output):
    if not case.name.startswith("dev-"):
        raise ValueError(
            "This response profile is development-only until calibration and suite freeze"
        )
    output.mkdir(parents=True, exist_ok=False)
    sources = {
        "runner.py": Path(__file__),
        **{
            m.__name__.replace(".", "_") + ".py": Path(m.__file__)
            for m in (
                contact_archive,
                contact_parameters,
                cloth_engines,
                contact_indent,
                contact_plane,
                contact_plane_native,
                physx_baseline,
                contact_task,
            )
        },
    }
    hashes = {name: digest(path) for name, path in sources.items()}
    for name, path in sources.items():
        (output / name).write_bytes(path.read_bytes())
    receipt = {
        "case": asdict(case),
        "limits": LIMITS,
        "engine": engine,
        "status": "preparing",
        "source_sha256": hashes,
        "task": contact_task.INDENT_TASK,
        "scope": "Development response measurement, not calibrated engine accuracy",
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
            contact_task.INDENT_TASK,
            sim_backend="isaacsim" if engine == "physx" else engine,
            env_cfg_override={
                "case": asdict(case.plane()),
                "sim_dt": case.timestep,
                "ctrl_dt": case.timestep,
                "max_episode_seconds": case.duration,
                "output_dir": str(output),
                "max_force_n": case.max_force,
            },
        )
        state = env.init_state()
        receipt["native"] = env.native.metadata
        receipt["status"] = "running"
        receipt["preparation_seconds"] = time.perf_counter() - started
        write_json(output / "run.json", receipt)
        rows.append(state.info)
        action = np.zeros(3, dtype=np.float32)
        for step in range(case.steps):
            action = case.command(
                step, state.info["pose"], state.info["velocity"], action
            )
            tick = time.perf_counter()
            state = env.step(action[None])
            step_seconds += time.perf_counter() - tick
            rows.append(state.info)
            actions.append(action.copy())
            contacts.append(state.info["contacts"])
            statuses.append(state.info["native_status"])
        receipt["status"] = "completed"
    except Exception:  # noqa: BLE001 -- preserve failed native measurements.
        receipt.update(status="error", error=traceback.format_exc())
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:  # noqa: BLE001 -- preserve a native shutdown failure.
                receipt["cleanup_error"] = traceback.format_exc()
        data = {
            "time": np.array([r["time_s"] for r in rows]),
            "pose": np.array([r["pose"] for r in rows]).reshape(-1, 7),
            "velocity": np.array([r["velocity"] for r in rows]).reshape(-1, 6),
            "contact_force": np.array([r["contact_force"] for r in rows[1:]]).reshape(
                -1, 3
            ),
            "external_force": np.array(actions).reshape(-1, 3),
            "target_height": case.target(np.arange(len(actions)) * case.timestep),
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


def verify(directory):
    receipt = json.loads((directory / "run.json").read_text())
    case = IndentCase(**receipt["case"])
    with np.load(directory / "states.npz", allow_pickle=False) as saved:
        data = dict(saved)
    result = score(case, data)
    artifacts = receipt.get("artifact_sha256", {})
    required = {
        "states.npz",
        contact_archive.contact_file(receipt),
        "native-status.json",
        *receipt.get("source_sha256", {}),
    }
    required |= contact_parameters.required_native_files(
        receipt["engine"], cylinder=False
    )
    matched = required <= artifacts.keys() and all(
        not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and (directory / name).is_file()
        and digest(directory / name) == expected
        for name, expected in artifacts.items()
    )
    result["checks"].update(
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
    try:
        contacts = contact_archive.read_contacts(directory, receipt)
        if len(contacts) != case.steps:
            raise ValueError("Incomplete contact record")
        for row in contacts:
            values = (
                row["normal_force"] + row["friction_force"]
                if receipt["engine"] == "physx"
                else [p["force_on_box"] for p in row]
            )
            force = np.asarray(values, dtype=float).reshape(-1, 3)
            if not np.isfinite(force).all():
                raise ValueError("Nonfinite contact force")
            ledger.append(force.sum(axis=0))
        result["checks"]["contact_ledger_matches"] = bool(
            np.allclose(ledger, data["contact_force"], atol=1e-7, rtol=1e-6)
        )
    except (KeyError, TypeError, ValueError):
        result["checks"]["contact_ledger_matches"] = False
    result["checks"].update(
        contact_parameters.native_checks(directory, receipt, case.plane())
    )
    result["passed"] = all(result["checks"].values())
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
            parser.error("--verify cannot be combined with run arguments")
        result = verify(args.verify.resolve())
    else:
        if not args.engine or not args.output:
            parser.error("--engine and --output are required")
        case = (
            IndentCase(**json.loads(args.case.read_text()))
            if args.case
            else IndentCase()
        )
        result = run(case, args.engine, args.output.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
