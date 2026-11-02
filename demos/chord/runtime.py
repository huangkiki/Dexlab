"""Read runtime identity without importing or initializing the simulator."""

import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import sys


def identity():
    packages = {}
    for name in ("isaaclab", "isaacsim", "rsl-rl-lib", "torch", "pyarrow", "tensordict", "wandb"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    releases = {}
    for name, variable in (("isaaclab", "ISAACLAB_PATH"), ("isaacsim", "ISAACSIM_ROOT_PATH")):
        root = os.environ.get(variable)
        version_file = Path(root) / "VERSION" if root else None
        releases[name] = {
            "version": version_file.read_text().strip() if version_file and version_file.is_file() else packages[name],
            "source": str(version_file) if version_file and version_file.is_file() else "package-metadata",
        }
    spec = importlib.util.find_spec("robotic_grounding")
    return {"python": sys.version.split()[0], "packages": packages, "releases": releases,
            "robotic_grounding": None if spec is None else spec.origin}


if __name__ == "__main__":
    print("DEXLAB_CHORD_PROBE=" + json.dumps(identity()))
