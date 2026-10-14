"""Validate complete version-2 native records and independently score substeps.

The caller pins both the execution request and a numerical protocol before
outcomes. Receipt hashes prove identity; the checks below separately establish
cross-channel completeness and calculate numerical residuals. Physical-reference
validity, joint reactions and learned-policy performance remain separate.
"""

import argparse
import io
import json
from pathlib import Path

import numpy as np

from dexlab.libero_bindings import JOINT_LAYOUT
from dexlab.libero_body_dynamics import body_accounting, free_com_balance, solver_observation
from dexlab.libero_demo import load_demo
from dexlab.libero_dynamics import diagnostics
from dexlab.libero_execute import validate_numerical_environment
from dexlab.libero_goals import goal_atoms
from dexlab.libero_initialization import INITIALIZATION_CONTRACT
from dexlab.libero_substeps import read_chunk
from dexlab.libero_workflow import file_hash
from dexlab.migration_budget import json_bytes, publish


METRICS = {"smooth_force", "actuator_transmission", "smooth_acceleration",
           "constrained_acceleration", "constraint_transmission", "euler_velocity",
           "euler_position", "contact_wrench"}
BODY_METRICS = {"spatial_inertia", "spatial_velocity", "projected_body_effort"}
COMMON_FILES = {"input.json", "task.json", "assets.json", "input-model.xml", "relocated-model.xml",
                "effective-model.xml", "bindings.json", "initialization.json", "trajectory.npz",
                "goals.json", "visual-markers.json", "physics-model.json", "substeps.json"}
# Independent float64 normalization may round differently from native scalar sums.
# This applies ONLY to quaternion normalization, never general state continuity.
QUAT_NORMALIZATION_ATOL = 32 * np.finfo(np.float64).eps


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _equal(actual, expected, name):
    _require(np.array_equal(actual, expected), "Inconsistent " + name)


def _numeric(value, shape, name, kind="fiu"):
    array = np.asarray(value)
    _require(array.shape == shape and array.dtype.kind in kind and np.isfinite(array).all(),
             "Malformed or non-finite " + name)
    return array


def _file(root, name):
    relative = Path(name)
    _require(not relative.is_absolute() and relative.as_posix() == name and ".." not in relative.parts,
             "Invalid record path")
    path = root / relative
    _require(path.resolve(strict=True).is_relative_to(root), "Record path escapes run directory")
    return path


def _state_link(before, after, model):
    """Permit only the native forward quaternion normalization between steps."""
    nq, nv = model["dimensions"]["nq"], model["dimensions"]["nv"]
    before = _numeric(before, (1 + nq + nv,), "preceding state")
    after = _numeric(after, before.shape, "following state")
    expected, mask = before.copy(), np.zeros(len(before), bool)
    for kind, address in zip(model["arrays"]["jnt_type"], model["arrays"]["jnt_qposadr"]):
        if kind in (0, 1):
            start = 1 + address + (3 if kind == 0 else 0)
            quaternion = before[start:start + 4]
            norm = np.linalg.norm(quaternion)
            _require(norm > 0, "Degenerate quaternion in state chain")
            expected[start:start + 4] = quaternion / norm
            mask[start:start + 4] = True
    _equal(after[~mask], before[~mask], "state continuity outside quaternion normalization")
    _require(np.allclose(after[mask], expected[mask], rtol=0, atol=QUAT_NORMALIZATION_ATOL),
             "State discontinuity exceeds quaternion normalization")


def _controller_initialization(init, run, expected, model):
    """Validate the new restoration contract without reinterpreting old records."""
    dims = model["dimensions"]
    contract = expected.get("initialization_contract")
    if contract is None:
        _require("initialization_contract" not in run and "contract" not in init,
                 "Historical initialization cannot be relabelled as a new contract")
        return
    _require(contract == INITIALIZATION_CONTRACT == run.get("initialization_contract") == init.get("contract"),
             "Unfrozen or unsupported controller initialization contract")
    _equal(init["after_controller_goals"], init["after_forward"], "controller goal reset state")
    controller = init["controller"]
    _require(controller["name"] == "OSC_POSE", "Unsupported restored controller")
    for key in ("joint_ids", "qpos_indices", "qvel_indices"):
        _numeric(controller[key], (7,), key, "iu")
    site = controller["eef_site_id"]
    _require(type(site) is int and 0 <= site < dims["nsite"]
             and model["names"]["site"][site] == "gripper0_grip_site", "Restored end-effector site identity")
    joint_ids = [model["names"]["joint"].index(f"robot0_joint{i}") for i in range(1, 8)]
    _equal(controller["joint_ids"], joint_ids, "Panda arm joint identity")
    _require(all(model["arrays"]["jnt_type"][i] == 3 for i in joint_ids), "Panda arm joint type")
    q = [model["arrays"]["jnt_qposadr"][i] for i in joint_ids]
    v = [model["arrays"]["jnt_dofadr"][i] for i in joint_ids]
    _equal(controller["qpos_indices"], q, "controller qpos indices")
    _equal(controller["qvel_indices"], v, "controller velocity indices")
    before, after, native = controller["before"], controller["after"], controller["native_after"]
    state = np.asarray(init["after_forward"])
    _equal(after["joint_pos"], state[1:1 + dims["nq"]][q], "restored joint cache")
    _equal(after["joint_vel"], state[1 + dims["nq"]:][v], "restored velocity cache")
    shapes = {"joint_pos": (7,), "joint_vel": (7,), "initial_joint": (7,),
              "ee_pos": (3,), "ee_ori_mat": (3, 3), "goal_pos": (3,), "goal_ori": (3, 3)}
    for snapshot in (before, after):
        for key, shape in shapes.items():
            _numeric(snapshot[key], shape, "controller memory: " + key)
        action = np.asarray(snapshot["gripper_current_action"])
        _require(action.shape in ((1,), (2,)) and np.isfinite(action).all(), "Invalid gripper memory")
        _require(type(snapshot["new_update"]) is bool, "Invalid native controller update flag")
    _require(after["new_update"] is False, "Native OSC refresh did not finish")
    for key in ("joint_pos", "joint_vel", "ee_pos", "ee_ori_mat"):
        _equal(after[key], native[key], "native controller readback: " + key)
    for goal, pose in (("goal_pos", "ee_pos"), ("goal_ori", "ee_ori_mat")):
        _equal(after[goal], after[pose], "restored controller goal: " + goal)
    for key in ("initial_joint", "gripper_current_action"):
        _equal(before[key], after[key], "retained native reset history: " + key)


def validate_bindings(binding, model, definition):
    """Check every entity/joint/site against the recorded native model tables."""
    dims, arrays, names = model["dimensions"], model["arrays"], model["names"]
    for size in ("nq", "nv", "na", "nM", "nbody", "ngeom", "nsite", "njnt", "nu", "ntendon", "neq"):
        _require(type(dims[size]) is int and dims[size] >= 0, "Invalid model dimension")
    _require(dims["nbody"] > 0 and dims["na"] == 0, "Unsupported flat native model state")
    for kind, size in (("body", "nbody"), ("joint", "njnt"), ("geom", "ngeom"), ("site", "nsite")):
        _require(len(names[kind]) == dims[size], "Incomplete model name table")
    parents = _numeric(arrays["body_parentid"], (dims["nbody"],), "body parents", "iu")
    _require(parents[0] == 0 and np.all(parents[1:] >= 0)
             and np.all(parents[1:] < np.arange(1, dims["nbody"])), "Invalid body topology")
    for kind, count in (("geom", "ngeom"), ("site", "nsite"), ("jnt", "njnt")):
        ids = np.asarray(arrays[kind + "_bodyid"], dtype=int) if not dims[count] else _numeric(
            arrays[kind + "_bodyid"], (dims[count],), kind + " ownership", "iu")
        _require(ids.shape == (dims[count],) and np.all((ids >= 0) & (ids < dims["nbody"])),
                 "Invalid native body ownership")
    _require(binding["schema_version"] == 2 and binding["goal"] == definition["goal"]
             and binding["objects_of_interest"] == definition["objects_of_interest"], "Task binding declaration changed")
    _require(binding["model_dimensions"] == {key: dims[key] for key in ("nbody", "njnt", "nq", "nv", "nsite", "ngeom")},
             "Binding/model dimensions disagree")
    entities = binding["entities"]
    _require(set(entities) == set(definition["objects"]) | set(definition["fixtures"]) | set(definition["regions"]),
             "Missing or unexpected task entity")
    atoms = goal_atoms(definition)
    required = set(definition["objects_of_interest"]) | {name for atom in atoms for name in atom[1:]}
    occupied = set()
    for name in set(definition["objects"]) | set(definition["fixtures"]):
        entry = entities[name]
        kind = entry["kind"]
        _require(entry["status"] == "bound" and (kind == "object" if name in definition["objects"]
                 else kind in ("fixture", "arena")), "Missing physical entity binding")
        body = entry["body_id"]
        _require(type(body) is int and 0 < body < dims["nbody"] and names["body"][body] == entry["body_name"],
                 "Body name/id mapping changed")
        descendants = {body}
        for index in range(body + 1, dims["nbody"]):
            if parents[index] in descendants:
                descendants.add(index)
        _require(entry["body_ids"] == sorted(descendants) and not occupied.intersection(descendants),
                 "Missing or aliased entity bodies")
        occupied.update(descendants)
        _require(entry["geom_ids"] == [i for i, owner in enumerate(arrays["geom_bodyid"]) if owner in descendants],
                 "Geometry ownership changed")
        expected_joints = []
        for joint, owner in enumerate(arrays["jnt_bodyid"]):
            if owner not in descendants:
                continue
            kind, nq, nv = JOINT_LAYOUT[arrays["jnt_type"][joint]]
            qa, va = arrays["jnt_qposadr"][joint], arrays["jnt_dofadr"][joint]
            expected_joints.append({"joint_id": joint, "joint_name": names["joint"][joint], "type": kind,
                                    "body_id": owner, "qpos_indices": list(range(qa, qa + nq)),
                                    "dof_indices": list(range(va, va + nv))})
        _require(entry["joints"] == expected_joints, "Missing or incorrect joint observations")
        query = entry["query_joint_ids"]
        _require(len(set(query)) == len(query) and set(query) <= {j["joint_id"] for j in expected_joints},
                 "Invalid native query joint mapping")
    for name, region in definition["regions"].items():
        entry = entities[name]
        _require(entry["kind"] == "region" and entry["declared_target"] == region["target"], "Region target changed")
        if entry["status"] != "bound":
            allowed = "not-materialized" if region["target_declared"] else "unresolved-source-target"
            _require(name not in required and entry["status"] == allowed, "Required region is unbound")
            continue
        site, body = entry["site_id"], entry["body_id"]
        _require(type(site) is int and 0 <= site < dims["nsite"] and names["site"][site] == name == entry["site_name"],
                 "Region site mapping changed")
        _require(arrays["site_bodyid"][site] == body and names["body"][body] == entry["body_name"]
                 and body in entities[region["target"]]["body_ids"], "Region ownership changed")
        ancestors, ancestor = {body}, body
        while ancestor:
            ancestor = int(parents[ancestor]); ancestors.add(ancestor)
        query = entry["query_joint_ids"]
        _require(len(set(query)) == len(query) and all(type(j) is int and 0 <= j < dims["njnt"]
                 and arrays["jnt_bodyid"][j] in ancestors for j in query), "Invalid region query joints")
    _require(all(entities[name]["status"] == "bound" for name in required), "Unbound task goal/interest")
    for atom in atoms:
        if atom[0] in ("open", "close", "turnon", "turnoff"):
            _require(bool(entities[atom[1]]["query_joint_ids"]), "Articulated goal has no query joint")


def _goals(events, ranges, intervals, done, definition):
    atoms, offset = goal_atoms(definition), 0
    for action, (begin, end) in enumerate(ranges):
        _require(begin == offset and begin < end <= len(events), "Dropped or extra native goal queries")
        for index in range(begin, end):
            event = events[index]
            _require(event["check_index"] == index and event["status"] == "completed", "Incomplete goal query")
            _require(event["time_s"] == event["time_after_s"] == intervals[action, 1], "Stale goal epoch")
            queries = event["queries"]
            _require(len(queries) == len(atoms), "Missing secondary goal")
            for goal_index, (query, atom) in enumerate(zip(queries, atoms)):
                _require(query["goal_index"] == goal_index and query["predicate"] == atom
                         and type(query["value"]) is bool, "Goal order/arguments changed")
            _require(type(event["native_success"]) is bool
                     and event["native_success"] == all(q["value"] for q in queries), "Contradictory native goal conjunction")
        _require(bool(done[action]) == events[end - 1]["native_success"], "Action success disagrees with native goals")
        offset = end
    _require(offset == len(events), "Unassigned goal queries")


def _protocol(protocol, model):
    version = model["schema_version"]
    equations = {1: "mujoco-2.3.7-euler-v1", 2: "mujoco-2.3.7-euler-body-v2"}
    _require(version in equations and protocol["schema_version"] == version and protocol["equations"] == equations[version],
             "Unsupported numerical protocol")
    _require(set(protocol["absolute_tolerances"]) == (METRICS | BODY_METRICS if version == 2 else METRICS),
             "Missing numerical metric tolerance")
    tolerances = {}
    for name, value in protocol["absolute_tolerances"].items():
        size = 6 if name == "contact_wrench" else model["dimensions"]["nq" if name == "euler_position" else "nv"]
        if name in ("spatial_inertia", "spatial_velocity"):
            size = model["dimensions"]["nbody"] * (10 if name == "spatial_inertia" else 6)
        limit = _numeric(value, (size,), "per-coordinate tolerance: " + name)
        _require(np.all(limit > 0), "Tolerances must be positive and frozen per coordinate")
        tolerances[name] = limit
    _require(isinstance(protocol["observations"], dict) and protocol["observations"], "Missing observation contract")
    return tolerances


def score_run(directory, receipt_sha256, expected, inputs_directory, protocol):
    """Score a complete instrumented run against external input and protocol pins.

    Structural contradictions raise ValueError. Numerical departures remain a
    separately labelled result with every affected action retained; they do not
    by themselves establish whether a recorder or the model caused the error.
    """
    root = Path(directory).resolve(strict=True)
    _require(file_hash(root / "run.json") == receipt_sha256, "Run receipt differs from external hash")
    run = json.loads((root / "run.json").read_bytes())
    _require(run["schema_version"] == 2 and run["status"] == "completed" and run["phase"] == "terminal",
             "Incomplete native run")
    _require(expected["recording"] is True and expected.get("substep_recording") is True
             and run["recording"] is True and run.get("substep_recording") is True,
             "Complete substep scoring requires the instrumented path")
    files = run["files"]
    _require(COMMON_FILES <= set(files) and "run.json" not in files, "Missing required native artifacts")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {"run.json"}
    _require(actual == set(files), "Run file manifest is incomplete or contains extras")
    for name, digest in files.items():
        _require(file_hash(_file(root, name)) == digest, "Changed native artifact: " + name)
    read = lambda name: json.loads(_file(root, name).read_bytes())
    _require(read("input.json") == expected, "Execution differs from externally frozen request")
    inputs = load_demo(inputs_directory, expected["input_manifest_sha256"], expected["demo_id"])
    _require(read("task.json") == inputs["task"] and run["task_id"] == expected["task_id"] == inputs["task"]["task_id"],
             "Task identity changed")
    _require(run["demo_id"] == expected["demo_id"] and run["input_manifest_sha256"] == expected["input_manifest_sha256"]
             and run["source_sha256"] == expected["source_sha256"] and run["versions"] == expected["runtime_versions"],
             "Runtime, source or input identity changed")
    if "numerical_environment" in expected:
        validate_numerical_environment(expected["numerical_environment"])
        _require(run.get("numerical_environment") == expected["numerical_environment"],
                 "Numerical environment differs from frozen execution")
    split = inputs["demonstration"]["split"]
    _require(run["purpose"] == expected["purpose"] and run["input_split"] == split
             and (expected["purpose"] == "baseline" or expected["purpose"] == split), "Demonstration split violated")
    instruction = {**inputs["admission"]["linkage"]["language"], "native_contract": "pinned-bddl", "policy_used": False}
    _require(run["instruction"] == instruction, "Instruction provenance changed")
    _require((root / "input-model.xml").read_text() == inputs["model_xml"], "Source model identity changed")
    model, binding = read("physics-model.json"), read("bindings.json")
    validate_bindings(binding, model, inputs["task"]["definition"])
    tolerances = _protocol(protocol, model)
    dims = model["dimensions"]
    dt, control = float(run["model_timestep"]), float(run["control_timestep"])
    _require(np.isfinite([dt, control, run["control_freq"]]).all() and dt > 0 and control >= dt
             and dt == model["options"]["timestep"] and control == 1 / run["control_freq"], "Invalid control/substep timing")
    per_action = int(control / dt)  # Pinned native robosuite stepping contract.
    _require(protocol["substeps_per_action"] == per_action, "Unfrozen or changed substep count")
    n = inputs["demonstration"]["action_count"]
    _require(type(n) is int and n > 0 and run["expected_actions"] == run["actions_executed"] == n,
             "Truncated action denominator")
    init = read("initialization.json")
    _require(init["status"] == "completed" and init["phase"] == "ready-for-actions"
             and init["model_dimensions"] == {k: dims[k] for k in ("nq", "nv", "na")}, "Invalid initialization")
    _equal(init["source"], inputs["initial"], "initial source")
    _equal(init["after_set"], inputs["initial"], "single source restore")
    _state_link(init["source"], init["after_forward"], model)
    _equal(init["expected_after_forward"], init["after_forward"], "forward initialization")
    _equal(init["after_post"], init["after_forward"], "post-processing state")
    _equal(init["normalized_indices"], np.flatnonzero(np.asarray(init["source"]) != init["after_forward"]), "normalization indices")
    _controller_initialization(init, run, expected, model)
    _require(run["initial_time_s"] == init["after_post"][0], "Initial epoch changed")
    with np.load(io.BytesIO((root / "trajectory.npz").read_bytes()), allow_pickle=False) as data:
        _require(len(data.files) == len(set(data.files)), "Duplicate trajectory member")
        trajectory = {key: data[key] for key in data.files}
    _equal(trajectory["initial"], inputs["initial"], "trajectory source initial state")
    _equal(trajectory["actions"], inputs["actions"], "complete admitted actions")
    shapes = {"actions": (n, 7), "state": (n, 1 + dims["nq"] + dims["nv"]), "time": (n,),
              "action_interval": (n, 2), "reward": (n,), "done": (n,), "ctrl": (n, dims["nu"]),
              "actuator_force": (n, dims["nu"]), "qfrc_actuator": (n, dims["nv"]),
              "body_xpos": (n, dims["nbody"], 3), "body_xquat": (n, dims["nbody"], 4),
              "body_xipos": (n, dims["nbody"], 3), "site_rgba": (n, dims["nsite"], 4), "goal_event_range": (n, 2)}
    _require(set(trajectory) == set(shapes) | set(protocol["observations"]) | {"initial"}, "Missing or unexpected observation channel")
    for key, shape in shapes.items():
        _numeric(trajectory[key], shape, key, "b" if key == "done" else "iu" if key == "goal_event_range" else "fiu")
    for key, contract in protocol["observations"].items():
        _require(key.startswith("obs:"), "Invalid frozen observation channel")
        _numeric(trajectory[key], (n, *contract["shape"]), key)
        _require(trajectory[key].dtype.str == contract["dtype"], "Observation dtype changed")
    intervals = trajectory["action_interval"]
    _equal(trajectory["time"], intervals[:, 1], "action times")
    _equal(trajectory["state"][:, 0], trajectory["time"], "state times")
    _goals(read("goals.json"), trajectory["goal_event_range"], intervals, trajectory["done"], inputs["task"]["definition"])
    _require(len(read("visual-markers.json")) == n, "Truncated visual marker history")
    _require(type(run["native_success_any"]) is bool and type(run["native_success_final"]) is bool
             and run["native_success_any"] == bool(np.any(trajectory["done"]))
             and run["native_success_final"] == bool(trajectory["done"][-1]), "Native success summary contradiction")
    index = read("substeps.json")
    _require(index["schema_version"] == 1 and index["active_action"] is None and index["unflushed_substeps"] == 0
             and len(index["chunks"]) == n and index["substeps"] == n * per_action, "Incomplete substep index")
    _require(set(files) == COMMON_FILES | {f"substeps/action-{a:06d}.npz" for a in range(n)}, "Missing or extra substep chunks")
    sequence, previous = 0, np.asarray(init["after_post"])
    maxima = {key: np.zeros_like(value) for key, value in tolerances.items()}
    actions, total_contacts = [], 0
    body_observation = model["schema_version"] == 2
    for action, chunk in enumerate(index["chunks"]):
        name = f"action-{action:06d}.npz"
        _require(chunk == {"name": name, "action_index": action, "substeps": per_action}, "Substep chunk/action mapping changed")
        records = read_chunk(_file(root, "substeps/" + name))
        _require(len(records) == per_action, "Truncated substeps within action")
        _require(intervals[action, 0] == previous[0], "Gap in action epochs")
        action_max = {key: np.zeros_like(value) for key, value in tolerances.items()}
        violations = {key: 0 for key in tolerances}
        body_max = np.zeros((dims["nbody"], 6))
        com_max, solver_counts = {}, []
        for row in records:
            _require(type(row["sequence"]) is int and row["sequence"] == sequence
                     and type(row["action_index"]) is int and row["action_index"] == action, "Missing or reordered substep")
            before, after = row["state_before"], row["state_after"]
            _state_link(previous, np.r_[before["time"], before["qpos"], before["qvel"]], model)
            residuals = diagnostics(model, row)
            if body_observation:
                solver_counts.append(solver_observation(model, row)["iterations"])
                bodies = body_accounting(model, row)
                residuals.update({key: value.reshape(-1) for key, value in bodies["residuals"].items()})
                body_max = np.maximum(body_max, np.abs(bodies["inferred_net_subtree_wrench"]))
                for balance in free_com_balance(model, row, bodies):
                    body = balance["body"]
                    summary = com_max.setdefault(body, {key: balance[key] for key in ("body", "joint", "status")})
                    if balance["status"] == "diagnostic-only":
                        summary["abs_max_N_s"] = np.maximum(summary.get("abs_max_N_s", np.zeros(3)), np.abs(balance["residual_N_s"])).tolist()
                    else:
                        summary["reason"] = balance["reason"]
            for key, residual in residuals.items():
                _require(np.isfinite(residual).all(), "Non-finite derived numerical residual: " + key)
                value = np.max(np.abs(residual), axis=0, initial=0) if key == "contact_wrench" else np.abs(residual)
                action_max[key] = np.maximum(action_max[key], value)
                violations[key] += int(np.any(value > tolerances[key]))
            total_contacts += len(row["force"]["contacts"])
            previous = np.r_[after["time"], after["qpos"], after["qvel"]]
            sequence += 1
        _equal(previous, trajectory["state"][action], "action terminal state")
        for key in ("ctrl", "actuator_force", "qfrc_actuator"):
            _equal(records[-1]["force"][key], trajectory[key][action], "action force readback: " + key)
        for native, key in (("xpos", "body_xpos"), ("xquat", "body_xquat"), ("xipos", "body_xipos")):
            _equal(records[-1]["force"][native], trajectory[key][action], "action body readback: " + key)
        for key, value in action_max.items():
            maxima[key] = np.maximum(maxima[key], value)
        actions.append({"action_index": action, "abs_max": {k: v.tolist() for k, v in action_max.items()},
                        "violating_substeps": violations})
        if body_observation:
            actions[-1].update(inferred_net_subtree_wrench_abs_max=body_max.tolist(),
                               free_com=list(com_max.values()), solver_iterations=solver_counts)
    _require(previous[0] == run["final_time_s"], "Run final epoch differs from complete substeps")
    return {"schema_version": 2, "record_valid": True, "actions": n, "substeps": sequence,
            "contacts_checked": total_contacts, "native_success": bool(trajectory["done"][-1]),
            "numerical_consistent": not any(count for action in actions for count in action["violating_substeps"].values()),
            "abs_max": {k: v.tolist() for k, v in maxima.items()}, "action_diagnostics": actions,
            "run_sha256": receipt_sha256, "protocol": protocol,
            "numerical_environment": run.get("numerical_environment"),
            "body_observation_schema": model["schema_version"] if body_observation else None,
            "free_com_reference_qualification": "pending", "solver_termination_reason": "not-exposed-by-native-api",
            "physical_reference": "not-evaluated", "joint_reaction_qualification": "pending",
            "scope": "Complete recorded sequence and per-coordinate numerical diagnostics; not physical validity or learned-policy evaluation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("directory", "receipt_sha256", "expected", "inputs_directory", "protocol", "output"):
        parser.add_argument(name)
    args = parser.parse_args()
    result = score_run(args.directory, args.receipt_sha256, json.loads(Path(args.expected).read_text()),
                       args.inputs_directory, json.loads(Path(args.protocol).read_text()))
    publish(Path(args.output), json_bytes(result))
    print(json.dumps({key: result[key] for key in ("record_valid", "actions", "substeps", "numerical_consistent")}))


if __name__ == "__main__":
    main()
