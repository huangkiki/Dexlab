"""Joint-space command prior shared by the two physics backends."""

import numpy as np


def smooth(time, start, duration):
    fraction = np.clip((time - start) / duration, 0, 1)
    return float(fraction * fraction * (3 - 2 * fraction))


def stem_target(plan, time):
    """Approach, close, lift and hold; no object pose is overwritten."""
    arm, hand = plan["arm"], plan["hand"]
    pre, grasp = plan["pre"], plan["grasp"]
    target = pre.copy()
    target[arm] += smooth(time, 0.5, 2) * (grasp[arm] - pre[arm])

    def interpolate(path, fraction):
        coordinate = fraction * (len(path) - 1)
        lower = min(int(coordinate), len(path) - 2)
        blend = coordinate - lower
        return (1 - blend) * path[lower] + blend * path[lower + 1]

    target[hand] = interpolate(plan["hand_path"], smooth(time, 3, 3))[hand]
    target[arm] += interpolate(plan["lift_path"], smooth(time, 7, 3))[arm] - grasp[arm]
    first, opened, closed, raised = plan["feedforward"]
    return (
        target
        + first
        + smooth(time, 0.5, 2) * (opened - first)
        + smooth(time, 3, 3) * (closed - opened)
        + smooth(time, 7, 3) * (raised - closed)
    )
