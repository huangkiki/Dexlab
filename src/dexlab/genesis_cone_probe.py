"""Native primitive diagnostic; deliberately separate from SDF grasp qualification."""
import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
from time import monotonic

CONDITIONS = ("no_write", "zero_all", "kick_all", "kick_x_only")


def run(output: Path) -> None:
    """Record both friction cones, retaining errors and refusing output overwrite."""
    os.environ.setdefault("QD_NUM_THREADS", "2")
    import genesis as gs

    if version("genesis-world") != "1.4.3":
        raise RuntimeError("This frozen diagnostic requires official Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    manifest = {
        "schema": 1, "engine": version("genesis-world"),
        "quadrants": version("quadrants"), "torch": version("torch"),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "backend": "cpu", "precision": "64", "seed": 0,
        "dt_s": 0.005, "settling_steps": 100, "steps": 40,
        "cube_size_m": [0.05] * 3, "density_kg_m3": 1000,
        "initial_position_m": [0, 0, 0.025], "mu": 0.5,
        "gravity_m_s2": [0, 0, -9.81], "noslip_iterations": 0,
        "scope": "Primitive kick/cone diagnostic; not SDF or hardware qualification",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for cone in ("pyramidal", "elliptic"):
        start = monotonic()
        try:
            gs.init(backend=gs.cpu, precision="64", seed=0,
                    use_deterministic_algorithms=True, logging_level="warning")
            options = gs.options.RigidOptions(
                noslip_iterations=0, friction_cone=getattr(gs.friction_cone, cone))
            scene = gs.Scene(show_viewer=False,
                             sim_options=gs.options.SimOptions(dt=0.005),
                             rigid_options=options)
            scene.add_entity(gs.morphs.Plane(), material=gs.materials.Rigid(friction=0.5))
            cube = scene.add_entity(
                gs.morphs.Box(size=(0.05,) * 3, pos=(0, 0, 0.025)),
                material=gs.materials.Rigid(rho=1000, friction=0.5))
            scene.build()
            (output / f"{cone}-settings.json").write_text(json.dumps({
                "options": options.model_dump(mode="json"),
                "build_and_init_wall_s": monotonic() - start}, indent=2) + "\n")

            def sample():
                return {"position": cube.get_pos().tolist(),
                        "velocity": cube.get_vel().tolist(),
                        "dofs_velocity": cube.get_dofs_velocity().tolist(),
                        "force": cube.get_links_net_contact_force().tolist(),
                        "quaternion": cube.get_quat().tolist()}

            for condition in CONDITIONS:
                scene.reset()
                for _ in range(100):
                    scene.step()
                before = sample()
                if condition == "zero_all":
                    cube.set_dofs_velocity([0] * 6)
                elif condition == "kick_all":
                    cube.set_dofs_velocity([0.5, 0, 0, 0, 0, 0])
                elif condition == "kick_x_only":
                    cube.set_dofs_velocity([0.5], dofs_idx_local=[0])
                after = sample()
                rows = []
                step_wall = observation_wall = 0.0
                for _ in range(40):
                    tick = monotonic()
                    scene.step()
                    step_wall += monotonic() - tick
                    tick = monotonic()
                    rows.append(sample())
                    observation_wall += monotonic() - tick
                record = {"cone": cone, "condition": condition, "before": before,
                          "after": after, "samples": rows,
                          "step_wall_s": step_wall, "observation_wall_s": observation_wall}
                (output / f"{cone}-{condition}.json").write_text(
                    json.dumps(record, indent=2) + "\n")
        except Exception as error:
            (output / f"{cone}-error.json").write_text(json.dumps({
                "type": type(error).__name__, "message": str(error)}, indent=2) + "\n")
            raise
        finally:
            gs.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
