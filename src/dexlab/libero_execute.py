"""Execute complete, admitted LIBERO action sequences with task-aware records.

Version 2 keeps historical single-object execution separate. This entrypoint
records control-step observations and native goals; substep force qualification
and learned-policy execution are separate acceptance, not implied by completion.
"""

import argparse
from contextlib import nullcontext
from copy import deepcopy
import importlib.metadata
import json
import os
from pathlib import Path
import time

import numpy as np

from dexlab.libero_bindings import bind_task
from dexlab.libero_demo import load_demo
from dexlab.libero_goals import record_goal_queries
from dexlab.libero_initialization import initialize_demo
from dexlab.libero_inputs import _source_identity
from dexlab.libero_physics import record_substeps
from dexlab.libero_substeps import SubstepArchive
from dexlab.libero_workflow import file_hash, relocate_assets
from dexlab.migration_budget import json_bytes, publish

RUNTIME_PACKAGES = {"mujoco", "robosuite", "libero", "numpy", "scipy", "numba", "llvmlite", "h5py", "bddl", "gym"}
NUMERICAL_ENVIRONMENT = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                         "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT", "NUMBA_CPU_NAME")
SOURCE_FILES = ("libero_execute.py", "libero_demo.py", "libero_initialization.py",
                "libero_bindings.py", "libero_goals.py", "libero_dataset.py",
                "libero_inputs.py", "libero_workflow.py", "migration_budget.py",
                "libero_physics.py", "libero_substeps.py")


def source_hashes():
    return {name: file_hash(Path(__file__).with_name(name)) for name in SOURCE_FILES}


def validate_numerical_environment(environment):
    """Freeze relevant inherited controls explicitly; null means unset, not defaulted."""
    if (not isinstance(environment, dict) or set(environment) != set(NUMERICAL_ENVIRONMENT)
            or any(value is not None and (not isinstance(value, str) or not value or "\0" in value)
                   for value in environment.values())):
        raise ValueError("Freeze every numerical environment control as a string or null")


def _append(rows, key, value):
    value = np.asarray(value)
    if not np.isfinite(value).all():
        raise ValueError("Non-finite native observation: " + key)
    previous = rows.setdefault(key, [])
    if previous and (value.shape != previous[0].shape or value.dtype != previous[0].dtype):
        raise ValueError("Native observation shape or dtype changed: " + key)
    previous.append(value.copy())


def execute_actions(env, actions, definition, *, recording, rows, events, markers, substeps=None):
    """Drive each action exactly once; observe success only where native code does.

    Caller-owned partial records survive an exception. A hook context restores
    itself even when an action fails. No success-triggered stop or state replay.
    """
    if (type(recording) is not bool or actions.ndim != 2 or actions.shape[1] != 7
            or actions.dtype.kind != "f"):
        raise ValueError("Expected native seven-dimensional actions and an explicit recording switch")
    if not len(actions) or not np.isfinite(actions).all():
        raise ValueError("Expected a complete nonempty finite action sequence")
    if rows or events or markers:
        raise ValueError("Execution output containers must be empty")
    context = record_goal_queries(env, definition) if recording else nullcontext([])
    observation_keys = None
    with context as queries:
        try:
            for action_index, action in enumerate(actions):
                before, start = float(env.sim.data.time), len(queries)
                if substeps is not None:
                    substeps.start_action(action_index)
                try:
                    obs, reward, done, _ = env.step(action.copy())
                except BaseException as error:
                    if substeps is not None:
                        try:
                            substeps.flush()
                        except BaseException as save_error:
                            raise error from save_error
                    raise
                if substeps is not None:
                    substeps.flush()
                if not isinstance(done, (bool, np.bool_)):
                    raise ValueError("Native step did not return boolean task success")
                if recording and (len(queries) == start or queries[-1]["native_success"] != bool(done)):
                    raise ValueError("Native step success contradicts its existing goal queries")
                if observation_keys is None:
                    observation_keys = set(obs)
                elif set(obs) != observation_keys:
                    raise ValueError("Native observation channels changed")
                data, model = env.sim.data, env.sim.model._model
                if not float(data.time) > before:
                    raise ValueError("Native action did not advance simulation time")
                values = {"action_interval": [before, float(data.time)], "actions": action,
                          "state": env.sim.get_state().flatten(), "time": float(data.time),
                          "reward": reward, "done": done, "ctrl": data.ctrl,
                          "actuator_force": data.actuator_force, "qfrc_actuator": data.qfrc_actuator,
                          "body_xpos": data._data.xpos, "body_xquat": data._data.xquat,
                          "body_xipos": data._data.xipos, "site_rgba": model.site_rgba,
                          "goal_event_range": [start, len(queries)]}
                values.update({"obs:" + key: value for key, value in obs.items()})
                for key, value in values.items():
                    _append(rows, key, value)
                markers.append({name: deepcopy(env.get_object(name).object_properties["vis_site_names"])
                                for name in env.visualization_sites_list})
        finally:
            events.extend(deepcopy(queries))


def run(payload, output):
    """Run one frozen case; the existing ledger owns admission, timeout and cost."""
    if (payload.get("schema_version") != 2 or type(payload.get("recording")) is not bool
            or type(payload.get("seed")) is not int or not 0 <= payload["seed"] < 2**32
            or payload.get("purpose") not in ("development", "baseline", "validation")):
        raise ValueError("Expected an explicit version-2 native execution case")
    substep_recording = payload.get("substep_recording", False)
    if type(substep_recording) is not bool or substep_recording and not payload["recording"]:
        raise ValueError("Substep recording requires the explicit recording path")
    versions = payload["runtime_versions"]
    if (set(versions) != RUNTIME_PACKAGES
            or {name: importlib.metadata.version(name) for name in versions} != versions):
        raise ValueError("Native runtime differs from the declared frozen package versions")
    if payload["source_sha256"] != source_hashes():
        raise ValueError("Execution source differs from the frozen case")
    numerical_environment = payload.get("numerical_environment")
    validate_numerical_environment(numerical_environment)
    if {key: os.environ.get(key) for key in NUMERICAL_ENVIRONMENT} != numerical_environment:
        raise ValueError("Native numerical environment differs from the frozen case")
    inputs = load_demo(payload["input_dir"], payload["input_manifest_sha256"], payload["demo_id"])
    task, declaration = inputs["task"], inputs["demonstration"]
    if task["task_id"] != payload["task_id"]:
        raise ValueError("Prepared task differs from the requested case")
    if payload["purpose"] != "baseline" and declaration["split"] != payload["purpose"]:
        raise ValueError("Requested execution violates the frozen demonstration split")
    source = Path(payload["libero_root"]).resolve(strict=True)
    _source_identity(source)
    bddl = (source / task["bddl_path"]).resolve(strict=True)
    if not bddl.is_relative_to(source) or bddl.read_bytes() != inputs["bddl"]:
        raise ValueError("Native BDDL differs from the prepared task")
    import robosuite
    from libero.libero.envs import TASK_MAPPING

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    publish(output / "input.json", json_bytes(payload))
    publish(output / "task.json", json_bytes(task))
    rows, events, markers, initialization = {}, [], [], {}
    started, env, status, phase = time.monotonic(), None, "failed", "asset-relocation"
    substeps = None
    receipt = {"schema_version": 2, "task_id": task["task_id"], "demo_id": declaration["demo_id"],
               "expected_actions": declaration["action_count"], "purpose": payload["purpose"],
               "input_split": declaration["split"], "recording": payload["recording"],
               "substep_recording": substep_recording,
               "input_manifest_sha256": payload["input_manifest_sha256"],
               "versions": versions, "source_sha256": payload["source_sha256"],
               "numerical_environment": numerical_environment,
               "instruction": {**inputs["admission"]["linkage"]["language"],
                               "native_contract": "pinned-bddl", "policy_used": False},
               "physics_qualification": "pending-substep-recording-and-independent-scoring"}
    try:
        xml, assets = relocate_assets(inputs["model_xml"], source, Path(robosuite.__file__).parent)
        publish(output / "assets.json", json_bytes(assets))
        publish(output / "input-model.xml", inputs["model_xml"].encode())
        publish(output / "relocated-model.xml", xml.encode())
        kwargs = dict(inputs["metadata"]["env_kwargs"])
        kwargs.update(bddl_file_name=str(bddl), has_renderer=False,
                      has_offscreen_renderer=False, use_camera_obs=False)
        np.random.seed(payload["seed"])
        phase = "native-initialization"
        env = TASK_MAPPING[inputs["metadata"]["problem_name"]](**kwargs)
        initialize_demo(env, xml, inputs["initial"], initialization)
        phase = "binding"
        bindings = bind_task(env, task["definition"])
        publish(output / "bindings.json", json_bytes(bindings))
        publish(output / "effective-model.xml", env.sim.model.get_xml().encode())
        receipt.update(control_freq=env.control_freq, control_timestep=env.control_timestep,
                       model_timestep=env.model_timestep, initial_time_s=float(env.sim.data.time),
                       observation_scope="Native non-image observations; channel epochs follow the pinned native implementation.",
                       force_scope="Control-step readbacks only; not substep force accounting.")
        if substep_recording:
            substeps = SubstepArchive(output / "substeps")
            receipt.update(force_scope="Native Euler substeps; force caches at pre-integration epoch; separate post-integration state.",
                           physics_qualification="pending-integrated-native-qualification-and-independent-scoring")
        phase = "actions"
        context = record_substeps(env.sim, substeps.append) if substeps is not None else nullcontext(None)
        with context as physics_model:
            if physics_model is not None:
                publish(output / "physics-model.json", json_bytes(physics_model))
            execute_actions(env, inputs["actions"], task["definition"], recording=payload["recording"],
                            rows=rows, events=events, markers=markers, substeps=substeps)
        if substeps is not None and (len(substeps.chunks) != len(inputs["actions"])
                                     or any(chunk["substeps"] == 0 for chunk in substeps.chunks)):
            raise ValueError("Missing substep observations for a complete action")
        if bindings != bind_task(env, task["definition"]):
            raise ValueError("Native entity bindings changed during execution")
        status, phase = "completed", "terminal"
    except BaseException as error:
        receipt["error_type"] = type(error).__name__
        raise
    finally:
        try:
            arrays = {key: np.asarray(value) for key, value in rows.items()}
            arrays["initial"] = inputs["initial"]
            with (output / "trajectory.npz").open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            publish(output / "initialization.json", json_bytes(initialization))
            publish(output / "goals.json", json_bytes(events))
            publish(output / "visual-markers.json", json_bytes(markers))
            if substeps is not None:
                publish(output / "substeps.json", json_bytes({"schema_version": 1,
                        "substeps": substeps.substeps, "chunks": substeps.chunks,
                        "unflushed_substeps": len(substeps.rows), "active_action": substeps.action}))
            done = rows.get("done", [])
            final_time = float(env.sim.data.time) if env is not None else None
            if final_time is not None and not np.isfinite(final_time):
                receipt["invalid_final_time"] = repr(final_time)
                final_time = None
            receipt.update(status=status, phase=phase, actions_executed=len(rows.get("actions", [])),
                           native_success_any=bool(any(done)),
                           native_success_final=bool(done[-1]) if status == "completed" and done else None,
                           final_time_s=final_time,
                           wall_s=time.monotonic() - started,
                           files={str(p.relative_to(output)): file_hash(p)
                                  for p in sorted(output.rglob("*")) if p.is_file()})
            publish(output / "run.json", json_bytes(receipt))
        finally:
            if env is not None:
                env.close()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(json.loads(args.input.read_text()), args.output)
    print(json.dumps({key: result[key] for key in ("status", "task_id", "demo_id", "actions_executed")}))


if __name__ == "__main__":
    main()
