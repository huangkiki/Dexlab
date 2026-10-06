"""Offline cloth/robot convex-collision diagnostic; never a grasp success test.

Only recorded poses and compiled geometry enter the calculation. Kinematics
reconstructs the surfaces; SciPy, not native contact queries, measures intrusion.
"""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

NUMERICAL_EPS_M = 1e-8


@dataclass(frozen=True)
class RobotHull:
    geom_id: int
    name: str
    vertices: np.ndarray
    equations: np.ndarray


def triangle_hull_depth(triangle, equations):
    """Maximize nearest-boundary distance inside a convex solid over a triangle.

    Hull planes satisfy n.p + b <= 0 with unit outward normals. Optimize d>=0
    and barycentric s,t>=0, s+t<=1, with n.(p0+s*a+t*b)+offset+d<=0.
    This is interior distance, not minimum translation or native contact depth.
    """
    triangle, equations = np.asarray(triangle), np.asarray(equations)
    if (triangle.shape != (3, 3) or equations.ndim != 2
            or equations.shape[1] != 4 or len(equations) < 4
            or not np.isfinite(triangle).all() or not np.isfinite(equations).all()
            or not np.allclose(np.linalg.norm(equations[:, :3], axis=1), 1,
                               rtol=0, atol=1e-10)
            or np.linalg.norm(np.cross(triangle[1] - triangle[0],
                                       triangle[2] - triangle[0])) < 1e-14):
        raise ValueError("Expected a nondegenerate triangle and normalized hull planes")
    normals, offsets = equations[:, :3], equations[:, 3]
    # Conservative rejection: one plane separates all three vertices.
    if np.any((triangle @ normals.T + offsets).min(axis=0) > NUMERICAL_EPS_M):
        return 0.0
    p, a, b = triangle[0], triangle[1] - triangle[0], triangle[2] - triangle[0]
    matrix = np.column_stack((normals @ a, normals @ b, np.ones(len(normals))))
    result = linprog(
        [0, 0, -1], A_ub=np.vstack((matrix, [1, 1, 0])),
        b_ub=np.r_[-offsets - normals @ p, 1], bounds=[(0, None)] * 3,
        method="highs", options={"primal_feasibility_tolerance": 1e-9},
    )
    if result.status == 2:
        return 0.0
    if not result.success:
        raise RuntimeError(f"Triangle/hull optimization failed: {result.message}")
    return max(0.0, float(result.x[2]))


def robot_hulls(model):
    """Read this demo's robot colliders, including both hands and both arms.

    Use the stored collision hull vertex IDs, not all render-mesh vertices:
    maxhullvert can make those two convex hulls different. Compiled vertices are
    already scaled/centered; geom_xpos/xmat applies their world transform once.
    """
    hulls = []
    for geom in range(model.ngeom):
        name = model.geom(geom).name or ""
        if name == "floor" or name.startswith("table_"):
            continue
        if not name.startswith("collision_"):
            raise ValueError(f"Unclassified geometry: {name or geom}")
        if (model.geom_type[geom] != mujoco.mjtGeom.mjGEOM_MESH
                or not (model.geom_contype[geom] or model.geom_conaffinity[geom])):
            raise ValueError(f"Expected an enabled mesh collider: {name}")
        mesh = int(model.geom_dataid[geom])
        address = int(model.mesh_graphadr[mesh])
        if address < 0:
            raise ValueError(f"Missing compiled collision hull: {name}")
        count = int(model.mesh_graph[address])
        ids = model.mesh_graph[address + 2 + count:address + 2 + 2 * count]
        if count < 4 or len(ids) != count or np.any(ids < 0) or np.any(ids >= model.mesh_vertnum[mesh]):
            raise ValueError(f"Invalid compiled collision hull: {name}")
        vertices = np.asarray(model.mesh_vert[model.mesh_vertadr[mesh] + ids], dtype=float)
        hulls.append(RobotHull(geom, name, vertices, ConvexHull(vertices).equations))
    if not hulls:
        raise ValueError("No robot collision meshes; absence is not zero intrusion")
    return hulls


def audit_robot(model, times, poses, triangles):
    """Inspect every supplied frame and every robot hull, with no integration."""
    times, poses, triangles = map(np.asarray, (times, poses, triangles))
    if (model.nflex != 1 or model.flex_dim[0] != 2 or model.nplugin
            or times.ndim != 1 or len(times) == 0
            or not np.isfinite(times).all() or np.any(np.diff(times) <= 0)
            or poses.shape != (len(times), model.nq) or not np.isfinite(poses).all()
            or triangles.ndim != 2 or triangles.shape[1] != 3
            or triangles.dtype.kind not in "iu"
            or not np.array_equal(triangles.ravel(), model.flex_elem)):
        raise ValueError("Expected complete finite poses and the compiled 2D cloth topology")
    hulls = robot_hulls(model)
    data = mujoco.MjData(model)
    rows, maxima = [], {hull.name: 0.0 for hull in hulls}
    for time, pose in zip(times, poses, strict=True):
        data.qpos[:] = pose
        mujoco.mj_kinematics(model, data)
        mujoco.mj_flex(model, data)
        world_faces = data.flexvert_xpos[triangles]
        if (not np.isfinite(world_faces).all() or np.any(np.linalg.norm(
                np.cross(world_faces[:, 1] - world_faces[:, 0],
                         world_faces[:, 2] - world_faces[:, 0]), axis=1) < 1e-14)):
            raise ValueError("Nonfinite or degenerate saved cloth surface")
        largest, witness, pairs = 0.0, None, 0
        for hull in hulls:
            rotation = data.geom_xmat[hull.geom_id].reshape(3, 3)
            faces = (world_faces - data.geom_xpos[hull.geom_id]) @ rotation
            lower, upper = hull.vertices.min(axis=0), hull.vertices.max(axis=0)
            candidates = np.flatnonzero(
                np.all(faces.max(axis=1) >= lower - NUMERICAL_EPS_M, axis=1)
                & np.all(faces.min(axis=1) <= upper + NUMERICAL_EPS_M, axis=1))
            for index in candidates:
                depth = triangle_hull_depth(faces[index], hull.equations)
                maxima[hull.name] = max(maxima[hull.name], depth)
                pairs += depth > NUMERICAL_EPS_M
                if depth > largest:
                    largest = depth
                    witness = {"geom": hull.name, "triangle": int(index)}
        rows.append({"time_s": float(time), "maximum_interior_depth_m": largest,
                     "intruding_triangle_geom_pairs": int(pairs), "witness": witness})
    affected = [row for row in rows if row["maximum_interior_depth_m"] > NUMERICAL_EPS_M]
    return {
        "version": "robot-convex-interior-v1",
        "status": "sampled_intrusion_detected" if affected else "no_sampled_intrusion",
        "classification": "exploratory_diagnostic_not_a_physical_acceptance_test",
        "method": "LP over zero-thickness triangles and stored robot collision hulls",
        "numerical_zero_tolerance_m": NUMERICAL_EPS_M,
        "saved_frames": len(times), "robot_geom_count": len(hulls),
        "triangle_count": len(triangles), "frames_with_intrusion": len(affected),
        "maximum_interior_depth_m": max(row["maximum_interior_depth_m"] for row in rows),
        "first_intrusion_time_s": affected[0]["time_s"] if affected else None,
        "per_geom_maximum_interior_depth_m": maxima, "rows": rows,
        "coverage_limits": [
            "Recorded frames only; no continuous-time separation claim",
            "Collision convex hulls, not detailed render surfaces or SDFs",
            "Zero-thickness cloth; no collision radius or contact margin inflation",
            "Interior distance is not native contact depth or minimum translation distance",
            "Small compliant contact overlap alone does not establish physical failure",
            "Floor, table and cloth self-intersection require separate audits",
            "Shared archived geometry and native kinematics; independent intersection algorithm",
        ],
    }


def audit_saved(directory):
    """Require the original demo's complete 25 Hz grid; leave the record intact."""
    directory = Path(directory)
    names = ("model.mjb", "states.npz", "summary.json")

    def hashes():
        result = {}
        for name in names:
            with (directory / name).open("rb") as stream:
                result[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        return result

    before = hashes()
    metadata = json.loads((directory / "summary.json").read_text())
    duration = metadata["schedule_s"]["duration"]
    if (not np.isfinite(duration) or duration <= 0
            or not np.isclose(duration * 25, round(duration * 25), rtol=0, atol=1e-10)):
        raise ValueError("Invalid recorded duration")
    expected = np.arange(round(duration * 25)) / 25
    model = mujoco.MjModel.from_binary_path(str(directory / "model.mjb"))
    with np.load(directory / "states.npz", allow_pickle=False) as archive:
        times, poses, triangles = (archive[key] for key in ("time_s", "qpos", "triangles"))
    if times.shape != expected.shape or not np.allclose(times, expected, rtol=0, atol=1e-10):
        raise ValueError("Incomplete 25 Hz saved-state grid")
    report = audit_robot(model, times, poses, triangles)
    if hashes() != before:
        raise ValueError("Recording changed during offline audit")
    report.update(input_sha256=before, physics_steps_executed=0,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  runtime={"mujoco": mujoco.__version__, "numpy": np.__version__,
                           "scipy": scipy.__version__})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error("Output must be outside the original recording")
    if args.output.exists():
        parser.error("Output already exists; choose a new file")
    report = audit_saved(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in (
        "status", "saved_frames", "robot_geom_count", "frames_with_intrusion",
        "maximum_interior_depth_m", "physics_steps_executed")}))


if __name__ == "__main__":
    main()
