# Two tofu cuts and a knife-face push

**Historical protocol archive. See the [current showcase](cut-push.md) for continuous cut-to-push motion and per-frame contact forces/displacements. Numbers and videos below retain their historical inputs; they are not the latest task.**

The current replay makes the source of post-cut motion visible: the knife returns to the left kerf and pushes the left piece sideways. Actuator forces and material reactions jointly integrate the blade; material velocity is never directly changed. Banana slicing and cross scoring remain separate tasks.

```{raw} html
<section class="cutting-player" aria-label="Two tofu cuts and independent motion"><header><h3>DexLab · Two tofu cuts</h3>
<div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-sequential/particles.mp4" data-poster="_static/cutting/tofu-sequential/particles-poster.png" aria-pressed="true">Particles</button><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-sequential/surface.mp4" data-poster="_static/cutting/tofu-sequential/surface-poster.png" aria-pressed="false">Surface</button></div></header>
<video controls muted playsinline preload="metadata" poster="_static/cutting/tofu-sequential/particles-poster.png" aria-label="Two tofu cuts and independent motion"><source src="_static/cutting/tofu-sequential/particles.mp4" type="video/mp4"></video>
<p>Two cuts form three pieces. The knife re-enters the left kerf, pushes through face contact, then withdraws. No direct material velocity increment.</p></section>
```

**Comparison boundary:** author clips initialize left-piece velocity; the current DexLab clip uses knife-face contact. The same cutting problem does not imply the same final input or permit displacement, force or cost rankings. Historical impulse data and downloads below remain unchanged and do not describe the new video.

## Motion and acceptance

A synthetic 90×30×30 mm block receives cuts at x=+15 then −15 mm, each lasting 2 s. Every saved state array through 4 s is identical to the historical fine-sampling record. At 4.00 s the knife edge moves from z=36 to 2 mm (by 4.80 s), its face pushes from x=−15 to −27 mm (by 6.00 s), then withdraws to z=36 mm (by 6.60 s); recording ends at 7.00 s. Cutting is disabled during pushing. Material and contact solvers are unchanged.

Displayed Fx is the native knife-on-material contact force (negative means left), excluding drive and board support. Displacements use the 4.00 s baseline. Independent scoring requires persistent three-piece topology, at least 1 mm relative left-piece motion, passive |dx|≤3 mm, net leftward knife-contact impulse≥0.001 N·s, and an external-force ledger without a material velocity impulse. Original momentum, overlap and positive-Jacobian limits are unchanged.

The replay uses a 5 mm grid, 0.25 ms timestep, 0.5 mm blade and 5 mm bevel; density 1100 kg/m³, E=6 kPa, ν=0.35, FLIP=0.95. These are inherited synthetic parameters, not calibrated tofu.

## New knife-push protocol results

| Case | Result | Components | Relative motion (mm) | Leftward knife impulse (N·s) | Worker time (s) |
| --- | --- | ---: | ---: | ---: | ---: |
| `physics-001-push` | Pass | 3 | 11.102 | 0.105801 | 736.02 |
| `physics-002-half` | Pass | 3 | 11.234 | 0.104222 | 1467.43 |
| `physics-003-no-push` | Rejected control | 3 | 0.007 | 0.000000 | 729.26 |
| `physics-004-legacy` | Pass | 3 | 2.799 | — | 155.91 |

Half-step results measure sensitivity, not convergence. The no-push control retains three pieces but fails motion and knife-impulse criteria; legacy impulse passes its original thresholds. Every run and cost is retained.

[Complete records](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-knife-push/evidence.json) · [Protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-knife-push/protocol.json) · [Raw records and media](https://github.com/huangkiki/Dexlab/releases/tag/v0.66.0)

## Historical impulse cohort: fine sampling (v0.64.0)

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

## Historical impulse qualification (v0.62.0)

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

## Reproduction

Run inside the [existing resource limits and shared lock](cutting.md#reproduce):

```bash
python -m dexlab.tofu_cut --task tofu-sequential --grid-spacing .005 --motion-protocol knife-push --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

`--motion-protocol no-push` selects the equal-duration no-push control; `--motion-protocol impulse` restores the historical 5 s velocity probe; `--dt .000125` selects half-step. Default grid remains 7.5 mm; the command explicitly selects the displayed 5 mm grid. Judge success by the independent score, not recorder exit status.
