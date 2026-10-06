"""Official native connected-cloth initial-fold stress, with no pins or rigid bodies."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from time import monotonic

from dexlab.cloth_fold import fold
from dexlab.genesis_cloth_probe import write_grid


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    mesh = output / "cloth.obj"
    write_grid(mesh)
    record = {
        "completed": False,
        "version": version("genesis-world"),
        "dt_s": 0.002,
        "steps": 20,
        "cases": [],
    }
    start = monotonic()
    try:
        import genesis as gs
        import numpy as np

        if record["version"] != "1.4.3":
            raise RuntimeError("Frozen runtime changed")
        record["runner_sha256"] = hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()
        for angle in (0, 150, 170):
            print("Building fold", angle, flush=True)
            case = {"angle_deg": angle, "episodes": []}
            record["cases"].append(case)
            gs.init(
                backend=gs.cpu,
                precision="64",
                seed=0,
                use_deterministic_algorithms=True,
                logging_level="warning",
            )
            try:
                options = gs.options.PBDOptions(
                    particle_size=0.008,
                    lower_bound=(-1, -1, -1),
                    upper_bound=(1, 1, 1),
                    max_stretch_solver_iterations=4,
                    max_bending_solver_iterations=1,
                )
                material = gs.materials.PBD.Cloth(
                    rho=0.2,
                    static_friction=0.5,
                    kinetic_friction=0.5,
                    stretch_compliance=1e-7,
                    bending_compliance=1e-5,
                    stretch_relaxation=0.3,
                    bending_relaxation=0.1,
                    air_resistance=0,
                )
                scene = gs.Scene(
                    show_viewer=False,
                    sim_options=gs.options.SimOptions(
                        dt=0.002, substeps=1, gravity=(0, 0, 0)
                    ),
                    pbd_options=options,
                )
                cloth = scene.add_entity(
                    gs.morphs.Mesh(file=str(mesh), pos=(0, 0, 0.2), decimate=False),
                    material=material,
                )
                begin = monotonic()
                scene.build()
                case["build_s"] = monotonic() - begin
                rest = cloth.get_particles_pos().cpu().numpy().copy()
                initial = fold(rest, angle)
                case.update(
                    rest=rest.tolist(),
                    faces=cloth._mesh.faces.tolist(),
                    mass=cloth.solver.particles_info.mass.to_numpy().tolist(),
                    options=options.model_dump(mode="json"),
                    material=material.model_dump(mode="json"),
                )
                for repeat in range(2):
                    scene.reset()
                    cloth.set_particles_pos(initial)
                    cloth.set_particles_vel(np.zeros_like(initial))
                    rows = []
                    step_s = 0.0
                    observation_s = 0.0
                    for step in range(21):
                        begin = monotonic()
                        rows.append(
                            {
                                "step": step,
                                "pos": cloth.get_particles_pos().tolist(),
                                "vel": cloth.get_particles_vel().tolist(),
                            }
                        )
                        observation_s += monotonic() - begin
                        if step < 20:
                            begin = monotonic()
                            scene.step()
                            step_s += monotonic() - begin
                    case["episodes"].append(
                        {
                            "repeat": repeat,
                            "rows": rows,
                            "step_s": step_s,
                            "observation_s": observation_s,
                        }
                    )
                    print(angle, repeat, "complete", flush=True)
            finally:
                gs.destroy()
        record["completed"] = True
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        record["wall_s"] = monotonic() - start
        (output / "record.json").write_text(
            json.dumps(record, indent=2, allow_nan=True) + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
