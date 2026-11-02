"""Validate the legacy Sharpa motion consumed by the pinned native command.

The dual-hand task uses ManoSharpaData, not the newer motion_v1 reader used by
whole-body tasks. Import this module without Isaac Sim; load() requires the
pinned robotic_grounding package and numpy in the isolated CHORD environment.
"""

import math
from pathlib import Path


def validate(data):
    """Reject empty, misaligned or nonphysical reference arrays before training."""
    import numpy as np

    fps = float(data.fps)
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("Reference fps must be finite and positive")
    frames = len(data.robot_right_wrist_position)
    if frames < 2:
        raise ValueError("Retargeted motion requires at least two robot frames")
    bodies = len(data.object_body_names)
    if not bodies:
        raise ValueError("A CHORD manipulation reference requires an object body")
    shapes = {"object_body_position": (frames, bodies, 3),
              "object_body_wxyz": (frames, bodies, 4)}
    for side in ("left", "right"):
        names = getattr(data, f"{side}_robot_finger_joint_names")
        if not names or len(names) != len(set(names)):
            raise ValueError(f"{side} finger joint names must be nonempty and unique")
        shapes.update({f"robot_{side}_wrist_position": (frames, 3),
                       f"robot_{side}_wrist_wxyz": (frames, 4),
                       f"robot_{side}_finger_joints": (frames, len(names))})
    fields = {}
    for name, shape in shapes.items():
        array = np.asarray(getattr(data, name), dtype=float)
        if array.shape != shape or not np.isfinite(array).all():
            raise ValueError(f"{name}: expected finite reference array {shape}, got {array.shape}")
        fields[name] = {"shape": list(shape)}
        if name.endswith("wxyz"):
            norm_error = float(np.max(np.abs(np.linalg.norm(array, axis=-1) - 1)))
            # Float32 serialized rotations should retain unit length; this is
            # input validity, not an evaluation success tolerance.
            if norm_error > 1e-4:
                raise ValueError(f"{name}: non-unit quaternion (max norm error {norm_error})")
            fields[name]["max_quaternion_norm_error"] = norm_error
    return {"reader": "robotic_grounding.retarget.data_logger.ManoSharpaData.from_parquet",
            "fps": fps, "frames": frames, "reference_span_s": (frames - 1) / fps,
            "object_body_names": list(data.object_body_names), "fields": fields}


def load(partition):
    """Load exactly one partition without rewriting or migrating source data."""
    from robotic_grounding.retarget.data_logger import ManoSharpaData

    partition = Path(partition)
    files = sorted(partition.glob("*.parquet"))
    if len(files) != 1:
        raise ValueError(f"Expected exactly one motion parquet in {partition}, found {len(files)}")
    data = ManoSharpaData.from_parquet(str(partition))
    return {"path": str(files[0]), **validate(data)}
