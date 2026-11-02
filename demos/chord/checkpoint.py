#!/usr/bin/env python3
"""Inspect optimizer evidence in a locally produced RSL-RL checkpoint.

This is serialization/update evidence. Actual policy reload is a separate
native evaluation, and neither establishes a learned manipulation skill.
"""

import argparse
import hashlib
import json
from pathlib import Path


def inspect(path):
    import torch

    state = torch.load(path, map_location="cpu", weights_only=True)
    parameters = state["model_state_dict"]
    optimizer = state["optimizer_state_dict"]
    if not parameters or not optimizer["state"]:
        raise ValueError("Checkpoint lacks model parameters or optimizer update state")
    steps, nonzero_moments = [], 0
    for item in optimizer["state"].values():
        step = float(item["step"])
        if not step.is_integer() or step <= 0:
            raise ValueError("Checkpoint has an unexecuted optimizer state")
        steps.append(int(step))
        for name in ("exp_avg", "exp_avg_sq"):
            value = item[name]
            if not torch.isfinite(value).all():
                raise ValueError(f"Nonfinite optimizer {name}")
            nonzero_moments += int(torch.count_nonzero(value))
    if not nonzero_moments:
        raise ValueError("Optimizer moments contain no update evidence")
    digest = hashlib.sha256()
    for name, tensor in sorted(parameters.items()):
        if not torch.isfinite(tensor).all():
            raise ValueError(f"Nonfinite model tensor {name}")
        digest.update(name.encode())
        digest.update(str((str(tensor.dtype), tuple(tensor.shape))).encode())
        digest.update(tensor.contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
    with Path(path).open("rb") as stream:
        file_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"checkpoint_sha256": file_hash, "model_tensors_sha256": digest.hexdigest(),
            "model_tensor_count": len(parameters), "saved_iteration": state.get("iter"),
            "optimizer_parameter_states": len(steps), "optimizer_step_min": min(steps),
            "optimizer_step_max": max(steps), "nonzero_moment_elements": nonzero_moments,
            "native_reload": "requires_separate_evaluation", "task_success": "not_inferred"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.checkpoint), indent=2, allow_nan=False))
