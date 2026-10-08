# UniSim reuse: standard-block admission boundary

Decision: retain native production scene ownership. The isolated FP64 candidate now passes the bounded primitive comparison below, but no production duplication has been removed and complete independent contact evidence still needs native access. This qualifies one candidate experiment, not the published adapter or SDF integration.

## Historical published-adapter rejection

The following audit describes the unchanged published adapter before the isolated candidate patch. Its rejection is retained rather than retroactively relabeled as success.

## Evidence

The inspected UniSim 1.7.10 source is commit `dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d`. Its unchanged loader requires Genesis 1.3.3 and rejects installed official Genesis 1.4.3 before a scene is built. An isolated diagnostic then called the unchanged materialization initializer directly with explicit native modules. This deliberately bypasses the already-failed loader **only to inspect initialization**, not to admit the backend.

Actual readback: native float dtype `torch.float32`; adapter tensor cache `torch.float32`; NumPy cache `float32`. No scene or physics step was executed. The native engine was not patched, and no dependency gate was modified. The diagnosis is stronger than noticing an empty float32 placeholder: the actual session and allocated cache use FP32.

## Task-specific contract audit

| Existing standard-block requirement | Inspected adapter behavior | Consequence |
|---|---|---|
| Official Genesis 1.4.3 | Exact 1.3.3 loader | Published route rejects before scene construction |
| CPU FP64, deterministic seed 0 | Initializer omits precision/seed; auto-selects GPU when available | Does not preserve frozen initialization |
| Full-precision position targets | `step` casts controls to NumPy float32 | Changing initialization alone is insufficient |
| FP64 measured state/contact records | `_make_device_cache` allocates torch.float32 | Output precision needs separate qualification |
| dt, gravity, elliptic friction cone | Explicit scene-builder options exist | Source support, not measured equivalence |
| noslip=0 and task-specific contact time constants | Public scene-builder options do not expose noslip; task-specific native settings still need tracing | No assertion that default solver parameters match |
| Bilateral full-rate forces and penetration | Portable exact-pair force aggregation exists; no penetration field found in this backend | Aggregated force is not the complete independent evidence ledger |
| Fresh-process repeat and scene reset | Session lifetime guard and reset methods exist | Actual reset/contact-state equivalence remains unmeasured |

Source anchors: `src/unisim/backend/genesis/dependencies.py::load_genesis_dependencies`, `materialization.py::init_genesis_session` and `build_genesis_scene`, `backend.py::_make_device_cache`, `step`, `_read_portable_contact`, `reset`. These findings concern the inspected source, not every possible adapter version.

## Reuse benefit and remaining work

Demonstrated task code removed: **0 lines**; migrated task paths: **0**. These are achieved-change counts, not an estimated saving or proof that the adapter is universally useless. Reusing the wrapper currently adds compatibility/precision/observation work before any measured reduction. The 163-line native runner remains the owner; the independent scorer and recording contract must remain regardless of route. No claim that all 163 lines are irreducible.

Do not run an FP32 replacement and call it qualification of the FP64 protocol. Any compatibility candidate must explicitly preserve runtime selection, initialization, control/cache precision, full native contact evidence, actual parameter readbacks and reset behavior. Only then freeze and execute a paired contact experiment, quantify removed duplication and validate any migrated SDF path through the existing full gates. The candidate result below supplies the paired experiment; it does not demonstrate production code reduction. It does not relax #47's separate native PhysX restriction or #6's hardware-data requirement.

## Cost and limits

Recovery installation completed in 5.867 s, and the isolated initialization/cache diagnostic in 11.849 s under a measured 24 GiB memory / two-core CPU / 128-task cgroup, swap disabled. Earlier interrupted installation failures remain preserved separately; these two durations are not total historical project cost. No timing comparison, task success or hardware-fidelity claim follows from initialization. The installed Torch CPU distribution avoids unrelated CUDA downloads for this CPU diagnostic.

## Reproduce the diagnostic

[Machine-readable readback and module hashes](evidence/unisim-reuse/reproducible-boundary.json) bind the diagnosis to the installed source and package versions. In a qualified isolated environment with the inspected source installed, run `python scripts/probe_unisim_genesis_boundary.py NEW_OUTPUT.json --initialize` under the documented bounded resource wrapper. It refuses to overwrite evidence; `loader.accepted=false` remains a rejection even when the diagnostic process exits successfully. It deliberately uses an adapter-private cache helper, so future API changes may invalidate this diagnostic rather than establish compatibility.

The reproducible second diagnostic completed in 4.252 s and confirmed the same dtypes. Static AST inspection counted 52 explicit float32 attribute references in backend.py and 19 in materialization.py. Counts include paths not exercised here; they are scope indicators, not 71 proven runtime faults or an edit prescription. A qualified precision patch requires path-by-path review and shared-helper checks, not blind replacement of these references. No compatibility patch was applied in that historical diagnostic.

## Candidate scope

An isolated, uncommitted FP64 adapter candidate now preserves task control and contact-force cache precision in focused tests. Existing import, parameter, nonzero-state reset and short contact admissions are retained; these do not establish paired task equivalence. The completed four-trial fixed-control comparison is reported below. Production scene ownership remains native pending runtime comparison and measured engineering benefit. Generic multi-environment candidate tests currently fail its explicit single-environment restriction.

## Fixed-control candidate result

Four candidate trials (pinch and open negative, each with reset replay) completed 32,000 steps. Independent comparison passed the frozen numerical thresholds: maximum position difference 1.773e-14 m, velocity difference 1.649e-12 m/s and net contact-force difference 2.012e-9 N. Public state and pair-force readbacks matched the native ledger exactly in these records. All four also passed the existing penetration, momentum, hold/negative and release checks. [Comparison](evidence/unisim-reuse/paired-score.json), [physical checks](evidence/unisim-reuse/physical-score.json).

This is an isolated patched single-environment candidate, not qualification of the published adapter. Strict option identity first failed; a native zero-step audit identified resolved defaults and two explicit batched-storage changes. The subsequent representation trial retains those differences and unchanged numerical tolerances. Original failures remain evidence. Native historical traces were reused, with one open-negative reference shared across two candidate repeats. No hardware accuracy or cross-machine performance claim follows. Production task paths migrated: 0; production duplication removed: 0. Native contact access remains necessary for penetration and full force-ledger scoring, so production ownership remains native pending a demonstrated maintenance benefit.

## Reproduction materials

The [candidate patch](evidence/unisim-reuse/unisim-fp64-candidate.patch.gz) applies to UniSim commit `dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d`; [provenance](evidence/unisim-reuse/candidate-provenance.json) binds its hash. It changes Python adapter code only. Decompress with `gzip -dc unisim-fp64-candidate.patch.gz` and pipe to `git apply` in an isolated checkout, then select that checkout's `src` using `PYTHONPATH`. Keep the official Genesis 1.4.3, Quadrants 1.3.3 and MuJoCo 3.15.0 qualification separate from this patch.

Under the documented resource wrapper, run `scripts/run_unisim_pinch.py NEW_OUTPUT --reference docs/evidence/unisim-reuse/reference.json`. The [reference](evidence/unisim-reuse/reference.json) preserves historical options and separately audited resolved options. `scripts/score_unisim_pinch.py NEW_OUTPUT NATIVE_CAMPAIGN_ROOT NEW_SCORE.json` checks source trace hashes before comparison. The native campaign root must contain the three original Issue90 attempt directories; the small JSON reference alone cannot substitute for raw trajectories. Reset observations are measured before new controls; subsequent steps replay commands, never saved states.

The run took 52.908 seconds including process overhead (47.761 seconds after imports), under a 24 GiB/two-core/128-task cgroup with swap disabled. These are instrumented costs, not a speed comparison with historical native runs. Earlier admissions, installation and failed attempts are not included. Generic multi-environment tests remain incompatible with this explicitly one-environment candidate. No GPU, soft-body, arbitrary material or hardware claim follows.

The [combined score](evidence/unisim-reuse/combined-score.json) also applies the existing independent physical scorer and directly compares candidate reset repeats. Both conditions replay with zero differences in the recorded states and forces. The public scoring command performs all three checks.
