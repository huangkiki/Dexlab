"""Explicit public projections of historical metadata; never edit raw records."""

from copy import deepcopy
import hashlib
import json
import re

_PRIVATE_PATH = re.compile(r"/(?:home|media|mnt|tmp)/|/dev/shm/")


def public_metadata(original):
    """Remove deployment-only fields, preserving every physical measurement.

    Return a copy and JSON pointers of changes. Unknown private paths fail closed
    rather than silently changing an unreviewed scientific field.
    """
    result = deepcopy(original)
    changed = []

    def visit(value, pointer=""):
        if isinstance(value, dict):
            for key in list(value):
                child = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                if re.fullmatch(r"(?:/records/\d+/(?:metadata|job))?/command", child) and isinstance(value[key], list):
                    # Commands describe private invocation, not the measured state.
                    if any(isinstance(v, str) and _PRIVATE_PATH.search(v) for v in value[key]):
                        del value[key]
                        changed.append(child)
                        continue
                if re.fullmatch(r"(?:/records/\d+/metadata)?/engine/package_identity/installation_origin", child) and isinstance(value[key], dict):
                    url = value[key].get("url", "")
                    if isinstance(url, str) and _PRIVATE_PATH.search(url):
                        del value[key]
                        changed.append(child)
                        continue
                if re.fullmatch(r"/records/\d+/job/suite", child) and isinstance(value[key], str) and _PRIVATE_PATH.search(value[key]):
                    # The retained run metadata pins suite_sha256; this is only its local filename.
                    del value[key]
                    changed.append(child)
                    continue
                visit(value[key], child)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, pointer + "/" + str(index))
        elif isinstance(value, str) and _PRIVATE_PATH.search(value):
            raise ValueError(f"Unreviewed private path at JSON pointer {pointer}")

    visit(result)
    return result, changed


def project_json(raw):
    """Preserve original bytes when no redaction is needed; return lineage."""
    value, changed = public_metadata(json.loads(raw))
    public = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode() if changed else raw
    return public, {
        "original_sha256": hashlib.sha256(raw).hexdigest(),
        "public_sha256": hashlib.sha256(public).hexdigest(),
        "removed_json_pointers": changed,
        "transformation": "deployment-metadata-redaction-v1" if changed else "byte-identical",
    }



def project_model(raw, temporary_directory):
    """Replace only the serialized path table, preserving its size and offsets.

    This edits a recorded model artifact, never an engine binary. Every byte
    outside the unique native path table must remain identical.
    """
    from pathlib import Path
    import tempfile
    import mujoco
    import numpy as np

    if mujoco.__version__ != "3.11.0":
        raise ValueError("Historical MJB projection requires official MuJoCo 3.11.0")
    with tempfile.TemporaryDirectory(dir=temporary_directory) as tmp:
        path = Path(tmp) / "original.mjb"
        path.write_bytes(raw)
        model = mujoco.MjModel.from_binary_path(str(path))
        paths = model.paths
        if not paths or raw.count(paths) != 1:
            raise ValueError("Cannot uniquely locate native model path table")
        components = paths.split(b"\0")
        count = 0
        for index, value in enumerate(components):
            if re.search(rb"/(?:home|media|mnt|tmp)/|/dev/shm/", value):
                basename = value.rsplit(b"/", 1)[-1]
                components[index] = b"_" * (len(value) - len(basename)) + basename
                count += 1
        projected = b"\0".join(components)
        offset = raw.index(paths)
        public = raw[:offset] + projected + raw[offset + len(paths):]
        if len(public) != len(raw) or re.search(rb"/(?:home|media|mnt)/|/dev/shm/", public):
            raise ValueError("Model privacy projection is incomplete")
        target = Path(tmp) / "public.mjb"
        target.write_bytes(public)
        restored = mujoco.MjModel.from_binary_path(str(target))
        checked = 0
        for name in dir(model):
            if name.startswith("_") or name == "paths":
                continue
            before, after = getattr(model, name), getattr(restored, name)
            if isinstance(before, np.ndarray):
                if before.dtype != after.dtype or before.shape != after.shape or before.tobytes() != after.tobytes():
                    raise ValueError(f"Model array changed: {name}")
                checked += 1
            elif isinstance(before, (int, float, bytes, str)) and before != after:
                raise ValueError(f"Model scalar changed: {name}")
        if restored.paths != projected:
            raise ValueError("Native path-table readback differs")
    return public, {"original_sha256": hashlib.sha256(raw).hexdigest(),
                    "public_sha256": hashlib.sha256(public).hexdigest(),
                    "transformation": "mujoco-path-table-redaction-v1",
                    "redacted_paths": count, "path_table_offset_bytes": offset,
                    "path_table_length_bytes": len(paths),
                    "native_arrays_byte_identical": checked,
                    "outside_path_table_byte_identical": True}

def bundle_readme(data):
    """Exclude external archive identity: a bundle cannot contain its own hash."""
    return re.sub(rb"<!-- repository-only:start -->\n.*?<!-- repository-only:end -->\n", b"", data,
                  flags=re.DOTALL).replace(b"(PUBLIC-ARCHIVE", b"(README")


def export_bundle(repository, locations, destination):
    """Export the two missing historical cohorts, with pinned offline scorers."""
    from pathlib import Path
    import subprocess
    from dexlab.evidence_report import digest, inside, read_json

    repository, destination = Path(repository), Path(destination)
    if destination.exists():
        raise ValueError("Use a fresh bundle directory")
    selected = {"cloth-heldout", "robot-cloth"}
    history = read_json(repository / "docs/evidence/historical-v1.json")
    selection = read_json(repository / "docs/evidence/cohorts.json")
    selection["cohorts"] = [c for c in selection["cohorts"] if c["id"] in selected]
    if {c["id"] for c in selection["cohorts"]} != selected:
        raise ValueError("Missing required cohort")
    roots = [Path(p).resolve() for k in selected for p in
             (locations[k].values() if isinstance(locations[k], dict) else [locations[k]])]
    if any(destination.resolve().is_relative_to(p) for p in roots):
        raise ValueError("Bundle cannot be written inside raw inputs")
    destination.mkdir(parents=True)
    manifest = {"schema": "public-historical-bundle-v1", "files": {}, "lineage": {},
                "environment": history["environment"],
                "historical_report_sha256": digest(repository / "docs/evidence/historical-v1.json"),
                "scope": "106 historical records; deployment metadata redacted; trajectories unchanged"}

    def write(name, data):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("Invalid public bundle member path")
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        manifest["files"][name] = hashlib.sha256(data).hexdigest()

    def write_json(name, value):
        write(name, (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode())

    public_rows = []
    for row in history["records"]:
        if row["cohort"] not in selected:
            continue
        row = deepcopy(row)
        location = locations[row["cohort"]]
        directory = Path(location[row["id"]]) if isinstance(location, dict) else Path(location) / row["id"]
        for name, expected in row["input_sha256"].items():
            raw = inside(directory, name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError(f"Original input hash mismatch: {row['cohort']}/{row['id']}/{name}")
            if name.endswith(".json"):
                data, lineage = project_json(raw)
            elif name.endswith(".mjb") and re.search(rb"/(?:home|media|mnt)/|/dev/shm/", raw):
                data, lineage = project_model(raw, destination)
            else:
                data = raw
                if re.search(rb"/(?:home|media|mnt)/|/dev/shm/", data):
                    raise ValueError(f"Private path in non-JSON payload: {name}")
                lineage = {"original_sha256": expected, "public_sha256": expected,
                           "removed_json_pointers": [], "transformation": "byte-identical"}
            target = f"raw/{row['cohort']}/{row['id']}/{name}"
            write(target, data)
            manifest["lineage"][target] = lineage
            row["input_sha256"][name] = lineage["public_sha256"]
            if digest(inside(directory, name)) != expected:
                raise ValueError("Original changed during export")
        public_rows.append(row)
    for spec in selection["cohorts"]:
        original = inside(repository, spec["report"])
        if digest(original) != spec["report_sha256"]:
            raise ValueError("Frozen cohort report changed")
        report, removed = public_metadata(read_json(original))
        original_report_hash = digest(original)
        rows = {r["id"]: r for r in public_rows if r["cohort"] == spec["id"]}
        if len(rows) != spec["count"]:
            raise ValueError("Export would omit historical records")
        if spec["kind"] == "cloth":
            for record in report["records"]:
                record["run_sha256"] = rows[record["run"]]["input_sha256"]["run.json"]
        if spec["kind"] == "robot_cloth":
            report["input_sha256"] = rows["integration-grasp-v1"]["input_sha256"]
        write_json("scorer/" + spec["report"], report)
        manifest["lineage"]["scorer/" + spec["report"]] = {
            "original_sha256": original_report_hash,
            "public_sha256": manifest["files"]["scorer/" + spec["report"]],
            "removed_json_pointers": removed,
            "transformation": "deployment-redaction-and-public-input-hash-rebinding-v1",
        }
        spec["report_sha256"] = manifest["files"]["scorer/" + spec["report"]]
        spec["raw_source"] = {"url": None, "availability": "included in this public bundle; explicit metadata projection"}
    for name, expected in history["scorer_sha256"].items():
        data = subprocess.check_output(["git", "-C", str(repository), "show", "v0.16.0:" + name])
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Frozen scorer does not match the published report")
        write("scorer/" + name, data)
    definitions = (repository / "docs/evidence/metrics.json").read_bytes()
    if hashlib.sha256(definitions).hexdigest() != history["metric_definitions_sha256"]:
        raise ValueError("Frozen metric definitions changed")
    write("scorer/docs/evidence/metrics.json", definitions)
    write_json("scorer/docs/evidence/public-cohorts.json", selection)
    write_json("expected-records.json", public_rows)
    for name in ("LICENSE", "NOTICE", "docs/asset-licenses/openarm-arm-LICENSE",
                 "docs/asset-licenses/openarm-arm-NOTICE", "docs/asset-licenses/wuji-hand-LICENSE",
                 "docs/asset-licenses/wuji-hand-NOTICE"):
        write(name, (repository / name).read_bytes())
    write("reproduce.py", (repository / "scripts/reproduce_historical_bundle.py").read_bytes())
    write("requirements.txt", ("\n".join(f"{name}=={version}" for name, version in history["environment"].items()) + "\n").encode())
    for language, filename in (("", "README.md"), (".zh-CN", "README.zh-CN.md")):
        write(filename, bundle_readme((repository / f"docs/evidence/PUBLIC-ARCHIVE{language}.md").read_bytes()))
    write_json("manifest.json", manifest)
    return manifest
