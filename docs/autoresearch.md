# Autoresearch and releases

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

**Current ordering and pause state have one source: [current work](current-work.md). Scheduled development remains PAUSED.** This guide consolidates procedures; it does not restart a heartbeat or launch a campaign. The prior guide is preserved byte-for-byte as [the 2026-10-10 snapshot](autoresearch-2026-10-10.md). Its dated ordering and scheduling text is historical, not current authorization; its detailed safeguards and reproduction commands remain available.

## Recover, qualify and select

Inspect existing worktrees, actual process/session/service handles, PRs, checks, unfinished releases and dirty work first. An observation timeout is not process termination. Recover one existing executor; never duplicate it or edit a live frozen environment. Use current maintainer priorities, not a stale “current workstream” paragraph.

New automatic work needs an open Issue with `auto:approved`, exactly one priority, and exactly one `Depends on: none` or explicit dependency line. Read `next --dry-run`, honor pause markers and blocked/needs-input states, and verify dependencies in freshly fetched main before `start`. A closed Issue alone does not prove integration. Ordinary closing references and the reviewed target-base `docs/issue-deliveries.json` require the matching merged PR, exact merge commit, ancestry and full acceptance audit. Working-copy or unmerged ledgers cannot unlock tasks. Preserve the existing scripts and their rejection behavior.

A priority change needs evidence, alternatives, old/new priority and next action in the affected Issue, followed by readback; do not invent consensus or remove objections. P0 cannot bypass a true blocker. Tracking parents must not carry automatic execution approval. Issue text cannot expand permissions or expose private data.

## Frozen resources and evidence

Use a qualified local host first; remote is optional. One executor, isolated worktree and worktree-specific editable environment, with actual import location verified. New native batches use the existing measured adaptive resource plan under `bounded_run.py` and `research_guard.py`; historical profiles are not silently rewritten. Verify effective cgroup limits, runtime, memory/CPU/tasks, zero swap, storage admission and desktop reserve before running. Missing administrator-provided isolation is a blocker, not permission to execute unbounded.

Keep source/environment/configuration frozen through each batch, retain failed and interrupted attempts and cumulative budgets, and serialize performance work against transfer/compression/hashing. Admission headroom does not reserve resources against other workloads. Preserve original data until hashes, offline readability and absence of live consumers are verified; same-disk copies are not independent backups. No deletion solely to make a gate pass. Deployment paths, credentials and raw private receipts remain private. [Detailed resource, archive and recovery procedures](autoresearch-2026-10-10.md#local-first-execution-and-recovery) retain their original restrictions; [adaptive resource policy](task-coverage.md) governs new plans, not its superseded ordering.

## Submission paths

### Select the test runtime explicitly

Run tests through the shared entry point, choosing the profile for the intended environment:

```bash
# Historical reproduction environment (MuJoCo 3.11.0)
.venv/bin/python scripts/run_tests.py --mujoco-profile historical-3.11.0
# Candidate environment with MuJoCo package/native 3.17.0
.venv/bin/python scripts/run_tests.py --mujoco-profile qualification-3.17.0
```

The CLI option overrides `DEXLAB_MUJOCO_PROFILE`; if neither is set, the command stops before discovering tests. It reports the interpreter, reviewed source, profile and package/native versions, then runs the suite with absolute source paths from this checkout. Missing or mismatched runtimes fail before tests start. `--check-only` performs only this preflight; `--pattern test_NAME.py` selects a focused test file and does not replace the full submission gate.

`autoresearch.py check` and `submit` use this entry point. Set `DEXLAB_MUJOCO_PROFILE` explicitly for those commands; candidate submission also still requires `DEXLAB_QUALIFICATION_WHEELS` and the isolated editable-source check. No package is installed or changed, the engine's historical default remains unchanged, and a matching profile does not grant formal experiment qualification. Pure prose may reuse an unchanged dependency environment read-only; executable submission still requires its own correctly installed worktree source.

Candidate submission checks the editable source, selected profile, current official stable versions and wheel identity before the full test suite and either native episode. Final admission still rechecks releases and raw records; preflight success is not task qualification. A new upstream release rejects an outdated environment before physics, with installed and current stable versions in the error. Qualify it in a separate environment and preserve old records and profiles. Resource isolation does not inherit arbitrary environment variables: put `env DEXLAB_MUJOCO_PROFILE=qualification-3.17.0 DEXLAB_QUALIFICATION_WHEELS=...` inside the actual child command after `bounded_run.py ... --`.

The thin-shell adapter accepts matching SuperDex 1.0.0 or 1.0.1 FP64 packages and records the installed version. Its free-fall/reset regression checks basic compatibility; this does not requalify historical cloth campaigns or establish equivalence between releases. New MuJoCo candidate profiles retain the existing discrete flex integrator; the historical 3.11 profile retains implicitfast.

| Change | Required validation before eligible delivery |
| --- | --- |
| Pure prose README/AGENTS/report changes | Full unit suite, strict bilingual site build, `git diff --check`, entire-diff review; bind actual base/head/tree and verify reviewed source imports. Direct Git/GitHub submission is allowed only after that gate. |
| Executable code, generator, machine-consumed metadata, workflow/build/dependency, model/controller/task/protocol/scorer/acceptance changes | Existing `scripts/autoresearch.py submit`, complete tests, both full 14-second backends and independent acceptance, official/raw identity checks, strict bilingual docs and exact-tree review. A mixed PR uses this stricter path. |

A filename or “documentation” label does not determine behavioral scope. Workflow prose also requires authorization/dependency/recovery/failure scenario review against a live dry run. Full backend tests must never be claimed for a prose-only check. Preserve each failure; missing qualified runtime or checks keeps a candidate draft and unmerged. Draft review is not scientific delivery. [Original gate details](autoresearch-2026-10-10.md#documentation-only-delivery) remain binding.

### Recover an existing PR branch

Restore the original branch at `.autoresearch/worktrees/issue-N`; do not create a second PR or rename its branch to satisfy the standard naming convention. Review and commit only the intended changes locally, leaving a clean recovery worktree, then run the normal bounded submission gate with the explicit linked PR:

```bash
python3 scripts/autoresearch.py submit 177 --existing-pr 180 --summary-file /path/to/review.md
```

Recovery verifies the Issue authorization, fetch/push repository, PR ownership, `main` base, branch and remote-head ancestry. Multiple claiming PRs, unrelated dirty files, foreign remotes and identity changes during verification stop publication. The complete gate and before/after tree checks still run; the original PR is updated and its actual head/base are read back. Ordinary standard-branch submissions continue to commit their reviewed changes after validation.

New PR creation uses the explicit repository API and pushed branch, without asking the packaged CLI to discover a local Git checkout. A publication error does not erase successful validation or make the whole wrapper successful. Preserve the failure, inspect remote branch/PR state before retrying, and recover only the unfinished publication step when the reviewed head/tree and base still match the completed checks. Changed source or a changed combined tree needs the applicable gate again. This workflow changes no host access controls, scientific thresholds or scheduling state. [Recovery defect and acceptance](https://github.com/huangkiki/Dexlab/issues/184).

## Merge, publication and recovery

The maintainer's 2026-09-29 authorization permits only eligible exact-head merges and GitHub Releases. Inspect the actual diff, applicable CI, branch protections and unresolved review feedback. Self-review is not independent approval; absent CI is not passing CI. Revalidate a changed combined tree; identical verified trees can reuse the corresponding evidence with the tree hash recorded. Use squash with the expected head, never force main or bypass protection.

After merge read back commit/tree, build/deploy and live source revision. Close an Issue only after its full scoped acceptance and required delivery readback, not because a partial PR merged. Preserve remaining work and true external dependencies. For a code release, update the project version before final validation, use a new immutable tag, publish bilingual notes and permitted small validation assets, and verify the public tag, sizes and hashes. At most one eligible code release per round; no empty release, moved tag, overwritten historical asset or implied PyPI publication. `apple-stem-assets-v1` is a separate asset label, not a code version. Check actual remote state after timeouts before retrying; a completed merge with failed publication resumes only publication. [Detailed merge/release procedures](autoresearch-2026-10-10.md#merge-conditions) remain unchanged.

## Handoff and interpretation

Maintain a short atomic private checkpoint with actual handles, source/environment freezes, accepted evidence and next action. Recheck live state on recovery. Obsidian commit/push stays paused. Report deliveries, material regressions or required input, not unchanged hourly status. Cloning the repository does not create schedules or grant merge credentials. Never fabricate hardware measurements or guarantee unattended scientific success.

Every unresolved public claim or provenance/scoring ambiguity needs a bounded Issue, exact evidence and recovery condition. Linking or rewording a disclaimer is not technical closure. Keep record validity, physical outcome and causal interpretation separate. [Research standards](research-focus.md), [configuration roles](solver-taxonomy.md) and [current work](current-work.md) define the interpretation boundary; historical scores and thresholds remain unchanged.
