# Drake contact-path protocol

[English](drake-contact-paths-protocol.md) | [简体中文](drake-contact-paths-protocol.zh-CN.md)

[#151](https://github.com/huangkiki/Dexlab/issues/151) extends the [original qualification](drake-incline-protocol.md), preserving its 1 µm-clearance v2 cohort. Official native Drake **1.57.0**, source `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`, Python 3.12.12, NumPy 2.5.3, CPU FP64. GitHub and PyPI latest-stable identities were checked before freezing; all 402 installed distribution files match the official wheel and #117. This is a native path, with no framework conversion or engine patch.

## Fixed matrix and parameters

The registered discrete solver is SAP, with `kLagged`, `kSimilar`, `kSap` approximations. Each uses point or hydroelastic contact: six effective configurations. The old kLagged/hydroelastic nine positives and negative are reused; the other five each run nine positives plus a negative in fresh processes. Enum aliases are not additional profiles. For this rigid-cube/compliant-half-space asset, fallback uses hydroelastic contact: all state/force/contact arrays in three independent 20-step static pairs are exactly equal. Other assets can fall back to point contact; this is not a global equivalence claim. [Versioned API/source inventory](evidence/drake-contact-paths/source-links.json).

Keep the original 40 mm / 64 g cube, zero COM, isotropic inertia, gravity9.81, 15° static μ=.5, 35° sliding μ=.5, 15° μ=0, 2/1/.5 ms, 2 s, score window .5–2 s. Initial pose is 1 µm above the plane. No-floor negative is2 s at1 ms. Matching geometry is retained even when the selected point model ignores hydroelastic properties.

- Hydroelastic: rigid cube resolution .01 m; compliant plane modulus1e8 Pa / slab .1 m.
- Point: each geometry explicitly authors2e6 N/m; series combination1e6 N/m. This is an engineering fixture, not material calibration or equivalence to hydroelastic stiffness.
- Equal static/dynamic friction, native harmonic combination. Hunt–Crossley dissipation0; stiction tolerance1e-4 m/s; near-rigid threshold1.0.
- Explicit relaxation time .1 s per geometry, native summed .2 s. `kSap` uses this Kelvin–Voigt parameter and ignores Hunt–Crossley dissipation; Lagged/Similar use Hunt–Crossley and ignore relaxation. Source default .1 s is not a runtime readback; the new property values are directly read back. [Property combinations](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_properties.cc), [native contact construction](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc).

No outcome tuning is performed. These fixed configurations are initial evidence, outside shared-budget development/holdout admission and reliable coverage-v1. More profiles do not add task types.

## Observations and acceptance

Record native initial mass/inertia/frames/materials and sampled output settings. Each update saves state, native generalized contact force/torque, and either integrated hydroelastic surface forces or point-pair force on bodyB, explicitly signed onto the cube. Point observations include ordered witnesses, penetration, normal, contact position and slip/separation speeds. Hydroelastic observations add every face's area, centroid, normal, sampled pressure and plane pressure gradient; these are not per-face solved force readbacks.

The sampled force belongs to the update interval, geometry to its start and velocity to its end. Validate clocks, position/velocity consistency, force sums, world torque about the old COM, pair sign and geometry. No state is written after initialization. Contact storage is native dynamic storage, with copied counts checked; no authored fixed contact-capacity claim. Solver iterations, achieved tolerances and the unsupported Python compliance-type value remain explicit missing readbacks. [Point force sign](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/point_pair_contact_info.h), [sampled contact generation](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc).

Physical limits are unchanged: static displacement/speed .001 m/.001 m/s; sliding position/velocity RMSE .01 m/.01 m/s; acceleration .05 m/s²; rotation .01 rad; geometric penetration .001 m; force-balance RMSE .01 N; continuous support. State/contact impulse guard stays **1e-7 N·s**. Independent scoring retains invalid observations in the nine-positive denominator and requires a valid rejected negative. The common scorer and old records are unchanged.

## Budget, resources and reproduction

The freeze contains50 formal starts /115000 updates. The separate six-hour/64-start development package used34 starts /13360 updates, including zero-step admission, short path probes, three pressure-observation replays of old sliding cases and two independent residual repeats. This does not consume the pinch research700-start budget.

The measured179.15 MiB short-probe peak selects **8 GiB / four-core quota**, zero swap and an additional8 GiB desktop reserve. Peak formal service memory was225.70 MiB; no memory-high/OOM or CPU throttling. New unknown/complex tasks retain16/24 GiB starts. A controller log-name collision stopped after one completed case before launching the second; the preserved continuation reuses that record and runs only49 missing cases. Physics source, protocols and resource plan did not change.

Run within the existing bounded runner and research lock. Inputs and portable acquisition controller are in the [evidence release](https://github.com/huangkiki/Dexlab/releases/tag/v0.55.0):

```bash
python evidence/frozen-v1/acquire-v2.py --frozen evidence/frozen-v1 \
  --repo "$CHECKOUT" --output "$NEW_OUTPUT" --python "$NATIVE_PYTHON" --kind formal
# A single archived case, in the qualified environment:
python -m dexlab.drake_incline --protocol "$CASE_PROTOCOL" \
  --proof evidence/frozen-v1/official-proof.json --output "$NEW_CASE" --record-only
# Engine-free replay (NumPy2.5.3):
PYTHONPATH=evidence/frozen-v1/scoring-source python scripts/score_drake_contact_paths.py \
  --frozen evidence/frozen-v1 --campaign evidence/campaign-v2 --output scores.json
PYTHONPATH=evidence/frozen-v1/scoring-source python scripts/diagnose_drake_lagged.py \
  --input evidence/lagged-diagnostic-v1/lagged-hydroelastic --output diagnosis.json
```

Local installation/traceback paths are redacted only in the public export with explicit source/published hashes and updated runtime-reference hashes. Native traces, contacts, admissions and protocols are unchanged; private originals are preserved. Whole-service and native-call costs are reported separately, not as engine throughput rankings. [Results](drake-contact-paths-results.md).
