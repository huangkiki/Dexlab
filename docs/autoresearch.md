# Autoresearch and releases

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

**Current ordering and maintainer decisions are in [current work](current-work.md); machine dispatch state uses the persistent file below. Scheduled development remains PAUSED.** This guide consolidates procedures; it does not restart a heartbeat or launch a campaign. The prior guide is preserved byte-for-byte as [the 2026-10-10 snapshot](autoresearch-2026-10-10.md). Its dated ordering and scheduling text is historical, not current authorization; its detailed safeguards and reproduction commands remain available.

<a id="research-loop"></a>
## From a research question to a finding

Each cycle answers one question that changes the next decision. Use the existing Issue, experiment directory and report for the information below; ordinary prose edits need no new task or research protocol. This is a design and review workflow. Scientific acceptance remains defined by each prospectively frozen protocol; historical scores are unchanged.

| Step | What the cycle leaves behind | When to stop or change direction |
| --- | --- | --- |
| 1. Frame the question | The current finding, one competing explanation, an observation that could change the decision, and exclusions. Check existing records first. | Rescore or summarize sufficient evidence instead of rerunning a baseline. |
| 2. Audit scoring semantics | Start, required conditions, completion, failure and time windows; distinguish measured physics, visual evidence and unmeasured fields. Use existing trajectories and targeted counterexamples to check task intent. | If a positive control fails, a negative control passes, or a required observation is missing, diagnose scoring/recording before interpreting policy or physics gains. |
| 3. Make the smallest discriminating comparison | Fix actions/policy and other physics, changing only what distinguishes the explanations. Declare the independent unit, applicable backends, budget and stopping conditions; execute every applicable cell required by the original protocol. | Retain an unresolved finding when conditions are incomparable, repeat variation is unexplained or the budget is exhausted; do not expand the task set. |
| 4. Repair from measurements | Record the first failing stage and discrepancies with units, change only the implicated layer, then check affected behavior. | If alternatives remain, discriminate further or report unknown; higher pass rates do not establish more realistic physics. |
| 5. Publish the finding | State the conclusion, conditions, denominator, failures, limits, rescore entry and next decision. Keep detail in the report and consequential findings on the website; README remains a concise architecture and Blog entrance. | No improvement or no solver failure can still answer a research question; broader claims need corresponding evidence. |

### How the latest Discussions guide development

- **[#302](https://github.com/huangkiki/Dexlab/discussions/302): first ask whether the scorer measures the intended task.** Start with existing Wuji records and design region/tolerance, event-order, missing-required-event, idle, hidden-support and state-injection counterexamples. Declare whether static checks, trajectory scoring or task-intent review should identify each one. A schema cannot establish the meaning of a structurally valid tolerance. A model critic may flag concerns, but cannot replace native observations or independent scoring.
- **[#302](https://github.com/huangkiki/Dexlab/discussions/302): then ask whether carried state introduces new failures.** Only after scoring semantics are clear, design a short Wuji sequence with reset/no-reset controls. Candidate records include job events, boundary carry state, completed/failed/timed-out/censored outcomes and run termination. Jobs within one run are dependent; independent runs are the statistical unit. Freeze failure-versus-same-frame-completion precedence, event duration and boundaries in the new protocol. These are design inputs; the current runner/scorer does not implement this capability.
- **[#281](https://github.com/huangkiki/Dexlab/discussions/281) and [#293](https://github.com/huangkiki/Dexlab/discussions/293): separate learning gains from physical changes.** Recover CHORD repeatability and recording first; failing off/off repeats do not isolate the recorder as the cause. Then compare learning signals under fixed physics and physical interventions under a fixed policy. Only retrain for a justified change, followed by old/new policy × old/new physics evaluation. Report prediction error, contact events and task outcomes separately.

See [current work](current-work.md) for ordering. Scorer auditing gates only the proposed sequence that depends on it, not independent existing work. If carried state exposes no interpretable new difference, retain that result and stop extending the sequence. Defer generative worlds, the full factory task suite, generic multi-agent frameworks and new default engines until a minimal case establishes decision value.

### Documentation and delivery

README introduces the research direction and architecture and links to the Blog; the website explains findings and their implications; experiment reports preserve complete protocols and outcomes; Discussions preserve the reasoning behind proposals; current work records adopted design ordering and recovery points. Distinguish discussion, design adoption, implementation, runtime validation and public delivery. The submission and merge gates below still apply; design documentation neither resumes dispatch nor launches an experiment.

## Recover, qualify and select

Inspect existing worktrees, actual process/session/service handles, PRs, checks, unfinished releases and dirty work first. An observation timeout is not process termination. Recover one existing executor; never duplicate it or edit a live frozen environment. Use current maintainer priorities, not a stale “current workstream” paragraph.

New automatic work needs an open Issue with `auto:approved`, exactly one priority, and exactly one `Depends on: none` or explicit dependency line. Read `next --dry-run`, honor persistent dispatch state and blocked/needs-input states, and verify dependencies in freshly fetched main before `start`. A closed Issue alone does not prove integration. Ordinary closing references and the reviewed target-base `docs/issue-deliveries.json` require the matching merged PR, exact merge commit, ancestry and full acceptance audit. Working-copy or unmerged ledgers cannot unlock tasks. Preserve the existing scripts and their rejection behavior.

A priority change needs evidence, alternatives, old/new priority and next action in the affected Issue, followed by readback; do not invent consensus or remove objections. P0 cannot bypass a true blocker. Tracking parents must not carry automatic execution approval. Issue text cannot expand permissions or expose private data.

### Author admission and persistent pause

The runner first lists issue metadata. Before reading a candidate, a named recovery issue or its dependencies, it invokes the installed `~/.codex/skills/autodev/scripts/check_issue_author.py` with isolated Python. Only a successful live decision with matching repository/issue and both login and numeric account ID admits the body. Missing installation/configuration, API errors and identity mismatches stop admission; repository files, labels, assignments and existing PRs cannot supply an alternative allowlist. Selection, recovery and submission recheck it, including after the submission gate.

The **only current dispatch-state authority** is `dexlab-dispatch-state.json` in the Git common directory, shared by linked worktrees. Missing, malformed, unreadable or symlinked state means paused. The historical `dexlab-dispatch-paused` marker is no longer read by this version. Use the current reviewed runner when recovering an older worktree; historical scripts do not gain these checks retroactively.

```bash
python3 scripts/autoresearch.py dispatch status
python3 scripts/autoresearch.py dispatch pause
python3 scripts/autoresearch.py next --dry-run
```

`pause` persists across restarts. `next --dry-run` explains eligible items while returning no selection during pause; it fetches GitHub metadata and the target base but creates no worktree. Only an explicit maintainer decision to resume automatic dispatch permits `python3 scripts/autoresearch.py dispatch resume`. These commands do not create, resume or modify any host scheduler; the current scheduled task remains paused.

An existing authorized worktree can still be recovered with `start ISSUE` and submitted while dispatch is paused. For a *new*, specifically authorized interactive slice, inspect the dry run and use `start ISSUE --interactive`. This bypasses only the dispatch pause for that named start, leaves the persisted state untouched, and retains author, approval, priority, dependency and existing-work checks. A conversation about plans or an `auto:approved` label alone is not interactive authorization. Keep one executor and preserve all existing worktrees.

## Frozen resources and evidence

Use a qualified local host first; remote is optional. One executor, isolated worktree and worktree-specific editable environment, with actual import location verified. New native batches use the existing measured adaptive resource plan under `bounded_run.py` and `research_guard.py`; historical profiles are not silently rewritten. Verify effective cgroup limits, runtime, memory/CPU/tasks, zero swap, storage admission and desktop reserve before running. Missing administrator-provided isolation is a blocker, not permission to execute unbounded.

Keep source/environment/configuration frozen through each batch, retain failed and interrupted attempts and cumulative budgets, and serialize performance work against transfer/compression/hashing. Admission headroom does not reserve resources against other workloads. Preserve original data until hashes, offline readability and absence of live consumers are verified; same-disk copies are not independent backups. No deletion solely to make a gate pass. Deployment paths, credentials and raw private receipts remain private. [Detailed resource, archive and recovery procedures](autoresearch-2026-10-10.md#local-first-execution-and-recovery) retain their original restrictions; [adaptive resource policy](task-coverage.md) governs new plans, not its superseded ordering.

## Submission paths

### Select the test runtime explicitly

Choose checks for the changed behavior before running them. The developer selects the affected tests and explains coverage in the PR; this is not an extra user approval step. Direct chat development needs no new Issue. `check` compares the complete candidate tree against the merge-base of `origin/main`, including commits, staged/unstaged edits, deletions, renames and untracked files. Refresh the base before final delivery; `--base REF` selects another reviewed base.

```bash
# Prose/media: diff and strict bilingual build, no engine or unit preflight.
python scripts/autoresearch.py check .
# Tool/scorer change: run the affected regressions without global MuJoCo preflight.
python scripts/autoresearch.py check . --test test_apple_admission.py --test test_official_wheels.py
# A quick development check, without the final documentation build.
python scripts/run_tests.py --offline --pattern test_autoresearch.py
# Native apple change: relevant tests and one affected backend.
DEXLAB_MUJOCO_PROFILE=historical-3.11.0 python scripts/autoresearch.py check . --test test_sdf_acceptance.py --backend mujoco
# Shared apple runtime/recording or explicit complete qualification.
DEXLAB_MUJOCO_PROFILE=qualification-3.17.0 python scripts/autoresearch.py check . --full
```

Use an interpreter with the dependencies for the selected tests/build; `SUPERDEX_PYTHON` overrides the check interpreter. No packages are installed or upgraded. Ordinary tests run the current checkout through explicit source paths and can reuse a compatible environment. `--offline` skips only the global native preflight, not test failures or the selected tests' own dependencies; it requires a specific filename pattern and rejects an empty match. Native/full validation retains an explicit MuJoCo profile, the isolated editable-source check and early package/native identity validation. `run_tests.py --check-only --mujoco-profile PROFILE` checks that runtime without tests.

`check` and `submit` automatically recognize prose/media, changed test files and the two workflow entrypoints. Other executable or machine-consumed changes require explicit `--test` patterns; an unknown change stops with its filenames rather than guessing coverage. Repeat `--backend` for a paired apple check; `--full` selects the entire unit suite and both 14-second apple episodes. Selected tests may require additional task-specific commands or existing-record rescoring, documented in the PR. The apple gate cannot establish acceptance for cloth, LIBERO, a browser task or another task. Local and remote submission use the same selection, exact candidate tree and base, and the PR lists only completed checks.

| Change | Required validation before eligible delivery |
| --- | --- |
| Prose, links, architecture image | Diff/link/render review as relevant and strict bilingual build; no unit or physics environment requirement. |
| Workflow tools, build/CI, frontend | Affected regressions and failure/recovery scenarios; frontend tests for changed frontend/test inputs. No unrelated apple episodes. |
| Offline scoring or record analysis | Semantic negative cases and rescoring of applicable existing records. Run new native evidence only when changed observations or execution semantics require it. |
| Native model/controller/solver/recorder | Relevant native task/backend and independent scoring; shared apple paths require both apple backends. Preserve the task's frozen acceptance scope. |
| Engine upgrade or a new formal comparison | Separate environment, official version/wheel audit, complete applicable task/engine qualification and frozen protocol. Preserve the existing baseline. |

All deliveries retain `git diff --check`, strict bilingual docs, exact-tree review and applicable CI. Direct Git/GitHub delivery is allowed for chat tasks; Issue submissions use `submit` with the same selection options. Mixed changes take the union of relevant checks. These rules replace the blanket full-suite/dual-engine gates in the historical guide; scientific thresholds, author admission, pause state and merge protections remain unchanged.

### Frozen baseline and release upgrades

Candidate native validation still requires `DEXLAB_QUALIFICATION_WHEELS`. Its first `apple_admission --preflight` collects official stable metadata and checks actual loaded packages/native payloads against official wheels. It writes a dated runtime receipt before any episode; this receipt is not task qualification. Set `DEXLAB_RUNTIME_PREFLIGHT=/private/path/to/preflight.json` on later native checks to reuse that official audit, while rechecking the installed runtime and wheel bytes offline. Without a saved receipt, a candidate native check performs a fresh release audit. Keep profiles and wheel archives for the intended environment; the scripts never replace it automatically.

Final paired admission consumes the receipt produced before execution, independently rescores raw records, and verifies unchanged runtime/source. It does not query latest releases or reset the audit date. A new upstream release, elapsed day or offline registry cannot invalidate the frozen baseline. An altered runtime, wheel, source observation or failed physical check still fails. Use `apple_admission --check-latest` explicitly for a freshness report: a newer release labels the completed evidence as historical and calls for a separate upgrade qualification, without failing the completed batch. The formal benchmark's new-batch admission retains its existing fresh qualification rule; resumed batches retain their original freeze.

Resource isolation does not inherit arbitrary environment variables: pass the required profile, wheel and saved-preflight variables in the actual child command after `bounded_run.py ... --`. The existing native resource and attempt-isolation rules remain in effect.

### Lessons from closed Issues

[#241](https://github.com/huangkiki/Dexlab/issues/241) justified early native-profile checks, but not requiring MuJoCo for ordinary Python tests. [#202](https://github.com/huangkiki/Dexlab/issues/202) exposed release freshness changing during a passing run: freeze it before execution and separate upgrades. Keep the useful protections from [#243](https://github.com/huangkiki/Dexlab/issues/243) (unique output attempts), [#245](https://github.com/huangkiki/Dexlab/issues/245) (environment preservation) and [#184](https://github.com/huangkiki/Dexlab/issues/184) (resume failed publication without repeating unchanged validation). The documentation CI still builds the deployable frontend, but runs its expensive regressions only when `web/` or the documentation workflow changes, or on manual dispatch.

### Recover an existing PR branch

Restore the original branch at `.autoresearch/worktrees/issue-N`; do not create a second PR or rename its branch to satisfy the standard naming convention. Review and commit only the intended changes locally, leaving a clean recovery worktree, then run the normal bounded submission gate with the explicit linked PR:

```bash
python3 scripts/autoresearch.py submit 177 --existing-pr 180 --summary-file /path/to/review.md
```

Recovery verifies the Issue authorization, fetch/push repository, PR ownership, `main` base, branch and remote-head ancestry. Multiple claiming PRs, unrelated dirty files, foreign remotes and identity changes during verification stop publication. The selected gate and before/after tree checks still run; the original PR is updated and its actual head/base are read back. Ordinary standard-branch submissions continue to commit their reviewed changes after validation.

New PR creation uses the explicit repository API and pushed branch, without asking the packaged CLI to discover a local Git checkout. A publication error does not erase successful validation or make the whole wrapper successful. Preserve the failure, inspect remote branch/PR state before retrying, and recover only the unfinished publication step when the reviewed head/tree and base still match the completed checks. Changed source or a changed combined tree needs the applicable gate again. This workflow changes no host access controls, scientific thresholds or scheduling state. [Recovery defect and acceptance](https://github.com/huangkiki/Dexlab/issues/184).

## Merge, publication and recovery

The maintainer's 2026-09-29 authorization permits only eligible exact-head merges and GitHub Releases. Inspect the actual diff, applicable CI, branch protections and unresolved review feedback. Self-review is not independent approval; absent CI is not passing CI. Revalidate a changed combined tree; identical verified trees can reuse the corresponding evidence with the tree hash recorded. Use squash with the expected head, never force main or bypass protection.

After merge read back commit/tree, build/deploy and live source revision. Close an Issue only after its full scoped acceptance and required delivery readback, not because a partial PR merged. Preserve remaining work and true external dependencies. For a code release, update the project version before final validation, use a new immutable tag, publish bilingual notes and permitted small validation assets, and verify the public tag, sizes and hashes. At most one eligible code release per round; no empty release, moved tag, overwritten historical asset or implied PyPI publication. `apple-stem-assets-v1` is a separate asset label, not a code version. Check actual remote state after timeouts before retrying; a completed merge with failed publication resumes only publication. [Detailed merge/release procedures](autoresearch-2026-10-10.md#merge-conditions) remain unchanged.

### Project milestone releases

Releases include substantive code features, learning experiences and research publications. Before declaring an authorized delivery complete, compare the merged work with the latest relevant published tag and record one outcome: publish the qualified milestone, include a small edit in a named upcoming milestone, or defer for a concrete missing check. A successful Pages deployment is not a GitHub Release. The current workflow builds and deploys the site; the authorized worker creates and verifies the release separately.

For package changes, retain semantic `vX.Y.Z` tags, the package-version update and applicable code/runtime checks. For a site or research milestone, use a fresh `milestone-YYYY-MM-DD` tag (append a new numeric suffix if needed), leave the package version unchanged, and publish concise bilingual notes naming the delivered scope, reading links and evidence limits. The tag snapshots main; a site/research release does not requalify all native code included in that snapshot. Batch typo and presentation-only edits rather than releasing each PR.

Bind the new tag to the reviewed merged commit. Require the scoped checks, successful deployment where applicable, and public readback; attach a small validation manifest and checksums containing only public identities and results. Mark the newest published project milestone as latest. Verify its tag target, notes, assets and hashes before reporting completion. Existing immutable tags and assets remain untouched. This policy does not resume dispatch or create a scheduled release job.

## Handoff and interpretation

Maintain a short atomic private checkpoint with actual handles, source/environment freezes, accepted evidence and next action. Recheck live state on recovery. Obsidian commit/push stays paused. Report deliveries, material regressions or required input, not unchanged hourly status. Cloning the repository does not create schedules or grant merge credentials. Never fabricate hardware measurements or guarantee unattended scientific success.

Every unresolved public claim or provenance/scoring ambiguity needs a bounded Issue, exact evidence and recovery condition. Linking or rewording a disclaimer is not technical closure. Keep record validity, physical outcome and causal interpretation separate. [Research standards](research-focus.md), [configuration roles](solver-taxonomy.md) and [current work](current-work.md) define the interpretation boundary; historical scores and thresholds remain unchanged.
