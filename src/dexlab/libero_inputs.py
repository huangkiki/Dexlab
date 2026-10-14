"""Freeze official LIBERO input identities without importing a simulator.

BDDL token normalization follows bddl.parsing.scan_tokens (BDDL 1.0.1).
Only declarations are inspected; expressions, assets and initial-state pickles
are never executed. This inventory is not dataset or runtime qualification.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

from dexlab.libero_workflow import UPSTREAM, file_hash
from dexlab.migration_budget import json_bytes, publish

DATASET_REVISION = "f13aa24a3da8c43c7225569f28c562979fa0e35a"
SUITE_COUNTS = {"libero_spatial": 10, "libero_object": 10, "libero_goal": 10,
                "libero_10": 10, "libero_90": 90}
TASK_MAP = "libero/libero/benchmark/libero_suite_task_map.py"
BENCHMARK = "libero/libero/benchmark/__init__.py"
DATASET_INDEX = Path(__file__).resolve().parents[2] / "demos/libero-contact/dataset-index.json"
DATASET_INDEX_SHA256 = "6a75976e7b27db7a2b4ff08fb66cdd7ce16b076969d175f996a3a2617d709a71"


def benchmark_language(name: str) -> str:
    """Mirror the pinned benchmark's grab_language_from_filename contract.

    Task.language and BDDL :language are separate upstream declarations. This
    API mapping must never replace the parsed BDDL language or goal semantics.
    """
    filename = name + ".bddl"
    if filename[0].isupper():
        offset = 8 if "SCENE10" in filename else 7
        filename = filename[filename.find("SCENE") + offset:]
    language = " ".join(filename.split("_"))
    return language[:language.find(".bddl")]


def task_map(raw: bytes) -> dict[str, list[str]]:
    """Read the named literal, never execute upstream Python or guess an assignment."""
    values = []
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == "libero_task_map" for t in targets):
            values.append(ast.literal_eval(node.value))
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ValueError("Expected one literal libero_task_map assignment")
    suites = values[0]
    if set(suites) != set(SUITE_COUNTS):
        raise ValueError("Expected exactly the five official suites; LIBERO-100 is not extra")
    for suite, expected in SUITE_COUNTS.items():
        names = suites[suite]
        if (not isinstance(names, list) or len(names) != expected
                or any(not isinstance(n, str) or not re.fullmatch(r"[A-Za-z0-9_]+", n)
                       for n in names) or len(set(names)) != expected):
            raise ValueError("Invalid or duplicate official tasks in " + suite)
    return suites


def _expression(raw: bytes) -> list[Any]:
    text = re.sub(r";.*$", "", raw.decode("utf-8"), flags=re.MULTILINE).lower()
    stack: list[list[Any]] = []
    current: list[Any] = []
    for token in re.findall(r"[()]|[^\s()]+", text):
        if token == "(":
            stack.append(current)
            current = []
        elif token == ")":
            if not stack:
                raise ValueError("BDDL has an unmatched closing parenthesis")
            group = current
            current = stack.pop()
            current.append(group)
        else:
            current.append(token)
    if stack or len(current) != 1 or not isinstance(current[0], list):
        raise ValueError("BDDL must contain one balanced expression")
    return current[0]


def _typed_names(tokens: list[Any]) -> dict[str, str]:
    names: dict[str, str] = {}
    pending: list[str] = []
    position = 0
    while position < len(tokens):
        name = tokens[position]
        if not isinstance(name, str):
            raise ValueError("Nested object declaration")
        if name != "-":
            pending.append(name)
            position += 1
            continue
        if not pending or position + 1 >= len(tokens):
            raise ValueError("Missing object name or type")
        kind = tokens[position + 1]
        if not isinstance(kind, str) or kind == "-":
            raise ValueError("Invalid object type")
        for item in pending:
            if item in names:
                raise ValueError("Duplicate object declaration: " + item)
            names[item] = kind
        pending = []
        position += 2
    if pending:
        raise ValueError("Untyped object declaration")
    return names


def _goal_references(expression: list[Any]) -> set[str]:
    if not expression or not isinstance(expression[0], str):
        raise ValueError("Invalid native goal expression")
    operator, *arguments = expression
    if operator in {"and", "or", "not"}:
        if (not arguments or (operator == "not" and len(arguments) != 1)
                or not all(isinstance(a, list) for a in arguments)):
            raise ValueError("Invalid native logical goal")
        return set().union(*(_goal_references(a) for a in arguments))
    if not arguments or not all(isinstance(a, str) for a in arguments):
        raise ValueError("Invalid native goal predicate")
    return set(arguments)


def bddl_identity(raw: bytes) -> dict[str, Any]:
    """Retain goal trees and region targets rather than inventing a target body."""
    root = _expression(raw)
    if not root or root[0] != "define":
        raise ValueError("BDDL root must be define")
    sections = {}
    for group in root[1:]:
        if not isinstance(group, list) or not group or not isinstance(group[0], str):
            raise ValueError("Invalid BDDL section")
        if group[0] in sections:
            raise ValueError("Duplicate BDDL section: " + group[0])
        sections[group[0]] = group[1:]
    required = {"problem", ":domain", ":language", ":objects", ":fixtures",
                ":regions", ":obj_of_interest", ":goal", ":init"}
    if not required <= sections.keys():
        raise ValueError("Missing BDDL declarations: " + str(sorted(required - sections.keys())))
    if (len(sections["problem"]) != 1 or sections[":domain"] != ["robosuite"]
            or not isinstance(sections["problem"][0], str)
            or not sections[":language"]
            or not all(isinstance(t, str) for t in sections[":language"])):
        raise ValueError("Invalid BDDL problem/domain/language")
    objects = _typed_names(sections[":objects"])
    fixtures = _typed_names(sections[":fixtures"])
    if objects.keys() & fixtures.keys():
        raise ValueError("Object and fixture identities overlap")
    bodies = objects.keys() | fixtures.keys()
    regions = {}
    for region in sections[":regions"]:
        if not isinstance(region, list) or not region or not isinstance(region[0], str):
            raise ValueError("Invalid BDDL region")
        targets = [a for a in region[1:] if isinstance(a, list) and a[:1] == [":target"]]
        if (len(targets) != 1 or len(targets[0]) != 2
                or not isinstance(targets[0][1], str) or not targets[0][1]):
            raise ValueError("Region needs one target name")
        target = targets[0][1]
        name = target + "_" + region[0]
        if name in regions or name in bodies:
            raise ValueError("Duplicate region identity: " + name)
        # Pinned Goal files include unused bowl_drainer regions without a body.
        # Preserve this source fact; do not invent that body or silently drop it.
        regions[name] = {"target": target, "target_declared": target in bodies,
                         "declaration": region}
    unresolved = sorted(n for n, r in regions.items() if not r["target_declared"])
    known = bodies | (regions.keys() - set(unresolved))
    interests = sections[":obj_of_interest"]
    if (not interests or any(not isinstance(n, str) or n not in known for n in interests)
            or len(set(interests)) != len(interests)):
        raise ValueError("Objects of interest must resolve to distinct declared entities")
    goals = sections[":goal"]
    if len(goals) != 1 or not isinstance(goals[0], list) or not goals[0]:
        raise ValueError("Expected one nonempty native goal expression")
    if not _goal_references(goals[0]) <= known:
        raise ValueError("Native goal references an undeclared entity")
    return {"problem": sections["problem"][0], "domain": "robosuite",
            "language": " ".join(sections[":language"]), "objects": objects,
            "fixtures": fixtures, "regions": regions, "objects_of_interest": interests,
            "unresolved_region_targets": unresolved,
            "goal": goals[0], "initial_predicates": sections[":init"]}


def dataset_index(path: Path = DATASET_INDEX) -> dict[str, dict[str, Any]]:
    """Admit only the reviewed metadata snapshot, including exact byte counts."""
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != DATASET_INDEX_SHA256:
        raise ValueError("Pinned dataset metadata changed")
    data = json.loads(raw)
    if (data.get("schema_version") != 1 or data.get("revision") != DATASET_REVISION
            or data.get("repository") != "yifengzhu-hf/LIBERO-datasets"):
        raise ValueError("Unexpected dataset identity")
    files = {}
    for row in data["files"]:
        path = PurePosixPath(row["path"])
        if (len(path.parts) != 2 or path.parts[0] not in SUITE_COUNTS
                or not path.name.endswith("_demo.hdf5")
                or type(row["bytes"]) is not int or row["bytes"] <= 0
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                or row["path"] in files):
            raise ValueError("Invalid dataset entry")
        files[row["path"]] = row
    if len(files) != sum(SUITE_COUNTS.values()):
        raise ValueError("Incomplete dataset metadata")
    return files


def _source_identity(root: Path) -> None:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    if git("rev-parse", "HEAD") != UPSTREAM:
        raise ValueError("Unexpected LIBERO source revision")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked LIBERO source is modified")


def _source_file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.resolve(strict=True).is_relative_to(root):
        raise ValueError("Input escapes LIBERO source root")
    if not path.is_file():
        raise ValueError("Expected a source file: " + relative)
    return path


def inventory(libero_root: Path) -> dict[str, Any]:
    """Regenerate all 130 identities from clean pinned source and reviewed metadata."""
    root = libero_root.resolve(strict=True)
    _source_identity(root)
    map_path = _source_file(root, TASK_MAP)
    suites = task_map(map_path.read_bytes())
    files = dataset_index()
    tasks = []
    for suite in SUITE_COUNTS:
        for position, name in enumerate(suites[suite]):
            data_path = f"{suite}/{name}_demo.hdf5"
            if data_path not in files:
                raise ValueError("Official task has no pinned dataset: " + data_path)
            bddl = f"libero/libero/bddl_files/{suite}/{name}.bddl"
            initial = f"libero/libero/init_files/{suite}/{name}.pruned_init"
            definition = _source_file(root, bddl)
            initial_file = _source_file(root, initial)
            raw = definition.read_bytes()
            tasks.append({"task_id": f"{suite}/{name}", "suite": suite, "task": name,
                          "default_task_index": position,
                          "benchmark_language": benchmark_language(name),
                          "bddl_path": bddl, "bddl_sha256": hashlib.sha256(raw).hexdigest(),
                          "init_states_path": initial, "init_states_sha256": file_hash(initial_file),
                          "definition": bddl_identity(raw), "dataset": files[data_path]})
    if {t["dataset"]["path"] for t in tasks} != files.keys():
        raise ValueError("Task and dataset coverage differ")
    _source_identity(root)
    return {"schema_version": 2, "upstream_commit": UPSTREAM,
            "task_map_sha256": file_hash(map_path), "dataset_revision": DATASET_REVISION,
            "benchmark_source_sha256": file_hash(_source_file(root, BENCHMARK)),
            "dataset_index_sha256": DATASET_INDEX_SHA256, "suite_counts": SUITE_COUNTS,
            "total_tasks": len(tasks), "dataset_total_bytes": sum(t["dataset"]["bytes"] for t in tasks),
            "scope": "Static source/input identity only; no HDF5 content or runtime qualification.",
            "tasks": tasks}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("libero_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inventory(args.libero_root)
    publish(args.output, json_bytes(result))
    print(json.dumps({"tasks": result["total_tasks"], "bytes": result["dataset_total_bytes"],
                      "scope": result["scope"]}))


if __name__ == "__main__":
    main()
