"""Native SuperDex setup and the three helpers used by this demo."""
import os
os.environ["SUPERDEX_PRECISION"] = "fp64"
from superdex import physics, robotics
import numpy as np

def smooth(t: float, start: float, duration: float) -> float:
    x = np.clip((t - start) / duration, 0, 1)
    return float(x * x * (3 - 2 * x))

def create_mesh_actor(scene, mesh, name, position, *, static=False, box=False):
    shape = physics.create_tri_mesh_shape(
        coordinates=np.asarray(mesh.vertices, float).ravel(),
        connectivity=np.asarray(mesh.faces, np.int32).ravel(),
    )
    try:
        return scene.create_rigid_actor(
            name=name,
            shape=shape,
            is_static=static,
            density=250,
            collider_type=physics.ColliderType.BOX
            if box
            else physics.ColliderType.AUTO,
            world_from_local=physics.TransformRT(translation=position),
        )
    finally:
        physics.release_shape(shape)

def actor_poses(actors):
    poses = []
    for actor in actors:
        transform = actor.get_root_transform()
        poses.append(
            np.r_[np.array(transform.translation), np.array(transform.rotation)]
        )
    return np.array(poses)
