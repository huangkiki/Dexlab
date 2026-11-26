"""Step a falling box in Bullet, with and without floor contact."""

import json
from statistics import mean

import pybullet as bullet

TIME_STEP = 1 / 240
STEPS = 480
HALF_SIDE = 0.10
MASS = 1.0
GRAVITY = 9.81


def run_drop(*, collision_enabled: bool) -> dict:
    client = bullet.connect(bullet.DIRECT)
    if client < 0:
        raise RuntimeError("Could not start a PyBullet DIRECT client")
    try:
        bullet.setTimeStep(TIME_STEP, physicsClientId=client)
        bullet.setPhysicsEngineParameter(numSubSteps=0, physicsClientId=client)
        bullet.setGravity(0, 0, -GRAVITY, physicsClientId=client)
        plane_shape = bullet.createCollisionShape(
            bullet.GEOM_PLANE, planeNormal=(0, 0, 1), physicsClientId=client
        )
        floor = bullet.createMultiBody(
            baseMass=0, baseCollisionShapeIndex=plane_shape, physicsClientId=client
        )
        box_shape = bullet.createCollisionShape(
            bullet.GEOM_BOX, halfExtents=(HALF_SIDE,) * 3, physicsClientId=client
        )
        box = bullet.createMultiBody(
            baseMass=MASS,
            baseCollisionShapeIndex=box_shape,
            basePosition=(0, 0, 1),
            physicsClientId=client,
        )
        bullet.changeDynamics(floor, -1, restitution=0, physicsClientId=client)
        bullet.changeDynamics(
            box, -1, restitution=0, linearDamping=0, angularDamping=0,
            physicsClientId=client,
        )
        bullet.setCollisionFilterPair(
            box, floor, -1, -1, int(collision_enabled), physicsClientId=client
        )

        first_support_step = None
        support_forces = []
        for step in range(1, STEPS + 1):
            bullet.stepSimulation(physicsClientId=client)
            contacts = bullet.getContactPoints(box, floor, physicsClientId=client)
            # Fields 7 and 9 are the normal on B (floor) and the normal force.
            support_z = sum(point[7][2] * point[9] for point in contacts)
            support_forces.append(support_z)
            if first_support_step is None and support_z > 0:
                first_support_step = step

        position, _ = bullet.getBasePositionAndOrientation(box, physicsClientId=client)
        linear_velocity, _ = bullet.getBaseVelocity(box, physicsClientId=client)
        return {
            "collision_enabled": collision_enabled,
            "first_support_step": first_support_step,
            "final_center_z_m": position[2],
            "final_vertical_speed_m_s": linear_velocity[2],
            "mean_support_z_last_half_second_n": mean(support_forces[-120:]),
        }
    finally:
        bullet.disconnect(physicsClientId=client)


if __name__ == "__main__":
    results = [run_drop(collision_enabled=True), run_drop(collision_enabled=False)]
    print(json.dumps(results, indent=2))
