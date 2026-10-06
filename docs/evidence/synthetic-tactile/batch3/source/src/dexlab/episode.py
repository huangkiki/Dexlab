"""One native physics step per coroutine send, with measured state snapshots.

The coroutine keeps the engine's scene and cleanup scope alive across calls.
Closing it executes the native owner's finally block, including on early exit.
"""

from dataclasses import dataclass
from threading import Lock

import numpy as np

SCENE_LOCK = Lock()  # SuperDex initialization/shutdown is process-global.


@dataclass
class GraspFrame:
    time: float
    joint_names: tuple[str, ...]
    joint_position: np.ndarray
    apple_pose: np.ndarray  # xyz + xyzw, privileged state for this baseline
    target: np.ndarray
    summary: dict | None = None


def run_prior(episode):
    """Compatibility runner for the standalone scripted experiment."""
    try:
        frame = next(episode)
        while frame.summary is None:
            frame = episode.send(frame.target.copy())
        return frame.summary
    finally:
        episode.close()
