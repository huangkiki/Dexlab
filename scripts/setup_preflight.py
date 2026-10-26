#!/usr/bin/env python3
"""Admit a historical installer target without importing any native engine."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from urllib.parse import unquote, urlparse

PROFILE = "historical-3.11.0"
MARKER = "dexlab-environment.json"


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def inspect_environment():
    """Executed by the target interpreter; inspect metadata, never engine code."""
    from importlib.metadata import distributions

    prefix = Path(sys.prefix).resolve()
    packages = []
    for dist in distributions():
        location = Path(dist.locate_file("")).resolve()
        external = not location.is_relative_to(prefix)
        # A local site directory can still contain links into a shared runtime.
        external |= any(not Path(dist.locate_file(entry)).resolve().is_relative_to(prefix)
                        for entry in (dist.files or ()))
        packages.append({"name": canonical(dist.metadata["Name"]), "version": dist.version,
                         "external": external,
                         "origin": json.loads(dist.read_text("direct_url.json") or "null")})
    return {"prefix": str(prefix), "base_prefix": str(Path(sys.base_prefix).resolve()),
            "python": list(sys.version_info[:2]), "packages": packages}


def pinned_versions(root, source):
    files = ["demos/apple-stem-grasp/requirements.txt", "scripts/python-constraints.txt",
             "scripts/runtime-requirements.txt"]
    if source:
        files.append("scripts/source-build-requirements.txt")
    pins = {}
    for name in files:
        for line in (root / name).read_text().splitlines():
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;]+)", line.strip())
            if match:
                key, version = canonical(match[1]), match[2]
                if key in pins and pins[key] != version:
                    raise ValueError(f"Conflicting installer pins for {key}")
                pins[key] = version
    return pins


def admit(root, *, profile, source=False, claim=False):
    if profile != PROFILE:
        raise ValueError(f"Setup targets {PROFILE}; requested {profile}. No environment was changed.")
    target = root / ".venv"
    if not target.exists() and not target.is_symlink():
        return "new environment"
    python = target / "bin/python"
    if not python.is_file():
        raise ValueError("Existing .venv is incomplete or a broken link; preserve it and use a separate checkout.")
    probe = subprocess.run([str(python), "-I", "-B", "-c",
                            "import json, runpy, sys; "
                            "print(json.dumps(runpy.run_path(sys.argv[1])['inspect_environment']()))",
                            str(Path(__file__).resolve())],
                           text=True, capture_output=True, check=True)
    observed = json.loads(probe.stdout)
    actual = target.resolve()
    if (observed["python"] != [3, 12] or observed["prefix"] != str(actual)
            or observed["prefix"] == observed["base_prefix"]):
        raise ValueError("Target must be its own Python 3.12 virtual environment.")
    pins = pinned_versions(root, source)
    editable_owner = False
    packages = observed["packages"]
    for package in packages:
        name, version = package["name"], package["version"]
        if package["external"]:
            raise ValueError(f"{name} is inherited or linked from outside this environment; shared packages are not install targets.")
        if name in pins and version != pins[name]:
            raise ValueError(f"Installed {name} {version} conflicts with {PROFILE} pin {pins[name]}.")
        if name == "dexlab":
            origin = package["origin"] or {}
            url = urlparse(origin.get("url", ""))
            editable_owner = (origin.get("dir_info", {}).get("editable") is True
                              and url.scheme == "file" and url.netloc in ("", "localhost")
                              and Path(unquote(url.path)).resolve() == root)
            if not editable_owner:
                raise ValueError("Existing DexLab install belongs to another checkout or is not editable.")
    marker = actual / MARKER
    expected = {"schema_version": 1, "checkout": str(root), "profile": PROFILE}
    if marker.is_symlink():
        raise ValueError("Environment ownership marker must not be a symlink.")
    if marker.exists():
        if json.loads(marker.read_text()) != expected:
            raise ValueError("Environment ownership/profile differs; --claim-environment cannot take it over.")
    else:
        if target.is_symlink():
            if not claim:
                raise ValueError("Unowned linked environment: use --claim-environment only for a dedicated compatible target.")
            if not editable_owner and any(p["name"] not in {"pip", "setuptools", "wheel"} for p in packages):
                raise ValueError("Cannot claim a populated shared environment without this checkout's editable DexLab ownership.")
        # Exclusive creation also prevents two checkouts claiming the same target.
        try:
            with marker.open("x") as stream:
                json.dump(expected, stream, indent=2)
                stream.write("\n")
        except FileExistsError:
            if json.loads(marker.read_text()) != expected:
                raise ValueError("Another checkout claimed this environment.") from None
    return str(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mujoco-profile", default=os.environ.get("DEXLAB_MUJOCO_PROFILE", PROFILE))
    parser.add_argument("--claim-environment", action="store_true",
                        help="Claim a dedicated linked venv after compatibility/ownership checks; never override another owner.")
    parser.add_argument("--source", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        target = admit(root, profile=args.mujoco_profile, source=args.source,
                       claim=args.claim_environment)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        separate = shlex.quote(str(root.parent / "Dexlab-historical"))
        print(f"Setup refused: {error}\nPreserve this environment. Choose an unused checkout path, for example:\n"
              f"git clone https://github.com/huangkiki/Dexlab.git {separate}\n"
              f"cd {separate}\nbash scripts/setup.sh --mujoco-profile {PROFILE}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Setup target: {PROFILE}; {target}")


if __name__ == "__main__":
    main()
