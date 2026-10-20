# Cutting fidelity and measured replay

The numeric GIFs display measurements from saved native states. They make the remaining differences easier to inspect; visual polish alone does not establish a reproduction of BladeMaster or real food.

## What changed after reading the paper closely

The [v2 paper](https://arxiv.org/html/2609.27342v2) separates material dynamics, persistent cutting history, contact and surface reconstruction. We audited those boundaries against the implementation:

| Paper detail | DexLab implementation and remaining gap |
| --- | --- |
| Eqs. 1–4: fixed reference interpolation and deformation update | Fixed reference stencils, fixed-corotated elasticity and MUSL update. CPU implementation; not the authors' GPU code. |
| Eqs. 5–6: directional contact work and blade-sweep side assignment | Cutting resistance uses positive advance work; geometric side assignment is separate from work progress. |
| Eqs. 7–9: persistent ternary history and compatible momentum exchange | Previous cut digits persist through later cuts and withdrawal. Exchange is antisymmetric and does not exchange mass. The independent scorer checks the resulting transfer graph. |
| Eqs. 10–16: proxy contact and equal/opposite tool reaction | Spherical material proxies, friction history and recorded reaction/impulse channels. The blade is guided; this is not the paper's freely rotating knife or robot controller. |
| Appendix, Eqs. 17–18: PIC/FLIP and MUSL momentum balance | Common blend ratio and fixed mass/code within a substep; tests and saved-state scoring check total momentum against recorded external impulses. A small residual establishes numerical consistency, not food accuracy. |
| III-F: linked reference volumes, Hermite data and local dual contouring | Tofu uses exposed material-cell faces. Banana generates each straight reference seam from the median recorded blade position during that active cut; surface rendering, numerical measurements and complete-task scoring share those recorded planes instead of fixed scoring regions. Opposing native histories expose cap triangles progressively, while compatible/unassigned regions within the same native mechanical component retain the bridge. A path that sweeps laterally by more than half a material spacing is rejected as a single-plane replay. Exact deformed cut geometry remains approximate. This is **not** the paper's Hermite/local dual-contouring reconstruction or an arbitrary-cut surface. |
| III-B: optional von Mises projection and Newtonian viscosity | The paper-parameter banana mode uses an independent perfect-J2 radial return in principal logarithmic strain; zero yield stress preserves every historical elastic record. Continuous-push tofu still uses synthetic `σᵥ=2ηD`, η=5 Pa·s; [model and results](cut-push.md). The paper does not publish its projection, hardening choice or banana viscosity, so this J2 algorithm is not author-code reproduction or food calibration. |
| III-G: compact active codes on GPU | Dense code storage on CPU. No GPU throughput claim. |

The earlier banana render applied 40 smoothing iterations and blended normals across cut rims. Its recorded maximum display-only vertex displacement was **2.358 mm**. Those operations rounded the cut ends. The refined renderer applies **no geometric smoothing**, marks the full cap rim and splits normals at sharp edges. Surface vertices still use saved particle motion and deformation; no separation displacement is added. The current tofu comparison uses a neutral gray scene and cream native particles with fixed reference floor markers. An orange rectangle projects the middle particle region; its contraction value comes from interior tetrahedra.

## Visible knife contact replaces the direct velocity input

[The historical two-cut tofu replay](tofu-comparison.md) re-enters the left kerf and pushes the left piece with the knife face before withdrawing. The push phase leaves cut history unchanged and never directly modifies material velocity. Recorded native knife poses, contact force and displacement drive the display. Author reference clips retain their original initial-velocity input; these final inputs are explicitly different.

[The latest tofu and banana showcase](cut-push.md) instead stays inside the last kerf, pushes directly and then withdraws. Its HUD shows |F|, Fx/Fz and all piece displacements from the initial state. Acceptance uses the final-cut end (3.30/5.30 s). Historical event measurements below keep their own baseline.

## Added crossed shallow cuts

The [cross-scoring task](tofu-scoring.md) computes contact and side assignment in the blade frame, withdraws, rotates 90° and makes a second shallow stroke. Native position, attitude and reaction are recorded; persistent histories and the lower transfer graph are checked separately. Depth is relative to the original upper surface, and the replay displays component count and base status. This extends guided orthogonal scoring, without reproducing the complete author knife-tip lateral path, free rotational dynamics or dual-contouring reconstruction.

## Same recorded state, before and after the display fix

| Previous display | Refined display |
| --- | --- |
| ![Rounded cut rims before the fix](../../evidence/cutting/refinement/same-state-before.png) | ![Sharp cut rims after the fix](../../evidence/cutting/refinement/same-state-after.png) |

Both frames use the **same original coarse record at 7.00 s**, verified by raw-state hashes. This isolates the display change; the new fine-sampling run is separate. <a href="_static/cutting/refinement/provenance.json">Frame provenance</a>.

## Reading the numbers

| Display | Definition |
| --- | --- |
| Cut opening, mm | Mean signed normal distance between two affine images of the same reference face: x for the first cross-scoring cut, y for the second. Only pairs with opposing nonzero native digits for that cut contribute. `--` means no eligible pair, not a zero-width cut. |
| Middle contraction / volume, % | Change in signed volume of fixed reference tetrahedra inside the middle third. Each complete native lattice cell contributes six tetrahedra; cells crossing a planned cut are excluded. Inversions are counted separately. The comparison GIF shows contraction -ΔV/V₀, while JSON retains signed volume change. |
| Interior volume, % | The same estimator summed over sampled piece interiors for banana or tofu halving. It does not measure the volume of the decorative skin. |
| After motion input, mm | Native equal-mass particle-centroid x displacement from the exact saved motion-start frame, ordered left to right. Knife push uses 4.00 s; historical impulse uses its original event time. |
| Knife on material Fx, N | Negative of the material-on-knife reaction x component at the completed substep; negative means the knife pushes material left. Excludes actuator, guide and board forces. |
| Knife reaction, N | Norm of the recorded material reaction on the knife. Guide, drive and board forces are separate. |

Each media folder contains `measurements.json` with units, definitions, frame indices and sample counts. GIFs slow playback for legibility; the clock and every displayed value retain their physical recorded time. `provenance.json` records frame mapping, source hashes and rendering hashes. MP4 and GIF use the same measured frames.

These estimates are new DexLab measurements, **not an exact implementation of the authors' unpublished metric sampling**. The paper reports 0.654/4.059 mm mean opening at first half-depth and 0.506/8.746% middle-volume contraction after two cuts for BladeMaster/CRESSim-MPM. Their full geometry, drive/contact settings, initial velocity and metric sampling remain [unresolved in #200](https://github.com/huangkiki/Dexlab/issues/200). No numerical three-method ranking follows from the adjacent videos.

## What the paper-parameter banana mode now qualifies

The banana force experiment in IV-C uses E=0.4 MPa, ν=0.45, density 1,100 kg/m³, yield stress 30 kPa, knife mass 0.1 kg, friction 0.2, Gc=700 J/m² and sharpness 0.9. The code now exposes that separate mode. Public banana GIFs and existing scores retain their original E=6 kPa, ν=0.35 elastic material, 0.2 kg knife and Gc=0.5 J/m²; they are not rewritten retroactively.

The paper states only a “von Mises-type plasticity projection”; it omits the projection formula, yield-stress convention, hardening law and source. DexLab declares the conventional equivalent stress `q=√(3/2)||s||`, radially returns principal logarithmic strain and retains volumetric strain. Analytical tests cover below-yield loading, yielded projection, unloading, superposed rigid rotation, positive Jacobians and nonnegative plastic dissipation. Every plastic record must carry per-substep dissipation telemetry. The [material protocol and source identities](https://github.com/huangkiki/Dexlab/blob/main/demos/banana-force/material-protocol.json) list every omitted field.

The independent [banana single-cut force experiment](banana-force.md) now runs 20 distinct particle samplings, one-factor timestep/contact sensitivity and an exact 64×-particle refinement at quarter grid spacing. Material, rigid-support and total resistance are separate; actuator and guide channels are excluded from resistance. The individual pre-support material peak is **0.8469 ± 0.1511 N**. Halving the timestep gives **0.621** normalized RMSE. The 64× run gives **2.051** RMSE and fails acceptance because it does not contact the support within 0.5 s, so the present force curve has not demonstrated numerical convergence. The authors' raw robot-force trace is unavailable; there is no real-force error or author-implementation equivalence result.

[#204](https://github.com/huangkiki/Dexlab/issues/204) still requires the linked-volume, Hermite-data and local dual-contouring reconstruction from paper III-F. The fruit is an authored shape rather than a scan, and the knife is a guided translating rigid body. Real-food calibration, the six-degree-of-freedom tool interface, robot pushing and force agreement remain unverified.

[Banana single-cut force](banana-force.md) · [Cross-scoring records](tofu-scoring.md) · [Two-cut tofu records](tofu-comparison.md) · [Separate banana task](banana-cutting.md) · [Three-column comparison](cutting-comparison.md)
