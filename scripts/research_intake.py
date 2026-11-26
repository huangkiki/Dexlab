"""Synchronize versioned research decisions from Discussions into GitHub Issues.

The Discussion owns the machine-readable decision block. This module validates
that contract, maintains one Triage umbrella issue per Discussion, and can
promote a selected candidate into a linked execution issue. It never grants
``auto:approved``.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

OWNER = "huangkiki"
REPO = f"{OWNER}/Dexlab"
PROJECT_NUMBER = 4
INTAKE_VERSION = 1
INTAKE_START = "<!-- dexlab-intake:v1:start -->"
INTAKE_END = "<!-- dexlab-intake:v1:end -->"
NON_EXECUTABLE_MARKER = "<!-- dexlab-intake-non-executable:v1 -->"
TRIAGE_STATUS = "Triage"
TODO_STATUS = "Todo"
DECISIONS = {"adopt-existing", "pilot", "experiment", "watch", "reject"}
CANDIDATE_KINDS = {"experiment", "enhancement", "bug", "documentation", "infrastructure"}
PRIORITIES = {"P0", "P1", "P2"}
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")


class IntakeError(ValueError):
    """A malformed or non-idempotent research-intake operation."""


def run(*args: str, input: str | None = None) -> str:
    result = subprocess.run(
        args,
        check=True,
        text=True,
        input=input,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def gh_json(*args: str) -> Any:
    return json.loads(run("gh", *args, "--repo", REPO))


def graphql(query: str) -> dict[str, Any]:
    return json.loads(run("gh", "api", "graphql", "-f", f"query={query}"))["data"]


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntakeError(f"{field} must be a nonempty string")
    return value.strip()


def _string_list(value: Any, field: str, *, required: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise IntakeError(f"{field} must be a list of nonempty strings")
    values = [item.strip() for item in value]
    if required and not values:
        raise IntakeError(f"{field} must not be empty")
    return values


def _relative_path(value: str, field: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.startswith(("/", "~")):
        raise IntakeError(f"{field} must use repository-relative paths: {value}")


def parse_discussion_body(body: str, discussion: int) -> dict[str, Any]:
    """Extract and strictly validate the single intake block in a Discussion."""
    if body.count(INTAKE_START) != 1 or body.count(INTAKE_END) != 1:
        raise IntakeError("Discussion must contain exactly one dexlab-intake:v1 block")
    pattern = re.compile(
        re.escape(INTAKE_START)
        + r"\s*```json\s*(.*?)\s*```\s*"
        + re.escape(INTAKE_END),
        re.DOTALL,
    )
    matches = pattern.findall(body)
    if len(matches) != 1:
        raise IntakeError("Intake markers must wrap exactly one fenced json block")
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as error:
        raise IntakeError(f"Invalid intake JSON: {error}") from error
    return validate_payload(payload, discussion)


def validate_payload(payload: Any, discussion: int) -> dict[str, Any]:
    """Validate the public intake schema without inventing missing research choices."""
    if not isinstance(payload, dict):
        raise IntakeError("Intake payload must be an object")
    required = {
        "schema_version", "discussion", "slug", "title", "decision",
        "summary", "current_work_impact", "candidates",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise IntakeError("Missing intake fields: " + ", ".join(missing))
    if type(payload["schema_version"]) is not int or payload["schema_version"] != INTAKE_VERSION:
        raise IntakeError(f"schema_version must be {INTAKE_VERSION}")
    if type(payload["discussion"]) is not int or payload["discussion"] != discussion:
        raise IntakeError("discussion must match the Discussion being imported")
    slug = _nonempty_string(payload["slug"], "slug")
    if not SLUG.fullmatch(slug):
        raise IntakeError("slug must contain 3-64 lowercase letters, digits or hyphens")
    title = _nonempty_string(payload["title"], "title")
    if len(title) > 120:
        raise IntakeError("title must be at most 120 characters")
    decision = _nonempty_string(payload["decision"], "decision")
    if decision not in DECISIONS:
        raise IntakeError("decision must be one of: " + ", ".join(sorted(DECISIONS)))
    summary = _nonempty_string(payload["summary"], "summary")
    impact = _nonempty_string(payload["current_work_impact"], "current_work_impact")
    candidates = payload["candidates"]
    if not isinstance(candidates, list):
        raise IntakeError("candidates must be a list")
    if decision in {"watch", "reject"} and candidates:
        raise IntakeError("watch/reject decisions must not contain executable candidates")
    if decision not in {"watch", "reject"} and not candidates:
        raise IntakeError("actionable decisions require at least one candidate")

    seen = set()
    normalized = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            raise IntakeError(f"{prefix} must be an object")
        candidate_required = {
            "slug", "kind", "goal", "entrypoints", "first_slice",
            "acceptance", "depends_on", "non_goals",
        }
        candidate_missing = sorted(candidate_required - set(candidate))
        if candidate_missing:
            raise IntakeError(f"{prefix} is missing: " + ", ".join(candidate_missing))
        candidate_slug = _nonempty_string(candidate["slug"], f"{prefix}.slug")
        if not SLUG.fullmatch(candidate_slug) or candidate_slug in seen:
            raise IntakeError(f"{prefix}.slug must be unique and URL-safe")
        seen.add(candidate_slug)
        kind = _nonempty_string(candidate["kind"], f"{prefix}.kind")
        if kind not in CANDIDATE_KINDS:
            raise IntakeError(f"{prefix}.kind must be one of: " + ", ".join(sorted(CANDIDATE_KINDS)))
        goal = _nonempty_string(candidate["goal"], f"{prefix}.goal")
        entrypoints = _string_list(candidate["entrypoints"], f"{prefix}.entrypoints")
        for entrypoint in entrypoints:
            _relative_path(entrypoint, f"{prefix}.entrypoints")
        first_slice = _nonempty_string(candidate["first_slice"], f"{prefix}.first_slice")
        acceptance = _string_list(candidate["acceptance"], f"{prefix}.acceptance")
        depends_on = candidate["depends_on"]
        if not isinstance(depends_on, list) or any(
            type(number) is not int or number <= 0 for number in depends_on
        ) or len(set(depends_on)) != len(depends_on):
            raise IntakeError(f"{prefix}.depends_on must contain unique positive Issue numbers")
        non_goals = _string_list(candidate["non_goals"], f"{prefix}.non_goals", required=False)
        target_issue = candidate.get("target_issue")
        if target_issue is not None and (type(target_issue) is not int or target_issue <= 0):
            raise IntakeError(f"{prefix}.target_issue must be a positive Issue number")
        normalized.append({
            "slug": candidate_slug,
            "kind": kind,
            "goal": goal,
            "entrypoints": entrypoints,
            "first_slice": first_slice,
            "acceptance": acceptance,
            "depends_on": depends_on,
            "non_goals": non_goals,
            **({"target_issue": target_issue} if target_issue is not None else {}),
        })
    return {
        "schema_version": INTAKE_VERSION,
        "discussion": discussion,
        "slug": slug,
        "title": title,
        "decision": decision,
        "summary": summary,
        "current_work_impact": impact,
        "candidates": normalized,
    }


def load_discussion(number: int) -> dict[str, Any]:
    if type(number) is not int or number <= 0:
        raise IntakeError("Discussion number must be positive")
    data = graphql(f"""
query {{
  repository(owner: "{OWNER}", name: "Dexlab") {{
    discussion(number: {number}) {{
      id
      number
      title
      body
      url
      comments(first: 100) {{ totalCount nodes {{ body }} }}
    }}
  }}
}}
""")
    discussion = (data.get("repository") or {}).get("discussion")
    if not discussion:
        raise IntakeError(f"Discussion #{number} was not found")
    if discussion["number"] != number:
        raise IntakeError("Discussion identity changed during lookup")
    return discussion


def _umbrella_marker(payload: dict[str, Any]) -> str:
    return (
        "<!-- dexlab-intake-issue:v1 "
        f"discussion={payload['discussion']} slug={payload['slug']} -->"
    )


def _child_marker(umbrella: int, payload: dict[str, Any], candidate: dict[str, Any]) -> str:
    return (
        "<!-- dexlab-intake-child:v1 "
        f"umbrella={umbrella} discussion={payload['discussion']} slice={candidate['slug']} -->"
    )


def _link_marker(discussion: int, slug: str) -> str:
    return f"<!-- dexlab-intake-link:v1 discussion={discussion} slug={slug} -->"


def _bullets(values: list[str], empty: str = "none", indent: str = "") -> str:
    return (
        "\n".join(f"{indent}- {value}" for value in values)
        if values else f"{indent}- {empty}"
    )


def render_umbrella(payload: dict[str, Any], discussion_url: str) -> str:
    slices = []
    for index, candidate in enumerate(payload["candidates"], 1):
        slices.append(
            f"""### {index}. `{candidate['slug']}`

- Type: `{candidate['kind']}`
- Goal: {candidate['goal']}
- First slice: {candidate['first_slice']}
- Entry points:
{_bullets(candidate['entrypoints'], indent='  ')}
- Acceptance:
{_bullets(candidate['acceptance'], indent='  ')}
- Dependencies: {', '.join(f'#{n}' for n in candidate['depends_on']) or 'none'}
- Explicit non-goals:
{_bullets(candidate['non_goals'], indent='  ')}
"""
        )
    return f"""{_umbrella_marker(payload)}
{NON_EXECUTABLE_MARKER}
## Research source / 研究来源

- Discussion #{payload['discussion']}: {discussion_url}
- Decision: `{payload['decision']}`
- Summary: {payload['summary']}

## Candidate slices / 候选切片

{''.join(slices)}
## Planning impact / 开发计划影响

{payload['current_work_impact']}

This umbrella issue is a Triage container. It is not authorized for execution
without a promoted child issue and a separate `auto:approved` label.

## Dependencies / 依赖

Depends on: none
"""


def render_child(
    payload: dict[str, Any],
    candidate: dict[str, Any],
    umbrella: int,
    discussion_url: str,
) -> str:
    dependencies = ", ".join(f"#{number}" for number in candidate["depends_on"]) or "none"
    return f"""{_child_marker(umbrella, payload, candidate)}
## Problem and evidence / 问题与证据

- Parent intake: #{umbrella}
- Source Discussion: {discussion_url}
- Decision: `{payload['decision']}`
- Goal: {candidate['goal']}

## Deliverable and exclusions / 交付与范围外内容

**First slice:** {candidate['first_slice']}

**Entry points:**
{_bullets(candidate['entrypoints'])}

**Explicit non-goals:**
{_bullets(candidate['non_goals'])}

## Acceptance and commands / 验收与命令

{_bullets(candidate['acceptance'])}

Suggested validation entrypoint (adjust `--test` / `--backend` to match modified files):
```bash
python3 scripts/autoresearch.py check . --base origin/main
```

## Dependencies / 依赖

Depends on: {dependencies}

## Resources and blockers / 资源与阻塞

Use only the resources already permitted by the parent intake and the current
execution record. Promotion does not grant execution authorization.
"""


def _find_issue(marker: str) -> dict[str, Any] | None:
    issues = gh_json(
        "issue", "list", "--state", "all", "--limit", "1000", "--json",
        "number,state,title,body,url,labels,author",
    )
    if len(issues) >= 1000:
        raise IntakeError("Issue inventory limit reached; refusing an incomplete snapshot")
    matches = [issue for issue in issues if marker in issue.get("body", "")]
    if len(matches) > 1:
        raise IntakeError(f"Multiple Issues contain the same intake marker: {marker}")
    return matches[0] if matches else None


def _project_context(status: str) -> dict[str, str]:
    data = graphql(f"""
query {{
  user(login: "{OWNER}") {{
    projectV2(number: {PROJECT_NUMBER}) {{
      id
      fields(first: 50) {{
        nodes {{
          ... on ProjectV2SingleSelectField {{ id name options {{ id name }} }}
        }}
      }}
    }}
  }}
}}
""")
    project = (data.get("user") or {}).get("projectV2")
    if not project:
        raise IntakeError(f"Project {PROJECT_NUMBER} was not found")
    status_field = next(
        (field for field in project["fields"]["nodes"] if field and field.get("name") == "Status"),
        None,
    )
    option = next(
        (item for item in status_field.get("options", []) if item["name"] == status),
        None,
    ) if status_field else None
    if not status_field or not option:
        raise IntakeError(f"Project {PROJECT_NUMBER} has no Status option {status!r}")
    return {
        "project_id": project["id"],
        "field_id": status_field["id"],
        "option_id": option["id"],
    }


def _project_item(url: str) -> dict[str, Any] | None:
    result = json.loads(run(
        "gh", "project", "item-list", str(PROJECT_NUMBER),
        "--owner", OWNER, "--limit", "1000", "--format", "json",
    ))
    items = result.get("items", [])
    if len(items) >= 1000:
        raise IntakeError("Project item limit reached; refusing an incomplete snapshot")
    matches = [
        item for item in items
        if (item.get("content") or {}).get("url") == url
    ]
    if len(matches) > 1:
        raise IntakeError(f"Project {PROJECT_NUMBER} contains multiple items for {url}")
    return matches[0] if matches else None


def ensure_project_status(url: str, status: str) -> dict[str, Any]:
    context = _project_context(status)
    item = _project_item(url)
    if item is None:
        item = json.loads(run(
            "gh", "project", "item-add", str(PROJECT_NUMBER),
            "--owner", "@me", "--url", url, "--format", "json",
        ))
    if item.get("status") != status:
        run(
            "gh", "project", "item-edit",
            "--id", item["id"],
            "--project-id", context["project_id"],
            "--field-id", context["field_id"],
            "--single-select-option-id", context["option_id"],
        )
    readback = _project_item(url)
    if readback is None or readback.get("status") != status:
        raise IntakeError(f"Project status readback for {url} is not {status!r}")
    return readback


def _create_issue(title: str, body: str, labels: tuple[str, ...] = ()) -> str:
    args = ["gh", "issue", "create", "--repo", REPO, "--title", title, "--body-file", "-"]
    for label in labels:
        args += ["--label", label]
    url = run(*args, input=body)
    if not re.fullmatch(rf"https://github\.com/{re.escape(REPO)}/issues/\d+", url):
        raise IntakeError(f"Issue creation returned an unexpected URL: {url!r}")
    return url


def _comment_link(discussion: dict[str, Any], issue_url: str, slug: str) -> bool:
    marker = _link_marker(discussion["number"], slug)
    comments = (discussion.get("comments") or {}).get("nodes", [])
    if any(marker in comment.get("body", "") for comment in comments):
        return False
    if (discussion.get("comments") or {}).get("totalCount", 0) >= 100:
        raise IntakeError("Discussion has reached the checked comment window; inspect before commenting")
    body = f"{marker}\n研究 intake 已登记为 {issue_url}。"
    graphql(f'''
mutation {{
  addDiscussionComment(input: {{
    discussionId: {json.dumps(discussion["id"])}
    body: {json.dumps(body)}
  }}) {{
    comment {{ id }}
  }}
}}
''')
    return True


def _issue_parent(number: int) -> dict[str, Any] | None:
    data = graphql(f"""
query {{
  repository(owner: "{OWNER}", name: "Dexlab") {{
    issue(number: {number}) {{ parent {{ id number }} }}
  }}
}}
""")
    issue = (data.get("repository") or {}).get("issue")
    if not issue:
        raise IntakeError(f"Issue #{number} was not found")
    return issue["parent"]


def check(number: int) -> dict[str, Any]:
    discussion = load_discussion(number)
    payload = parse_discussion_body(discussion["body"], number)
    actionable = payload["decision"] not in {"watch", "reject"}
    return {
        "discussion": number,
        "url": discussion["url"],
        "action": "create-umbrella" if actionable else "record-disposition-only",
        "payload": payload,
    }


def sync(number: int, *, dry_run: bool = False) -> dict[str, Any]:
    discussion = load_discussion(number)
    payload = parse_discussion_body(discussion["body"], number)
    if payload["decision"] in {"watch", "reject"}:
        return {
            "discussion": number,
            "action": "none",
            "reason": "watch/reject decisions do not create Triage Issues",
        }
    context = _project_context(TRIAGE_STATUS)
    marker = _umbrella_marker(payload)
    existing = _find_issue(marker)
    title = f"[Research intake] {payload['title']}"
    body = render_umbrella(payload, discussion["url"])
    if existing is not None and existing["state"] == "CLOSED":
        raise IntakeError("The existing intake umbrella is closed; reopen it explicitly or use a new Discussion decision")
    if dry_run:
        return {
            "discussion": number,
            "action": "update" if existing else "create",
            "issue": existing["number"] if existing else None,
            "title": title,
            "body": body,
            "payload": payload,
            "project_status": TRIAGE_STATUS,
            "project_context": context,
        }
    if existing is None:
        url = _create_issue(title, body)
        issue_number = int(url.rsplit("/", 1)[1])
        action = "created"
    else:
        issue_number, url, action = existing["number"], existing["url"], "updated"
        run(
            "gh", "issue", "edit", str(issue_number), "--repo", REPO,
            "--title", title, "--body-file", "-", input=body,
        )
    project_item = ensure_project_status(url, TRIAGE_STATUS)
    commented = _comment_link(discussion, url, payload["slug"])
    readback = gh_json(
        "issue", "view", str(issue_number), "--json",
        "number,state,title,body,url,labels",
    )
    if (
        readback["body"] != body
        or readback["title"] != title
        or run("gh", "issue", "view", str(issue_number), "--repo", REPO, "--json", "url", "--jq", ".url")
        != url
    ):
        raise IntakeError("Umbrella Issue readback does not match the written intake")
    return {
        "discussion": number,
        "action": action,
        "issue": readback["number"],
        "url": readback["url"],
        "state": readback["state"],
        "project_status": project_item.get("status", TRIAGE_STATUS),
        "discussion_comment_added": commented,
    }


def _parse_issue_marker(body: str) -> tuple[int, str]:
    match = re.search(
        r"<!-- dexlab-intake-issue:v1 discussion=(\d+) slug=([a-z0-9-]+) -->",
        body,
    )
    if not match:
        raise IntakeError("Issue is not a dexlab intake umbrella")
    return int(match.group(1)), match.group(2)


def promote(
    umbrella: int,
    slice_slug: str,
    priority: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    priority = priority.upper()
    if priority not in PRIORITIES:
        raise IntakeError("priority must be P0, P1 or P2")
    umbrella_issue = gh_json(
        "issue", "view", str(umbrella), "--json",
        "number,state,title,body,url,id,labels",
    )
    discussion_number, umbrella_slug = _parse_issue_marker(umbrella_issue["body"])
    body_text = umbrella_issue["body"]
    has_structured_guard = NON_EXECUTABLE_MARKER in body_text
    has_legacy_guard = "not authorized" in body_text.lower()
    if not (has_structured_guard or has_legacy_guard):
        raise IntakeError("Umbrella body is missing the non-executable intake marker")
    discussion = load_discussion(discussion_number)
    payload = parse_discussion_body(discussion["body"], discussion_number)
    if payload["slug"] != umbrella_slug:
        raise IntakeError("Umbrella slug does not match the source Discussion")
    candidate = next(
        (item for item in payload["candidates"] if item["slug"] == slice_slug),
        None,
    )
    if candidate is None:
        raise IntakeError(f"Slice {slice_slug!r} is not present in Discussion #{discussion_number}")
    marker = _child_marker(umbrella, payload, candidate)
    existing = _find_issue(marker)
    project = _project_context(TODO_STATUS)
    title = f"[Research execution] {candidate['goal']}"
    body = render_child(payload, candidate, umbrella, discussion["url"])
    if dry_run:
        return {
            "action": "reuse" if existing else "create",
            "issue": existing["number"] if existing else None,
            "title": title,
            "body": body,
            "labels": [candidate["kind"], f"priority:{priority}"],
            "project_status": TODO_STATUS,
            "project_context": project,
        }
    if existing is None:
        url = _create_issue(
            title,
            body,
            (candidate["kind"], f"priority:{priority}"),
        )
        child_number = int(url.rsplit("/", 1)[1])
        action = "created"
    else:
        child_number, url, action = existing["number"], existing["url"], "reused"
    child = gh_json(
        "issue", "view", str(child_number), "--json",
        "number,state,title,body,url,id,labels",
    )
    if "auto:approved" in {label["name"] for label in child["labels"]}:
        raise IntakeError("Promotion must not grant auto:approved")
    ensure_project_status(url, TODO_STATUS)
    parent = _issue_parent(child_number)
    if parent is not None and parent["id"] != umbrella_issue["id"]:
        raise IntakeError(f"Issue #{child_number} already belongs to a different parent intake")
    if parent is None:
        graphql(f'''
mutation {{
  addSubIssue(input: {{
    issueId: {json.dumps(umbrella_issue["id"])}
    subIssueId: {json.dumps(child["id"])}
    replaceParent: false
  }}) {{
    issue {{ id }}
  }}
}}
''')
    return {
        "action": action,
        "issue": child["number"],
        "url": child["url"],
        "state": child["state"],
        "project_status": TODO_STATUS,
        "execution_authorized": False,
    }
