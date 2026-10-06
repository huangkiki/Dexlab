"""Independent rest-edge/dihedral response diagnostic; not fabric calibration."""

import argparse
import json
from pathlib import Path

import numpy as np


def surface_error(position, rest, faces):
    """Return dimensionless edge-strain RMS and adjacent-face angle RMS in radians."""
    position, rest = np.asarray(position, float), np.asarray(rest, float)
    faces = np.asarray(faces)
    if (
        position.ndim != 2
        or position.shape[1] != 3
        or rest.shape != position.shape
        or not np.isfinite(position).all()
        or not np.isfinite(rest).all()
        or faces.ndim != 2
        or faces.shape[1] != 3
        or not len(faces)
        or not np.issubdtype(faces.dtype, np.integer)
        or (faces < 0).any()
        or (faces >= len(rest)).any()
    ):
        raise ValueError("Invalid surface arrays")
    edge_faces = {}
    for index, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            edge_faces.setdefault(tuple(sorted((int(a), int(b)))), []).append(index)
    if any(len(v) > 2 for v in edge_faces.values()):
        raise ValueError("Nonmanifold surface")
    edges = np.array(list(edge_faces))
    rest_lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    lengths = np.linalg.norm(position[edges[:, 0]] - position[edges[:, 1]], axis=1)
    if (rest_lengths <= 1e-12).any():
        raise ValueError("Degenerate rest edge")
    triangles = position[faces]
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    areas2 = np.linalg.norm(normals, axis=1)
    if (areas2 <= 1e-12).any():
        raise ValueError("Degenerate triangle")
    normals /= areas2[:, None]
    pairs = np.array([v for v in edge_faces.values() if len(v) == 2])
    if not len(pairs):
        raise ValueError("No shared edge for bending reference")
    dots = np.einsum("ij,ij->i", normals[pairs[:, 0]], normals[pairs[:, 1]])
    angles = np.arccos(np.clip(dots, -1, 1))
    return {
        "strain_rms": float(np.sqrt(np.mean((lengths / rest_lengths - 1) ** 2))),
        "bend_rms_rad": float(np.sqrt(np.mean(angles**2))),
    }


def score(record):
    try:
        if (
            not isinstance(record, dict)
            or not record.get("completed")
            or "error" in record
        ):
            raise ValueError("Incomplete response record")
        expected = [
            (d, dt, mode, on)
            for d in (0.012, 0.008, 0.006)
            for dt in (0.004, 0.002, 0.001)
            for mode in ("stretch", "bend")
            for on in (False, True)
        ]
        if (
            record["version"] != "1.4.3"
            or [
                (s["diameter"], s["dt"], s["mode"], s["enabled"])
                for s in record["cases"]
            ]
            != expected
        ):
            raise ValueError("Incomplete frozen factorial")
        results = []
        for case in record["cases"]:
            expected_stretch = (
                0.3 if case["enabled"] and case["mode"] == "stretch" else 0
            )
            expected_bend = 0.1 if case["enabled"] and case["mode"] == "bend" else 0
            if (
                case["options"]["max_stretch_solver_iterations"] != 4
                or case["options"]["max_bending_solver_iterations"] != 1
                or case["material"]["stretch_relaxation"] != expected_stretch
                or case["material"]["bending_relaxation"] != expected_bend
            ):
                raise ValueError("Native constraint controls mismatch")
            rest = np.asarray(case["rest"], float)
            initial = np.asarray(case["initial"]["pos"], float)
            final = np.asarray(case["final"]["pos"], float)
            iv = np.asarray(case["initial"]["vel"], float)
            fv = np.asarray(case["final"]["vel"], float)
            mass = np.asarray(case["mass"], float)
            if (
                rest.shape != initial.shape
                or final.shape != rest.shape
                or iv.shape != rest.shape
                or fv.shape != rest.shape
                or not np.isfinite(iv).all()
                or not np.isfinite(fv).all()
                or mass.shape != (len(rest),)
                or not np.isfinite(mass).all()
                or (mass <= 0).any()
                or abs(mass.sum() - 0.00032) > 1e-8
                or np.max(abs(iv)) > 1e-8
            ):
                raise ValueError("Invalid native state/mass")
            target = rest.copy()
            if case["mode"] == "stretch":
                target[:, 0] *= 1.1
            else:
                target[:, 2] += 0.2 * abs(target[:, 0])
            if np.max(abs(initial - target)) > 1e-8:
                raise ValueError("Initial deformation mismatch")
            before = surface_error(initial, rest, case["faces"])
            after = surface_error(final, rest, case["faces"])
            metric = "strain_rms" if case["mode"] == "stretch" else "bend_rms_rad"
            reduction = before[metric] - after[metric]
            shift = float(np.linalg.norm((final - initial).T @ mass / mass.sum()))
            unchanged = np.max(abs(final - initial)) <= 1e-9 and np.max(abs(fv)) <= 1e-8
            passed = (
                (reduction > 1e-10 and shift <= 1e-9) if case["enabled"] else unchanged
            )
            results.append(
                {
                    "diameter_m": case["diameter"],
                    "dt_s": case["dt"],
                    "mode": case["mode"],
                    "enabled": case["enabled"],
                    "particles": len(rest),
                    "before": before,
                    "after": after,
                    "reduction": reduction,
                    "center_shift_m": shift,
                    "passed": bool(passed),
                }
            )
        return {
            "valid": True,
            "passed": all(c["passed"] for c in results),
            "cases": results,
            "limits": "One-step constraint direction/sensitivity; not constitutive magnitude, unloading, continuum convergence or calibrated cloth.",
        }
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        return {"valid": False, "passed": False, "reason": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = score(json.loads(parser.parse_args().record.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["passed"] else 1)
