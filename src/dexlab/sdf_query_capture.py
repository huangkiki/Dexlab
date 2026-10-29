"""Candidate capture order for the frozen synthetic box, not native qualification.

The caller owns official-runtime admission, actor creation, finite budgets and
binding the raw directory to its frozen protocol. This function does not prove
that an object implementing the API is an authentic native actor.
"""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from dexlab.contact_transfer import box_mesh_matches

from dexlab.sdf_query_domain import classify_actor_domain
from dexlab.sdf_near_surface import HALF_SIZE, TRANSLATION, query_cohort, score_queries


COORDINATE_GUARD_M = 1e-12
EXPECTED_ROTATION_XYZW = np.array([0, 0, np.sin(.35), np.cos(.35)])


def _write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, allow_nan=False, indent=2, sort_keys=True)
        stream.write("\n")


def _snapshot(actor):
    transform = actor.get_root_transform()
    bounds = actor.get_aabb_local()
    mesh = actor.get_mesh()
    return {
        "name": actor.get_name(),
        "collider_type": actor.get_collider_type().name,
        "has_root_transform": actor.has_root_transform(),
        "translation_m": np.asarray(transform.translation).copy(),
        "rotation_xyzw": np.asarray(transform.rotation).copy(),
        "bounds_local_m": np.array([bounds.min, bounds.max]),
        "vertices_m": np.asarray(mesh.coordinates).copy().reshape(-1, 3),
        "faces": np.asarray(mesh.connectivity).copy().reshape(-1, 3),
        "nodes_per_element": mesh.nodes_per_element,
    }


def _json_snapshot(snapshot):
    return {key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in snapshot.items()}


def capture_box_queries(actor, output, *, expected_name, vertices_m, faces):
    """Save pre-query identity and mask, then retain query results and recheck.

    Only the existing fixed 40x30x20 mm box cohort is supported. Input geometry
    must be independently bound to the frozen source by the caller. No step,
    actor mutation, runtime import, automatic retry or threshold tuning occurs.
    The supplied actor is queried exactly once. Mock/API-shaped objects are
    useful for ordering tests, but their files are not native evidence.
    """
    output = Path(output)
    output.mkdir(exist_ok=False)
    stage = "source-geometry"
    try:
        vertices_m, faces = np.asarray(vertices_m), np.asarray(faces)
        if (vertices_m.dtype.kind not in "fiu" or faces.dtype.kind not in "iu"
                or not box_mesh_matches(vertices_m / HALF_SIZE, faces, 1)):
            raise ValueError("Source must be the closed, outward-oriented fixed box")
        stage = "identity-before-query"
        cohort = query_cohort()
        before = _snapshot(actor)
        _write_json(output / "before.json", _json_snapshot(before))
        if (before["name"] != expected_name or before["collider_type"] != "SDF"
                or before["has_root_transform"] is not True
                or before["nodes_per_element"] != 3):
            raise ValueError("Actor name, collider, root or mesh kind mismatch")
        if (not np.array_equal(before["vertices_m"], vertices_m)
                or not np.array_equal(before["faces"], faces)):
            raise ValueError("Actor geometry differs from the frozen source arrays")
        domain = classify_actor_domain(
            cohort["world_m"], translation_m=before["translation_m"],
            rotation_xyzw=before["rotation_xyzw"],
            bounds_local_m=before["bounds_local_m"],
            coordinate_guard_m=COORDINATE_GUARD_M,
        )
        if (not np.allclose(before["translation_m"], TRANSLATION, rtol=0, atol=1e-12)
                or min(np.max(np.abs(before["rotation_xyzw"] - EXPECTED_ROTATION_XYZW)),
                       np.max(np.abs(before["rotation_xyzw"] + EXPECTED_ROTATION_XYZW))) > 1e-12):
            raise ValueError("Actor pose differs from the frozen box cohort")
        lower, upper = before["bounds_local_m"]
        if np.any(before["vertices_m"] < lower - 1e-12) or np.any(before["vertices_m"] > upper + 1e-12):
            raise ValueError("Actor AABB does not contain its source mesh")
        if not np.allclose(domain["local_m"], cohort["local_m"], rtol=0, atol=1e-12):
            raise ValueError("Native pose does not recover the fixed query frame")
        np.savez(output / "before.npz", world_m=cohort["world_m"],
                 reference_local_m=cohort["local_m"],
                 coordinate_guard_m=np.array(COORDINATE_GUARD_M), **domain)
        before_hashes = {name: sha256((output / name).read_bytes()).hexdigest()
                         for name in ("before.json", "before.npz")}
        _write_json(output / "before-manifest.json", before_hashes)
        manifest_hash = sha256((output / "before-manifest.json").read_bytes()).hexdigest()

        stage = "distance-query"
        distances = np.full(len(cohort["world_m"]), np.nan, dtype=np.float64)
        try:
            actor.get_points_distance_to_surface(cohort["world_m"], distances)
        finally:
            # Keep partial/unwritten/nonfinite samples, including raised calls.
            np.savez(output / "distances.npz", distances_m=distances)
        stage = "identity-after-query"
        after = _snapshot(actor)
        _write_json(output / "after.json", _json_snapshot(after))
        for key, value in before.items():
            if isinstance(value, np.ndarray):
                unchanged = np.array_equal(value, after[key])
            else:
                unchanged = value == after[key]
            if not unchanged:
                raise ValueError(f"Actor identity changed during query: {key}")
        if any(sha256((output / name).read_bytes()).hexdigest() != digest
               for name, digest in before_hashes.items()):
            raise ValueError("Pre-query identity or mask artifact changed")
        if sha256((output / "before-manifest.json").read_bytes()).hexdigest() != manifest_hash:
            raise ValueError("Pre-query manifest artifact changed")
        if not np.isfinite(distances).all():
            raise ValueError("Incomplete or nonfinite native distance observations")
        stage = "offline-scoring"
        report = score_queries(cohort["local_m"], cohort["world_m"],
                               distances, domain["interior_mask"])
        _write_json(output / "score.json", report)
        return report
    except Exception as error:
        _write_json(output / "capture-failure.json", {
            "stage": stage, "error_type": type(error).__name__, "error": str(error),
        })
        raise
