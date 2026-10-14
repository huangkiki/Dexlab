"""Offline comparison of the native reference and public-UniSim pinch records.

This module never imports an engine or changes a score threshold. Contact
identity is matched by geometry and position before forces are compared.
"""
from __future__ import annotations

import math
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.adapter_qualification import compare_initial, numeric_error
from dexlab.genesis_pinch_score import score_force_record, score_trial

STATE_TOLERANCE = 1e-9
FORCE_TOLERANCE = 1e-7
TIME_TOLERANCE = 1e-12
STATE_FIELDS = ("q", "qvel", "object_pos", "object_quat", "object_vel", "object_ang")


def comparison_matrix(cases):
    """38 isolated launches; default entries contain four reset/replay episodes."""
    protocols = [(f"reset-{round(dt*1e6)}us", dt, None) for dt in (.001, .0005, .00025)]
    protocols += [(case['id'], .0005, case) for case in cases]
    return [dict(id=f'{name}-{route}', pair=name, route=route, dt_s=dt, case=case)
            for name, dt, case in protocols for route in ('native', 'unisim')]


def _array(value, shape, name, kind="f"):
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in kind or not np.isfinite(array).all():
        raise ValueError(f"Malformed contact {name}: expected {shape} / {kind}")
    return array


def contact_rows(record, initial, *, native):
    """Normalize explicit orientation and IDs, preserving every solved contact."""
    if native:
        raw = record["native"]
        if record["normal_orientation"] != "native B to A" or record["force_side"] != "B":
            raise ValueError("Unknown native contact convention")
        a, b = raw["geom_a"], raw["geom_b"]
        names = initial["reference_geometry_names"]
        forces = raw["force"]
        normals = -np.asarray(raw["normal"], dtype=float)
        distances = -np.asarray(raw["penetration"], dtype=float)
        positions = raw["position"]
    else:
        if record["available"] != [True] or any(record["env_ids"]):
            raise ValueError("Expected complete contact observations from exactly one world")
        a, b = record["geom_a"], record["geom_b"]
        names = initial["geom_names"]
        forces, normals = record["force_b"], record["normal"]
        distances, positions = record["signed_distance"], record["position"]
        if len(record["env_ids"]) != len(a):
            raise ValueError("Missing contact environment identities")
    count = len(a)
    a = _array(a, (count,), "geom_a", "iu") if count else np.empty(0, dtype=int)
    b = _array(b, (count,), "geom_b", "iu") if count else _array(b, (0,), "geom_b", "fiu")
    if np.any(a < 0) or np.any(b < 0):
        raise ValueError("Unbound geometry identity")
    if not native and count:
        _array(record["env_ids"], (count,), "env_ids", "iu")
    # Empty JSON arrays have no vector width; the declared zero-contact case is explicit.
    if count == 0:
        vectors = (forces, normals, distances, positions)
        if not native:
            vectors += (record["force_a"],)
        if any(np.asarray(value).size for value in vectors):
            raise ValueError("Stale vectors in an empty contact set")
        return []
    forces = _array(forces, (count, 3), "force")
    normals = _array(normals, (count, 3), "normal")
    positions = _array(positions, (count, 3), "position")
    distances = _array(distances, (count,), "distance")
    if not native:
        force_a = _array(record["force_a"], (count, 3), "force_a")
        if not np.array_equal(force_a, -forces):
            raise ValueError("Contact sides are not equal and opposite")
    result = []
    for i in range(count):
        left = names[str(int(a[i]))] if native else names[int(a[i])]
        right = names[str(int(b[i]))] if native else names[int(b[i])]
        if left == right:
            raise ValueError("A contact cannot reference one geometry twice")
        forward = left < right
        result.append({
            "pair": (left, right) if forward else (right, left),
            "position": positions[i], "distance": distances[i],
            "normal": normals[i] if forward else -normals[i],
            "force": forces[i] if forward else -forces[i],
        })
    return result


def compare_contacts(reference, candidate):
    """Match a one-to-one geometric ledger; never choose a match using force."""
    if len(reference) != len(candidate):
        raise ValueError("Contact count differs")
    remaining = list(candidate)
    maxima = dict(position=0., distance=0., normal=0., force=0.)
    for row in reference:
        matches = [i for i, other in enumerate(remaining)
                   if row["pair"] == other["pair"]
                   and np.max(np.abs(row["position"] - other["position"])) <= STATE_TOLERANCE]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous contact identity/position")
        other = remaining.pop(matches[0])
        for field in maxima:
            maxima[field] = max(maxima[field], float(np.max(np.abs(row[field] - other[field]))))
    return maxima


def compare_trial(reference, candidate, dt, *, case=None):
    """Check initial admission, every sample/epoch/contact and independent scores."""
    if dt not in (.001, .0005, .00025) or (case is not None and dt != .0005):
        raise ValueError("Unsupported comparison timestep")
    if (reference["condition"], reference["repeat"], reference.get("case_id")) != (
            candidate["condition"], candidate["repeat"], candidate.get("case_id")):
        raise ValueError("Mislabeled comparison trial")
    if case is not None and (reference.get("case_id") != case["id"]
                             or reference["condition"] != case["condition"]
                             or reference["repeat"] != 0):
        raise ValueError("Trial differs from frozen case identity")
    expected_count = round(4 / dt)
    if len(reference["samples"]) != expected_count or len(candidate["samples"]) != expected_count:
        raise ValueError("Incomplete comparison trajectory")
    admission = compare_initial(candidate["initial"], reference["initial"], storage_trial=True)
    failure = {} if admission["passed"] else {"initial": 0.}
    state_errors = {key: 0. for key in (*STATE_FIELDS, "command", "object_contact_force")}
    contact_errors = dict(position=0., distance=0., normal=0., force=0.)
    for index, (left, right) in enumerate(zip(reference["samples"], candidate["samples"], strict=True)):
        t = (index + 1) * dt
        for row in (left, right):
            if not math.isclose(row["time"], t, rel_tol=0, abs_tol=TIME_TOLERANCE):
                raise ValueError("Missing or mistimed state sample")
        for key in state_errors:
            error = numeric_error(right[key], left[key])
            state_errors[key] = max(state_errors[key], error)
            tolerance = (FORCE_TOLERANCE if key == "object_contact_force" else
                         TIME_TOLERANCE if key == "command" else STATE_TOLERANCE)
            if error > tolerance:
                failure.setdefault(key, t)
        for key, expected in (("state_time", t), ("geometry_time", index * dt),
                              ("force_start_time", index * dt), ("force_end_time", t)):
            for row in (left, right):
                epoch = row["complete_contacts"][key]
                if isinstance(epoch, list):
                    if len(epoch) != 1:
                        raise ValueError("Expected one contact epoch")
                    epoch = epoch[0]
                if numeric_error(epoch, expected) > TIME_TOLERANCE:
                    raise ValueError("Contact epoch differs from the frozen solve interval")
        try:
            errors = compare_contacts(
                contact_rows(left["complete_contacts"], reference["initial"], native=True),
                contact_rows(right["complete_contacts"], candidate["initial"], native=False))
            for key, error in errors.items():
                contact_errors[key] = max(contact_errors[key], error)
                if error > (FORCE_TOLERANCE if key == "force" else STATE_TOLERANCE):
                    failure.setdefault("contact_" + key, t)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            failure.setdefault("contact_identity: " + str(error), t)
    scores = [score_force_record(record, case) if case is not None else score_trial(record, dt)
              for record in (reference, candidate)]
    if scores[0]["checks"] != scores[1]["checks"]:
        failure["score_outcome"] = 0.
    if scores[0]["first_failure_time_s"] != scores[1]["first_failure_time_s"]:
        failure["score_failure_time"] = 0.
    # Equal trajectories must still satisfy the frozen numerical/physical gates.
    # Task failures (insufficient grip or failed release) remain measured outcomes.
    physical_checks = ("declared_import", "native_penetration_1mm",
                       "reference_table_penetration_1mm", "force_ledger",
                       "momentum_balance_5percent_weight")
    if case is not None:
        physical_checks += ("initial_rest_orientation", "box_inertia_and_friction")
    for score in scores:
        for key in physical_checks:
            if score["checks"].get(key) is not True:
                failure.setdefault("physical_validity_" + key,
                                   score["first_failure_time_s"].get(key, 0.))
    if not all(score["checks"]["declared_import"] for score in scores):
        failure["declared_import"] = 0.
    return {"passed": not failure, "initial": admission, "first_failure_time_s": failure,
            "state_max_absolute_errors": state_errors, "contact_max_absolute_errors": contact_errors,
            "native_score": scores[0], "candidate_score": scores[1]}


def read_recording(directory, case, source_sha256):
    """Bind a sealed recording to a predeclared acquisition source and case."""
    directory = Path(directory)
    protocol = json.loads((directory/'protocol.json').read_bytes())
    source = (directory/'runner.py').read_bytes()
    if (hashlib.sha256(source).hexdigest() != source_sha256
            or protocol['source_sha256'] != source_sha256):
        raise ValueError('Acquisition source does not match frozen manifest')
    trial = case['case']
    conditions = [trial['condition']] if trial else ['pinch', 'open_negative']
    repeats = 1 if trial else 2
    expected = dict(schema=2 if trial else 1, case=trial, engine='1.4.3',
                    dt_s=case['dt_s'], steps=round(4/case['dt_s']), duration_s=4,
                    mass_kg=.064, cube_size_m=.04, mu=.5, gravity_m_s2=9.81,
                    backend='cpu', precision='64', seed=0, repeats=repeats,
                    conditions=conditions, plane_cube_geom_timeconst_s=.002,
                    route='frozen_native_reference' if case['route'] == 'native' else case.get('recording_route', 'unisim_public_candidate'))
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise ValueError(f'Frozen protocol differs: {key}')
    if (case.get('matched_batched_info') and case['route'] == 'native'
            and protocol.get('batched_info') is not True):
        raise ValueError('Matched storage protocol requires an explicitly batched native reference')
    records = {}
    for condition in conditions:
        for repeat in range(repeats):
            name = f'{condition}-{repeat}'
            record = json.loads((directory/f'{name}.json').read_bytes())
            if (record['condition'] != condition or record['repeat'] != repeat
                    or record.get('case_id') != (trial['id'] if trial else None)):
                raise ValueError('Mislabeled migration recording')
            if case.get('matched_batched_info') and any(
                record['initial']['options'].get(key) is not True
                for key in ('batch_links_info', 'batch_dofs_info')
            ):
                raise ValueError('Native effective storage differs from the matched protocol')
            if case['route'] == 'unisim':
                reset = record['reset_contacts']
                if (reset['available'] != [False] or reset['env_ids'] != []
                        or reset['state_time'] != [0.]):
                    raise ValueError('Reset did not clear solved observations and clock')
            records[name] = record
    return records


def compare_recordings(native, candidate, case):
    """Physical equality and reset replay are separate from task success."""
    if native.keys() != candidate.keys():
        raise ValueError('Missing comparison trial')
    results = {key: compare_trial(native[key], candidate[key], case['dt_s'], case=case['case'])
               for key in native}
    reset = {}
    if case['case'] is None:
        for route, records in (('native', native), ('unisim', candidate)):
            for condition in ('pinch', 'open_negative'):
                reset[f'{route}-{condition}'] = (
                    records[f'{condition}-0']['samples'] == records[f'{condition}-1']['samples'])
    return {'passed': all(row['passed'] for row in results.values()) and all(reset.values()),
            'trials': results, 'exact_reset_replay': reset}
