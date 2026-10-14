"""Serial, budgeted retrieval of the pinned official LIBERO data files.

Run inside the existing archive resource envelope and shared research guard.
Incomplete attempt receipts block further transfers until explicit recovery.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

from dexlab.libero_dataset import frozen_inputs
from dexlab.libero_inputs import DATASET_REVISION
from dexlab.libero_workflow import file_hash
from dexlab.migration_budget import json_bytes, publish

LIMITS = {"max_attempts": 390, "max_attempts_per_file": 3, "max_body_bytes": 125 * 1024**3,
          "max_wall_s": 12 * 3600, "attempt_wall_s": 600,
          "body_bytes_per_s": 8 * 1024**2, "chunk_bytes": 1024**2}
EXTENDED_WALL_LIMITS = {"max_wall_s": 24 * 3600, "attempt_wall_s": 1800}
BASE_URL = f"https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/resolve/{DATASET_REVISION}/"


def create_plan(root: Path, inventory_hash: str) -> None:
    root.mkdir(parents=True, exist_ok=False)
    (root / "attempts").mkdir()
    publish(root / "plan.json", json_bytes({"schema_version": 1, "dataset_revision": DATASET_REVISION,
                                          "inventory_sha256": inventory_hash, "limits": LIMITS}))


@contextmanager
def _lock(root: Path):
    with (root / "lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def _owner() -> dict:
    return {"pid": os.getpid(), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "start_ticks": Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()[19]}


def _alive(owner: dict) -> bool:
    if owner["boot_id"] != Path("/proc/sys/kernel/random/boot_id").read_text().strip():
        return False
    try:
        fields = Path(f"/proc/{owner['pid']}/stat").read_text().rsplit(")", 1)[1].split()
    except FileNotFoundError:
        return False
    return fields[19] == owner["start_ticks"] and fields[0] not in {"Z", "X"}


def _history(root: Path, inventory_hash: str) -> tuple[str, list[tuple[dict, dict | None]]]:
    raw = (root / "plan.json").read_bytes()
    plan = json.loads(raw)
    if plan != {"schema_version": 1, "dataset_revision": DATASET_REVISION,
                "inventory_sha256": inventory_hash, "limits": LIMITS}:
        raise ValueError("Transfer plan differs from frozen inventory or declared limits")
    digest = hashlib.sha256(raw).hexdigest()
    history = []
    for index, path in enumerate(sorted((root / "attempts").glob("*.started.json")), 1):
        if path.name != f"{index:04d}.started.json":
            raise ValueError("Transfer attempt sequence is incomplete")
        started = json.loads(path.read_bytes())
        if started["plan_sha256"] != digest:
            raise ValueError("An attempt belongs to a different transfer plan")
        terminal = path.with_name(f"{index:04d}.finished.json")
        finished = json.loads(terminal.read_bytes()) if terminal.exists() else None
        if finished is not None and finished["started_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("Transfer receipt does not bind its reservation")
        if (type(started["reserved_body_bytes"]) is not int or started["reserved_body_bytes"] < 0
                or (finished is not None and (
                    type(finished["body_bytes_charged"]) is not int
                    or not 0 <= finished["body_bytes_charged"] <= started["reserved_body_bytes"]
                    or not isinstance(finished["wall_s_charged"], (int, float))
                    or not math.isfinite(finished["wall_s_charged"]) or finished["wall_s_charged"] < 0))):
            raise ValueError("Invalid transfer accounting; budget cannot be recreated")
        history.append((started, finished))
    if any(not p.with_name(p.name.replace(".finished.", ".started.")).exists()
           for p in (root / "attempts").glob("*.finished.json")):
        raise ValueError("Transfer reservation is missing; budget cannot be recreated")
    return digest, history


def _receipt_prefix_hash(root: Path, count: int) -> str:
    identities = [[hashlib.sha256((root / "attempts" / f"{index:04d}.{phase}.json").read_bytes()).hexdigest()
                   for phase in ("started", "finished")] for index in range(1, count + 1)]
    return hashlib.sha256(json_bytes(identities)).hexdigest()


def _wall_limits(root: Path, plan_hash: str, history: list) -> tuple[dict, str | None]:
    """Validate one explicit extension without replacing the original ledger."""
    path = root / "wall-amendment.json"
    limits, amendment_hash, boundary = LIMITS, None, len(history)
    if path.exists():
        raw = path.read_bytes()
        amendment = json.loads(raw)
        boundary = amendment["after_attempt"]
        if (amendment.get("schema_version") != 1
                or amendment.get("original_plan_sha256") != plan_hash
                or type(boundary) is not int or not 1 <= boundary <= len(history)
                or any(finished is None for _, finished in history[:boundary])
                or amendment.get("prior_receipts_sha256") != _receipt_prefix_hash(root, boundary)
                or amendment.get("wall_limits") != EXTENDED_WALL_LIMITS
                or not isinstance(amendment.get("reason"), str) or not amendment["reason"].strip()
                or amendment.get("evidence_sha256") != file_hash(root / "wall-amendment-evidence.json")):
            raise ValueError("Invalid wall-budget amendment; preserve original accounting")
        limits = {**LIMITS, **EXTENDED_WALL_LIMITS}
        amendment_hash = hashlib.sha256(raw).hexdigest()
    for index, (started, _) in enumerate(history):
        expected_hash = amendment_hash if index >= boundary else None
        expected_wall = limits["attempt_wall_s"] if index >= boundary else LIMITS["attempt_wall_s"]
        if (started.get("wall_amendment_sha256") != expected_hash
                or started.get("reserved_wall_s", LIMITS["attempt_wall_s"]) != expected_wall):
            raise ValueError("Attempt differs from its frozen wall allowance")
    return limits, amendment_hash


def amend_wall_budget(root: Path, inventory_hash: str, evidence: Path, reason: str) -> dict:
    """Explicitly extend wall allowance once, after all recorded owners finish."""
    with _lock(root):
        plan_hash, history = _history(root, inventory_hash)
        _, existing = _wall_limits(root, plan_hash, history)
        if (existing is not None or not history or any(finished is None for _, finished in history)
                or any(_alive(started["owner"]) for started, _ in history)):
            raise ValueError("Wall amendment requires terminal history and no prior amendment")
        raw = evidence.read_bytes()
        report = json.loads(raw)
        if (not isinstance(reason, str) or not reason.strip() or not isinstance(report, dict)
                or report.get("transfer_plan_sha256") != plan_hash
                or report.get("inventory_sha256") != inventory_hash
                or type(report.get("completed_successful_transfers")) is not int
                or report["completed_successful_transfers"] < 1):
            raise ValueError("Wall amendment requires measured evidence for this frozen input plan")
        evidence_hash = hashlib.sha256(raw).hexdigest()
        amendment = {"schema_version": 1, "original_plan_sha256": plan_hash,
                     "after_attempt": len(history), "prior_receipts_sha256": _receipt_prefix_hash(root, len(history)),
                     "evidence_sha256": evidence_hash, "wall_limits": EXTENDED_WALL_LIMITS, "reason": reason.strip()}
        saved = root / "wall-amendment-evidence.json"
        if saved.exists():
            if file_hash(saved) != evidence_hash:
                raise ValueError("Preserve different existing amendment evidence")
        else:
            publish(saved, raw)
        publish(root / "wall-amendment.json", json_bytes(amendment))
        return amendment


def recover(root: Path, inventory_hash: str) -> int:
    """Only a dead recorded owner can be charged its full unfinished allowance."""
    with _lock(root):
        plan_hash, history = _history(root, inventory_hash)
        _wall_limits(root, plan_hash, history)
        count = 0
        for index, (started, finished) in enumerate(history, 1):
            if finished is not None:
                continue
            if _alive(started["owner"]):
                raise ValueError("Transfer owner is still live; do not restart it")
            raw = (root / "attempts" / f"{index:04d}.started.json").read_bytes()
            publish(root / "attempts" / f"{index:04d}.finished.json", json_bytes({
                "started_sha256": hashlib.sha256(raw).hexdigest(), "status": "interrupted",
                "body_bytes_charged": started["reserved_body_bytes"],
                "wall_s_charged": started.get("reserved_wall_s", LIMITS["attempt_wall_s"]), "actual_received_bytes": None,
                "scope": "Unknown actual usage charged at the full reserved allowance."}))
            count += 1
        return count


def _headers(response, expected: dict, offset: int, saved: dict | None) -> dict:
    """Validate response identity/range before opening the partial for append."""
    if response.headers.get("Content-Encoding", "identity") != "identity":
        raise ValueError("Encoded HTTP body cannot be appended as pinned file bytes")
    remaining = expected["bytes"] - offset
    if response.headers.get("Content-Length") != str(remaining):
        raise ValueError("HTTP body length differs from remaining pinned bytes")
    etag = response.headers.get("ETag")
    if offset:
        if (response.status != 206
                or response.headers.get("Content-Range") != f"bytes {offset}-{expected['bytes']-1}/{expected['bytes']}"
                or saved is None or saved["etag"] != etag or not etag or etag.startswith("W/")):
            raise ValueError("Resume requires exact Content-Range and unchanged strong ETag")
    elif response.status != 200:
        raise ValueError("Fresh transfer requires a complete HTTP 200 response")
    return {"dataset": expected, "etag": etag}


def _check_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise TimeoutError("Transfer reached its frozen wall-time limit")


def _hash_until(path: Path, deadline: float) -> str:
    """Include complete-file verification in the retrieval deadline."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            _check_deadline(deadline)
            chunk = stream.read(LIMITS["chunk_bytes"])
            _check_deadline(deadline)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def _receive(expected: dict, partial: Path, metadata: Path, *, deadline: float,
             progress: dict) -> None:
    offset = partial.stat().st_size if partial.exists() else 0
    saved = json.loads(metadata.read_bytes()) if metadata.exists() else None
    if saved is not None and saved["dataset"] != expected:
        raise ValueError("Partial transfer metadata belongs to different pinned bytes")
    headers = {"Accept-Encoding": "identity"}
    if offset:
        if saved is None or not saved["etag"] or saved["etag"].startswith("W/"):
            raise ValueError("Partial transfer lacks a strong ETag; preserve it for recovery")
        headers.update(Range=f"bytes={offset}-", **{"If-Range": saved["etag"]})
    request = urllib.request.Request(BASE_URL + expected["path"], headers=headers)
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=30) as response:
        identity = _headers(response, expected, offset, saved)
        if saved is None:
            publish(metadata, json_bytes(identity))
        elif identity != saved:
            raise ValueError("HTTP identity changed; preserve the existing partial")
        with partial.open("ab" if partial.exists() else "xb") as target:
            remaining = expected["bytes"] - offset
            while remaining:
                _check_deadline(deadline)
                chunk = response.read(min(LIMITS["chunk_bytes"], remaining))
                if not chunk:
                    raise ValueError("HTTP body ended before the pinned byte count")
                progress["body_bytes_charged"] += len(chunk)
                target.write(chunk)
                _check_deadline(deadline)
                remaining -= len(chunk)
                delay = progress["body_bytes_charged"] / LIMITS["body_bytes_per_s"] - (time.monotonic() - started)
                if delay > 0:
                    time.sleep(min(delay, max(0, deadline - time.monotonic())))
            # Content-Length was checked before reading; no unbounded trailing read.
            target.flush()
            os.fsync(target.fileno())


def download_one(root: Path, inventory_hash: str, expected: dict, destination: Path) -> dict:
    """One attempt; never retry invisibly or replace an existing final file."""
    with _lock(root):
        plan_hash, history = _history(root, inventory_hash)
        limits, amendment_hash = _wall_limits(root, plan_hash, history)
        if any(finished is None for _, finished in history):
            raise ValueError("Unfinished transfer exists; inspect its owner and recover first")
        if destination.exists():
            if destination.stat().st_size != expected["bytes"] or file_hash(destination) != expected["sha256"]:
                raise ValueError("Existing final file differs; preserve it instead of overwriting")
            return {"status": "existing-pinned-file", "received_bytes": 0}
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_name(destination.name + ".partial")
        metadata = destination.with_name(destination.name + ".http.json")
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > expected["bytes"]:
            raise ValueError("Partial exceeds pinned file size; preserve it for investigation")
        reserved = expected["bytes"] - offset
        count = sum(s["dataset"] == expected["path"] for s, _ in history)
        used_bytes = sum(f["body_bytes_charged"] for _, f in history)
        used_wall = sum(f["wall_s_charged"] for _, f in history)
        if (len(history) >= limits["max_attempts"] or count >= limits["max_attempts_per_file"]
                or used_bytes + reserved > limits["max_body_bytes"]
                or used_wall + limits["attempt_wall_s"] > limits["max_wall_s"]):
            raise ValueError("Cumulative transfer budget exhausted; preserve remaining scope")
        number = len(history) + 1
        start = time.monotonic()
        started = {"plan_sha256": plan_hash, "dataset": expected["path"], "owner": _owner(),
                   "offset": offset, "reserved_body_bytes": reserved, "started_unix_s": time.time(),
                   "reserved_wall_s": limits["attempt_wall_s"], "wall_amendment_sha256": amendment_hash}
        raw = json_bytes(started)
        publish(root / "attempts" / f"{number:04d}.started.json", raw)
        progress = {"body_bytes_charged": 0}
        status = "failed"
        deadline = start + limits["attempt_wall_s"]
        try:
            if reserved:
                _receive(expected, partial, metadata, deadline=deadline, progress=progress)
            _check_deadline(deadline)
            if partial.stat().st_size != expected["bytes"] or _hash_until(partial, deadline) != expected["sha256"]:
                raise ValueError("Complete transfer differs from pinned file digest; preserve partial")
            _check_deadline(deadline)
            # Exclusive hard-link publication never overwrites another final file.
            os.link(partial, destination)
            partial.unlink()
            status = "downloaded-hash-verified"
            return {"status": status, "received_bytes": progress["body_bytes_charged"]}
        finally:
            publish(root / "attempts" / f"{number:04d}.finished.json", json_bytes({
                "started_sha256": hashlib.sha256(raw).hexdigest(), "status": status,
                "received_body_bytes": progress["body_bytes_charged"],
                "body_bytes_charged": progress["body_bytes_charged"] if status == "downloaded-hash-verified" else reserved,
                "wall_s_charged": time.monotonic() - start}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "get", "recover", "amend-wall"))
    parser.add_argument("libero_root", type=Path)
    parser.add_argument("frozen", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--task-id")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--reason")
    args = parser.parse_args()
    inputs, digest = frozen_inputs(args.libero_root, args.frozen)
    if args.command == "init":
        create_plan(args.ledger, digest)
        print(json.dumps({"status": "plan-frozen", "limits": LIMITS}))
    elif args.command == "recover":
        print(json.dumps({"recovered": recover(args.ledger, digest)}))
    elif args.command == "amend-wall":
        if args.evidence is None or not args.reason:
            parser.error("amend-wall requires --evidence and --reason")
        print(json.dumps(amend_wall_budget(args.ledger, digest, args.evidence, args.reason)))
    else:
        tasks = {task["task_id"]: task for task in inputs["tasks"]}
        if args.task_id not in tasks or args.data_root is None:
            parser.error("get requires one frozen task ID and --data-root")
        expected = tasks[args.task_id]["dataset"]
        try:
            print(json.dumps(download_one(args.ledger, digest, expected, args.data_root / expected["path"])))
        except urllib.error.HTTPError as error:
            parser.exit(1, f"HTTP {error.code}; transfer receipt and partial retained\n")
        except urllib.error.URLError:
            parser.exit(1, "Network request failed; transfer receipt and partial retained\n")


if __name__ == "__main__":
    main()
