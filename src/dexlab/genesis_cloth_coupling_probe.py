"""Frozen free-plate PBD momentum diagnostic; not frictional grasp qualification."""

import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
from time import monotonic


def write_grid(path):
    """An authored open surface; native remeshing is recorded separately."""
    lines = [
        f"v {i * 0.01 - 0.02:.8f} {j * 0.01 - 0.02:.8f} 0"
        for j in range(5)
        for i in range(5)
    ]
    for j in range(4):
        for i in range(4):
            a = j * 5 + i + 1
            lines.extend((f"f {a} {a + 1} {a + 6}", f"f {a} {a + 6} {a + 5}"))
    path.write_text("\n".join(lines) + "\n")


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    mesh = output / "authored.obj"
    write_grid(mesh)
    record = {
        "schema": 1,
        "completed": False,
        "scenes": [],
        "runner_sha256": hashlib.sha256(source).hexdigest(),
        "mesh_sha256": hashlib.sha256(mesh.read_bytes()).hexdigest(),
        "protocol": {
            "dt_s": 0.002,
            "steps": 150,
            "repeats": 2,
            "diameter_m": 0.008,
            "area_density_kg_m2": 0.2,
            "initial_height_m": 0.02,
            "initial_vz_m_s": -0.1,
            "gravity_m_s2": [0, 0, 0],
            "plate_size_m": [0.08, 0.08, 0.01],
            "plate_mass_kg": 0.001,
        },
        "scope": "Free-body linear momentum diagnostic, not frictional grasp qualification",
    }
    started = monotonic()
    try:
        os.environ.setdefault("QD_NUM_THREADS", "2")
        import genesis as gs
        import numpy as np

        record["versions"] = {
            name: version(name) for name in ("genesis-world", "quadrants", "torch")
        }
        if record["versions"]["genesis-world"] != "1.4.3":
            raise RuntimeError("Frozen protocol requires official Genesis 1.4.3")
        root = Path(gs.__file__).parent
        files = [
            "engine/materials/PBD/cloth.py",
            "engine/entities/pbd_entity.py",
            "engine/solvers/pbd_solver.py",
            "engine/couplers/legacy_coupler.py",
        ]
        record["native_sources"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in files
        }
        for name, mu, coupled in (("coupled", 0.01, True), ("disabled", 0.01, False)):
            print("Building", name, flush=True)
            scene_record = {"name": name, "mu": mu, "coupled": coupled, "episodes": []}
            record["scenes"].append(scene_record)
            build_start = monotonic()
            gs.init(
                backend=gs.cpu,
                precision="64",
                seed=0,
                use_deterministic_algorithms=True,
                logging_level="warning",
            )
            try:
                sim = gs.options.SimOptions(dt=0.002, substeps=1, gravity=(0, 0, 0))
                pbd = gs.options.PBDOptions(
                    particle_size=0.008,
                    lower_bound=(-1, -1, -1),
                    upper_bound=(1, 1, 1),
                    max_stretch_solver_iterations=4,
                    max_bending_solver_iterations=1,
                )
                cloth_material = gs.materials.PBD.Cloth(
                    rho=0.2,
                    static_friction=mu,
                    kinetic_friction=mu,
                    stretch_compliance=1e-7,
                    bending_compliance=1e-5,
                    stretch_relaxation=0.3,
                    bending_relaxation=0.1,
                    air_resistance=0,
                )
                plane_material = gs.materials.Rigid(
                    rho=15.625, friction=mu, coup_friction=mu, needs_coup=coupled
                )
                scene = gs.Scene(
                    show_viewer=False,
                    sim_options=sim,
                    pbd_options=pbd,
                    rigid_options=gs.options.RigidOptions(noslip_iterations=0),
                )
                plane = scene.add_entity(
                    gs.morphs.Box(size=(0.08, 0.08, 0.01), pos=(0, 0, 0), fixed=False),
                    material=plane_material,
                )
                cloth = scene.add_entity(
                    gs.morphs.Mesh(file=str(mesh), pos=(0, 0, 0.02), decimate=False),
                    material=cloth_material,
                )
                scene.build()
                scene_record["build_s"] = monotonic() - build_start
                scene_record["settings"] = {
                    "sim": sim.model_dump(mode="json"),
                    "pbd": pbd.model_dump(mode="json"),
                    "cloth": cloth_material.model_dump(mode="json"),
                    "plane": plane_material.model_dump(mode="json"),
                }
                scene_record["native"] = {
                    "particle_count": cloth.n_particles,
                    "plate_mass_kg": float(plane.get_mass()),
                    "plate_dofs": plane.n_dofs,
                    "mesh_vertices": cloth._mesh.verts.tolist(),
                    "mesh_faces": cloth._mesh.faces.tolist(),
                    "edges": cloth._edges.tolist(),
                    "edge_rest_m": cloth._edges_len_rest.tolist(),
                    "particle_mass_kg": cloth.solver.particles_info.mass.to_numpy().tolist(),
                    "particle_diameter_m": cloth.solver.particle_size,
                    "stretch_compliance": cloth.solver.edges_info.stretch_compliance.to_numpy().tolist(),
                    "bend_compliance": cloth.solver.inner_edges_info.bending_compliance.to_numpy().tolist(),
                }
                scene_record["force_scope"] = (
                    "Plane accessor is direct rigid contacts; PBD coupling-force availability unqualified. Do not use it as cloth support truth."
                )
                for repeat in range(2):
                    scene.reset()
                    cloth.set_particles_vel(
                        np.tile([0, 0, -0.1], (cloth.n_particles, 1))
                    )

                    def sample(step):
                        return {
                            "step": step,
                            "pos": cloth.get_particles_pos().tolist(),
                            "vel": cloth.get_particles_vel().tolist(),
                            "plate_pos": plane.get_pos().tolist(),
                            "plate_vel": plane.get_vel().tolist(),
                            "plate_quat": plane.get_quat().tolist(),
                            "plate_ang": plane.get_ang().tolist(),
                            "plate_direct_contact_force": plane.get_links_net_contact_force().tolist(),
                        }

                    episode = {
                        "repeat": repeat,
                        "rows": [sample(0)],
                        "step_s": 0.0,
                        "observation_s": 0.0,
                    }
                    scene_record["episodes"].append(episode)
                    for step in range(1, 151):
                        tick = monotonic()
                        scene.step()
                        episode["step_s"] += monotonic() - tick
                        tick = monotonic()
                        episode["rows"].append(sample(step))
                        episode["observation_s"] += monotonic() - tick
                    print(name, "repeat", repeat, "complete", flush=True)
            finally:
                gs.destroy()
        record["completed"] = True
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        record["wall_s"] = monotonic() - started
        (output / "record.json").write_text(
            json.dumps(record, indent=2, allow_nan=True) + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
