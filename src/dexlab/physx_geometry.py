"""Independent triangle-surface penetration audit of recorded native body poses.

Adaptive temporal samples have a rigid-motion coverage bound for every saved
physics step. Spatial subdivision bounds uncovered triangle interiors. Winding
queries use Warp, not PhysX contacts; mesh discretization/FP error remain explicit.
"""

import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh
import warp as wp
from scipy.spatial.transform import Rotation


@wp.kernel
def distances(
    mesh: wp.uint64,
    points: wp.array(dtype=wp.vec3),
    positions: wp.array(dtype=wp.vec3),
    rotations: wp.array(dtype=wp.quat),
    peaks: wp.array(dtype=float),
    failures: wp.array(dtype=int),
):
    frame, vertex = wp.tid()
    p = wp.quat_rotate(rotations[frame], points[vertex]) + positions[frame]
    query = wp.mesh_query_point_sign_winding_number(mesh, p, 10.0, 8.0, 0.5)
    if query.result:
        nearest = wp.mesh_eval_position(mesh, query.face, query.u, query.v)
        depth = -query.sign * wp.length(p - nearest)
        wp.atomic_max(peaks, frame, depth)
    else:
        wp.atomic_add(failures, 0, 1)


def dense(mesh, edge):
    v, f = trimesh.remesh.subdivide_to_size(
        mesh.vertices, mesh.faces, edge, max_iter=12
    )
    longest = np.linalg.norm(v[f][:, [1, 2, 0]] - v[f], axis=2).max()
    if longest > edge * 1.00001:
        raise ValueError("Incomplete spatial refinement")
    return np.asarray(v, np.float32), float(longest)


def native_mesh(mesh):
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume <= 0:
        raise ValueError("Reference surface must be a positive, closed oriented volume")
    return wp.Mesh(
        points=wp.array(np.asarray(mesh.vertices, np.float32), dtype=wp.vec3),
        indices=wp.array(np.asarray(mesh.faces, np.int32).ravel(), dtype=int),
        support_winding_number=True,
    )


def query(mesh, points, pos, rot):
    peaks = wp.zeros(len(pos), dtype=float)
    failed = wp.zeros(1, dtype=int)
    wp.launch(
        distances,
        dim=(len(pos), len(points)),
        inputs=[
            mesh.id,
            wp.array(points, dtype=wp.vec3),
            wp.array(pos.astype(np.float32), dtype=wp.vec3),
            wp.array(rot.as_quat().astype(np.float32), dtype=wp.quat),
            peaks,
            failed,
        ],
    )
    wp.synchronize()
    if failed.numpy()[0]:
        raise ValueError("Reference distance query missed a point")
    return peaks.numpy()


def self_test():
    """Check GPU inside/outside signs and distances against an analytical box."""
    reference = trimesh.creation.box([0.02, 0.04, 0.06])
    gpu = native_mesh(reference)
    rng = np.random.default_rng(70231)
    positions = rng.uniform(-0.035, 0.035, size=(1000, 3)).astype(np.float32)
    expected = np.maximum(np.min([0.01, 0.02, 0.03] - np.abs(positions), axis=1), 0.0)
    actual = query(
        gpu, np.zeros((1, 3), np.float32), positions, Rotation.identity(len(positions))
    )
    error = float(np.max(np.abs(actual - expected)))
    if error > 1e-6:
        raise ValueError(f"Analytical query error: {error}")
    # A translated, rotated sample verifies transform order independently.
    rotated = query(
        gpu,
        np.array([[0.003, 0.002, 0]], np.float32),
        np.array([[0.009, 0, 0]]),
        Rotation.from_euler("z", [90], degrees=True),
    )
    if not np.allclose(rotated, [0.003], rtol=0, atol=1e-6):
        raise ValueError("Query frame transform mismatch")
    return {
        "samples": 1000,
        "maximum_box_error_m": error,
        "rotated_point_depth_m": float(rotated[0]),
        "tolerance_m": 1e-6,
        "scope": "analytical box checks; not a general floating-point error proof",
    }


def audit(a):
    p = a.run.resolve()
    if a.output.exists():
        raise FileExistsError(a.output)
    started = time.monotonic()
    receipt = json.loads((p / "run.json").read_text())
    x = np.load(p / "states.npz")
    wp.init()
    wp.set_device(a.device)
    query_checks = self_test()
    apple_id = receipt["body_names"].index("apple/apple")
    ar = Rotation.from_quat(x["quaternion"][:, apple_id][:, [1, 2, 3, 0]])
    ap = x["position"][:, apple_id]
    apple = trimesh.load_mesh(p / "apple.obj", process=False)
    apple_gpu = native_mesh(apple)
    apple_points, apple_edge = dense(apple, a.edge)
    apple_center = apple.bounding_box.centroid
    apple_radius = np.linalg.norm(apple.vertices - apple_center, axis=1).max()
    apple_origin_radius = np.linalg.norm(apple.vertices, axis=1).max()
    apple_centers = ap + ar.apply(np.broadcast_to(apple_center, ap.shape))
    xml = ET.parse(p / "robot-model/robot.xml")
    assets = {m.get("name"): m for m in xml.findall("./asset/mesh")}
    results = []
    for body in xml.findall(".//body"):
        name = "robot/" + body.get("name")
        bid = receipt["body_names"].index(name)
        br = Rotation.from_quat(x["quaternion"][:, bid][:, [1, 2, 3, 0]])
        bp = x["position"][:, bid]
        for geom in body.findall("geom"):
            asset = assets[geom.get("mesh")]
            path = Path(asset.get("file"))
            if not path.is_absolute():
                path = p / "robot-model" / path
            mesh = trimesh.load_mesh(path, process=False)
            mesh.apply_scale(np.fromstring(asset.get("scale", "1 1 1"), sep=" "))
            gr = Rotation.from_quat(
                np.fromstring(geom.get("quat", "1 0 0 0"), sep=" ")[[1, 2, 3, 0]]
            )
            mesh.vertices = gr.apply(mesh.vertices) + np.fromstring(
                geom.get("pos", "0 0 0"), sep=" "
            )
            center = mesh.bounding_box.centroid
            radius = np.linalg.norm(mesh.vertices - center, axis=1).max()
            centers = bp + br.apply(np.broadcast_to(center, bp.shape))
            near = np.flatnonzero(
                np.linalg.norm(centers - apple_centers, axis=1) <= radius + apple_radius
            )
            report = {
                "body": name,
                "geom": geom.get("name"),
                "near_steps": len(near),
                "total_steps": len(ap),
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            if not len(near):
                report["bounding_spheres_disjoint"] = True
                results.append(report)
                continue
            rr = ar.inv() * br
            rp = ar.inv().apply(bp - ap)
            ir = rr.inv()
            ip = ir.apply(-rp)
            shape_radius = np.linalg.norm(mesh.vertices, axis=1).max()
            selected = [int(near[0])]
            max_motion = 0.0
            for i in near[1:]:
                prev = selected[-1]
                angle = (rr[prev].inv() * rr[i]).magnitude()
                bound = max(
                    np.linalg.norm(rp[i] - rp[prev]) + shape_radius * angle,
                    np.linalg.norm(ip[i] - ip[prev]) + apple_origin_radius * angle,
                )
                if bound > a.motion:
                    selected.append(int(i))
                else:
                    max_motion = max(max_motion, float(bound))
            points, edge = dense(mesh, a.edge)
            other_gpu = native_mesh(mesh)
            forward = query(apple_gpu, points, rp[selected], rr[selected])
            reverse = query(other_gpu, apple_points, ip[selected], ir[selected])
            peak = float(max(forward.max(), reverse.max()))
            report.update(
                sampled_steps=len(selected),
                sampled_step_indices=selected,
                surface_points=len(points),
                apple_surface_points=len(apple_points),
                sampled_max_penetration_m=peak,
                spatial_bound_m=max(edge, apple_edge),
                temporal_bound_m=max_motion,
                covered_penetration_bound_m=peak + max(edge, apple_edge) + max_motion,
            )
            results.append(report)
            print(
                json.dumps(
                    {k: v for k, v in report.items() if k != "sampled_step_indices"}
                ),
                flush=True,
            )
    result = {
        "scope": __doc__,
        "warp_version": wp.__version__,
        "precision": "FP32 query, FP64 pose coverage calculation",
        "query_accuracy": 8.0,
        "analytic_query_check": query_checks,
        "spatial_edge_m": a.edge,
        "temporal_motion_m": a.motion,
        "limit_m": 0.001,
        "bounds_exclude": [
            "reference mesh error",
            "unbounded query floating-point error",
        ],
        "maximum_sampled_penetration_m": max(
            [r.get("sampled_max_penetration_m", 0) for r in results]
        ),
        "maximum_coverage_bound_m": max(
            [r.get("covered_penetration_bound_m", 0) for r in results]
        ),
        "results": results,
        "states_sha256": hashlib.sha256((p / "states.npz").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "elapsed_s": time.monotonic() - started,
    }
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(a.output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--edge", type=float, default=0.0004)
    parser.add_argument("--motion", type=float, default=0.0002)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--self-test-only", action="store_true")
    a = parser.parse_args()
    if a.self_test_only:
        wp.init()
        wp.set_device(a.device)
        print(json.dumps(self_test(), indent=2))
        return
    if a.run is None or a.output is None:
        parser.error("run and --output are required")
    if not np.isfinite([a.edge, a.motion]).all() or min(a.edge, a.motion) <= 0:
        parser.error("Spatial and motion bounds must be positive and finite")
    audit(a)


if __name__ == "__main__":
    main()
