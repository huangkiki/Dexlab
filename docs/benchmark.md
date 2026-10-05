# Benchmark protocol

[English](benchmark.md) | [简体中文](benchmark.zh-CN.md)

DexLab separates **controlled physics comparisons** from **task robustness**. The former requires shared physical response targets, control laws and boundary conditions. The latter permits backend-specific configuration, frozen before evaluation with tuning conditions disclosed. The current apple experiment belongs to the latter; it is not calibrated material validation or an engine-accuracy ranking.

## Apple task: executable first layer

[apple-stem-v1.json](../benchmarks/apple-stem-v1.json) was committed before execution: 20 development, 10 regression and 100 test cases, with disjoint IDs and seeds. Each case stores explicit values consumed by both backends. Engine RNG equivalence is unnecessary. Default policies come from v0.1.0 and were not retuned on these cases.

| Parameter | Distribution and units | Source |
|---|---|---|
| Apple mass | Uniform 0.16–0.24 kg | Declared engineering perturbation |
| Initial horizontal x and y offset | Independently uniform −5–5 mm | Declared engineering perturbation |
| Initial rotation about vertical | Uniform −10–10° | Declared engineering perturbation |
| Geometry, actuation, contact settings | Frozen backend-specific defaults | [Backend implementation](sdf-backends.md) |

These are not measured hardware distributions. The base and table remain fixed; changing apple mass changes its inertia consistently. Both paths first settle the apple for 3 seconds in SuperDex at a fixed 2 ms timestep, then plan from the known settled pose. MuJoCo receives the model from this preparation and retains its original one-time alignment. This is not an exclusively MuJoCo preparation chain or a controlled comparison replaying identical absolute joint commands.

```bash
# Unperturbed baseline; use a new output directory to preserve evidence
.venv/bin/python -m dexlab.benchmark run --case baseline \
  --output demos/apple-stem-grasp/runs/benchmark-baseline
# Ten paired regression cases: twenty full 14-second episodes
.venv/bin/python -m dexlab.benchmark run --split regression \
  --output demos/apple-stem-grasp/runs/benchmark-regression
# Once the policy is frozen: one hundred paired test cases, two hundred episodes
.venv/bin/python -m dexlab.benchmark run --split test \
  --output demos/apple-stem-grasp/runs/benchmark-test
# h, h/2 and h/4 for each backend, on the same unperturbed scene
.venv/bin/python -m dexlab.benchmark run --case baseline --timestep-sweep \
  --output demos/apple-stem-grasp/runs/benchmark-timestep
```

Choose `--backend mujoco|superdex|all` or one case in the current split, such as `--case regression-000`. The per-episode timeout defaults to 1200 seconds and can be set with `--timeout`. Timeouts and crashes remain failed outcomes with logs. Wall time generally exceeds simulated time.

`--resume` skips completed episodes only when cases, source, environment, selection and recorded artifact hashes are unchanged. Unfinished directories are never automatically restarted: inspect the original process, preserve interrupted evidence and use a new output directory. Outputs include `run.json`, the suite snapshot, per-episode `job.json`, `result.json`, `episode.log`, raw physics arrays and independent scoring. Every scheduled case stays in the denominator of `report.json`, including pending, runtime_error and timeout entries; only a completed report is a final result.

CLI exit 0 means every episode was scored, **not that every grasp succeeded**. Reports retain all case outcomes and failed checks, with 95% Wilson success-rate intervals. Do not select only successful videos or average only successful trials. Test outcomes must not tune the same policy version; redesign requires a new protocol version.

New batches store MuJoCo binaries as lossless, content-addressed 1 MiB gzip chunks. Identical chunks share disk inodes across episodes, while each record has its own complete `model-chunks/` directory and manifest; copying a record to another filesystem remains self-contained. Ordered reconstruction must match the original full SHA-256 before the raw binary is removed. Never edit a hash-named chunk in place. Independent verification and jitter analysis also accept raw MJB and legacy `model.mjb.gz`. Physical arrays and failures are retained. Runs stop before starting a new scene if less than 4 GiB is free.

## Completed experiments

All ten paired regression cases were scored, with no runtime errors or timeouts. The default MuJoCo configuration passed **1/10** and SuperDex passed **10/10**; the respective 95% Wilson intervals are **1.8–40.4%** and **72.2–100%**. Failures include hold drift, lost support and excessive penetration; failed episodes remain in the denominator. The separate frozen 100-case test set has not completed evaluation. Its first batch was interrupted after negative scientific-notation offsets exposed an argument-transport error before simulation; all records are retained. The fix changes argument encoding only, without retuning the policy, cases or acceptance thresholds. The full paired suite is rerun in a new directory.

| Backend | Timestep | Full acceptance | Maximum hand penetration, full episode |
|---|---:|---|---:|
| MuJoCo | 0.5 ms | Pass | 0.15918 mm |
| MuJoCo | 0.25 ms | **Fail: excessive penetration** | 1.15241 mm |
| MuJoCo | 0.125 ms | Pass | 0.17969 mm |
| SuperDex | 2 ms | Pass | 0.45226 mm |
| SuperDex | 1 ms | Pass | 0.45167 mm |
| SuperDex | 0.5 ms | Pass | 0.45200 mm |

The timestep study runs the same default scene once per configuration; it does not estimate success rates. These results establish neither monotonic convergence nor an engine as physical ground truth. The original 1 mm penetration limit was not changed to accommodate failures.

[All regression records](../demos/apple-stem-grasp/evidence/benchmark/regression-v1.json) · [All timestep records](../demos/apple-stem-grasp/evidence/benchmark/timestep-v1.json). Reports include individual outcomes, parameters, timing, environment and raw-file hashes. Full arrays and models remain in their run directories; the report alone cannot independently rescore physics or replay trajectories.

```bash
# No simulation: check complete batch identities and file hashes, retaining failures
.venv/bin/python -m dexlab.benchmark report \
  demos/apple-stem-grasp/runs/benchmark-regression --output regression-report.json
```

Collection rejects incomplete batches, changed evidence, pass flags inconsistent with checks, and aggregate reports inconsistent with individual records. Output cannot overwrite an existing file. Historical batches retain their original source hashes; new batches also archive Python source snapshots and check their contents during resume and collection. Collection verifies archive integrity rather than recalculating physical scores.

## Measurement and timestep

Acceptance retains the original clearance, continuous two-pad support, hold drift, penetration and momentum-balance thresholds. The independent scorer receives expected mass from the frozen case, not the runtime's claimed mass. Rechecking nondefault mass requires `verify_sdf_grasp.py RUN --expected-mass-kg MASS`.

- Record every physics step; unavailable measurements remain unknown. The hold window remains [11, 14) seconds.
- Wrist-relative drift and centered RMS are not cumulative material slip. The existing SuperDex normal-force column is a placeholder and must not estimate friction capacity.
- Preparation includes SDF construction, settling, robot loading, planning and display-model construction. `physics_step_seconds` times native integration calls only. Execution including control, observations and export is recorded separately; headless rendering time is zero.
- MuJoCo uses h=0.5 ms and SuperDex h=2 ms, each followed by h/2 and h/4. MuJoCo's existing 5 ms contact time constant does not trigger its 2h lower-bound adjustment in this sweep. Targets are sampled at physics steps and moving-target velocity is differenced, so this measures task time discretization rather than isolated solver error.
- A smaller timestep is a numerical reference, not physical ground truth. Cross-engine speed/error comparisons additionally require matching physical response targets and tolerances.

## Mechanistic contact experiments

The three implemented development tasks, 38 completed runs and known failures are documented in [contact-mechanics experiments](../demos/contact-benchmark/README.md). Nominal profiles remain uncalibrated; formal held-out evaluation has not started.

[Issue #10](https://github.com/huangkiki/Dexlab/issues/10) covers indentation/unloading, planar sliding, two-pad cylinder load sweeps and complete release. Include expected successes and expected failures. For ideal horizontal normals with Coulomb friction, no geometric jamming and no other support, static load capacity is `mu * (N_left + N_right)`; excess load should slip. This expression must not be applied blindly to compliance, torsional friction or complex geometry.

Controlled comparisons fix source geometry, mass/inertia, physical control laws, update frequency and limits. Fit contact response to independent indentation/sliding targets rather than copying similarly named parameters. Recheck penetration against shared reference geometry; record actual tangential relative velocity, normal load and observation coverage. Fruit-body contact is allowed, while stem support and fruit-assisted support are reported separately.

## Backends and solvers

[Issue #4](https://github.com/huangkiki/Dexlab/issues/4) qualifies UniSim equivalence; [PhysX #5](https://github.com/huangkiki/Dexlab/issues/5) and [Newton/other backends #11](https://github.com/huangkiki/Dexlab/issues/11) require separate runtime evidence.

Scope includes the pinned UniSim declarations for MuJoCo/mjbatch, SuperDex, MJWarp, Newton, Motrix, Drake, Genesis, IsaacGym and IsaacSim, plus availability audits of Newton's rigid-capable MuJoCo, XPBD, VBD, Featherstone, SemiImplicit and Kamino solvers. Identify engines, integrators, constraint solvers and wrappers separately. Newton SolverMuJoCo is not independent non-MuJoCo physics. Missing SDKs, SDF, joints or contact readback cannot silently fall back or count as passes.

## Cloth experiments

Seven native solver profiles have published 105 frozen held-out episodes: 52 protocol passes and 53 failures. Nominal materials are not calibrated across solvers. The robot cloth grasp passed its original protocol, but subsequent independent geometry checks found table intersections in 176 of 225 saved frames (maximum interior depth 3.00 mm). Physical repair and bimanual folding remain unvalidated. [Results and reproduction](../demos/cloth-benchmark/README.md) · [Robot cloth grasp](../demos/cloth-folding/README.md).

[Issue #12](https://github.com/huangkiki/Dexlab/issues/12) shares versioning, evidence and run management with rigid tasks, but uses separate scores. Initial experiments: pinned-edge extension/unloading, gravity sag and draping/contact over an analytic obstacle, with self-collision where supported.

Record topology/resolution, areal density/total mass, thickness, stretch/shear/bending/damping, rest configuration and pins. Measure deformation, sag, residual motion, penetration, constraint error and cost, including temporal and spatial refinement. Calibrate different constitutive responses; a volumetric solid is not automatically thin-shell cloth. Physical fidelity still requires the material and sensor measurements in [#6](https://github.com/huangkiki/Dexlab/issues/6).

## Method references

[ContactBench](https://arxiv.org/abs/2304.06372) separates contact models and numerical approximations; [SimBenchmark](https://leggedrobotics.github.io/SimBenchmark/) compares speed/error curves; [GAUGE](https://internrobotics.github.io/GAUGE/) motivates measurement-grounded evaluation. DexLab declares its own case ranges and acceptance criteria; these are not hardware findings supplied by those projects.

The [transient development comparison](../demos/contact-benchmark/TRANSIENT_RESPONSE.md) fixes K, D and load history, then compares three timesteps. Six of 12 candidates pass combined checks and all failures remain; these deterministic checks are not random success-rate trials.
