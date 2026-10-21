#!/usr/bin/env python3
"""Check the selected MuJoCo runtime before discovering this checkout's tests."""

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (str(ROOT / "src"), str(ROOT / "demos/apple-stem-grasp/src"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mujoco-profile", default=os.environ.get("DEXLAB_MUJOCO_PROFILE"),
                        help="Explicit compatibility profile; otherwise use DEXLAB_MUJOCO_PROFILE")
    parser.add_argument("--pattern", default="test_*.py", help="Unittest discovery filename pattern")
    parser.add_argument("--check-only", action="store_true", help="Check runtime without running tests")
    args = parser.parse_args(argv)
    if not args.mujoco_profile:
        parser.error("Select --mujoco-profile or set DEXLAB_MUJOCO_PROFILE explicitly "
                     "(for example historical-3.11.0 for the historical environment, "
                     "or qualification-3.16.0 for a matching candidate environment).")

    # The interpreter supplies dependencies; this checkout supplies reviewed code.
    sys.path[:0] = SOURCE_DIRS
    runtime = {"python": sys.executable, "profile": args.mujoco_profile,
               "checkout": str(ROOT)}
    try:
        import dexlab
        from dexlab.engine_versions import mujoco_profile_identity
        runtime["source"] = str(Path(dexlab.__file__).resolve())
        if not Path(runtime["source"]).is_relative_to(ROOT / "src/dexlab"):
            raise ValueError("DexLab was already imported from another checkout")
        runtime["package"] = version("mujoco")
        import mujoco
        runtime["native"] = mujoco.mj_versionString()
        print("Test runtime: " + json.dumps(runtime), flush=True)
        mujoco_profile_identity({"version": runtime["package"]}, runtime["native"],
                                profile=args.mujoco_profile)
    except (ImportError, OSError, ValueError) as error:
        print("Test preflight failed: " + str(error), file=sys.stderr)
        print(json.dumps(runtime), file=sys.stderr)
        print("Use the interpreter for the intended environment and select its explicit "
              "--mujoco-profile. No packages were changed; the test suite was not started.",
              file=sys.stderr)
        return 2

    if args.check_only:
        return 0
    environment = {**os.environ, "DEXLAB_MUJOCO_PROFILE": args.mujoco_profile}
    inherited = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join((*SOURCE_DIRS, *([inherited] if inherited else [])))
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", args.pattern],
        cwd=ROOT, env=environment, check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
