# Research experience: from existing experiments to the next check

Each experience retains conditions, observations, explanation, advice, limits and evidence. A versioned index generates this page and checks report/data-summary SHA-256 hashes. Download raw trajectories from the immutable releases linked in each report and verify their manifests. This page adds no new holdout or reliable coverage.

<!-- research-experience:start -->

(normal-response)=
## Static calibration works; mass transfer still needs checks

**Conditions:** A 40 mm cube, 0.2 kg, 0.5 ms; 2/4/6/−1 N loading. The 20 kN/m response is a synthetic target.

**Observation:** MuJoCo initially measured about 80 kN/m and approached 20 kN/m after calibration. Fixed parameters gave 10.01/40.04 kN/m at 0.1/0.4 kg; the predeclared mass conversion gave 20.04/19.93 kN/m.

**Explanation and evidence level:** Established in this fixture: reference-acceleration response depends on mass and impedance. Equal parameter names do not establish equal material stiffness across engines.

**Advice:** Check effective response on declared fitting loads, apply an explicit conversion hypothesis, and validate other loads and masses independently.

**Limits:** This constant-impedance, four-point face-contact fixture does not supply a universal geometry formula or measured material calibration. Historical PhysX identity remains missing under the #126 audit.

**First check in a new scene:** Check inertia, contact count, native parameters and force/displacement slope; retain the separating-load segment.

**Starting candidate:** MuJoCo 3.11.0 / native Newton: reported solimp=[.9,.9,.001,.5,2], fitted solref stiffness −2499.883; read the complete damping and mass rule from the frozen manifest. SuperDex 1.0.0 FP64 and historical PhysX have separate profiles.

**Cost:** 17 historical records: 11 passed, 6 failed; includes fitting and validation, not one comparative cohort.

**Evidence:** [demos/contact-benchmark/NORMAL_RESPONSE.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/NORMAL_RESPONSE.md) · [demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md) · [benchmarks/contact-normal-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-normal-v1.json)

(transient-cost)=
## Similar static response does not imply similar transients or cost

**Conditions:** A 0.2 kg cube; synthetic K=20 kN/m and D=40 N·s/m; 0.5/0.25/0.125 ms. Transients include historical PhysX; repeated costs use MuJoCo 3.14 / SuperDex 1.0 FP64.

**Observation:** Low-impedance MuJoCo transient RMS is 2.771→1.327→0.617 µm, versus 120.654→76.542→67.765 µm at high impedance. The cost cohort passes 9/9 versus 0/9; SuperDex passes 0/9, including tension failures. Three historical PhysX transient cases pass.

**Explanation and evidence level:** Established: decreasing the step does not generally remove these configuration/model differences. This SuperDex damping depends on elastic contact force and is not the same law as a constant linear damper.

**Advice:** Accept static response, transients, no tension and cost together; check the contact law before a timestep sweep.

**Limits:** These are synthetic targets. Cost repetitions rebuild scenes within one process, not independent-process repeatability or a universal ranking. Historical PhysX lacks core telemetry and is not a current SDK recommendation.

**First check in a new scene:** Freeze the response target, damping definition and load epochs; record native stepping and observation costs separately.

**Starting candidate:** MuJoCo 3.14 / native Newton: low impedance d=.001 and direct solref=[−24975,−49.95] are a starting candidate for this target. Use the frozen manifest and revalidate transfers.

**Cost:** 27 cost records: 9 joint passes, 18 failures. Smaller steps add calls; observation overhead is not solver cost.

**Evidence:** [demos/contact-benchmark/TRANSIENT_RESPONSE.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/TRANSIENT_RESPONSE.md) · [demos/contact-benchmark/RESPONSE_COST.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/RESPONSE_COST.md) · [docs/evidence/response-cost-v1.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/response-cost-v1.json) · [benchmarks/contact-response-cost-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-response-cost-v1.json)

(mass-size-transfer)=
## Passing one scene does not establish transfer

**Conditions:** Mass 0.12–0.28 kg, half-size 15–25 mm, three fixed response profiles and ten conditions at 0.5 ms.

**Observation:** All 30 records completed; 1/30 passes engineering checks, 0/30 passes transient/joint checks. No mass or area compensation was applied.

**Explanation and evidence level:** Established: these fixed profiles fail this transfer set. The evidence does not attribute every failure to a solver algorithm.

**Advice:** Check mass, size and contact-topology sensitivity first. Declare any parameter conversion before freezing new holdouts.

**Limits:** This transfer set was frozen after development and before outcomes, not a hidden blind test. Old records cannot become unseen holdouts for new tuning.

**First check in a new scene:** Start near the target mass/geometry and check inertia, contact count, displacement response and tension.

**Starting candidate:** Use the MuJoCo 3.14 high/low-impedance and SuperDex 1.0 FP64 profiles in contact-transfer-v1 as failed baselines. No configuration is qualified for direct transfer across this range.

**Cost:** All 30 trajectories remain; report additional tuning and readmission costs separately.

**Evidence:** [demos/contact-benchmark/TRANSFER.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/TRANSFER.md) · [docs/evidence/contact-transfer-v1.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-transfer-v1.json) · [benchmarks/contact-transfer-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-transfer-v1.json)

(physx-observation)=
## Separate PhysX physical error from observation error

**Conditions:** PhysX SDK 5.9.0 / native CPU FP32: PGS, PGS friction-every-iteration, TGS and TGS external-forces-every-iteration on nine frozen incline cases.

**Observation:** Pass counts are 7/9, 7/9, 3/9 and 3/9; 13 positives fail numerical checks; all four negatives are valid and rejected. Moving TGS cases have state/impulse residuals of 1.09e−7 to 1.96e−7 N·s.

**Explanation and evidence level:** Established: impulses and velocities use separate native FP32 operation paths, and independent repeats reproduce records. Every residual is not yet uniquely decomposed. Initializing inertia before disabling collision corrected the earlier negative-control mass. New offline decomposition reduces the PGS direction residual using native normals; native mass/gravity still do not remove TGS exceedances. Original scores are unchanged.

**Advice:** Check mass, impulse epochs and FP32 readbacks before tuning. #163 preserves old checks and owns independent diagnosis, a frozen new protocol and holdouts.

**Limits:** Failure in four finite profiles does not establish PhysX unsuitability. GPU, Isaac and arbitrary penetration scenarios are not covered; no general tuning-success claim follows.

**First check in a new scene:** Check N=mg cosθ and the static-friction inequality first, then sliding acceleration and per-step impulses.

**Starting candidate:** Native SDK 5.9.0 PGS is one development starting point for this incline, not a global optimum. Use the frozen mass, step, iterations and offsets; do not transplant same-named framework defaults.

**Cost:** 40 formal records, 10.782 s total acquisition service time; instrumented correctness cost, not a throughput ranking.

**Evidence:** [docs/physx-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) · [docs/physx-incline-protocol.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-protocol.md) · [docs/evidence/physx-incline/profiles.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/profiles.json) · [docs/evidence/physx-incline/readback-interpretation.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/readback-interpretation.json) · [docs/physx-precision-diagnostics.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.md) · [docs/physx-precision-diagnostics.zh-CN.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.zh-CN.md) · [docs/evidence/physx-incline/precision-pgs.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/precision-pgs.json) · [docs/evidence/physx-incline/precision-tgs.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/precision-tgs.json)

(pinch-load)=
## Pinch diagnosis must explain load, slip and release

**Conditions:** A native Genesis finite fixture, four force caps and ±2 mm initial offsets: 16 fixed cases. Separate MuJoCo cube-pinch and robot SDF historical scenes also exist.

**Observation:** Genesis cannot retain the object at 0.2/0.4 N caps; 0.8/10 N holds and releases. This result is limited to the reported fixture and drive.

**Explanation and evidence level:** Established: drive caps change load capacity. Friction/torque balance starts diagnosis; small contact-force residuals alone do not establish grasp success.

**Advice:** Start with object load, each side’s normal force and effective friction, then check finite pads, slip and release alongside actual drive output.

**Limits:** This is not a unified cross-engine pinch ranking. #145 inertia/frames and #132→#134 shared-drive/594-episode research remain independently open.

**First check in a new scene:** Validate no-pinch/low-force negatives, then the full lift, hold, offset and release trajectory; inspect actual object motion.

**Starting candidate:** Reuse the native version and complete drive parameters in the Genesis force-limit report. For robot grasping, start from the verified MuJoCo/SuperDex 14 s SDF case and requalify new geometry.

**Cost:** Report force-cap sweeps, drive and geometry preparation separately; historical robot success does not provide free admission of a new task.

**Evidence:** [docs/force-limit-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) · [docs/pinch-load-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md) · [demos/apple-stem-grasp/README.md](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) · [docs/pinch-boundary-roadmap.md](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-roadmap.md)

(six-engine-incline)=
## Use one physical question to expose configuration differences

**Conditions:** Native incline cohorts: MuJoCo 3.15.0, SuperDex 1.0.0, Genesis 1.4.3, Newton Physics 1.6.1, PhysX 5.9.0 and Drake 1.57.0; each records contact law, precision and applicable profiles.

**Observation:** All six have positive, negative and failed evidence. Genesis floors nominal-zero contact friction to .01; SuperDex BFGS/SR1 execute Newton-equivalent steps under assembly every step.

**Explanation and evidence level:** Established effective-parameter/execution-path differences change the interpretation of same-named profiles. Initial pass rates do not replace equal-budget tuned comparisons.

**Advice:** Filter candidates by sticking/sliding, low friction and contact scale; inspect invalid records, physical error and cost together.

**Limits:** Cohort protocols and admission scope remain separate. The full matrix maps research scope, not universal rank. Numerical work remains in #157/#159/#163/#165.

**First check in a new scene:** Check the target static-friction threshold and frictionless control first, then sliding, rotation and force/state consistency.

**Starting candidate:** Select nearby conditions with valid observations from the full matrix; take exact settings from each frozen protocol. No new coverage-v1 reliability admission is claimed.

**Cost:** Compare cost only under matched conditions, budgets and observation paths; separate initialization and native stepping.

**Evidence:** [docs/mujoco-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) · [docs/superdex-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) · [docs/genesis-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) · [docs/newton-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) · [docs/physx-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) · [docs/drake-contact-paths-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md)

(framework-path)=
## The same core still requires effective-state checks after conversion

**Conditions:** Matched MuJoCo/MJWarp 3.11.0 and Warp 1.16.0; native versus an Isaac Sim 6.1 source-tag build, 200-step cube support/no-floor diagnostics.

**Observation:** Four of 55 selected GPU fields differ despite equal CPU models. Aligning them still fails the original momentum check and does not reproduce the framework trajectory; three independent native processes record identical steps.

**Explanation and evidence level:** Established: matching imported models does not guarantee matching effective GPU models; these four fields do not explain the full divergence. CPU out-of-bounds contact readback is corrected; unavailable values cannot be interpreted as zero.

**Advice:** Save source assets, intermediate models and effective parameters; align control epochs, contact paths, inertia and capacity before comparing.

**Limits:** Attribution covers isolated factors only, not all internal state or a unique framework cause. Latest-native, full incline/collision/pinch and holdouts remain in #152.

**First check in a new scene:** Compare no-contact trajectories first, then model/state around the first divergence and native contact addresses.

**Starting candidate:** This matched version is for attribution. Selection still separates latest stable native from official compatible framework versions; reuse the public default/aligned protocols.

**Cost:** Retain initialization, observation, cache and independent-process costs; 200-step diagnostics do not establish long-grasp throughput.

**Evidence:** [docs/framework-mjwarp-diagnostics.md](https://github.com/huangkiki/Dexlab/blob/main/docs/framework-mjwarp-diagnostics.md) · [docs/evidence/framework-mjwarp/matched-core.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/framework-mjwarp/matched-core.json) · [docs/evidence/framework-mjwarp/archive.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/framework-mjwarp/archive.json)

(libero-workflow)=
## LIBERO: native success does not imply credible contacts

**Conditions:** Official cream-cheese-to-basket, Panda / robosuite 1.4.0 / MuJoCo 2.3.7 Newton elliptic; 20 Hz control, original 2 ms step.

**Observation:** Original and 1 ms heldout action executions both complete 10/10 tasks; numerical screens pass 5/10 and 3/10, with about double stepping cost. Five settling steps change one end-effector position component by 4.481 mm while the old observation is retained.

**Explanation and evidence level:** Observation assignment omission is verified. Positive contact time constants couple to the timestep safety floor in pinned source. Smaller steps do not consistently help; the mechanism behind 12.163 mm floor overlap continues in #174.

**Advice:** Refresh observations first; distinguish controller goals, actuator output and contact forces. Retain failures and localize controlled experiments to the actual contact. No new physics profile is recommended.

**Limits:** Demonstration action execution only: no fixed-policy closed-loop effect, real-material accuracy or mid-episode restore qualification. Holdouts are ten demonstrations of one task, not new-task generalization.

**First check in a new scene:** Check initial state/controller reset, post-settling observation, native contact pair/epoch/frame, effective parameters and unchanged native success.

**Starting candidate:** Retain LIBERO 8f1084e / robosuite 1.4.0 / MuJoCo 2.3.7 defaults with the reversible observation-refresh patch; 1 ms remains an unqualified comparison.

**Cost:** Eight candidates (six physical configurations and two audits), three development and ten heldout demos; all 40 current-protocol records retained. Heldout native stepping totals 2.239 s / 4.481 s; full recording costs remain in the ledger.

**Evidence:** [docs/evidence/libero/summary.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/summary.json) · [docs/evidence/libero/patch-validation.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/patch-validation.json) · [demos/libero-contact/protocol.json](https://github.com/huangkiki/Dexlab/blob/main/demos/libero-contact/protocol.json) · [docs/evidence/libero/process-repeat.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/process-repeat.json) · [docs/evidence/libero/budget.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/budget.json) · [docs/evidence/libero/resources.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/resources.json) · [docs/evidence/libero/native-package-integrity.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/native-package-integrity.json) · [docs/evidence/libero/history.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/history.json) · [docs/evidence/libero/archive.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/archive.json)

<!-- research-experience:end -->
