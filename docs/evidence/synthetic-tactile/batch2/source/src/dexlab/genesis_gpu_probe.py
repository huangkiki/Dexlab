"""Small native CUDA isolation and capacity diagnostics; no CPU fallback."""
import argparse
import hashlib
import json
import os
import time
from importlib.metadata import version
from pathlib import Path


def run(output: Path, case: str) -> None:
    os.environ.setdefault("QD_NUM_THREADS", "2")
    import genesis as gs
    import torch

    if version("genesis-world") != "1.4.3" or not torch.cuda.is_available():
        raise RuntimeError("Requires official Genesis 1.4.3 and CUDA")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    count = 1 if case == "reset" else 2
    pairs = 1 if case == "overflow" else 32
    result = {
        "schema": 1, "case": case, "num_envs": count,
        "genesis": version("genesis-world"), "quadrants": version("quadrants"),
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0), "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Primitive CUDA diagnostic; not grasp, hardware, capacity maximum or throughput qualification",
        "timing_scope": "Synchronized wall time; stepping excludes observations; first step reported separately. Existing JIT cache retained.",
        "timing_s": {}, "episodes": [], "completed": False,
    }
    timing = result["timing_s"]

    def measured(name, operation):
        torch.cuda.synchronize()
        start = time.perf_counter()
        try:
            return operation()
        finally:
            torch.cuda.synchronize()
            timing[name] = timing.get(name, 0.0) + time.perf_counter() - start

    expected_overflow = False
    try:
        start = time.perf_counter()
        gs.init(backend=gs.cuda, precision="64", seed=0, logging_level="warning")
        torch.cuda.synchronize()
        timing["init"] = time.perf_counter() - start
        options = gs.options.RigidOptions(max_collision_pairs=pairs, noslip_iterations=0,
                                         friction_cone=gs.friction_cone.elliptic)
        result["options"] = options.model_dump(mode="json")
        result["dt_s"] = .001
        scene = gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=.001), rigid_options=options)
        scene.add_entity(gs.morphs.Plane(), material=gs.materials.Rigid(friction=.5))
        bodies = 4 if case in ("capacity", "overflow") else 1
        cubes = [scene.add_entity(gs.morphs.Box(size=(.04,) * 3, pos=(i * .1, 0, .0199)),
                                 material=gs.materials.Rigid(rho=1000, friction=.5)) for i in range(bodies)]
        try:
            measured("build", lambda: scene.build(n_envs=count))
        except Exception as error:
            if case != "overflow" or "Exceeding max number of candidate contact points" not in str(error):
                raise
            result["expected_overflow"] = str(error)
            expected_overflow = True
        if not expected_overflow:
            solver = scene.sim.rigid_solver
            info = solver.collider.collider_info
            result["capacity"] = {key: int(getattr(info, key)[None]) for key in (
                "max_possible_pairs", "max_collision_pairs", "max_collision_pairs_broad",
                "max_candidate_contacts", "max_contacts")}
            for episode in range(2):
                measured("reset", scene.reset)
                if case == "isolation" and episode == 1:
                    cubes[0].set_pos([[.1, 0, .0199]], envs_idx=[1])
                rows = []
                for step in range(20):
                    measured("first_step" if episode == 0 and step == 0 else "stepping", scene.step)
                    measured("error_check", solver.check_errno)
                    def observe():
                        return {"pos": [cube.get_pos().tolist() for cube in cubes],
                                "force": [cube.get_links_net_contact_force().tolist() for cube in cubes],
                                "error_mask": solver.get_error_envs_mask().tolist()}
                    rows.append(measured("observations", observe))
                result["episodes"].append(rows)
            result["completed"] = True
        result["rendering"] = "not executed"
        result["archival"] = "not executed"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        gs.destroy()
    if case == "overflow" and not expected_overflow:
        raise RuntimeError("Expected capacity overflow was not detected during build")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=("reset", "isolation", "capacity", "overflow"), required=True)
    args = parser.parse_args()
    run(args.output, args.case)


if __name__ == "__main__":
    main()
