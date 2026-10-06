"""Offline checks of saved synthetic maps, isolated calls and analytic volume."""

import numpy as np
from dexlab.tactile_depth import depth_map


def rotation(quaternion):
    w, x, y, z = quaternion
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def audit_observations(arrays, resolution):
    pose = arrays["pose"]
    images = arrays["maps"]
    if pose.shape != (6001, 7) or images.shape != (150, resolution, resolution):
        raise ValueError("Missing frozen every-step state or 50 Hz maps")
    maximum_error = 0.0
    volumes = []
    for i, image in enumerate(images):
        state = pose[(i + 1) * 40]
        r = rotation(state[3:])
        actual = depth_map(state[:3], r, resolution=resolution)
        maximum_error = max(maximum_error, float(np.max(abs(actual - image))))
        if np.max(abs(r - np.eye(3))) <= 1e-12:
            widths = np.maximum(
                0,
                np.minimum(0.04, state[:2] + 0.02)
                - np.maximum(-0.04, state[:2] - 0.02),
            )
            height = max(0.0, min(0.001, state[2] + 0.02) - max(0.0, state[2] - 0.02))
            reference = float(np.prod(widths) * height)
            measured = float(image.sum() * (0.08 / resolution) ** 2)
            volumes.append(
                {
                    "step": (i + 1) * 40,
                    "reference_m3": reference,
                    "sampled_m3": measured,
                    "absolute_error_m3": abs(measured - reference),
                }
            )
    # Replay unrelated paths/resolutions and mutate returned maps before the
    # same exact final observation: no native state is changed by this test.
    state = pose[-1]
    expected = depth_map(state[:3], rotation(state[3:]), resolution=resolution)
    for index in (0, 2000, 4000):
        other = pose[index]
        image = depth_map(
            other[:3], rotation(other[3:]), resolution=64 if resolution == 32 else 32
        )
        image[:] = -1
    repeated = depth_map(state[:3], rotation(state[3:]), resolution=resolution)
    isolated = bool(np.array_equal(expected, repeated))
    finite = bool(np.isfinite(images).all())
    return {
        "passed": finite and maximum_error <= 1e-12 and isolated,
        "stored_map_maximum_error_m": maximum_error,
        "same_state_interleaved_calls_equal": isolated,
        "axis_aligned_volume_references": volumes,
        "limits": "Stored-map recomputation checks provenance, not independent material fidelity. Analytic volume applies only to axis-aligned samples. Exact-pose call histories are an observer test, not new native trajectories.",
    }
