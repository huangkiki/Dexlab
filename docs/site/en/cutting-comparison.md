# Do cut pieces stay independent?

This page retains the historical v0.66.0 three-column comparison, with values and videos from that protocol. See the [current showcase](cut-push.md) for tofu/banana final cuts transitioning directly into a side push.

```{raw} html
:file: _cutting-comparison.html
```

Measured GIFs show opening, interior volume and piece motion derived from saved states. GIF playback is slowed; clocks retain physical time. [Paper audit and measurement definitions](cutting-fidelity.md).

## What the original comparison tests

The [BladeMaster project](https://jango6324.github.io/blademaster/#comparison) and [paper v2, IV-A / Fig. 5](https://arxiv.org/abs/2609.27342v2) test history retention after two parallel cuts. After withdrawal, only the left piece receives an initial leftward velocity; motion of the middle and right pieces reveals unwanted shared-grid coupling. Both reference clips were published by the BladeMaster authors, including their comparison against [Ou and Tavakoli (2025)](https://arxiv.org/abs/2502.18437).

| Measurement event and quantity | BladeMaster¹ | CRESSim-MPM¹ | DexLab² |
| --- | ---: | ---: | ---: |
| First cut at half depth: mean opening (mm) | 0.654 | 4.059 | 0.496 (0.82 s) |
| Both cuts withdrawn: middle-piece contraction (%) | 0.506 | 8.746 | 2.509 (4.00 s) |
| After knife-face push: left x displacement (mm) | Different input | Different input | -11.128 |
| Same window: middle / right x displacement (mm) | Different input | Different input | -0.038 / -0.015 |
| Push phase: net leftward contact impulse (N·s) | Different input | Different input | 0.105801 |

**Different final inputs:** author clips initialize left-piece velocity; DexLab now pushes through native knife contact with no direct material velocity increment. The first two cutting metrics remain side by side; the last three rows describe only DexLab’s knife-push phase, not a matched-input comparison.

¹ Values reported by the [BladeMaster project / paper Fig. 5](https://jango6324.github.io/blademaster/#comparison), including its CRESSim-MPM comparison. ² [DexLab event measurements from saved states](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-knife-push/evidence.json): 5 mm grid, 0.25 ms timestep and 0.5 mm blade; displacements cover 4.00–7.00 s; contact impulse is integrated over 4.00–6.60 s. The half-depth event occurs at 0.82375 s; the table uses the nearest saved frame, 0.82 s. Openings use affine material faces and volumes use interior middle-piece tetrahedra; contraction is the negative relative volume change (-ΔV/V₀). These are **reported / measured values side by side**. Complete author settings and sampling remain [unmatched](https://github.com/huangkiki/Dexlab/issues/200), so the table does not establish a controlled accuracy ranking.

Reference videos remain attributed embeds on the original host. DexLab records, failures and controls are in the [two-cut tofu experiment](tofu-comparison.md).

## DexLab event measurements (5 mm grid)

Signed openings use an affine material-face estimator; volume uses middle-region interior tetrahedra. These independently defined estimates and synthetic settings do not support a ranking against the author-reported values above.

| Event | Saved time (s) | Cut 1 (mm) | Cut 2 (mm) | Middle volume change (%) | Knife on material Fx (N) |
| --- | ---: | ---: | ---: | ---: | ---: |
| First cut half-depth | 0.82 | +0.496 | — | -1.323 | -0.0133 |
| Both cuts withdrawn / motion baseline | 4.00 | +0.124 | +0.250 | -2.509 | -0.0000 |
| Start lateral push | 4.80 | +0.100 | +0.543 | -2.598 | +0.0037 |
| End lateral push | 6.00 | +0.134 | +11.491 | -2.479 | -0.0747 |
| Withdrawal ends | 6.60 | +0.134 | +11.194 | -2.479 | -0.0000 |
| Final | 7.00 | +0.134 | +11.319 | -2.479 | -0.0000 |

<a href="_static/cutting/tofu-sequential/measurements.json">Per-frame values</a> · <a href="_static/cutting/tofu-sequential/particles.gif">Measured GIF</a>

The third column uses a neutral gray ground, cream particles and an orthographic camera similar to the reference presentation. The orange rectangle projects the middle native particle region, including proxy radii; its number comes from interior tetrahedra, not rectangle area. Particle count, physical dimensions, blade pose and material motion retain the recorded values. The 5 mm sampling looks coarser than the author clips; visual consistency does not align the outstanding physical settings.

[Crossed shallow incisions with a connected base](tofu-scoring.md) form a separate task.

## Protocol for a future matched comparison

1. **Freeze one question.** Does the first discontinuity remain mechanically separated after the second cut? Freeze block dimensions, material parameters, sampling, blade geometry, trajectories and contact model before running. Resolve missing author parameters rather than estimate them from screenshots.
2. **Align events.** Save first half-depth, first withdrawal, second withdrawal, single-piece velocity initialization and a fixed elapsed interval. Synchronize only shared-input runs; never stretch clips to imply equal speed or cost.
3. **Measure separately.** Sample gap distributions in the same material-coordinate band, declare the middle-piece volume estimator, and record every piece's centroid motion, momentum and external impulse. A visible gap does not replace connectivity scoring.
4. **Keep counterexamples.** Uncut, partial-cut and history-disabled-after-withdrawal ablations; half-step and finer-sampling sensitivities. Retain failed, invalid and not-run cases.
5. **Qualify before ranking.** Every executed implementation needs source/binary versions, shared inputs, independent scoring, budgets and raw records. Author videos are references. No matched three-method comparison or superiority ranking has yet been established.

This is a reusable comparison workflow. A new benchmark still needs its own frozen protocol and resource budget. This page first delivers the three-column view and explicit provenance.
