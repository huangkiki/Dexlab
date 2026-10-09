# Task coverage and continuous development

[English](task-coverage.md) | [简体中文](task-coverage.zh-CN.md)

**We value an engine that reliably completes more types of tasks.** Each task may use its appropriate solver and parameters. Physical error, stability and cost remain visible alongside coverage. Repeats, timestep scans and another framework do not create new task types.

## One inventory, four generated views

`docs/task-coverage.json` is the versioned inventory. Run `python scripts/task_coverage.py` after updating evidence; `--check` rejects stale README/site tables and is part of the strict bilingual build. Fixed task IDs distinguish passive folded drop, robot cloth grasp/lift and active folding. Every row identifies core, solver, runtime path, version and cohort, and accounts for every task. Tables split columns for readability, not to change the denominator.

Every cell links to its original report (including commands and raw-data entry points) or a recovery Issue. Observed results and unsupported claims require a repository evidence file and SHA-256. Historical cloth counts are recomputed from all 105 frozen summaries: duplicate, missing or contradictory records fail validation. This is an inventory audit, not independent trajectory rescoring. Historical missing readbacks stay missing; documentation changes do not fill them.

Historical cohorts are displayed separately and never enter the new `coverage-v1` reliable total. That protocol is an acceptance contract, not a claim that a campaign has run. Before a new comparison, freeze development/holdout cases and an equal tuning budget. A qualified cell requires a hashed independent acceptance report identifying the exact protocol, task, engine, solver, runtime path and version, and true checks for positive cases, negative controls, independent physics, frozen holdout, equal tuning budget and provenance. Attach underlying protocol, raw records, scores, resource receipt and deployed evidence links before admission. The generator validates the report contract; reviewers still verify its evidence. Only then does the engine total take the **union of task IDs** across qualified configurations. Failed, partial, blocked, unsupported and unrun cells do not count. No configurations have yet been admitted under this new contract.

## Execution order (maintainer decision, 2026-10-09)

1. Deliver #119's inventory, bilingual presentation and resource/recovery rules.
2. Resume #143: isolate threads, batch storage, environment count and independent-process repeatability. Keep #145 inertia/frame changes separate. Preserve failed cohorts. Check effective parameters, commands, epochs and precision before numerical attribution. If native repeatability itself diverges, develop and freeze a new acceptance protocol using development diagnostics, then test untouched holdouts. Repeatability error never justifies unlimited physical tolerance.
3. Complete #117 and independent engine slices of #121. Drake qualification must not block other engines. Applicable registered solvers need measured results or sourced unsupported reasons.
4. Compare native MJWarp with Isaac Sim integration on incline, collision and pinch: original asset/default import versus explicit parameter alignment. Save input assets, intermediate models, final effective parameters and conversion provenance using existing configuration/contact readback. Audit inertia, drives, friction, geometry, contact generation and capacity. Native paths use the latest stable core; framework paths use official compatible combinations. Match core versions in attribution experiments; otherwise do not attribute all differences to the framework.
5. Requalify #47 under that dual-version policy, then expand pushing, grasping, #48 rotation and #28 cloth. After each newly delivered task type, advance one #132 → #133 → #134 pinch slice. Preserve the 594-case research campaign and 24 controls.

#124–#126 need a bounded historical search and acceptance reconciliation. Irrecoverable telemetry remains explicitly absent; newly qualified runs can replace evidence used for current claims, never impersonate historical observations. Close only the reconciled scope or a reviewed withdrawal, retaining any residual follow-up. #6 remains dependent on real hardware data; finish collection/scoring preparation and continue independent simulation work.

## Resources and recovery

Historical `experiment` (16 GiB / 2 cores) and `experiment-24g` remain reproducible. New batches use `bounded_run.py --profile adaptive --resource-plan BATCH.json`: unknown load starts at 16 GiB, `--complex-model` at 24 GiB. With `--peak-receipt PREVIOUS.json`, choose the smallest 8/16/24/32/40 GiB tier at least 1.5 times measured peak. Each launch separately requires its whole cap plus 8 GiB available RAM, zero swap and the existing free-disk/I/O admission. CPU starts at 4 core equivalents; `--cpu-cores 8` requires a diagnosed CPU bottleneck. Reuse identical plan arguments throughout a batch; changed resources require a new batch plan. Never overwrite receipts or a frozen plan.

Receipts include memory peaks/events, CPU throttling counters, memory/CPU/I/O pressure and sampled GPU memory. Missing GPU/PSI telemetry is null, not zero. GPU samples are whole-device observations every ~10 seconds, not per-process allocation or exact peaks. Whole-service cost includes monitoring and is not isolated solver throughput. Existing read/write caps remain; review stalls before changing them. Correctness may use at most two independent processes after isolation validation. Performance measurements remain exclusive, including transfers and large hashing.

Development uses append-only six-hour work packages. The next #143 package permits 64 starts, retaining the old 46-start ledger and failed outcomes. A new package requires new evidence, a concrete hypothesis, frozen diagnostic cases and a fresh ledger; no repeated approval for an obsolete 48-start limit. Formal 6 h / 700-start accounting remains separate. Recover interrupted work from actual processes, source identity and receipts; an incomplete receipt is not success.

Keep one development executor. Resume work, solve actionable blockers, implement, independently verify, merge and verify the published revision, then update coverage and continue. The existing hourly heartbeat only recovers the loop, notifying on delivery, important failure or required external input. It does not authorize duplicate workers or repeat trials without new evidence.
