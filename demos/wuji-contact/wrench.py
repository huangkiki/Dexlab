"""Point-contact wrench geometry in world coordinates."""

import numpy as np


def point_force_map(points, center, length_scale):
    """Map point forces to total force and length-scaled moment about the COM."""
    blocks = []
    for point in points:
        x, y, z = (np.asarray(point) - center) / length_scale
        cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
        blocks.append(np.vstack([np.eye(3), cross]))
    return np.hstack(blocks)
