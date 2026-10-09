# UniSim contact-path migration

[English](unisim-contact-migration.md) | [简体中文](unisim-contact-migration.zh-CN.md)

The maintainer selected UniSim as the owner of scene import, native stepping/reset and engine state/contact translation. DexLab owns experiment protocols, control inputs, recording, recoverable campaign budgets, independent scoring and evidence. [Discussion #129](https://github.com/huangkiki/Dexlab/discussions/129#discussioncomment-18830621) records the decision; [#142](https://github.com/huangkiki/Dexlab/issues/142) tracks all applicable production paths and [#143](https://github.com/huangkiki/Dexlab/issues/143) executes the first migration. Native B [#132](https://github.com/huangkiki/Dexlab/issues/132) changes are preserved as references; its protocol/accounting work remains reusable.

## First path and proof

The first target is the existing finite Genesis primitive pinch/hold/release entry point, `dexlab.genesis_pinch_probe`, with its independent `genesis_pinch_score`. This already has a native implementation and previous isolated adapter comparison, permitting direct before/after verification. Historical candidate results are evidence for their own frozen version only; the new public interface, current UniSim revision and actual production switch require fresh checks. The new external-PD campaign stays a separate protocol and will consume the qualified interfaces later.

Retain the native source and frozen protocol by Git revision for reproducible reference execution. Only after comparison passes may the production entry point switch to UniSim and remove its native scene/lifecycle/observation code. The reference is explicitly selected; there is no silent runtime fallback. Preserve CLI/control/output behavior and every physical failure. Shared experiment logic must not migrate into UniSim.

Before qualification, freeze the exact native/adapter source trees, official runtime identities, model files, controller, cases, acceptance and output schema. Compare all 16 existing `force-limit-v1` cases on both paths at 0.5 ms, plus the default pinch and open control with two reset replays at each of the three supported timesteps. This is 38 base process launches and 56 four-second episodes. The original three candidates used one executor, at most 48 launches and 90 minutes total process wall time, at most 15 minutes per process; this development migration budget is separate from the new campaign's 6 h / 700 launches. Keep all attempts, reject startup without remaining budget and retain incomplete coverage as incomplete. Do not execute this comparison until source/runtime admission and the frozen manifest exist.

Keep initial numeric agreement at 1e-12 and trajectory state agreement at 1e-9; contact force agreement remains 1e-7 N. Independently retain the existing 1e-8 N contact ledger check, 1 mm penetration budget, 5% weight-normalized momentum residual and original hold/release tests. These thresholds have different purposes. Require matching scientific pass/fail outcomes, not successful grasp in every case. Compare complete contact identity, point, normal, depth, forces and epochs, permit contact-slot permutation only after matching physical identities, and reject missing/duplicated records. The only currently reviewed representation difference is batched link/DOF storage; report it explicitly.

## Capability work and six-engine scope

| Engine | This migration | Evidence needed to advance |
|---|---|---|
| Genesis | Fixed-model path integrated under #143 | 19/19 storage-aligned pairs pass; production integration and delivery checks below |
| MuJoCo | Not migrated by this first slice | Native contact solve epoch, effective configuration and current official-runtime compatibility through UniSim |
| SuperDex | Not migrated by this first slice | Qualify official runtime against UniSim binding requirements and complete contact readback |
| Newton Physics | Not migrated by this first slice | Same-scene state/control/contact qualification |
| PhysX | Not migrated by this first slice | Public worker/native version identity, contact and solver observability |
| Drake | Not migrated by this first slice | Positive-duration task qualification, then common interface comparison |

Missing capabilities become adapter work with bounded evidence/acceptance in #143 or follow-up Issues under #142. They do not justify a parallel DexLab production adapter. UniSim capability declarations, fake-runtime tests and successful imports are not physical equivalence. Unavailable native observations remain missing; command values cannot substitute for measurements. The first slice does not close #142, the six-engine research parent #130, or related incline #121.

## Delivery

UniSim changes must pass its lint/type/contract/package gates and remain reviewable without claiming upstream merge or release permission. DexLab delivery uses the existing `submit`, full regression, both complete 14-second checks, bilingual build and exact-head review. Return qualification and report decisions to Discussion #129 and link concrete follow-ups. README reports actual migration and evidence only after verification; unfinished work links directly to Issues.

## Frozen comparison and recovery

`scripts/run_contact_migration.py` provides `freeze`, `run`, `status` and `check` for this bounded migration. It reuses `bounded_run.py` and `research_guard.py`. Use the isolated candidate Python environment; freeze copies both source trees, records their base revisions and file hashes, generates the exact portable models, verifies installed engine code against admitted official-wheel receipts, and records dependency/runtime identities. Local worktree paths in the private manifest are execution inputs, not public report content.

Each run names one of the 38 frozen launch identities. An append-only hash-linked ledger reserves the full 900-second process allowance before launch. Recovery preserves all reservations and attempts; a live or unverified process blocks new dispatch. Only a terminal bounded-run receipt and inactive service release a reservation. A failed infrastructure/recording attempt may receive one explicitly justified retry, within the frozen allowance (48 starts / 5,400 seconds for the historical candidates). Recorded physical outcomes never retry to success. Damaged history, changed source/runtime/model identities or exhausted allowance stop execution instead of recreating the budget.

A corrected implementation requires a new frozen source revision, not altered records. `freeze --previous-comparison` retires dispatch on the old candidate and inherits its complete launch/wall accounting, binding the predecessor manifest and ledger head. Previous physical failures remain results of the previous candidate. Start the controller with Python `-I` so external shell Python paths cannot contaminate the admitted dependency inventory.

Offline `check` verifies sealed evidence, source/case identity, each state and contact epoch, complete contacts matched by geometry/position, independent scientific scoring and exact reset replay. It reports coverage and physical agreement separately; final acceptance additionally requires `--verify-runtime` to repeat the installed-code byte check. A missing case yields an incomplete report. The original public force-limit scorer retains its acquisition-source check; the migration checker binds both explicitly reviewed recording sources before calling the same independent scoring logic.

The first candidate passed UniSim lint/type/package gates, 1,631 baseline tests (141 skipped), and 110 real Genesis 1.4.3 tests (16 skipped). Its first complete 1 ms comparison failed: reset replay was exact on both paths, but native contact forces differed from the second step. The factory silently overwrote the consumer's unprefixed `friction_cone` keyword, selecting pyramidal friction instead of elliptic. The corrected candidate uses `genesis_friction_cone`, checks the effective enum name before recording and rejects silently overwritten factory options. The native reference now preserves requested options separately from solver-effective options. No trajectory tolerance changed. A fresh frozen comparison and production switch remain required under [#143](https://github.com/huangkiki/Dexlab/issues/143); the two failed-comparison launches and all earlier development attempts are retained.

The second frozen candidate passed both 1 ms and 0.5 ms comparisons, then failed full contact-position matching at 0.25 ms from 0.52475 s; task scores and exact reset replay still passed. Native and implicit MJCF cube inertia differed by one FP64 ULP. A materialization-only diagnostic also found that explicit inertia was rounded to six significant digits by the intermediate compiled XML writer. The correction authors mass and inertia using the native primitive analytic operation order and restores explicit inertials at full precision during UniSim export. Native readback now exactly matches the reference mass/inertia; this is not yet proof of trajectory equivalence. All six second-version launches, the first-version failure and their cumulative cost remain preserved. A third frozen candidate must pass the original contact/state/force thresholds and complete matrix before production migration.

## Third frozen comparison: complete evidence, failed qualification

The [machine-readable summary](evidence/unisim-contact-migration/comparison-v3-summary.json) binds manifest `ac88593f973b2cab4bd0adb1d203618dbcb1874e71344b79e450b1db8153f052` and the final checker output. All 38 launches / 56 episodes were recorded; sealed evidence, full coverage and installed runtime bytes passed verification. Of 19 paired comparisons, 13 passed and six failed: 0.2 N and 0.4 N at each of the center, left and right initial positions. Default pinch/open comparisons at all three timesteps had zero state, command, net-force and contact differences; all 12 reset replay checks passed.

Original scientific pass/fail classifications matched throughout, including failed hold at low force. This does not replace pointwise migration acceptance. The center 0.2 N case developed state/contact disagreements around 1.63 s, with maximum net-force difference about 0.0008665 N. Contact maxima in detailed reports include only successfully matched contacts. At that stage, threading, batched parameter storage, native N=0 versus adapter N=1 lifecycle and independent-process repeatability were unresolved factors under [#143](https://github.com/huangkiki/Dexlab/issues/143#issuecomment-6080931836). Separately, repeated floating-point clock addition shifted membership at the exact 2 s scoring boundary; a subsequent clock fix requires its own version and validation, and is not an explanation for physical differences.

Across all three candidates, 46 launches used 896.5872933129431 s of complete process wall time. Those costs and failures remain immutable. The maintainer subsequently approved an additional six-hour / 64-start development work package under the [coverage-first plan](task-coverage.md), recorded in [#143](https://github.com/huangkiki/Dexlab/issues/143#issuecomment-6081934903). The append-only ledger retains lifetime totals; a source revision inherits its package allowance, while a new package needs new evidence and a concrete hypothesis. Old package IDs, dropped package declarations and changed limits cannot restart the allowance. Unknown interrupted cost charges the full reservation. The new external-PD campaign's 6 h / 700 starts remain unused. At that checkpoint production remained native; no UniSim upstream release is claimed. This summary does not distribute the private full raw archive; its hashes identify retained evidence, not a public download.

## Current capability boundary

[The development Project](https://github.com/users/huangkiki/projects/4) tracks the accepted Issues and actual delivery states; it does not launch experiments. The Genesis 1.4.3 candidate preserves native default inertia alignment. Body mass and COM reset mutations are not admitted for this version: native aligned-root write restrictions and the coordinate effects of changing alignment require separate qualification in [#145](https://github.com/huangkiki/Dexlab/issues/145). The pinned 1.3.3 behavior remains separate. The fixed-model pinch comparison does not require inertial randomization.

The inertial correction passed the full UniSim baseline (1,638 passed / 141 skipped), Ruff/mypy/Pyright (0 errors, 175 optional-dependency warnings), wheel/sdist packaging and real Genesis 1.4.3 suite (112 passed / 16 skipped). DexLab migration/evidence/budget tests (23) and existing force-protocol tests (7) passed. Checks also caught and corrected root poses being applied twice after XML recompilation; the existing source-snapshot export semantics are retained and only explicit inertial fields restored, with multi-entity pose/sensor regression coverage passing again.

After freezing and completing v3, the local candidate clock was changed to restored origin plus integer host ticks. Eight regression cases first reproduced the old drift and then passed at all three timesteps in FP32/FP64, including selected reset, playback and tensor-to-host rebasing. The updated candidate passed 1,646 baseline tests (141 skipped), 120 real Genesis suite tests (16 skipped), lint/types/package gates and the same 30 DexLab focused tests. These checks do not retroactively qualify v3 or resolve its low-force discrepancies; the subsequent v4 comparison below validates this clock change.

## Native isolation and the storage-aligned protocol

[The 24-process isolation result](evidence/unisim-contact-migration/native-isolation-v1-summary.json) tests only development case `dev-cap-0.2`: 1/2 Quadrants threads × link/DOF parameter storage off/on × 0/1/2 native environments × two fresh-process repeats, at 0.5 ms for 4 s. Official Genesis 1.4.3 / Quadrants 1.3.3 code was reverified. All 32 recorded worlds retain the expected low-force hold failure and pass the existing numerical/physical-validity checks. The package used 361.494566 s; per-process aggregate peak was 1.457 GiB under the frozen 16 GiB / 4-core envelope, with no OOM.

Thread count, environment count and fresh-process repetition produced zero observed differences within each storage profile. Enabling both `batch_links_info` and `batch_dofs_info` alone reproduces the previous discrepancy: maximum net-force difference `0.0008664952219903156 N`, angular-velocity difference `0.0003385957228926784 rad/s`, and first contact-position mismatch at 1.63 s. This isolates the combined storage factor, not the exact compiler operation or either flag individually. The eight storage-changing baseline comparisons fail the original pointwise gate; all 16 fresh-repeat world pairs and eight within-process world comparisons pass with zero differences. None of these repeats adds a task type.

The batched native record also passes the unchanged migration gate against the retained third-version adapter record: commands, position, velocity, net force and every matched contact agree exactly; quaternion and angular-velocity differences are at most `1.11e-16` and `2.71e-20`. Thus this development discrepancy can occur without the adapter. It is not evidence that arbitrary framework paths are equivalent.

The fourth comparison froze two explicit layers: retain the original unbatched-native versus batched-native diagnostic as a numerical configuration difference; compare **storage-aligned native versus adapter** with the original 1e-12 initial / 1e-9 state / 1e-7 N force bounds, unchanged physical scoring, all 16 force cases and all reset/timestep controls. Effective storage flags must now agree on both paths. Native `--batched-info` is explicit; omitting it retains the historical reference. #145 remains separate from this fixed-model qualification.

The [frozen diagnostic acquisition source](evidence/unisim-contact-migration/native-isolation-v1-runner.py) reproduces each matrix cell, for example:

```bash
python docs/evidence/unisim-contact-migration/native-isolation-v1-runner.py OUTPUT \
  --source-root . --case-id dev-cap-0.2 --num-threads 1 --batch-info on --n-envs 0
```

Use the admitted environment and existing bounded runner. Vary the declared factors and retain each output in a fresh directory. Full raw diagnostic records and the sealed manifest remain in the private archive; the public summary identifies their hashes and is not a raw-data download.

For the new full comparison, `freeze --previous-comparison PREDECESSOR` inherits that work package automatically; `--work-package FILE` starts an evidenced successor package. `--peak-receipt RECEIPT` copies and hashes a measured receipt, and each new batch freezes its adaptive plan. `--native-storage matched` is the new freeze default; `historical` reproduces the former comparison convention. These changes do not alter old manifests, failures or the formal 6 h / 700-start campaign.

## Fourth comparison: all 19 pairs pass

The [v4 summary](evidence/unisim-contact-migration/comparison-v4-summary.json) binds manifest `474de44f8900cb9ba0210434e8da37f9f9405bdf8f35508a804ad725ed2ee854`. All 38 launches / 56 episodes, all 19 pairs, all 12 exact reset replays, sealed records and runtime byte checks pass. Initial configuration, commands, positions, velocities, net forces and complete contact observations agree exactly. The remaining quaternion/angular-velocity differences are rounding scale within the original bounds. Scientific checks and exact first-failure times agree, including the six failed low-force holds at 2.0 s. Matching failure is a successful path comparison, not a successful grasp.

The four-second comparison cost was 637.493444 s of complete process wall time with a 1.566 GiB peak under a frozen 8 GiB / 4-core envelope. Including native isolation, the development package has used 62 of 64 starts / 998.988010 s; lifetime accounting is 108 starts / 1895.575303 s. Full-process costs include imports, instrumentation and writing, and are not physics throughput. The formal 6 h / 700-start campaign remains unused. The original unbatched results are not relabeled.

The production entry point now directly contains the qualified public-interface acquisition; the temporary `unisim_pinch_probe` module is removed. Native lifecycle/scene/contact code is retained only in `scripts/references/genesis_pinch_native.py`, selected explicitly. `MODEL`, case lookup, CLI arguments and the independent scientific scorer remain available at the existing entry point. Storage options must be read back as enabled before acquisition; an unpatched backend fails with the required dependency rather than silently falling back. Integration verification and final delivery gates are tracked in #143.

## Reproduce the disclosed development combination

This is a local adapter contribution based on UniSim `91470d714531894db5f645b48982bee91d441eb9` (package 1.7.12), with official Genesis 1.4.3, Quadrants 1.3.3, MuJoCo 3.15.0, NumPy 2.5.2, SciPy 1.18.1 and Torch 2.9.1+cpu on Python 3.12.12. It is **not** the upstream official Genesis extra: that release still specifies Genesis 1.3.3 and MuJoCo 3.11. Official-compatible framework admission remains a separate track. Do not install this patch into an existing frozen PhysX or other experiment environment.

The [complete adapter patch](../scripts/patches/unisim-1.7.12-contact-readback.patch), including new source, tests and bilingual contract documentation, has SHA-256 `85354840a47f3fac0ee19450006b5d5c61621261a027d780a40d995521e29ef3`. No engine implementation is patched. In a fresh source checkout and isolated environment with the listed official runtime versions:

```bash
git clone https://github.com/unilabsim/unisim.git "$CONTACT_SOURCE"
git -C "$CONTACT_SOURCE" checkout --detach 91470d714531894db5f645b48982bee91d441eb9
git -C "$CONTACT_SOURCE" apply --check "$DEXLAB_ROOT/scripts/patches/unisim-1.7.12-contact-readback.patch"
git -C "$CONTACT_SOURCE" apply "$DEXLAB_ROOT/scripts/patches/unisim-1.7.12-contact-readback.patch"
uv pip install --python "$CONTACT_PYTHON" --no-deps -e "$CONTACT_SOURCE" -e "$DEXLAB_ROOT"
uv pip check --python "$CONTACT_PYTHON"
"$CONTACT_PYTHON" -m dexlab.genesis_pinch_probe NEW_OUTPUT --dt 0.0005 --case-id dev-cap-0.2
"$CONTACT_PYTHON" -m dexlab.genesis_pinch_score NEW_OUTPUT
```

Choose fresh mounted-data paths for the variables and use the existing bounded runner for simulation. The example deliberately retains the failed low-force hold. The dependency range permits the disclosed 1.7.12 candidate while legacy constraints keep 1.7.10; installing the released wheel alone does not provide this unreleased capability. The [frozen v4 recorder](evidence/unisim-contact-migration/recording-v4.py) preserves the acquisition source used for the full comparison. Private archived source trees and raw records allow exact historical rescoring; the current checker refuses a different frozen scoring implementation. No upstream merge, release, general scene equivalence, additional reliable task type or #145 inertial mutation is claimed.

## Production integration verification

The [integration summary](evidence/unisim-contact-migration/production-integration-v1-summary.json) records two additional production launches: the 0.25 ms reset/replay controls and the right-offset 0.2 N case. They pass the same complete-contact/state comparison against sealed v4 native records and the existing public scorer, retaining the low-force hold failure. The full 38-launch qualification was not rerun: model construction, commands and per-step acquisition are structurally identical to the qualified candidate; only protocol metadata, utility placement and pre-acquisition checks changed. All initial/model/record hashes and installed runtime bytes were rechecked.

The package finishes at 64/64 launches and 1079.143235 s, with lifetime totals of 110 launches / 1975.730528 s. Further diagnostic packages require a new hypothesis and new evidence; this successful integration does not authorize repeated identical acquisitions. All prior source snapshots, failures and accounting remain retained.

Final adapter checks on the disclosed patch passed: Ruff, mypy, Pyright (0 errors, 175 optional-SDK warnings), 1,646 baseline tests (141 skipped), 120 real Genesis 1.4.3 tests (16 skipped), and wheel/sdist builds. The updated comparison also rejects identical-but-physically-invalid trajectories and differing exact failure times; missing force data or equal bad physics cannot qualify a path.

[Additional sealed-record scoring](evidence/unisim-contact-migration/physical-recheck-v1-summary.json) passed all 21 pairs (19 qualification + 2 integration), enforcing physical validity and exact first-failure times. No new simulation was run and no historical verdict was rewritten.
