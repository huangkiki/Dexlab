# Two tofu cuts and independent motion

This matches the task in the two author reference clips: two parallel cuts in a rectangular soft block, followed by independent left-piece motion after withdrawal. Banana slicing is a [separate experiment](banana-cutting.md) and is not part of this comparison.

```{raw} html
<section class="cutting-player" aria-label="Two tofu cuts and independent motion"><header><h3>DexLab · Two tofu cuts</h3>
<div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-sequential/particles.mp4" data-poster="_static/cutting/tofu-sequential/particles-poster.png" aria-pressed="true">Particles</button><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-sequential/surface.mp4" data-poster="_static/cutting/tofu-sequential/surface-poster.png" aria-pressed="false">Surface</button></div></header>
<video controls muted playsinline preload="metadata" poster="_static/cutting/tofu-sequential/particles-poster.png" aria-label="Two tofu cuts and independent motion"><source src="_static/cutting/tofu-sequential/particles.mp4" type="video/mp4"></video>
<p>Two cuts make three pieces. After withdrawal, only the left piece receives an initial leftward velocity.</p></section>
```

[BladeMaster / CRESSim-MPM / DexLab: three-column playback](cutting-comparison.md)

## Inputs and comparison scope

An independent CPU TLMPM implementation drives the blade through both actuator forces and material reactions. The block is 90×30×30 mm; cuts at x=+15 then −15 mm each include descent and withdrawal. The 0.5 mm blade matches the thickness stated for the paper's comparison; its 5 mm symmetric bevel is an explicit DexLab geometry choice.

Defaults: grid 7.5 mm, timestep 0.25 ms, density 1,100 kg/m³, Young's modulus 6 kPa, Poisson ratio 0.35, FLIP=0.95, normal scale=0.1. Each cut takes 2 s. At 4.2 s, only the left region with reference x<−15 mm receives Δv=(−0.12,0,0) m/s; recording ends at 5 s. This predeclared initial-velocity probe is not a robotic pushing policy.

**The task is matched; complete parameter matching is not claimed.** The paper/videos do not expose all dimensions, contact/drive settings and initial velocities needed to recreate this comparison exactly. Values not explicitly matched above are synthetic DexLab choices. The authors' gap width/tetrahedral volume contraction cannot be substituted with our proxy overlap/connectivity metrics. No controlled accuracy or speed ranking is established.

## Additional fine-sampling records and measured GIFs

This is the separate #203 cohort; v0.62.0 records and failures remain unchanged. Displayed sampling uses a 5 mm grid with unchanged physics source and scorer. Half-step, uncut and partial-second-cut cases were frozen before execution.

| Case | Result | Particles | Components | Relative motion (mm) | Peak reaction (N) | Worker time (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `physics-001-tofu-fine` | Pass | 5184 | 3 | 2.398 | 0.02472 | 532.79 |
| `physics-002-tofu-half` | Pass | 5184 | 3 | 2.939 | 0.03088 | 1040.47 |
| `physics-003-tofu-uncut` | Rejected control | 5184 | 1 | 0.234 | 0.00000 | 513.70 |
| `physics-004-tofu-partial` | Rejected control | 5184 | 2 | 0.717 | 0.02472 | 523.23 |
| `physics-005-banana-fine` | Pass | 2480 | 4 | 2.350 | 0.06982 | 363.60 |

This cohort contains 5 physics calls and 2973.79 worker seconds; guard waiting is recorded separately. Differences between sampling/timestep variants remain sensitivity results, not demonstrated force convergence.

[Complete new records](https://github.com/huangkiki/Dexlab/blob/main/demos/cutting-refinement/evidence.json) · [Definitions and paper audit](cutting-fidelity.md)

[New raw records and measured replay downloads](https://github.com/huangkiki/Dexlab/releases/tag/v0.64.0).

## Qualification records

<!-- tofu-comparison-results:start -->
| Case | Task | Components | Overlap (mm) | Relative motion (mm) | Peak reaction (N) | Record time (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `019-tofu-comparison-full` | Pass | 3 | 0.102 | 2.799 | 0.03250 | 155.01 |
| `020-tofu-comparison-half` | Pass | 3 | 0.023 | 3.076 | 0.04065 | 307.25 |
| `021-tofu-comparison-refined` | Pass | 3 | 0.145 | 2.624 | 0.03001 | 298.99 |
| `022-tofu-comparison-uncut` | Rejected control | 1 | 0.101 | 0.328 | 0.00000 | 151.38 |
| `023-tofu-comparison-partial` | Rejected control | 2 | 0.121 | 0.624 | 0.03036 | 153.54 |
| `024-banana-regression` | Pass | 4 | 0.754 | 3.807 | 0.03071 | 213.17 |
| `025-tofu-regression` | Pass | 2 | 0.633 | 3.221 | 0.07661 | 24.87 |

The default result has three equal-mass pieces. Left/middle/right x displacements after the probe are -2.851, -0.075, -0.029 mm. All three full cuts progress through 2→3 components; controls retain one or two. Existing banana and tofu-halving regressions also pass.

The shared ledger contains 25 invocations and 5114.87 s including failures and waits. These seven records share one frozen source cohort. The earlier 18 banana development/qualification records retain their original sources. Neither real-tofu calibration nor cutting-force convergence is established.

[Evidence JSON](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-comparison/evidence.json) · [Raw archives](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)
<!-- tofu-comparison-results:end -->

The independent scorer uses saved reference stencils, cut history, positions, velocities and external impulses. A full task must progress through 2→3 components with masses matching the original cut regions. After withdrawal, the left piece must move at least 1 mm leftward relative to the other pieces, each of which must drift no more than 3 mm in x. Frozen numerical limits remain: momentum error ≤10⁻⁹ N·s, det F≥0.05, proxy overlap ≤one particle radius and nonzero material reaction. Uncut and partial-second-cut controls retain one and at most two components, respectively.

## Display and reproduction

The particle view retains physical proxy sizes for comparison with the author's particle clips. The surface view embeds exposed material-cell faces with saved deformation gradients and cut history. No extra gaps or piece displacements are added. The current comparison uses a neutral gray ground, cream native particles and a thin blade. Particle inventory, dimensions and poses remain unchanged. The orange marker and measurement definitions are explained in the [numerical comparison](cutting-comparison.md). Rendering is not food calibration.

Inside the [existing resource limits and shared lock](cutting.md#reproduce), run:

```bash
python -m dexlab.tofu_cut --task tofu-sequential --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

Controls use `--mode uncut` or `--mode partial`; half-step uses `--dt 0.000125`, finer sampling `--grid-spacing 0.006`. A successful recorder exit does not establish task success: inspect the independent score. Failures, budgets and raw records remain in the [experiment record](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-comparison).
