"""Plan the second grasp from the apple's released pose, using an isolated FK robot."""

import itertools

import numpy as np
from physics_utils import smooth
from apple_scene import CLOSED, OPEN, PALM_ROTATION, physics, robotics, solve_arm


def plan_body_grasp(prefab, context, reference, arm, hand, bounds, apple_position):
    """Never change the live robot or apple while evaluating inverse kinematics."""
    scene = physics.create_scene("body grasp inverse kinematics only")
    bot = None
    try:
        bot = robotics.create_bot(scene, prefab, context)
        actor = bot.get_articulated_actor()
        links = [scene.get_actor(h) for h in actor.get_nested_link_actors()]
        wrist = links[[link.name for link in prefab.links].index("r_wrist")]
        opened = reference.copy()
        opened[hand] = OPEN
        position = np.asarray(apple_position) + [0.03, -0.10, 0.045]
        pre = solve_arm(
            actor, wrist, opened, arm, bounds, position + [0, 0, 0.14], PALM_ROTATION
        )
        grasp = solve_arm(actor, wrist, pre, arm, bounds, position, PALM_ROTATION)
        closed = grasp.copy()
        closed[hand] = CLOSED
        raised = solve_arm(
            actor, wrist, closed, arm, bounds, position + [0, 0, 0.16], PALM_ROTATION
        )
        return [
            (23.0, reference.copy()),
            (26.0, pre),
            (29.0, grasp),
            (29.5, grasp),
            (32.5, closed),
            (33.0, closed),
            (36.0, raised),
            (40.0, raised),
        ]
    finally:
        if bot is not None:
            robotics.destroy_bot(scene, bot)
        physics.destroy_scene(scene)


def body_target(keyframes, time):
    for (start, first), (end, second) in itertools.pairwise(keyframes):
        if time <= end:
            return first + smooth(time, start, end - start) * (second - first)
    return keyframes[-1][1].copy()
