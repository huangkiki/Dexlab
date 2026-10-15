# Crossed shallow cuts with an intact base

```{raw} html
<section class="cutting-player" aria-label="Crossed shallow cuts with an intact base"><header><h3>Crossed shallow cuts with an intact base</h3>
<div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-scoring/surface.mp4" data-poster="_static/cutting/tofu-scoring/surface-poster.png" aria-pressed="true">Surface</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-scoring/particles.mp4" data-poster="_static/cutting/tofu-scoring/particles-poster.png" aria-pressed="false">Particles / history</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu-scoring/surface-poster.png" aria-label="Crossed shallow cuts with an intact base"><source src="_static/cutting/tofu-scoring/surface.mp4" type="video/mp4"></video></section>
```

The blade makes a shallow incision, withdraws fully, turns 90°, and repeats. The crossing incisions retain a connected lower bridge. Surface and particle replays use the same saved states, with signed opening widths, blade depth, component count and base status displayed throughout.

## What this motion tests

This independent task is inspired by [BladeMaster's scoring demonstration](https://jango6324.github.io/blademaster/): history should persist after reorientation, and partial cuts should preserve the lower bridge. It is qualified separately from [two parallel cuts followed by independent motion](cutting-comparison.md).

DexLab uses two guided orthogonal shallow strokes, with reorientation only when the blade is fully clear. This does not reproduce the complete author knife-tip lateral path or free rotational dynamics. Translational motion integrates driving force and material reaction. Native histories expose the incisions; the display does not draw cracks or add separation.

## Why the surface traces become fine after withdrawal

The current elastic material recoils. At 4.2 s, mean affine-face openings are about 0.277/0.276 mm, while the displayed mesh openings at the top intersection are only about 0.039/0.005 mm, below a pixel in many views. These sample different locations. The particle view colours actual histories: both upper side assignments persist and the uncut base stays cream. Colour does not imply a wider gap.

[Same-state surface diagnostics](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/surface-closure.json) retain the split vertices at reference point (0,0,30 mm). No opening is enlarged and no crack is painted. Matching real-food residual grooves requires material modelling and calibration, which this task does not establish.

## Inputs and measurement definitions

The block is 45×45×30 mm, using a 5 mm grid and 3,888 native particles. Blade thickness is 0.5 mm with a 5 mm bevel. Target edge height falls from 42 to 24 mm and withdraws; the second stroke repeats after a 90° vertical-axis turn. Duration is 4.2 s; nominal timestep is 0.25 ms with a 0.125 ms control. Synthetic E=6 kPa, ν=0.35 and ρ=1,100 kg/m³ are not calibrated tofu parameters.

The first and second openings are measured along x and y using opposing affine material faces; negative values indicate estimated overlap. Blade depth is relative to the original 30 mm upper surface, not local depth below the currently deformed surface. The base is the fixed reference region below 15 mm.

Independent acceptance requires a complete record, persistent histories, opposing side labels for both cuts, and measured maximum edge depths of 2–12 mm each. The native transfer graph must have one component at 0, 1.2, 2, 3.2, 4 and 4.2 s; the base must remain unlabelled and connected throughout. Momentum error ≤10⁻⁹ N·s, det F≥0.05, proxy overlap ≤one particle radius and nonzero material reaction retain their frozen thresholds. Apparent surface connectivity cannot substitute for this check.

<!-- scoring-results:start -->
## Qualification results

| Case | Result | Components | Scoring depths (mm) | Peak reaction (N) | Worker time (s) |
| --- | --- | ---: | --- | ---: | ---: |
| `physics-001-cross` | Pass | 1 | 5.977 / 5.967 | 0.007879 | 342.98 |
| `physics-002-cross-half` | Pass | 1 | 5.966 / 5.964 | 0.008680 | 680.83 |
| `physics-003-cross-uncut` | Rejected control | 1 | — (knife clear) | 0.000000 | 343.00 |
| `physics-004-sequential-regression` | Pass | 3 | — | 0.032504 | 178.50 |

The first three records are scoring cases; the last is the original sequential-cut regression. Every case, failure and cost is retained. Passing at two timesteps does not establish force convergence.

Half-step peak reaction changes by +10.16% relative to default; interpret this as sensitivity.

<!-- scoring-results:end -->

## Reproduction and raw records

Run within the [shared lock and resource limits](cutting.md#reproduce). The pre-run [protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/protocol.json) retains all cases, budgets and acceptance definitions.

```bash
python -m dexlab.tofu_cut --task tofu-scoring --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

Add `--dt 0.000125` for the half-step case or `--mode uncut` for the negative control. The uncut case must fail the cutting outcome while retaining one component and numerical consistency. [Evidence](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/evidence.json) includes source and resource costs; [v0.65.0 archives](https://github.com/huangkiki/Dexlab/releases/tag/v0.65.0) retain the complete cohort.

<a href="_static/cutting/tofu-scoring/measurements.json">Per-frame measurements</a> · <a href="_static/cutting/tofu-scoring/surface.gif">Measured surface GIF</a> · <a href="_static/cutting/tofu-scoring/particles.gif">Measured particle GIF</a>
