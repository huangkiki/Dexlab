"""Observed native identities and raw-record rescoring for apple qualification."""

import hashlib
import json
import math
import os
from importlib.metadata import distribution
from pathlib import Path

from dexlab.cloth_engines import package_identity


APPLE_PARAMETERS = (
    "mujoco_height_offset",
    "mujoco_friction",
    "mujoco_pinch_gain",
    "gap",
    "stiffness",
    "friction_velocity",
    "roll",
    "yaw",
    "height_offset",
    "linear_solver",
    "timestep",
    "apple_mass",
    "apple_x_offset",
    "apple_y_offset",
    "apple_yaw",
)


PACKAGES = ("mujoco", "superdex-physics", "superdex-robotics",
            "superdex-physics-fp64", "superdex-robotics-fp64")


def file_hash(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def record_native_file(package, path):
    """Require the actually loaded payload to belong to the audited wheel."""
    path = Path(path).resolve(strict=True)
    dist = distribution(package)
    entries = {Path(dist.locate_file(entry)).resolve(): entry for entry in dist.files or ()}
    if path not in entries:
        raise ValueError(f"Loaded native module is outside {package}'s wheel RECORD")
    entry = entries[path]
    import base64

    digest = file_hash(path)
    encoded = base64.urlsafe_b64encode(bytes.fromhex(digest)).rstrip(b"=").decode()
    if entry.hash is None or entry.hash.mode != "sha256" or entry.hash.value != encoded:
        raise ValueError(f"Loaded native module differs from {package}'s wheel RECORD")
    return digest


def loaded_mujoco_library():
    """Resolve the library mapped by this Linux process, not an install guess."""
    paths = set()
    for row in Path("/proc/self/maps").read_text().splitlines():
        fields = row.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name.startswith("libmujoco.so."):
            paths.add(Path(fields[5]).resolve(strict=True))
    if len(paths) != 1:
        raise ValueError("Expected exactly one actually mapped MuJoCo native library")
    return paths.pop()


def observe_runtime():
    """Observe the shared apple preparation/runtime without creating a scene.

    SuperDex does not expose a native semantic-version API here. Record its
    loaded payload identity and native precision explicitly; do not present
    the facade package version as a reported native version.
    """
    os.environ.setdefault("SUPERDEX_PRECISION", "fp64")
    import mujoco
    import superdex.physics as physics
    import superdex.robotics as robotics

    if not physics.uses_double_precision():
        raise ValueError("Apple qualification requires native SuperDex FP64")
    packages = {name: package_identity(name) for name in PACKAGES}
    payloads = {
        "mujoco": record_native_file("mujoco", loaded_mujoco_library()),
        "superdex-physics-fp64": record_native_file(
            "superdex-physics-fp64", physics._extension.__file__),
        "superdex-robotics-fp64": record_native_file(
            "superdex-robotics-fp64", robotics._extension.__file__),
    }
    return {
        "installed": {name: row["version"] for name, row in packages.items()},
        "native": {
            "mujoco": mujoco.mj_versionString(),
            "superdex": {"version_api": None, "precision": "fp64",
                         "identity_method": "loaded wheel payload SHA256",
                         "physics_sha256": payloads["superdex-physics-fp64"],
                         "robotics_sha256": payloads["superdex-robotics-fp64"]},
        },
        "artifact_sha256": payloads,
        "package_code_sha256": {name: row["code_sha256"] for name, row in packages.items()},
    }


def raw_record_hash(directory, backend):
    """Hash all scorer inputs, including any losslessly packed native model."""
    from dexlab.mujoco_artifacts import model_inputs

    directory = Path(directory)
    paths = [directory / name for name in
             ("engine.json", "unilab.json", "sdf-dynamics.npz", "sdf-contacts.npz",
              "qualification-observation.json")]
    if backend == "mujoco":
        paths += model_inputs(directory)
    elif backend != "superdex":
        raise ValueError("Unsupported apple backend")
    hashes = {path.relative_to(directory).as_posix(): file_hash(path) for path in paths}
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def rescore_record(directory, backend, *, expected_profile, expected_source, runtime):
    """A saved success flag is never used as task-qualification evidence."""
    from verify_sdf_grasp import verify_grasp

    directory = Path(directory)
    before = raw_record_hash(directory, backend)
    observation = json.loads((directory / "qualification-observation.json").read_text())
    if (observation.get("source_unchanged") is not True
            or observation.get("runtime_unchanged") is not True
            or observation.get("source_sha256") != expected_source
            or observation.get("runtime") != runtime
            or observation.get("backend") != backend):
        raise ValueError("Raw record source/native observation differs from this execution")
    metadata = json.loads((directory / "unilab.json").read_text())
    engine = json.loads((directory / "engine.json").read_text())
    if metadata["backend"] != backend or engine["backend"] != backend:
        raise ValueError("Raw record backend mismatch")
    if (observation.get("profile") != expected_profile
            or apple_profile(backend, metadata["parameters"]) != expected_profile
            or engine["dt"] != expected_profile["parameters"]["timestep"]):
        raise ValueError("Raw record configuration differs from the requested profile")
    # The independent scorer checks expected mass against the native model;
    # production qualification uses the declared baseline, not a recorded mass.
    score = verify_grasp(directory, expected_mass=0.2)
    if not score["passed"]:
        raise ValueError("Independent baseline task qualification failed")
    if raw_record_hash(directory, backend) != before:
        raise ValueError("Raw evidence changed during independent scoring")
    return {"raw_record_sha256": before, "profile": expected_profile,
            "checks": score["checks"]}


def apple_profile(backend, parameters):
    """Separate frozen controller/solver settings from benchmark scene variables."""
    from wuji_stem_grasp import parse_args

    if backend not in ("mujoco", "superdex") or set(parameters) - set(APPLE_PARAMETERS):
        raise ValueError("Unknown apple backend or control parameter")
    defaults = parse_args(["--backend", backend])
    merged = {key: getattr(defaults, key) for key in APPLE_PARAMETERS} | parameters
    if merged["timestep"] is None:
        merged["timestep"] = 0.0005 if backend == "mujoco" else 0.002
    if not math.isfinite(merged["timestep"]) or merged["timestep"] <= 0:
        raise ValueError("Qualification timestep must be finite and positive")
    scene = {"apple_mass", "apple_x_offset", "apple_y_offset", "apple_yaw"}
    return {"backend": backend, "device": "cpu", "precision": "float64",
            "parameters": {key: value for key, value in merged.items() if key not in scene}}


def profile_key(profile):
    return profile["backend"] + "-" + hashlib.sha256(
        json.dumps(profile, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()[:16]


def official_json(url):
    """Retry transient transport failures; never substitute cached qualification."""
    import ssl
    import time
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen

    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return json.load(response)
        except HTTPError:
            raise  # Do not retry an explicit server rejection or rate limit.
        except (URLError, ssl.SSLEOFError, TimeoutError, ConnectionError) as error:
            if isinstance(getattr(error, 'reason', error), ssl.SSLCertVerificationError) or attempt == 2:
                raise
            time.sleep(attempt + 1)


def refresh_inventory():
    """Fetch official non-yanked latest stable metadata at a new batch freeze."""
    from datetime import datetime, timezone
    from packaging.version import Version

    rows = []
    for package in PACKAGES:
        source = f"https://pypi.org/pypi/{package}/json"
        payload = official_json(source)
        releases = [Version(version) for version, files in payload["releases"].items()
                    if files and any(not item.get("yanked", False) for item in files)
                    and not Version(version).is_prerelease
                    and not Version(version).is_devrelease and not Version(version).local]
        if not releases:
            raise ValueError(f"No stable non-yanked release found for {package}")
        latest = str(max(releases))
        selected = official_json(f"https://pypi.org/pypi/{package}/{latest}/json")
        files = [item for item in selected["urls"] if not item.get("yanked", False)]
        if not files or Version(selected["info"]["version"]) != Version(latest):
            raise ValueError("Official release metadata changed during collection")
        rows.append({"package": package, "version": latest, "source": source,
                     "checked_at": datetime.now(timezone.utc).isoformat(), "yanked": False,
                     "classifiers": selected["info"].get("classifiers", []),
                     "requires_dist": selected["info"].get("requires_dist"),
                     "distribution_sha256": {item["filename"]: item["digests"]["sha256"]
                                             for item in files}})
    return rows


COMMON_CHECKS = set("""completed uniform_step_coverage finite_records
native_sdf_apple_and_pads free_apple_no_attachment original_apple_mass fixed_base
no_solver_warnings bounded_penetration full_hold lifted hand_supports_weight
no_table_support no_other_support retained contact_step_times_valid
contact_ledger_matches_hand_force two_sdf_pads_throughout_hold
no_fruit_support_during_hold only_two_pads_support momentum_balance""".split())


def admit_records(record_map, profiles, source_hashes, *, wheel_dir=None):
    """Derive qualification from actual raw runs; paths never enter public freeze."""
    from dexlab.engine_versions import require_formal_batch_qualification

    if set(record_map) != set(profiles):
        raise ValueError("Qualification records must exactly cover requested profiles")
    if wheel_dir is None:
        raise ValueError("Official wheel directory required for new qualification")
    runtime = observe_runtime()
    audit = refresh_inventory()
    from dexlab.official_wheels import verify_official_wheel

    official_wheels = {}
    for row in audit:
        package = row["package"]
        available = [(Path(wheel_dir) / filename, digest)
                     for filename, digest in row["distribution_sha256"].items()
                     if filename.endswith(".whl") and (Path(wheel_dir) / filename).is_file()]
        if len(available) != 1:
            raise ValueError(f"Expected one official wheel for {package} in the private directory")
        path, digest = available[0]
        official_wheels[package] = verify_official_wheel(
            path, package=package, version=runtime["installed"][package],
            official_sha256=digest,
            installed_code_sha256=runtime["package_code_sha256"][package])
    evidence = {}
    required = {}
    for key, profile in profiles.items():
        backend = profile["backend"]
        evidence[key] = rescore_record(Path(record_map[key]), backend,
                                      expected_profile=profile, expected_source=source_hashes,
                                      runtime=runtime)
        required[key] = COMMON_CHECKS | (
            {"official_wheel", "no_apple_actuation"} if backend == "mujoco" else {"fp64"})
    receipt = {"schema_version": 1, "task": "apple-stem", "profiles": profiles,
               "source_sha256": source_hashes, "runtime": runtime, "audit": audit,
               "evidence_sha256": {key: row["raw_record_sha256"] for key, row in evidence.items()}}
    frozen = require_formal_batch_qualification(
        "apple-stem", profiles, receipt=receipt, source_hashes=source_hashes,
        runtime=runtime, evidence=evidence, required_checks=required,
    )
    frozen["official_wheels"] = official_wheels
    return frozen


def publication_status(frozen):
    """Recheck releases without rewriting the completed batch's dated evidence."""
    from dexlab.engine_versions import validate_versions

    audit = refresh_inventory()
    current = {row["package"]: row["version"] for row in audit}
    original = frozen["runtime"]["installed"]
    changes = {name: {"frozen": version, "latest": current.get(name)}
               for name, version in original.items() if current.get(name) != version}
    if set(current) != set(original):
        raise ValueError("Publication inventory does not cover the frozen runtime")
    if not changes:
        validate_versions(audit, original, frozen["runtime"]["native"])
    return {"classification": "historical_new_qualification_required" if changes else "latest_stable",
            "release_changes": changes, "audit": audit,
            "scope": "Release freshness only; does not replace task or artifact verification"}


def main():
    """Requalify the completed paired gate without dispatching held-out scenes."""
    import argparse
    from dexlab.benchmark import source_hashes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mujoco", type=Path, required=True)
    parser.add_argument("--superdex", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Keep previous qualification evidence; use a new output")
    profiles, records = {}, {}
    for backend in ("mujoco", "superdex"):
        directory = getattr(args, backend)
        observation = json.loads((directory / "qualification-observation.json").read_text())
        if observation["backend"] != backend:
            raise ValueError("Qualification directory backend mismatch")
        profile = observation["profile"]
        key = profile_key(profile)
        profiles[key], records[key] = profile, str(directory)
    source = source_hashes()
    frozen = admit_records(records, profiles, source, wheel_dir=args.wheel_dir)
    publication = publication_status(frozen)
    if source_hashes() != source or observe_runtime() != frozen["runtime"]:
        raise ValueError("Source or runtime changed during final qualification")
    with args.output.open("x") as stream:
        json.dump({"admission": frozen, "publication": publication}, stream, indent=2, allow_nan=False)
        stream.write("\n")
    if publication["classification"] != "latest_stable":
        raise ValueError("New upstream release requires qualification; dated evidence retained")
    print("Paired raw acceptance, official wheel identity and latest-stable publication check passed")


if __name__ == "__main__":
    main()
