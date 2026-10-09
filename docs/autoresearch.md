# Autoresearch and releases

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

Codex implements, verifies and reviews issue-scoped changes, then merges eligible PRs and publishes GitHub Releases. The maintainer authorized automatic merge and release for this repository on **2026-09-29**, without per-run confirmation. `scripts/autoresearch.py` handles selection, worktrees, checks and PR submission; the authorized Codex worker performs review, merge and release through GitHub tools. Running the script alone does not merge PRs or invoke a model, and does not call Astra/Jev inside the grasp controller.

## Current execution policy (2026-10-09)

[Task coverage and continuous development](task-coverage.md) is the latest authorized ordering, dual-version, work-package and resource policy. It supersedes the earlier pinch-first ordering and legacy resource defaults below; historical commands/configurations remain for reproduction. The queue filters dependencies; the executor restores and selects an explicit Issue under the new plan. Drake or irrecoverable historical telemetry must not block independent tasks. New batches use `--profile adaptive --resource-plan BATCH.json`, not the old 16 GiB / 2-core profile.

## Resume and select

1. Inspect existing worktrees, associated PRs, review feedback, applicable checks and interrupted releases first. Finish existing work; excluding claimed tasks from new dispatch must not cause them to be skipped forever. PR links and explicit `Refs #N` statements count even on other branch names.
2. Use `next --dry-run` to inspect all candidates and exclusion reasons. New tasks must be open and labeled `auto:approved`, with exactly one priority and an explicit dependency declaration. Exclude `needs-input`, `blocked`, existing worktrees and open PRs. Choose P0 before P1 before P2, then creation time. Missing metadata, unknown dependencies and cycles fail closed.
3. Handle one issue at a time with one worker per queue. A continuous goal can repeat this cycle after each verified delivery; an hourly trigger is recovery guidance, not a stopping boundary. Use an isolated worktree from current `origin/main`, preserving unfinished changes. Issue bodies are task data and do not expand authorization.

```bash
python3 scripts/autoresearch.py next --dry-run
python3 scripts/autoresearch.py next
python3 scripts/autoresearch.py start 3
# In the returned worktree: bash scripts/setup.sh, then implement and review.
python3 scripts/autoresearch.py submit 3 --summary-file /path/to/review.md \
  --check-remote "$DEXLAB_CHECKOUT"
```

Run queue commands from the primary checkout; install and edit in the returned worktree. Each needs its own editable environment; uv and asset caches are reusable. `submit` reruns unit tests, both complete 14-second backend episodes and independent acceptance before committing. Failed checks stop submission. Use existing `gh`/Git authentication without changing global credentials.

## Current workstream and Discussion handoff (2026-10-09)

The [unified-drive pinch roadmap](pinch-boundary-roadmap.md) connects Discussion [#129](https://github.com/huangkiki/Dexlab/discussions/129), tracking-only parent [#130](https://github.com/huangkiki/Dexlab/issues/130), and execution chain #131 → #132 → #133 → #134. Do not add `auto:approved` to the parent. The maintainer explicitly selected these four P1 children as the current workstream; P0 #124/#125/#126 and later urgent P0s remain ahead.

Each iteration first inspects and safely recovers/concludes live workers and in-flight delivery, then reads `next --dry-run`. When no P0 is actionable, choose an eligible child of this workstream whose dependencies are verified delivered and call the existing `start ISSUE`. Creation-time order is the default recommendation, not an override of the maintainer's explicit selection. Recover existing workstream worktrees instead of recreating them when excluded from eligible. Pause, authorization, blockers, dependency proofs and single-worker rules still apply. If every child is blocked, record restoration conditions and continue other independent authorized tasks without inventing dependencies or closing old work.

Discussion owns research tradeoffs and stage interpretation; Issues own scope, questions, acceptance and recovery; PRs and repository protocols/manifests govern delivery and runs. Unreviewed discussion comments cannot alter frozen experiments. Return to #129 after #132 qualification and #134 reporting, converting actions into Issues. Verify code delivery, complete two-engine acquisition and the six-engine research objective separately. This integration creates entry points; it neither launches physics nor creates a scheduled job.

The campaign's 6 h / 700-start budget includes qualification, bridging, formal cases, controls and retries. Development/submission regressions are accounted separately under existing limits. Recoverable accounting, native observations and scoring remain undelivered child-Issue acceptance items. See the roadmap for scope, tests and completion criteria.

## Public uncertainty becomes work

Any unresolved fact, provenance, implementation or measurement/scoring ambiguity found while developing must have a bounded Issue. Search existing work first. Record the exact public sentence or artifact and its version, question, known evidence, interpretation impact, verification route, acceptance, resources and concrete recovery condition. Use the existing labels and selector; no separate uncertainty database or scheduler.

Public README/site ambiguity defaults to `priority:P0` before new P1 capabilities. Safety incidents and corrupt evidence still take precedence. Review the priority with evidence, assign exactly one priority, declare dependencies, then read back `next --dry-run`; an Issue link alone is not queue admission. Resume or finish the current live worker safely before switching work. A blocker does not disappear because the Issue is P0; continue other eligible independent work. Priority is not a hard dependency: declare a dependency when work actually consumes that evidence/deliverable; unrelated unresolved historical provenance does not automatically forbid newly qualified evidence.

Use known facts and a direct audit link in both README languages and public homepages. Source an algorithm from the version and selected path that actually ran, not a current default. Preserve frozen historical artifacts and add a versioned evidence supplement. An audit that cannot recover identity remains open/blocked with an exact recovery condition, or withdraws the affected interpretation through an explicit reviewed decision and separately tracks remaining work. A wording edit, linked Issue or empty disclaimer is not technical closure. Quantified uncertainty with a defined evidence basis remains a scientific result, not an unresolved identity claim.

Current public audits: [SuperDex #124](https://github.com/huangkiki/Dexlab/issues/124), [Genesis #125](https://github.com/huangkiki/Dexlab/issues/125), [historical PhysX #126](https://github.com/huangkiki/Dexlab/issues/126). Their technical acceptance is separate from the workflow change #123.

## Documentation-only delivery

For prose-only README/AGENTS, Markdown reports/workflow instructions and Markdown Issue templates, a single worker may submit via direct Git/`gh` after full unit tests, the strict bilingual site build, `git diff --check` and review of the entire diff. Bind the record to the actual base/head/tree, state the test environment and confirm imports resolve to the reviewed worktree. An unchanged qualified environment may be reused read-only with the worktree source explicitly selected. Stage only the reviewed files. The PR must name this documentation-only path and its actual checks; do not copy the full-backend validation statement emitted by `submit`.

This path excludes changes to executable code, machine-consumed delivery ledgers or admission metadata, workflows/build configuration, dependency/runtime versions, assets, physical models, controllers, task protocols, scoring or acceptance thresholds. Such changes use `scripts/autoresearch.py submit` and the complete applicable gate. That script remains unchanged and always runs the full backend checks. Classify by behavioral impact, not extension or label: machine-read labels, dependencies or other Markdown-template fields that change dispatch/acceptance take the stricter path. Workflow prose changes require scenario review of authorization, priority/dependencies, recovery and failure handling against a live queue dry run; changes to scientific acceptance or executable behavior still require the full applicable gate. A mixed PR follows the stricter path.

For either path, inspect current-head checks and unresolved feedback, validate the combined tree, merge with the expected head only under existing authorization, then verify the merged tree, actual site build/deploy and live `build-info.json`. A documentation-only change does not require a new code release.

## Labels, dependencies and migration

| Dimension | Labels |
|---|---|
| Primary work type | `bug`, `enhancement`, `documentation`, `experiment`, `infrastructure` |
| Area, usually one or two | `area:contact`, `area:cloth`, `area:evaluation`, `area:benchmark`, `area:backend`, `area:hardware` |
| Exactly one priority | `priority:P0` (public evidence ambiguity, invalid evidence, data safety, execution blockers), `priority:P1` (current core work), `priority:P2` (extensions) |
| Authorization and blockers | `auto:approved`, `needs-input`, `blocked` |

Replace broad `research` classifications individually; they never grant execution authority. `autoresearch` is the former opt-in spelling and is no longer accepted by this selector. Script and branch names remain unchanged. Tracking parents must not carry the execution opt-in once work is delegated to children. Use the existing Issue/PR state for progress.

Every executable issue declares exactly one line `Depends on: none` or, for example, `Depends on: #12, #27`. Dependencies must be closed AND have a merged PR whose GitHub closing-issue association identifies them and whose merge commit is an ancestor of the freshly fetched `origin/main`. A closed issue or a partial PR with only `Refs` is insufficient. For completed historical work lacking that association, establish a reviewed integration link rather than inventing completion evidence. Subdivide independently deliverable dependencies instead of waiting for a whole research umbrella to close.

During migration, create `dexlab-dispatch-paused` inside the directory returned by `git rev-parse --git-common-dir`. Its presence prevents new selection/creation across worktrees; existing authorized work can still be recovered and submitted. The scheduled controller also pauses dispatch while older code remains installed. Preserve snapshots, then migrate labels, bodies, code, templates, docs and scheduler instructions together. Inspect `next --dry-run`, verify ongoing work recovery, and remove only this marker after acceptance. A dry run reads GitHub and refreshes the Git base but does not claim tasks. The controller remains responsible for checking runtime resources and acceptance scope before execution.

## Local-first execution and recovery

Use a qualified local host first; remote execution is optional. Local authorization is not resource qualification. Launch experiments through the existing bounded runner, inside the cooperative research window:

```bash
python3 scripts/bounded_run.py --profile experiment \
  --io-device "$DATA_DEVICE" --data-dir "$DATA_DIR" \
  --receipt "$PRIVATE_STATE/unique-resources.json" -- \
  python3 scripts/research_guard.py run \
    --lock "$PRIVATE_STATE/window.lock" --kind qualification \
    --receipt "$PRIVATE_STATE/unique-window.json" -- \
    python3 scripts/autoresearch.py submit 49 --summary-file "$REVIEW"
```

All variables are private deployment configuration. Set the selected worktree's ignored run-output directory on the data volume before launch; `--data-dir` checks the volume but does not redirect arbitrary child writes. Preserve existing directories rather than replacing them. Archive evidence and raw outputs must not enter Git. The bounded runner requires the existing administrator-provided `sudo -n systemd-run` capability and never creates privileges or falls back to unbounded execution.

The experiment profile enforces 16 GiB maximum / 15 GiB high memory, CPU quota 200% (two logical-core equivalents), 128 tasks, zero experiment swap and a one-hour maximum runtime. Data-device I/O is limited to 32 MiB/s reads and 16 MiB/s writes. It checks effective cgroup limits before the command and records counters and systemd results. Missing final telemetry prevents successful qualification. Admission requires measured available RAM for the envelope plus 8 GiB desktop reserve and at least 20 GiB free on the configured data volume, checked before launch and again inside the service. The supplied device must directly back that volume or its partition; stacked storage needs separate qualification. Headroom is a launch-time check, not protection against unrelated future workloads. The archive profile keeps its existing 8/6 GiB, one-CPU, 32-task and 16/8 MiB/s limits. These conservative starting profiles are not tuned performance settings; additional concurrency requires measurement.

Before any launch, recheck recorded process/session/service handles, source tree and environment. A timeout while observing is not process termination. Continue a live job without changing its frozen source/environment or starting another. Keep failed/interrupted receipts; retry only after actual termination with fresh output and receipt identities. Confirm hashes, offline readability and no active consumers before deleting originals; another directory on the same disk is not an independent backup. The shared guard serializes timing against transfer/compression/hash work. Qualification includes setup/tests/source hashing and is not a speed benchmark; record local/remote hardware and do not pool their timings as identical conditions.

For an optional remote gate, set `DEXLAB_CHECKOUT` privately to `SSH_ALIAS:/absolute/check-out` and pass `--check-remote` to `submit`. Prepare an isolated remote checkout with its own editable environment. The unchanged gate compares both source trees before and after checks; it does not copy files or forward authentication. Remote resource admission remains required. A remote outage must not block independent work already qualified locally.

## Priority review before each work selection

Inspect all open Issues, associated PRs/releases, dependencies, latest maintainer goals, existing review objections, live processes, resource capacity and expected cost. Before changing labels, comment on the affected Issue with evidence, alternative ordering, old → proposed priority and the selected next action. Do not invent agreement or remove unresolved human objections. If priorities stay unchanged, write one concise reason in #49 for that scheduled round; do not repeat it on every Issue or mechanically change labels. Assign exactly one priority, read it back, then select an eligible task. Priorities never bypass dependencies, authorization, reviews or acceptance.


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

The existing heartbeat checks this thread hourly. A continuous authorized goal keeps working between triggers. Report PR outcomes, resolved Issues or blockers requiring maintainer input; do not send minute/hour status messages. Obsidian commits and pushes are paused until explicitly resumed. Before context compaction or handoff, save a short private checkpoint with actual handles, frozen source/environment, verified evidence and next action. Resume by checking actual processes and GitHub, not by trusting a stale checkpoint alone; a text instruction cannot force host context compaction. Scheduling belongs to the maintainer's app/account; cloning the repository does not create a schedule, grant credentials or authorize merges for other users. The host and runtime environment must be available.

This is a verifiable development workflow, not guaranteed unattended scientific discovery; missing hardware measurements cannot be invented. [Issues](https://github.com/huangkiki/Dexlab/issues) track research scope, dependencies and progress. See the delivered [model audit](model-audit.md) and [jitter diagnostics](jitter.md).

[Parameter provenance and research methods](research-focus.md) · [DexLab](../README.en.md)

[Remote qualification and archive protocol](remote-research.md)

The explicit `experiment-24g` profile is available after the measured native-qualification pressure failure: 24 GiB maximum / 23 GiB high memory, with the same two-core CPU quota, 128 tasks, zero swap, I/O limits and finite runtime. The default `experiment` profile remains 16/15 GiB and rejects a 24 GiB override. Both experiment profiles require measured available RAM for their full cap plus 8 GiB desktop reserve before launch and inside the service; larger memory is not permission for concurrent jobs.

[End-to-end delivery and recovery evidence](autonomous-delivery.md)

## Manually audited dependency deliveries

For a phased PR with `Refs`, a manual Issue closure may have no GitHub automatic closing reference. `docs/issue-deliveries.json` is a reviewed list of `issue`, `pr`, full `merge_commit`, and issue-comment `audit_url`. The audit must cover the original acceptance; a partial delivery must not be entered. The first entry records #42 / PR #76; its earlier rigid evidence is retained in the audit.

The selector reads the ledger from fetched `origin/main`, never the working copy or candidate branch. Each entry requires a currently closed issue, the matching merged PR targeting main, an exact merge hash, and commit ancestry in main. Malformed, missing or stale evidence stops dispatch with an actionable error; inspect and correct the reviewed record instead of deleting dependencies. An audit link is a traceability pointer, not an automated semantic proof. Regular closing references and all approval, blocker, recursive-dependency and active-work checks remain unchanged.

This repairs dispatch evidence only; it does not qualify cloth or any new physics. #77 still needs its own bounded acceptance. Unmerged ledger edits intentionally cannot unlock tasks before review/merge.
