# Contact-onset cone and time-constant protocol

[English](CONE_PROTOCOL.md) | [简体中文](CONE_PROTOCOL.zh-CN.md)

**Executed: 24 fixed conditions + 2 exact repeats; 26/26 valid and passing the existing planar engineering checks.** This is a MuJoCo development contrast, not a Manda reproduction or cross-engine material comparison. See [Issue10 protocol](https://github.com/huangkiki/Dexlab/issues/10#issuecomment-6018191256) and the [frozen matrix](../../benchmarks/contact-cone-timeconst-v1.json).

Keep a fresh0.2kg/40mm cube, gravity9.81m/s² and initialvx0.25m/s. No settling; start at geometric touch with zero vertical/angular velocity. This measures non-equilibrium contact onset, not steady sliding. No actuator or runtime pose overwrite.

Run elliptic/pyramidal cones × timeconstants5/20ms × timesteps1/.5/.25ms × authoredfriction.3/0. Keep dampratio1, solimp[.95,.99,.001,.5,2], Euler/Newton100iterations/tolerance1e-10. Each of24 cases runs0.5s, followed by two exact repeats of mu.3/dt1ms/tc5ms, one percone. Preserve all failures; no new cohort or tuning after outcomes. One qualified worker,600s budget/660s deadline.

The [official solver-parameter guide](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters) motivates separating contact settings from the integrator. Both timeconstants exceed2dt here. Changing timeconstant changes response stiffness/damping; this is not solely numerical-error refinement. MuJoCo's native friction floor remains even at authoredzero.

Keep existing planar engineering limits. Independently verify clocks, native settings, initialstates, forceledgers, warnings and hashes before matched contrasts. Report first10ms excessnormalimpulse, peak|vz| and first50ms horizontalvelocity discrepancy from the conditional no-tip Coulomb reference. Exact repeats establish numerical repeatability; they are not statistical population trials. Neither the finest timestep nor the analytic approximation is measured material truth.

## Results and interpretation

![Matched contact-onset diagnostics](evidence/cone-timeconst/cone-results.png)

Axes start at zero; panel scales differ. Lines connect three tested timesteps and do not establish a convergence rate. Two exact repeats are omitted from the curves but retained in the [complete CSV](evidence/cone-timeconst/cone-results.csv) and [independent score](evidence/cone-timeconst/cone-results.json).

| Observation | Result | What it establishes |
|---|---|---|
| Valid records / engineering checks | 26/26 / 26/26 | Existing limits pass for this fixture, not material accuracy |
| Exact repeated state arrays | 2/2 | Repeatability of two fixed settings, not a population estimate |
| Friction 0.3: peak vertical speed | 8.360–23.682 mm/s | Contact onset remains sensitive within passing configurations |
| Friction 0.3: first 50 ms max horizontal discrepancy | 2.508–7.104 mm/s | Difference from a conditional rigid Coulomb reference |
| Authored zero friction: same horizontal discrepancy | 0.004903–0.004917 mm/s | Negative control is small but not exactly zero; native friction floor retained |
| Cone change, pyramidal minus elliptic: peak vertical speed | −0.583 to +2.819 mm/s | Direction depends on the matched setting; neither cone wins uniformly |
| Time constant 20 minus 5 ms: peak vertical speed | −8.614 to 0 mm/s | Reduced or unchanged in this finite matrix, not a universal tuning rule |

The 12 cone contrasts and 12 time-constant contrasts hold the other declared factors fixed. The zero-friction peak vertical speed equals g·dt at these tested settings (2.4525, 4.905, 9.81 mm/s): geometric-touch initialization includes the first gravity step. It must not be interpreted as a settled sliding instability. First-10-ms excess normal impulse is retained in the CSV; its sign also depends on the configuration. None of these diagnostics replaces the frozen engineering acceptance thresholds.

**Decision:** distinguish solver/contact configuration from engine identity before attributing a transient to an engine. Passing a coarse task check can coexist with measurable configuration sensitivity. Do not choose a winning cone, claim asymptotic convergence, pool this with Genesis, or treat a time-constant adjustment as a calibrated shared material. The common-material and unloading obligations in [the acceptance audit](CONCLUSIONS.md) remain open.

## Verification and reproduction

The opt-in cone argument reaches compiled native options; the default remains elliptic. Seven focused tests cover actual compiled options and synthetic negatives: missing rows/cases, altered settings/XML, coherent force injection, hashes, and repeat mismatch. Synthetic fixtures are test data, not additional physical episodes. An independent process re-scored all archived records and matched the original result exactly. Official-wheel/latest-version admission passed for MuJoCo 3.15.0 before execution. The entire admitted wrapper took 152.713 s including admission/tests; it is not a physics speed measurement. It used one worker with enforced 16 GiB memory, two CPU-core equivalents, 128 tasks, no swap and a 660 s deadline; no memory-high/OOM events occurred.

From an installed source checkout with official MuJoCo 3.15.0 and `DEXLAB_MUJOCO_PROFILE=qualification-3.15.0`, execute inside the documented [resource guard](../../docs/autoresearch.md):

```bash
python -m dexlab.contact_cone_run /path/to/new-study
python -m dexlab.contact_cone_run /path/to/study --verify
python scripts/report_contact_cone.py /path/to/study /path/to/report
```

The last two commands use archived data without re-running native dynamics. The study retains authored XML, native readbacks, every-step states/forces/contacts/warnings, source snapshots and hashes. The frozen protocol SHA-256 is `11833036123c60de572cfd8e6325d0b181328f33a19250430f42d3985f906a52`. No official engine modification, acceptance relaxation or post-outcome retuning was used. This is an onset microbenchmark, not a grasp success or hardware validation result.
