# Three sequential banana cuts

A force-driven blade descends and withdraws at three positions, cutting a curved peeled-banana shape into four pieces. Surface and particle views replay the same physical states. Pause, scrub or switch representations to inspect each cut.

```{raw} html
<section class="cutting-player" aria-label="Three banana cuts">
<header><h3>Three banana cuts</h3><div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana/surface.mp4" data-poster="_static/cutting/banana/surface-poster.png" aria-pressed="true">Surface</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana/particles.mp4" data-poster="_static/cutting/banana/particles-poster.png" aria-pressed="false">Particles</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/banana/surface-poster.png" aria-label="Three banana cuts"><source src="_static/cutting/banana/surface.mp4" type="video/mp4"><a href="_static/cutting/banana/surface.mp4">Watch video</a></video>
<p>Three sequential cuts with persistent separation.</p>
</section>
```

At 6.2 s, the outer piece receives a known diagnostic impulse to test independent motion. This is not a robotic pushing policy. See also [tofu halving](cutting.md).

## Implementation and parameters

This is an independent CPU TLMPM implementation of mechanisms in [BladeMaster v2](https://arxiv.org/abs/2609.27342v2). Cuts are at x = −30, 0 and 30 mm, in three 2 s cycles within a 7 s record. A bounded PD force drives the blade, material reactions change its velocity, and board support impulses are recorded separately.

The blade is 1 × 80 × 40 mm with a 5 mm symmetric bevel at the cutting edge. Contact uses the actual closest point and normal of this convex prism; rendering uses the same geometry. The retained tofu baseline uses its original rectangular blade.

Each particle stores successive cut sides as ternary digits. Opposing assigned sides in any previous cut prevent grid momentum exchange; unassigned material can still bridge a partial incision. A new cut resets contact-work progress but retains earlier side assignments. An independent scorer reconstructs the transfer graph and checks progressive 2→3→4 components, rather than inferring separation from colours or visible gaps.

The authored banana geometry is 120 mm long, with a maximum diameter of about 24 mm, sampled using equal-volume particles. Density is 1,100 kg/m³, Young's modulus 6 kPa and Poisson ratio 0.35. Other contact/drive parameters follow the [tofu experiment](cutting.md); the task's transfer blend is recorded below and in each manifest. **These are synthetic parameters, not a real-banana calibration.** Changing timestep also changes penalty stiffness, so it is a sensitivity check.

## Qualification records

<!-- banana-results:start -->
Defaults: Δx=6 mm; dt=0.25 ms; FLIP=0.95; normal scale=0.1. Sensitivities: half-step: dt=0.000125 s; refined: Δx=0.005 m.

| Case / 案例 | Result / 任务 | Components / 分量 | Overlap / 重叠 (mm) | Probe / 相对位移 (mm) | Peak force / 峰值反力 (N) | Time / 记录 (s) |
|---|---|---:|---:|---:|---:|---:|
| `018-final-full` | Pass / 通过 | 4 | 0.754 | 3.807 | 0.03071 | 214.63 |
| `013-final-half-step` | Pass / 通过 | 4 | 0.531 | 4.034 | 0.05387 | 427.21 |
| `014-final-refined` | Pass / 通过 | 4 | 1.145 | 2.350 | 0.06982 | 363.93 |
| `015-final-uncut` | Rejected / 拒绝 | 1 | 0.616 | 0.464 | 0.00000 | 201.47 |
| `016-final-partial` | Rejected / 拒绝 | 3 | 0.733 | 0.740 | 0.03043 | 212.14 |
| `017-tofu-regression` | Pass / 通过 | 2 | 0.633 | 3.221 | 0.07661 | 24.63 |

Full-cut transfer graphs progress through 2, 3 and 4 components; default final mass fractions are 32.78%, 32.78%, 17.22%, 17.22%. Uncut and partial-last-cut controls fail the four-piece task while passing numerical checks. Limits remain: momentum error ≤10⁻⁹ N·s, det F≥0.05, overlap ≤one proxy radius, relative motion ≥1 mm and other pieces' x drift ≤3 mm.

All 18 bounded invocations consume 3610.32 s including guard waits. Final-batch source hashes match. Development penetration failures and one inverted-material run are retained. Transfer damping/contact coefficients were development choices; this batch qualifies numerical/task behaviour, not held-out food generalization or cutting-force convergence.

[Complete metrics, configurations and failures](https://github.com/huangkiki/Dexlab/blob/main/demos/banana-cut/evidence.json) · [Raw data and replay downloads](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0).
<!-- banana-results:end -->

## How the surface is made

A dense peeled-fruit skin follows the initial material profile, with longitudinal ridges, fibre colour variation and fresh cut-core detail. Each vertex blends saved particle positions/deformation gradients from up to 32 nearby particles within its mechanical component. Caps appear only after the native transfer graph confirms complete separation; piece motion is not additionally prescribed.

This skin does not resolve incomplete incisions: inspect those in the particle view. It is authored display geometry, not a photographic scan or calibrated food material. Particles retain their physical proxy sizes. Subsequent smoothing preserves embedded cap x coordinates. The provenance.json records raw-state, rendering-source and output hashes and display-smoothing displacement. Wood, lighting and the handle are scenery.

## Reproduce

Install `.[cutting,cutting-render]` in the existing DexLab environment. Under the repository's bounded runner and shared research lock, use new output directories:

```bash
python -m dexlab.tofu_cut --task banana --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

These are the commands inside the resource guard; see the [complete bounded-run example](cutting.md#reproduce). `--mode uncut` retains the uncut control; `--mode partial` makes only the third incision shallow. Timestep/grid sensitivity settings are listed above. A successful runner exit means the record completed; use the independent score for the task verdict. Render in a separate bounded postprocessing window.

[Implementation #197](https://github.com/huangkiki/Dexlab/issues/197) · [Source and evidence](https://github.com/huangkiki/Dexlab/tree/main/demos/banana-cut) · [Cutting discussion](https://github.com/huangkiki/Dexlab/discussions/191)
