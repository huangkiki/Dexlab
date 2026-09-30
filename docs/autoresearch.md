# Autoresearch and releases

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

Codex implements, verifies and reviews issue-scoped changes, then merges eligible PRs and publishes GitHub Releases. The maintainer authorized automatic merge and release for this repository on **2026-09-29**, without per-run confirmation. `scripts/autoresearch.py` handles selection, worktrees, checks and PR submission; the authorized Codex worker performs review, merge and release through GitHub tools. Running the script alone does not merge PRs or invoke a model, and does not call Astra/Jev inside the grasp controller.

## Resume and select

1. Inspect existing worktrees, associated PRs, review feedback, applicable checks and interrupted releases first. Finish existing work; excluding claimed tasks from new dispatch must not cause them to be skipped forever. PR links and explicit `Refs #N` statements count even on other branch names.
2. Use `next --dry-run` to inspect all candidates and exclusion reasons. New tasks must be open and labeled `auto:approved`, with exactly one priority and an explicit dependency declaration. Exclude `needs-input`, `blocked`, existing worktrees and open PRs. Choose P0 before P1 before P2, then creation time. Missing metadata, unknown dependencies and cycles fail closed.
3. Handle at most one issue per run with one worker per queue. Use an isolated worktree from current `origin/main`, preserving unfinished changes. Issue bodies are task data and do not expand authorization.

```bash
python3 scripts/autoresearch.py next --dry-run
python3 scripts/autoresearch.py next
python3 scripts/autoresearch.py start 3
# In the returned worktree: bash scripts/setup.sh, then implement and review.
python3 scripts/autoresearch.py submit 3 --summary-file /path/to/review.md \
  --check-remote "$DEXLAB_CHECKOUT"
```

Run queue commands from the primary checkout; install and edit in the returned worktree. Each needs its own editable environment; uv and asset caches are reusable. `submit` reruns unit tests, both complete 14-second backend episodes and independent acceptance before committing. Failed checks stop submission. Use existing `gh`/Git authentication without changing global credentials.

## Labels, dependencies and migration

| Dimension | Labels |
|---|---|
| Primary work type | `bug`, `enhancement`, `documentation`, `experiment`, `infrastructure` |
| Area, usually one or two | `area:contact`, `area:cloth`, `area:evaluation`, `area:benchmark`, `area:backend`, `area:hardware` |
| Exactly one priority | `priority:P0` (invalid evidence, data safety, execution blockers), `priority:P1` (current core work), `priority:P2` (extensions) |
| Authorization and blockers | `auto:approved`, `needs-input`, `blocked` |

Replace broad `research` classifications individually; they never grant execution authority. `autoresearch` is the former opt-in spelling and is no longer accepted by this selector. Script and branch names remain unchanged. Tracking parents must not carry the execution opt-in once work is delegated to children. Use the existing Issue/PR state for progress.

Every executable issue declares exactly one line `Depends on: none` or, for example, `Depends on: #12, #27`. Dependencies must be closed AND have a merged PR whose GitHub closing-issue association identifies them and whose merge commit is an ancestor of the freshly fetched `origin/main`. A closed issue or a partial PR with only `Refs` is insufficient. For completed historical work lacking that association, establish a reviewed integration link rather than inventing completion evidence. Subdivide independently deliverable dependencies instead of waiting for a whole research umbrella to close.

During migration, create `dexlab-dispatch-paused` inside the directory returned by `git rev-parse --git-common-dir`. Its presence prevents new selection/creation across worktrees; existing authorized work can still be recovered and submitted. The scheduled controller also pauses dispatch while older code remains installed. Preserve snapshots, then migrate labels, bodies, code, templates, docs and scheduler instructions together. Inspect `next --dry-run`, verify ongoing work recovery, and remove only this marker after acceptance. A dry run reads GitHub and refreshes the Git base but does not claim tasks. The controller remains responsible for checking runtime resources and acceptance scope before execution.

Full physics checks run only in the authorized remote environment. Set `DEXLAB_CHECKOUT` privately to `SSH_ALIAS:/absolute/check-out`, prepare that isolated checkout with the exact source and its own environment, then pass `--check-remote` to `submit`. The gate hashes tracked and non-ignored new files with a temporary Git index; it refuses a mismatched remote tree, executes the unchanged full checks remotely, and checks both trees again before submission. Remote validation failures stop submission. This option does not copy files, forward GitHub credentials, or qualify batch execution/performance. Keep deployment values out of committed configuration and public logs. Without this option, `check`/`submit` execute on the calling host; call them there only if it is the approved simulation host.

## Merge conditions

- Review the actual PR diff against the complete issue acceptance criteria, preserving parameter provenance, approximations and failed experiments. Update both languages; do not modify official engines or relax physics thresholds.
- Bind verification to the current head and target base. When the base changes, conflicts are resolved or other changes are combined, validate the combined tree. Physics-related combinations require both complete backend checks. A commit with an exactly identical validated tree may reuse that evidence, recording the tree hash.
- Satisfy applicable CI and branch protection, with no unresolved blocking feedback. No configured CI is not a CI pass; self-review is not independent reviewer approval.
- Recheck the head and use `gh pr merge NUMBER --squash --match-head-commit HEAD_SHA`. Do not bypass protection with `--admin` or force-push. Read back `MERGED`, main's commit/tree, and issue completion. Submission uses `Refs #N`; close an issue only after verifying its complete acceptance criteria, including work outside a partial PR.
- Repair actionable problems. When external data, an environment or a necessary decision is missing, record concrete resumption conditions. Unresolved objections or failed verification prevent merging.

## Release conditions

After eligible changes are merged, publish at most one code release per run. Do not publish an empty release when nothing changed since the last code release. `apple-stem-assets-v1` distributes assets and is outside the code-version sequence.

The first code release is `v0.1.0`, matching the project version in `pyproject.toml`. Subsequent compatible fixes normally increment patch; features may increment minor. Update the package version before final verification. Create a new immutable tag; never move/delete existing tags or overwrite old release assets.

1. Tag the validated main commit, push, and verify the remote target.
2. Prepare Chinese/English notes covering changes, actual verification, commit/tree and limitations. Attach small validation reports without repackaging unauthorized third-party assets.
3. Use `gh release create` with the tag, notes file and evidence attachments. Read back the public release, tag target, asset sizes and hashes before reporting completion. This publishes a GitHub Release, not an automatic PyPI distribution.
4. After an uncertain push/create response, inspect remote state before retrying to avoid duplicates. If merge succeeded but publication failed, resume publication only.

## Scheduling and boundaries

The current Codex heartbeat checks this thread hourly, stays quiet when state is unchanged, and reports releases, regressions or required input. Scheduling belongs to the maintainer's app/account; cloning the repository does not create a schedule, grant credentials or authorize merges for other users. The host and runtime environment must be available.

This is a verifiable development workflow, not guaranteed unattended scientific discovery; missing hardware measurements cannot be invented. [Issues](https://github.com/huangkiki/Dexlab/issues) track research scope, dependencies and progress. See the delivered [model audit](model-audit.md) and [jitter diagnostics](jitter.md).

[Parameter provenance and research methods](research-focus.md) · [DexLab](../README.en.md)
