#!/usr/bin/env python3
"""Verify the seed-137 hand-contact negative's initial state and physical model."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.amp_lift_audit import compare_probe_values
from dexlab.libero_substeps import read_chunk


def compare_pair(reference, negative, protocol):
    manifests = [json.loads((path / "invocation.json").read_text()) for path in (reference, negative)]
    metadata = [json.loads((path / "native/recording.json").read_text()) for path in (reference, negative)]
    for manifest, case in zip(manifests, ("policy-seed-137", "no-hand-seed-137")):
        if manifest["status"] != "completed" or manifest["case"] != next(c for c in protocol["cases"] if c["id"] == case) or \
                manifest["completed_actions"] != manifest["case"]["actions"]:
            raise ValueError("Pairing requires the two complete frozen seed-137 cases")
    for key in ("source", "runtime", "native_payload", "runner_sha256", "recorder_sha256", "protocol_sha256"):
        if manifests[0][key] != manifests[1][key]:
            raise ValueError(f"Negative/reference identity mismatch: {key}")
    for key in ("options", "time_dtype", "force_decoder_sha256", "body_names", "geom_names",
                "joint_names", "site_names", "actuator_names"):
        if metadata[0][key] != metadata[1][key]:
            raise ValueError(f"Negative/reference compiled metadata mismatch: {key}")
    a, b = [read_chunk(path / "initial-state.npz") for path in (reference, negative)]
    if len(a) != 1 or len(b) != 1:
        raise ValueError("Missing paired initial state")
    initial_error = compare_probe_values(a[0], b[0], atol=protocol["checks"]["state_parity_atol"],
                                         rtol=protocol["checks"]["state_parity_rtol"], path="paired initial state")
    names = metadata[0]["geom_names"]
    hands = [names.index(f"robot/{side}_{part}_collision")
             for side in ("left", "right") for part in ("hand", "wrist")]
    with np.load(reference / "native/effective-model.npz", allow_pickle=False) as a, \
            np.load(negative / "native/effective-model.npz", allow_pickle=False) as b:
        if set(a.files) != set(b.files):
            raise ValueError("Paired model fields differ")
        # These are compiler-generated collision candidates. Removing the four
        # geometries legitimately changes their extent; do not compare IDs from
        # different candidate lists as if they were invariant physics fields.
        generated = {"nxn_geom_pair", "nxn_pairid"}
        checked = []
        for key in a.files:
            if key in generated:
                continue
            expected = a[key].copy()
            if key in ("geom_contype", "geom_conaffinity"):
                if expected.shape == (1, len(names)):
                    expected[0, hands] = 0
                elif expected.shape == (len(names),):
                    expected[hands] = 0
                else:
                    raise ValueError("Unexpected compiled collision-mask layout")
            compare_probe_values(expected, b[key], atol=0., rtol=0., path=f"paired model.{key}")
            checked.append(key)
        if np.isin(b["pair_geom1"], hands).any() or np.isin(b["pair_geom2"], hands).any():
            raise ValueError("An explicit contact pair bypasses the negative's hand masks")
    evidence = {}
    for label, directory in (("reference", reference), ("negative", negative)):
        evidence[label] = {}
        for name in ("invocation.json", "initial-state.npz", "native/recording.json", "native/effective-model.npz"):
            with (directory / name).open("rb") as stream:
                evidence[label][name] = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"passed": True, "maximum_initial_component_error": initial_error,
            "physical_fields_checked": checked, "generated_collision_fields_excluded": sorted(generated),
            "hand_geom_ids": hands, "task_success": None, "evidence_sha256": evidence,
            "scope": "Initial-state and effective physical-parameter pairing; trajectory outcomes remain separate."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--negative", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(Path(__file__).with_name("protocol.json").read_text())
    result = compare_pair(args.reference, args.negative, protocol)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(args.output)


if __name__ == "__main__":
    main()
