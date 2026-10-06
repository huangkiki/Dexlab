# Paired mass and size transfer: prospective protocol

English | [简体中文](TRANSFER.zh-CN.md)

Status: all30 preregistered episodes and independent rescoring completed; delivery regressions and evidence were published in [v0.25.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.25.0). Select this cohort after development but before seeing its transfer outcomes. It is not an earlier concealed blind test or the apple-grasp held-out set.

## Question

Do three frozen contact profiles retain their declared synthetic normal response and unloading behavior at new mass/size combinations? Keep both MuJoCo impedance candidates and the SuperDex load-damping candidate, including the known poor candidate. No retuning from new outcomes.

The reference remains the synthetic K=20,000 N/m, D=40 N s/m model, evaluated with each declared mass. Native mappings stay at their nominal0.2kg/40mm development values without mass/area compensation. This tests configuration transfer, not whether different native contact algorithms are wrong. Keep positive-load windows, independent unloading checks and engineering thresholds; no phase/time/position fitting.

## Frozen rules

`benchmarks/contact-transfer-v1.json` declares ten deterministic seeds. SHA256 the decimal seed; divide its first two big-endian64-bit integers by2^64 to sample mass[0.12,0.28)kg and half-size[0.015,0.025)m, rounded to six decimals. Exact combinations were checked against previous repository matrices with no duplicate found; this does not exhaustively audit every historical temporary run, and the parameter ranges are not claimed unseen.

Three profiles per combination give30 serial fresh-scene0.8s episodes at0.5ms. Rotate profile order by seed index. No retries, retuning or discarded failures. Batch budget600s, enforced process timeout660s; latest official stable admission and local hard resource limits apply. PhysX remains explicitly excluded pending stable-runtime qualification.

## Comparability is separate from physical scoring

Verify complete archives/pairs, actual initial states, commands and native mass/inertia before comparison. Preserve missing/error outcomes in the declared denominator. Compare each native profile to the same synthetic target; do not claim constitutive equivalence.

Read MuJoCo compiled analytic box/plane geometry directly. Check SuperDex submitted mesh vertices, faces, dimensions and closed surface separately from unobservable internal cooking. If public APIs expose neither cooked geometry nor combined contact-law parameters, retain unknown status rather than inventing comprehensive qualification.

Report every seed's outcome, absolute response discrepancy, unloading force, penetration, representation checks and gaps, with raw data/source/version provenance. Single-episode costs have no repeat interval from the previous three-repeat study.

## Result: nominal profiles do not retain the transfer target

All30 runs have complete paired evidence, matching actual initial states and geometry checks within the declared scope; SuperDex internal cooking and combined-law observability remain unknown. Original engineering checks pass1/30, transient target0/30 and combined checks0/30. All failures independently reproduce. Nominal-scene success does not establish mass/size transfer, and failure of fixed parameter mappings does not establish engine error.

| Profile | Combined pass | Worst-window RMS range / µm |
|---|---:|---:|
| mujoco-imp0001-500us | 0/10 | 12.951–155.253 |
| mujoco-imp09-500us | 0/10 | 120.915–154.669 |
| superdex-load-damping-500us | 0/10 | 9.421–214.371 |

[Preregistration](https://github.com/huangkiki/Dexlab/issues/10#issuecomment-5997434279) · [All30 results](../../docs/evidence/contact-transfer-v1.json)

```bash
python demos/contact-benchmark/report_transfer.py PATH_TO_EVIDENCE/study
```

![Per-scenario synthetic response discrepancy](../../docs/evidence/contact-transfer-v1.png)
