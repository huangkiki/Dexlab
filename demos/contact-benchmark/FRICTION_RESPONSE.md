# Friction response diagnostics

[English](FRICTION_RESPONSE.md) | [简体中文](FRICTION_RESPONSE.zh-CN.md)

**Both engines pass all eight declared development cases, but their low-speed resultant-force responses differ.** The existing plane scorer checks the complete trajectory against ideal, non-tipping Coulomb sliding. The new read-only diagnostic groups measured resultant force by actual COM speed, leaving that scorer and all frozen acceptance limits unchanged.

For each completed solve, use the midpoint of its recorded pre/post-step planar COM velocities, `v_mid`. With positive normal resultant `Fz`, report the signed resisting ratio `−Ft·v_mid / (|v_mid| Fz)`. Positive means opposing translation; negative means assisting it. This is a force ratio, not an identified static friction coefficient. The native force epoch and integrated state epoch differ; midpoint pairing is an explicit temporal approximation.

Bins start at 0.0001, 0.001, 0.01, 0.05, 0.1 and 0.3 m/s; the final bin is open-ended. Reject ratio samples below 1% of body weight in normal load, below the speed floor, or with opposing bracketing velocity directions. Retain disjoint exclusion counts and bin durations. Empty bins are null, never zero. These choices are diagnostic partitions, not new success thresholds or measured material properties.

Missing contact coverage makes the diagnostic incomplete. Failed momentum, penetration or reference checks remain failed even when a curve can be computed. Tipping or non-planar motion invalidates the planar reference. `Σ Ft·v_mid Δt` is only a translational contact-work proxy: rotation, contact-point motion and native friction anchors are omitted, so it is not material-point slip or total frictional dissipation.

```bash
.venv/bin/python -m dexlab.contact_friction runs/contact-plane
```

The command reads and independently verifies an existing archive, prints JSON, and returns nonzero for failed archive acceptance. It does not launch physics or overwrite records. Legacy engine versions remain historical. New paired development runs require current official-version admission, frozen inputs and bounded execution; friction/material equivalence, cooked geometry and formal cost–error comparison remain open in #10.

## Frozen development result

![Native friction diagnostics and all-case velocity errors](media/friction-response-v1.png)

Points are within-bin medians at geometric bin centers; connecting lines guide the eye and are not fitted constitutive laws. Empty bins remain absent. The right panel includes all 16 cases, including zero-friction and rest controls. No failed native outcomes were discarded: all 16 passed the unchanged plane checks and independent offline rescoring reproduced each verdict. Synthetic missing-contact, assisting-force, reversal and tipping negatives remain separate unit tests, not native episodes.

The [frozen matrix](../../benchmarks/contact-friction-v1.json) uses MuJoCo **3.14.0** and SuperDex **1.0.0 FP64**, with official wheel/native identity and latest-stable metadata checked before execution. Eight paired configurations cover forward/reverse 0.25 m/s, forward/reverse 0.005 m/s, zero friction, rest, mass 0.4 kg and half timestep. Default mass is 0.2 kg, coefficient 0.3, timestep 0.5 ms, settling 0.2 s and measurement 0.5 s. No parameters were fitted after seeing outcomes. This is development evidence, not held-out calibration.

| Observation | MuJoCo | SuperDex |
|---|---:|---:|
| Forward: median force ratio in 1–10 mm/s bin | 0.15641 | 0.02076 |
| Slow start: same bin | 0.10405 | 0.02320 |
| Forward maximum velocity-reference error | 4.877 mm/s | 2.954 mm/s |
| Half-step maximum velocity-reference error | 3.779 mm/s | 3.285 mm/s |
| Nominal initial COM height after native settling | 19.996671 mm | 20.063331 mm |

At higher speed the forward-bin ratios approach the nominal 0.3. Low-speed response depends on native laws and the within-bin velocity distribution; the medians are not identical-speed constitutive samples. Halving the timestep does not uniformly improve the reference error. MuJoCo's nominal zero-friction run records approximately 0.00001 resisting ratio, versus effectively zero in SuperDex; this stays in the report and is not rounded into exact equivalence. The different initial settled heights are measured, not hidden by pose alignment. This experiment does not identify which engine best matches real materials.

[Complete per-case results](evidence/friction-response-v1.json) include exact initial poses/velocities, native readbacks, source hashes, artifact hashes, exclusions, all scores and costs. Batch wall time including official admission was 27.492 s. Preparation ranges were 0.091–0.105 s / 0.298–1.189 s; stepping plus observations 0.059–0.094 s / 0.131–0.242 s for MuJoCo / SuperDex. These include different instrumentation and timestep counts, exclude no cases, and are **not isolated native-solver throughput comparisons**. No rendering was used in physics runs; report plotting is separate. No real hardware data was collected.

Reproduction uses the qualified official runtime, its existing wheel cache, and a fresh output directory under the repository's bounded research runner:

```bash
python demos/contact-benchmark/friction_response.py runs/friction-new --wheel-dir "$OFFICIAL_WHEEL_DIR"
python demos/contact-benchmark/report_friction.py runs/friction-new --output runs/friction-report.json --plot runs/friction-report.png
```

The batch is capped at 16 native runs and 1800 s; enforce the same outer cgroup deadline. Runtime errors stop execution; physical failures remain in the report. A zero report exit means recorded outcomes were reproduced, not that every physical case passed. The published raw bundle below includes the standalone offline reproducer; the checked-in summary is not a substitute for raw records.

Published v0.21.0 raw bundle: [dexlab-friction-evidence-v1.tar.gz](https://github.com/huangkiki/Dexlab/releases/download/v0.21.0/dexlab-friction-evidence-v1.tar.gz), 4289185 bytes, SHA-256 `cd25b5c05d7dfadca69e195ff0cc1269a7052b24180e8a998c791edc93822001`. All 293 file hashes and 16 rescored outcomes verified after extraction; native state/contact bytes unchanged. Only private source-map keys were redacted; before/after hashes are included.
