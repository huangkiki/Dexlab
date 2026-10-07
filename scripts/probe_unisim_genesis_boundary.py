"""Inspect an unchanged UniSim Genesis boundary; never construct or step a scene.

Run in an isolated environment under the repository resource wrapper.
--initialize explicitly calls materialization after recording loader rejection;
this diagnostic is not backend admission or physics qualification.
"""
import argparse
import hashlib
import inspect
import json
from importlib import metadata
from pathlib import Path


def probe(initialize=False):
    from unisim.backend.genesis import dependencies, materialization, backend

    result = {
        "scope": "Admission diagnostic only; no scene, physics or equivalence claim",
        "packages": {name: metadata.version(name) for name in
                     ("unisim-core", "genesis-world", "quadrants", "torch", "mujoco")},
        "source_sha256": {module.__name__: hashlib.sha256(
            Path(module.__file__).read_bytes()).hexdigest()
            for module in (dependencies, materialization, backend)},
    }
    try:
        dependencies.load_genesis_dependencies()
    except dependencies.GenesisDependencyError as error:
        result["loader"] = {"accepted": False, "reason": str(error)}
    else:
        result["loader"] = {"accepted": True}
    if initialize:
        import genesis as gs
        import torch
        import mujoco

        result["initialization_scope"] = (
            "Explicit direct call to unchanged materialization, independent of loader verdict; "
            "does not authorize this runtime combination")
        result["genesis_init_default_precision"] = inspect.signature(gs.init).parameters["precision"].default
        deps = dependencies.GenesisDependencies(genesis=gs, torch=torch, mujoco=mujoco)
        try:
            materialization.init_genesis_session(deps)
            tensor, array = backend._make_device_cache(torch, (1, 3))
            result["observed"] = {"native_float_dtype": str(gs.tc_float),
                                  "tensor_cache_dtype": str(tensor.dtype),
                                  "numpy_cache_dtype": str(array.dtype)}
        finally:
            materialization.destroy_genesis_session(deps)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--initialize", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve previous evidence; choose a new output")
    result = probe(args.initialize)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
