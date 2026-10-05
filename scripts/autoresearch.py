#!/usr/bin/env python3
"""Issue queue and verified PR submission for the Codex research worker.

This tool does not invent a policy or invoke a hidden model. The scheduled Codex
worker reads the selected issue, implements it, and uses these commands to keep
work isolated and run checks before submission.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
import uuid
from pathlib import Path

REPO = "huangkiki/Dexlab"
ROOT = Path(__file__).resolve().parents[1]
APPROVAL = "auto:approved"
PRIORITIES = ("priority:P0", "priority:P1", "priority:P2")


def run(*args, cwd=None, capture=False, input=None):
    result = subprocess.run(
        args,
        cwd=ROOT if cwd is None else cwd,
        check=True,
        text=True,
        input=input,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def gh_json(*args):
    return json.loads(run("gh", *args, "--repo", REPO, capture=True))


def dependencies(issue):
    """Parse one explicit, human-readable dependency declaration."""
    lines = re.findall(r"^Depends on:[ \t]*(.*)$", issue.get("body", ""), re.M)
    if not lines and issue["state"] == "CLOSED":
        return ()  # Historical closed issues predate the queue template.
    if len(lines) != 1:
        raise ValueError("exactly one 'Depends on: none' or 'Depends on: #N, #M' is required")
    value = lines[0].strip()
    if value == "none":
        return ()
    if not re.fullmatch(r"#[1-9]\d*(?:,\s*#[1-9]\d*)*", value):
        raise ValueError("malformed dependency declaration")
    numbers = tuple(int(n) for n in re.findall(r"#(\d+)", value))
    if len(set(numbers)) != len(numbers):
        raise ValueError("duplicate dependency")
    return numbers


def linked_issues(pull):
    """Recognize explicit PR associations even on a nonstandard branch."""
    numbers = {item["number"] for item in pull.get("closingIssuesReferences", [])}
    branch = re.fullmatch(r"autoresearch/issue-(\d+)", pull.get("headRefName", ""))
    if branch:
        numbers.add(int(branch[1]))
    # Do not mistake an arbitrary dependency mention for ownership of that issue.
    for match in re.finditer(
        r"\b(?:Refs|Fix(?:es|ed)?|Close(?:s|d)?|Resolve(?:s|d)?)\s+(#\d+(?:,\s*#\d+)*)",
        pull.get("body", ""), re.I,
    ):
        numbers.update(int(number) for number in re.findall(r"#(\d+)", match[1]))
    return numbers


def queue_report(issues, pulls, *, integrated=(), claimed=(), paused=False):
    """Explain eligibility without claiming work or accepting labels as evidence."""
    by_number = {item["number"]: item for item in issues}
    active = set(claimed)
    for pull in pulls:
        if pull.get("state", "OPEN") == "OPEN":
            active.update(linked_issues(pull))
    integrated = set(integrated)
    eligible, excluded = [], []

    def dependency_errors(number, path=()):
        if number in path:
            return ["dependency cycle: " + " -> ".join(map(str, (*path, number)))]
        item = by_number.get(number)
        if item is None:
            return [f"unknown dependency #{number}"]
        try:
            required = dependencies(item)
        except ValueError as error:
            return [f"#{number}: {error}"]
        errors = []
        for dependency in required:
            errors.extend(dependency_errors(dependency, (*path, number)))
            target = by_number.get(dependency)
            if target is not None and (
                target["state"] != "CLOSED" or dependency not in integrated
            ):
                errors.append(f"dependency #{dependency} is not closed and verified integrated")
        return errors

    for item in issues:
        if item["state"] != "OPEN":
            continue
        number = item["number"]
        labels = {label["name"] for label in item["labels"]}
        reasons = []
        if APPROVAL not in labels:
            reasons.append(f"missing {APPROVAL}")
        for blocker in ("needs-input", "blocked"):
            if blocker in labels:
                reasons.append(blocker)
        priority = labels.intersection(PRIORITIES)
        if len(priority) != 1:
            reasons.append("exactly one priority label is required")
        if not item.get("createdAt"):
            reasons.append("creation time is missing")
        reasons.extend(dependency_errors(number))
        if number in active:
            reasons.append("existing PR or worktree; recover it before new dispatch")
        if reasons:
            excluded.append({"number": number, "reasons": list(dict.fromkeys(reasons))})
        else:
            eligible.append(item)
    eligible.sort(key=lambda item: (
        next(i for i, label in enumerate(PRIORITIES) if label in {
            entry["name"] for entry in item["labels"]
        }), item["createdAt"], item["number"],
    ))
    return {
        "paused": paused,
        "selected": eligible[0] if eligible and not paused else None,
        "eligible": eligible,
        "excluded": excluded,
    }


def select_issue(issues, pulls, **context):
    return queue_report(issues, pulls, **context)["selected"]


def queue_context():
    """Refresh the base and verify merged dependency commits against its ancestry."""
    run("git", "fetch", "origin", "main")
    issues = gh_json(
        "issue", "list", "--state", "all", "--limit", "1000", "--json",
        "number,title,body,state,labels,url,createdAt",
    )
    pulls = gh_json(
        "pr", "list", "--state", "all", "--limit", "1000", "--json",
        "number,headRefName,state,baseRefName,mergeCommit,closingIssuesReferences,body,url",
    )
    if len(issues) >= 1000 or len(pulls) >= 1000:
        raise SystemExit("Queue inventory limit reached; refusing an incomplete snapshot")
    integrated = set()
    for pull in pulls:
        commit = (pull.get("mergeCommit") or {}).get("oid", "")
        if (pull["state"] != "MERGED" or pull["baseRefName"] != "main"
                or not re.fullmatch(r"[0-9a-f]{40}", commit)):
            continue
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "origin/main"],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            integrated.update(item["number"] for item in pull["closingIssuesReferences"])
    claimed = set()
    for line in run("git", "worktree", "list", "--porcelain", capture=True).splitlines():
        match = re.fullmatch(r"branch refs/heads/autoresearch/issue-(\d+)", line)
        if match:
            claimed.add(int(match[1]))
    common = Path(run("git", "rev-parse", "--git-common-dir", capture=True))
    if not common.is_absolute():
        common = ROOT / common
    return issues, pulls, {
        "integrated": integrated,
        "claimed": claimed,
        "paused": (common / "dexlab-dispatch-paused").exists(),
    }


def next_issue(explain=False):
    issues, pulls, context = queue_context()
    report = queue_report(issues, pulls, **context)
    return report if explain else report["selected"]


def authorized_issue(number):
    """Authorization/dependencies also apply to resuming and submitting work."""
    issues, _, context = queue_context()
    item = next((item for item in issues if item["number"] == number), None)
    report = queue_report(issues, [], integrated=context["integrated"])
    if item is None or number not in {item["number"] for item in report["eligible"]}:
        reasons = next((row["reasons"] for row in report["excluded"]
                        if row["number"] == number), ["issue is missing or closed"])
        raise SystemExit(f"Issue #{number} is not eligible: {'; '.join(reasons)}")
    return item


def start(number):
    issue = authorized_issue(number)
    branch = f"autoresearch/issue-{number}"
    worktree = ROOT / ".autoresearch" / "worktrees" / f"issue-{number}"
    if not worktree.exists():
        issues, pulls, context = queue_context()
        report = queue_report(issues, pulls, **context)
        if report["paused"] or number not in {item["number"] for item in report["eligible"]}:
            raise SystemExit("New dispatch is paused or work already exists; inspect next --dry-run")
        exists = (
            subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                cwd=ROOT,
                check=False,
            ).returncode
            == 0
        )
        if exists:
            run("git", "worktree", "add", str(worktree), branch)
        else:
            run("git", "worktree", "add", "-b", branch, str(worktree), "origin/main")
    actual = run("git", "branch", "--show-current", cwd=worktree, capture=True)
    if actual != branch:
        raise SystemExit("Unexpected branch in existing worktree; leaving it unchanged")
    return {"issue": issue, "branch": branch, "worktree": str(worktree)}


def source_tree(worktree):
    """Hash the submit tree without changing the user's index or creating a commit."""
    with tempfile.TemporaryDirectory(prefix="dexlab-index-") as directory:
        environment = {**os.environ, "GIT_INDEX_FILE": str(Path(directory) / "index")}
        def git(*args):
            return subprocess.check_output(
                ["git", *args], cwd=worktree, env=environment, text=True,
            ).strip()
        git("read-tree", "HEAD")
        git("add", "-A")
        git("diff", "--cached", "--check")
        return git("write-tree")


def check_remote(worktree, destination, remote_state=None):
    """Run the same gate on a prepared SSH checkout, bound to the local source tree.

    The caller prepares the checkout/environment; this command never syncs over
    remote work or forwards GitHub credentials. Destination is private CLI input.
    """
    host, separator, directory = destination.partition(":")
    if (not separator or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@-]*", host)
            or not directory.startswith("/") or "\n" in directory):
        raise SystemExit("Expected SSH_ALIAS:/absolute/check-out; use an SSH config alias")
    expected = source_tree(worktree)
    arguments = ["python3", "scripts/autoresearch.py", "check", ".", "--expected-tree", expected]
    if remote_state is not None:
        state = Path(remote_state)
        if not state.is_absolute():
            raise SystemExit("Remote research state must use an absolute private path")
        receipt = state / "receipts" / (uuid.uuid4().hex + "-gate.json")
        arguments += ["--resource-dir", str(state / "receipts")]
        arguments = ["python3", "scripts/research_guard.py", "run",
                     "--lock", str(state / "window.lock"), "--kind", "qualification",
                     "--receipt", str(receipt), "--", *arguments]
    command = "cd " + shlex.quote(directory) + " && " + shlex.join(arguments)
    run("ssh", "-o", "BatchMode=yes", "-o", "ForwardAgent=no", "-o", "ConnectTimeout=15",
        host, command, cwd=worktree)
    if source_tree(worktree) != expected:
        raise SystemExit("Local source changed during remote verification; rerun the gate")
    return {"source_tree": expected, "checks": "full", "execution": "remote"}


def check(worktree, resource_dir=None):
    """Always verify both physical episodes; test logs stay inside the worktree."""
    python = os.environ.get("SUPERDEX_PYTHON") or str(worktree / ".venv/bin/python")
    wheel_dir = os.environ.get("DEXLAB_QUALIFICATION_WHEELS")
    if os.environ.get("DEXLAB_MUJOCO_PROFILE", "").startswith("qualification-") and not wheel_dir:
        raise ValueError("Candidate submission requires DEXLAB_QUALIFICATION_WHEELS")
    run(
        python,
        "-c",
        "from pathlib import Path; import dexlab; "
        "assert Path(dexlab.__file__).resolve().is_relative_to(Path.cwd().resolve()), "
        "'Editable install points outside this worktree; rerun setup here'",
        cwd=worktree,
    )
    run("git", "diff", "--check", cwd=worktree)
    run(
        python,
        "-m",
        "compileall",
        "-q",
        "src/dexlab",
        "demos/apple-stem-grasp/src",
        cwd=worktree,
    )
    run(
        python,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        cwd=worktree,
    )
    run_id = uuid.uuid4().hex
    resource_dir = None if resource_dir is None else Path(resource_dir)
    if resource_dir is not None:
        resource_dir.mkdir(parents=True, exist_ok=True)
    def measured(backend, phase, *command):
        if resource_dir is None:
            return run(*command, cwd=worktree)
        receipt = resource_dir / f"{run_id}-{backend}-{phase}.json"
        layout = ('{"whole_command_wall_s":%e,"user_cpu_s":%U,"system_cpu_s":%S,'
                  '"maximum_child_rss_kib":%M,"returncode":%x}')
        return run("env", "LC_ALL=C", "/usr/bin/time", "-q", "-f", layout,
                   "-o", str(receipt), "--", *command, cwd=worktree)
    outputs = {}
    output_root = Path(os.environ.get("DEXLAB_RUN_ROOT") or worktree / "demos/apple-stem-grasp/runs")
    if not output_root.is_absolute():
        raise ValueError("DEXLAB_RUN_ROOT must be an absolute output directory")
    for backend in ("mujoco", "superdex"):
        output = output_root / f"autoresearch-{backend}-{run_id}"
        outputs[backend] = str(output)
        measured(backend, "episode",
            "bash",
            "demos/apple-stem-grasp/run.sh",
            "--backend",
            backend,
            "--headless",
            "--output",
            str(output),
        )
        measured(backend, "verify", python,
                 "demos/apple-stem-grasp/src/verify_sdf_grasp.py", str(output))
    result = {"run_id": run_id, "outputs": outputs}
    if wheel_dir:
        admission = output_root / f"autoresearch-admission-{run_id}.json"
        run(python, "-m", "dexlab.apple_admission", "--mujoco", outputs["mujoco"],
            "--superdex", outputs["superdex"], "--wheel-dir", wheel_dir,
            "--output", str(admission), cwd=worktree)
        result["admission"] = str(admission)
    if resource_dir is not None:
        (resource_dir / f"{run_id}-outputs.json").write_text(json.dumps(result, indent=2))
    return result


def submit(number, summary_file, check_remote_at=None, remote_state=None):
    worktree = ROOT / ".autoresearch/worktrees" / f"issue-{number}"
    branch = f"autoresearch/issue-{number}"
    if not worktree.is_dir():
        raise SystemExit("Run start first")
    if run("git", "branch", "--show-current", cwd=worktree, capture=True) != branch:
        raise SystemExit("Refusing to submit from a different branch")
    # Read review text before expensive verification or any mutation.
    summary = Path(summary_file).read_text().strip()
    if not summary:
        raise SystemExit("Provide a concrete implementation and validation summary")
    issue = authorized_issue(number)
    validated_tree = source_tree(worktree)
    if check_remote_at:
        check_remote(worktree, check_remote_at, remote_state)
    else:
        check(worktree)
    if source_tree(worktree) != validated_tree:
        raise SystemExit("Source changed during verification; rerun the gate")
    issue = authorized_issue(number)  # Approval can be withdrawn during a long gate.
    run("git", "add", "-A", cwd=worktree)
    staged = run("git", "diff", "--cached", "--name-only", cwd=worktree, capture=True)
    if run("git", "write-tree", cwd=worktree, capture=True) != validated_tree:
        raise SystemExit("Staged tree differs from the validated tree")
    if staged:
        run("git", "diff", "--cached", "--check", cwd=worktree)
        run(
            "git",
            "commit",
            "-m",
            f"research: {issue['title']} (#{number})",
            cwd=worktree,
        )
    ahead = int(
        run(
            "git",
            "rev-list",
            "--count",
            f"origin/main..{branch}",
            cwd=worktree,
            capture=True,
        )
    )
    if not ahead:
        raise SystemExit("No implementation commit to submit")
    run("git", "push", "--set-upstream", "origin", branch, cwd=worktree)
    body = (
        summary
        + f"\n\nValidation: unit tests and full MuJoCo/SuperDex 14 s SDF acceptance.\n\nRefs #{number}\n"
    )
    existing = gh_json(
        "pr", "list", "--head", branch, "--state", "open", "--json", "number,url"
    )
    if existing:
        run(
            "gh",
            "pr",
            "edit",
            str(existing[0]["number"]),
            "--repo",
            REPO,
            "--body-file",
            "-",
            input=body,
        )
        url = existing[0]["url"]
    else:
        url = run(
            "gh",
            "pr",
            "create",
            "--repo",
            REPO,
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            issue["title"],
            "--body-file",
            "-",
            input=body,
            capture=True,
        )
    result = gh_json("pr", "view", url, "--json", "url,state,headRefName,headRefOid")
    expected = run("git", "rev-parse", "HEAD", cwd=worktree, capture=True)
    if (
        result["state"] != "OPEN"
        or result["headRefName"] != branch
        or result["headRefOid"] != expected
    ):
        raise SystemExit("PR readback does not match the submitted commit")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("next").add_argument("--dry-run", action="store_true")
    sub.add_parser("start").add_argument("issue", type=int)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("worktree", type=Path)
    check_parser.add_argument("--expected-tree")
    check_parser.add_argument("--resource-dir", type=Path)
    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("issue", type=int)
    submit_parser.add_argument("--summary-file", required=True, type=Path)
    submit_parser.add_argument("--check-remote", metavar="SSH_ALIAS:/CHECKOUT")
    submit_parser.add_argument("--remote-state", type=Path)
    args = parser.parse_args()
    if args.command == "next":
        result = next_issue(explain=args.dry_run)
    elif args.command == "start":
        result = start(args.issue)
    elif args.command == "check":
        worktree = args.worktree.resolve()
        before = source_tree(worktree)
        if args.expected_tree and before != args.expected_tree:
            raise SystemExit("Remote checkout does not match the expected source tree")
        checks = check(worktree, args.resource_dir)
        if source_tree(worktree) != before:
            raise SystemExit("Source changed during verification; rerun the gate")
        result = {"source_tree": before, "checks": "full", **checks}
    else:
        result = submit(args.issue, args.summary_file, args.check_remote, args.remote_state)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
