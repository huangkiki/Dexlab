# MuJoCo versus SuperDex: a free-cube incline comparison

[简体中文](incline-comparison-results.zh-CN.md) · [Preregistered protocol](incline-comparison-protocol.md) · [All metrics](evidence/incline-comparison/results.json)

With matching geometry, mass, initial state, gravity and three timesteps, two **fixed native contact profiles** produce different drift and stability. MuJoCo 3.15.0 at impedance=0.9 passes 3/9 original joint checks; SuperDex 1.0.0 FP64 passes 8/9. These are deterministic-case counts, not sampled success probabilities or real-material accuracy rankings.

## Findings

- **Static friction is not exact rest.** At 15°/μ=0.5, both engines creep. Steady speed is approximately 0.635 mm/s in MuJoCo and 0.319 mm/s in SuperDex. Two-second drift is 1.301–1.336 mm versus 0.708–1.132 mm, giving 0/3 versus 2/3 under the original 1 mm limit. SuperDex drift increases with timestep refinement; convergence is not established.
- **Sliding stability differs between these profiles.** At 35°/μ=0.5, MuJoCo loses contact in 72.8–74.15% of full-run solve samples and rotates 0.169–3.130 rad; all three violate the analytical sliding assumptions. All three SuperDex cases meet the original joint limits, retain support during 0.5–2 s and rotate less than 0.00414 rad. Its 1/0.5 ms cases still have early contact-loss samples accounting for 0.55/0.975% of the full run; support is not continuous from initialization.
- **Nominal zero-friction bias has a known source.** Both pass 3/3, but MuJoCo's native contact μ floor is 1e−5, giving window velocity RMSE about 8.21e−5 m/s; SuperDex yields 8.04e−12–1.52e−10 m/s. The latter approaches this case's numerical precision scale, not general collision or material accuracy.
- **Retain the counterexample to configuration-based rankings.** This pairing preregistered the MuJoCo impedance=0.9 baseline. The [original #95 impedance=0.99 cases](incline-friction-results.md) drift only 0.141–0.179 mm, less than every SuperDex case here. That sensitivity evidence remains visible; neither engine was retuned after outcomes.

## Conditions and evidence

A uniform 40 mm, 64 g free cube, g=9.81 m/s², initially at rest with its bottom flush against the plane, duration 2 s, no controller or state writes after initialization. Static reference |f|≤μN; sliding a=g(sinθ−μcosθ) applies only with negligible rotation and continuous support. Parameters and sources follow the [frozen manifest](evidence/incline-comparison/manifest.json) and original protocol.

MuJoCo uses Euler/Newton, 100 iterations maximum, tolerance 1e−10, solref=[0.02,1], constant solimp=0.9 and an elliptic friction cone. SuperDex uses BACKWARD_EULER, 100 iterations maximum, absolute/relative tolerances 1e−9, penalty=1e9, threshold 1e−4 m, smoothing half-distance 5e−5 m, friction smoothing speed 1e−3 m/s, zero normal/viscous damping. Values come from published native fixtures and tangent experiments; **they are not equivalent materials or equal solver work**.

All 21,000 new SuperDex steps report CONVERGED. Mass, inertia, gravity, coordinates, geometry, initial state and solver readbacks pass; every state/force impulse residual is below the original 1e−7 N·s bound. Independent scoring verifies actor parameters without inventing the combined friction-law readback unavailable in SuperDex. MuJoCo retains its native combined friction observations. Mathematical consistency cannot rule out every possible fabrication.

MuJoCo forces come from the preintegration solve, while SuperDex forces are queried after the step; each is paired with that step's velocity increment. Native contact-distance epochs differ, so a supplementary common cube/plane geometric penetration is also reported from saved poses, without changing original checks. It is zero in all nine SuperDex cases: contact can activate at a positive gap, which does not imply an exactly rigid contact model.

## Every paired case

Velocity RMSE and acceleration errors use 0.5–2 s, initializing the analytical reference from the measured window-start state. Fits for MuJoCo sliding cases that violate assumptions are diagnostic only. Contact loss and drift/travel cover the full run. JSON retains every threshold, force error and individual check.

Static cases use static displacement/speed checks; their sliding-fit errors in the table are not acceptance criteria.

| Case | Engine | Drift/travel (mm) | Window velocity RMSE (m/s) | Acceleration error (m/s²) | Rotation (rad) | Contact loss | Pass |
|---|---|---:|---:|---:|---:|---:|---|
| static-d0.9-h0.002 | mujoco | 1.3360 | 3.4391e-11 | 2.6294e-12 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.002 | superdex | 0.7085 | 4.9802e-16 | 7.1027e-17 | 0.00064297 | 0.000% | True |
| static-d0.9-h0.001 | mujoco | 1.3125 | 1.5649e-11 | 1.1174e-12 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.001 | superdex | 0.8471 | 1.0809e-15 | 5.7369e-17 | 0.0015764 | 0.450% | True |
| static-d0.9-h0.0005 | mujoco | 1.3008 | 9.561e-12 | 6.5559e-13 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.0005 | superdex | 1.1319 | 1.948e-15 | 3.952e-16 | 0.0019206 | 0.825% | False |
| sliding-d0.9-h0.002 | mujoco | 3219.5391 | 0.099105 | 0.012352 | 3.1304 | 72.800% | False |
| sliding-d0.9-h0.002 | superdex | 3257.9769 | 5.7581e-07 | 6.6638e-07 | 0.0017856 | 0.000% | True |
| sliding-d0.9-h0.001 | mujoco | 3218.0635 | 0.068754 | 0.00090431 | 0.16872 | 74.150% | False |
| sliding-d0.9-h0.001 | superdex | 3283.6218 | 3.8327e-07 | 4.0609e-07 | 0.0041306 | 0.550% | True |
| sliding-d0.9-h0.0005 | mujoco | 3206.5829 | 0.083108 | 0.02272 | 1.2045 | 73.275% | False |
| sliding-d0.9-h0.0005 | superdex | 3309.0334 | 2.6197e-07 | 2.1428e-07 | 0.0027688 | 0.975% | True |
| frictionless-d0.9-h0.002 | mujoco | 5082.9180 | 8.209e-05 | 9.4757e-05 | 1.0324e-07 | 0.000% | True |
| frictionless-d0.9-h0.002 | superdex | 5083.1077 | 8.0447e-12 | 1.3071e-11 | 0 | 0.000% | True |
| frictionless-d0.9-h0.001 | mujoco | 5080.3791 | 8.2076e-05 | 9.4757e-05 | 1.0745e-07 | 0.000% | True |
| frictionless-d0.9-h0.001 | superdex | 5080.5687 | 1.8544e-11 | 1.9817e-11 | 0 | 0.450% | True |
| frictionless-d0.9-h0.0005 | mujoco | 5079.1096 | 8.2069e-05 | 9.4757e-05 | 1.0324e-07 | 0.000% | True |
| frictionless-d0.9-h0.0005 | superdex | 5079.2992 | 1.5159e-10 | 2.1352e-10 | 0 | 0.825% | True |

## Initial transients remain visible

These errors use the initial rest state at t=0. Although SuperDex 35° cases pass the window criteria, full-run velocity error increases from 0.0185 to 0.0453 m/s under refinement. Tiny window-fit errors do not establish full-trajectory accuracy. Geometric penetration is a supplementary diagnostic, not a rewritten acceptance criterion.

| Case | MuJoCo full velocity RMSE (m/s) | SuperDex full velocity RMSE (m/s) | MuJoCo geometric penetration (mm) | SuperDex geometric penetration (mm) |
|---|---:|---:|---:|---:|
| static-d0.9-h0.002 | 0.000714932 | 0.000684274 | 0.169099 | 0 |
| static-d0.9-h0.001 | 0.000669145 | 0.00150622 | 0.120738 | 0 |
| static-d0.9-h0.0005 | 0.000655178 | 0.00270599 | 0.120208 | 0 |
| sliding-d0.9-h0.002 | 0.077904 | 0.0185466 | 4.6068 | 0 |
| sliding-d0.9-h0.001 | 0.0553112 | 0.0321913 | 0.928803 | 0 |
| sliding-d0.9-h0.0005 | 0.0724752 | 0.0453452 | 0.959918 | 0 |
| frictionless-d0.9-h0.002 | 0.000109444 | 7.00678e-12 | 0.159249 | 0 |
| frictionless-d0.9-h0.001 | 0.00010943 | 1.61531e-11 | 0.102009 | 0 |
| frictionless-d0.9-h0.0005 | 0.000109423 | 1.2816e-10 | 0.0945565 | 0 |

## Cost and reproduction

The new bounded service takes 3.772 s: summed setup 0.615 s, native stepping 0.630 s, observation 1.352 s and other loop recording overhead 0.253 s. CPU: Intel Core i9-14900K, x86_64, zero native worker threads. Enforced limits: 16 GiB, 2 CPU quota, 128 tasks, zero swap, 1800 s. Historical MuJoCo reports the same CPU model but a separate environment and measurement time: **no speed ranking**. These short timings contain noise; no rendering or concurrent transfers. Environment setup separately takes 15.396 s.

| Case | SD setup (s) | SD native steps (s) | SD observation (s) | SD loop wall (s) | SD total (s) | MJ historical native steps (s) |
|---|---:|---:|---:|---:|---:|---:|
| static-d0.9-h0.002 | 0.26139 | 0.04411 | 0.06605 | 0.12234 | 0.38672 | 0.00251 |
| static-d0.9-h0.001 | 0.04760 | 0.08908 | 0.13333 | 0.24682 | 0.30024 | 0.00489 |
| static-d0.9-h0.0005 | 0.04560 | 0.17572 | 0.26266 | 0.48699 | 0.54489 | 0.00967 |
| sliding-d0.9-h0.002 | 0.04343 | 0.04229 | 0.06700 | 0.12168 | 0.16856 | 0.00181 |
| sliding-d0.9-h0.001 | 0.04317 | 0.07272 | 0.13271 | 0.23008 | 0.28009 | 0.00358 |
| sliding-d0.9-h0.0005 | 0.04362 | 0.11600 | 0.25741 | 0.42225 | 0.47988 | 0.00715 |
| frictionless-d0.9-h0.002 | 0.04369 | 0.01290 | 0.06207 | 0.08681 | 0.13295 | 0.00303 |
| frictionless-d0.9-h0.001 | 0.04311 | 0.02566 | 0.12474 | 0.17389 | 0.22154 | 0.00592 |
| frictionless-d0.9-h0.0005 | 0.04340 | 0.05124 | 0.24641 | 0.34435 | 0.39659 | 0.01166 |

```bash
# Offline rescore after extracting the release archive:
python -m dexlab.incline_compare_score --superdex paired-incline/superdex --mujoco paired-incline/mujoco --output comparison.json
# New native run, only inside the documented bounded resource/research window:
python -m dexlab.incline_compare_run --manifest docs/evidence/incline-comparison/manifest.json --output /data/new-comparison --admission-only
python -m dexlab.incline_compare_run --manifest docs/evidence/incline-comparison/manifest.json --output /data/new-physical-comparison
```

Offline scoring needs NumPy; native execution needs the official FP64 packages. The historical MuJoCo archive hash, offline CRC and all 18 rescored cases were verified without rerunning physics. Zero-step admission was extended with gravity and plane-distance readbacks; exactly one positive-duration nine-case campaign was run. All failures remain. New motion records bind to acquisition commit `dd5b9c0`; geometric penetration is a later offline diagnostic, with no changed traces or thresholds.

For grasping, static support requires drift and hold-duration measurements; sliding interpretation first requires checking support continuity and rotation. This primitive does not qualify a complete grasp policy. Further work stays in [#113](https://github.com/huangkiki/Dexlab/issues/113) and [Issues](https://github.com/huangkiki/Dexlab/issues), rather than being presented as verified capability.

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.46.0/paired-incline-raw-v1.zip) · [SHA256](evidence/incline-comparison/archive.json)
