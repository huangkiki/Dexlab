"""Explicit single-environment contact diagnostics, including friction patches.

Normal contacts and friction anchors are distinct native records, not a
one-to-one correspondence. Arrays are copied before the next SDK query can
overwrite its shared count/index buffers. No engine SDK is imported here.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def compact_patches(
    buffers: tuple[np.ndarray, ...], target_ids: list[int], capacity: int
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Validate native ragged slices and retain only initialized contact rows."""
    *values, counts, starts = buffers
    shape = (1, len(target_ids))
    if counts.shape != shape or starts.shape != shape:
        raise ValueError("Contact patch counts do not match declared body filters")
    if counts.dtype.kind not in "iu" or starts.dtype.kind not in "iu":
        raise ValueError("Contact patch counts/indices must be integers")
    indices: list[int] = []
    owners: list[int] = []
    for body, count, start in zip(target_ids, counts[0], starts[0]):
        count, start = int(count), int(start)
        if count < 0 or (count and (start < 0 or start + count >= capacity)):
            raise ValueError("Contact buffer is invalid or may be saturated")
        indices.extend(range(start, start + count))
        owners.extend([body] * count)
    if len(indices) != len(set(indices)):
        raise ValueError("Contact patch ranges overlap")
    selected = np.asarray(indices, dtype=np.int64)
    packed = []
    for value in values:
        if value.ndim != 2 or value.shape[0] != capacity:
            raise ValueError("Native contact buffer has an unexpected shape")
        row = value[selected].copy()
        if not np.isfinite(row).all():
            raise ValueError("Native contact data contains nonfinite values")
        packed.append(row)
    return np.asarray(owners, dtype=np.int64), packed


class ContactDetails:
    """Own a native contact view and immutable snapshots for an explicit request."""

    def __init__(self, view: Any, target_ids: list[int], capacity: int) -> None:
        self.view = view
        self.target_ids = target_ids
        self.capacity = capacity
        self.latest: dict[str, np.ndarray] | None = None

    def poll(self, dt: float) -> None:
        def copy_buffers(values: Any) -> tuple[np.ndarray, ...]:
            return tuple(value.detach().cpu().numpy().copy() for value in values)

        normal = copy_buffers(self.view.get_contact_data(dt))
        normal_ids, normal_values = compact_patches(normal, self.target_ids, self.capacity)
        if len(normal_values) != 4:
            raise ValueError("Expected force, point, normal and separation buffers")
        force, point, direction, distance = normal_values
        if (force.shape != (len(normal_ids), 1) or point.shape != (len(normal_ids), 3)
                or direction.shape != point.shape or distance.shape != force.shape):
            raise ValueError("Malformed normal-contact rows")
        # This query may reuse the normal-contact count/index tensors.
        friction = copy_buffers(self.view.get_friction_data(dt))
        friction_ids, friction_values = compact_patches(
            friction, self.target_ids, self.capacity
        )
        if len(friction_values) != 2:
            raise ValueError("Expected friction force and anchor buffers")
        friction_force, friction_point = friction_values
        if (friction_force.shape != (len(friction_ids), 3)
                or friction_point.shape != friction_force.shape):
            raise ValueError("Malformed friction-contact rows")
        self.latest = {
            "normal_body_ids": normal_ids,
            "normal_force": force * direction,
            "normal_magnitude": force[:, 0],
            "normal_point": point,
            "normal_direction": direction,
            "separation": distance[:, 0],
            "friction_body_ids": friction_ids,
            "friction_force": friction_force,
            "friction_point": friction_point,
        }
