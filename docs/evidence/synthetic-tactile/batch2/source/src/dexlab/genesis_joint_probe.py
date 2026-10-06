"""Read back imported inertia before comparing native joint-limit configurations."""
import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
from time import monotonic


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def readback(entity):
    fields = ("get_links_mass", "get_dofs_armature", "get_dofs_damping",
              "get_dofs_kp", "get_dofs_kv", "get_dofs_position", "get_mass_mat")
    result = {name: getattr(entity, name)().tolist() for name in fields}
    for name in ("get_dofs_limit", "get_dofs_force_range"):
        result[name] = [value.tolist() for value in getattr(entity, name)()]
    result["joint_sol_params"] = entity.get_joint("slide").get_sol_params().tolist()
    return result


def run(output: Path):
    os.environ.setdefault("QD_NUM_THREADS", "2")
    import genesis as gs

    if version("genesis-world") != "1.4.3":
        raise RuntimeError("Frozen protocol requires Genesis 1.4.3")
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "runner.py").write_bytes(source)
    write_json(output / "protocol.json", {
        "schema": 1, "engine": version("genesis-world"),
        "quadrants": version("quadrants"), "torch": version("torch"),
        "dt_s": 0.002, "steps": 500, "mass_kg": 0.1,
        "gravity": [0, 0, 0], "range_m": [0, 0.05], "initial_q_m": 0.025,
        "targets_m": [-0.05, 0.1], "kp": 100, "kv": 10,
        "effort_range_N": [-5, 5], "precision": "64", "backend": "cpu",
        "max_violation_m": 0.001, "negative_min_exceedance_m": 0.01,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scope": "Synthetic slider controls; no hardware calibration or grasp claim",
    })
    for armature in ("as_imported", "zero"):
        for response in ("default", "explicit004"):
            name = f"{armature}-{response}"
            extra = ' solreflimit="0.004 1"' if response == "explicit004" else ""
            model = output / f"{name}.xml"
            model.write_text(
                '<mujoco><compiler angle="radian"/><worldbody><body name="base">'
                '<body name="slider"><joint name="slide" type="slide" axis="1 0 0" '
                f'limited="true" range="0 0.05" damping="0"{extra}/>'
                '<geom type="box" size="0.01 0.01 0.01" mass="0.1" '
                'contype="0" conaffinity="0"/></body></body></worldbody></mujoco>')
            for enabled in (True, False):
                started = monotonic()
                try:
                    gs.init(backend=gs.cpu, precision="64", seed=0,
                            use_deterministic_algorithms=True, logging_level="warning")
                    options = gs.options.RigidOptions(enable_joint_limit=enabled, noslip_iterations=0)
                    scene = gs.Scene(show_viewer=False,
                                     sim_options=gs.options.SimOptions(dt=0.002, gravity=(0, 0, 0)),
                                     rigid_options=options)
                    entity = scene.add_entity(gs.morphs.MJCF(file=str(model)))
                    scene.build()
                    if entity.n_dofs != 1:
                        raise RuntimeError("Expected exactly one prismatic DOF")
                    if armature == "zero":
                        entity.set_dofs_armature([0])
                    entity.set_dofs_kp([100])
                    entity.set_dofs_kv([10])
                    entity.set_dofs_force_range([-5], [5])
                    build_time = monotonic() - started
                    for target in (-0.05, 0.1):
                        scene.reset()
                        entity.set_dofs_position([0.025])
                        entity.control_dofs_force([0])
                        # In position mode this native matrix includes implicit actuator damping.
                        # Read physical inertia in zero-force mode at the resting zero-gravity state.
                        scene.step()
                        initial = readback(entity)
                        entity.control_dofs_position([target])
                        rows = []
                        step_time = observation_time = 0.0
                        for index in range(500):
                            tick = monotonic()
                            scene.step()
                            step_time += monotonic() - tick
                            tick = monotonic()
                            rows.append({"step": index + 1,
                                         "q_m": entity.get_dofs_position().tolist()[0],
                                         "v_m_s": entity.get_dofs_velocity().tolist()[0],
                                         "generalized_force_N": entity.get_dofs_force().tolist()[0]})
                            observation_time += monotonic() - tick
                        write_json(output / f"{name}-{enabled}-{target}.json", {
                            "armature_profile": armature, "response": response,
                            "limits_enabled": enabled, "target_m": target,
                            "initial_readback": initial, "samples": rows,
                            "options": options.model_dump(mode="json"),
                            "build_init_wall_s": build_time, "step_wall_s": step_time,
                            "observation_wall_s": observation_time})
                except Exception as error:
                    write_json(output / f"{name}-{enabled}-error.json",
                               {"type": type(error).__name__, "message": str(error)})
                    raise
                finally:
                    gs.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
