"""Standalone Python 3.11 worker for the pinned official surface-deformable API.

No DexLab/UniSim package import is required in the SDK environment. Only explicit
world attachments constrain pinned vertices; node states are reset once before
recording and are never overwritten during the measured trajectory.
"""

import hashlib
import inspect
import json
import sys
import traceback
from multiprocessing.connection import Connection
from pathlib import Path

import numpy as np


def launch(config):
    from isaaclab.app import AppLauncher

    output = Path(config["directory"])
    original = (
        Path(inspect.getfile(AppLauncher)).resolve().parents[4]
        / "apps/isaaclab.python.headless.kit"
    )
    # Separate app configuration: retain official physics/core dependencies, omit
    # unrelated RL/task extensions. The installed SDK/IsaacLab files stay intact.
    experience = output / "cloth-headless.kit"
    experience.write_text(
        "\n".join(
            line
            for line in original.read_text().splitlines()
            if not line.startswith(('"isaaclab"', '"isaaclab_'))
        )
    )
    (output / "IsaacLab-LICENSE.txt").write_bytes(
        (original.parents[1] / "LICENSE").read_bytes()
    )
    app = AppLauncher(
        {
            "headless": True,
            "enable_cameras": False,
            "device": config["device"],
            "multi_gpu": False,
            "experience": str(experience),
        }
    ).app
    return app, hashlib.sha256(original.read_bytes()).hexdigest()


def scene(config, experience_hash):
    from importlib.metadata import version

    import isaaclab.sim as sim_utils
    import omni.physics.tensors
    import torch
    from omni.physx.scripts import deformableUtils, physicsUtils
    from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics, Vt

    case = config["case"]
    vertices = np.asarray(config["vertices"], dtype=np.float32)
    triangles = np.asarray(config["triangles"], dtype=np.int32)
    pins = np.asarray(config["pins"], dtype=np.int32)
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(
            dt=config["dt"],
            device=config["device"],
            gravity=(0, 0, -9.81),
        )
    )
    stage = sim.stage
    mesh = UsdGeom.Mesh.Define(stage, "/World/cloth")
    mesh.CreatePointsAttr().Set(Vt.Vec3fArray.FromNumpy(vertices))
    mesh.CreateFaceVertexCountsAttr().Set([3] * len(triangles))
    mesh.CreateFaceVertexIndicesAttr().Set(triangles.ravel().tolist())
    mesh.CreateSubdivisionSchemeAttr().Set("none")
    if not deformableUtils.set_physics_surface_deformable_body(stage, mesh.GetPath()):
        raise RuntimeError("Official surface-deformable schema setup failed")
    prim = mesh.GetPrim()
    prim.ApplyAPI("PhysxSurfaceDeformableBodyAPI")
    settings = {
        "physxDeformableBody:selfCollision": True,
        "physxDeformableBody:enableSpeculativeCCD": True,
        "physxDeformableBody:solverPositionIterationCount": config["iterations"],
        "physxDeformableBody:maxLinearVelocity": 100.0,
        "physxDeformableBody:linearDamping": 0.0,
        "physxDeformableBody:sleepThreshold": 0.0,
        "physxDeformableBody:settlingThreshold": 0.0,
    }
    for key, value in settings.items():
        attribute = prim.GetAttribute(key)
        if not attribute:
            raise RuntimeError(f"Missing pinned SDK attribute: {key}")
        attribute.Set(value)
    collision = PhysxSchema.PhysxCollisionAPI.Apply(prim)
    collision.CreateRestOffsetAttr().Set(case["radius"])
    collision.CreateContactOffsetAttr().Set(2 * case["radius"])
    mass = float(np.sum(config["masses"]))
    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr().Set(mass)
    thickness = 0.0005
    deformableUtils.add_surface_deformable_material(
        stage,
        "/World/material",
        density=case["areal_density"] / thickness,
        dynamic_friction=0.5,
        youngs_modulus=20000.0,
        poissons_ratio=0.0,
        surface_thickness=thickness,
    )
    physicsUtils.add_physics_material_to_prim(stage, prim, "/World/material")
    material = stage.GetPrimAtPath("/World/material")
    material.ApplyAPI("PhysxSurfaceDeformableMaterialAPI")
    material.GetAttribute("physxDeformableMaterial:elasticityDamping").Set(0.0)
    material.GetAttribute("physxDeformableMaterial:bendDamping").Set(0.0)
    if len(pins):
        UsdGeom.Xform.Define(stage, "/World/anchor")
        attachment = stage.DefinePrim("/World/pins", "OmniPhysicsVtxXformAttachment")
        attachment.GetRelationship("omniphysics:src0").SetTargets(["/World/cloth"])
        attachment.GetRelationship("omniphysics:src1").SetTargets(["/World/anchor"])
        attachment.GetAttribute("omniphysics:vtxIndicesSrc0").Set(pins.tolist())
        attachment.GetAttribute("omniphysics:localPositionsSrc1").Set(
            Vt.Vec3fArray.FromNumpy(vertices[pins])
        )
    if case["experiment"] in ("drape", "folded-drop"):
        plane = UsdGeom.Cube.Define(stage, "/World/ground")
        plane.CreateSizeAttr().Set(2.0)
        plane.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.01))
        plane.AddScaleOp().Set(Gf.Vec3d(2, 2, 0.01))
        UsdPhysics.CollisionAPI.Apply(plane.GetPrim())
    if case["experiment"] == "drape":
        sphere = UsdGeom.Sphere.Define(stage, "/World/sphere")
        sphere.CreateRadiusAttr().Set(case["sphere_radius"])
        sphere.AddTranslateOp().Set(Gf.Vec3d(0, 0, case["sphere_height"]))
        UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
    stage.Export(str(Path(config["directory"]) / "scene.usda"))
    # Initialize without extra render warm-up, then restore the declared initial
    # state once. SDK initialization itself may still advance native physics.
    sim.initialize_physics()
    tensor_sim = omni.physics.tensors.create_simulation_view("torch")
    tensor_sim.set_subspace_roots("/")
    view = tensor_sim.create_surface_deformable_body_view("/World/cloth")
    if (
        view.count != 1
        or view.max_simulation_nodes_per_body != len(vertices)
        or view.num_nodes_per_element != 3
    ):
        raise RuntimeError("Native surface topology dimensions changed")
    rest = view.get_rest_nodal_positions().cpu().numpy().copy()[0]
    elements = view.get_simulation_element_indices().cpu().numpy().copy()[0]
    if not np.array_equal(rest, vertices) or not np.array_equal(elements, triangles):
        raise RuntimeError(
            "Native mesh ordering/rest shape differs from the shared mesh"
        )
    warmup_positions = view.get_simulation_nodal_positions().cpu().numpy().copy()[0]
    warmup_velocities = view.get_simulation_nodal_velocities().cpu().numpy().copy()[0]
    indices = torch.tensor([0], device=config["device"], dtype=torch.int32)
    view.set_simulation_nodal_positions(
        torch.tensor(vertices[None], device=config["device"]), indices
    )
    view.set_simulation_nodal_velocities(
        torch.zeros((1, len(vertices), 3), device=config["device"]), indices
    )
    np.savez_compressed(
        Path(config["directory"]) / "native-initial.npz",
        rest=rest,
        elements=elements,
        warmup_positions=warmup_positions,
        warmup_velocities=warmup_velocities,
    )
    metadata = {
        "engine": "PhysX surface deformable beta / Isaac Sim 5.1",
        "packages": {name: version(name) for name in ("isaacsim", "isaaclab", "torch")},
        "gpu": torch.cuda.get_device_name(config["device"]),
        "experience_source_sha256": experience_hash,
        "native_api_source_sha256": {
            "deformableUtils.py": hashlib.sha256(
                Path(inspect.getfile(deformableUtils)).read_bytes()
            ).hexdigest(),
            "tensor_api.py": hashlib.sha256(
                Path(inspect.getfile(type(view))).read_bytes()
            ).hexdigest(),
        },
        "representation": "original triangle surface; no particle-cloth or volume surrogate",
        "native_mesh_matches": True,
        "native_vertex_count": len(vertices),
        "native_triangle_count": len(triangles),
        "authored_total_mass_kg": mass,
        "mass_observation": "USD-authored mass and density/thickness; this tensor API exposes no nodal mass readback",
        "material": {
            attribute.GetName(): attribute.Get()
            for attribute in material.GetAttributes()
            if attribute.GetName().startswith(
                ("omniphysics:", "physxDeformableMaterial:")
            )
            and isinstance(attribute.Get(), (float, int, bool, str))
        },
        "body_settings": {key: prim.GetAttribute(key).Get() for key in settings},
        "rest_offset_m": collision.GetRestOffsetAttr().Get(),
        "contact_offset_m": collision.GetContactOffsetAttr().Get(),
        "particle_velocity_limit_m_s": 100.0,
        "parameter_provenance": "nominal engineering profile; not calibrated across solvers or hardware",
        "initialization": "one native position/velocity reset after SDK initialization; warm-up state archived",
        "boundary": "explicit vertex-to-world-anchor attachments; no position/velocity writes after initialization",
        "nodal_force_upload": False,
        "velocity_observation": "actual native surface node positions and velocities",
    }
    return sim, tensor_sim, view, metadata


def observe(view):
    return {
        "positions": view.get_simulation_nodal_positions().cpu().numpy()[0].tolist(),
        "velocities": view.get_simulation_nodal_velocities().cpu().numpy()[0].tolist(),
    }


def main(fd):
    connection = Connection(fd)
    app = sim = _tensor_sim = view = None
    stop_requested = False
    try:
        config = json.loads(connection.recv_bytes())
        if config.get("op") != "init":
            raise ValueError("First worker command must initialize the scene")
        app, experience_hash = launch(config)
        sim, _tensor_sim, view, metadata = scene(config, experience_hash)
        connection.send_bytes(
            json.dumps(
                {"metadata": metadata, **observe(view)}, allow_nan=False
            ).encode()
        )
        while True:
            request = json.loads(connection.recv_bytes())
            if request == {"op": "stop"}:
                stop_requested = True
                break
            if request != {"op": "step"}:
                raise ValueError("Unknown native cloth command")
            sim.step(render=False)
            connection.send_bytes(json.dumps(observe(view), allow_nan=False).encode())
    except Exception:  # noqa: BLE001 -- transport native traceback to the host
        connection.send_bytes(json.dumps({"error": traceback.format_exc()}).encode())
    finally:
        # The official stop callback renders indefinitely while the timeline is
        # stopped. Clear its subscription through the public lifecycle method.
        if app is not None:
            import isaaclab.sim as sim_utils

            sim_utils.SimulationContext.clear_instance()
            if sim is not None:
                sim.stop()
            if stop_requested:
                connection.send_bytes(b'{"stopped": true}')
            connection.close()
            app.close(wait_for_replicator=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
