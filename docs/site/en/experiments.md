# Experiment catalog

The [16-case block force-limit experiment](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) is complete: 0.2/0.4 N fail retention, 0.8/10 N hold and release, including ±2 mm offsets. Numerical validity and task outcome are separate; no hardware-fidelity claim.

Keep existing code paths to preserve asset references, reproduction commands and historical evidence. Each experiment connects a question, configuration, raw record, independent score, report and failures.

| Experiment | Code | Question and status |
|---|---|---|
| [RSS wiping and assisted retention](rss-wiping.md) | [demos/rss-wiping/](https://github.com/huangkiki/Dexlab/tree/main/demos/rss-wiping/) | Compare the original and no-latch runs with fixed geometry; retain holding, slipping and cleaning results |
| [Sequential cutting and knife-driven pushing](cut-push.md) | [demos/tofu-knife-push/](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-knife-push/) | Three tofu pieces and four banana pieces; explain separation through recorded knife-contact forces, using synthetic materials |
| [Cross scoring](tofu-scoring.md) | [demos/tofu-cut/](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-cut/) | Two shallow cuts and a connected base; distinguish elastic rebound from native cut history |
| [Synthetic tofu halving](cutting.md) | [demos/tofu-cut/](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-cut/) | Single-cut CPU TLMPM, dynamic blade reaction and separation after withdrawal; independent BladeMaster reference |
| Apple stem grasp | [demos/apple-stem-grasp/](https://github.com/huangkiki/Dexlab/tree/main/demos/apple-stem-grasp/) | OpenArm + Wuji SDF-SDF frictional holding; distinguish default cases and historical perturbations |
| Robot cloth grasp | [demos/cloth-folding/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-folding/) | Pinch, lift and release; historical intersections retained; one repaired 9 s development case passes, robustness untested |
| Contact and drives | [demos/contact-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/contact-benchmark/) | Sliding, loading/unloading and transients; synthetic response is not hardware calibration |
| Basic cloth | [demos/cloth-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-benchmark/) | Stretch, drape, collision and falling folds; separate material/solver capabilities |
| PhysX | [demos/physx-contact/](https://github.com/huangkiki/Dexlab/tree/main/demos/physx-contact/) | Native rigid bodies, SDFs, joints and surface cloth; one success does not establish held-out performance |
| Genesis | [#42](https://github.com/huangkiki/Dexlab/issues/42) | Scoped rigid evidence in #42; [PBD cloth diagnostics](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md) retain failed momentum/grasp checks; tested frictional grasp profile rejected; equal-time response, connected folds and two held-out offsets recorded |

`src/dexlab/` contains shared task registration, scoring and recording. `scripts/` contains setup, rescoring, documentation and research tools. Share code only for real duplication or invariants; this is not a new general simulation framework.

## Apple control and dynamics

The right thumb/index pinch the stem while the left arm remains parked. Apple and stem form a 0.2 kg free rigid body. Known poses, IK and fixed joint targets drive the robot; the engine integrates actual object motion without attachment or object-position actuation. The continuous hold window is 11–14 s, with fruit contact allowed during approach.

The display camera follows recorded apple poses for playback only. There is no validated visual controller, stem fracture or hardware accuracy claim.

[Implementation and parameters](https://github.com/huangkiki/Dexlab/blob/main/docs/sdf-backends.md) · [Full inventory](https://github.com/huangkiki/Dexlab/blob/main/docs/inventory/README.md)

(apple-replays)=
## Continuous close-up records

These are development-scene replays at the original pinned versions, not held-out success rates. The cloth recording preserves the detected table-intersection failure.

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item-card} MuJoCo
![MuJoCo](../../../demos/apple-stem-grasp/media/mujoco-sdf.gif)
:::
:::{grid-item-card} SuperDex FP64
![SuperDex FP64](../../../demos/apple-stem-grasp/media/superdex-sdf.gif)
:::
:::{grid-item-card} PhysX
![PhysX](../../../demos/physx-contact/media/physx-sdf.gif)
:::
:::{grid-item-card} Cloth: geometric failure
![Cloth: geometric failure](../../../demos/cloth-folding/media/grasp.gif)
:::
::::

## Hardware acquisition preparation

The [protocol, empty template and log validator](https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.md) cover two UR7e arms and two identical CTAG2F90D grippers. Commands, measured feedback and independent references remain separate; unknown data stays unknown. The tool only reads files and does not control hardware. Format validity does not establish calibration.

## Friction response development

The [16-run planar report](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/FRICTION_RESPONSE.md) retains all paired MuJoCo 3.14.0 / SuperDex FP64 outcomes, measured initial states, speed-bin force ratios and costs. Every run passes existing plane checks, while low-speed resistance differs. This is not matched material calibration or an engine-accuracy ranking.

## Repaired cloth development case

![Continuous repaired pinch, lift and release](../../../demos/cloth-folding/media/compliance-grasp.gif)

One 9 s candidate passes the fixed v3 criteria; self penetration remains close to its limit. [Metrics, failed controls, video provenance and exact command](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.md). This does not replace the historical failure above or establish robustness.

## Initial Drake incline qualification

Official 1.57.0 / SAP / kLagged / hydroelastic: all six static and frictionless cases pass, three sliding cases fail, and the no-floor negative is rejected. The original coplanar failure is retained; 1 µm clearance belongs to a separate protocol. Reliable coverage under the new protocol remains unqualified. [报告 / Report](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md).

<!-- visual-research:start -->
(full-experiment-catalogue)=
## Full experiment and historical index

```{raw} html
<div class="experiment-grid">
<article class="experiment-card"><a href="banana-force.html"><img loading="lazy" src="_static/cutting/banana-force/force-protocol.svg" alt="Banana single-cut force: 20 samplings and 64× particles"></a><div class="card-copy"><h3><a href="banana-force.html">Banana single-cut force: 20 samplings and 64× particles</a></h3><p class="engines">CPU TLMPM / independent paper-value protocol</p><p>Is material resistance stable across sampling, timestep, contact scale and particle refinement?</p><p>Twenty baseline runs qualify numerically; the 64× case misses support contact within 0.5 s and gives 2.051 RMSE, so convergence and real-force accuracy remain unsupported.</p></div></article>
<article class="experiment-card"><a href="cut-push.html"><img loading="lazy" src="_static/cutting/tofu-cut-push/surface-poster.png" alt="Final cut directly into a side push: tofu and banana"></a><div class="card-copy"><h3><a href="cut-push.html">Final cut directly into a side push: tofu and banana</a></h3><p class="engines">CPU TLMPM / measured knife contact</p><p>Does visible blade-face contact drive the final piece apart?</p><p>Three tofu pieces and four banana pieces; the final cut transitions directly to a face push, displaying contact force and motion. Tofu adds Newtonian viscosity with retained elastic, half-step and no-push controls.</p></div></article>
<article class="experiment-card"><a href="cutting.html"><img loading="lazy" src="_static/cutting/tofu/surface-poster.png" alt="Historical: Synthetic tofu halving"></a><div class="card-copy"><h3><a href="cutting.html">Historical: Synthetic tofu halving</a></h3><p class="engines">CPU TLMPM / BladeMaster v2 reference</p><p>Do the two cut pieces move independently after withdrawal?</p><p>Three full-cut cases yield 50% mass pieces; negative controls stay connected. Force convergence and real-tofu calibration are unproven.</p></div></article>
<article class="experiment-card"><a href="cutting-comparison.html"><img loading="lazy" src="_static/cutting/tofu-sequential/surface-poster.png" alt="Historical: Two tofu cuts: three-method view"></a><div class="card-copy"><h3><a href="cutting-comparison.html">Historical: Two tofu cuts: three-method view</a></h3><p class="engines">CPU TLMPM / author reference videos</p><p>Can the left piece move independently after two cuts?</p><p>Two cuts form three pieces; native knife contact pushes the left piece, with measured force and displacement. Author clips use a final velocity input, so inputs differ.</p></div></article>
<article class="experiment-card"><a href="tofu-scoring.html"><img loading="lazy" src="_static/cutting/tofu-scoring/surface-poster.png" alt="Crossed shallow tofu cuts"></a><div class="card-copy"><h3><a href="tofu-scoring.html">Crossed shallow tofu cuts</a></h3><p class="engines">CPU TLMPM / guided orthogonal scoring</p><p>Does the lower bridge remain connected after crossing incisions?</p><p>Default and half-step cases form two shallow cuts while retaining one native component; the uncut control is rejected. Synthetic material, not food calibration.</p></div></article>
<article class="experiment-card"><a href="banana-cutting.html"><img loading="lazy" src="_static/cutting/banana/surface-poster.png" alt="Historical: Three sequential banana cuts"></a><div class="card-copy"><h3><a href="banana-cutting.html">Historical: Three sequential banana cuts</a></h3><p class="engines">CPU TLMPM / persistent cut history</p><p>Do subsequent cuts preserve earlier discontinuities?</p><p>Progressive separation and complete controls in the experiment record. Surface/particles share physical states; no real-banana calibration.</p></div></article>
<article class="experiment-card"><a href="libero-workflow.html"><img loading="lazy" src="_static/visual/libero-summary.png" alt="Native LIBERO: diagnosis and change"></a><div class="card-copy"><h3><a href="libero-workflow.html">Native LIBERO: diagnosis and change</a></h3><p class="engines">LIBERO / robosuite 1.4.0 / MuJoCo 2.3.7 · Newton / elliptic</p><p>How can an existing benchmark expose and validate a change?</p><p>Stale observations identified; timestep trials retain successes, failures and regressions.</p></div></article>
<article class="experiment-card"><a href="experience.html#normal-response"><img loading="lazy" src="_static/visual/catalogue/normal-response-v1.png" alt="Normal &amp; transient response"></a><div class="card-copy"><h3><a href="experience.html#normal-response">Normal &amp; transient response</a></h3><p class="engines">MuJoCo · SuperDex · historical PhysX</p><p>How do parameters change loading, unloading and transients?</p><p>Static calibration works; dynamics and mass transfer need separate checks.</p></div></article>
<article class="experiment-card"><a href="visual-comparisons.html#incline"><img loading="lazy" src="_static/visual/catalogue/error-cost.png" alt="Six-engine incline &amp; friction"></a><div class="card-copy"><h3><a href="visual-comparisons.html#incline">Six-engine incline &amp; friction</a></h3><p class="engines">MuJoCo · SuperDex · Genesis · Newton Physics · PhysX · Drake</p><p>Where do static, sliding and low-friction cases differ?</p><p>Fixed-profile outcomes and observation validity are separate; failures remain.</p></div></article>
<article class="experiment-card"><a href="results.html"><img loading="lazy" src="_static/visual/catalogue/sensitivity.png" alt="Impact &amp; contact onset"></a><div class="card-copy"><h3><a href="results.html">Impact &amp; contact onset</a></h3><p class="engines">MuJoCo · SuperDex</p><p>How do timestep, stiffness and impact phase affect transients?</p><p>Existing phase/stiffness sweeps; smaller steps do not automatically remove model differences.</p></div></article>
<article class="experiment-card"><a href="visual-comparisons.html#pinch"><img loading="lazy" src="_static/visual/catalogue/frame-060.png" alt="Fixture pinch, lift &amp; release"></a><div class="card-copy"><h3><a href="visual-comparisons.html#pinch">Fixture pinch, lift &amp; release</a></h3><p class="engines">Genesis · MuJoCo · SuperDex (separate protocols)</p><p>Why does the grasp hold or slip?</p><p>Genesis 0.4 N and 0.8 N configurations have different retention outcomes.</p></div></article>
<article class="experiment-card"><a href="experiments.html#apple-replays"><img loading="lazy" src="_static/visual/catalogue/superdex-sdf.png" alt="Apple-stem grasp · SDF contact"></a><div class="card-copy"><h3><a href="experiments.html#apple-replays">Apple-stem grasp · SDF contact</a></h3><p class="engines">MuJoCo · SuperDex · historical PhysX</p><p>Can a grasp maintain contact on complex geometry?</p><p>Native continuous replays and historical independent checks; cohorts stay separate.</p></div></article>
<article class="experiment-card"><a href="coverage.html"><img loading="lazy" src="_static/visual/catalogue/cloth-poster.png" alt="Cloth mechanics &amp; robot grasp"></a><div class="card-copy"><h3><a href="coverage.html">Cloth mechanics &amp; robot grasp</a></h3><p class="engines">MuJoCo · SuperDex · Newton Physics · Genesis · historical PhysX</p><p>When do deformation, contact and retention fail?</p><p>Historical compliant-grasp frame; mechanics, drop and grasp retain separate protocols and failures.</p></div></article>
<article class="experiment-card"><a href="experience.html#mass-size-transfer"><img loading="lazy" src="_static/visual/catalogue/contact-transfer-v1.png" alt="Mass / size transfer"></a><div class="card-copy"><h3><a href="experience.html#mass-size-transfer">Mass / size transfer</a></h3><p class="engines">MuJoCo · SuperDex</p><p>Do fixed parameters transfer to nearby scenes?</p><p>30 historical transfer records, 0/30 joint passes; failures guide selection.</p></div></article>
<article class="experiment-card"><a href="experience.html#transient-cost"><img loading="lazy" src="_static/visual/catalogue/response-cost-v1.png" alt="Response error &amp; cost"></a><div class="card-copy"><h3><a href="experience.html#transient-cost">Response error &amp; cost</a></h3><p class="engines">MuJoCo · SuperDex</p><p>What does lower error cost?</p><p>27 records separate native computation, recording and scoring costs.</p></div></article>
<article class="experiment-card"><a href="experience.html#framework-path"><img loading="lazy" src="_static/visual/catalogue/contact-parameters.png" alt="Native &amp; framework paths"></a><div class="card-copy"><h3><a href="experience.html#framework-path">Native &amp; framework paths</a></h3><p class="engines">MuJoCo / MJWarp · Newton / Isaac Sim</p><p>Why can matching cores still produce different trajectories?</p><p>GPU field differences remain after CPU alignment; parameter-map thumbnail is not trajectory evidence.</p></div></article>
</div>
```

**Pending / incomplete:** broader pushing, in-hand rotation, active folding and grasp transfer remain in their existing Issues. Existing knife-driven pushing has its own protocol; folded drop is not active folding.

## What we already know

(experiment-highlight-incline)=
### Six-engine incline: shared conditions, different responses

A 40 mm, 64 g cube; static, sliding and nominal-zero-friction conditions at three timesteps. Curves and replays retain the original passes, failures and invalid records.

![Six-engine incline: shared conditions, different responses](../../../docs/evidence/visual/incline-static-0.001.png)

![Six-engine incline: shared conditions, different responses — curves](../../../docs/evidence/visual/incline-static-0.001-curves.svg)

[Synchronized replay, full-rate curves, parameters and original evidence](incline)

(experiment-highlight-normal)=
### Normal response: change parameters or the solver?

The same MuJoCo fixture moves from about 80 kN/m toward the synthetic 20 kN/m target. Inspect loaded-window indentation, then the complete unloading trace; success belongs to the stated checks and conditions.

![Normal response: change parameters or the solver?](../../../docs/evidence/visual/normal-calibration.png)

![Normal response: change parameters or the solver? — curves](../../../docs/evidence/visual/normal-summary.en.svg)

[Synchronized replay, full-rate curves, parameters and original evidence](normal)

(experiment-highlight-pinch)=
### Pinch: 0.4 N slips, 0.8 N holds

The same Genesis fixture and object, changing the finger-joint force limit. Compare complete closing, lifting, holding and release, with an open-gripper negative control retained.

![Pinch: 0.4 N slips, 0.8 N holds](../../../docs/evidence/visual/pinch-summary.png)

![Pinch: 0.4 N slips, 0.8 N holds — curves](../../../docs/evidence/visual/pinch-retention-curves.svg)

[Synchronized replay, full-rate curves, parameters and original evidence](pinch)

(experiment-highlight-libero)=
### LIBERO: native task, timestep control and observation fix

Same actions, initial state, Panda and native success; original 2 ms versus unqualified 1 ms control. Heldout task success stays 10/10, screens change from 5/10 to 3/10, and cost doubles. Policy effects of observation refresh remain unverified.

![LIBERO: native task, timestep control and observation fix](../../../docs/evidence/visual/libero-summary.png)

![LIBERO: native task, timestep control and observation fix — curves](../../../docs/evidence/visual/libero-demo0-curves.svg)

[Synchronized replay, full-rate curves, parameters and original evidence](libero)

## Which engines and solvers are compared?

| Engine | Roles in registered profiles (not peer algorithms) | Experiment versions and paths |
| --- | --- | --- |
| **MuJoCo** | Constraint method: CG (nonlinear) · Newton · PGS<br>Friction cone: elliptic · pyramidal<br>Integration: Euler · implicitfast<br>Unresolved role/identity: SolverMuJoCo; algorithm unqualified | 3.11.0, 3.14.0, 3.15.0; native / historical paths in matrix |
| **SuperDex** | Deformable implementation: experimental-shell<br>Outer nonlinear: BFGS · Newton · SR1<br>Inner linear: ASYNC_CG · AUGMENTED_CG · CG · CUDA_CG · CUDA_GMRES · EXPERIMENTAL_CUDA_SPARSE_CHOLESKY · EXPERIMENTAL_CUDA_SPARSE_LDLT · EXPERIMENTAL_CUDA_SPARSE_LU · GMRES · LDLT · LU · MINRES · PARALLEL_CG<br>Linear selection: AUTO<br>Friction regularization/model: C1_REGULARIZED · CINF_REGULARIZED<br>Precision in label: FP64 | 1.0.0; native / historical paths in matrix |
| **Genesis** | Deformable implementation: PBD<br>Constraint method: CG (nonlinear) · Newton<br>Friction cone: elliptic · pyramidal<br>Contact model: Signorini · convex<br>Coupling path: rigid coupling<br>Integration: approximate_implicitfast | 1.4.3; native / historical paths in matrix |
| **Newton Physics** | Implementation/system: Featherstone · Kamino · SemiImplicit · VBD · VBD compliant · VBD legacy · XPBD<br>Deformable implementation: ImplicitMPM · Style3D<br>Dynamics backend: DVI · PADMM<br>Integration: Euler<br>Update/budget options: 100 sweeps | 1.6.1 / Warp 1.18.0, 1.7.0.dev0 @ 2dee3234; native / historical paths in matrix |
| **PhysX** | Deformable implementation: surface cloth<br>Constraint method: PGS · TGS<br>Friction regularization/model: patch friction<br>Update/budget options: external forces every iteration · friction every iteration<br>Unresolved role/identity: historical readback incomplete (#126) · pending qualification | 5.9.0; native / historical paths in matrix |
| **Drake** | Constraint method: SAP<br>Contact model: hydroelastic · point<br>Discrete contact approximation: kLagged · kSap · kSimilar<br>Unresolved role/identity: not qualified | 1.57.0; native / historical paths in matrix |

Native and framework **MJWarp** are separate paths with their actual core identified. Newton Physics is an engine project; Newton is also an algorithm name. Tested SuperDex BFGS/SR1 with assembly period=1 execute Newton-equivalent steps; configuration names are not independent algorithm counts.

This is a research inventory including failures and unqualified entries. Execution, CPU/GPU, precision, full profiles and unsupported reasons:  [完整矩阵 / Full matrix](coverage.md)。

Roles interpret recorded names within each engine, not identical mathematical problems or evidence that every combination ran. AUTO is a selection policy; missing identities are not filled from defaults.

**Comparison boundary:** distinguish system-profile selection from controlled algorithm attribution. Read record integrity, numerical consistency, physical references and task outcomes separately; original scores and failure denominators are unchanged. [Roles and evidence guide](solver-taxonomy.md)。

Thin-feature SDF geometry/response qualification remains [#178](https://github.com/huangkiki/Dexlab/issues/178); cloth material, collision/coupling and grasp baselines remain [#179](https://github.com/huangkiki/Dexlab/issues/179). Existing development passes are not calibrated cross-engine material comparisons.

**MJWarp path comparison (MuJoCo core)**

| Runtime path | Actual physics core | Solver / contact path | Task acceptance |
| --- | --- | --- | --- |
| Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / Newton contacts | [not-run](coverage.md) |
| Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / MJWarp contacts | [not-run](coverage.md) |
| Native matched core / vendor Warp1.16.0; original and four-field aligned | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / MJWarp contacts | [not-run](coverage.md) |

Model/clock diagnostics already exist; task acceptance retains the matrix state. [Path differences #152](https://github.com/huangkiki/Dexlab/issues/152) remain a separate research question.

<!-- visual-research:end -->
