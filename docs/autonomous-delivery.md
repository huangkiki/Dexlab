# Bounded autonomous research: delivery audit

[English](autonomous-delivery.md) | [简体中文](autonomous-delivery.zh-CN.md)

This report traces **the actual #32 research delivery, #31 public offline reproduction, and a separately injected process-recovery exercise**. The injection is not presented as a crash of that physics experiment. Successful delivery does not establish physical accuracy.

## Research delivery and reference standards

| Stage | Inspectable evidence | Finding and limitation |
|---|---|---|
| Question and hypothesis | [Table-edge counterexample](../demos/cloth-folding/TABLE-CONTACT.md) | Native contact distance alone missed triangle-interior intersections. The isolated triangle and disabled-midphase controls reject an explanation based solely on whole-cloth contact competition |
| Bounded experiments and rejected candidates | [Settling and release investigation](../demos/cloth-folding/SETTLING.md) | Table subdivision delayed intersection; node alignment did not repair it. A half-step run still failed and changed the initial state, so it is not a convergence demonstration. Failures remain available |
| Independent scoring and controls | Protocol, table, floor, self-contact and robot audits linked from that report | Native extrema scan every step; independent geometry samples saved frames. Injected intrusion is detected and separated controls pass; neither proves continuous-time or finite-thickness separation |
| Outcome | 9 s / 72,000 steps; strain 3.5161%; self contact 1.492 mm; final normal force 0 N | Passes frozen engineering checks, only 7.95 µm below the self-contact limit. No measured material calibration or robustness/physical-accuracy claim |
| Regression and delivery | [PR #56](https://github.com/huangkiki/Dexlab/pull/56), [v0.19.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.19.0) validation asset | At delivery: 397 tests, both complete 14 s backend checks, bilingual docs and applicable CI; self-review, not independent approval |
| Public archive and offline reproduction | [Archive protocol/results](evidence/PUBLIC-ARCHIVE.md), [PR #57](https://github.com/huangkiki/Dexlab/pull/57), [v0.19.1](https://github.com/huangkiki/Dexlab/releases/tag/v0.19.1) | 106 records reproduced in a separate minimal environment, including failures. Frozen-scorer replay is not current-engine resimulation or proof that local copies are independent backups |

PR #56 tested tree: `740473e03aab5a448850914611fa680b408882b4`; merge: `82279e5ae5ab7e44da2dde361c1be2f76307025f`. Its release asset retains execution-source hashes, media linkage and the historical admission timestamp. PR #57 merge: `29cd396818ebd7beb5dfa017c80f891651d54155`; public archive SHA-256: `09c4da563ffefa3635b0830d7b9334ab6f97e9f83e4f0fba731d56e9a349ad82`. These are historical results, not latest-engine evidence.

## Recovery: real process fault injection

The [machine-readable result](evidence/recovery-exercise-v1.json) concerns a separate small fixture. Its bounded service enforced 8 GiB memory, one CPU quota, 32 tasks, a 120 s deadline and zero swap. This is not a throughput measurement.

1. Start a guard with a foreground child waiting for a release signal; retain the active record.
2. Kill only the guard and measure one surviving child. A second request exits 75 without executing its command marker or creating a false completed receipt.
3. Release the original child and confirm no live group members before recovery.
4. Recovery exits 0 and links the original window. The fixture SHA-256 is unchanged and the interrupted record remains available.

The outer launcher exits 247 because the internal guard's signal exit passes through Python exit-status handling; it must not be interpreted as normal experiment completion. The enclosing bounded verification service finally exits 0.

The regression is `test_killed_guard_keeps_live_child_group_blocked_then_recovers` in `tests/test_research_guard.py`. Added assertions check unchanged interrupted-receipt bytes and fixture hash. Run inside an admitted resource envelope and the research mutex:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_research_guard.py' -v
```

Coverage is the foreground process-group contract, not escaping daemons, cross-host partitions, power-loss durability, large-archive corruption or scheduler wake-up guarantees. Eligibility/dependency claims are covered separately in `tests/test_autoresearch.py`. Deployment paths, accounts and private receipts are excluded.

## Versions and scientific limits

Keep historical batches frozen. Apply [version admission](engine-qualification.md) at new dispatch, batch freeze and publication; record old runs when releases change, without mutating live environments or relabeling evidence. Genesis remains subject to #42 dependencies and qualification; this report does not claim its support.

This establishes one bounded traceable delivery instance and the specified recovery behavior. Evaluate physical validity separately using the [research standards](research-focus.md). Workflow acceptance for #35 does not resolve #10 contact mechanisms or #6 measured calibration.
