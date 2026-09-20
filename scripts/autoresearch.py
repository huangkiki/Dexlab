#!/usr/bin/env python3
"""Issue queue and verified PR submission for the Codex research worker.

This tool does not invent a policy or invoke a hidden model. The scheduled Codex
worker reads the selected issue, implements it, and uses these commands to keep
work isolated and run checks before submission.
"""

import argparse
import json
import subprocess
from pathlib import Path

REPO = "huangkiki/Dexlab"
ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, capture=False, input=None):
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        input=input,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def gh_json(*args):
    return json.loads(run("gh", *args, "--repo", REPO, capture=True))


def select_issue(issues, pulls):
    """Only explicitly opted-in, open issues without an existing open PR."""
    active = {pr["headRefName"] for pr in pulls}
    candidates = [
        item
        for item in issues
        if item["state"] == "OPEN"
        and "autoresearch" in {label["name"] for label in item["labels"]}
        and "needs-input" not in {label["name"] for label in item["labels"]}
        and f"autoresearch/issue-{item['number']}" not in active
    ]
    return min(candidates, key=lambda item: item["number"], default=None)


def next_issue():
    issues = gh_json(
        "issue",
        "list",
        "--state",
        "open",
        "--label",
        "autoresearch",
        "--limit",
        "100",
        "--json",
        "number,title,body,state,labels,url",
    )
    pulls = gh_json(
        "pr",
        "list",
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        "number,headRefName,url",
    )
    return select_issue(issues, pulls)


def start(number):
    issue = gh_json(
        "issue", "view", str(number), "--json", "number,title,body,state,labels,url"
    )
    if select_issue([issue], []) is None:
        raise SystemExit(
            "Issue must be open, labeled autoresearch, and not needs-input"
        )
    branch = f"autoresearch/issue-{number}"
    worktree = ROOT / ".autoresearch" / "worktrees" / f"issue-{number}"
    if not worktree.exists():
        run("git", "fetch", "origin", "main")
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


def check(worktree):
    """Always verify both physical episodes; test logs stay inside the worktree."""
    python = str(worktree / ".venv/bin/python")
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
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        cwd=worktree,
    )
    for backend in ("mujoco", "superdex"):
        output = worktree / "demos/apple-stem-grasp/runs" / f"autoresearch-{backend}"
        run(
            "bash",
            "demos/apple-stem-grasp/run.sh",
            "--backend",
            backend,
            "--headless",
            "--output",
            str(output),
            cwd=worktree,
        )
        run(
            python,
            "demos/apple-stem-grasp/src/verify_sdf_grasp.py",
            str(output),
            cwd=worktree,
        )


def submit(number, summary_file):
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
    issue = gh_json(
        "issue", "view", str(number), "--json", "number,title,body,state,labels,url"
    )
    if select_issue([issue], []) is None:
        raise SystemExit("Issue is no longer eligible")
    check(worktree)
    run("git", "add", "-A", cwd=worktree)
    staged = run("git", "diff", "--cached", "--name-only", cwd=worktree, capture=True)
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
        + f"\n\nValidation: unit tests and full MuJoCo/SuperDex 14 s SDF acceptance.\n\nFixes #{number}\n"
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
    sub.add_parser("next")
    sub.add_parser("start").add_argument("issue", type=int)
    sub.add_parser("check").add_argument("worktree", type=Path)
    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("issue", type=int)
    submit_parser.add_argument("--summary-file", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "next":
        result = next_issue()
    elif args.command == "start":
        result = start(args.issue)
    elif args.command == "check":
        result = check(args.worktree.resolve())
    else:
        result = submit(args.issue, args.summary_file)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
