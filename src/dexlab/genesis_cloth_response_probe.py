"""Bounded one-step response factorial for official Genesis PBD cloth."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from time import monotonic

from dexlab.genesis_cloth_probe import write_grid


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    mesh = output / "authored.obj"
    write_grid(mesh)
    record = {"completed": False, "cases": []}
    start = monotonic()
    try:
        import genesis as gs
        import numpy as np

        record["version"] = version("genesis-world")
        if record["version"] != "1.4.3":
            raise RuntimeError("Frozen runtime changed")
        record["runner_sha256"] = hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()
        for diameter in (0.012, 0.008, 0.006):
            for dt in (0.004, 0.002, 0.001):
                for mode in ("stretch", "bend"):
                    for enabled in (False, True):
                        case = {
                            "diameter": diameter,
                            "dt": dt,
                            "mode": mode,
                            "enabled": enabled,
                        }
                        record["cases"].append(case)
                        print(diameter, dt, mode, enabled, flush=True)
                        gs.init(
                            backend=gs.cpu,
                            precision="64",
                            seed=0,
                            use_deterministic_algorithms=True,
                            logging_level="warning",
                        )
                        try:
                            begin = monotonic()
                            options = gs.options.PBDOptions(
                                particle_size=diameter,
                                lower_bound=(-1, -1, -1),
                                upper_bound=(1, 1, 1),
                                max_stretch_solver_iterations=4,
                                max_bending_solver_iterations=1,
                            )
                            material = gs.materials.PBD.Cloth(
                                rho=0.2,
                                static_friction=0,
                                kinetic_friction=0,
                                stretch_compliance=1e-7,
                                bending_compliance=1e-5,
                                stretch_relaxation=0.3
                                if enabled and mode == "stretch"
                                else 0,
                                bending_relaxation=0.1
                                if enabled and mode == "bend"
                                else 0,
                                air_resistance=0,
                            )
                            scene = gs.Scene(
                                show_viewer=False,
                                sim_options=gs.options.SimOptions(
                                    dt=dt, substeps=1, gravity=(0, 0, 0)
                                ),
                                pbd_options=options,
                            )
                            cloth = scene.add_entity(
                                gs.morphs.Mesh(
                                    file=str(mesh), pos=(0, 0, 0.2), decimate=False
                                ),
                                material=material,
                            )
                            scene.build()
                            case["build_s"] = monotonic() - begin
                            rest = cloth.get_particles_pos().cpu().numpy().copy()
                            case.update(
                                rest=rest.tolist(),
                                faces=cloth._mesh.faces.tolist(),
                                mass=cloth.solver.particles_info.mass.to_numpy().tolist(),
                                options=options.model_dump(mode="json"),
                                material=material.model_dump(mode="json"),
                            )
                            initial = rest.copy()
                            if mode == "stretch":
                                initial[:, 0] *= 1.1
                            else:
                                initial[:, 2] += 0.2 * abs(initial[:, 0])
                            cloth.set_particles_pos(initial)
                            cloth.set_particles_vel(np.zeros_like(initial))

                            def sample():
                                return {
                                    "pos": cloth.get_particles_pos().tolist(),
                                    "vel": cloth.get_particles_vel().tolist(),
                                }

                            case["initial"] = sample()
                            begin = monotonic()
                            scene.step()
                            case["step_s"] = monotonic() - begin
                            case["final"] = sample()
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
