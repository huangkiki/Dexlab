"""Independently audit frozen landing records; never solve replacement forces."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from dexlab.landing_trace import align_states, contact_pairs


def load_arrays(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def collision_distances(model, qpos):
    """Minimum manifold distance by pair at a saved pose, without dynamics."""
    import mujoco

    data = mujoco.MjData(model)
    data.qpos[:] = qpos
    mujoco.mj_kinematics(model, data)
    mujoco.mj_collision(model, data)
    distances = {}
    for contact in data.contact:
        pair = tuple(sorted(map(int, contact.geom)))
        distances[pair] = min(distances.get(pair, np.inf), float(contact.dist))
    return distances


def audit(directory, protocol, *, geometry=False):
    """Return record integrity and contact evidence as separate conclusions."""
    directory = Path(directory)
    states = load_arrays(directory / "rollout.npz")
    native = load_arrays(directory / "contact_forces_200hz.npz")
    report = {
        "schema_version": 1,
        "state_alignment": align_states(
            states["states"], native, protocol["joint_names"], list(native["joint_names"])[1:],
            controls=protocol["control_steps"], substeps_per_control=protocol["substeps_per_control"],
            physics_dt=protocol["physics_dt_s"], state_tolerance=protocol["state_alignment_tolerance"]),
        "time_basis": "declared substep schedule; native clock and contact epoch require qualification",
        "native_pairs": "unavailable",
        "geometry_reconstruction": "not requested",
        "task_success": None,
        "causal_conclusion": "No solver-failure attribution follows from this audit alone.",
    }
    count = protocol["control_steps"] * protocol["substeps_per_control"]
    force = native["nonfoot_force"]
    counts = native["nonfoot_contacts"]
    if (force.shape != (count, 3) or not np.isfinite(force).all()
            or counts.shape != (count,) or counts.dtype.kind not in "iu" or np.any(counts < 0)):
        raise ValueError("Invalid complete nonfoot force/count records")
    report["recorded_nonfoot"] = {
        "loaded_pair_samples": np.flatnonzero(counts > 0).tolist(),
        "loaded_resultant_samples": np.flatnonzero(
            np.linalg.norm(force, axis=1) > protocol["loaded_pair_force_threshold_n"]).tolist(),
        "max_resultant_n": float(np.linalg.norm(force, axis=1).max()),
    }
    report["native_clock"] = "unavailable"
    if "native_time_before" in native and "native_time_after" in native:
        before, after = native["native_time_before"], native["native_time_after"]
        if (before.shape != (count,) or after.shape != (count,)
                or not np.isfinite(before).all() or not np.isfinite(after).all()):
            raise ValueError("Invalid native clock readback")
        report["native_clock"] = {
            "initial_time_s": float(before[0]), "final_time_s": float(after[-1]),
            "max_step_duration_error_s": float(np.max(np.abs(after - before - protocol["physics_dt_s"]))),
            "max_boundary_discontinuity_s": float(np.max(np.abs(before[1:] - after[:-1]))) if count > 1 else 0,
            "nonadvancing_substeps": np.flatnonzero(after <= before).tolist(),
            "contact_epoch": "A native clock alone does not timestamp the collision cache",
        }
    if "nonfoot_contact" in states:
        mask = states["nonfoot_contact"]
        if mask.dtype.kind != "b" or mask.shape != (protocol["control_steps"] + 1,):
            raise ValueError("Invalid upstream geometric classification")
        report["upstream_geometric_nonfoot_frames"] = np.flatnonzero(mask).tolist()
        report["upstream_geometric_source"] = "Author's stored classification, not an independent reconstruction"
    inputs = [directory / "rollout.npz", directory / "contact_forces_200hz.npz"]
    pair_path = directory / "native_contacts.npz"
    if pair_path.exists():
        metadata_path = directory / "native_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        pairs = load_arrays(pair_path)
        spans = contact_pairs(pairs["offsets"], pairs["pairs"], pairs["distances"], pairs["local_forces"],
                              steps=count, geom_count=len(metadata["geom_names"]))
        addresses = pairs["efc_address"]
        if addresses.shape != pairs["distances"].shape or addresses.dtype.kind not in "iu":
            raise ValueError("Invalid contact constraint addresses")
        if pairs["frames"].shape != (len(addresses), 3, 3) or not np.isfinite(pairs["frames"]).all():
            raise ValueError("Invalid native contact frames")
        report["native_pairs"] = {"contacts": int(len(addresses)), "complete_substeps": len(spans),
                                  "active_contacts": int(np.count_nonzero(addresses >= 0))}
        candidate_path = directory / "warp_candidates.npz"
        if not candidate_path.exists():
            raise ValueError("Native audit requires candidates retained before copy filtering")
        candidates = load_arrays(candidate_path)
        offsets = candidates["offsets"]
        if (offsets.shape != (count + 1,) or offsets.dtype.kind not in "iu" or offsets[0] != 0
                or np.any(offsets[1:] < offsets[:-1]) or offsets[-1] != len(candidates["dist"])):
            raise ValueError("Invalid complete candidate stream")
        candidate_count = int(offsets[-1])
        if candidates["dist"].shape != (candidate_count,):
            raise ValueError("Invalid candidate distances")
        for name, shape in (("geom", (candidate_count, 2)), ("type", (candidate_count,)),
                            ("worldid", (candidate_count,))):
            if candidates[name].shape != shape or candidates[name].dtype.kind not in "iu":
                raise ValueError(f"Invalid candidate {name}")
        if (not np.isfinite(candidates["dist"]).all() or np.any(candidates["geom"] < 0)
                or np.any(candidates["geom"] >= len(metadata["geom_names"]))
                or np.any(candidates["geom"][:, 0] == candidates["geom"][:, 1])
                or np.any(candidates["worldid"] != 0)):
            raise ValueError("Invalid candidate geometry or world")
        report["native_pairs"]["unfiltered_candidates"] = int(offsets[-1])
        types, frequencies = np.unique(candidates["type"], return_counts=True)
        report["native_pairs"]["candidate_type_counts"] = dict(zip(map(str, types), map(int, frequencies)))
        report["native_pairs"]["copy_filter"] = metadata["contact_copy_filter"]
        inputs += [pair_path, metadata_path]
        inputs.append(candidate_path)
        if geometry:
            model_path = directory / "native_model.mjb"
            report["geometry_reconstruction"] = reconstruct(
                native, pairs, spans, metadata, model_path, protocol, candidates=candidates)
            inputs.append(model_path)
    elif geometry:
        raise ValueError("Independent geometry comparison requires the native pair stream and model")
    report["input_sha256"] = {}
    for path in inputs:
        with path.open("rb") as stream:
            report["input_sha256"][path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
    return report


def reconstruct(native, pairs, spans, metadata, model_path, protocol, *, candidates=None):
    import mujoco

    if mujoco.__version__ != metadata["mujoco_version"]:
        raise ValueError("Geometry reconstruction requires the recorded MuJoCo version")
    model = mujoco.MjModel.from_binary_path(str(model_path))
    count = len(spans)
    for key in ("qpos", "pre_qpos"):
        if native[key].shape != (count, model.nq) or not np.isfinite(native[key]).all():
            raise ValueError(f"Invalid {key} for reconstruction")
    floor = set(metadata["floor"])
    feet = set().union(*map(set, metadata["feet"]))

    def nonfoot(pair):
        a, b = pair
        return (a in floor and b not in feet | floor) or (b in floor and a not in feet | floor)

    rows = []
    for step, span in enumerate(spans):
        pre = collision_distances(model, native["pre_qpos"][step])
        post = collision_distances(model, native["qpos"][step])
        distances = {}
        raw_distances, raw_types = {}, {}
        if candidates is not None:
            start, end = candidates["offsets"][step:step + 2]
            for pair, distance, kind in zip(candidates["geom"][start:end], candidates["dist"][start:end],
                                           candidates["type"][start:end]):
                pair = tuple(sorted(map(int, pair)))
                raw_distances[pair] = min(raw_distances.get(pair, np.inf), float(distance))
                raw_types.setdefault(pair, set()).add(int(kind))
        active = loaded = 0
        for pair, distance, address, force in zip(pairs["pairs"][span], pairs["distances"][span],
                                                  pairs["efc_address"][span], pairs["local_forces"][span]):
            pair = tuple(sorted(map(int, pair)))
            distances[pair] = min(distances.get(pair, np.inf), float(distance))
            if nonfoot(pair):
                active += int(address >= 0)
                loaded += int(np.linalg.norm(force[:3]) > protocol["loaded_pair_force_threshold_n"])
        # Only compare identical pairs. Absence is reported separately, never distance zero.
        errors = {}
        for epoch, reconstructed in (("pre", pre), ("post", post)):
            common = distances.keys() & reconstructed.keys()
            errors[epoch] = {
                "common_pairs": len(common),
                "native_only_pairs": [list(pair) for pair in sorted(distances.keys() - reconstructed.keys())],
                "reconstructed_only_pairs": [list(pair) for pair in sorted(reconstructed.keys() - distances.keys())],
                "max_distance_error_m": max((abs(distances[p] - reconstructed[p]) for p in common), default=None),
                "nonfoot_penetration_m": max((max(0, -d) for p, d in reconstructed.items() if nonfoot(p)), default=0),
            }
        nonfoot_pairs = sorted(pair for pair in pre.keys() | post.keys() | distances.keys() | raw_distances.keys()
                               if nonfoot(pair))
        rows.append({"substep": step + 1, "declared_post_time_s": float(native["time"][step]),
                     "native_nonfoot_active": active, "native_nonfoot_loaded": loaded,
                     "nonfoot_pairs": [{"pair": list(pair), "pre_distance_m": pre.get(pair),
                                        "post_distance_m": post.get(pair),
                                        "exported_distance_m": distances.get(pair),
                                        "raw_candidate_distance_m": raw_distances.get(pair),
                                        "raw_candidate_types": sorted(raw_types.get(pair, set()))}
                                       for pair in nonfoot_pairs], **errors})
    return {"method": "mj_kinematics + mj_collision; no forward dynamics or replacement force",
            "epoch_conclusion": "Compare pre/post distances and pair presence; do not infer epoch from array index alone",
            "substeps": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--geometry", action="store_true")
    args = parser.parse_args()
    protocol_bytes = args.protocol.read_bytes()
    report = audit(args.directory, json.loads(protocol_bytes), geometry=args.geometry)
    report["protocol_sha256"] = hashlib.sha256(protocol_bytes).hexdigest()
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
