# Genesis incline protocol v1

[简体中文](genesis-incline-protocol.zh-CN.md) · [Results](genesis-incline-results.md)

Native latest-stable qualification is frozen to Genesis 1.4.3, source `216a708e06124595521a9d36a51fae5393fd4ff8`, and Quadrants 1.3.3. Official wheel contents match installed code and mapped compiler library. CPU FP64, deterministic mode, seed 0, one execution/compile thread, fresh unbatched scene per case; batched link/DoF parameter storage is explicit. Framework-compatible pathways remain separate. No official engine is patched.

The uniform 40 mm cube has density 1000 kg/m³, mass 64 g and principal inertia 1.7066666666666674e-5 kg·m². It starts at rest, flush with an infinite plane, rotated about +Y. World gravity is [0,0,-9.81] m/s²; local COM is zero, free-body DoFs are six. Three conditions—15° static μ=.5, 35° sliding μ=.5 and 15° nominal μ=0—use dt 2/1/.5 ms, each for 2 s. Score window .5–2 s; [original equations/limits](incline-comparison-protocol.md) stay unchanged, including the 1e-7 N·s consistency guard.

Freeze five applicable solver/cone/contact combinations from the official Newton/CG, elliptic/pyramidal and convex/Signorini enums. Signorini requires Newton/elliptic. Fix approximate_implicitfast, 100 iterations, tolerance 1e-9, noslip 0, torsional/rolling friction off; impratio 100 for elliptic and 1 for pyramidal. Full effective options and static kernel flags are saved per profile. This is not an integrator/device/tuning Cartesian search.

Before stepping, set both geoms' sol_params to [.02,1,.9,.9,.001,.5,2]; preserve constructor values and subsequent effective values. Effective pair sol_params average both geoms, with time constant floored at 2dt. Explicit .02 avoids that floor across the timestep sweep. Pair friction is max of scaled geom values and .01. A nominal-zero case records both the requested zero and native .01, fails requested-model matching, and retains a separately labeled effective-model diagnostic. Identical parameter names do not establish material equivalence across engines.

Each profile includes a 15°/.5/1 ms negative with plane collision masks 1 and cube masks 2, retaining both geoms but no eligible pair. Require zero contacts/force and gravity-consistent motion. Constructor masks 0 were rejected during development because the native build removes that geom; this never became a positive-duration cohort.

Contact normals point B→A; stored forces act on B. Per-contact sums are checked against an independent native cube net-force getter. Forces and pre-integration contact geometry belong to the just-completed step; state clocks come from scene.get_time(). Full clock, geometry, effective-friction/sol_params, native-error, contact-count and force/impulse checks precede analytic scoring. Initial setters never run after stepping begins. Interrupted records retain actual completed and attempted lengths, never zero-pad missing observations. Achieved CPU loop counts are not exposed; graph-loop counters are not substituted.

Acquisition budget: five serial starts, 50 episodes, 115,000 updates, ≤600 s/profile and ≤1 h batch within a separate 6 h development package. Unknown positive-duration peak starts at 16 GiB/four-core quota, zero swap, 8 GiB launch reserve. Diagnostic prefixes use their own freeze/resource receipts and do not replace original scores. Formal pinch 700-start budget is untouched. Every geometry/options admission passed before outcome inspection; there was no outcome-based threshold change.

```bash
# Native commands require the bounded resource/research-lock wrapper.
python -m dexlab.genesis_incline --protocol docs/evidence/genesis-incline/profiles/newton-elliptic-signorini.json --proof docs/evidence/genesis-incline/official-proof.json --output /data/admission --admission-only
python -m dexlab.genesis_incline --protocol docs/evidence/genesis-incline/profiles/newton-elliptic-signorini.json --proof docs/evidence/genesis-incline/official-proof.json --output /data/physical
# Offline, after extracting the raw archive (NumPy only):
python -m dexlab.genesis_incline_score --input dexlab-genesis-incline-v1/campaign-v1/newton-elliptic-signorini --output score.json
# Separately budgeted diagnostic prefixes:
python scripts/diagnose_genesis_incline.py --input dexlab-genesis-incline-v1/campaign-v1/cg-elliptic-convex --case static-h0.001 --output /data/diagnosis-100
python scripts/diagnose_genesis_incline.py --input dexlab-genesis-incline-v1/campaign-v1/cg-elliptic-convex --case static-h0.001 --iterations 1000 --output /data/diagnosis-1000
```
